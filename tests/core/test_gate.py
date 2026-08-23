"""
Minimal Gate tests — frozen precedence matrix.
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
)
from gate import evaluate_gate, build_output_contract


def _base_candidate(**overrides) -> LifecycleCandidate:
    defaults = dict(
        document_id="doc-001",
        identified_ontology=IdentifiedOntology(objects=["passport"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=LifecycleStatus.ACTIVE,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[SourceSpan(span_id="s1", text="выдан 12.05.2024")],
        target_entity_id="entity-ext-42",
        temporal=TemporalAttributes(issued_at="2024-05-12"),
    )
    defaults.update(overrides)
    return LifecycleCandidate(**defaults)


def test_activate_happy_path():
    c = _base_candidate()
    assert evaluate_gate(c) == GateDecision.ACTIVATE_DLE


def test_human_review_on_ambiguous():
    c = _base_candidate(epistemic_uncertainty=EpistemicUncertainty.AMBIGUOUS)
    assert evaluate_gate(c) == GateDecision.HUMAN_REVIEW


def test_human_review_on_unknown():
    c = _base_candidate(epistemic_uncertainty=EpistemicUncertainty.UNKNOWN)
    assert evaluate_gate(c) == GateDecision.HUMAN_REVIEW


def test_block_on_unsupported():
    c = _base_candidate(grounding_status=GroundingStatus.UNSUPPORTED_INFERENCE)
    assert evaluate_gate(c) == GateDecision.BLOCK_DLE


def test_block_on_none_lifecycle():
    c = _base_candidate(lifecycle_status=LifecycleStatus.NONE)
    assert evaluate_gate(c) == GateDecision.BLOCK_DLE


def test_block_on_philosophical():
    c = _base_candidate(semantic_mode=SemanticMode.PHILOSOPHICAL)
    assert evaluate_gate(c) == GateDecision.BLOCK_DLE


def test_block_on_metaphorical():
    c = _base_candidate(semantic_mode=SemanticMode.METAPHORICAL)
    assert evaluate_gate(c) == GateDecision.BLOCK_DLE


def test_block_on_norm():
    c = _base_candidate(semantic_mode=SemanticMode.NORM)
    assert evaluate_gate(c) == GateDecision.BLOCK_DLE


def test_activate_on_potential():
    c = _base_candidate(lifecycle_status=LifecycleStatus.POTENTIAL)
    assert evaluate_gate(c) == GateDecision.ACTIVATE_DLE


def test_activate_on_historical():
    c = _base_candidate(lifecycle_status=LifecycleStatus.HISTORICAL)
    assert evaluate_gate(c) == GateDecision.ACTIVATE_DLE


def test_activate_on_obligation():
    c = _base_candidate(semantic_mode=SemanticMode.OBLIGATION)
    assert evaluate_gate(c) == GateDecision.ACTIVATE_DLE


def test_precedence_uncertainty_over_grounding():
    # Uncertainty wins even if grounding is bad
    c = _base_candidate(
        epistemic_uncertainty=EpistemicUncertainty.DISPUTED,
        grounding_status=GroundingStatus.UNSUPPORTED_INFERENCE,
    )
    assert evaluate_gate(c) == GateDecision.HUMAN_REVIEW


def test_output_contract_carries_decision():
    c = _base_candidate()
    contract = build_output_contract(c)
    assert contract.dle_eligibility_decision == GateDecision.ACTIVATE_DLE
    assert contract.document_id == "doc-001"
