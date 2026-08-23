
"""F04 — Unicode NFC pointer canonicalization (not semantic resolution)."""
from __future__ import annotations
import sys
from pathlib import Path

from contracts import (
    canonicalize_pointer,
    LifecycleCandidate,
    IdentifiedOntology,
    SemanticMode,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
    SourceSpan,
)
from gate import evaluate_gate
from evidence import package_evidence
from dle_core import DLECore


def _pkg(pointer: str, doc: str = "d"):
    cand = LifecycleCandidate(
        document_id=doc,
        identified_ontology=IdentifiedOntology(objects=["x"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=LifecycleStatus.POTENTIAL,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[SourceSpan("s", "t")],
        target_entity_id=pointer,
    )
    return package_evidence(cand, evaluate_gate(cand))


def test_nfc_equates_precomposed_and_decomposed():
    decomposed = "ent_e\u0301"   # e + combining acute
    precomposed = "ent_\u00e9"  # precomposed é
    assert decomposed != precomposed  # raw Python inequality
    assert canonicalize_pointer(decomposed) == canonicalize_pointer(precomposed)


def test_core_same_object_for_nfc_equivalent_pointers():
    core = DLECore()
    decomposed = "ent_e\u0301"
    precomposed = "ent_\u00e9"
    r1 = core.receive_evidence(_pkg(decomposed, "d1"))
    r2 = core.receive_evidence(_pkg(precomposed, "d2"))
    assert r1.object_id == r2.object_id


def test_distinct_unicode_remain_distinct():
    assert canonicalize_pointer("alpha") != canonicalize_pointer("beta")
    assert canonicalize_pointer("Entity\u00c5") != canonicalize_pointer("EntityA")


def test_nfkc_not_used_fullwidth_stays_distinct_under_nfc():
    fullwidth_a = "\uff21"  # FULLWIDTH LATIN CAPITAL A
    assert canonicalize_pointer(fullwidth_a) == fullwidth_a  # NFC does not collapse
    assert canonicalize_pointer(fullwidth_a) != "A"


def test_ascii_unchanged():
    assert canonicalize_pointer("ent_project_alpha") == "ent_project_alpha"


def test_none_pointer():
    assert canonicalize_pointer(None) is None


def test_no_semantic_alias_matching():
    assert canonicalize_pointer("Company ABC") != canonicalize_pointer("ABC Ltd.")
    assert canonicalize_pointer("ООО Ромашка") != canonicalize_pointer("Romashka LLC")
    assert canonicalize_pointer("Company ABC") != canonicalize_pointer("Company  ABC")


def test_package_evidence_applies_nfc():
    decomposed = "p_e\u0301"
    pkg = _pkg(decomposed)
    assert pkg is not None
    assert pkg.target_entity_id == canonicalize_pointer(decomposed)
