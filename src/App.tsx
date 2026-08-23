import React, { useState } from "react";
import {
  ShieldCheck,
  FileCode,
  Layers,
  Terminal,
  Cpu,
  CheckCircle2,
  Lock,
  GitBranch,
  BookOpen,
  ArrowRight,
  Database,
  Search,
} from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab] = useState<"overview" | "pipeline" | "tests" | "protocol">("overview");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-10 shadow-xs">
        <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-900 text-white flex items-center justify-center font-mono font-bold text-lg shadow-xs">
              DN
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-900">
                  DN CLASSIC MONOREPO
                </h1>
                <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-800 rounded-full border border-emerald-300">
                  v1.0.0-canonical
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Deterministic Constraint, Grounding, and Evidence Architecture
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>162 / 162 Tests Passing</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium">
              <Lock className="w-4 h-4 text-slate-500" />
              <span>Frozen Core</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-6 flex gap-6 border-t border-slate-100">
          {[
            { id: "overview", label: "Architecture Overview", icon: Layers },
            { id: "pipeline", label: "8-Stage Pipeline", icon: Cpu },
            { id: "tests", label: "Verification & Audits", icon: ShieldCheck },
            { id: "protocol", label: "Agent Protocol", icon: BookOpen },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-3 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
                  isActive
                    ? "border-slate-900 text-slate-900 font-semibold"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === "overview" && (
          <div className="space-y-8">
            {/* Axiom Banner */}
            <div className="p-5 rounded-xl bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="text-xs uppercase tracking-widest text-emerald-400 font-mono font-bold">
                  Canonical Axiom
                </span>
                <h2 className="text-2xl font-bold font-mono mt-0.5">Evidence ≠ Truth</h2>
                <p className="text-slate-300 text-sm max-w-2xl mt-1">
                  Grounding establishes lexical provenance against source spans. Evidence certifies contract adherence.
                  It proves verifiable provenance within the system boundary — not external metaphysical truth.
                </p>
              </div>
              <div className="shrink-0 font-mono text-xs bg-slate-800/80 px-4 py-2.5 rounded-lg border border-slate-700 text-slate-300">
                Core Purity: Zero I/O, Zero Network
              </div>
            </div>

            {/* Tripartite Authority Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200">
                    STAGE: PROPOSER
                  </span>
                  <Cpu className="w-5 h-5 text-amber-600" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">External Agent</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Probabilistic upstream reasoning layer. Extracts claims, dates, and entities from documents.
                  Holds <strong>zero lifecycle authority</strong> and cannot directly alter state.
                </p>
                <ul className="text-xs text-slate-500 space-y-1 pt-2 border-t border-slate-100">
                  <li>• Receives: <code className="text-slate-800 font-mono">StructureRecord</code></li>
                  <li>• Returns: <code className="text-slate-800 font-mono">ProposalSet</code></li>
                  <li>• Constraint: Non-executable (<code className="text-slate-800 font-mono">is_command=False</code>)</li>
                </ul>
              </div>

              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
                    STAGE: INFRASTRUCTURE
                  </span>
                  <Database className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Pipeline Harness</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Deterministic I/O and validation engine. Reads ZIPs, computes SHA-256 hashes, applies NFC normalization,
                  and executes the <strong>Semantic Guard</strong>.
                </p>
                <ul className="text-xs text-slate-500 space-y-1 pt-2 border-t border-slate-100">
                  <li>• Modules: <code className="text-slate-800 font-mono">archive_adapter</code>, <code className="text-slate-800 font-mono">upstream_stages</code></li>
                  <li>• Enforces: Exact substring span checks</li>
                  <li>• Output: <code className="text-slate-800 font-mono">LifecycleCandidate</code></li>
                </ul>
              </div>

              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                    STAGE: AUTHORITY
                  </span>
                  <Lock className="w-5 h-5 text-emerald-600" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Frozen Core</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Canonical mathematical state engine. Evaluates Gate admission (<code className="text-slate-800 font-mono">evaluate_gate</code>),
                  packages immutable evidence, and executes DLE state transitions.
                </p>
                <ul className="text-xs text-slate-500 space-y-1 pt-2 border-t border-slate-100">
                  <li>• Primitives: Object, State, Transition, Condition, Evidence</li>
                  <li>• Graph: NEW → ACKNOWLEDGED → IN_PROGRESS → COMPLETED</li>
                  <li>• Isolation: AST verified (zero I/O imports)</li>
                </ul>
              </div>
            </div>

            {/* Monorepo Directory Layout */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
                <FileCode className="w-4 h-4 text-slate-700" />
                Canonical Repository Layout
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
                <div className="p-4 bg-slate-900 text-slate-200 rounded-lg space-y-1">
                  <div className="text-emerald-400 font-bold"># CORE LAYER (FROZEN AUTHORITY)</div>
                  <div>core/src/contracts.py</div>
                  <div>core/src/gate.py</div>
                  <div>core/src/evidence.py</div>
                  <div>core/src/dle_core.py</div>
                  <div>core/src/consumption_boundary.py</div>
                  <div>core/src/source_boundary.py</div>
                  <div>core/src/trace.py</div>
                </div>
                <div className="p-4 bg-slate-900 text-slate-200 rounded-lg space-y-1">
                  <div className="text-blue-400 font-bold"># PIPELINE LAYER (INFRASTRUCTURE)</div>
                  <div>pipeline/src/upstream_types.py</div>
                  <div>pipeline/src/archive_adapter.py</div>
                  <div>pipeline/src/upstream_stages.py</div>
                  <div>pipeline/src/upstream_pipeline.py</div>
                  <div>pipeline/src/process_archive.py</div>
                  <div className="text-amber-400 font-bold pt-2"># TESTS & HARNESS (162 PASSED)</div>
                  <div>tests/core/ (12 test suites)</div>
                  <div>tests/pipeline/ (5 test suites)</div>
                  <div>tests/architecture/test_isolation.py</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "pipeline" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
              <h3 className="text-lg font-bold text-slate-900 mb-1">
                The 8 Deterministic Pipeline Stages
              </h3>
              <p className="text-sm text-slate-500 mb-6">
                End-to-end execution flow from raw archive bytes to DLE lifecycle state transitions.
              </p>

              <div className="space-y-3">
                {[
                  {
                    step: "01",
                    name: "Archive Adapter",
                    desc: "Reads ZIP or directory deterministically. Excludes binary files (.png, .jpg, .bin). Calculates SHA-256 digest and normalizes text with NFC.",
                    artifact: "AnalysisSnapshot / ReadOnlySource",
                  },
                  {
                    step: "02",
                    name: "Structure Extraction",
                    desc: "Transforms snapshot files into indexed document records with verified hashes and byte counts.",
                    artifact: "List[StructureRecord]",
                  },
                  {
                    step: "03",
                    name: "Agent Proposer Hook",
                    desc: "Invokes external agent or default baseline proposer to extract candidate claims, entities, and source spans.",
                    artifact: "ProposalSet",
                  },
                  {
                    step: "04",
                    name: "Semantic Guard",
                    desc: "Deterministic validation: checks exact span text at [start:end] in source document, verifies typed enums, and blocks command injection.",
                    artifact: "List[GuardedProposal] (ACCEPT / REJECT / UNKNOWN)",
                  },
                  {
                    step: "05",
                    name: "Candidate Assembly",
                    desc: "Converts accepted proposals into typed, immutable candidates matching the Core specification.",
                    artifact: "List[LifecycleCandidate]",
                  },
                  {
                    step: "06",
                    name: "Frozen Gatekeeper",
                    desc: "Executes evaluate_gate to determine DLE eligibility: ACTIVATE_DLE, BLOCK_DLE, or HUMAN_REVIEW.",
                    artifact: "List[OutputContract]",
                  },
                  {
                    step: "07",
                    name: "Evidence Packaging",
                    desc: "Packages admitted candidates into immutable evidence with strict identity separation (is_command=False).",
                    artifact: "List[EvidencePackage]",
                  },
                  {
                    step: "08",
                    name: "DLE Core Engine",
                    desc: "Applies condition evaluation and executes deterministic state transitions (NEW → IN_PROGRESS / COMPLETED).",
                    artifact: "List[CoreReceipt]",
                  },
                ].map((s) => (
                  <div
                    key={s.step}
                    className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="flex items-start gap-3">
                      <span className="font-mono text-xs font-bold bg-slate-900 text-white px-2.5 py-1 rounded">
                        {s.step}
                      </span>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">{s.name}</h4>
                        <p className="text-xs text-slate-600 mt-0.5">{s.desc}</p>
                      </div>
                    </div>
                    <div className="shrink-0 font-mono text-xs bg-white px-3 py-1.5 rounded border border-slate-200 text-slate-700">
                      → {s.artifact}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Code Example */}
            <div className="bg-slate-900 text-slate-100 p-6 rounded-xl border border-slate-800 shadow-xs font-mono text-xs space-y-2">
              <div className="text-emerald-400 font-bold flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                Python Execution Entrypoint
              </div>
              <pre className="text-slate-300 overflow-x-auto p-3 bg-slate-950 rounded-lg">
{`from pipeline.src.upstream_pipeline import process_archive
from core.src.dle_core import DLECore

dle = DLECore()
result = process_archive("contracts_archive.zip", dle_instance=dle)

print("Snapshot Hash :", result.snapshot.computed_hash)
print("Admitted      :", len(result.candidates))
print("Evidence Pkgs :", len(result.evidence_packages))
print("DLE Receipts  :", len(result.dle_receipts))`}
              </pre>
            </div>
          </div>
        )}

        {activeTab === "tests" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Verification & Audit Matrix</h3>
                  <p className="text-xs text-slate-500">
                    162 automated tests running in under 0.3s with 100% pass rate.
                  </p>
                </div>
                <div className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs border border-emerald-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  162 / 162 Passed
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50 text-slate-700">
                      <th className="py-2.5 px-3 font-semibold">Test Suite</th>
                      <th className="py-2.5 px-3 font-semibold">Target File</th>
                      <th className="py-2.5 px-3 font-semibold">Assertions / Scope</th>
                      <th className="py-2.5 px-3 font-semibold">Count</th>
                      <th className="py-2.5 px-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {[
                      { suite: "Core Adversarial Audit", file: "tests/core/test_adversarial.py", scope: "Exhaustive contract attack audit", count: 38 },
                      { suite: "Consumption Boundary", file: "tests/core/test_consumption_boundary.py", scope: "Passive hand-off boundary checks", count: 13 },
                      { suite: "Gate Decisions", file: "tests/core/test_gate.py", scope: "Gate evaluation logic & precedence", count: 13 },
                      { suite: "Temporal Expressiveness", file: "tests/core/test_experimental_temporal_...py", scope: "Domain temporal obligation conditions", count: 12 },
                      { suite: "Slice 2 Sufficiency", file: "tests/core/test_slice2_functional_...py", scope: "Multi-step lifecycle graph progression", count: 11 },
                      { suite: "Domain Facts Contract", file: "tests/core/test_domain_facts_contract.py", scope: "Key-blind condition evaluation", count: 11 },
                      { suite: "DLE Core Audit", file: "tests/core/test_dle_core_adversarial_...py", scope: "State machine invariant checks", count: 10 },
                      { suite: "Contract Attacks", file: "tests/core/test_consumption_contract_...py", scope: "Adversarial mutation defenses", count: 10 },
                      { suite: "F04 Canonicalization", file: "tests/core/test_f04_canonicalization.py", scope: "NFC Unicode normalization proofs", count: 8 },
                      { suite: "DLE Core Probe", file: "tests/core/test_dle_core_probe.py", scope: "Five core primitives verification", count: 8 },
                      { suite: "Evidence & Identity", file: "tests/core/test_evidence_and_identity.py", scope: "Identity separation & passive proof", count: 7 },
                      { suite: "Functional Expansion", file: "tests/core/test_functional_expansion_...py", scope: "Earned lifecycle transitions", count: 7 },
                      { suite: "Archive Adapter", file: "tests/pipeline/test_archive_adapter.py", scope: "ZIP, dir, SHA-256, binary filters", count: 7 },
                      { suite: "Upstream Guard", file: "tests/pipeline/test_upstream_stages.py", scope: "Span matching & command rejection", count: 7 },
                      { suite: "Proposer Hook", file: "tests/pipeline/test_agent_proposer_hook.py", scope: "External agent proposer contracts", count: 3 },
                      { suite: "E2E Processing", file: "tests/pipeline/test_process_archive_e2e.py", scope: "End-to-end 8-stage pipeline run", count: 3 },
                      { suite: "Pipeline Extraction", file: "tests/pipeline/test_pipeline.py", scope: "Adapter extraction compatibility", count: 1 },
                      { suite: "Architectural Isolation", file: "tests/architecture/test_isolation.py", scope: "AST check: Core imports 0 pipeline/IO", count: 1 },
                    ].map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="py-2 px-3 font-sans font-medium text-slate-900">{row.suite}</td>
                        <td className="py-2 px-3 text-slate-500">{row.file}</td>
                        <td className="py-2 px-3 text-slate-600 font-sans">{row.scope}</td>
                        <td className="py-2 px-3 text-slate-800 font-bold">{row.count}</td>
                        <td className="py-2 px-3">
                          <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-bold">
                            PASSED
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === "protocol" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Agent Protocol & Boundaries</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Rules and contracts governing external LLMs and autonomous agents interacting with DN CLASSIC.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-emerald-800 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Agent Responsibilities (DOs)
                  </h4>
                  <ul className="text-xs text-slate-600 space-y-2 leading-relaxed">
                    <li className="p-2.5 rounded bg-emerald-50/50 border border-emerald-100">
                      <strong>1. Propose Claims with Spans:</strong> Anchor every proposed claim to exact start/end character offsets in <code className="font-mono text-slate-900">normalized_text</code>.
                    </li>
                    <li className="p-2.5 rounded bg-emerald-50/50 border border-emerald-100">
                      <strong>2. Declare Uncertainty Honestly:</strong> Use <code className="font-mono text-slate-900">AMBIGUOUS</code> or <code className="font-mono text-slate-900">DISPUTED</code> when text is unclear.
                    </li>
                    <li className="p-2.5 rounded bg-emerald-50/50 border border-emerald-100">
                      <strong>3. Conform to Enums:</strong> Use standard <code className="font-mono text-slate-900">SemanticMode</code>, <code className="font-mono text-slate-900">LifecycleStatus</code>, and <code className="font-mono text-slate-900">GroundingStatus</code>.
                    </li>
                  </ul>
                </div>

                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-rose-800 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-rose-600" />
                    Strict Prohibitions (DON'Ts)
                  </h4>
                  <ul className="text-xs text-slate-600 space-y-2 leading-relaxed">
                    <li className="p-2.5 rounded bg-rose-50/50 border border-rose-100">
                      <strong>1. Never Issue Commands:</strong> Proposals with <code className="font-mono text-rose-900">is_command=True</code> are rejected immediately by the Semantic Guard.
                    </li>
                    <li className="p-2.5 rounded bg-rose-50/50 border border-rose-100">
                      <strong>2. Never Fabricate Spans:</strong> Text mismatch between proposal and source document triggers immediate rejection.
                    </li>
                    <li className="p-2.5 rounded bg-rose-50/50 border border-rose-100">
                      <strong>3. Never Mutate Core State:</strong> Agent has zero direct write access to DLE objects or state transitions.
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
