"""
Evidence packaging + identity separation + temporal data (GREEN only).
"""

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


def _candidate(**overrides) -> LifecycleCandidate:
    defaults = dict(
        document_id="doc-002",
        identified_ontology=IdentifiedOntology(objects=["contract"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=LifecycleStatus.POTENTIAL,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[SourceSpan(span_id="s1", text="действует до 31.12.2026")],
        target_entity_id="ext-entity-99",
        temporal=TemporalAttributes(
            effective_from="2024-01-01",
            expires_at="2026-12-31",
            sequence_id="seq-7",
        ),
    )
    defaults.update(overrides)
    return LifecycleCandidate(**defaults)


def test_package_on_activate():
    c = _candidate()
    decision = evaluate_gate(c)
    assert decision == GateDecision.ACTIVATE_DLE
    pkg = package_evidence(c, decision)
    assert isinstance(pkg, EvidencePackage)
    assert pkg.is_command is False
    assert pkg.target_entity_id == "ext-entity-99"
    assert pkg.lifecycle_status == LifecycleStatus.POTENTIAL
    assert pkg.temporal is not None
    assert pkg.temporal.expires_at == "2026-12-31"
    assert pkg.temporal.sequence_id == "seq-7"


def test_no_package_on_block():
    c = _candidate(lifecycle_status=LifecycleStatus.NONE)
    decision = evaluate_gate(c)
    assert decision == GateDecision.BLOCK_DLE
    pkg = package_evidence(c, decision)
    assert pkg is None


def test_no_package_on_human_review():
    c = _candidate(epistemic_uncertainty=EpistemicUncertainty.AMBIGUOUS)
    decision = evaluate_gate(c)
    assert decision == GateDecision.HUMAN_REVIEW
    pkg = package_evidence(c, decision)
    assert pkg is None


def test_evidence_never_command():
    c = _candidate()
    decision = evaluate_gate(c)
    pkg = package_evidence(c, decision)
    assert pkg is not None
    assert pkg.is_command is False
    # Potential stays descriptive
    assert pkg.lifecycle_status == LifecycleStatus.POTENTIAL


def test_identity_separation_ok():
    # Different IDs — must pass
    assert_identity_separation("ext-entity-99", "dle-obj-001")


def test_identity_separation_violation():
    try:
        assert_identity_separation("same-id", "same-id")
        assert False, "Should have raised"
    except AssertionError as e:
        assert "IDENTITY VIOLATION" in str(e)


def test_temporal_absolute_present():
    c = _candidate()
    assert c.temporal is not None
    assert c.temporal.expires_at == "2026-12-31"
    # relative_raw deliberately left None (YELLOW zone)
    assert c.temporal.relative_raw is None
