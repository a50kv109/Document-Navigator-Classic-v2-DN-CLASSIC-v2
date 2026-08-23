"""
DN CLASSIC — Evidence packaging (GREEN).
Passive only. Never creates Objects, never issues Transitions.
"""

from __future__ import annotations

from contracts import (
    LifecycleCandidate,
    EvidencePackage,
    GateDecision,
    LifecycleStatus,
    canonicalize_pointer,
)


def package_evidence(candidate: LifecycleCandidate, decision: GateDecision) -> EvidencePackage | None:
    """
    Build an EvidencePackage only when Gate admits the candidate.
    If decision is not ACTIVATE_DLE the package is not produced.
    Evidence remains descriptive data; is_command is always False.
    """
    if decision != GateDecision.ACTIVATE_DLE:
        return None

    return EvidencePackage(
        document_id=candidate.document_id,
        target_entity_id=canonicalize_pointer(candidate.target_entity_id),
        lifecycle_status=candidate.lifecycle_status,
        grounding_status=candidate.grounding_status,
        epistemic_uncertainty=candidate.epistemic_uncertainty,
        source_spans=list(candidate.source_spans),
        temporal=candidate.temporal,
        candidate_evidence_refs=list(candidate.candidate_evidence_refs),
        is_command=False,
    )


def assert_identity_separation(target_entity_id: str | None, dle_object_id: str | None) -> None:
    """
    HARD INVARIANT: target_entity_id is never a DLE Object ID.
    This function exists solely to make the boundary testable.
    Real DLE Core (when it exists) owns Object identity resolution.
    """
    if target_entity_id is not None and dle_object_id is not None:
        if target_entity_id == dle_object_id:
            raise AssertionError(
                "IDENTITY VIOLATION: target_entity_id must not equal DLE Object ID"
            )
