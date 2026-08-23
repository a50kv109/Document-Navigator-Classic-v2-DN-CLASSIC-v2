"""
DN CLASSIC — Minimal decision trace (GREEN).
Audit record of Gate decisions. No architectural weight.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timezone

from contracts import GateDecision, LifecycleCandidate, OutputContract


@dataclass(frozen=True)
class DecisionRecord:
    document_id: str
    decision: GateDecision
    timestamp_utc: str
    reason_summary: str


@dataclass
class DecisionTrace:
    records: List[DecisionRecord] = field(default_factory=list)

    def record(self, candidate: LifecycleCandidate, contract: OutputContract) -> None:
        reason = _summarise(candidate, contract.dle_eligibility_decision)
        rec = DecisionRecord(
            document_id=candidate.document_id,
            decision=contract.dle_eligibility_decision,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            reason_summary=reason,
        )
        self.records.append(rec)


def _summarise(candidate: LifecycleCandidate, decision: GateDecision) -> str:
    return (
        f"mode={candidate.semantic_mode.value} "
        f"life={candidate.lifecycle_status.value} "
        f"ground={candidate.grounding_status.value} "
        f"unc={candidate.epistemic_uncertainty.value} "
        f"→ {decision.value}"
    )
