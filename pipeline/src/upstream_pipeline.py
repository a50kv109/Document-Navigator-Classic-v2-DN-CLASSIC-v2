"""
DN CLASSIC — Upstream Pipeline Execution Engine.
Coordinates reading archives, transforming snapshots to structure,
invoking the agent proposer hook, executing semantic guard validation,
assembling candidates, evaluating the frozen Gate, packaging evidence,
and routing to DLE Core.
"""
from __future__ import annotations
import unicodedata
from typing import List, Optional, Callable, Dict, Any

from contracts import (
    LifecycleCandidate,
    OutputContract,
    EvidencePackage,
    GateDecision,
    SemanticMode,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
    SourceSpan,
)
from gate import evaluate_gate, build_output_contract
from evidence import package_evidence
from consumption_boundary import consume_evidence, BoundaryReceipt
from source_boundary import SourceDocument
from archive_adapter import read_archive_or_directory
from upstream_types import (
    AnalysisSnapshot,
    StructureRecord,
    AgentProposal,
    ProposalSet,
    GuardedProposal,
    GuardStatus,
    PipelineExecutionResult,
)
from upstream_stages import (
    snapshot_to_structure,
    validate_proposal_guard,
    assemble_candidate,
)


def normalize_text(text: str) -> str:
    """
    Deterministic text normalization.
    Uses NFC to match CORE's canonicalization strategy.
    """
    return unicodedata.normalize("NFC", text)


def default_proposer_hook(records: List[StructureRecord]) -> ProposalSet:
    """
    Default deterministic baseline proposer hook.
    Proposes grounded claim candidates across parsed documents.
    """
    proposals: List[AgentProposal] = []
    for r in records:
        if not r.normalized_text.strip():
            continue
        # Default proposal anchors the entire non-empty document text as a span
        span = SourceSpan(
            span_id=f"{r.document_id}-span-0",
            text=r.normalized_text,
            start=0,
            end=len(r.normalized_text),
        )
        proposals.append(
            AgentProposal(
                document_id=r.document_id,
                target_entity_id=r.document_id,
                semantic_mode=SemanticMode.CLAIM,
                lifecycle_status=LifecycleStatus.ACTIVE,
                grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
                epistemic_uncertainty=EpistemicUncertainty.CLEAR,
                source_spans=[span],
            )
        )
    return ProposalSet(proposals=proposals, agent_id="default-baseline-agent")


def process_archive(
    source_input: str,
    proposer_hook: Optional[Callable[[List[StructureRecord]], ProposalSet]] = None,
    dle_instance: Optional[Any] = None,
) -> PipelineExecutionResult:
    """
    Primary public execution entrypoint for DN CLASSIC.
    
    Stages:
    1. Input/Archive → Snapshot (via archive_adapter)
    2. Snapshot → Structure Records (via snapshot_to_structure)
    3. Structure Records → ProposalSet (via proposer_hook)
    4. ProposalSet → Guarded Proposals (via validate_proposal_guard)
    5. Guarded Proposals → Lifecycle Candidates (via assemble_candidate)
    6. Lifecycle Candidates → Output Contracts & Gate Evaluation (via evaluate_gate / build_output_contract)
    7. Gate Evaluation → Evidence Packages (via package_evidence)
    8. Evidence Packages → DLE Processing (via dle_instance or consumption boundary)
    """
    # 1. Read archive into deterministic snapshot
    snapshot: AnalysisSnapshot = read_archive_or_directory(source_input)

    # 2. Extract structure records
    records: List[StructureRecord] = snapshot_to_structure(snapshot)
    records_by_id: Dict[str, StructureRecord] = {r.document_id: r for r in records}

    # 3. Invoke agent proposer hook (or default)
    active_hook = proposer_hook if proposer_hook is not None else default_proposer_hook
    proposal_set: ProposalSet = active_hook(records)

    # 4 & 5. Guard validation and Candidate assembly
    guarded_proposals: List[GuardedProposal] = []
    candidates: List[LifecycleCandidate] = []

    for proposal in proposal_set.proposals:
        source_rec = records_by_id.get(proposal.document_id)
        val_result = validate_proposal_guard(proposal, source_rec)
        guarded_proposals.append(GuardedProposal(proposal=proposal, validation=val_result))

        if val_result.status == GuardStatus.ACCEPT:
            cand = assemble_candidate(proposal, val_result)
            if cand is not None:
                candidates.append(cand)

    # 6 & 7. Gate evaluation and Evidence packaging
    output_contracts: List[OutputContract] = []
    evidence_packages: List[EvidencePackage] = []

    for cand in candidates:
        contract = build_output_contract(cand)
        output_contracts.append(contract)
        
        evidence = package_evidence(cand, contract.dle_eligibility_decision)
        if evidence is not None:
            evidence_packages.append(evidence)

    # 8. DLE Processing
    dle_receipts: List[Any] = []
    for pkg in evidence_packages:
        if dle_instance is not None:
            if hasattr(dle_instance, "receive_evidence"):
                receipt = dle_instance.receive_evidence(pkg)
                dle_receipts.append(receipt)
            elif hasattr(dle_instance, "process_evidence"):
                receipt = dle_instance.process_evidence(pkg)
                dle_receipts.append(receipt)
        else:
            receipt = consume_evidence(pkg)
            dle_receipts.append(receipt)

    return PipelineExecutionResult(
        snapshot=snapshot,
        structure_records=records,
        proposals=proposal_set,
        guarded_proposals=guarded_proposals,
        candidates=candidates,
        output_contracts=output_contracts,
        evidence_packages=evidence_packages,
        dle_receipts=dle_receipts,
    )
