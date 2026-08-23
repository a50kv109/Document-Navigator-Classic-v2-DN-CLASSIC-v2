"""
DN CLASSIC — Deterministic DLE Gate (GREEN).
Sole admission boundary. Pure function. No side effects.
"""

from __future__ import annotations

from contracts import (
    LifecycleCandidate,
    OutputContract,
    GateDecision,
    SemanticMode,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
)


def evaluate_gate(candidate: LifecycleCandidate) -> GateDecision:
    """
    Apply the frozen precedence matrix (highest first):

    1. epistemic_uncertainty ≠ CLEAR          → HUMAN_REVIEW
    2. grounding_status = UNSUPPORTED_INFERENCE → BLOCK_DLE
    3. lifecycle_status = NONE                → BLOCK_DLE
    4. semantic_mode ∈ {NORM, PHILOSOPHICAL, METAPHORICAL} → BLOCK_DLE
    5. otherwise (GROUNDED + CLAIM|OBLIGATION + ACTIVE|HISTORICAL|POTENTIAL + CLEAR)
                                              → ACTIVATE_DLE
    """
    # 1. Uncertainty first
    if candidate.epistemic_uncertainty != EpistemicUncertainty.CLEAR:
        return GateDecision.HUMAN_REVIEW

    # 2. Unsupported inference
    if candidate.grounding_status == GroundingStatus.UNSUPPORTED_INFERENCE:
        return GateDecision.BLOCK_DLE

    # 3. No lifecycle
    if candidate.lifecycle_status == LifecycleStatus.NONE:
        return GateDecision.BLOCK_DLE

    # 4. Non-operational semantic modes
    if candidate.semantic_mode in (
        SemanticMode.NORM,
        SemanticMode.PHILOSOPHICAL,
        SemanticMode.METAPHORICAL,
    ):
        return GateDecision.BLOCK_DLE

    # 5. Remaining cases are admissible
    # (CLAIM or OBLIGATION) + (ACTIVE|HISTORICAL|POTENTIAL) + GROUNDED + CLEAR
    return GateDecision.ACTIVATE_DLE


def build_output_contract(candidate: LifecycleCandidate) -> OutputContract:
    """Assemble the typed Output Contract after Gate evaluation."""
    decision = evaluate_gate(candidate)
    return OutputContract(
        document_id=candidate.document_id,
        identified_ontology=candidate.identified_ontology,
        semantic_mode=candidate.semantic_mode,
        lifecycle_status=candidate.lifecycle_status,
        grounding_status=candidate.grounding_status,
        epistemic_uncertainty=candidate.epistemic_uncertainty,
        dle_eligibility_decision=decision,
        source_spans=list(candidate.source_spans),
        candidate_evidence_refs=list(candidate.candidate_evidence_refs),
    )
