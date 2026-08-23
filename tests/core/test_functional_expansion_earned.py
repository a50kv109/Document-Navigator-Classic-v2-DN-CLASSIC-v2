"""Earned functional expansion tests + explicit NOT YET EARNED failure path."""

from __future__ import annotations
import sys
from pathlib import Path

from contracts import (
    LifecycleCandidate, IdentifiedOntology, SemanticMode, LifecycleStatus,
    GroundingStatus, EpistemicUncertainty, GateDecision, SourceSpan, EvidencePackage,
)
from gate import evaluate_gate
from evidence import package_evidence
from dle_core import DLECore, ObjectState


def _ev(doc, life, pointer="ent_x", ground=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        unc=EpistemicUncertainty.CLEAR):
    cand = LifecycleCandidate(
        document_id=doc,
        identified_ontology=IdentifiedOntology(objects=["c"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=life,
        grounding_status=ground,
        epistemic_uncertainty=unc,
        source_spans=[SourceSpan("s", "obligation text")],
        target_entity_id=pointer,
    )
    d = evaluate_gate(cand)
    if d == GateDecision.ACTIVATE_DLE:
        return package_evidence(cand, d)
    return EvidencePackage(
        document_id=doc, target_entity_id=pointer, lifecycle_status=life,
        grounding_status=ground, epistemic_uncertainty=unc,
        source_spans=cand.source_spans, temporal=None,
        candidate_evidence_refs=[], is_command=False,
    )


def test_A_full_obligation_happy_path():
    core = DLECore()
    assert core.receive_evidence(_ev("1", LifecycleStatus.POTENTIAL)).state_after == ObjectState.ACKNOWLEDGED
    assert core.receive_evidence(_ev("2", LifecycleStatus.ACTIVE)).state_after == ObjectState.IN_PROGRESS
    assert core.receive_evidence(_ev("3", LifecycleStatus.HISTORICAL)).state_after == ObjectState.COMPLETED


def test_C_active_first_sighting():
    core = DLECore()
    r = core.receive_evidence(_ev("a", LifecycleStatus.ACTIVE))
    assert r.transition.transition_name == "REGISTER_ACTIVE"
    assert r.state_after == ObjectState.IN_PROGRESS


def test_C_historical_first_sighting():
    core = DLECore()
    r = core.receive_evidence(_ev("h", LifecycleStatus.HISTORICAL))
    assert r.transition.transition_name == "REGISTER_CLOSED"
    assert r.state_after == ObjectState.COMPLETED


def test_close_after_ack_without_work():
    core = DLECore()
    core.receive_evidence(_ev("1", LifecycleStatus.POTENTIAL))
    r = core.receive_evidence(_ev("2", LifecycleStatus.HISTORICAL))
    assert r.transition.transition_name == "CLOSE_ACKNOWLEDGED"
    assert r.state_after == ObjectState.COMPLETED


def test_B_failed_not_yet_earned_no_failed_state():
    """FAILED terminal requires Evidence discrimination not present in GREEN enums."""
    assert not hasattr(ObjectState, "FAILED")
    # HISTORICAL from IN_PROGRESS still maps only to COMPLETED — success/closure
    core = DLECore()
    core.receive_evidence(_ev("1", LifecycleStatus.POTENTIAL))
    core.receive_evidence(_ev("2", LifecycleStatus.ACTIVE))
    r = core.receive_evidence(_ev("3", LifecycleStatus.HISTORICAL))
    assert r.state_after == ObjectState.COMPLETED
    assert r.transition.transition_name == "COMPLETE_WORK"


def test_replay_register_active():
    core = DLECore()
    core.receive_evidence(_ev("1", LifecycleStatus.ACTIVE, pointer="ra"))
    r = core.receive_evidence(_ev("2", LifecycleStatus.ACTIVE, pointer="ra"))
    assert r.transition is None
    assert r.state_after == ObjectState.IN_PROGRESS


def test_terminal_completed_stable():
    core = DLECore()
    core.receive_evidence(_ev("1", LifecycleStatus.HISTORICAL, pointer="t"))
    for life in (LifecycleStatus.POTENTIAL, LifecycleStatus.ACTIVE, LifecycleStatus.HISTORICAL):
        r = core.receive_evidence(_ev("x"+life.value, life, pointer="t"))
        assert r.state_after == ObjectState.COMPLETED
        assert r.transition is None
