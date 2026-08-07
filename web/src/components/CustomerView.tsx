import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  ShieldCheck,
  AlertTriangle,
  FileText,
  ChevronRight,
  Lock,
  Eye,
  EyeOff,
  CreditCard,
  Clock,
  CheckCircle2,
  ShieldAlert,
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp,
  Wallet,
  Bell,
  X,
  Shield,
  MessageSquare,
  Activity
} from 'lucide-react';
import {
  ChatMessage,
  Transaction,
  AccountSummary,
  CardDetails,
  CaseRecord,
  FraudAssessment,
  SecurityIncident,
  FraudAlert
} from '../types';
import { FraudAssessmentSummaryPanel } from './FraudAssessmentSummaryPanel';
import { FraudAssessmentCard } from './FraudAssessmentCard';
import { ActionWorkflowPage } from './ActionWorkflowPage';
import { FraudAlertCenter } from './FraudAlertCenter';

interface CustomerViewProps {
  alerts?: FraudAlert[];
  incidents?: SecurityIncident[];
  onRefreshAlerts?: () => void;
  onRefreshIncidents?: () => void;
  onReportFraudTransaction: (txnId: string) => void;
  customerSubTab?: 'concierge' | 'alerts' | 'activity';
  onSelectCustomerSubTab?: (subTab: 'concierge' | 'alerts' | 'activity') => void;
}

const renderFormattedText = (rawText?: string) => {
  if (!rawText) return null;

  const lines = rawText.split('\n');

  return lines.map((line, lineIdx) => {
    // Regex splits by markdown **bold**, `code`, or *italic*
    const parts = line.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*)/g);

    return (
      <div key={lineIdx} className={lineIdx < lines.length - 1 ? "mb-1" : ""}>
        {parts.map((part, partIdx) => {
          if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
            const content = part.slice(2, -2).replace(/\*/g, '');
            return (
              <strong key={partIdx} className="font-bold text-white">
                {content}
              </strong>
            );
          }
          if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
            const content = part.slice(1, -1).replace(/\*/g, '');
            return (
              <code key={partIdx} className="bg-white/10 text-orange-400 font-mono px-1.5 py-0.5 rounded text-[11px] font-semibold border border-white/10">
                {content}
              </code>
            );
          }
          if (part.startsWith('*') && part.endsWith('*') && part.length >= 2 && !part.startsWith('**')) {
            const content = part.slice(1, -1).replace(/\*/g, '');
            return (
              <em key={partIdx} className="italic text-slate-300">
                {content}
              </em>
            );
          }
          // Remove any stray asterisks from normal text chunk
          const cleanText = part.replace(/\*/g, '');
          return <span key={partIdx}>{cleanText}</span>;
        })}
      </div>
    );
  });
};

