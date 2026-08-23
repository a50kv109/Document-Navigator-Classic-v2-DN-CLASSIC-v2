"""
DN CLASSIC — DLE CORE RUNTIME (Functional Sufficiency Expansion)

Exactly five primitives: Object, State, Transition, Condition, Evidence.
DLECore is the orchestrator — NOT a sixth primitive.

Lifecycle graph (earned edges only):

  NEW --ACKNOWLEDGE_POTENTIAL--> ACKNOWLEDGED
  NEW --REGISTER_ACTIVE--------> IN_PROGRESS
  NEW --REGISTER_CLOSED--------> COMPLETED
  ACKNOWLEDGED --START_WORK----> IN_PROGRESS
  ACKNOWLEDGED --CLOSE_ACK-----> COMPLETED
  IN_PROGRESS --COMPLETE_WORK--> COMPLETED

FAILED terminal is NOT YET EARNED: EvidencePackage cannot distinguish
failure vs successful closure without GREEN contract extension or
semantic collapse (forbidden).

No Temporal Engine. No persistence. No scheduler.
Implementation Gate remains CLOSED for production.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable
from enum import Enum

from contracts import (
    EvidencePackage,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
    canonicalize_pointer,
)


class ObjectState(str, Enum):
    """
    Durable Object lifecycle states.
    COMPLETED is terminal success/closure for current rule set.
    FAILED not introduced — not discriminable from Evidence enums alone.
    """
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


@dataclass
class DLEObject:
    """Core-owned identity. Managed instances created only inside Core."""
    object_id: str
    semantic_pointer: Optional[str]
    state: ObjectState = ObjectState.NEW
    evidence_log: List[str] = field(default_factory=list)


def _base_ok(evidence: EvidencePackage) -> bool:
    return (
        evidence.grounding_status == GroundingStatus.GROUNDED_SOURCE_CLAIM
        and evidence.epistemic_uncertainty == EpistemicUncertainty.CLEAR
        and evidence.is_command is False
    )


def condition_acknowledge_potential(evidence: EvidencePackage, obj: DLEObject) -> bool:
    return (
        _base_ok(evidence)
        and evidence.lifecycle_status == LifecycleStatus.POTENTIAL
        and obj.state == ObjectState.NEW
    )


def condition_register_active(evidence: EvidencePackage, obj: DLEObject) -> bool:
    return (
        _base_ok(evidence)
        and evidence.lifecycle_status == LifecycleStatus.ACTIVE
        and obj.state == ObjectState.NEW
    )


def condition_register_closed(evidence: EvidencePackage, obj: DLEObject) -> bool:
    return (
        _base_ok(evidence)
        and evidence.lifecycle_status == LifecycleStatus.HISTORICAL
        and obj.state == ObjectState.NEW
    )


def condition_start_work(evidence: EvidencePackage, obj: DLEObject) -> bool:
    return (
        _base_ok(evidence)
        and evidence.lifecycle_status == LifecycleStatus.ACTIVE
        and obj.state == ObjectState.ACKNOWLEDGED
    )


def condition_close_acknowledged(evidence: EvidencePackage, obj: DLEObject) -> bool:
    return (
        _base_ok(evidence)
        and evidence.lifecycle_status == LifecycleStatus.HISTORICAL
        and obj.state == ObjectState.ACKNOWLEDGED
    )


def condition_complete_work(evidence: EvidencePackage, obj: DLEObject) -> bool:
    return (
        _base_ok(evidence)
        and evidence.lifecycle_status == LifecycleStatus.HISTORICAL
        and obj.state == ObjectState.IN_PROGRESS
    )


# ---------------------------------------------------------------------------
# Domain temporal Conditions (approved contract consumers of domain_facts).
# NOT registered in TRANSITION_RULES — application may register as needed.
# Core remains key-blind; these pure predicates interpret domain_facts only.
# ---------------------------------------------------------------------------

def _facts(evidence: EvidencePackage) -> dict:
    return evidence.domain_facts or {}


def condition_model_a_extinguishment(evidence: EvidencePackage, obj: DLEObject) -> bool:
    """Model A: termination extinguishes obligation.
    Requires performance; if termination exists, performance must be <= termination.
    Also requires performance <= due when due is present.
    Missing keys => False (fail closed).
    """
    if obj.state != ObjectState.IN_PROGRESS:
        return False
    f = _facts(evidence)
    performed = f.get("performed")
    if not performed:
        return False
    due = f.get("due")
    if due is not None and not (performed <= due):
        return False
    terminated = f.get("terminated")
    if terminated is not None and not (performed <= terminated):
        return False
    return True


def condition_model_b_survival(evidence: EvidencePackage, obj: DLEObject) -> bool:
    """Model B: obligation survives termination until due.
    Completion if performance <= due; termination ignored for extinguishment.
    Missing performed or due => False.
    """
    if obj.state != ObjectState.IN_PROGRESS:
        return False
    f = _facts(evidence)
    performed = f.get("performed")
    due = f.get("due")
    if not performed or not due:
        return False
    return performed <= due



@dataclass(frozen=True)
class TransitionResult:
    applied: bool
    transition_name: str
    from_state: ObjectState
    to_state: Optional[ObjectState]
    reason: str


@dataclass(frozen=True)
class TransitionRule:
    name: str
    from_state: ObjectState
    to_state: ObjectState
    condition: Callable[[EvidencePackage, DLEObject], bool]


def transition_acknowledge(obj: DLEObject) -> TransitionResult:
    if obj.state != ObjectState.NEW:
        return TransitionResult(
            applied=False,
            transition_name="ACKNOWLEDGE_POTENTIAL",
            from_state=obj.state,
            to_state=None,
            reason="object not in NEW state",
        )
    old = obj.state
    obj.state = ObjectState.ACKNOWLEDGED
    return TransitionResult(
        applied=True,
        transition_name="ACKNOWLEDGE_POTENTIAL",
        from_state=old,
        to_state=ObjectState.ACKNOWLEDGED,
        reason="condition satisfied",
    )


TRANSITION_RULES: List[TransitionRule] = [
    TransitionRule("ACKNOWLEDGE_POTENTIAL", ObjectState.NEW, ObjectState.ACKNOWLEDGED, condition_acknowledge_potential),
    TransitionRule("REGISTER_ACTIVE", ObjectState.NEW, ObjectState.IN_PROGRESS, condition_register_active),
    TransitionRule("REGISTER_CLOSED", ObjectState.NEW, ObjectState.COMPLETED, condition_register_closed),
    TransitionRule("START_WORK", ObjectState.ACKNOWLEDGED, ObjectState.IN_PROGRESS, condition_start_work),
    TransitionRule("CLOSE_ACKNOWLEDGED", ObjectState.ACKNOWLEDGED, ObjectState.COMPLETED, condition_close_acknowledged),
    TransitionRule("COMPLETE_WORK", ObjectState.IN_PROGRESS, ObjectState.COMPLETED, condition_complete_work),
]


@dataclass
class CoreReceipt:
    accepted: bool
    object_id: Optional[str]
    state_before: Optional[ObjectState]
    state_after: Optional[ObjectState]
    transition: Optional[TransitionResult]
    note: str


class DLECore:
    def __init__(self) -> None:
        self._objects: Dict[str, DLEObject] = {}
        self._pointer_map: Dict[str, str] = {}
        self._next_id = 1

    def _resolve_or_create(self, pointer: Optional[str]) -> DLEObject:
        pointer = canonicalize_pointer(pointer)
        if pointer is not None and pointer in self._pointer_map:
            return self._objects[self._pointer_map[pointer]]
        oid = f"dle-obj-{self._next_id:04d}"
        self._next_id += 1
        obj = DLEObject(object_id=oid, semantic_pointer=pointer, state=ObjectState.NEW)
        self._objects[oid] = obj
        if pointer is not None:
            self._pointer_map[pointer] = oid
        return obj

    def receive_evidence(self, evidence: EvidencePackage) -> CoreReceipt:
        if not isinstance(evidence, EvidencePackage):
            raise TypeError("DLE Core accepts only EvidencePackage")
        if evidence.is_command:
            raise ValueError("Evidence must not be a command")

        obj = self._resolve_or_create(evidence.target_entity_id)
        state_before = obj.state
        obj.evidence_log.append(evidence.document_id)

        for rule in TRANSITION_RULES:
            if obj.state == rule.from_state and rule.condition(evidence, obj):
                old = obj.state
                obj.state = rule.to_state
                tr = TransitionResult(
                    applied=True,
                    transition_name=rule.name,
                    from_state=old,
                    to_state=rule.to_state,
                    reason="condition satisfied",
                )
                return CoreReceipt(
                    accepted=True,
                    object_id=obj.object_id,
                    state_before=state_before,
                    state_after=obj.state,
                    transition=tr,
                    note=f"Condition satisfied; Transition {rule.name} applied",
                )

        return CoreReceipt(
            accepted=True,
            object_id=obj.object_id,
            state_before=state_before,
            state_after=obj.state,
            transition=None,
            note="Evidence stored as data; no Condition matched; no Transition",
        )
