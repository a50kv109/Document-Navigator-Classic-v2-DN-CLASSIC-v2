"""
Slice 2 — Functional sufficiency expansion tests.
Slice 1 golden path must remain intact (regression via full suite).
"""

from __future__ import annotations

import sys
from pathlib import Path


from contracts import (
    LifecycleCandidate,
    IdentifiedOntology,
    SemanticMode,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
    GateDecision,
    SourceSpan,
    EvidencePackage,
)
from gate import evaluate_gate
from evidence import package_evidence
from dle_core import DLECore, ObjectState


TEXT = "Company undertakes to prepare project documentation."


def _ev(
    *,
    doc: str,
    pointer: str = "ent_project_docs",
    life: LifecycleStatus,
    ground: GroundingStatus = GroundingStatus.GROUNDED_SOURCE_CLAIM,
    unc: EpistemicUncertainty = EpistemicUncertainty.CLEAR,
) -> EvidencePackage:
    cand = LifecycleCandidate(
        document_id=doc,
        identified_ontology=IdentifiedOntology(objects=["company"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=life,
        grounding_status=ground,
        epistemic_uncertainty=unc,
        source_spans=[SourceSpan("s1", TEXT)],
        target_entity_id=pointer,
    )
    d = evaluate_gate(cand)
    if d == GateDecision.ACTIVATE_DLE:
        pkg = package_evidence(cand, d)
        assert pkg is not None
        return pkg
    return EvidencePackage(
        document_id=doc,
        target_entity_id=pointer,
        lifecycle_status=life,
        grounding_status=ground,
        epistemic_uncertainty=unc,
        source_spans=cand.source_spans,
        temporal=None,
        candidate_evidence_refs=[],
        is_command=False,
    )


# ---------------------------------------------------------------------------
# Normal multi-step progression (the scenario that broke one-Transition Core)
# ---------------------------------------------------------------------------

def test_slice2_full_progression():
    core = DLECore()
    r1 = core.receive_evidence(_ev(doc="e1", life=LifecycleStatus.POTENTIAL))
    assert r1.state_after == ObjectState.ACKNOWLEDGED
    assert r1.transition and r1.transition.transition_name == "ACKNOWLEDGE_POTENTIAL"

    r2 = core.receive_evidence(_ev(doc="e2", life=LifecycleStatus.ACTIVE))
    assert r2.object_id == r1.object_id
    assert r2.state_after == ObjectState.IN_PROGRESS
    assert r2.transition and r2.transition.transition_name == "START_WORK"

    r3 = core.receive_evidence(_ev(doc="e3", life=LifecycleStatus.HISTORICAL))
    assert r3.object_id == r1.object_id
    assert r3.state_after == ObjectState.COMPLETED
    assert r3.transition and r3.transition.transition_name == "COMPLETE_WORK"


def test_slice1_golden_path_unchanged():
    """Slice 1: POTENTIAL on NEW still only ACKNOWLEDGE_POTENTIAL."""
    core = DLECore()
    r = core.receive_evidence(_ev(doc="s1", life=LifecycleStatus.POTENTIAL))
    assert r.state_before == ObjectState.NEW
    assert r.state_after == ObjectState.ACKNOWLEDGED
    assert r.transition.transition_name == "ACKNOWLEDGE_POTENTIAL"


# ---------------------------------------------------------------------------
# Adversarial
# ---------------------------------------------------------------------------

def test_replay_at_each_stage_no_double_transition():
    core = DLECore()
    p = "ent_replay"
    core.receive_evidence(_ev(doc="1", pointer=p, life=LifecycleStatus.POTENTIAL))
    r = core.receive_evidence(_ev(doc="1b", pointer=p, life=LifecycleStatus.POTENTIAL))
    assert r.transition is None
    assert r.state_after == ObjectState.ACKNOWLEDGED

    core.receive_evidence(_ev(doc="2", pointer=p, life=LifecycleStatus.ACTIVE))
    r = core.receive_evidence(_ev(doc="2b", pointer=p, life=LifecycleStatus.ACTIVE))
    assert r.transition is None
    assert r.state_after == ObjectState.IN_PROGRESS

    core.receive_evidence(_ev(doc="3", pointer=p, life=LifecycleStatus.HISTORICAL))
    r = core.receive_evidence(_ev(doc="3b", pointer=p, life=LifecycleStatus.HISTORICAL))
    assert r.transition is None
    assert r.state_after == ObjectState.COMPLETED


def test_out_of_order_active_before_potential():
    """ACTIVE on NEW is mid-lifecycle entry: REGISTER_ACTIVE (earned expansion)."""
    core = DLECore()
    r = core.receive_evidence(_ev(doc="early", life=LifecycleStatus.ACTIVE))
    assert r.transition is not None
    assert r.transition.transition_name == "REGISTER_ACTIVE"
    assert r.state_after == ObjectState.IN_PROGRESS


def test_out_of_order_historical_before_progress():
    """HISTORICAL on ACKNOWLEDGED closes without work phase: CLOSE_ACKNOWLEDGED."""
    core = DLECore()
    core.receive_evidence(_ev(doc="1", life=LifecycleStatus.POTENTIAL))
    r = core.receive_evidence(_ev(doc="skip", life=LifecycleStatus.HISTORICAL))
    assert r.transition is not None
    assert r.transition.transition_name == "CLOSE_ACKNOWLEDGED"
    assert r.state_after == ObjectState.COMPLETED


def test_conflicting_unsupported_does_not_progress():
    core = DLECore()
    core.receive_evidence(_ev(doc="1", life=LifecycleStatus.POTENTIAL))
    r = core.receive_evidence(
        _ev(doc="bad", life=LifecycleStatus.ACTIVE, ground=GroundingStatus.UNSUPPORTED_INFERENCE)
    )
    assert r.transition is None
    assert r.state_after == ObjectState.ACKNOWLEDGED


def test_ambiguous_uncertainty_blocks():
    core = DLECore()
    core.receive_evidence(_ev(doc="1", life=LifecycleStatus.POTENTIAL))
    r = core.receive_evidence(
        _ev(doc="amb", life=LifecycleStatus.ACTIVE, unc=EpistemicUncertainty.AMBIGUOUS)
    )
    assert r.transition is None


def test_different_pointers_independent_lifecycles():
    core = DLECore()
    r_a = core.receive_evidence(_ev(doc="a1", pointer="proj_A", life=LifecycleStatus.POTENTIAL))
    r_b = core.receive_evidence(_ev(doc="b1", pointer="proj_B", life=LifecycleStatus.POTENTIAL))
    assert r_a.object_id != r_b.object_id
    core.receive_evidence(_ev(doc="a2", pointer="proj_A", life=LifecycleStatus.ACTIVE))
    # B still only ACKNOWLEDGED
    r_b2 = core.receive_evidence(_ev(doc="b2", pointer="proj_B", life=LifecycleStatus.POTENTIAL))
    assert r_b2.state_after == ObjectState.ACKNOWLEDGED
    assert r_b2.transition is None


def test_invalid_transition_no_public_api():
    core = DLECore()
    assert not hasattr(core, "force_transition")
    assert not hasattr(core, "set_state")


def test_completed_is_terminal_for_slice2_rules():
    core = DLECore()
    p = "term"
    core.receive_evidence(_ev(doc="1", pointer=p, life=LifecycleStatus.POTENTIAL))
    core.receive_evidence(_ev(doc="2", pointer=p, life=LifecycleStatus.ACTIVE))
    core.receive_evidence(_ev(doc="3", pointer=p, life=LifecycleStatus.HISTORICAL))
    r = core.receive_evidence(_ev(doc="4", pointer=p, life=LifecycleStatus.POTENTIAL))
    assert r.state_after == ObjectState.COMPLETED
    assert r.transition is None


def test_no_sixth_primitive_after_expansion():
    import dle_core as m
    for bad in ("LifecycleManager", "TemporalEngine", "IdentityEngine",
                "RuleEngine", "EventEngine", "WorkflowEngine"):
        assert bad not in dir(m)
