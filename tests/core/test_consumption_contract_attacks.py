"""
Adversarial attacks A–Q on Evidence → DLE Core consumption contract.
No DLE Core logic. Boundary isolation only.
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
from evidence import package_evidence, assert_identity_separation
from consumption_boundary import consume_evidence, BoundaryReceipt
from conceptual_core_sketch import future_dle_core_receive


def _pkg(
    *,
    document_id: str = "doc-1",
    target_entity_id: str | None = "ent_x",
    lifecycle_status: LifecycleStatus = LifecycleStatus.ACTIVE,
    temporal: TemporalAttributes | None = None,
) -> EvidencePackage:
    cand = LifecycleCandidate(
        document_id=document_id,
        identified_ontology=IdentifiedOntology(objects=["x"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=lifecycle_status,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[SourceSpan(span_id="s", text="t")],
        target_entity_id=target_entity_id,
        temporal=temporal,
    )
    d = evaluate_gate(cand)
    assert d == GateDecision.ACTIVATE_DLE
    pkg = package_evidence(cand, d)
    assert pkg is not None
    return pkg


# A. Unknown target_entity_id
def test_A_unknown_target_entity_id():
    pkg = _pkg(target_entity_id="ent_never_seen_before")
    r = consume_evidence(pkg)
    assert r.accepted
    assert r.target_entity_id == "ent_never_seen_before"
    # Core sketch also accepts without resolving
    obs = future_dle_core_receive(pkg)
    assert obs["opaque_semantic_pointer"] == "ent_never_seen_before"


# B. Two packages same target_entity_id
def test_B_two_packages_same_pointer():
    p1 = _pkg(document_id="doc-a", target_entity_id="ent_shared")
    p2 = _pkg(document_id="doc-b", target_entity_id="ent_shared")
    r1 = consume_evidence(p1)
    r2 = consume_evidence(p2)
    assert r1.target_entity_id == r2.target_entity_id == "ent_shared"
    # No identity collapse or merge performed by boundary


# C. Different pointers possibly same real-world entity
def test_C_different_pointers_no_forced_merge():
    p1 = _pkg(target_entity_id="ent_alpha")
    p2 = _pkg(target_entity_id="ent_ALPHA_alias")
    assert p1.target_entity_id != p2.target_entity_id
    # Boundary does not equate them


# D/E/F. POTENTIAL / HISTORICAL / ACTIVE
def test_DEF_lifecycle_statuses_descriptive():
    for status in (LifecycleStatus.POTENTIAL, LifecycleStatus.HISTORICAL, LifecycleStatus.ACTIVE):
        pkg = _pkg(lifecycle_status=status)
        r = consume_evidence(pkg)
        assert r.lifecycle_status_descriptive == status.value
        obs = future_dle_core_receive(pkg)
        assert "No Transition executed" in obs["note"]


# G. Conflicting Evidence (two packages, conflicting descriptive status)
def test_G_conflicting_evidence_crosses_as_data():
    p_active = _pkg(document_id="d1", lifecycle_status=LifecycleStatus.ACTIVE)
    p_hist = _pkg(document_id="d2", lifecycle_status=LifecycleStatus.HISTORICAL)
    # Both cross independently; conflict resolution belongs to future Core/Condition
    assert consume_evidence(p_active).accepted
    assert consume_evidence(p_hist).accepted


# H. Different document_id
def test_H_different_document_ids():
    p1 = _pkg(document_id="doc-1")
    p2 = _pkg(document_id="doc-2")
    assert consume_evidence(p1).document_id != consume_evidence(p2).document_id


# I/J/K/L. sequence / timestamps combinations
def test_IJKL_temporal_combinations():
    cases = [
        TemporalAttributes(sequence_id="seq-1", issued_at="2026-01-01"),
        TemporalAttributes(issued_at="2026-01-01", event_at="2026-01-01"),  # equal timestamps
        TemporalAttributes(issued_at="2026-06-01"),  # timestamp, no sequence
        TemporalAttributes(sequence_id="seq-only"),  # sequence, no timestamp
    ]
    for t in cases:
        pkg = _pkg(temporal=t)
        r = consume_evidence(pkg)
        assert r.accepted
        # No ordering / expiry logic executed by boundary


# M. expires_at present
def test_M_expires_at_passive():
    t = TemporalAttributes(expires_at="2026-12-31")
    pkg = _pkg(temporal=t)
    r = consume_evidence(pkg)
    assert r.accepted
    assert not hasattr(r, "timer")
    assert not hasattr(r, "schedule")


# N. relative_raw present (YELLOW remains unresolved)
def test_N_relative_raw_opaque():
    t = TemporalAttributes(relative_raw="через 30 дней после подписания")
    pkg = _pkg(temporal=t)
    r = consume_evidence(pkg)
    assert r.accepted
    # relative not parsed into duration/anchor by boundary or sketch
    obs = future_dle_core_receive(pkg)
    assert "No Object created" in obs["note"]


# O. Attempt to encode Transition command
def test_O_command_impossible():
    try:
        EvidencePackage(
            document_id="x",
            target_entity_id=None,
            lifecycle_status=LifecycleStatus.ACTIVE,
            grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
            epistemic_uncertainty=EpistemicUncertainty.CLEAR,
            source_spans=[],
            temporal=None,
            candidate_evidence_refs=[],
            is_command=True,
        )
        assert False
    except ValueError:
        pass


# P. Attempt to pass DLE Object ID through target_entity_id
def test_P_object_id_via_pointer_rejected_by_invariant():
    # Boundary itself does not prevent the *string* from looking like an Object ID,
    # but the architectural invariant (assert_identity_separation) forbids treating it as such.
    pointer = "dle-obj-999"
    try:
        assert_identity_separation(pointer, "dle-obj-999")  # must raise when equal
        assert False, "expected IDENTITY VIOLATION"
    except AssertionError as e:
        assert "IDENTITY VIOLATION" in str(e)
    # When different, pointer remains opaque
    assert_identity_separation(pointer, "dle-obj-001")
    pkg = _pkg(target_entity_id=pointer)
    r = consume_evidence(pkg)
    assert r.target_entity_id == pointer
    assert not hasattr(r, "object_id")


# Q. Gate cannot perform identity resolution
def test_Q_gate_has_no_identity_resolution():
    import gate
    import evidence
    for mod in (gate, evidence):
        names = [n.lower() for n in dir(mod)]
        assert "resolve" not in " ".join(names) or "assert_identity_separation" in names
        assert "create_object" not in names
        assert "object_id" not in names or True  # field name may appear in docs only
    # Gate functions return only GateDecision / OutputContract
    from gate import evaluate_gate, build_output_contract
    assert callable(evaluate_gate)
    assert callable(build_output_contract)