export const CustomerView: React.FC<CustomerViewProps> = ({
  alerts = [],
  incidents = [],
  onRefreshAlerts,
  onRefreshIncidents,
  onReportFraudTransaction,
  customerSubTab,
  onSelectCustomerSubTab
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPiiMasking, setShowPiiMasking] = useState(true);
  const [isAccountsOpen, setIsAccountsOpen] = useState(true);
  const [customerTab, setCustomerTab] = useState<'concierge' | 'alerts' | 'activity'>(customerSubTab || 'concierge');

  useEffect(() => {
    if (customerSubTab) {
      setCustomerTab(customerSubTab);
    }
  }, [customerSubTab]);

  const handleTabChange = (tab: 'concierge' | 'alerts' | 'activity') => {
    setCustomerTab(tab);
    if (onSelectCustomerSubTab) {
      onSelectCustomerSubTab(tab);
    }
  };
  const [showToastAlert, setShowToastAlert] = useState<FraudAlert | null>(null);
  const [initialAlertSearch, setInitialAlertSearch] = useState<string>('');
  const [selectedWorkflowAction, setSelectedWorkflowAction] = useState<{
    actionTitle: string;
    assessment?: FraudAssessment;
  } | null>(null);

  const [dashboardData, setDashboardData] = useState<{
    profile?: any;
    accounts?: AccountSummary[];
    cards?: CardDetails[];
    transactions?: Transaction[];
    cases?: CaseRecord[];
  }>({});

  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const fetchDashboard = async () => {
    try {
      const res = await fetch('/api/customer/CUST-1001/dashboard');
      const data = await res.json();
      setDashboardData(data);
    } catch (e) {
      console.error('Failed to load customer dashboard', e);
    }
  };

  useEffect(() => {
    fetchDashboard();

    // Initial Welcome Message
    setMessages([
      {
        id: 'INIT-1',
        sender: 'agent',
        agentName: 'SentinelBank AI Assistant',
        text: 'Hello Priya! I am your AI Banking Assistant. How can I assist you today? You can ask about your account balances, recent charges, bank policies, or report any unrecognized activity.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggestedActions: [
          'Report ₹2,499.99 charge from Luxure Electronics',
          'I received a suspicious phishing email asking for my OTP',
          'My physical card was lost or stolen',
          'What is my checking balance?'
        ]
      }
    ]);
  }, []);

  // Monitor active open alerts for Toast Notifications
  useEffect(() => {
    const openAlert = alerts.find(a => a.status === 'open');
    if (openAlert) {
      setShowToastAlert(openAlert);
    }
  }, [alerts]);

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  const handleOpenActionWorkflow = (actionTitle: string, assessment?: FraudAssessment) => {
    setSelectedWorkflowAction({ actionTitle, assessment });
  };

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `USER-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!customText) setInput('');
    setLoading(true);

    const lowerText = textToSend.toLowerCase();

    // Check for transaction query intent
    const isTransactionIntent =
      lowerText.includes('transaction') ||
      lowerText.includes('charge') ||
      lowerText.includes('payment') ||
      lowerText.includes('recognize') ||
      lowerText.includes('made by me') ||
      lowerText.includes('unrecognized') ||
      lowerText.includes('report') ||
      lowerText.includes('fraud') ||
      lowerText.includes('luxure') ||
      lowerText.includes('2499') ||
      lowerText.includes('2,499') ||
      lowerText.includes('recent') ||
      lowerText.includes('spent') ||
      lowerText.includes('purchase');

    if (isTransactionIntent) {
      let searchWord = '';
      if (lowerText.includes('luxure')) searchWord = 'Luxure';
      else if (lowerText.includes('2499') || lowerText.includes('2,499')) searchWord = '2499';
      else if (lowerText.includes('coffee')) searchWord = 'Coffee';
      else if (lowerText.includes('metro')) searchWord = 'Metro';

      setInitialAlertSearch(searchWord);

      // Add system redirect message
      const redirectMsg: ChatMessage = {
        id: `SYS-${Date.now()}`,
        sender: 'agent',
        agentName: 'SentinelBank AI Assistant',
        text: `🔍 Transaction query detected: "${textToSend}". Automatically redirecting you to your Real-Time Fraud Alerts & Recent Transactions portal...`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, redirectMsg]);

      // Switch to Real-Time Fraud Alerts tab
      handleTabChange('alerts');
    }

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          customerId: 'CUST-1001',
          userRole: 'customer'
        })
      });

      const data = await res.json();
      if (data.responseMessage) {
        setMessages(prev => [...prev, data.responseMessage]);
      }
      fetchDashboard();
    } catch (e) {
      setMessages(prev => [
        ...prev,
        {
          id: `ERR-${Date.now()}`,
          sender: 'agent',
          agentName: 'System Error',
          text: 'Sorry, I encountered an issue connecting to the banking agent gateway. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAuthorized = async (alertId: string) => {
    try {
      await fetch(`/api/alerts/${alertId}/confirm-authorized`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (onRefreshAlerts) onRefreshAlerts();
      if (onRefreshIncidents) onRefreshIncidents();
      fetchDashboard();
    } catch (e) {
      console.error('Confirm authorized error', e);
    }
  };

  const handleConfirmUnauthorized = async (alertId: string, actionType: 'freeze' | 'report') => {
    try {
      await fetch(`/api/alerts/${alertId}/confirm-unauthorized`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actionType })
      });
      if (onRefreshAlerts) onRefreshAlerts();
      if (onRefreshIncidents) onRefreshIncidents();
      fetchDashboard();
    } catch (e) {
      console.error('Confirm unauthorized error', e);
    }
  };

  const handleOpenChatWithQuery = (queryText: string) => {
    setCustomerTab('concierge');
    handleSendMessage(queryText);
  };

  // Extract all fraud assessment results from chat history
  const assessmentItems = messages
    .filter(m => m.fraudAssessment && m.fraudAssessment.isFraud && m.fraudAssessment.category !== 'General Banking Inquiry')
    .map(m => {
      const msgIdx = messages.findIndex(msg => msg.id === m.id);
      const userMsg = msgIdx > 0 ? messages[msgIdx - 1] : null;
      const queryText = userMsg && userMsg.sender === 'user' ? userMsg.text : 'Unrecognized Activity / Fraud Inquiry';
      return {
        id: m.id,
        queryText,
        timestamp: m.timestamp,
        assessment: m.fraudAssessment!
      };
    });

  const activeAlertsCount = alerts.filter(a => a.status === 'open' || a.status === 'investigating').length;

  if (selectedWorkflowAction) {
    return (
      <ActionWorkflowPage
        actionTitle={selectedWorkflowAction.actionTitle}
        assessment={selectedWorkflowAction.assessment}
        onBackToDashboard={() => setSelectedWorkflowAction(null)}
        onBackToChat={() => setSelectedWorkflowAction(null)}
      />
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 relative">
      {/* Real-time Toast Notification Banner */}
      {showToastAlert && (
        <div className="fixed top-20 right-6 z-50 max-w-md w-full bg-[#111111] border-2 border-red-500/80 rounded-xl shadow-2xl p-4 text-white animate-bounce-short">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-red-600/20 border border-red-500/40 text-red-500 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-5 h-5 animate-pulse text-red-500" />
              </div>
              <div>
                <span className="text-[10px] font-mono font-bold uppercase bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded">
                  CRITICAL FRAUD ALERT
                </span>
                <h4 className="text-xs font-bold text-white mt-1">
                  Suspicious Charge: ₹{showToastAlert.amount.toLocaleString('en-IN')} at {showToastAlert.merchantName}
                </h4>
                <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                  Flagged by Real-Time Surveillance Engine (Risk Score: {showToastAlert.riskScore}/100)
                </p>
              </div>
            </div>

            <button
              onClick={() => setShowToastAlert(null)}
              className="text-slate-500 hover:text-white p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-3 pt-2 border-t border-white/10 flex items-center justify-between font-mono text-xs">
            <span className="text-[10px] text-slate-400">Card ending in ****-4832</span>
            <button
              onClick={() => {
                setCustomerTab('alerts');
                setShowToastAlert(null);
              }}
              className="bg-red-600 hover:bg-red-500 text-white font-bold px-3 py-1.5 rounded-lg text-xs flex items-center gap-1 shadow transition-all"
            >
              Review Alert Center <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Customer Header Banner */}
      <div className="bg-[#111111] border border-white/10 rounded-xl p-6 text-white shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-light tracking-tight text-white">Priya Sharma</h1>
              <span className="bg-green-500/10 text-green-400 border border-green-500/30 text-[10px] uppercase font-bold px-2.5 py-0.5 rounded flex items-center gap-1 font-mono">
                <ShieldCheck className="w-3.5 h-3.5" /> KYC VERIFIED
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-1 font-mono">Customer ID: CUST-1001 • Primary Checking ****-9128</p>
          </div>

          <div className="flex items-center gap-6 bg-[#050505] px-5 py-3 rounded-lg border border-white/5">
            <div>
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Total Checking Balance</p>
              <p className="text-xl font-mono font-bold text-white">₹14,250.80 <span className="text-xs text-slate-500 font-sans font-normal">INR</span></p>
            </div>
            <div className="h-8 w-px bg-white/10" />
            <div>
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Card Status</p>
              <p className="text-sm font-semibold text-emerald-400 flex items-center gap-1">
                {dashboardData.cards?.[0]?.status === 'frozen' ? (
                  <span className="text-red-500 font-mono">FROZEN (UNDER REVIEW)</span>
                ) : (
                  <span className="font-mono text-xs text-green-400">ACTIVE DEBIT ****-4832</span>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>



      {/* MAIN TAB CONTENT 1: AI Banking Concierge Primary Centerpiece */}
      {customerTab === 'concierge' && (
        <div className="flex flex-col bg-[#111111] rounded-xl border border-white/10 shadow-2xl h-[720px] overflow-hidden w-full">
          {/* Chat Header */}
          <div className="p-4 bg-[#080808] border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-orange-600/20 text-orange-500 border border-orange-500/30 flex items-center justify-center shadow-inner">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-semibold text-white tracking-tight">AI Banking Concierge</h2>
                  <span className="flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] uppercase font-mono font-bold px-2.5 py-0.5 rounded-full">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> ONLINE
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono tracking-wider mt-0.5">24/7 Intelligent Banking Assistant • Secure Encrypted Support</p>
              </div>
            </div>

            {/* PII Masking Toggle Badge */}
            <button
              onClick={() => setShowPiiMasking(!showPiiMasking)}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-[#181818] border border-white/10 text-xs text-slate-300 hover:text-white hover:border-orange-500/50 transition-all shadow-sm"
            >
              <Lock className="w-4 h-4 text-green-400" />
              <span className="font-mono text-xs font-semibold">PII MASKING: {showPiiMasking ? 'ENABLED' : 'DISABLED'}</span>
            </button>
          </div>

          {/* Chat Messages Feed */}
          <div ref={messagesContainerRef} className="flex-1 p-6 overflow-y-auto space-y-6 custom-scrollbar bg-[#0d0d0d]">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-[11px] font-mono text-slate-500">
                    {msg.sender === 'user' ? 'You (Priya Sharma)' : msg.agentName || 'AI Concierge'}
                  </span>
                  <span className="text-[10px] text-slate-600 font-mono">{msg.timestamp}</span>
                </div>

                <div
                  className={`p-4 rounded-2xl max-w-3xl text-sm leading-relaxed shadow-md ${
                    msg.sender === 'user'
                      ? 'bg-orange-600 text-white rounded-tr-none font-medium'
                      : 'bg-[#181818] text-slate-200 border border-white/10 rounded-tl-none'
                  }`}
                >
                  {renderFormattedText(msg.text)}

                  {/* Render Fraud Assessment Inline Card if attached */}
                  {msg.fraudAssessment && (
                    <div className="mt-4 pt-3 border-t border-white/10">
                      <FraudAssessmentCard
                        assessment={msg.fraudAssessment}
                        onExecuteAction={(actionText) => handleOpenActionWorkflow(actionText, msg.fraudAssessment)}
                      />
                    </div>
                  )}
                </div>

                {/* Suggested Action Chips */}
                {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2 max-w-3xl">
                    {msg.suggestedActions.map((action, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSendMessage(action)}
                        className="text-xs bg-[#1a1a1a] hover:bg-orange-600/20 text-orange-400 hover:text-orange-300 border border-orange-500/30 hover:border-orange-500/60 px-3 py-1.5 rounded-full transition-all flex items-center space-x-1.5 font-mono shadow-sm"
                      >
                        <Sparkles className="w-3 h-3 text-orange-400" />
                        <span>{action}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center space-x-3 text-slate-400 bg-[#181818] p-4 rounded-xl border border-white/10 max-w-md font-mono text-xs">
                <div className="w-2 h-2 rounded-full bg-orange-500 animate-ping" />
                <span>SentinelBank AI Assistant is checking your account security...</span>
              </div>
            )}
          </div>

          {/* Chat Input Bar */}
          <div className="p-4 bg-[#080808] border-t border-white/10">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center space-x-3"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your accounts, recent charges, or report fraud..."
                className="flex-1 bg-[#141414] text-white placeholder-slate-500 text-sm px-4 py-3 rounded-xl border border-white/10 focus:outline-none focus:border-orange-500 font-sans shadow-inner"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-xl transition-all shadow-lg shadow-orange-600/20 flex items-center space-x-2"
              >
                <span>Send</span>
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* MAIN TAB CONTENT 2: Real-Time Fraud Alert Center */}
      {customerTab === 'alerts' && (
        <FraudAlertCenter
          alerts={alerts}
          incidents={incidents}
          transactions={dashboardData.transactions || []}
          initialSearchQuery={initialAlertSearch}
          onConfirmAuthorized={handleConfirmAuthorized}
          onConfirmUnauthorized={handleConfirmUnauthorized}
          onRefreshAlerts={onRefreshAlerts}
          onOpenChatWithQuery={handleOpenChatWithQuery}
          onReportFraudTransaction={onReportFraudTransaction}
        />
      )}

      {/* MAIN TAB CONTENT 3: Accounts & Dispute Cases View */}
      {customerTab === 'activity' && (
        <div className="space-y-6">
          <div className="bg-[#111111] border border-white/10 rounded-xl p-6 text-white shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-orange-500" /> Payment Cards & Account Balances
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
              <div className="bg-[#080808] p-4 rounded-xl border border-white/10 space-y-2">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Primary Checking</span>
                <p className="text-xl font-bold text-white">₹14,250.80 INR</p>
                <p className="text-slate-400 text-[11px]">Account Masked: ****-9128</p>
              </div>

              <div className="bg-[#080808] p-4 rounded-xl border border-white/10 space-y-2">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Active Debit Card</span>
                <p className="text-xl font-bold text-white">****-4832 VISA</p>
                <p className="text-emerald-400 font-bold text-[11px]">
                  {dashboardData.cards?.[0]?.status === 'frozen' ? 'STATUS: FROZEN (TEMPORARY BLOCK)' : 'STATUS: ACTIVE'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Auxiliary Features Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-white/10">
        {/* Card 1: Quick Banking Actions */}
        <div className="bg-[#111111] rounded-xl border border-white/10 p-5 text-white shadow-md flex flex-col justify-between">
          <div>
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-3 flex items-center gap-1.5 font-mono">
              <ShieldCheck className="w-4 h-4 text-orange-500" /> Quick Banking Actions
            </h3>
            <div className="space-y-2 font-mono text-xs">
              <button
                onClick={() => setCustomerTab('alerts')}
                className="w-full text-left bg-[#080808] hover:bg-orange-600/20 p-2.5 rounded border border-white/5 transition-all text-slate-200 flex items-center justify-between"
              >
                <span>🚨 Fraud Alert Center</span>
                <ChevronRight className="w-3.5 h-3.5 text-orange-400" />
              </button>
              <button
                onClick={() => handleSendMessage('Report ₹2,499.99 charge from Luxure Electronics')}
                className="w-full text-left bg-[#080808] hover:bg-orange-600/20 p-2.5 rounded border border-white/5 transition-all text-slate-200 flex items-center justify-between"
              >
                <span>Dispute Unrecognized Charge</span>
                <ChevronRight className="w-3.5 h-3.5 text-orange-400" />
              </button>
              <button
                onClick={() => handleSendMessage('I need to freeze my physical card immediately')}
                className="w-full text-left bg-[#080808] hover:bg-orange-600/20 p-2.5 rounded border border-white/5 transition-all text-slate-200 flex items-center justify-between"
              >
                <span>Request Temporary Card Freeze</span>
                <ChevronRight className="w-3.5 h-3.5 text-orange-400" />
              </button>
            </div>
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-3">24/7 Multi-Agent Protection</p>
        </div>

        {/* Card 2: Accounts & Payment Cards Summary */}
        <div className="bg-[#111111] rounded-xl border border-white/10 p-5 text-white shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 flex items-center gap-1.5 font-mono">
                <Wallet className="w-4 h-4 text-orange-500" /> Accounts & Cards
              </h3>
              <button
                onClick={() => setIsAccountsOpen(!isAccountsOpen)}
                className="text-slate-400 hover:text-white"
              >
                {isAccountsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>

            {isAccountsOpen && (
              <div className="space-y-2">
                {dashboardData.accounts?.map((acc) => (
                  <div key={acc.accountId} className="bg-[#080808] p-2.5 rounded border border-white/5 flex justify-between items-center">
                    <div>
                      <p className="text-xs font-semibold text-white capitalize">{acc.accountType}</p>
                      <p className="text-[10px] text-slate-500 font-mono">{acc.accountNumberMasked}</p>
                    </div>
                    <p className="text-xs font-mono font-bold text-slate-100">₹{acc.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-3 pt-2 border-t border-white/5 flex justify-between items-center text-[11px] font-mono">
            <span className="text-slate-400">Debit Card ****-4832:</span>
            {dashboardData.cards?.[0]?.status === 'frozen' ? (
              <span className="text-red-500 font-bold">FROZEN</span>
            ) : (
              <span className="text-emerald-400 font-bold">ACTIVE</span>
            )}
          </div>
        </div>

        {/* Card 3: Active Fraud Cases */}
        <div className="bg-[#111111] rounded-xl border border-white/10 p-5 text-white shadow-md flex flex-col justify-between">
          <div>
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-3 flex items-center gap-1.5 font-mono">
              <Clock className="w-4 h-4 text-orange-500" /> Active Fraud Cases
            </h3>

            {dashboardData.cases && dashboardData.cases.length > 0 ? (
              <div className="space-y-2 max-h-[140px] overflow-y-auto pr-1">
                {dashboardData.cases.map((c) => (
                  <div key={c.caseId} className="bg-[#080808] p-2.5 rounded border border-white/5 space-y-0.5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-orange-400">{c.caseId}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold uppercase ${
                        c.status === 'pending_approval' ? 'bg-orange-600/20 text-orange-400 border border-orange-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'
                      }`}>
                        {c.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-xs font-medium text-slate-200 truncate">{c.title}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 font-mono py-2">No open dispute cases.</p>
            )}
          </div>

          <p className="text-[10px] text-slate-500 font-mono mt-2">SLA Tracking Active • Zero Liability</p>
        </div>

        {/* Card 4: Security Incidents (Admin Sync) */}
        <div className="bg-[#111111] rounded-xl border border-orange-500/30 p-5 text-white shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 font-mono">
              <h3 className="text-[10px] uppercase font-bold tracking-widest text-orange-400 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-orange-400" /> Security Incidents
              </h3>
              <span className="text-[9px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-bold uppercase border border-emerald-500/30 animate-pulse">
                LIVE
              </span>
            </div>

            {incidents.length > 0 ? (
              <div className="space-y-2 max-h-[140px] overflow-y-auto pr-1 font-mono">
                {incidents.map((inc) => (
                  <div key={inc.incidentId} className="bg-[#080808] p-2.5 rounded border border-white/10 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-orange-400">{inc.incidentId}</span>
                      <span className={`text-[9px] font-bold ${
                        inc.status === 'Resolved' ? 'text-emerald-400' : 'text-orange-400'
                      }`}>
                        {inc.status}
                      </span>
                    </div>
                    <p className="text-xs font-sans text-slate-200 truncate">{inc.actionInitiated}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-2">No active incidents logged.</p>
            )}
          </div>

          <p className="text-[10px] text-slate-500 font-mono mt-2">Real-time Sync with Analyst Operations</p>
        </div>
      </div>

      {/* AI Fraud Assessment Summary Dossier Section Below Customer View */}
      <div className="pt-2">
        <FraudAssessmentSummaryPanel
          assessmentItems={assessmentItems}
          onExecuteAction={(actionText, assessment) => handleOpenActionWorkflow(actionText, assessment)}
        />
      </div>
    </div>
  );
};
