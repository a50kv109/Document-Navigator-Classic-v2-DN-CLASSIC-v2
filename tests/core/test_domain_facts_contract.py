"""Production tests for approved domain_facts contract."""
from __future__ import annotations
import sys
from pathlib import Path

from contracts import (
    EvidencePackage, LifecycleStatus, GroundingStatus, EpistemicUncertainty,
    SourceSpan, TemporalAttributes,
)
from dle_core import (
    DLECore, ObjectState, DLEObject,
    condition_model_a_extinguishment, condition_model_b_survival,
    condition_complete_work, TRANSITION_RULES,
)
import inspect


def _ep(**kwargs) -> EvidencePackage:
    base = dict(
        document_id="d1",
        target_entity_id="ent_o1",
        lifecycle_status=LifecycleStatus.HISTORICAL,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[SourceSpan("s", "t")],
        temporal=None,
        candidate_evidence_refs=[],
        is_command=False,
    )
    base.update(kwargs)
    return EvidencePackage(**base)


def test_evidence_without_domain_facts():
    ep = _ep()
    assert ep.domain_facts is None


def test_evidence_with_domain_facts():
    facts = {"performed": "2026-09-12", "due": "2026-09-15"}
    ep = _ep(domain_facts=facts)
    assert ep.domain_facts == facts


def test_model_a_false():
    ep = _ep(domain_facts={
        "terminated": "2026-09-10",
        "performed": "2026-09-12",
        "due": "2026-09-15",
    })
    obj = DLEObject(object_id="dle-obj-1", semantic_pointer="ent_o1", state=ObjectState.IN_PROGRESS)
    assert condition_model_a_extinguishment(ep, obj) is False


def test_model_b_true():
    ep = _ep(domain_facts={
        "terminated": "2026-09-10",
        "performed": "2026-09-12",
        "due": "2026-09-15",
    })
    obj = DLEObject(object_id="dle-obj-1", semantic_pointer="ent_o1", state=ObjectState.IN_PROGRESS)
    assert condition_model_b_survival(ep, obj) is True


def test_missing_facts_false():
    obj = DLEObject(object_id="dle-obj-1", semantic_pointer="ent_o1", state=ObjectState.IN_PROGRESS)
    assert condition_model_a_extinguishment(_ep(), obj) is False
    assert condition_model_b_survival(_ep(), obj) is False


def test_empty_facts_false():
    obj = DLEObject(object_id="dle-obj-1", semantic_pointer="ent_o1", state=ObjectState.IN_PROGRESS)
    assert condition_model_a_extinguishment(_ep(domain_facts={}), obj) is False
    assert condition_model_b_survival(_ep(domain_facts={}), obj) is False


def test_existing_arity2_conditions_valid():
    sig = inspect.signature(condition_complete_work)
    assert list(sig.parameters) == ["evidence", "obj"]
    sig_a = inspect.signature(condition_model_a_extinguishment)
    assert list(sig_a.parameters) == ["evidence", "obj"]


def test_core_blind_to_domain_facts():
    """Core receive_evidence must not branch on domain_facts keys."""
    src = inspect.getsource(DLECore.receive_evidence)
    assert "domain_facts" not in src
    core = DLECore()
    from contracts import LifecycleStatus as LS
    ep_active = _ep(
        lifecycle_status=LS.ACTIVE,
        domain_facts={"noise": "should_be_ignored_by_core"},
    )
    r1 = core.receive_evidence(ep_active)
    assert r1.object_id is not None
    ep_hist = _ep(
        lifecycle_status=LS.HISTORICAL,
        domain_facts={"performed": "2026-09-12", "due": "2026-09-15"},
    )
    core.receive_evidence(ep_hist)  # must not raise


def test_five_primitives_unchanged():
    # structural: no new engine modules; TRANSITION_RULES still 6
    assert len(TRANSITION_RULES) == 6
    names = {r.name for r in TRANSITION_RULES}
    assert "ACKNOWLEDGE_POTENTIAL" in names
    # Model A/B not auto-registered (no architecture expansion of default graph)
    assert "MODEL_A" not in names
    assert "MODEL_B" not in names


def test_no_failed_unknown_engines():
    import dle_core as m
    src = Path(m.__file__).read_text()
    assert "TemporalEngine" not in src
    assert "RuleEngine" not in src
    assert "ObjectState.FAILED" not in src
    assert "ObjectState.UNKNOWN" not in src


def test_same_facts_a_false_b_true():
    facts = {
        "terminated": "2026-09-10",
        "performed": "2026-09-12",
        "due": "2026-09-15",
    }
    ep = _ep(domain_facts=facts)
    obj = DLEObject(object_id="dle-obj-9", semantic_pointer="ent_o1", state=ObjectState.IN_PROGRESS)
    assert condition_model_a_extinguishment(ep, obj) is False
    assert condition_model_b_survival(ep, obj) is True
