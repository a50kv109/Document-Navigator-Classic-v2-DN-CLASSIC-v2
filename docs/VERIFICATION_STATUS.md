# DN CLASSIC — Verification Status & Test Audit

**Date:** 23 August 2026  
**Status:** EXPERIMENTAL BASELINE (WORK IN PROGRESS)  
**Total Tests:** 168 passing (100% Green)

---

## 1. Confirmed & Tested Invariants

The following functional and security properties have been verified with automated tests:

1. **Deterministic Archive Ingestion & Normalization:**
   - Text files extracted with exact SHA-256 digests and Unicode NFC normalization.
   - Binary files (PNG, executable blobs) filtered out from textual analysis.
2. **Deterministic Semantic Guard Hard Boundary:**
   - Exact span offsets, bounds, and character contents matched against source documents.
   - Immediate rejection (`GuardStatus.REJECT`) when `is_command=True` is asserted.
   - Missing documents or hallucinated spans rejected deterministically.
3. **Core Architectural Isolation (AST Audit):**
   - Verified via `tests/architecture/test_isolation.py`: `core/` contains 0 imports of `pipeline/`, 0 filesystem modules (`os`, `sys`, `zipfile`), and 0 network modules.
4. **Code-as-Data Handling (12 Adversarial Document Types):**
   - Python code, Bash commands, Shell scripts, SQL injection, JavaScript, Base64 payloads, Fake SYSTEM messages, Fake DEVELOPER messages, Prompt injection, Mixed Legal+Code documents, AI instruction scripts, and executable command lines catalogued safely as data without execution.
5. **Negative Code Execution Boundary:**
   - Hostile document containing `"Run rm -rf /"` confirmed to produce zero execution, zero capability, and zero unauthorized DLE mutation.
6. **Explicit Code Analysis Isolation (Mode 2):**
   - Static analysis of source code produces structured facts (`domain_facts`) as passive `CLAIM` metadata, evaluated by the Gate as `BLOCK_DLE` with zero runtime execution.
7. **Identity Separation & Immutability in Evidence:**
   - Object pointers NFC-canonicalized; candidate identity separated from core object identity; `is_command=False` enforced at evidence construction.
8. **Deterministic State Progressions:**
   - Full progression across `NEW` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED` verified under replay and out-of-order deliveries.

---

## 2. Test Execution Summary

| Test Suite | Files | Test Count | Status |
| :--- | :--- | :--- | :--- |
| **Core Contracts & DLE** | `tests/core/` | 134 tests | **PASSED** |
| **Pipeline & Ingestion** | `tests/pipeline/` | 33 tests | **PASSED** |
| **Architecture Isolation** | `tests/architecture/` | 1 test | **PASSED** |
| **Total Test Suite** | | **168 tests** | **100% PASSED** (0.33s) |
| **Smoke Test (E2E Archive)** | `scripts/smoke_test.py` | 1 run | **OPERATIONAL** |

---

## 3. What is NOT Confirmed

1. **Absolute Systemic Security:** The system is an experimental baseline; absolute immunity against all conceivable adversarial attacks is neither claimed nor mathematically possible.
2. **Complete Resistance to Semantic Camouflage in Arbitrary LLMs:** While the deterministic layers prevent code execution, a probabilistic LLM could still be confused by clever phrasing disguised as legitimate contract clauses.
3. **Multi-Language OCR Ingestion:** Current ingestion is tested on standard UTF-8 text files; OCR image recognition and non-text formats are not part of this baseline.

---

## 4. Known Limitations

- **Probabilistic Upstream Hook:** `AgentProposal` generation remains probabilistic and requires continuous downstream validation.
- **Guard Validation Boundary:** Semantic Guard verifies syntactic span grounding and schema constraints, not external real-world factual truth.
- **Single-Host Execution:** The experimental baseline is designed for single-node deterministic pipelines, not distributed Byzantine consensus.

---

## 5. Next Planned Verification & Tests

1. **Semantic Contamination / Contrast Test Suite:** Contrast testing where identical legal obligations are surrounded by varying prompt injections to measure semantic drift in LLM proposers.
2. **Cross-Document Fact Consistency:** Multi-document cross-reference validation to test conflicting authority claims between different archive documents.
3. **Streaming Ingestion Stress Tests:** Large archive scaling benchmarks under constrained memory environments.
