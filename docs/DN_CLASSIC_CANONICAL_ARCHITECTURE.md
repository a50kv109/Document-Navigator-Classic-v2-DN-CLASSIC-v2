# DN CLASSIC — CANONICAL ARCHITECTURE SPECIFICATION

**Status:** CANONICAL & FROZEN  
**Architecture Form:** Monorepo (`core` + `pipeline`)  
**Specification Version:** 1.0.0

---

## 1. System Mission & Boundary Definition

**DN CLASSIC** is a **Deterministic Constraint, Grounding, and Evidence Architecture**.
It bridges probabilistic upstream agent reasoning (LLMs, neural extractors) and deterministic downstream state management (DLE Core, audit ledgers, state machines).

### Fundamental Axiom:
$$\text{Evidence} \neq \text{Truth}$$

- **Grounding** establishes lexical provenance against a source document.
- **Evidence** certifies that a structured claim satisfies defined contracts and spans.
- **Evidence does NOT prove objective truth** in the external world; it proves verifiable textual provenance within the closed system boundary.

---

## 2. Monorepo Structural Taxonomy

```
dn-classic/
├── core/                  # Deterministic Authority Layer (FROZEN)
│   ├── src/
│   │   ├── contracts.py           # Types, enums, data contracts
│   │   ├── gate.py                # Deterministic Gatekeeper (evaluate_gate)
│   │   ├── evidence.py            # Evidence packaging & identity separation
│   │   ├── dle_core.py            # DLE State machine runtime (5 primitives)
│   │   ├── consumption_boundary.py# Conceptual passive evidence consumer
│   │   ├── source_boundary.py     # Read-only SourceDocument abstraction
│   │   └── trace.py               # Minimal Gate decision trace
│   └── docs/
│       └── CANONICAL_AGENT_FACING_SPECIFICATION.md
├── pipeline/              # Deterministic Infrastructure Layer
│   └── src/
│       ├── upstream_types.py      # Snapshots, records, agent proposals
│       ├── archive_adapter.py     # Deterministic ZIP/dir ingestion (SHA-256/NFC)
│       ├── upstream_stages.py     # Structure, Semantic Guard, Assembly
│       ├── upstream_pipeline.py   # 8-stage pipeline execution engine
│       └── process_archive.py     # Public operational entrypoint
├── tests/                 # Automated Test Suite (162+ Tests)
│   ├── core/                      # Frozen core tests & mathematical proofs
│   ├── pipeline/                  # Execution harness & adapter tests
│   └── architecture/              # AST-based isolation verification
├── docs/                  # Canonical Documentation
│   ├── AGENT_PROTOCOL.md
│   ├── DN_CLASSIC_CANONICAL_ARCHITECTURE.md
│   ├── DN_CLASSIC_EXECUTION_HARNESS.md
│   └── DN_CLASSIC_RELEASE_CHECKPOINT.md
└── scripts/               # Operational Scripts
    ├── smoke_test.py              # End-to-end execution smoke test
    └── publish_to_github.sh       # Release & publication script
```

---

## 3. Separation of Concerns & Tripartite Authority

| Layer | Responsibility | Authority Level | Purity |
|---|---|---|---|
| **CORE** | Invariant enforcement, Gate evaluation, DLE state transitions | **Deterministic Authority** | Pure memory, zero I/O, zero network |
| **PIPELINE** | File extraction, NFC normalization, SHA-256 digests, Semantic Guard, candidate assembly | **Deterministic Infrastructure** | File I/O, format conversion |
| **AGENT** | Proposing claims, spans, semantics, entities from text | **Proposer Only** | Probabilistic, untrusted |

---

## 4. Architectural Isolation Invariant

- **Rule:** `PIPELINE` imports `CORE`. `CORE` **NEVER** imports `PIPELINE`.
- **I/O Rule:** `CORE` modules contain zero imports of `os`, `sys`, `zipfile`, `socket`, or network libraries.
- **Verification:** Automatically enforced on every test run via `tests/architecture/test_isolation.py` through Python Abstract Syntax Tree (AST) inspection.

---

## 5. The Five Core Primitives

The DLE Core runtime operates strictly on five mathematical primitives:

1. **Object:** A unique identity managed solely within Core (`DLEObject`).
2. **State:** Discrete lifecycle state (`NEW`, `ACKNOWLEDGED`, `IN_PROGRESS`, `COMPLETED`).
3. **Transition:** Atomic state migration triggered by matched conditions (`TransitionRule`).
4. **Condition:** Pure predicate evaluating an `EvidencePackage` and current `DLEObject`.
5. **Evidence:** Passive, immutable verification record (`EvidencePackage`).

*Note:* `DLECore` is the orchestrator of these five primitives — it is **NOT** a sixth primitive.

---

## 6. Deterministic Execution Flow

$$\text{Archive} \xrightarrow{\text{Adapter}} \text{Snapshot} \xrightarrow{\text{Structure}} \text{Records} \xrightarrow{\text{Agent}} \text{Proposals} \xrightarrow{\text{Guard}} \text{Candidates} \xrightarrow{\text{Gate}} \text{Evidence} \xrightarrow{\text{DLE}} \text{State}$$

1. **Archive Ingestion:** Reads ZIP/dir, computes SHA-256, normalizes Unicode (NFC), produces `ReadOnlySource` and `AnalysisSnapshot`.
2. **Structure Stage:** Converts snapshots into immutable `StructureRecord` entries.
3. **Agent Hook:** External agent proposes `ProposalSet` without direct lifecycle power.
4. **Semantic Guard:** Validates exact span offsets, type conformance, and command absence (`is_command=False`).
5. **Assembly:** Constructs typed, immutable `LifecycleCandidate`.
6. **Gate Evaluation:** Evaluates candidate semantics (`ACTIVATE_DLE` vs `BLOCK_DLE` vs `HUMAN_REVIEW`).
7. **Evidence Packaging:** Produces immutable `EvidencePackage` with strict identity separation.
8. **DLE Processing:** Updates object state machine according to registered deterministic transition rules.

---

## 7. The Code-as-Data Invariant & Harvard Authority Isolation

### Fundamental Principle:
$$\text{DOCUMENT CONTENT} \neq \text{EXECUTABLE AUTHORITY}$$

1. **Instruction / Data Separation:**
   - Instruction flow originates strictly from `SYSTEM / HOST` configuration.
   - Data flow originates strictly from `DOCUMENT` content.
   - Code, scripts, shell commands, SQL, Python, or Base64 located inside documents are treated purely as observed data bytes.
2. **No Autonomous Capability Generation:**
   - Text within a document cannot instantiate `CAPABILITY` or execute shell/OS calls.
3. **Explicit Code Analysis Isolation:**
   - When explicit code analysis is requested via an authorized task, analysis is static and observational ($\text{CODE ANALYSIS} \neq \text{CODE EXECUTION}$).
   - Execution requires an external sandbox completely decoupled from the DN CLASSIC pipeline.

