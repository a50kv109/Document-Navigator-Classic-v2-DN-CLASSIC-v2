"""
DN CLASSIC — Upstream Pipeline Stages: Structure, Semantic Guard, and Assembly.
Guarantees deterministic validation of agent proposals and safe candidate assembly.
"""
from __future__ import annotations
from typing import List, Optional
from upstream_types import (
    AnalysisSnapshot,
    StructureRecord,
    AgentProposal,
    GuardStatus,
    GuardValidationResult,
)
from contracts import (
    LifecycleCandidate,
    SourceSpan,
    IdentifiedOntology,
    SemanticMode,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
)
from source_boundary import SourceDocument


def snapshot_to_structure(snapshot: AnalysisSnapshot) -> List[StructureRecord]:
    """Transforms an AnalysisSnapshot into structured document records."""
    records = []
    for source_id in sorted(snapshot.sources.keys()):
        src = snapshot.sources[source_id]
        records.append(StructureRecord(
            document_id=src.source_id,
            text=src.text_content,
            normalized_text=src.text_content,
            source_hash=src.sha256_hash,
            metadata={"total_bytes": len(src.raw_bytes)},
        ))
    return records


def validate_proposal_guard(proposal: AgentProposal, source_record: Optional[StructureRecord]) -> GuardValidationResult:
    """
    Deterministic Semantic Guard.
    Enforces that:
    1. Agent cannot inject executable commands (is_command must be False).
    2. Document source exists.
    3. SourceSpan coordinates strictly match text in the source document.
    4. Epistemic uncertainty and semantic fields are strictly typed.
    """
    # 1. Command injection protection
    if proposal.is_command:
        return GuardValidationResult(
            status=GuardStatus.REJECT,
            reason="Command injection violation: agent proposal attempted to set is_command=True",
        )

    # 2. Source document presence
    if source_record is None or source_record.document_id != proposal.document_id:
        return GuardValidationResult(
            status=GuardStatus.REJECT,
            reason=f"Missing or mismatched source document for document_id: {proposal.document_id}",
        )

    # 3. Verify SourceSpans
    source_doc = SourceDocument(
        document_id=source_record.document_id,
        text=source_record.normalized_text,
    )
    
    verified_spans: List[SourceSpan] = []
    for span in proposal.source_spans:
        # Check start and end boundaries
        if span.start is None or span.end is None:
            return GuardValidationResult(
                status=GuardStatus.REJECT,
                reason=f"Span '{span.span_id}' missing start/end offsets",
            )
        if not source_doc.verify_span(span.start, span.end, span.text):
            return GuardValidationResult(
                status=GuardStatus.REJECT,
                reason=f"Grounding failure: span '{span.span_id}' text '{span.text}' does not match source at [{span.start}:{span.end}]",
            )
        verified_spans.append(span)

    # 4. Uncertainty classification
    if proposal.epistemic_uncertainty in (EpistemicUncertainty.UNKNOWN, EpistemicUncertainty.AMBIGUOUS, EpistemicUncertainty.DISPUTED):
        return GuardValidationResult(
            status=GuardStatus.UNKNOWN,
            reason=f"Proposal marked with epistemic uncertainty: {proposal.epistemic_uncertainty.value}",
            verified_spans=verified_spans,
        )

    # 5. Passed all guard checks
    return GuardValidationResult(
        status=GuardStatus.ACCEPT,
        reason="Guard passed: schema valid, spans grounded, non-executable",
        verified_spans=verified_spans,
    )


def assemble_candidate(proposal: AgentProposal, validation: GuardValidationResult) -> Optional[LifecycleCandidate]:
    """
    Assembles a validated AgentProposal into a typed LifecycleCandidate.
    Returns None if validation is not ACCEPT.
    """
    if validation.status != GuardStatus.ACCEPT:
        return None

    ontology = proposal.identified_ontology or IdentifiedOntology()
    
    return LifecycleCandidate(
        document_id=proposal.document_id,
        identified_ontology=ontology,
        semantic_mode=proposal.semantic_mode,
        lifecycle_status=proposal.lifecycle_status,
        grounding_status=proposal.grounding_status,
        epistemic_uncertainty=proposal.epistemic_uncertainty,
        source_spans=validation.verified_spans,
        candidate_evidence_refs=list(proposal.candidate_evidence_refs),
        target_entity_id=proposal.target_entity_id,
        temporal=proposal.temporal,
    )
