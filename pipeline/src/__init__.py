"""
DN CLASSIC PIPELINE package.
"""
from upstream_types import (
    ReadOnlySource,
    AnalysisSnapshot,
    StructureRecord,
    AgentProposal,
    GuardStatus,
    GuardValidationResult,
    ProposalSet,
    GuardedProposal,
    PipelineExecutionResult,
)
from archive_adapter import (
    read_archive_or_directory,
    read_zip_bytes,
    extract_text_from_zip,
    compute_sha256,
    normalize_text_nfc,
)
from upstream_stages import (
    snapshot_to_structure,
    validate_proposal_guard,
    assemble_candidate,
)
from upstream_pipeline import (
    process_archive,
    default_proposer_hook,
    normalize_text,
)

__all__ = [
    "ReadOnlySource",
    "AnalysisSnapshot",
    "StructureRecord",
    "AgentProposal",
    "GuardStatus",
    "GuardValidationResult",
    "ProposalSet",
    "GuardedProposal",
    "PipelineExecutionResult",
    "read_archive_or_directory",
    "read_zip_bytes",
    "extract_text_from_zip",
    "compute_sha256",
    "normalize_text_nfc",
    "snapshot_to_structure",
    "validate_proposal_guard",
    "assemble_candidate",
    "process_archive",
    "default_proposer_hook",
    "normalize_text",
]
