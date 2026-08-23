"""
DN CLASSIC — Standalone process_archive entrypoint module.
"""
from upstream_pipeline import process_archive, default_proposer_hook
from upstream_types import PipelineExecutionResult, AnalysisSnapshot, StructureRecord, ProposalSet, AgentProposal

__all__ = [
    "process_archive",
    "default_proposer_hook",
    "PipelineExecutionResult",
    "AnalysisSnapshot",
    "StructureRecord",
    "ProposalSet",
    "AgentProposal",
]
