"""
Minimal DLE Core Runtime Probe tests.
One vertical slice + adversarial checks. No production Core.
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
    TemporalAttributes,
    EvidencePackage,
)
from gate import evaluate_gate
from evidence import package_evidence
from dle_core import DLECore, ObjectState, CoreReceipt


def _evidence(
    *,
    document_id: str = "doc-1",
    target_entity_id: str | None = "ent_project_alpha",
    lifecycle_status: LifecycleStatus = LifecycleStatus.POTENTIAL,
    grounding: GroundingStatus = GroundingStatus.GROUNDED_SOURCE_CLAIM,
    uncertainty: EpistemicUncertainty = EpistemicUncertainty.CLEAR,
    temporal: TemporalAttributes | None = None,
) -> EvidencePackage:
    cand = LifecycleCandidate(
        document_id=document_id,
        identified_ontology=IdentifiedOntology(objects=["company"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=lifecycle_status,
        grounding_status=grounding,
        epistemic_uncertainty=uncertainty,
        source_spans=[SourceSpan(span_id="s1", text="Компания обязуется разработать проект.")],
        target_entity_id=target_entity_id,
        temporal=temporal,
    )
    decision = evaluate_gate(cand)
    # Only packages that Gate admits reach Core in the real pipeline;
    # for Condition-failure tests we may force a package that would be blocked
    # by Gate — still test Core isolation.
    if decision != GateDecision.ACTIVATE_DLE:
        # construct package directly for negative Condition tests
        return EvidencePackage(
            document_id=document_id,
            target_entity_id=target_entity_id,
            lifecycle_status=lifecycle_status,
            grounding_status=grounding,
            epistemic_uncertainty=uncertainty,
            source_spans=cand.source_spans,
            temporal=temporal,
            candidate_evidence_refs=[],
            is_command=False,
        )
    pkg = package_evidence(cand, decision)
    assert pkg is not None
    return pkg


# ---------------------------------------------------------------------------
# TEST 1 — Canonical vertical slice
# ---------------------------------------------------------------------------

def test_1_canonical_vertical_slice():
    """Evidence → Object → Condition → Transition → State"""
    core = DLECore()
    pkg = _evidence(
        lifecycle_status=LifecycleStatus.POTENTIAL,
        grounding=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        uncertainty=EpistemicUncertainty.CLEAR,
    )
    receipt = core.receive_evidence(pkg)

    assert receipt.accepted is True
    assert receipt.object_id is not None
    assert receipt.object_id.startswith("dle-obj-")
    assert receipt.state_before == ObjectState.NEW
    assert receipt.state_after == ObjectState.ACKNOWLEDGED
    assert receipt.transition is not None
    assert receipt.transition.applied is True
    assert receipt.transition.transition_name == "ACKNOWLEDGE_POTENTIAL"
    assert "Condition satisfied" in receipt.note


# ---------------------------------------------------------------------------
# TEST 2 — Evidence is not a command
# ---------------------------------------------------------------------------

def test_2_evidence_not_command():
    try:
        EvidencePackage(
            document_id="x",
            target_entity_id=None,
            lifecycle_status=LifecycleStatus.POTENTIAL,
            grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
            epistemic_uncertainty=EpistemicUncertainty.CLEAR,
            source_spans=[],
            temporal=None,
            candidate_evidence_refs=[],
            is_command=True,
        )
        assert False, "must reject is_command=True"
    except ValueError:
        pass

    # Even if somehow obtained, Core rejects
    core = DLECore()
    # cannot construct; invariant holds


# ---------------------------------------------------------------------------
# TEST 3 — Condition failure → no Transition
# ---------------------------------------------------------------------------

def test_3_condition_failure_no_transition():
    core = DLECore()
    # AMBIGUOUS uncertainty → all Conditions fail (ACTIVE alone is now a valid entry path)
    pkg = _evidence(
        lifecycle_status=LifecycleStatus.POTENTIAL,
        uncertainty=EpistemicUncertainty.AMBIGUOUS,
    )
    receipt = core.receive_evidence(pkg)
    assert receipt.accepted is True
    assert receipt.transition is None
    assert receipt.state_before == ObjectState.NEW
    assert receipt.state_after == ObjectState.NEW
    assert "no Transition" in receipt.note


def test_3b_unsupported_no_transition():
    core = DLECore()
    pkg = _evidence(grounding=GroundingStatus.UNSUPPORTED_INFERENCE)
    receipt = core.receive_evidence(pkg)
    assert receipt.transition is None
    assert receipt.state_after == ObjectState.NEW


# ---------------------------------------------------------------------------
# TEST 4 — Same semantic pointer → same Object
# ---------------------------------------------------------------------------

def test_4_same_pointer_same_object():
    core = DLECore()
    p1 = _evidence(document_id="d1", target_entity_id="ent_project_alpha")
    p2 = _evidence(document_id="d2", target_entity_id="ent_project_alpha")
    r1 = core.receive_evidence(p1)
    r2 = core.receive_evidence(p2)
    assert r1.object_id == r2.object_id
    # first transition applied; second sees already ACKNOWLEDGED → no second transition
    assert r1.transition is not None and r1.transition.applied
    assert r2.transition is None
    assert r2.state_after == ObjectState.ACKNOWLEDGED


# ---------------------------------------------------------------------------
# TEST 5 — Different pointers → different Objects
# ---------------------------------------------------------------------------

def test_5_different_pointers_different_objects():
    core = DLECore()
    r1 = core.receive_evidence(_evidence(target_entity_id="ent_alpha"))
    r2 = core.receive_evidence(_evidence(target_entity_id="ent_beta"))
    assert r1.object_id != r2.object_id


# ---------------------------------------------------------------------------
# TEST 6 — Temporal data passive
# ---------------------------------------------------------------------------

def test_6_temporal_data_passive():
    core = DLECore()
    t = TemporalAttributes(
        issued_at="2026-01-10",
        expires_at="2026-12-31",
        sequence_id="17",
    )
    pkg = _evidence(temporal=t)
    receipt = core.receive_evidence(pkg)
    assert receipt.accepted is True
    # no timer / scheduler attributes on core
    assert not hasattr(core, "timers")
    assert not hasattr(core, "scheduler")
    assert not hasattr(core, "clock")


# ---------------------------------------------------------------------------
# Ownership / isolation
# ---------------------------------------------------------------------------

def test_no_external_object_creation_api():
    core = DLECore()
    assert not hasattr(core, "create_object")
    assert not hasattr(core, "change_state")
    assert not hasattr(core, "execute_transition")
    # only receive_evidence is the public entry for lifecycle work
    assert callable(core.receive_evidence)


def test_pointer_is_not_object_id():
    core = DLECore()
    r = core.receive_evidence(_evidence(target_entity_id="ent_project_alpha"))
    assert r.object_id != "ent_project_alpha"
    assert r.object_id.startswith("dle-obj-")
