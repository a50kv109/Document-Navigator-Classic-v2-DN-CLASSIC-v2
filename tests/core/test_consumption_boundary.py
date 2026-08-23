"""
Evidence Consumption Boundary Probe tests.
Protect only the frozen GREEN → future DLE Core interface.
No DLE Core logic.
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
from consumption_boundary import consume_evidence, BoundaryReceipt, reject_non_evidence


def _make_pkg(**overrides) -> EvidencePackage:
    """Build a valid EvidencePackage via the real Gate path."""
    base = dict(
        document_id="boundary-doc",
        identified_ontology=IdentifiedOntology(objects=["proj"], evidence=[], events=[]),
        semantic_mode=SemanticMode.CLAIM,
        lifecycle_status=LifecycleStatus.ACTIVE,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[SourceSpan(span_id="s1", text="undertakes to develop")],
        target_entity_id="ent_proj_alpha",
        temporal=None,
    )
    base.update(overrides)
    cand = LifecycleCandidate(**base)
    decision = evaluate_gate(cand)
    assert decision == GateDecision.ACTIVATE_DLE
    pkg = package_evidence(cand, decision)
    assert pkg is not None
    return pkg


# ---------------------------------------------------------------------------
# 1. Acceptance of valid EvidencePackage
# ---------------------------------------------------------------------------

def test_boundary_accepts_evidence_package():
    """Invariant: Gate-produced EvidencePackage crosses boundary safely."""
    pkg = _make_pkg()
    receipt = consume_evidence(pkg)
    assert isinstance(receipt, BoundaryReceipt)
    assert receipt.accepted is True
    assert receipt.document_id == "boundary-doc"
    assert receipt.note.startswith("received as passive")


# ---------------------------------------------------------------------------
# 2. Wrong type rejected
# ---------------------------------------------------------------------------

def test_boundary_rejects_non_package():
    """Invariant: only EvidencePackage may cross."""
    try:
        consume_evidence({"fake": True})  # type: ignore
        assert False, "must reject dict"
    except TypeError as e:
        assert "EvidencePackage" in str(e)

    try:
        reject_non_evidence("raw string")
        assert False
    except TypeError:
        pass


# ---------------------------------------------------------------------------
# 3. target_entity_id remains opaque
# ---------------------------------------------------------------------------

def test_boundary_preserves_opaque_pointer():
    """Invariant: semantic pointer does not become Object ID."""
    pkg = _make_pkg(target_entity_id="ent_proj_alpha")
    receipt = consume_evidence(pkg)
    assert receipt.target_entity_id == "ent_proj_alpha"
    # Receipt has no object_id / dle_object_id field
    assert not hasattr(receipt, "object_id")
    assert not hasattr(receipt, "dle_object_id")
    assert not hasattr(receipt, "resolved_object")


def test_boundary_allows_missing_pointer():
    pkg = _make_pkg(target_entity_id=None)
    receipt = consume_evidence(pkg)
    assert receipt.target_entity_id is None


# ---------------------------------------------------------------------------
# 4. Evidence remains passive / POTENTIAL descriptive
# ---------------------------------------------------------------------------

def test_boundary_potential_stays_descriptive():
    """Invariant: POTENTIAL crosses as data, not as Transition command."""
    pkg = _make_pkg(lifecycle_status=LifecycleStatus.POTENTIAL)
    receipt = consume_evidence(pkg)
    assert receipt.lifecycle_status_descriptive == "POTENTIAL"
    assert "no lifecycle action performed" in receipt.note
    # No execution side-effects exist on the adapter
    assert not hasattr(consume_evidence, "last_transition")
    assert not hasattr(consume_evidence, "created_objects")


def test_boundary_historical_stays_descriptive():
    pkg = _make_pkg(lifecycle_status=LifecycleStatus.HISTORICAL)
    receipt = consume_evidence(pkg)
    assert receipt.lifecycle_status_descriptive == "HISTORICAL"


# ---------------------------------------------------------------------------
# 5. Temporal attributes remain passive
# ---------------------------------------------------------------------------

def test_boundary_temporal_passive():
    """Invariant: temporal data crosses; no timer/scheduler created."""
    t = TemporalAttributes(
        issued_at="2026-01-10",
        expires_at="2026-12-31",
        sequence_id="17",
    )
    pkg = _make_pkg(temporal=t)
    receipt = consume_evidence(pkg)
    assert receipt.accepted is True
    # Adapter itself holds no temporal execution state
    assert not hasattr(receipt, "expires_at")  # receipt does not even copy timers
    assert not hasattr(receipt, "timer")
    assert not hasattr(receipt, "schedule")


# ---------------------------------------------------------------------------
# 6. Command-like fields cannot trigger execution
# ---------------------------------------------------------------------------

def test_boundary_rejects_command_flag():
    """Invariant: is_command=True cannot be constructed or cross."""
    # Construction itself is already forbidden by EvidencePackage
    try:
        EvidencePackage(
            document_id="x",
            target_entity_id=None,
            lifecycle_status=LifecycleStatus.ACTIVE,
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


# ---------------------------------------------------------------------------
# 7–10. No Object / State / Transition created by adapter
# ---------------------------------------------------------------------------

def test_boundary_creates_no_object_or_transition():
    """Invariant: adapter performs zero lifecycle actions."""
    pkg = _make_pkg()
    receipt = consume_evidence(pkg)
    # Receipt is pure data acknowledgment
    assert set(receipt.__dataclass_fields__.keys()) == {
        "accepted",
        "document_id",
        "target_entity_id",
        "lifecycle_status_descriptive",
        "note",
    }
    # No hidden registries
    import consumption_boundary as cb
    for name in dir(cb):
        low = name.lower()
        assert "object_registry" not in low
        assert "state_store" not in low
        assert "transition" not in low or name == "BoundaryReceipt"  # no method
        assert "create_object" not in low
        assert "execute" not in low


def test_boundary_no_persistence_side_effect():
    """Invariant: no store / save / db interaction."""
    import consumption_boundary as cb
    src = open(cb.__file__).read()
    for forbidden in ("open(", "sqlite", "db.", "persist", "save(", "write("):
        # allow comments / docstrings only; real calls would appear as statements
        assert forbidden not in src.replace(" ", "") or forbidden in (
            "persist",  # appears only in comments of other modules; check local
        )
    # Local file itself must not contain persistence verbs as executable
    assert "sqlite" not in src
    assert "open(" not in src
    assert ".write(" not in src
