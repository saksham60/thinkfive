import React, { useState } from 'react';
import { ShieldAlert, Users, LayoutDashboard, Cpu, RefreshCw, Zap, Menu, X, LogOut, ShieldCheck, User, Bot, HelpCircle, CreditCard, FileText, Activity, Layers, ChevronDown, ChevronRight } from 'lucide-react';
import { UserRole } from '../types';
import { AuthRole } from './LoginScreen';
import { AgentId } from './AIAgentsView';

interface SidebarProps {
  activeTab: 'customer' | 'analyst' | 'agents' | 'supervisor' | 'architecture';
  setActiveTab: (tab: 'customer' | 'analyst' | 'agents' | 'supervisor' | 'architecture') => void;
  customerSubTab?: 'concierge' | 'alerts' | 'activity';
  onSelectCustomerSubTab?: (subTab: 'concierge' | 'alerts' | 'activity') => void;
  activeAlertsCount?: number;
  selectedAgentId?: AgentId;
  onSelectAgent?: (agentId: AgentId) => void;
  userRole: UserRole;
  setUserRole: (role: UserRole) => void;
  authRole: AuthRole;
  onLogout: () => void;
  wsConnected: boolean;
  onTriggerSimulator: (scenario: string) => void;
  onResetSeedData: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  customerSubTab = 'concierge',
  onSelectCustomerSubTab,
  activeAlertsCount = 0,
  selectedAgentId = 'supervisor',
  onSelectAgent,
  userRole,
  setUserRole,
  authRole,
  onLogout,
  wsConnected,
  onTriggerSimulator,
  onResetSeedData
}) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [customerSectionOpen, setCustomerSectionOpen] = useState(true);
  const [agentsSectionOpen, setAgentsSectionOpen] = useState(true);

  const handleNavClick = (tab: 'customer' | 'analyst' | 'agents' | 'supervisor' | 'architecture', role?: UserRole, agentId?: AgentId) => {
    setActiveTab(tab);
    if (role) setUserRole(role);
    if (agentId && onSelectAgent) onSelectAgent(agentId);
    setMobileOpen(false);
  };

  const isAdmin = authRole === 'admin';

  return (
    <>
      {/* Mobile Top Header */}
      <div className="md:hidden bg-[#0d0d0d] border-b border-white/10 p-4 text-white flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-orange-600 rounded flex items-center justify-center font-bold text-white shadow-md shadow-orange-600/30">
            S
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight uppercase text-white">
              SentinelBank <span className="text-orange-500">AI</span>
            </h1>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={onLogout}
            className="p-2 text-slate-400 hover:text-red-400 rounded bg-white/5 border border-white/10 text-xs flex items-center space-x-1 font-mono"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 text-slate-400 hover:text-white rounded bg-white/5 border border-white/10"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Backdrop overlay for mobile */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 md:hidden"
        />
      )}

      {/* Main Sidebar Container */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-50 h-screen w-64 bg-[#0a0a0a] border-r border-white/10 text-white flex flex-col justify-between transition-transform duration-300 ease-in-out ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full overflow-y-auto custom-scrollbar">
          {/* Brand Logo & System Info */}
          <div className="p-5 border-b border-white/10">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 bg-orange-600 rounded-lg flex items-center justify-center font-extrabold text-lg text-white shadow-lg shadow-orange-600/30 flex-shrink-0">
                S
              </div>
              <div className="min-w-0">
                <h1 className="text-base font-bold tracking-tight uppercase text-white truncate">
                  SentinelBank <span className="text-orange-500">AI</span>
                </h1>
                <p className="text-[10px] text-slate-500 font-mono tracking-wider truncate">
                  v4.2.0-STABLE | REGIONAL_FINALS
                </p>
              </div>
            </div>

            {/* Authenticated Persona Badge */}
            <div className="mt-3.5 p-2 rounded-md bg-[#111111] border border-white/5 flex items-center justify-between">
              <div className="flex items-center space-x-2 min-w-0">
                {isAdmin ? (
                  <ShieldCheck className="w-4 h-4 text-red-400 flex-shrink-0" />
                ) : (
                  <User className="w-4 h-4 text-orange-400 flex-shrink-0" />
                )}
                <div className="min-w-0">
                  <p className="text-xs font-bold text-white truncate">
                    {isAdmin ? 'Administrator' : 'Priya Sharma'}
                  </p>
                  <p className="text-[10px] font-mono text-slate-400 truncate">
                    {isAdmin ? '🛡️ Admin Command' : '👤 Customer Portal'}
                  </p>
                </div>
              </div>
              <span className={`text-[9px] uppercase font-mono font-bold px-1.5 py-0.5 rounded border ${
                isAdmin ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-orange-500/10 text-orange-400 border-orange-500/20'
              }`}>
                {isAdmin ? 'Admin' : 'User'}
              </span>
            </div>
          </div>

          {/* Navigation Section */}
          <div className="px-3 py-4 space-y-6 flex-1">
            <div>
              <div className="px-3 mb-2 text-[10px] font-bold uppercase text-slate-500 tracking-widest font-mono">
                Command Navigation
              </div>
              <nav className="space-y-1">
                <div>
                  <button
                    onClick={() => {
                      setCustomerSectionOpen(!customerSectionOpen);
                      if (activeTab !== 'customer') handleNavClick('customer', 'customer');
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-semibold tracking-wide transition-all ${
                      activeTab === 'customer'
                        ? 'bg-orange-600/10 text-orange-500 border border-orange-500/40 font-bold shadow-sm'
                        : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <Users className="w-4 h-4 text-orange-500" />
                      <span>Customer View</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      {activeTab === 'customer' && <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mr-1" />}
                      {customerSectionOpen ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-400" />}
                    </div>
                  </button>

                  {/* Sub-menu for Customer Portal */}
                  {customerSectionOpen && (
                    <div className="ml-3 pl-3 border-l border-white/10 mt-1 space-y-1">
                      <button
                        onClick={() => {
                          handleNavClick('customer', 'customer');
                          if (onSelectCustomerSubTab) onSelectCustomerSubTab('concierge');
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                          activeTab === 'customer' && customerSubTab === 'concierge'
                            ? 'bg-orange-500/20 text-orange-400 font-bold border border-orange-500/30'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                        }`}
                      >
                        <span className="flex items-center gap-2 truncate">
                          <Bot className="w-3.5 h-3.5 text-orange-400 shrink-0" />
                          <span className="truncate">AI Banking Concierge</span>
                        </span>
                      </button>

                      <button
                        onClick={() => {
                          handleNavClick('customer', 'customer');
                          if (onSelectCustomerSubTab) onSelectCustomerSubTab('alerts');
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                          activeTab === 'customer' && customerSubTab === 'alerts'
                            ? 'bg-orange-500/20 text-orange-400 font-bold border border-orange-500/30'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                        }`}
                      >
                        <span className="flex items-center gap-2 truncate">
                          <ShieldAlert className="w-3.5 h-3.5 text-red-400 shrink-0" />
                          <span className="truncate">Real-Time Fraud Alerts</span>
                        </span>
                        {activeAlertsCount > 0 && (
                          <span className="bg-red-500 text-white text-[9px] font-mono font-extrabold px-1.5 py-0.2 rounded-full animate-pulse ml-1">
                            {activeAlertsCount}
                          </span>
                        )}
                      </button>

                      <button
                        onClick={() => {
                          handleNavClick('customer', 'customer');
                          if (onSelectCustomerSubTab) onSelectCustomerSubTab('activity');
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                          activeTab === 'customer' && customerSubTab === 'activity'
                            ? 'bg-orange-500/20 text-orange-400 font-bold border border-orange-500/30'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                        }`}
                      >
                        <span className="flex items-center gap-2 truncate">
                          <CreditCard className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                          <span className="truncate">Accounts & Disputes</span>
                        </span>
                      </button>
                    </div>
                  )}
                </div>

                    {/* ADMIN / STAFF NAVIGATION MODULES */}
                    {isAdmin && (
                      <>
                        {/* "AI AGENTS" SECTION */}
                        <div className="pt-2">
                          <button
                            onClick={() => {
                              setAgentsSectionOpen(!agentsSectionOpen);
                              if (activeTab !== 'agents') handleNavClick('agents', 'supervisor', 'supervisor');
                            }}
                            className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-semibold tracking-wide transition-all ${
                              activeTab === 'agents'
                                ? 'bg-orange-600/10 text-orange-400 border border-orange-500/40 font-bold'
                                : 'text-slate-300 hover:text-white hover:bg-white/5 border border-transparent'
                            }`}
                          >
                            <div className="flex items-center space-x-2.5">
                              <Bot className="w-4 h-4 text-orange-400" />
                              <span className="font-bold">AI Agents</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <span className="text-[9px] bg-orange-500/20 text-orange-400 px-1.5 py-0.2 rounded font-mono font-bold">7</span>
                              {agentsSectionOpen ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-400" />}
                            </div>
                          </button>

                          {/* Sub-menu of 7 Agents */}
                          {agentsSectionOpen && (
                            <div className="ml-3 pl-3 border-l border-white/10 mt-1 space-y-1">
                              <button
                                onClick={() => handleNavClick('agents', 'supervisor', 'supervisor')}
                                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                                  activeTab === 'agents' && selectedAgentId === 'supervisor'
                                    ? 'bg-orange-500/20 text-orange-400 font-bold'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-1.5">
                                  <Bot className="w-3 h-3 text-orange-400" /> 1. Supervisor
                                </span>
                              </button>

                              <button
                                onClick={() => handleNavClick('agents', 'supervisor', 'support')}
                                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                                  activeTab === 'agents' && selectedAgentId === 'support'
                                    ? 'bg-blue-500/20 text-blue-400 font-bold'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-1.5">
                                  <HelpCircle className="w-3 h-3 text-blue-400" /> 2. Support Agent
                                </span>
                              </button>

                              <button
                                onClick={() => handleNavClick('agents', 'supervisor', 'transaction')}
                                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                                  activeTab === 'agents' && selectedAgentId === 'transaction'
                                    ? 'bg-cyan-500/20 text-cyan-400 font-bold'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-1.5">
                                  <CreditCard className="w-3 h-3 text-cyan-400" /> 3. Transaction
                                </span>
                              </button>

                              <button
                                onClick={() => handleNavClick('agents', 'supervisor', 'knowledge')}
                                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                                  activeTab === 'agents' && selectedAgentId === 'knowledge'
                                    ? 'bg-emerald-500/20 text-emerald-400 font-bold'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-1.5">
                                  <FileText className="w-3 h-3 text-emerald-400" /> 4. Knowledge (RAG)
                                </span>
                              </button>

                              <button
                                onClick={() => handleNavClick('agents', 'supervisor', 'fraud')}
                                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                                  activeTab === 'agents' && selectedAgentId === 'fraud'
                                    ? 'bg-red-500/20 text-red-400 font-bold'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-1.5">
                                  <ShieldAlert className="w-3 h-3 text-red-400" /> 5. Fraud Agent
                                </span>
                              </button>

                              <button
                                onClick={() => handleNavClick('agents', 'supervisor', 'risk')}
                                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                                  activeTab === 'agents' && selectedAgentId === 'risk'
                                    ? 'bg-amber-500/20 text-amber-400 font-bold'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-1.5">
                                  <Activity className="w-3 h-3 text-amber-400" /> 6. Risk Scoring
                                </span>
                              </button>

                              <button
                                onClick={() => handleNavClick('agents', 'supervisor', 'case')}
                                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono transition-all ${
                                  activeTab === 'agents' && selectedAgentId === 'case'
                                    ? 'bg-purple-500/20 text-purple-400 font-bold'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-1.5">
                                  <Layers className="w-3 h-3 text-purple-400" /> 7. Case Agent
                                </span>
                              </button>
                            </div>
                          )}
                        </div>

                        <button
                          onClick={() => handleNavClick('analyst', 'analyst')}
                          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-semibold tracking-wide transition-all relative ${
                            activeTab === 'analyst'
                              ? 'bg-orange-600/10 text-orange-500 border border-orange-500/40 font-bold shadow-sm'
                              : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                          }`}
                        >
                          <div className="flex items-center space-x-2.5">
                            <ShieldAlert className="w-4 h-4 text-orange-400" />
                            <span>Analyst Hub</span>
                          </div>
                          <span className="flex h-2 w-2 relative">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                          </span>
                        </button>

                        <button
                          onClick={() => handleNavClick('supervisor', 'supervisor')}
                          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-semibold tracking-wide transition-all ${
                            activeTab === 'supervisor'
                              ? 'bg-orange-600/10 text-orange-500 border border-orange-500/40 font-bold shadow-sm'
                              : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                          }`}
                        >
                          <div className="flex items-center space-x-2.5">
                            <LayoutDashboard className="w-4 h-4 text-orange-500" />
                            <span>Supervisor Hub</span>
                          </div>
                          {activeTab === 'supervisor' && <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />}
                        </button>

                        <button
                          onClick={() => handleNavClick('architecture')}
                          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-semibold tracking-wide transition-all ${
                            activeTab === 'architecture'
                              ? 'bg-orange-600/10 text-orange-500 border border-orange-500/40 font-bold shadow-sm'
                              : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                          }`}
                        >
                          <div className="flex items-center space-x-2.5">
                            <Cpu className="w-4 h-4 text-orange-500" />
                            <span>Agents & Eval</span>
                          </div>
                          {activeTab === 'architecture' && <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />}
                        </button>
                      </>
                    )}
              </nav>
            </div>

            {/* Synthetic Event Injector - Admin Only */}
            {isAdmin && (
              <div className="pt-2 border-t border-white/10">
                <div className="px-3 mb-2 text-[10px] font-bold uppercase text-slate-500 tracking-widest font-mono flex items-center justify-between">
                  <span>Event Simulator</span>
                  <Zap className="w-3 h-3 text-orange-500 fill-current" />
                </div>

                <div className="space-y-1.5 px-1">
                  <button
                    onClick={() => {
                      onTriggerSimulator('stolen_card');
                      setMobileOpen(false);
                    }}
                    className="w-full text-left p-2.5 rounded bg-[#111111] hover:bg-[#181818] border border-white/5 transition-all flex items-center justify-between text-xs text-slate-200 group"
                  >
                    <span className="group-hover:text-white truncate">🚨 Stolen Card Fraud</span>
                    <span className="text-[10px] text-red-500 font-mono font-bold ml-1">R:94</span>
                  </button>

                  <button
                    onClick={() => {
                      onTriggerSimulator('fraud_ring');
                      setMobileOpen(false);
                    }}
                    className="w-full text-left p-2.5 rounded bg-[#111111] hover:bg-[#181818] border border-white/5 transition-all flex items-center justify-between text-xs text-slate-200 group"
                  >
                    <span className="group-hover:text-white truncate">🕸️ Fraud Ring Cluster</span>
                    <span className="text-[10px] text-orange-400 font-mono font-bold ml-1">R:92</span>
                  </button>

                  <button
                    onClick={() => {
                      onTriggerSimulator('travel_false_positive');
                      setMobileOpen(false);
                    }}
                    className="w-full text-left p-2.5 rounded bg-[#111111] hover:bg-[#181818] border border-white/5 transition-all flex items-center justify-between text-xs text-slate-200 group"
                  >
                    <span className="group-hover:text-white truncate">✈️ Travel False Positive</span>
                    <span className="text-[10px] text-green-400 font-mono font-bold ml-1">R:32</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Footer Controls & System Telemetry */}
          <div className="p-4 border-t border-white/10 bg-[#080808] space-y-3">
            {/* Live Telemetry Status */}
            <div className="space-y-1.5 text-[11px] font-mono">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] uppercase font-bold text-slate-500">MCP Gateway</span>
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-slate-600'}`}></span>
                  <span className={wsConnected ? 'text-green-400 font-bold' : 'text-slate-500'}>
                    {wsConnected ? 'ONLINE' : 'OFFLINE'}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] uppercase font-bold text-slate-500">LangGraph Agent</span>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  <span className="text-green-400 font-bold">READY</span>
                </div>
              </div>
            </div>

            {/* Seed Data Reset Action - Admin Only */}
            {isAdmin && (
              <button
                onClick={onResetSeedData}
                className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-slate-300 hover:text-white font-mono transition-colors"
                title="Reset Synthetic Seed Data"
              >
                <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
                <span>Reset Database</span>
              </button>
            )}

            {/* Logout Action */}
            <button
              onClick={onLogout}
              className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-xs text-red-400 font-mono transition-colors uppercase font-bold"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>LOGOUT SESSION</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

