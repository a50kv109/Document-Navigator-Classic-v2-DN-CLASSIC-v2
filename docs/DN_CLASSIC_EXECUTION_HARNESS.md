# DN CLASSIC — EXECUTION HARNESS GUIDE

**Status:** Canonical Implementation  
**Module:** `pipeline.src`

---

## 1. Overview

The **DN CLASSIC Execution Harness** is the deterministic operational layer that ingests external inputs (ZIP archives, directories, documents), coordinates agent proposing, executes semantic guard validation, and routes admitted candidates through the Frozen Core to DLE state management.

---

## 2. The 8 Operational Stages

```
[1. Archive Adapter]
      │ (Reads ZIP/Dir, SHA-256, NFC, filters non-text)
      ▼
[2. Analysis Snapshot & Structure]
      │ (Produces List[StructureRecord])
      ▼
[3. Agent Proposer Hook]
      │ (Invokes external agent or default baseline -> ProposalSet)
      ▼
[4. Semantic Guard]
      │ (Validates span bounds, exact substring match, non-command)
      ▼
[5. Candidate Assembly]
      │ (Assembles accepted proposals -> LifecycleCandidate)
      ▼
[6. Frozen Gatekeeper]
      │ (Evaluates evaluate_gate -> ACTIVATE_DLE / BLOCK_DLE / HUMAN_REVIEW)
      ▼
[7. Evidence Packaging]
      │ (Produces immutable EvidencePackage with identity separation)
      ▼
[8. DLE Lifecycle Engine]
        (Applies state transition in DLECore: NEW -> ACKNOWLEDGED / IN_PROGRESS / COMPLETED)
```

---

## 3. Public Entrypoints

### `process_archive`
The primary unified execution entrypoint:

```python
from pipeline.src.upstream_pipeline import process_archive
from core.src.dle_core import DLECore

# 1. Standard execution with default baseline proposer
result = process_archive("path/to/archive.zip")

# 2. Execution with custom Agent Proposer and DLE instance
dle = DLECore()
result = process_archive(
    source_input="path/to/archive.zip",
    proposer_hook=my_agent_proposer,
    dle_instance=dle,
)
```

### Result Container: `PipelineExecutionResult`
Provides transparent access to every stage's artifacts:

- `result.snapshot`: `AnalysisSnapshot` with computed SHA-256 hash
- `result.structure_records`: `List[StructureRecord]`
- `result.proposals`: `ProposalSet`
- `result.guarded_proposals`: `List[GuardedProposal]` (with acceptance/rejection reasons)
- `result.candidates`: `List[LifecycleCandidate]`
- `result.output_contracts`: `List[OutputContract]`
- `result.evidence_packages`: `List[EvidencePackage]`
- `result.dle_receipts`: `List[CoreReceipt | BoundaryReceipt]`

---

## 4. Archive Ingestion & Normalization

- **Determinism:** Directory entries and ZIP items are sorted alphabetically.
- **Binary Filtering:** Automated exclusion of binary assets (`.png`, `.jpg`, `.pdf`, `.bin`, `.exe`, etc.).
- **Unicode Normalization:** All text inputs are normalized to **NFC** (`unicodedata.normalize("NFC", text)`).
- **Integrity Digest:** Calculates SHA-256 checksums per file and an aggregate digest for the snapshot.

---

## 5. Semantic Guard Invariants

The Semantic Guard guarantees that bad, fabricated, or malicious agent outputs are intercepted before reaching Core:

1. **Span Text Match:** Checks `source_text[start:end] == span_text`. Any mismatch or index error immediately results in `REJECT`.
2. **Command Rejection:** Any proposal with `is_command=True` results in `REJECT`.
3. **Missing Document:** Proposing against a non-existent document ID results in `REJECT`.
4. **Epistemic Uncertainty:** Proposals marked `AMBIGUOUS`, `UNKNOWN`, or `DISPUTED` result in `UNKNOWN` status and are held from automatic DLE transition.

---

## 6. Example Usage

```python
import zipfile
from pipeline.src.upstream_pipeline import process_archive
from pipeline.src.upstream_types import StructureRecord, ProposalSet, AgentProposal
from contracts import SemanticMode, LifecycleStatus, EpistemicUncertainty, SourceSpan
from dle_core import DLECore

def my_proposer(records: list[StructureRecord]) -> ProposalSet:
    proposals = []
    for r in records:
        # Locate exact text span
        target = "tenant agrees to pay"
        idx = r.normalized_text.find(target)
        if idx != -1:
            span = SourceSpan(
                span_id="span-1",
                text=target,
                start=idx,
                end=idx + len(target),
            )
            proposals.append(
                AgentProposal(
                    document_id=r.document_id,
                    target_entity_id=r.document_id,
                    semantic_mode=SemanticMode.OBLIGATION,
                    lifecycle_status=LifecycleStatus.ACTIVE,
                    epistemic_uncertainty=EpistemicUncertainty.CLEAR,
                    source_spans=[span],
                )
            )
    return ProposalSet(proposals=proposals, agent_id="my-llm-proposer")

# Execute
dle = DLECore()
result = process_archive("sample.zip", proposer_hook=my_proposer, dle_instance=dle)
print(f"Admitted Candidates: {len(result.candidates)}")
print(f"Evidence Generated: {len(result.evidence_packages)}")
```
