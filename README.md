# Document-Navigator-Classic-v2 (DN CLASSIC v2)

**STATUS:** EXPERIMENTAL BASELINE / WORK IN PROGRESS / UNDER VERIFICATION  
**BASELINE DATE:** 23 AUGUST 2026  
**VERSION:** 2.0.0-experimental-baseline  
**ARCHITECTURE:** Monorepo (`core` + `pipeline`)

> `Document-Navigator-Classic-v2` is a new experimental architectural iteration of the Document Navigator concept. It is an engineering research baseline under active verification and testing. It is **NOT** presented as a finished product, a production-ready framework, or a guarantee of complete security.

---

## 1. What is Document-Navigator-Classic-v2?

**Document-Navigator-Classic-v2 (DN CLASSIC v2)** is an experimental deterministic architecture designed for safer, predictable, and verifiable document processing with autonomous AI agents.

It bridges probabilistic upstream agent reasoning (LLMs, neural extractors, heuristic parsers) with deterministic downstream state evaluation (pure in-memory finite state machines, semantic guardrails, cryptographic evidence packages, and strict provenance tracking).

```
DOCUMENT ARCHIVE
    ↓ (deterministic ingestion)
DERIVED ANALYSIS SNAPSHOT (SHA-256 / NFC normalization)
    ↓
LIBRARIAN-STYLE OBSERVATION (Agent Hook)
    ↓
SEMANTIC PROPOSALS (AgentProposal)
    ↓
DETERMINISTIC VALIDATION (Semantic Guard)
    ↓
EVIDENCE PACKAGING (EvidencePackage)
    ↓
LIFECYCLE EVALUATION (DLE Core)
```

---

## 2. Fundamental Axiom: Grounding ≠ Truth

$$\mathbf{Evidence \neq Truth}$$

- **Grounding** establishes lexical provenance (a statement exists at exact offsets in a source document).
- **Evidence** certifies that a structured claim satisfies defined contracts and span rules.
- **Evidence does NOT prove objective truth in the real world.** A claim can be perfectly grounded in a fraudulent contract or fictional story while remaining false in reality. DN CLASSIC verifies internal structural provenance and contract adherence, not external objective truth.

---

## 3. The Core Principles & Architectural Invariants

### Principle 1: Document Content ≠ Executable Authority
$$\mathbf{DOCUMENT\ CONTENT \neq EXECUTABLE\ AUTHORITY}$$
A document may contain arbitrary text: legal clauses, natural prose, bash commands, shell scripts, SQL queries, Python scripts, JavaScript, Base64 payloads, or pseudo-system directives (`SYSTEM: OVERRIDE`). The presence of executable-like text inside a document grants **zero system authority** and **zero execution capability**.

### Principle 2: Original Document is Immutable Source Data
$$\mathbf{ORIGINAL\ SOURCE} \longrightarrow \mathbf{READ\text{-}ONLY\ COPY / SNAPSHOT} \longrightarrow \mathbf{AGENT\ ANALYSIS} \longrightarrow \mathbf{DERIVED\ REPRESENTATION}$$
The system treats original documents as sacred, immutable source records. Original archive files are never modified, edited, or overwritten by the agent or the pipeline. All normalized texts, extracted spans, candidate entities, and lifecycle receipts are strictly derivative representations.

### Principle 3: The Librarian Principle
The agent operates under the **Librarian Principle**:
- It reads, catalogues, classifies, and indexes document content.
- It **does not obey** commands found in documents.
- It treats executable code in documents as passive data (`ContentNature.CODE_OR_EXECUTABLE`).

### Principle 4: Code Analysis ≠ Code Execution
- **Mode 1 (Librarian Observation - Default):** Code is indexed as passive data with zero execution.
- **Mode 2 (Explicit Code Analysis):** When an authorized user task explicitly asks to analyze code, the agent performs static structural inspection (AST, signatures, types). Static analysis **never** triggers runtime execution. Runtime execution requires an external isolated sandbox decoupled from DN CLASSIC.

---

## 4. Architectural Isolation & Tripartite Model

