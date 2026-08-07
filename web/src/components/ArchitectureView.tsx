import React, { useState } from 'react';
import { Cpu, Server, ShieldCheck, Database, GitMerge, Lock, FileCode, CheckCircle2 } from 'lucide-react';
import { EvaluationSuite } from './EvaluationSuite';

export const ArchitectureView: React.FC = () => {
  const [activeSection, setActiveSection] = useState<'diagram' | 'mcp' | 'evaluation'>('diagram');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Banner */}
      <div className="bg-[#111111] rounded-xl p-5 border border-white/10 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-6 h-6 text-orange-500" />
            <h1 className="text-xl font-light tracking-tight text-white">System Architecture & Agent Evaluation</h1>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-orange-600/20 text-orange-400 border border-orange-500/30 font-mono">
              LangGraph + MCP Gateway
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Explore LangGraph supervisor routing, MCP tool permission enforcement, and automated safety benchmarks.
          </p>
        </div>

        {/* Section Tabs */}
        <div className="flex items-center space-x-2 bg-[#080808] p-1.5 rounded border border-white/10">
          <button
            onClick={() => setActiveSection('diagram')}
            className={`px-3 py-1.5 rounded text-xs font-semibold tracking-wide transition-all ${
              activeSection === 'diagram' ? 'bg-orange-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Agent Topology
          </button>
          <button
            onClick={() => setActiveSection('mcp')}
            className={`px-3 py-1.5 rounded text-xs font-semibold tracking-wide transition-all ${
              activeSection === 'mcp' ? 'bg-orange-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            MCP Tool Registry
          </button>
          <button
            onClick={() => setActiveSection('evaluation')}
            className={`px-3 py-1.5 rounded text-xs font-semibold tracking-wide transition-all ${
              activeSection === 'evaluation' ? 'bg-orange-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Golden Eval Suite
          </button>
        </div>
      </div>

      {activeSection === 'diagram' && (
        <div className="bg-[#111111] rounded-xl border border-white/10 p-6 text-white space-y-6 shadow-xl">
          <h2 className="text-[10px] font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2 font-mono">
            <GitMerge className="w-4 h-4 text-orange-500" /> LangGraph Supervisor & MCP Gateway Pipeline
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
            {/* Step 1 */}
            <div className="bg-[#080808] p-4 rounded border border-white/10 space-y-2">
              <span className="text-[10px] font-bold text-orange-400 uppercase">1. Guardrails AI & Presidio</span>
              <h3 className="font-bold text-white text-sm">Input Security Layer</h3>
              <p className="text-slate-400 text-[11px] font-sans">
                Masks SSNs, 16-digit card numbers, CVVs, and PINs. Rejects prompt injection attacks before reaching LLM state.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-[#080808] p-4 rounded border border-white/10 space-y-2">
              <span className="text-[10px] font-bold text-purple-400 uppercase">2. LangGraph Supervisor</span>
              <h3 className="font-bold text-white text-sm">Intent & Urgency Router</h3>
              <p className="text-slate-400 text-[11px] font-sans">
                Classifies intent into 7 categories. Directs execution to specialized subgraphs (Fraud, Support, Knowledge RAG).
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-[#080808] p-4 rounded border border-white/10 space-y-2">
              <span className="text-[10px] font-bold text-amber-400 uppercase">3. MCP Gateway & 3 Servers</span>
              <h3 className="font-bold text-white text-sm">Controlled Tool Execution</h3>
              <p className="text-slate-400 text-[11px] font-sans">
                Enforces Zod schema validation, customer ownership checks, idempotency keys, and human analyst approval checks.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-[#080808] p-4 rounded border border-white/10 space-y-2">
              <span className="text-[10px] font-bold text-green-400 uppercase">4. Temporal & Audit Engine</span>
              <h3 className="font-bold text-white text-sm">Audit & SLA Workflows</h3>
              <p className="text-slate-400 text-[11px] font-sans">
                Logs immutable audit records. Manages dispute SLA timers, case creation, and real-time WebSocket notifications.
              </p>
            </div>
          </div>
        </div>
      )}

      {activeSection === 'mcp' && (
        <div className="bg-[#111111] rounded-xl border border-white/10 p-6 text-white space-y-6 shadow-xl">
          <h2 className="text-[10px] font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2 font-mono">
            <Server className="w-4 h-4 text-orange-500" /> Three MCP Servers & Tool Specifications
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Banking MCP */}
            <div className="bg-[#080808] p-5 rounded-xl border border-white/10 space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="font-bold text-sm text-orange-400">1. Banking MCP Server</span>
                <span className="text-[10px] font-mono bg-orange-600/20 text-orange-400 px-2 py-0.5 rounded font-bold">6 Tools</span>
              </div>
              <ul className="space-y-2 text-xs font-mono text-slate-300">
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-orange-400 font-bold">get_customer_profile</span>
                  <p className="text-[10px] text-slate-400 font-sans">Retrieves KYC and travel notice profile</p>
                </li>
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-orange-400 font-bold">get_account_summary</span>
                  <p className="text-[10px] text-slate-400 font-sans">Fetches checking & savings balance</p>
                </li>
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-orange-400 font-bold">get_transaction</span>
                  <p className="text-[10px] text-slate-400 font-sans">Looks up transaction metadata & device IP</p>
                </li>
                <li className="bg-[#111111] p-2 rounded border border-red-500/30">
                  <span className="text-red-500 font-bold">freeze_card</span>
                  <p className="text-[10px] text-red-400 font-sans">🔒 REQUIRES HUMAN ANALYST APPROVAL</p>
                </li>
              </ul>
            </div>

            {/* Fraud MCP */}
            <div className="bg-[#080808] p-5 rounded-xl border border-white/10 space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="font-bold text-sm text-orange-400">2. Fraud MCP Server</span>
                <span className="text-[10px] font-mono bg-orange-600/20 text-orange-400 px-2 py-0.5 rounded font-bold">6 Tools</span>
              </div>
              <ul className="space-y-2 text-xs font-mono text-slate-300">
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-orange-400 font-bold">calculate_fraud_score</span>
                  <p className="text-[10px] text-slate-400 font-sans">Runs rules, ML, isolation forest & graph score</p>
                </li>
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-orange-400 font-bold">get_related_entities</span>
                  <p className="text-[10px] text-slate-400 font-sans">Explores customer-device-IP network clusters</p>
                </li>
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-orange-400 font-bold">get_fraud_evidence</span>
                  <p className="text-[10px] text-slate-400 font-sans">Extracts evidence package for analyst review</p>
                </li>
              </ul>
            </div>

            {/* Case MCP */}
            <div className="bg-[#080808] p-5 rounded-xl border border-white/10 space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="font-bold text-sm text-purple-400">3. Case MCP Server</span>
                <span className="text-[10px] font-mono bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded font-bold">6 Tools</span>
              </div>
              <ul className="space-y-2 text-xs font-mono text-slate-300">
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-purple-300 font-bold">create_case</span>
                  <p className="text-[10px] text-slate-400 font-sans">Opens case in fraud ops queue</p>
                </li>
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-purple-300 font-bold">request_approval</span>
                  <p className="text-[10px] text-slate-400 font-sans">Queues Human-in-the-Loop analyst approval</p>
                </li>
                <li className="bg-[#111111] p-2 rounded border border-white/5">
                  <span className="text-purple-300 font-bold">send_customer_notification</span>
                  <p className="text-[10px] text-slate-400 font-sans">Dispatches SMS/Email dispute notification</p>
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {activeSection === 'evaluation' && (
        <EvaluationSuite />
      )}
    </div>
  );
};
