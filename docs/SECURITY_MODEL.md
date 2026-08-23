# DN CLASSIC — Minimal Security Model

**Status:** EXPERIMENTAL BASELINE (WORK IN PROGRESS)  
**Date:** 23 August 2026  
**Applicability:** DN CLASSIC Architecture (`core` + `pipeline`)

---

## 1. Security Scope & Boundary Disclaimer

> **IMPORTANT DISCLAIMER:**  
> **DN CLASSIC DOES NOT CLAIM ABSOLUTE SECURITY.**  
> Security claims are strictly limited to the tested architectural invariants and implemented deterministic boundaries. DN CLASSIC is an experimental baseline under active verification, not a "finished", "guaranteed safe", or "unbreakable" system.

---

## 2. Core Security Invariants

### Invariant 1: $\text{DOCUMENT CONTENT} \neq \text{EXECUTABLE AUTHORITY}$
No document content, regardless of syntax, framing, formatting, or internal commands, possesses execution privileges. Documents are treated purely as passive data records.

### Invariant 2: $\text{DOCUMENT CONTENT} \neq \text{SYSTEM AUTHORITY}$
Document text containing pseudo-system headers (e.g., `SYSTEM:`, `DEVELOPER:`, `ROOT:`, `ADMIN:`) has zero authority to alter system configurations, disable guards, or modify evaluation rules.

### Invariant 3: $\text{INSTRUCTION IN DOCUMENT} \neq \text{INSTRUCTION TO AGENT}$
An instruction observed inside a document (e.g., *"The director ordered the team to delete the records"*) is an observation of a claim, not an instruction to the processing agent or pipeline runtime.

### Invariant 4: Code as Data
Programmatic code (Python, Bash, Shell, SQL, JavaScript, Base64, JSON configuration) contained within documents is treated strictly as passive data bytes (`ContentNature.CODE_OR_EXECUTABLE`). It is never automatically executed, compiled, evaluated, or dynamically loaded.

### Invariant 5: $\text{CODE ANALYSIS} \neq \text{CODE EXECUTION}$
When explicit code analysis is requested via an authorized external user task (Mode 2), the analysis remains strictly static and observational (AST inspection, structural metadata extraction). Code inspection does not grant execution capabilities. Execution requires an isolated external sandbox outside the DN CLASSIC pipeline.

### Invariant 6: Original Document is Immutable Source Data
$$\text{ORIGINAL SOURCE} \longrightarrow \text{READ-ONLY COPY / DERIVED REPRESENTATION} \longrightarrow \text{METADATA / EVIDENCE}$$
The pipeline never mutates, overwrites, or deletes original archive files. All normalized texts, extracted spans, candidates, evidence packages, and state receipts are derivative data structures.

### Invariant 7: Agent Role is Restricted to Proposer / Librarian
The external agent operates strictly as an untrusted proposer (`Role: PROPOSER ONLY`). An agent submits `AgentProposal` structures containing suggested entities and spans, but cannot directly alter Core states, bypass guards, or grant itself system capabilities.

### Invariant 8: Deterministic Semantic Guard as Hard Boundary
All agent proposals must pass deterministic validation in `validate_proposal_guard`:
- Any proposal with `is_command=True` is immediately rejected (`GuardStatus.REJECT`).
- All `SourceSpan` offsets, lengths, and exact text slices are checked against normalized source text.
- Epistemic uncertainty (`UNKNOWN`, `AMBIGUOUS`, `DISPUTED`) prevents direct candidate admission.

### Invariant 9: DLE Core Execution Isolation
`DLECore` is a pure in-memory finite state machine that operates with zero I/O, zero network, zero filesystem, and zero OS/shell execution capability.

---

## 3. Two Operational Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MODE 1 — LIBRARIAN / DOCUMENT OBSERVATION (Default Mode)                   │
│                                                                             │
│ SOURCE(Document Archive) ──► FLOW ──► STATE(Passive Records) ──► Proposal   │
│                                                                             │
│ - Agent catalogues, classifies, and indexes document content.               │
│ - Code and commands are catalogued as DATA (ContentNature.CODE_OR_EXEC).   │
│ - Zero execution. Zero command privileges.                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ MODE 2 — EXPLICIT CODE ANALYSIS (Authorized User Task Only)                 │
│                                                                             │
│ SOURCE(User Task) ──► CONSTRAINT ──► CAPABILITY(Static Code Inspection)     │
│                                                                             │
│ - Triggered only by an explicit external user request.                      │
│ - Inspects static structure (AST, functions, parameters, typing).           │
│ - Produces domain facts as passive CLAIM metadata.                          │
│ - Zero runtime execution inside DN CLASSIC.                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Semantic Drift, Camouflage & Known Limitations

1. **Probabilistic Upstream Proposer:**  
   The external agent (LLM, heuristic, or neural classifier) is probabilistic. It may misclassify content, suffer from semantic camouflage (e.g., malicious commands disguised as formal legal obligations), or hallucinate interpretations.
2. **Guard Scope:**  
   The Semantic Guard verifies formal and structural properties (span exactness, document existence, absence of `is_command`). It does **not** prove the objective truth of the extracted statement.
3. **Semantic Contamination:**  
   While harmful code cannot execute, malicious document text could theoretically influence a probabilistic LLM's classification of surrounding benign text. Deterministic downstream layers (Gate, DLE Core) bound and limit the systemic consequences of such misclassifications.

---

## 5. SOL (System Operator Logic) Architectural Interpretation

DN CLASSIC maps security boundaries strictly across standard SOL primitives without introducing ad-hoc primitives:

$$\mathbf{SOURCE} \longrightarrow \mathbf{FLOW} \longrightarrow \mathbf{STATE} \longrightarrow \mathbf{COMPARE} \longrightarrow \mathbf{CONSTRAINT} \longrightarrow \mathbf{CAPABILITY} \longrightarrow \mathbf{EVIDENCE}$$

- $\mathbf{SOURCE(Document)}$ generates $\mathbf{FLOW(Text Ingestion)}$ into $\mathbf{STATE(Observed Content)}$.
- $\mathbf{STATE(Observed Content)}$ is evaluated via $\mathbf{COMPARE(Span Grounding)}$ under $\mathbf{CONSTRAINT(Semantic Guard)}$.
- $\mathbf{SOURCE(Document)}$ **CANNOT** directly instantiate $\mathbf{CAPABILITY(Execute)}$ or mutate $\mathbf{CONSTRAINT(System Rules)}$.
- Only $\mathbf{SOURCE(System/Host Configuration)}$ establishes $\mathbf{CONSTRAINT(Pipeline Execution Boundaries)}$.
- $\mathbf{EVIDENCE}$ is the passive, immutable product certifying compliance.
