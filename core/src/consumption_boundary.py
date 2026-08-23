"""
DN CLASSIC — Evidence Consumption Boundary Probe (GREEN → future DLE Core)

This module demonstrates ONLY the architectural boundary:

    EvidencePackage  →  [future DLE Core]

It does NOT implement DLE Core.
It does NOT create Object / State / Transition.
It does NOT resolve identity.
It does NOT evaluate Condition.
It does NOT execute anything.
It does NOT persist.
It does NOT schedule.

Implementation Gate remains CLOSED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from contracts import EvidencePackage, LifecycleStatus


@dataclass(frozen=True)
class BoundaryReceipt:
    """
    Pure acknowledgment that a passive EvidencePackage crossed the boundary.
    Contains no Object ID, no State, no Transition result.
    Exists solely to make the hand-off testable.
    """
    accepted: bool
    document_id: str
    target_entity_id: Optional[str]   # still the opaque semantic pointer
    lifecycle_status_descriptive: str  # copied as data only
    note: str = "received as passive evidence; no lifecycle action performed"


def consume_evidence(package: EvidencePackage) -> BoundaryReceipt:
    """
    Minimal conceptual adapter.

    INPUT:  EvidencePackage (passive proof produced by Gate)
    OUTPUT: BoundaryReceipt (acknowledgment only)

    Ownership after this call is conceptual only:
    future DLE Core would own interpretation.
    This function performs ZERO lifecycle semantics.
    """
    if not isinstance(package, EvidencePackage):
        raise TypeError(
            "Boundary accepts only EvidencePackage; "
            f"got {type(package).__name__}"
        )

    if package.is_command:
        # Defensive: contract already forbids this, but boundary re-asserts
        raise ValueError("EvidencePackage with is_command=True cannot cross boundary")

    # No Object creation, no State mutation, no Transition, no identity mapping.
    # We deliberately do not inspect or interpret lifecycle_status beyond copying.
    return BoundaryReceipt(
        accepted=True,
        document_id=package.document_id,
        target_entity_id=package.target_entity_id,  # opaque pointer preserved
        lifecycle_status_descriptive=package.lifecycle_status.value,
        note="received as passive evidence; no lifecycle action performed",
    )


def reject_non_evidence(payload: Any) -> None:
    """
    Explicit negative path: anything that is not EvidencePackage is rejected.
    Used only by tests to prove isolation.
    """
    if isinstance(payload, EvidencePackage):
        raise AssertionError("reject_non_evidence called with valid EvidencePackage")
    # Simply do nothing / raise if caller expects rejection
    raise TypeError(f"Not an EvidencePackage: {type(payload).__name__}")