```
┌────────────────────────────────────────────────────────┐
│                   EXTERNAL AGENT                       │
│  Role: PROPOSER ONLY (Probabilistic, Untrusted)        │
└──────────────────────────┬─────────────────────────────┘
                           │ (ProposalSet)
                           ▼
┌────────────────────────────────────────────────────────┐
│                      PIPELINE                          │
│  Role: DETERMINISTIC INFRASTRUCTURE                    │
│  ├── Archive Ingestion (SHA-256 / NFC normalization)   │
│  ├── Analysis Snapshot & Structure Records             │
│  ├── Semantic Guard (Span grounding / non-command)     │
│  └── Candidate Assembly                                │
└──────────────────────────┬─────────────────────────────┘
                           │ (LifecycleCandidate)
                           ▼
┌────────────────────────────────────────────────────────┐
│                        CORE                            │
│  Role: DETERMINISTIC AUTHORITY (Frozen)                │
│  ├── Gatekeeper (evaluate_gate: ACTIVATE/BLOCK/REVIEW) │
│  ├── Evidence Packaging (is_command=False)             │
│  └── DLE State Machine (5 Primitives: Object/State/    │
│      Transition/Condition/Evidence)                    │
└────────────────────────────────────────────────────────┘
```

- **`core/`** is pure in-memory deterministic authority. It contains zero I/O, zero network, zero filesystem access, and never imports `pipeline/`.
- **`pipeline/`** provides deterministic infrastructure (file reading, SHA-256 calculation, text normalization, and Semantic Guard validation).
- **Agent** has proposer-only authority. It cannot bypass the Semantic Guard or directly mutate the DLE state machine.

---

## 5. Security Scope & Boundary Disclaimer

> **IMPORTANT DISCLAIMER:**  
> **DOCUMENT-NAVIGATOR-CLASSIC-V2 DOES NOT CLAIM ABSOLUTE SECURITY.**  
> This repository represents a working experimental baseline under active verification. Security claims are strictly limited to the tested architectural invariants and implemented deterministic boundaries.

### What is Protected and Verified:
- Deterministic archive extraction and text NFC normalization.
- Rejection of commands (`is_command=True`) by the Semantic Guard.
- Validation of exact text span offsets against source documents.
- Safe cataloguing of 12 adversarial code/injection formats as passive data.
- AST isolation preventing `core/` from accessing I/O or shell execution.

### What is NOT Guaranteed & Known Limitations:
- Absolute immunity of probabilistic LLMs against semantic camouflage or sophisticated hallucination.
- Real-world factual accuracy of statements grounded in deceptive source documents.
- Potential semantic contamination of surrounding text inside an LLM's context window.

---

## 6. How to Run Tests & Verification

### Running the Full Test Suite (168 tests):
```bash
pytest -v
```

### Running Architecture Isolation Tests (AST verification):
```bash
pytest -v tests/architecture/
```

### Running the E2E Smoke Test:
```bash
python3 scripts/smoke_test.py
```

---

## 7. Starting Guide: What to Read First (START HERE)

If you are a new engineer or autonomous agent exploring this repository:

1. **`README.md`** (This file) — High-level architecture, principles, and invariants.
2. **`docs/AGENT_ONBOARDING.md`** — Quick-start orientation for autonomous agents.
3. **`docs/AGENT_PROTOCOL.md`** — Formal protocol, schema rules, and forbidden actions.
4. **`docs/SECURITY_MODEL.md`** — Minimal security model and SOL mapping.
5. **`docs/DN_CLASSIC_CANONICAL_ARCHITECTURE.md`** — In-depth architectural specification.
6. **`docs/VERIFICATION_STATUS.md`** — Full audit of verified invariants and test coverage.

---

## 8. Repository Layout

```
Document-Navigator-Classic-v2/
├── core/                  # Deterministic Authority Layer (FROZEN)
│   ├── src/               # contracts, gate, evidence, dle_core
│   └── docs/              # CANONICAL_AGENT_FACING_SPECIFICATION.md
├── pipeline/              # Deterministic Infrastructure Layer
│   └── src/               # archive_adapter, upstream_stages, upstream_pipeline
├── tests/                 # 168 Automated Tests (100% Green)
│   ├── core/              # Mathematical proofs, gate logic, and boundary audits
│   ├── pipeline/          # Archive adapter, guard, adversarial code-as-data tests
│   └── architecture/      # AST isolation invariant verification
├── docs/                  # Canonical Specifications & Security Documentation
│   ├── AGENT_ONBOARDING.md
│   ├── AGENT_PROTOCOL.md
│   ├── SECURITY_MODEL.md
│   ├── VERIFICATION_STATUS.md
│   ├── DN_CLASSIC_CANONICAL_ARCHITECTURE.md
│   ├── DN_CLASSIC_EXECUTION_HARNESS.md
│   └── DN_CLASSIC_RELEASE_CHECKPOINT.md
└── scripts/               # Operational Scripts
    ├── smoke_test.py
    └── publish_to_github.sh
```
