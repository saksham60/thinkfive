import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Zap,
  Activity,
  Bot,
  ShieldAlert,
  Search,
  FileText,
  CreditCard,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  Database,
  Terminal,
  Play,
  RotateCcw,
  Sliders,
  Layers,
  Lock,
  UserCheck,
  Building,
  GitBranch,
  Network,
  Share2,
  Inbox,
  AlertOctagon,
  Eye,
  HelpCircle
} from 'lucide-react';

export type AgentId = 'supervisor' | 'support' | 'transaction' | 'knowledge' | 'fraud' | 'risk' | 'case';

interface AIAgentsViewProps {
  initialAgentId?: AgentId;
  onSelectAgent?: (id: AgentId) => void;
}

// Pre-packaged Simulation Scenarios
const SIMULATION_SCENARIOS = [
  {
    id: 'unauthorized_purchase',
    title: '🚨 Unauthorized ₹45,000 Electronics Purchase (Stolen Card)',
    prompt: 'I see a charge of ₹45,000 at Luxe Electronics London that I did not make!',
    customerId: 'CUST-1001',
    transactionId: 'TXN-9021',
    category: 'Stolen Card / Unauthorized TXN'
  },
  {
    id: 'phishing_otp',
    title: '🎣 Phishing Attack & Foreign IP Login',
    prompt: 'Someone called claiming to be SentinelBank asking for my OTP and now money is missing.',
    customerId: 'CUST-1002',
    transactionId: 'TXN-8812',
    category: 'Phishing / Social Engineering'
  },
  {
    id: 'policy_dispute',
    title: '📚 Customer Policy Inquiry (Chargeback Dispute Procedure)',
    prompt: 'What is the exact process and SLA for filing a card dispute for unauthorized charges?',
    customerId: 'CUST-1001',
    category: 'General Policy Query'
  },
  {
    id: 'balance_check',
    title: '💳 Balance & Recent Transaction Check',
    prompt: 'What is my current checking account balance and my last 3 transactions?',
    customerId: 'CUST-1001',
    category: 'Customer Support Inquiry'
  }
];

