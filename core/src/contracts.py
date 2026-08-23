"""
DN CLASSIC — GREEN data contracts only.
Frozen architecture. No DLE Core. No Temporal Engine.
Implementation Gate: CLOSED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any, Dict
from datetime import date, datetime
import unicodedata


def canonicalize_pointer(pointer: Optional[str]) -> Optional[str]:
    """F04: Unicode NFC only — character representation, NOT semantic resolution.

    Ensures canonically equivalent code-point sequences compare equal.
    Does not equate aliases, languages, or organization names.
    NFKC is deliberately NOT used (compatibility collapse risk).
    """
    if pointer is None:
        return None
    return unicodedata.normalize("NFC", pointer)



# ---------------------------------------------------------------------------
# Enums locked by Output Contract schema + Activation Model
# ---------------------------------------------------------------------------

class SemanticMode(str, Enum):
    CLAIM = "CLAIM"
    NORM = "NORM"
    OBLIGATION = "OBLIGATION"
    PHILOSOPHICAL = "PHILOSOPHICAL"
    METAPHORICAL = "METAPHORICAL"


class LifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    HISTORICAL = "HISTORICAL"
    POTENTIAL = "POTENTIAL"
    NONE = "NONE"


class GroundingStatus(str, Enum):
    GROUNDED_SOURCE_CLAIM = "GROUNDED_SOURCE_CLAIM"
    UNSUPPORTED_INFERENCE = "UNSUPPORTED_INFERENCE"


class EpistemicUncertainty(str, Enum):
    CLEAR = "CLEAR"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"
    DISPUTED = "DISPUTED"


class GateDecision(str, Enum):
    ACTIVATE_DLE = "ACTIVATE_DLE"
    BLOCK_DLE = "BLOCK_DLE"
    HUMAN_REVIEW = "HUMAN_REVIEW"


# ---------------------------------------------------------------------------
# Temporal attributes — absolute only (GREEN)
# Relative expressions are YELLOW and deliberately not structured here.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TemporalAttributes:
    """Passive temporal data carried inside Evidence.
    Absolute timestamps / dates / sequence only.
    Relative expressions (e.g. 'through 30 days') remain opaque strings
    or are left out until a contract is fixed.
    """
    issued_at: Optional[str] = None          # ISO date or datetime string
    effective_from: Optional[str] = None
    expires_at: Optional[str] = None
    event_at: Optional[str] = None
    revoked_at: Optional[str] = None
    sequence_id: Optional[str] = None        # ordering from document system
    # relative_raw is intentionally free-form and marked YELLOW
    relative_raw: Optional[str] = None


@dataclass(frozen=True)
class SourceSpan:
    span_id: str
    text: str
    start: Optional[int] = None
    end: Optional[int] = None


@dataclass(frozen=True)
class IdentifiedOntology:
    objects: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LifecycleCandidate — passive immutable assembly (GREEN)
# Never creates DLE Objects, never issues Transition commands.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LifecycleCandidate:
    """Ephemeral passive data structure.
    Exists only to feed the Output Contract and Gate.
    Must never be persisted as a long-lived entity.
    """
    document_id: str
    identified_ontology: IdentifiedOntology
    semantic_mode: SemanticMode
    lifecycle_status: LifecycleStatus
    grounding_status: GroundingStatus
    epistemic_uncertainty: EpistemicUncertainty
    source_spans: List[SourceSpan] = field(default_factory=list)
    candidate_evidence_refs: List[str] = field(default_factory=list)
    # target_entity_id is external reference only — NOT a DLE Object ID
    target_entity_id: Optional[str] = None
    temporal: Optional[TemporalAttributes] = None


# ---------------------------------------------------------------------------
# OutputContract — exact match to frozen schema
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OutputContract:
    document_id: str
    identified_ontology: IdentifiedOntology
    semantic_mode: SemanticMode
    lifecycle_status: LifecycleStatus
    grounding_status: GroundingStatus
    epistemic_uncertainty: EpistemicUncertainty
    dle_eligibility_decision: GateDecision
    source_spans: List[SourceSpan]
    candidate_evidence_refs: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# EvidencePackage — passive proof payload for DLE Core (GREEN packaging)
# Evidence is data / proof, never a command.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidencePackage:
    """Immutable package that may be admitted by Gate.
    Contains only descriptive data.
    """
    document_id: str
    target_entity_id: Optional[str]          # external id, NOT DLE Object ID
    lifecycle_status: LifecycleStatus        # descriptive only
    grounding_status: GroundingStatus
    epistemic_uncertainty: EpistemicUncertainty
    source_spans: List[SourceSpan]
    temporal: Optional[TemporalAttributes]
    candidate_evidence_refs: List[str]
    # Explicit marker that this is not executable
    is_command: bool = False                 # always False by construction
    # Optional opaque domain facts carrier (approved contract).
    # Core and Gate MUST remain key-blind. Conditions may interpret keys.
    # Values are strings only (proven experiment). Default None = absent.
    domain_facts: Optional[Dict[str, str]] = None

    def __post_init__(self):
        # Enforce invariant even under frozen dataclass
        if self.is_command:
            raise ValueError("EvidencePackage must never be a command")
