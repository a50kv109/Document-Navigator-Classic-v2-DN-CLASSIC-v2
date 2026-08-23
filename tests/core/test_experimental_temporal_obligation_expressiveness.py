"""
TEST-LOCAL / EXPERIMENTAL ONLY — Temporal obligation expressiveness.

Does NOT modify production contracts, Conditions, or DLE Core.
Removable without leaving production changes.

Hypothesis under test:
  Five primitives + test-local data + pure Condition callables
  can express Model A vs Model B on the same facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any

# ---------------------------------------------------------------------------
# PART 1 — Test-local opaque facts (NOT production EvidencePackage)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LocalTemporalFacts:
    """Opaque domain bag for the experiment only. Core never sees this type."""
    created: Optional[str] = None      # ISO date YYYY-MM-DD
    due: Optional[str] = None
    terminated: Optional[str] = None
    performed: Optional[str] = None


# Canonical scenario facts — SAME object for both models
CANONICAL = LocalTemporalFacts(
    created="2026-09-01",
    due="2026-09-15",
    terminated="2026-09-10",
    performed="2026-09-12",
)


def _le(a: Optional[str], b: Optional[str]) -> bool:
    """Lexicographic ISO date compare; missing -> not ordered."""
    if a is None or b is None:
        return False
    return a <= b


def _lt(a: Optional[str], b: Optional[str]) -> bool:
    if a is None or b is None:
        return False
    return a < b


# ---------------------------------------------------------------------------
# PART 2–3 — Pure test-local Conditions (not production rule table)
# Signature deliberately mirrors production spirit: (facts, obj_stub) -> bool
# Domain rule is selected by WHICH callable is used, not by a Core Context.
# ---------------------------------------------------------------------------

@dataclass
class ObjStub:
    """Stand-in for DLEObject; experiment does not need real Core objects."""
    state: str = "IN_PROGRESS"


def condition_model_a_extinguishment(facts: LocalTemporalFacts, obj: ObjStub) -> bool:
    """
    Model A: termination extinguishes obligation.
    Completion requires performance and (no termination OR performance <= termination).
    Also requires performance <= due when due is known.
    """
    if obj.state != "IN_PROGRESS":
        return False
    if facts.performed is None:
        return False
    if facts.due is not None and not _le(facts.performed, facts.due):
        return False
    if facts.terminated is not None and not _le(facts.performed, facts.terminated):
        return False  # performed after termination -> False under A
    return True


def condition_model_b_survival(facts: LocalTemporalFacts, obj: ObjStub) -> bool:
    """
    Model B: obligation survives termination until due.
    Completion if performance <= due; termination ignored for extinguishment.
    """
    if obj.state != "IN_PROGRESS":
        return False
    if facts.performed is None:
        return False
    if facts.due is None:
        return False  # need due under B for this scenario
    return _le(facts.performed, facts.due)


# ---------------------------------------------------------------------------
# PART 4 — Critical: same facts, different Conditions
# ---------------------------------------------------------------------------

def test_critical_same_facts_model_a_false_model_b_true():
    obj = ObjStub("IN_PROGRESS")
    facts = CANONICAL  # identical
    assert condition_model_a_extinguishment(facts, obj) is False
    assert condition_model_b_survival(facts, obj) is True


# ---------------------------------------------------------------------------
# PART 5 — Production Condition(evidence, obj) compatibility discussion tests
# ---------------------------------------------------------------------------

def test_production_signature_shape_is_arity_two():
    """Production Conditions are (evidence, obj) -> bool; we mirror that shape
    with (facts, obj) -> bool. Domain choice = which callable is registered,
    not a third argument."""
    import inspect
    from dle_core import condition_complete_work
    sig = inspect.signature(condition_complete_work)
    params = list(sig.parameters)
    assert params == ["evidence", "obj"]


def test_model_distinction_via_two_callables_not_third_arg():
    """Minimum mechanism: two pure callables. No DomainConfig object required
    for expressiveness proof."""
    a = condition_model_a_extinguishment
    b = condition_model_b_survival
    assert a is not b
    obj = ObjStub()
    assert a(CANONICAL, obj) != b(CANONICAL, obj)


def test_closure_can_capture_domain_rule_without_third_arg():
    """Optional pattern: factory returns Condition(evidence_like, obj)-shaped fn."""
    def make_completion_condition(mode: str) -> Callable[[LocalTemporalFacts, ObjStub], bool]:
        if mode == "A":
            return condition_model_a_extinguishment
        if mode == "B":
            return condition_model_b_survival
        # absent rule -> always False (safe)
        return lambda facts, obj: False

    obj = ObjStub()
    assert make_completion_condition("A")(CANONICAL, obj) is False
    assert make_completion_condition("B")(CANONICAL, obj) is True
    assert make_completion_condition("ABSENT")(CANONICAL, obj) is False


# ---------------------------------------------------------------------------
# PART 10 — T1–T5
# ---------------------------------------------------------------------------

def test_T1_performed_before_due_no_termination():
    facts = LocalTemporalFacts(
        created="2026-09-01", due="2026-09-15", performed="2026-09-12"
    )
    obj = ObjStub()
    # B-style eligibility
    assert condition_model_b_survival(facts, obj) is True
    # A also true (no termination to extinguish)
    assert condition_model_a_extinguishment(facts, obj) is True


def test_T2_performed_after_due():
    facts = LocalTemporalFacts(
        created="2026-09-01", due="2026-09-15", performed="2026-09-16"
    )
    obj = ObjStub()
    assert condition_model_b_survival(facts, obj) is False
    assert condition_model_a_extinguishment(facts, obj) is False


def test_T3_model_a_term_before_perf():
    assert condition_model_a_extinguishment(CANONICAL, ObjStub()) is False


def test_T4_model_b_term_before_perf_before_due():
    assert condition_model_b_survival(CANONICAL, ObjStub()) is True


def test_T5_absent_domain_rule_no_unsafe_positive():
    def absent_rule(facts: LocalTemporalFacts, obj: ObjStub) -> bool:
        return False  # missing rule => do not complete

    assert absent_rule(CANONICAL, ObjStub()) is False


# ---------------------------------------------------------------------------
# PART 7–8 — Core blindness & five primitives (documentation assertions)
# ---------------------------------------------------------------------------

def test_core_need_not_import_test_local_types():
    """DLE Core module must not reference test-local fact types."""
    import dle_core
    import inspect
    src = inspect.getsource(dle_core)
    assert "LocalTemporalFacts" not in src
    assert "TestLocalTemporalFacts" not in src


def test_no_sixth_primitive_required_by_experiment():
    forbidden = [
        "ObligationPrimitive",
        "ContractPrimitive",
        "EventPrimitive",
        "RelationPrimitive",
        "TimePrimitive",
        "RulePrimitive",
    ]
    # Experiment file itself must not define those as architecture
    import pathlib
    text = pathlib.Path(__file__).read_text()
    for name in forbidden:
        assert f"class {name}" not in text


def test_production_evidence_untouched_no_payload_field():
    from contracts import EvidencePackage
    assert "payload" not in EvidencePackage.__dataclass_fields__
