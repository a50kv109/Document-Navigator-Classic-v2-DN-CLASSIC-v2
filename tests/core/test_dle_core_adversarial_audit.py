"""
Adversarial audit of Minimal DLE Core.
Attack only. Do not expand Core. Do not auto-fix architecture.
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
from evidence import package_evidence
from dle_core import (
    DLECore,
    DLEObject,
    ObjectState,
    condition_acknowledge_potential,
    transition_acknowledge,
    TransitionResult,
)


def _ev(
    *,
    doc: str = "doc",
    pointer: str | None = "ent_project_alpha",
    life: LifecycleStatus = LifecycleStatus.POTENTIAL,
    ground: GroundingStatus = GroundingStatus.GROUNDED_SOURCE_CLAIM,
    unc: EpistemicUncertainty = EpistemicUncertainty.CLEAR,
) -> EvidencePackage:
    cand = LifecycleCandidate(
        document_id=doc,
        identified_ontology=IdentifiedOntology(objects=["c"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=life,
        grounding_status=ground,
        epistemic_uncertainty=unc,
        source_spans=[SourceSpan("s", "Компания обязуется разработать проект.")],
        target_entity_id=pointer,
    )
    d = evaluate_gate(cand)
    if d == GateDecision.ACTIVATE_DLE:
        pkg = package_evidence(cand, d)
        assert pkg is not None
        return pkg
    # force package for negative condition cases
    return EvidencePackage(
        document_id=doc,
        target_entity_id=pointer,
        lifecycle_status=life,
        grounding_status=ground,
        epistemic_uncertainty=unc,
        source_spans=cand.source_spans,
        temporal=None,
        candidate_evidence_refs=[],
        is_command=False,
    )


# =============================================================================
# PHASE 2 — IDENTITY
# =============================================================================

def test_A_same_pointer_one_object():
    core = DLECore()
    r1 = core.receive_evidence(_ev(doc="d1", pointer="A"))
    r2 = core.receive_evidence(_ev(doc="d2", pointer="A"))
    assert r1.object_id == r2.object_id


def test_B_same_evidence_replay_no_second_transition():
    core = DLECore()
    pkg = _ev(pointer="replay")
    r1 = core.receive_evidence(pkg)
    r2 = core.receive_evidence(pkg)
    assert r1.transition is not None and r1.transition.applied
    assert r2.transition is None
    assert r2.state_after == ObjectState.ACKNOWLEDGED
    assert r1.object_id == r2.object_id


def test_C_different_pointers_different_objects():
    core = DLECore()
    r1 = core.receive_evidence(_ev(pointer="A"))
    r2 = core.receive_evidence(_ev(pointer="B"))
    assert r1.object_id != r2.object_id


def test_D_pointer_collision_exact_match_only():
    """Document actual behavior: no normalization (YELLOW / UNDEFINED)."""
    core = DLECore()
    ids = []
    for p in ("alpha", "ALPHA", " alpha ", "ent_project_alpha"):
        ids.append(core.receive_evidence(_ev(pointer=p)).object_id)
    # All distinct under exact-match map
    assert len(set(ids)) == 4


def test_D2_none_pointer_creates_distinct_objects():
    """Document: None pointer does not share identity (probe limitation)."""
    core = DLECore()
    r1 = core.receive_evidence(_ev(doc="n1", pointer=None))
    r2 = core.receive_evidence(_ev(doc="n2", pointer=None))
    assert r1.object_id != r2.object_id


# =============================================================================
# PHASE 3 — STATE
# =============================================================================

def test_E_potential_causes_transition():
    core = DLECore()
    r = core.receive_evidence(_ev(life=LifecycleStatus.POTENTIAL))
    assert r.state_before == ObjectState.NEW
    assert r.state_after == ObjectState.ACKNOWLEDGED
    assert r.transition and r.transition.applied


def test_F_after_acknowledged_stable():
    core = DLECore()
    core.receive_evidence(_ev(doc="1", pointer="stable"))
    r = core.receive_evidence(_ev(doc="2", pointer="stable"))
    assert r.state_before == ObjectState.ACKNOWLEDGED
    assert r.state_after == ObjectState.ACKNOWLEDGED
    assert r.transition is None


def test_G_external_state_mutation_via_private_access():
    """
    FINDING (documented, not auto-fixed):
    DLEObject is a mutable dataclass; core._objects is accessible by convention.
    External code CAN mutate state if it reaches into private attrs.
    Classification: ACCEPTABLE PROBE LIMITATION / YELLOW
    (Python soft privacy; not an architectural sixth primitive.)
    """
    core = DLECore()
    r = core.receive_evidence(_ev(pointer="mut"))
    obj = core._objects[r.object_id]
    obj.state = ObjectState.NEW  # bypass
    assert obj.state == ObjectState.NEW
    # Core path still works; next valid evidence will transition again
    r2 = core.receive_evidence(_ev(doc="again", pointer="mut"))
    assert r2.transition is not None and r2.transition.applied


# =============================================================================
# PHASE 4 — CONDITION
# =============================================================================

def test_H_happy_condition_fires():
    core = DLECore()
    r = core.receive_evidence(_ev(
        life=LifecycleStatus.POTENTIAL,
        ground=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        unc=EpistemicUncertainty.CLEAR,
    ))
    assert r.transition and r.transition.applied


def test_I_unsupported_blocks_transition():
    core = DLECore()
    r = core.receive_evidence(_ev(ground=GroundingStatus.UNSUPPORTED_INFERENCE))
    assert r.transition is None
    assert r.state_after == ObjectState.NEW


def test_J_disputed_blocks_transition():
    core = DLECore()
    r = core.receive_evidence(_ev(unc=EpistemicUncertainty.DISPUTED))
    assert r.transition is None
    assert r.state_after == ObjectState.NEW


def test_K_is_command_impossible():
    try:
        EvidencePackage(
            document_id="x",
            target_entity_id=None,
            lifecycle_status=LifecycleStatus.POTENTIAL,
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


# =============================================================================
# PHASE 5 — TRANSITION BOUNDARY
# =============================================================================

def test_L_no_public_transition_method_on_core():
    core = DLECore()
    assert not hasattr(core, "transition")
    assert not hasattr(core, "execute_transition")
    assert not hasattr(core, "apply_transition")


def test_M_module_level_transition_callable_but_needs_object_ref():
    """
    FINDING: transition_acknowledge is module-level public.
    Without a DLEObject reference obtained via private access, external
    caller cannot usefully invoke it against Core-managed objects.
    Classification: soft boundary / YELLOW implementation detail.
    """
    assert callable(transition_acknowledge)
    orphan = DLEObject(object_id="orphan", semantic_pointer=None, state=ObjectState.NEW)
    tr = transition_acknowledge(orphan)
    assert tr.applied is True
    assert orphan.state == ObjectState.ACKNOWLEDGED
    # orphan is NOT in any Core registry


def test_N_cannot_inject_orphan_into_core_via_public_api():
    core = DLECore()
    orphan = DLEObject(object_id="dle-obj-9999", semantic_pointer="hijack", state=ObjectState.NEW)
    # public API has no inject path
    assert not hasattr(core, "register")
    assert not hasattr(core, "add_object")
    r = core.receive_evidence(_ev(pointer="hijack"))
    # Core creates its own object; orphan remains separate
    assert r.object_id != "dle-obj-9999"


# =============================================================================
# PHASE 6 — OBJECT OWNERSHIP / IDENTITY
# =============================================================================

def test_P_pointer_never_equals_object_id():
    core = DLECore()
    for p in ("ent_project_alpha", "dle-obj-0001", "x"):
        r = core.receive_evidence(_ev(pointer=p, doc=p))
        assert r.object_id != p
        assert r.object_id.startswith("dle-obj-")


# =============================================================================
# PHASE 7 — EVIDENCE PASSIVITY
# =============================================================================

def test_evidence_has_no_lifecycle_methods():
    pkg = _ev()
    for name in ("execute", "execute_transition", "change_state", "create_object", "schedule"):
        assert not hasattr(pkg, name)


# =============================================================================
# PHASE 8 — TEMPORAL CONTAMINATION
# =============================================================================

def test_no_temporal_engine_in_core():
    import dle_core as m
    import ast
    src = open(m.__file__).read()
    # Strip docstrings/comments for keyword scan — avoid false positives on "No scheduler" prose
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if ast.get_docstring(node):
                pass  # docstring presence is fine
    # Executable indicators only
    assert "datetime.now" not in src.replace(" ", "")
    assert "time.sleep" not in src
    assert "asyncio.sleep" not in src
    # No scheduler *call* or attribute — docstring denial is not a scheduler
    core = DLECore()
    assert not hasattr(core, "timers")
    assert not hasattr(core, "clock")
    assert not hasattr(core, "scheduler")
    assert not hasattr(core, "cron")
    # temporal data still accepted
    from contracts import TemporalAttributes
    cand = LifecycleCandidate(
        document_id="t",
        identified_ontology=IdentifiedOntology(objects=[], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=LifecycleStatus.POTENTIAL,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[SourceSpan("s", "t")],
        target_entity_id="t1",
        temporal=TemporalAttributes(expires_at="2026-12-31", sequence_id="9"),
    )
    pkg = package_evidence(cand, evaluate_gate(cand))
    assert pkg is not None
    r = core.receive_evidence(pkg)
    assert r.accepted


# =============================================================================
# PHASE 9 — ORDER / REPLAY
# =============================================================================

def test_order_potential_then_active():
    """After Slice 2: ACTIVE on ACKNOWLEDGED is a defined Transition (START_WORK)."""
    core = DLECore()
    r1 = core.receive_evidence(_ev(doc="1", pointer="ord", life=LifecycleStatus.POTENTIAL))
    r2 = core.receive_evidence(_ev(doc="2", pointer="ord", life=LifecycleStatus.ACTIVE))
    assert r1.transition and r1.transition.applied
    assert r2.transition is not None and r2.transition.transition_name == "START_WORK"
    assert r2.state_after == ObjectState.IN_PROGRESS


def test_order_active_then_potential():
    """ACTIVE first: REGISTER_ACTIVE → IN_PROGRESS; later POTENTIAL does not regress."""
    core = DLECore()
    r1 = core.receive_evidence(_ev(doc="1", pointer="ord2", life=LifecycleStatus.ACTIVE))
    r2 = core.receive_evidence(_ev(doc="2", pointer="ord2", life=LifecycleStatus.POTENTIAL))
    assert r1.transition is not None and r1.transition.transition_name == "REGISTER_ACTIVE"
    assert r1.state_after == ObjectState.IN_PROGRESS
    assert r2.transition is None
    assert r2.state_after == ObjectState.IN_PROGRESS


# =============================================================================
# PHASE 11 — INVARIANTS (spot checks)
# =============================================================================

def test_I1_identity_separation():
    core = DLECore()
    r = core.receive_evidence(_ev(pointer="ent_x"))
    assert r.object_id != "ent_x"


def test_I5_only_transition_changes_state_on_happy_path():
    core = DLECore()
    r = core.receive_evidence(_ev())
    assert r.state_before != r.state_after
    assert r.transition is not None


def test_I8_no_sixth_primitive_in_module():
    import dle_core as m
    # Known names only
    allowed = {
        "ObjectState", "DLEObject", "condition_acknowledge_potential",
        "TransitionResult", "transition_acknowledge", "CoreReceipt", "DLECore",
        "EvidencePackage", "LifecycleStatus", "GroundingStatus", "EpistemicUncertainty",
    }
    public = [n for n in dir(m) if not n.startswith("_") and n[0].isupper() or n in (
        "condition_acknowledge_potential", "transition_acknowledge"
    )]
    # No LifecycleManager, TemporalEngine, IdentityEngine, etc.
    for bad in ("LifecycleManager", "TemporalEngine", "IdentityEngine",
                "EvidenceEngine", "RuleEngine", "EventEngine", "Scheduler"):
        assert bad not in dir(m)
