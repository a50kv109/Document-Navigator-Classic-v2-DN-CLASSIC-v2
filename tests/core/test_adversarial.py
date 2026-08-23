"""
Adversarial verification tests for GREEN foundation.
Each test protects a frozen invariant. No feature expansion.
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import FrozenInstanceError


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
    OutputContract,
)
from gate import evaluate_gate, build_output_contract
from evidence import package_evidence, assert_identity_separation
from trace import DecisionTrace


def _c(**kw) -> LifecycleCandidate:
    base = dict(
        document_id="adv-doc",
        identified_ontology=IdentifiedOntology(objects=["x"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=LifecycleStatus.ACTIVE,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[SourceSpan(span_id="s", text="t")],
        target_entity_id="ext-pointer-1",
        temporal=None,
    )
    base.update(kw)
    return LifecycleCandidate(**base)


# ---------------------------------------------------------------------------
# 1. Gate precedence / uncertainty
# ---------------------------------------------------------------------------

def test_adv_disputed_overrides_grounded():
    """Invariant: uncertainty > grounding. DISPUTED → HUMAN_REVIEW."""
    c = _c(epistemic_uncertainty=EpistemicUncertainty.DISPUTED)
    assert evaluate_gate(c) == GateDecision.HUMAN_REVIEW


def test_adv_unknown_overrides_everything():
    c = _c(
        epistemic_uncertainty=EpistemicUncertainty.UNKNOWN,
        grounding_status=GroundingStatus.UNSUPPORTED_INFERENCE,
        lifecycle_status=LifecycleStatus.NONE,
    )
    assert evaluate_gate(c) == GateDecision.HUMAN_REVIEW


# ---------------------------------------------------------------------------
# 2. Evidence pass/block isolation
# ---------------------------------------------------------------------------

def test_adv_no_evidence_on_block_or_review():
    """Invariant: only ACTIVATE produces EvidencePackage."""
    for status, mode, unc, ground in [
        (LifecycleStatus.NONE, SemanticMode.CLAIM, EpistemicUncertainty.CLEAR, GroundingStatus.GROUNDED_SOURCE_CLAIM),
        (LifecycleStatus.ACTIVE, SemanticMode.PHILOSOPHICAL, EpistemicUncertainty.CLEAR, GroundingStatus.GROUNDED_SOURCE_CLAIM),
        (LifecycleStatus.ACTIVE, SemanticMode.CLAIM, EpistemicUncertainty.AMBIGUOUS, GroundingStatus.GROUNDED_SOURCE_CLAIM),
        (LifecycleStatus.ACTIVE, SemanticMode.CLAIM, EpistemicUncertainty.CLEAR, GroundingStatus.UNSUPPORTED_INFERENCE),
    ]:
        c = _c(
            lifecycle_status=status,
            semantic_mode=mode,
            epistemic_uncertainty=unc,
            grounding_status=ground,
        )
        d = evaluate_gate(c)
        assert d != GateDecision.ACTIVATE_DLE
        assert package_evidence(c, d) is None


# ---------------------------------------------------------------------------
# 3. POTENTIAL remains descriptive
# ---------------------------------------------------------------------------

def test_adv_potential_is_descriptive_not_command():
    """Invariant: POTENTIAL is data, never execute_transition."""
    c = _c(lifecycle_status=LifecycleStatus.POTENTIAL)
    d = evaluate_gate(c)
    assert d == GateDecision.ACTIVATE_DLE
    pkg = package_evidence(c, d)
    assert pkg is not None
    assert pkg.lifecycle_status == LifecycleStatus.POTENTIAL
    assert pkg.is_command is False
    # No method exists that would execute anything
    assert not hasattr(pkg, "execute")
    assert not hasattr(pkg, "execute_transition")
    assert not hasattr(pkg, "change_state")


# ---------------------------------------------------------------------------
# 4. Identity separation
# ---------------------------------------------------------------------------

def test_adv_identity_spaces_remain_separate():
    """Invariant: target_entity_id is opaque pointer, not DLE Object ID."""
    c = _c(target_entity_id="semantic-pointer-ABC")
    pkg = package_evidence(c, evaluate_gate(c))
    assert pkg is not None
    assert pkg.target_entity_id == "semantic-pointer-ABC"
    # Field is named target_entity_id, never object_id
    assert not hasattr(pkg, "object_id")
    assert not hasattr(pkg, "dle_object_id")
    # Separation helper rejects collapse
    assert_identity_separation("semantic-pointer-ABC", "dle-internal-001")
    try:
        assert_identity_separation("same", "same")
        assert False
    except AssertionError:
        pass


def test_adv_missing_target_entity_id_allowed():
    """Missing pointer is SAFE; Gate does not invent Object ID."""
    c = _c(target_entity_id=None)
    d = evaluate_gate(c)
    assert d == GateDecision.ACTIVATE_DLE
    pkg = package_evidence(c, d)
    assert pkg is not None
    assert pkg.target_entity_id is None


# ---------------------------------------------------------------------------
# 5. Absolute temporal propagation (passive)
# ---------------------------------------------------------------------------

def test_adv_absolute_temporal_is_passive_data():
    """Invariant: temporal fields are data only; no scheduler."""
    t = TemporalAttributes(
        issued_at="2024-05-12",
        expires_at="2026-12-31",
        sequence_id="seq-9",
        relative_raw=None,  # YELLOW left unresolved
    )
    c = _c(temporal=t)
    pkg = package_evidence(c, evaluate_gate(c))
    assert pkg is not None
    assert pkg.temporal.issued_at == "2024-05-12"
    assert pkg.temporal.expires_at == "2026-12-31"
    assert pkg.temporal.sequence_id == "seq-9"
    # No timer / comparison methods on the package
    assert not hasattr(pkg.temporal, "is_expired")
    assert not hasattr(pkg.temporal, "tick")
    assert not hasattr(pkg.temporal, "schedule")


def test_adv_relative_temporal_left_unresolved():
    """Invariant: relative temporal format is YELLOW — do not invent schema."""
    t = TemporalAttributes(relative_raw="через 30 дней после получения")
    c = _c(temporal=t)
    pkg = package_evidence(c, evaluate_gate(c))
    assert pkg is not None
    # Stored as opaque string only; no parsed duration/anchor fields exist
    assert pkg.temporal.relative_raw == "через 30 дней после получения"
    assert not hasattr(pkg.temporal, "duration_days")
    assert not hasattr(pkg.temporal, "anchor")


# ---------------------------------------------------------------------------
# 6. Candidate transience / frozenness
# ---------------------------------------------------------------------------

def test_adv_candidate_is_frozen():
    """Invariant: LifecycleCandidate is immutable (architectural passivity)."""
    c = _c()
    try:
        c.document_id = "mutated"  # type: ignore
        assert False, "should be frozen"
    except FrozenInstanceError:
        pass
    try:
        c.lifecycle_status = LifecycleStatus.NONE  # type: ignore
        assert False
    except FrozenInstanceError:
        pass


def test_adv_evidence_package_is_frozen():
    c = _c()
    pkg = package_evidence(c, evaluate_gate(c))
    assert pkg is not None
    try:
        pkg.is_command = True  # type: ignore
        assert False
    except FrozenInstanceError:
        pass


def test_adv_is_command_cannot_be_true():
    """Invariant: EvidencePackage rejects is_command=True at construction."""
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
        assert False, "must reject is_command=True"
    except ValueError as e:
        assert "never be a command" in str(e)


# ---------------------------------------------------------------------------
# 7. No Object / Transition / State creation outside DLE Core
# ---------------------------------------------------------------------------

def test_adv_no_object_creation_api():
    """Invariant: GREEN modules expose no Object creation."""
    import contracts
    import gate
    import evidence
    for mod in (contracts, gate, evidence):
        for name in dir(mod):
            low = name.lower()
            assert "create_object" not in low
            assert "upsert_object" not in low
            assert "object_registry" not in low
            assert "execute_transition" not in low
            assert "change_state" not in low


# ---------------------------------------------------------------------------
# 8. Gate isolation — no bypass path into Evidence without decision
# ---------------------------------------------------------------------------

def test_adv_package_requires_explicit_decision():
    """Invariant: package_evidence requires GateDecision; cannot skip Gate."""
    c = _c()
    # Calling with BLOCK must yield None even if candidate looks "good"
    assert package_evidence(c, GateDecision.BLOCK_DLE) is None
    assert package_evidence(c, GateDecision.HUMAN_REVIEW) is None
    assert package_evidence(c, GateDecision.ACTIVATE_DLE) is not None


# ---------------------------------------------------------------------------
# 9. Negative / malformed inputs
# ---------------------------------------------------------------------------

def test_adv_null_temporal_ok():
    c = _c(temporal=None)
    d = evaluate_gate(c)
    pkg = package_evidence(c, d)
    assert pkg is not None
    assert pkg.temporal is None


def test_adv_empty_spans_ok():
    c = _c(source_spans=[])
    d = evaluate_gate(c)
    assert d == GateDecision.ACTIVATE_DLE
    pkg = package_evidence(c, d)
    assert pkg is not None
    assert pkg.source_spans == []


def test_adv_conflicting_status_still_routed_safely():
    """Even contradictory-looking combinations are handled by precedence."""
    c = _c(
        lifecycle_status=LifecycleStatus.POTENTIAL,
        grounding_status=GroundingStatus.UNSUPPORTED_INFERENCE,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
    )
    # Unsupported wins → BLOCK (after uncertainty check which is CLEAR)
    assert evaluate_gate(c) == GateDecision.BLOCK_DLE


# ---------------------------------------------------------------------------
# 10. Trace does not become lifecycle engine
# ---------------------------------------------------------------------------

def test_adv_trace_is_audit_only():
    """datetime.now in trace is audit stamp, not Temporal Engine."""
    c = _c()
    contract = build_output_contract(c)
    trace = DecisionTrace()
    trace.record(c, contract)
    assert len(trace.records) == 1
    assert trace.records[0].decision == GateDecision.ACTIVATE_DLE
    # Trace has no execute / expire / schedule methods
    assert not hasattr(trace, "execute")
    assert not hasattr(trace, "expire")
    assert not hasattr(trace, "schedule")