export const AIAgentsView: React.FC<AIAgentsViewProps> = ({
  initialAgentId = 'supervisor',
  onSelectAgent
}) => {
  const [selectedAgent, setSelectedAgent] = useState<AgentId>(initialAgentId);
  const [isRunningSimulation, setIsRunningSimulation] = useState(false);
  const [simulationStep, setSimulationStep] = useState<number>(-1);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('unauthorized_purchase');
  const [customPrompt, setCustomPrompt] = useState<string>('I see a charge of ₹45,000 at Luxe Electronics London that I did not make!');
  const [ragQuery, setRagQuery] = useState<string>('fraud dispute procedure');

  // Sync prop changes
  useEffect(() => {
    if (initialAgentId) {
      setSelectedAgent(initialAgentId);
    }
  }, [initialAgentId]);

  const handleAgentClick = (id: AgentId) => {
    setSelectedAgent(id);
    if (onSelectAgent) onSelectAgent(id);
  };

  // Run LangGraph Simulation
  const handleRunSimulation = () => {
    setIsRunningSimulation(true);
    setSimulationStep(0);

    const steps = [0, 1, 2, 3, 4, 5, 6];
    let stepIdx = 0;

    const interval = setInterval(() => {
      stepIdx++;
      if (stepIdx < steps.length) {
        setSimulationStep(stepIdx);
        // Automatically pivot highlight if requested
      } else {
        clearInterval(interval);
        setIsRunningSimulation(false);
      }
    }, 1200);
  };

  const currentScenario = SIMULATION_SCENARIOS.find(s => s.id === selectedScenarioId) || SIMULATION_SCENARIOS[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 text-slate-100 font-sans">
      {/* Top Banner Header */}
      <div className="bg-[#111111] rounded-xl p-5 border border-white/10 text-white flex flex-col lg:flex-row lg:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-6 h-6 text-orange-500" />
            <h1 className="text-xl font-light tracking-tight text-white">LangGraph Multi-Agent Architecture</h1>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-orange-600/20 text-orange-400 border border-orange-500/30 font-mono">
              7 Autonomous AI Nodes
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Interactive multi-agent workflow orchestration. Select an agent node to view its responsibilities, live state, input/output pipelines, and sample execution traces.
          </p>
        </div>

        {/* Simulation Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedScenarioId}
            onChange={(e) => {
              setSelectedScenarioId(e.target.value);
              const sc = SIMULATION_SCENARIOS.find(s => s.id === e.target.value);
              if (sc) setCustomPrompt(sc.prompt);
            }}
            className="bg-[#080808] text-xs font-mono text-slate-200 border border-white/10 rounded px-3 py-2 outline-none focus:border-orange-500"
          >
            {SIMULATION_SCENARIOS.map(s => (
              <option key={s.id} value={s.id}>{s.title}</option>
            ))}
          </select>

          <button
            onClick={handleRunSimulation}
            disabled={isRunningSimulation}
            className={`flex items-center space-x-2 px-4 py-2 rounded font-mono text-xs font-bold uppercase transition-all shadow-lg ${
              isRunningSimulation
                ? 'bg-orange-600/50 text-white cursor-wait animate-pulse'
                : 'bg-orange-600 hover:bg-orange-500 text-white shadow-orange-600/20'
            }`}
          >
            <Play className={`w-3.5 h-3.5 ${isRunningSimulation ? 'animate-spin' : 'fill-current'}`} />
            <span>{isRunningSimulation ? `Simulating Node ${simulationStep + 1}/7...` : 'Run LangGraph Simulation'}</span>
          </button>
        </div>
      </div>

      {/* Visual LangGraph Workflow Pipeline Diagram */}
      <div className="bg-[#111111] rounded-xl p-5 border border-white/10 space-y-3 shadow-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center space-x-2">
            <GitBranch className="w-4 h-4 text-orange-500" />
            <span className="text-xs font-bold uppercase tracking-widest text-slate-300 font-mono">
              LangGraph State Directed Acyclic Graph (DAG)
            </span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            State Persistence: MemorySaver & Postgres Checkpointer
          </span>
        </div>

        {/* Node Pipeline Diagram */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 pt-2">
          {/* Node 1: Supervisor */}
          <button
            onClick={() => handleAgentClick('supervisor')}
            className={`p-3 rounded-lg border text-left transition-all relative ${
              selectedAgent === 'supervisor'
                ? 'bg-orange-600/20 border-orange-500 text-white shadow-lg shadow-orange-600/10'
                : 'bg-[#080808] border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200'
            } ${simulationStep === 0 ? 'ring-2 ring-orange-400 animate-pulse' : ''}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] font-mono font-bold text-orange-400 uppercase">Node 01</span>
              <Bot className="w-3.5 h-3.5 text-orange-400" />
            </div>
            <p className="text-xs font-bold truncate">Supervisor</p>
            <p className="text-[10px] text-slate-500 font-mono truncate">Orchestrator</p>
          </button>

          {/* Node 2: Support */}
          <button
            onClick={() => handleAgentClick('support')}
            className={`p-3 rounded-lg border text-left transition-all relative ${
              selectedAgent === 'support'
                ? 'bg-orange-600/20 border-orange-500 text-white shadow-lg shadow-orange-600/10'
                : 'bg-[#080808] border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200'
            } ${simulationStep === 1 ? 'ring-2 ring-orange-400 animate-pulse' : ''}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] font-mono font-bold text-blue-400 uppercase">Node 02</span>
              <HelpCircle className="w-3.5 h-3.5 text-blue-400" />
            </div>
            <p className="text-xs font-bold truncate">Customer Support</p>
            <p className="text-[10px] text-slate-500 font-mono truncate">MCP Gateway</p>
          </button>

          {/* Node 3: Transaction */}
          <button
            onClick={() => handleAgentClick('transaction')}
            className={`p-3 rounded-lg border text-left transition-all relative ${
              selectedAgent === 'transaction'
                ? 'bg-orange-600/20 border-orange-500 text-white shadow-lg shadow-orange-600/10'
                : 'bg-[#080808] border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200'
            } ${simulationStep === 2 ? 'ring-2 ring-orange-400 animate-pulse' : ''}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] font-mono font-bold text-cyan-400 uppercase">Node 03</span>
              <CreditCard className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <p className="text-xs font-bold truncate">Transaction</p>
            <p className="text-[10px] text-slate-500 font-mono truncate">Anomaly Baseline</p>
          </button>

          {/* Node 4: Knowledge */}
          <button
            onClick={() => handleAgentClick('knowledge')}
            className={`p-3 rounded-lg border text-left transition-all relative ${
              selectedAgent === 'knowledge'
                ? 'bg-orange-600/20 border-orange-500 text-white shadow-lg shadow-orange-600/10'
                : 'bg-[#080808] border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200'
            } ${simulationStep === 3 ? 'ring-2 ring-orange-400 animate-pulse' : ''}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] font-mono font-bold text-emerald-400 uppercase">Node 04</span>
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <p className="text-xs font-bold truncate">Knowledge (RAG)</p>
            <p className="text-[10px] text-slate-500 font-mono truncate">LlamaIndex SOPs</p>
          </button>

          {/* Node 5: Fraud */}
          <button
            onClick={() => handleAgentClick('fraud')}
            className={`p-3 rounded-lg border text-left transition-all relative ${
              selectedAgent === 'fraud'
                ? 'bg-orange-600/20 border-orange-500 text-white shadow-lg shadow-orange-600/10'
                : 'bg-[#080808] border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200'
            } ${simulationStep === 4 ? 'ring-2 ring-orange-400 animate-pulse' : ''}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] font-mono font-bold text-red-400 uppercase">Node 05</span>
              <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
            </div>
            <p className="text-xs font-bold truncate">Fraud Agent</p>
            <p className="text-[10px] text-slate-500 font-mono truncate">Neo4j Intelligence</p>
          </button>

          {/* Node 6: Risk */}
          <button
            onClick={() => handleAgentClick('risk')}
            className={`p-3 rounded-lg border text-left transition-all relative ${
              selectedAgent === 'risk'
                ? 'bg-orange-600/20 border-orange-500 text-white shadow-lg shadow-orange-600/10'
                : 'bg-[#080808] border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200'
            } ${simulationStep === 5 ? 'ring-2 ring-orange-400 animate-pulse' : ''}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] font-mono font-bold text-amber-400 uppercase">Node 06</span>
              <Activity className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-xs font-bold truncate">Risk Scoring</p>
            <p className="text-[10px] text-slate-500 font-mono truncate">Explainable Rules</p>
          </button>

          {/* Node 7: Case */}
          <button
            onClick={() => handleAgentClick('case')}
            className={`p-3 rounded-lg border text-left transition-all relative ${
              selectedAgent === 'case'
                ? 'bg-orange-600/20 border-orange-500 text-white shadow-lg shadow-orange-600/10'
                : 'bg-[#080808] border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200'
            } ${simulationStep === 6 ? 'ring-2 ring-orange-400 animate-pulse' : ''}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] font-mono font-bold text-purple-400 uppercase">Node 07</span>
              <Layers className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <p className="text-xs font-bold truncate">Case Agent</p>
            <p className="text-[10px] text-slate-500 font-mono truncate">Temporal Workflows</p>
          </button>
        </div>
      </div>

      {/* Main Agent Detail View Container */}
      <div className="space-y-6">
        {/* AGENT 1: SUPERVISOR AGENT */}
        {selectedAgent === 'supervisor' && (
          <SupervisorAgentDetail
            currentPrompt={customPrompt}
            scenario={currentScenario}
          />
        )}

        {/* AGENT 2: CUSTOMER SUPPORT AGENT */}
        {selectedAgent === 'support' && (
          <CustomerSupportAgentDetail
            currentPrompt={customPrompt}
            scenario={currentScenario}
          />
        )}

        {/* AGENT 3: TRANSACTION AGENT */}
        {selectedAgent === 'transaction' && (
          <TransactionAgentDetail
            scenario={currentScenario}
          />
        )}

        {/* AGENT 4: KNOWLEDGE AGENT (RAG) */}
        {selectedAgent === 'knowledge' && (
          <KnowledgeAgentDetail
            ragQuery={ragQuery}
            setRagQuery={setRagQuery}
          />
        )}

        {/* AGENT 5: FRAUD AGENT */}
        {selectedAgent === 'fraud' && (
          <FraudAgentDetail
            scenario={currentScenario}
          />
        )}

        {/* AGENT 6: RISK AGENT */}
        {selectedAgent === 'risk' && (
          <RiskAgentDetail
            scenario={currentScenario}
          />
        )}

        {/* AGENT 7: CASE AGENT */}
        {selectedAgent === 'case' && (
          <CaseAgentDetail
            scenario={currentScenario}
          />
        )}
      </div>
    </div>
  );
};

/* ====================================================================
   AGENT 1: SUPERVISOR AGENT
   ==================================================================== */
function SupervisorAgentDetail({ currentPrompt, scenario }: { currentPrompt: string; scenario: any }) {
  return (
    <div className="space-y-6">
      {/* Header Badge & Overview */}
      <div className="bg-[#111111] rounded-xl border border-orange-500/30 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-orange-600/20 border border-orange-500/40 flex items-center justify-center text-orange-400">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">1. Supervisor Agent</h2>
                <span className="text-[10px] bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-orange-500/30">
                  Orchestrator
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Central LangGraph workflow state machine & decision orchestrator.</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-mono">Status:</span>
            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded font-mono font-bold uppercase border border-emerald-500/30 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              ROUTING_ACTIVE
            </span>
          </div>
        </div>

        {/* Responsibilities Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-orange-400 font-mono font-bold uppercase block">Core Task 01</span>
            <p className="text-xs font-semibold text-slate-200">Detect customer intent and urgency level</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-orange-400 font-mono font-bold uppercase block">Core Task 02</span>
            <p className="text-xs font-semibold text-slate-200">Maintain & persist LangGraph state graph</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-orange-400 font-mono font-bold uppercase block">Core Task 03</span>
            <p className="text-xs font-semibold text-slate-200">Route requests to appropriate specialized agent</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-orange-400 font-mono font-bold uppercase block">Core Task 04</span>
            <p className="text-xs font-semibold text-slate-200">Coordinate parallel multi-agent execution</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-orange-400 font-mono font-bold uppercase block">Core Task 05</span>
            <p className="text-xs font-semibold text-slate-200">Decide when to escalate to human analyst</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-orange-400 font-mono font-bold uppercase block">Core Task 06</span>
            <p className="text-xs font-semibold text-slate-200">Require human approval for sensitive actions</p>
          </div>
        </div>
      </div>

      {/* Live State & Decision Telemetry Panel */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Real-time Routing State */}
        <div className="lg:col-span-2 bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl font-mono">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <Zap className="w-4 h-4 text-orange-500" /> Active Supervisor Decisions
            </span>
            <span className="text-[10px] text-slate-500">Trace ID: TR-8912-SUP</span>
          </div>

          <div className="grid sm:grid-cols-2 gap-3 text-xs">
            <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Detected Intent</span>
              <p className="text-sm font-bold text-orange-400">{scenario.category}</p>
            </div>
            <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Urgency Priority</span>
              <p className="text-sm font-bold text-red-400">P0 - CRITICAL (SLA: 15 MIN)</p>
            </div>
            <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Next Agent Target</span>
              <p className="text-sm font-bold text-cyan-400">Fraud Agent & Risk Agent</p>
            </div>
            <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-bold">LangGraph State</span>
              <p className="text-sm font-bold text-emerald-400">EVALUATION_IN_PROGRESS</p>
            </div>
          </div>

          {/* Decision Rationale */}
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-2">
            <span className="text-[10px] text-slate-400 font-bold uppercase block">Routing Decision Rationale</span>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              Customer message contains explicit tokens associated with unauthorized transactions and card misuse. High risk deviation detected against historical baseline. Routing message context to Transaction Agent for anomaly validation and triggering Fraud & Risk evaluation nodes concurrently.
            </p>
          </div>
        </div>

        {/* Right Col: Human Approval Requirement */}
        <div className="bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl font-mono">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-white/10 pb-3">
            <Lock className="w-4 h-4 text-red-500" /> Human Approval Governance
          </span>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center p-2.5 rounded bg-[#080808] border border-white/5">
              <span className="text-slate-400">Account Block / Freeze:</span>
              <span className="text-amber-400 font-bold">REQUIRES APPROVAL</span>
            </div>
            <div className="flex justify-between items-center p-2.5 rounded bg-[#080808] border border-white/5">
              <span className="text-slate-400">Transaction Reversal:</span>
              <span className="text-amber-400 font-bold">REQUIRES APPROVAL</span>
            </div>
            <div className="flex justify-between items-center p-2.5 rounded bg-[#080808] border border-white/5">
              <span className="text-slate-400">Temporary Card Lock:</span>
              <span className="text-emerald-400 font-bold">AUTO-EXECUTABLE</span>
            </div>
          </div>
        </div>
      </div>

      {/* Input / Output Data Pipelines */}
      <InputOutputPanel
        inputData={{
          customerId: scenario.customerId,
          rawUserMessage: currentPrompt,
          sessionRole: 'customer',
          securityCheckStatus: 'PASSED_PRESIDIO_PII_CLEAN'
        }}
        outputData={{
          intent: scenario.category,
          urgency: 'P0_CRITICAL',
          workflowState: 'EVALUATION_IN_PROGRESS',
          routesTo: ['transaction_agent', 'fraud_agent', 'risk_agent'],
          escalationRequired: true
        }}
      />

      {/* Sample Execution Logs */}
      <ExecutionLogsPanel logs={[
        { time: '02:14:01', level: 'INFO', text: 'Presidio Guardrails check passed. 0 PII violations found.' },
        { time: '02:14:02', level: 'ROUTE', text: `Supervisor detected intent '${scenario.category}'. Urgency: HIGH.` },
        { time: '02:14:02', level: 'STATE', text: 'LangGraph State persisted to MemorySaver checkpointer. State ID: chk_8912.' },
        { time: '02:14:03', level: 'DISPATCH', text: 'Dispatched context to Transaction & Fraud Subgraphs concurrently.' }
      ]} />
    </div>
  );
}

/* ====================================================================
   AGENT 2: CUSTOMER SUPPORT AGENT
   ==================================================================== */
function CustomerSupportAgentDetail({ currentPrompt, scenario }: { currentPrompt: string; scenario: any }) {
  return (
    <div className="space-y-6">
      <div className="bg-[#111111] rounded-xl border border-blue-500/30 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">2. Customer Support Agent</h2>
                <span className="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-blue-500/30">
                  Banking Support & MCP Gateway
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Handles general banking queries, balance lookups, and customer communications.</p>
            </div>
          </div>

          <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded font-mono font-bold uppercase border border-emerald-500/30">
            MCP SERVER CONNECTED
          </span>
        </div>

        {/* Responsibilities Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-blue-400 font-mono font-bold uppercase block">Core Task 01</span>
            <p className="text-xs font-semibold text-slate-200">Balance inquiries & account summary lookups</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-blue-400 font-mono font-bold uppercase block">Core Task 02</span>
            <p className="text-xs font-semibold text-slate-200">Account and card status FAQs</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-blue-400 font-mono font-bold uppercase block">Core Task 03</span>
            <p className="text-xs font-semibold text-slate-200">Service requests & complaint registration</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-blue-400 font-mono font-bold uppercase block">Core Task 04</span>
            <p className="text-xs font-semibold text-slate-200">Fetch customer-specific data via Banking MCP Server</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-blue-400 font-mono font-bold uppercase block">Core Task 05</span>
            <p className="text-xs font-semibold text-slate-200">Query Knowledge Agent for policies and SOPs</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-blue-400 font-mono font-bold uppercase block">Core Task 06</span>
            <p className="text-xs font-semibold text-slate-200">General empathetic customer communications</p>
          </div>
        </div>
      </div>

      {/* Banking MCP Tool Execution Console */}
      <div className="grid lg:grid-cols-2 gap-6 font-mono">
        <div className="bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-white/10 pb-3">
            <Database className="w-4 h-4 text-blue-400" /> Banking MCP Server Tools
          </span>

          <div className="space-y-2 text-xs">
            <div className="p-3 bg-[#080808] rounded border border-white/5 flex justify-between items-center">
              <div>
                <p className="font-bold text-blue-400">get_account_balance</p>
                <p className="text-[10px] text-slate-500">Fetches current checking & savings balance</p>
              </div>
              <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">EXECUTED</span>
            </div>

            <div className="p-3 bg-[#080808] rounded border border-white/5 flex justify-between items-center">
              <div>
                <p className="font-bold text-blue-400">get_card_status</p>
                <p className="text-[10px] text-slate-500">Checks active/frozen status of debit cards</p>
              </div>
              <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">EXECUTED</span>
            </div>

            <div className="p-3 bg-[#080808] rounded border border-white/5 flex justify-between items-center">
              <div>
                <p className="font-bold text-blue-400">query_policy_docs</p>
                <p className="text-[10px] text-slate-500">Submits policy query to Knowledge Agent RAG</p>
              </div>
              <span className="text-[10px] text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">ROUTED</span>
            </div>
          </div>
        </div>

        {/* Customer Communication Draft */}
        <div className="bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-white/10 pb-3">
            <Bot className="w-4 h-4 text-blue-400" /> AI Customer Communication Output
          </span>

          <div className="bg-[#080808] p-4 rounded border border-blue-500/30 text-xs font-sans space-y-2 text-slate-200 leading-relaxed">
            <p className="font-bold text-blue-400 font-mono text-[11px]">Draft Customer Response:</p>
            <p>
              "Hello Priya, I understand your concern regarding the unrecognized transaction at Luxe Electronics London (₹45,000). I have immediately flagged this transaction for fraud investigation and routed it to our Fraud Operations team."
            </p>
            <p>
              "Your debit card ending in •••• 9821 has been temporarily locked to prevent further charges. Our risk assessment team is reviewing the case."
            </p>
          </div>
        </div>
      </div>

      <InputOutputPanel
        inputData={{
          customerId: scenario.customerId,
          messageText: currentPrompt,
          mcpServerAuthorized: true
        }}
        outputData={{
          mcpToolsCalled: ['get_account_balance', 'get_card_status'],
          knowledgeAgentQuery: 'dispute_procedure_stolen_card',
          responseGenerated: true
        }}
      />

      <ExecutionLogsPanel logs={[
        { time: '02:14:03', level: 'MCP_CALL', text: 'Invoking MCP Tool BankingMCP.get_account_summary for CUST-1001.' },
        { time: '02:14:04', level: 'MCP_CALL', text: 'Invoking MCP Tool BankingMCP.get_card_status for CUST-1001.' },
        { time: '02:14:04', level: 'INFO', text: 'Queried Knowledge Agent RAG node for dispute procedure guidelines.' }
      ]} />
    </div>
  );
}

/* ====================================================================
   AGENT 3: TRANSACTION AGENT
   ==================================================================== */
function TransactionAgentDetail({ scenario }: { scenario: any }) {
  return (
    <div className="space-y-6">
      <div className="bg-[#111111] rounded-xl border border-cyan-500/30 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">3. Transaction Agent</h2>
                <span className="text-[10px] bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-cyan-500/30">
                  Transaction & Anomaly Analyzer
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Analyzes customer transactions, detects duplicates, and checks baseline deviations.</p>
            </div>
          </div>

          <span className="text-xs bg-red-500/20 text-red-400 px-2.5 py-1 rounded font-mono font-bold uppercase border border-red-500/30">
            ANOMALY FLAG DETECTED
          </span>
        </div>

        {/* Responsibilities Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-cyan-400 font-mono font-bold uppercase block">Core Task 01</span>
            <p className="text-xs font-semibold text-slate-200">Retrieve detailed transaction records</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-cyan-400 font-mono font-bold uppercase block">Core Task 02</span>
            <p className="text-xs font-semibold text-slate-200">Display recent transactions with merchant metadata</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-cyan-400 font-mono font-bold uppercase block">Core Task 03</span>
            <p className="text-xs font-semibold text-slate-200">Detect duplicate or double-processed charges</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-cyan-400 font-mono font-bold uppercase block">Core Task 04</span>
            <p className="text-xs font-semibold text-slate-200">Explain merchant, amount, MCC, and location details</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-cyan-400 font-mono font-bold uppercase block">Core Task 05</span>
            <p className="text-xs font-semibold text-slate-200">Compare against customer's baseline normal behavior</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-cyan-400 font-mono font-bold uppercase block">Core Task 06</span>
            <p className="text-xs font-semibold text-slate-200">Forward suspicious transactions to Fraud Agent</p>
          </div>
        </div>
      </div>

      {/* Transaction Analysis Table & Anomaly Breakdown */}
      <div className="grid lg:grid-cols-3 gap-6 font-mono">
        <div className="lg:col-span-2 bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-white/10 pb-3">
            <CreditCard className="w-4 h-4 text-cyan-400" /> Target Transaction Under Analysis
          </span>

          <div className="bg-[#080808] p-4 rounded border border-white/10 space-y-3 text-xs">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-bold">Transaction ID</span>
                <span className="font-bold text-slate-200">TXN-9021</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-bold">Merchant Name</span>
                <span className="font-bold text-slate-200">Luxe Electronics UK</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-bold">Amount</span>
                <span className="font-bold text-red-400 text-sm">₹45,000.00</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-bold">Merchant Category</span>
                <span className="text-slate-300">MCC 5732 - Electronics</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-bold">Location</span>
                <span className="text-slate-300">London, United Kingdom</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-bold">Device IP</span>
                <span className="text-slate-300">185.220.101.4 (TOR Exit)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Behavioral Deviation Comparison */}
        <div className="bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl font-mono">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-white/10 pb-3">
            <Activity className="w-4 h-4 text-cyan-400" /> Normal Baseline Comparison
          </span>

          <div className="space-y-3 text-xs">
            <div className="p-2.5 bg-[#080808] rounded border border-white/5 space-y-1">
              <span className="text-slate-400 text-[10px] uppercase font-bold">30-Day Avg Spend per TXN</span>
              <p className="text-sm font-bold text-emerald-400">₹3,200.00</p>
            </div>
            <div className="p-2.5 bg-[#080808] rounded border border-white/5 space-y-1">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Current TXN Deviation</span>
              <p className="text-sm font-bold text-red-400">14.06x Above Average</p>
            </div>
            <div className="p-2.5 bg-[#080808] rounded border border-white/5 space-y-1">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Duplicate Check Status</span>
              <p className="text-xs font-bold text-slate-200">NO_DUPLICATES_FOUND</p>
            </div>
          </div>
        </div>
      </div>

      <InputOutputPanel
        inputData={{
          transactionId: 'TXN-9021',
          customerId: 'CUST-1001',
          accountId: 'ACC-00192'
        }}
        outputData={{
          merchantName: 'Luxe Electronics UK',
          amount: 45000,
          location: 'London, UK',
          behavioralDeviation: '14x_ABOVE_BASELINE',
          forwardToFraudAgent: true
        }}
      />

      <ExecutionLogsPanel logs={[
        { time: '02:14:04', level: 'INFO', text: 'Retrieved transaction record TXN-9021 via Banking MCP.' },
        { time: '02:14:05', level: 'INFO', text: 'Ran duplicate detection against 24h window. 0 duplicates found.' },
        { time: '02:14:05', level: 'WARN', text: 'Baseline deviation: ₹45,000 vs 30-day avg ₹3,200. Anomaly flag raised.' },
        { time: '02:14:05', level: 'DISPATCH', text: 'Forwarding transaction telemetry packet to Fraud Agent node.' }
      ]} />
    </div>
  );
}

/* ====================================================================
   AGENT 4: KNOWLEDGE AGENT (LlamaIndex RAG)
   ==================================================================== */
function KnowledgeAgentDetail({ ragQuery, setRagQuery }: { ragQuery: string; setRagQuery: (q: string) => void }) {
  return (
    <div className="space-y-6">
      <div className="bg-[#111111] rounded-xl border border-emerald-500/30 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">4. Knowledge Agent (LlamaIndex RAG)</h2>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-emerald-500/30">
                  RAG Policy Search
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Retrieves banking policies, dispute procedures, KYC guidelines, and compliance SOPs.</p>
            </div>
          </div>

          <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-3 py-1 rounded text-[11px] font-mono font-bold uppercase flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5" />
            NO LIVE BALANCE ACCESS
          </div>
        </div>

        {/* Responsibilities Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase block">Core Task 01</span>
            <p className="text-xs font-semibold text-slate-200">Search banking policies & regulations</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase block">Core Task 02</span>
            <p className="text-xs font-semibold text-slate-200">Retrieve fraud dispute & chargeback procedures</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase block">Core Task 03</span>
            <p className="text-xs font-semibold text-slate-200">Search KYC & identity guidelines</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase block">Core Task 04</span>
            <p className="text-xs font-semibold text-slate-200">Search FAQs & help center documentation</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase block">Core Task 05</span>
            <p className="text-xs font-semibold text-slate-200">Retrieve compliance & audit SOPs</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase block">Core Task 06</span>
            <p className="text-xs font-semibold text-slate-200">Display document version, source, and effective date</p>
          </div>
        </div>
      </div>

      {/* RAG Search Tester */}
      <div className="bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest font-mono flex items-center gap-2">
            <Search className="w-4 h-4 text-emerald-400" /> Vector Database Policy Corpus (LlamaIndex)
          </span>

          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              placeholder="Query policy vector db..."
              className="bg-[#080808] border border-white/10 rounded px-3 py-1.5 text-xs text-slate-200 font-mono outline-none focus:border-emerald-500 w-64"
            />
            <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded font-mono font-bold">
              3 DOCUMENTS FOUND
            </span>
          </div>
        </div>

        {/* Retrieved Document Cards */}
        <div className="grid md:grid-cols-2 gap-4 font-mono">
          <div className="bg-[#080808] p-4 rounded-lg border border-white/10 space-y-2">
            <div className="flex items-center justify-between border-b border-white/5 pb-2 text-xs">
              <span className="font-bold text-emerald-400">DOC-SOP-001</span>
              <span className="text-[10px] text-slate-400 bg-white/5 px-2 py-0.5 rounded">Similarity: 0.94</span>
            </div>
            <p className="text-xs font-bold text-white font-sans">Fraud Dispute & Chargeback Policy</p>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              In cases of reported unauthorized card transactions, the card must be immediately frozen and a temporary credit issued within 48 hours pending investigation.
            </p>

            <div className="pt-2 border-t border-white/5 text-[10px] text-slate-400 grid grid-cols-3 gap-1">
              <div>Version: <strong className="text-slate-200">v3.2.0</strong></div>
              <div>Source: <strong className="text-slate-200">Compliance DB</strong></div>
              <div>Effective: <strong className="text-slate-200">Jan 2026</strong></div>
            </div>
          </div>

          <div className="bg-[#080808] p-4 rounded-lg border border-white/10 space-y-2">
            <div className="flex items-center justify-between border-b border-white/5 pb-2 text-xs">
              <span className="font-bold text-emerald-400">DOC-SOP-004</span>
              <span className="text-[10px] text-slate-400 bg-white/5 px-2 py-0.5 rounded">Similarity: 0.89</span>
            </div>
            <p className="text-xs font-bold text-white font-sans">Stolen Debit Card Emergency Freeze Protocol</p>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              Customer initiated stolen card reports require immediate token invalidation across Apple Pay and Google Wallet endpoints.
            </p>

            <div className="pt-2 border-t border-white/5 text-[10px] text-slate-400 grid grid-cols-3 gap-1">
              <div>Version: <strong className="text-slate-200">v2.1.0</strong></div>
              <div>Source: <strong className="text-slate-200">Risk Guidelines</strong></div>
              <div>Effective: <strong className="text-slate-200">Mar 2026</strong></div>
            </div>
          </div>
        </div>
      </div>

      <InputOutputPanel
        inputData={{
          query: ragQuery,
          topK: 3,
          minScore: 0.75
        }}
        outputData={{
          documentsRetrieved: 3,
          highestRelevanceDoc: 'DOC-SOP-001',
          summaryAnswerGenerated: true
        }}
      />

      <ExecutionLogsPanel logs={[
        { time: '02:14:05', level: 'RAG_SEARCH', text: `Vector similarity search for query '${ragQuery}' against 48 policy embeddings.` },
        { time: '02:14:06', level: 'INFO', text: 'Retrieved DOC-SOP-001 (Similarity 0.94) and DOC-SOP-004 (Similarity 0.89).' }
      ]} />
    </div>
  );
}

/* ====================================================================
   AGENT 5: FRAUD AGENT (Neo4j & Evidence Collector)
   ==================================================================== */
function FraudAgentDetail({ scenario }: { scenario: any }) {
  return (
    <div className="space-y-6">
      <div className="bg-[#111111] rounded-xl border border-red-500/30 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-red-600/20 border border-red-500/40 flex items-center justify-center text-red-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">5. Fraud Agent</h2>
                <span className="text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-red-500/30">
                  Neo4j & Evidence Collector
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Investigates suspicious transactions, queries graph DB for shared device links, and collects multi-source evidence.</p>
            </div>
          </div>

          <span className="text-xs bg-red-500/20 text-red-400 px-2.5 py-1 rounded font-mono font-bold uppercase border border-red-500/30">
            HIGH FRAUD PROBABILITY
          </span>
        </div>

        {/* Responsibilities Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-red-400 font-mono font-bold uppercase block">Core Task 01</span>
            <p className="text-xs font-semibold text-slate-200">Analyze suspicious transactions & rule breaches</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-red-400 font-mono font-bold uppercase block">Core Task 02</span>
            <p className="text-xs font-semibold text-slate-200">Retrieve fraud alerts & historical incident logs</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-red-400 font-mono font-bold uppercase block">Core Task 03</span>
            <p className="text-xs font-semibold text-slate-200">Check device hash & IP velocity risk profiles</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-red-400 font-mono font-bold uppercase block">Core Task 04</span>
            <p className="text-xs font-semibold text-slate-200">Retrieve customer fraud history & dispute patterns</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-red-400 font-mono font-bold uppercase block">Core Task 05</span>
            <p className="text-xs font-semibold text-slate-200">Query Neo4j Graph DB for related entities & ring clusters</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-red-400 font-mono font-bold uppercase block">Core Task 06</span>
            <p className="text-xs font-semibold text-slate-200">Generate structured Fraud Investigation Summary</p>
          </div>
        </div>
      </div>

      {/* Fraud Investigation Summary Card */}
      <div className="bg-[#111111] rounded-xl border border-red-500/40 p-5 space-y-4 shadow-xl font-mono">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <span className="text-xs font-bold text-red-400 uppercase tracking-widest flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-red-400" /> Fraud Investigation Summary Output
          </span>
          <span className="text-[10px] text-slate-500">Node: Neo4j_Evidence_Engine</span>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="bg-[#080808] p-3 rounded border border-white/10 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Fraud Probability</span>
            <p className="text-2xl font-bold text-red-400">94.2%</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/10 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Rules Violated</span>
            <p className="text-sm font-bold text-orange-400">3 Rules Triggered</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/10 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Neo4j Cluster Link</span>
            <p className="text-sm font-bold text-purple-400">3 Shared Accounts</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/10 space-y-1">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Recommended Action</span>
            <p className="text-xs font-bold text-emerald-400">Freeze Debit Card</p>
          </div>
        </div>

        {/* Detailed Evidence Collected */}
        <div className="bg-[#080808] p-4 rounded border border-white/5 space-y-2 text-xs font-sans">
          <p className="font-bold font-mono text-xs text-slate-200">Collected Evidence Checklist:</p>
          <ul className="space-y-1 text-slate-300 list-disc list-inside">
            <li><strong>IP Velocity Mismatch:</strong> Transaction originated from IP 185.220.101.4 (London, TOR exit node).</li>
            <li><strong>Neo4j Graph Relationship:</strong> Device hash DEV-RING-X992 is associated with 2 other previously flagged fraudulent customer profiles.</li>
            <li><strong>XGBoost ML Fraud Model:</strong> Raw score 0.942 (Threshold: 0.85).</li>
            <li><strong>Customer Fraud History:</strong> 0 prior disputes reported in last 12 months.</li>
          </ul>
        </div>
      </div>

      <InputOutputPanel
        inputData={{
          transactionId: 'TXN-9021',
          customerId: 'CUST-1001',
          deviceHash: 'DEV-RING-X992',
          ipHash: '185.220.101.4'
        }}
        outputData={{
          fraudProbability: 0.942,
          evidenceCount: 4,
          neo4jClusterFound: true,
          sharedAccounts: ['CUST-1001', 'CUST-1088', 'CUST-2019'],
          recommendedAction: 'temporary_card_freeze'
        }}
      />

      <ExecutionLogsPanel logs={[
        { time: '02:14:06', level: 'GRAPH_QUERY', text: 'Executing Neo4j Cypher query MATCH (d:Device {hash: "DEV-RING-X992"})-[:USED_BY]->(c:Customer) RETURN c.' },
        { time: '02:14:07', level: 'WARN', text: 'Neo4j detected 3 linked customer accounts sharing this device hash.' },
        { time: '02:14:07', level: 'INFO', text: 'Calculated Fraud Probability score: 0.942.' }
      ]} />
    </div>
  );
}

/* ====================================================================
   AGENT 6: RISK AGENT (Explainable Risk Scoring)
   ==================================================================== */
function RiskAgentDetail({ scenario }: { scenario: any }) {
  return (
    <div className="space-y-6">
      <div className="bg-[#111111] rounded-xl border border-amber-500/30 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-amber-600/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">6. Risk Agent</h2>
                <span className="text-[10px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-amber-500/30">
                  Explainable Risk Scoring Engine
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Consolidates ML fraud scores, business rules, and graph risk into an explainable score (0-100).</p>
            </div>
          </div>

          <div className="bg-amber-500/10 border border-amber-500/30 text-amber-400 px-3 py-1 rounded text-[11px] font-mono font-bold uppercase flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            RECOMMENDS ONLY (NEVER EXECUTES)
          </div>
        </div>

        {/* Explicit Constraint Notice */}
        <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded text-xs font-mono text-amber-300 flex items-center gap-2">
          <AlertOctagon className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span><strong>Critical Policy Rule:</strong> The Risk Agent ONLY recommends risk scores and action policies. It NEVER executes card blocks or balance locks directly.</span>
        </div>

        {/* Responsibilities Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-amber-400 font-mono font-bold uppercase block">Core Task 01</span>
            <p className="text-xs font-semibold text-slate-200">Combine ML fraud model probability scores</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-amber-400 font-mono font-bold uppercase block">Core Task 02</span>
            <p className="text-xs font-semibold text-slate-200">Apply deterministic banking business rules</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-amber-400 font-mono font-bold uppercase block">Core Task 03</span>
            <p className="text-xs font-semibold text-slate-200">Include anomaly detection baseline results</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-amber-400 font-mono font-bold uppercase block">Core Task 04</span>
            <p className="text-xs font-semibold text-slate-200">Include graph-risk relationship scores</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-amber-400 font-mono font-bold uppercase block">Core Task 05</span>
            <p className="text-xs font-semibold text-slate-200">Produce consolidated Risk Score (0–100)</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-amber-400 font-mono font-bold uppercase block">Core Task 06</span>
            <p className="text-xs font-semibold text-slate-200">Assign Low/Medium/High/Critical priority and approval tag</p>
          </div>
        </div>
      </div>

      {/* Explainable Risk Score Breakdown */}
      <div className="grid lg:grid-cols-3 gap-6 font-mono">
        <div className="lg:col-span-2 bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-white/10 pb-3">
            <Sliders className="w-4 h-4 text-amber-400" /> Explainable Risk Composite Meter
          </span>

          <div className="bg-[#080808] p-4 rounded border border-white/10 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-xs text-slate-400 uppercase font-bold">Consolidated Risk Score</span>
              <span className="text-2xl font-bold text-red-400">88 / 100</span>
            </div>

            {/* Risk Bar */}
            <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden">
              <div className="bg-gradient-to-r from-amber-500 to-red-600 h-full w-[88%] rounded-full"></div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px] pt-2 border-t border-white/5">
              <div>ML Score: <strong className="text-slate-200">94/100</strong></div>
              <div>Rule Score: <strong className="text-slate-200">85/100</strong></div>
              <div>Anomaly Score: <strong className="text-slate-200">90/100</strong></div>
              <div>Graph Score: <strong className="text-slate-200">83/100</strong></div>
            </div>
          </div>
        </div>

        <div className="bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl font-mono">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-white/10 pb-3">
            <UserCheck className="w-4 h-4 text-amber-400" /> Human Approval Governance Tag
          </span>

          <div className="space-y-3 text-xs">
            <div className="p-2.5 bg-[#080808] rounded border border-white/5 space-y-1">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Priority Rating</span>
              <p className="text-sm font-bold text-red-400">CRITICAL PRIORITY</p>
            </div>
            <div className="p-2.5 bg-[#080808] rounded border border-white/5 space-y-1">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Human Approval Required?</span>
              <p className="text-sm font-bold text-amber-400">YES (ANALYST APPROVAL NEEDED)</p>
            </div>
          </div>
        </div>
      </div>

      <InputOutputPanel
        inputData={{
          fraudProbability: 0.942,
          ruleViolations: 3,
          graphClusterScore: 0.83,
          anomalyScore: 0.90
        }}
        outputData={{
          compositeRiskScore: 88,
          priority: 'Critical',
          recommendedAction: 'temporary_card_freeze',
          humanApprovalRequired: true
        }}
      />

      <ExecutionLogsPanel logs={[
        { time: '02:14:07', level: 'INFO', text: 'Combined weights: 40% ML + 25% Rules + 20% Anomaly + 15% Graph.' },
        { time: '02:14:08', level: 'SCORE', text: 'Final Explainable Risk Score calculated: 88/100 (Critical Priority).' },
        { time: '02:14:08', level: 'DISPATCH', text: 'Dispatching risk package to Case Agent for workflow creation.' }
      ]} />
    </div>
  );
}

/* ====================================================================
   AGENT 7: CASE AGENT (Temporal Workflows & Investigation Lifecycle)
   ==================================================================== */
function CaseAgentDetail({ scenario }: { scenario: any }) {
  return (
    <div className="space-y-6">
      <div className="bg-[#111111] rounded-xl border border-purple-500/30 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">7. Case Agent</h2>
                <span className="text-[10px] bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-purple-500/30">
                  Temporal Lifecycle Manager
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Manages case creation, Temporal background workflows, SLA timers, and analyst routing.</p>
            </div>
          </div>

          <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded font-mono font-bold uppercase border border-emerald-500/30">
            CASE CREATED & SYNCED
          </span>
        </div>

        {/* Responsibilities Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-purple-400 font-mono font-bold uppercase block">Core Task 01</span>
            <p className="text-xs font-semibold text-slate-200">Create fraud investigation cases in database</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-purple-400 font-mono font-bold uppercase block">Core Task 02</span>
            <p className="text-xs font-semibold text-slate-200">Assign cases to specialized fraud analysts</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-purple-400 font-mono font-bold uppercase block">Core Task 03</span>
            <p className="text-xs font-semibold text-slate-200">Maintain investigation notes & analyst logs</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-purple-400 font-mono font-bold uppercase block">Core Task 04</span>
            <p className="text-xs font-semibold text-slate-200">Request human analyst approval via Admin Portal</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-purple-400 font-mono font-bold uppercase block">Core Task 05</span>
            <p className="text-xs font-semibold text-slate-200">Trigger Temporal background workflows & SLA timers</p>
          </div>
          <div className="bg-[#080808] p-3 rounded border border-white/5 space-y-1">
            <span className="text-[10px] text-purple-400 font-mono font-bold uppercase block">Core Task 06</span>
            <p className="text-xs font-semibold text-slate-200">Send customer real-time portal notifications</p>
          </div>
        </div>
      </div>

      {/* Case Timeline & Temporal Workflow Status */}
      <div className="bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl font-mono">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
            <Clock className="w-4 h-4 text-purple-400" /> Complete Case Timeline & Workflow Progress
          </span>
          <span className="text-[10px] text-slate-500">Temporal Workflow ID: wf_case_9021</span>
        </div>

        {/* Visual Step Timeline */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs pt-2">
          <div className="bg-[#080808] p-3 rounded border border-emerald-500/30 text-center space-y-1">
            <span className="text-[9px] text-emerald-400 font-bold uppercase block">Step 01 - DONE</span>
            <p className="font-bold text-white">Case Created</p>
            <span className="text-[9px] text-slate-500">INC-2026-8911</span>
          </div>

          <div className="bg-[#080808] p-3 rounded border border-emerald-500/30 text-center space-y-1">
            <span className="text-[9px] text-emerald-400 font-bold uppercase block">Step 02 - DONE</span>
            <p className="font-bold text-white">Analyst Assigned</p>
            <span className="text-[9px] text-slate-500">Sarah Jenkins</span>
          </div>

          <div className="bg-[#080808] p-3 rounded border border-emerald-500/30 text-center space-y-1">
            <span className="text-[9px] text-emerald-400 font-bold uppercase block">Step 03 - DONE</span>
            <p className="font-bold text-white">Temporal Triggered</p>
            <span className="text-[9px] text-slate-500">Timer: 15m SLA</span>
          </div>

          <div className="bg-[#080808] p-3 rounded border border-amber-500/30 text-center space-y-1">
            <span className="text-[9px] text-amber-400 font-bold uppercase block">Step 04 - IN REVIEW</span>
            <p className="font-bold text-white">Analyst Approval</p>
            <span className="text-[9px] text-amber-400">Awaiting Action</span>
          </div>

          <div className="bg-[#080808] p-3 rounded border border-white/10 text-center space-y-1 opacity-50">
            <span className="text-[9px] text-slate-500 font-bold uppercase block">Step 05 - PENDING</span>
            <p className="font-bold text-slate-400">Resolved & Closed</p>
            <span className="text-[9px] text-slate-500">Final Sync</span>
          </div>
        </div>
      </div>

      <InputOutputPanel
        inputData={{
          customerId: 'CUST-1001',
          riskScore: 88,
          recommendedAction: 'temporary_card_freeze',
          fraudCategory: 'Stolen Card'
        }}
        outputData={{
          incidentId: 'INC-2026-8911',
          assignedAnalyst: 'Analyst Sarah Jenkins',
          temporalWorkflowStatus: 'RUNNING',
          customerNotified: true,
          slaTargetMinutes: 15
        }}
      />

      <ExecutionLogsPanel logs={[
        { time: '02:14:08', level: 'CASE_CREATE', text: 'Created security incident record INC-2026-8911 in database.' },
        { time: '02:14:09', level: 'TEMPORAL', text: 'Started Temporal Workflow wf_case_9021 with 15-minute SLA timer.' },
        { time: '02:14:09', level: 'NOTIFY', text: 'Pushed live WebSocket notification to Customer Portal & Analyst Queue.' }
      ]} />
    </div>
  );
}

/* ====================================================================
   HELPER COMPONENTS: INPUT/OUTPUT & LOGS PANELS
   ==================================================================== */
function InputOutputPanel({ inputData, outputData }: { inputData: any; outputData: any }) {
  return (
    <div className="grid sm:grid-cols-2 gap-6 font-mono text-xs">
      <div className="bg-[#111111] rounded-xl border border-white/10 p-4 space-y-2 shadow-xl">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block border-b border-white/10 pb-2">
          📥 Node Inputs (Incoming LangGraph State)
        </span>
        <pre className="bg-[#080808] p-3 rounded text-[11px] text-orange-300 overflow-x-auto border border-white/5">
          {JSON.stringify(inputData, null, 2)}
        </pre>
      </div>

      <div className="bg-[#111111] rounded-xl border border-white/10 p-4 space-y-2 shadow-xl">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block border-b border-white/10 pb-2">
          📤 Node Outputs (Outgoing LangGraph State)
        </span>
        <pre className="bg-[#080808] p-3 rounded text-[11px] text-emerald-300 overflow-x-auto border border-white/5">
          {JSON.stringify(outputData, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function ExecutionLogsPanel({ logs }: { logs: Array<{ time: string; level: string; text: string }> }) {
  return (
    <div className="bg-[#111111] rounded-xl border border-white/10 p-4 space-y-3 font-mono shadow-xl">
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <span className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <Terminal className="w-4 h-4 text-orange-500" /> Real-Time Node Execution Logs
        </span>
        <span className="text-[10px] text-slate-500">Buffer: 100 lines</span>
      </div>

      <div className="bg-[#080808] p-3 rounded text-xs space-y-1.5 border border-white/5 max-h-48 overflow-y-auto custom-scrollbar">
        {logs.map((l, i) => (
          <div key={i} className="flex items-start space-x-2 text-[11px]">
            <span className="text-slate-500 flex-shrink-0">[{l.time}]</span>
            <span className={`px-1.5 py-0.2 rounded font-bold text-[9px] uppercase flex-shrink-0 ${
              l.level === 'WARN' ? 'bg-amber-500/20 text-amber-400' :
              l.level === 'ROUTE' || l.level === 'DISPATCH' ? 'bg-blue-500/20 text-blue-400' :
              l.level === 'MCP_CALL' || l.level === 'RAG_SEARCH' ? 'bg-emerald-500/20 text-emerald-400' :
              'bg-slate-800 text-slate-300'
            }`}>
              {l.level}
            </span>
            <span className="text-slate-300 font-sans">{l.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
