"""
DN CLASSIC — End-to-End Archive Processing Test Suite.
Verifies complete flow:
Archive → Snapshot → Structure → Agent Proposer → Guard → Assembly → Gate → Evidence → DLE
"""
import zipfile
import pytest

from upstream_pipeline import process_archive
from upstream_types import AgentProposal, ProposalSet, StructureRecord
from contracts import (
    SemanticMode,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
    SourceSpan,
    GateDecision,
)
from dle_core import DLECore, ObjectState


def test_process_archive_default_e2e(tmp_path):
    zip_path = str(tmp_path / "dataset.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("doc1.txt", "Tenant agrees to pay 1000 USD on 1st of month.".encode("utf-8"))
        zf.writestr("doc2.txt", "Landlord agrees to maintain heating.".encode("utf-8"))
        zf.writestr("image.png", b"\x89PNGfake")

    result = process_archive(zip_path)
    
    # Verify snapshot & structure extraction
    assert len(result.snapshot.sources) == 2
    assert len(result.structure_records) == 2
    
    # Verify proposals & guard
    assert len(result.proposals.proposals) == 2
    assert len(result.candidates) == 2
    
    # Verify gate evaluations
    assert len(result.output_contracts) == 2
    for contract in result.output_contracts:
        assert contract.dle_eligibility_decision == GateDecision.ACTIVATE_DLE
        
    # Verify evidence packages
    assert len(result.evidence_packages) == 2
    for pkg in result.evidence_packages:
        assert pkg.is_command is False
        assert pkg.lifecycle_status == LifecycleStatus.ACTIVE
        
    # Verify DLE receipts
    assert len(result.dle_receipts) == 2
    for receipt in result.dle_receipts:
        assert receipt.accepted is True


def test_process_archive_with_dle_instance(tmp_path):
    zip_path = str(tmp_path / "contracts.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("contract_01.txt", "Obligation statement for contract.".encode("utf-8"))

    dle = DLECore()
    
    result = process_archive(zip_path, dle_instance=dle)
    
    assert len(result.evidence_packages) == 1
    assert len(result.dle_receipts) == 1
    
    receipt = result.dle_receipts[0]
    assert receipt.accepted is True
    assert receipt.state_after == ObjectState.IN_PROGRESS
    assert receipt.transition is not None
    assert receipt.transition.transition_name == "REGISTER_ACTIVE"


def test_process_archive_with_rejected_proposals(tmp_path):
    zip_path = str(tmp_path / "adversarial.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("terms.txt", "Normal contract terms.".encode("utf-8"))

    def adversarial_agent(records):
        return ProposalSet(
            proposals=[
                # Proposal 1: command injection attempt -> REJECT by Guard
                AgentProposal(
                    document_id="terms.txt",
                    is_command=True,
                ),
                # Proposal 2: span text mismatch -> REJECT by Guard
                AgentProposal(
                    document_id="terms.txt",
                    source_spans=[
                        SourceSpan(
                            span_id="fakespan",
                            text="Hallucinated text",
                            start=0,
                            end=17,
                        )
                    ],
                ),
                # Proposal 3: NORM semantic mode with valid span -> ACCEPT by Guard, BLOCK by Gate
                AgentProposal(
                    document_id="terms.txt",
                    target_entity_id="terms.txt",
                    semantic_mode=SemanticMode.NORM,
                    lifecycle_status=LifecycleStatus.ACTIVE,
                    grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
                    epistemic_uncertainty=EpistemicUncertainty.CLEAR,
                    source_spans=[
                        SourceSpan(
                            span_id="normspan",
                            text="Normal contract terms.",
                            start=0,
                            end=22,
                        )
                    ],
                ),
            ]
        )

    result = process_archive(zip_path, proposer_hook=adversarial_agent)
    
    assert len(result.guarded_proposals) == 3
    # 2 rejected by Guard, 1 accepted by Guard
    assert len(result.candidates) == 1
    assert result.candidates[0].semantic_mode == SemanticMode.NORM
    
    # 1 candidate reached Gate, and was BLOCKED
    assert len(result.output_contracts) == 1
    assert result.output_contracts[0].dle_eligibility_decision == GateDecision.BLOCK_DLE
    
    # Zero evidence packages produced
    assert len(result.evidence_packages) == 0
    assert len(result.dle_receipts) == 0
