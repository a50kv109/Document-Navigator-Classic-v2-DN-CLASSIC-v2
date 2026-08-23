"""
DN CLASSIC — Upstream Stages & Semantic Guard Test Suite.
Verifies structure conversion, deterministic span grounding validation,
command injection prevention, and typed candidate assembly.
"""
import pytest

from upstream_types import (
    ReadOnlySource,
    AnalysisSnapshot,
    StructureRecord,
    AgentProposal,
    GuardStatus,
    ProposalSet,
)
from upstream_stages import (
    snapshot_to_structure,
    validate_proposal_guard,
    assemble_candidate,
)
from contracts import (
    SemanticMode,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
    SourceSpan,
    LifecycleCandidate,
)


def test_snapshot_to_structure():
    src1 = ReadOnlySource(
        source_id="doc1.txt",
        raw_bytes=b"Content 1",
        text_content="Content 1",
        sha256_hash="hash1",
    )
    snapshot = AnalysisSnapshot(
        snapshot_id="snap1",
        sources={"doc1.txt": src1},
        total_bytes=9,
        computed_hash="snaphash",
    )
    records = snapshot_to_structure(snapshot)
    assert len(records) == 1
    assert records[0].document_id == "doc1.txt"
    assert records[0].normalized_text == "Content 1"
    assert records[0].source_hash == "hash1"


def test_guard_accepts_valid_proposal():
    text = "The tenant shall pay rent on the first day."
    target_phrase = "pay rent on the first day"
    start_idx = text.find(target_phrase)
    end_idx = start_idx + len(target_phrase)
    
    rec = StructureRecord(
        document_id="policy.txt",
        text=text,
        normalized_text=text,
        source_hash="polhash",
    )
    span = SourceSpan(
        span_id="s1",
        text=target_phrase,
        start=start_idx,
        end=end_idx,
    )
    proposal = AgentProposal(
        document_id="policy.txt",
        target_entity_id="policy.txt",
        semantic_mode=SemanticMode.OBLIGATION,
        lifecycle_status=LifecycleStatus.ACTIVE,
        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
        source_spans=[span],
    )
    
    val = validate_proposal_guard(proposal, rec)
    assert val.status == GuardStatus.ACCEPT
    assert len(val.verified_spans) == 1
    
    cand = assemble_candidate(proposal, val)
    assert cand is not None
    assert isinstance(cand, LifecycleCandidate)
    assert cand.document_id == "policy.txt"
    assert cand.semantic_mode == SemanticMode.OBLIGATION


def test_guard_rejects_command_injection():
    rec = StructureRecord(
        document_id="doc.txt",
        text="Sample text",
        normalized_text="Sample text",
        source_hash="dh",
    )
    proposal = AgentProposal(
        document_id="doc.txt",
        is_command=True,  # Attempted command injection
    )
    val = validate_proposal_guard(proposal, rec)
    assert val.status == GuardStatus.REJECT
    assert "Command injection violation" in val.reason
    assert assemble_candidate(proposal, val) is None


def test_guard_rejects_ungrounded_span_text():
    rec = StructureRecord(
        document_id="doc.txt",
        text="Actual text in source document",
        normalized_text="Actual text in source document",
        source_hash="dh",
    )
    span = SourceSpan(
        span_id="s1",
        text="Fabricated claim not in text",
        start=0,
        end=27,
    )
    proposal = AgentProposal(
        document_id="doc.txt",
        source_spans=[span],
    )
    val = validate_proposal_guard(proposal, rec)
    assert val.status == GuardStatus.REJECT
    assert "Grounding failure" in val.reason


def test_guard_rejects_out_of_bounds_span():
    rec = StructureRecord(
        document_id="doc.txt",
        text="Short text",
        normalized_text="Short text",
        source_hash="dh",
    )
    span = SourceSpan(
        span_id="s1",
        text="Short text",
        start=0,
        end=50,  # Beyond length of text
    )
    proposal = AgentProposal(
        document_id="doc.txt",
        source_spans=[span],
    )
    val = validate_proposal_guard(proposal, rec)
    assert val.status == GuardStatus.REJECT
    assert "Grounding failure" in val.reason


def test_guard_rejects_missing_document():
    proposal = AgentProposal(
        document_id="nonexistent.txt",
    )
    val = validate_proposal_guard(proposal, None)
    assert val.status == GuardStatus.REJECT
    assert "Missing or mismatched source document" in val.reason


def test_guard_handles_uncertainty():
    rec = StructureRecord(
        document_id="doc.txt",
        text="Some uncertain statement",
        normalized_text="Some uncertain statement",
        source_hash="dh",
    )
    span = SourceSpan(
        span_id="s1",
        text="Some uncertain statement",
        start=0,
        end=24,
    )
    proposal = AgentProposal(
        document_id="doc.txt",
        epistemic_uncertainty=EpistemicUncertainty.AMBIGUOUS,
        source_spans=[span],
    )
    val = validate_proposal_guard(proposal, rec)
    assert val.status == GuardStatus.UNKNOWN
    assert "epistemic uncertainty" in val.reason
    # Assembly returns None for non-ACCEPT guard results
    assert assemble_candidate(proposal, val) is None
