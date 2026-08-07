import React, { useState } from 'react';
import {
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Lock,
  CreditCard,
  FileText,
  Sparkles,
  Download,
  ChevronRight,
  UserCheck,
  KeyRound,
  RefreshCw,
  Send,
  Zap,
  Building,
  Check
} from 'lucide-react';
import { FraudAssessment } from '../types';

interface ActionWorkflowPageProps {
  actionTitle: string;
  assessment?: FraudAssessment;
  onBackToDashboard: () => void;
  onBackToChat: () => void;
}

export const ActionWorkflowPage: React.FC<ActionWorkflowPageProps> = ({
  actionTitle,
  assessment,
  onBackToDashboard,
  onBackToChat
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [stepData, setStepData] = useState<{
    verifyIdentity: boolean;
    reasonSelected: string;
    notes: string;
    replacementRequested: boolean;
    otpCode: string;
    isOtpSent: boolean;
  }>({
    verifyIdentity: false,
    reasonSelected: 'unauthorized_charge',
    notes: 'Customer reported via AI Fraud Assistant',
    replacementRequested: true,
    otpCode: '',
    isOtpSent: false
  });

  const [isFinished, setIsFinished] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);
  const [createdIncident, setCreatedIncident] = useState<any>(null);

  // Generate an action reference ID
  const [referenceId] = useState(() => `ACT-SEC-${Math.floor(100000 + Math.random() * 900000)}`);
  const [caseTicketId] = useState(() => `FRD-2026-${Math.floor(1000 + Math.random() * 9000)}`);

  // Automatically create security incident in Admin Portal on mount
  React.useEffect(() => {
    const createSecurityIncident = async () => {
      try {
        const res = await fetch('/api/incidents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            customerId: 'CUST-1001',
            customerName: 'Priya Sharma',
            fraudCategory: assessment?.category || 'Unauthorized Transaction',
            severity: assessment?.severity || 'High',
            actionInitiated: actionTitle,
            aiAssessmentSummary: assessment?.summaryText || `Customer initiated security protocol: ${actionTitle}`,
            transactionId: 'TXN-10452',
            cardId: 'CARD-4832'
          })
        });
        const data = await res.json();
        setCreatedIncident(data);
      } catch (e) {
        console.error('Failed to dispatch security incident to Admin Portal', e);
      }
    };

    createSecurityIncident();
  }, [actionTitle, assessment]);

  // Contextual explanation based on actionTitle
  const getActionExplanation = () => {
    const titleLower = actionTitle.toLowerCase();
    if (titleLower.includes('block') || titleLower.includes('freeze card') || titleLower.includes('hold')) {
      return 'This security protocol immediately deactivates authorization tokens for your payment card ****-4832, preventing any further unauthorized POS, online, or contactless transactions while securing your account balance.';
    } else if (titleLower.includes('dispute') || titleLower.includes('regulation e') || titleLower.includes('unauthorized')) {
      return 'Initiating a formal Zero-Liability dispute flags the contested transaction (Luxure Electronics ₹2,499.99) for immediate chargeback investigation and issues provisional credit directly to your primary checking account.';
    } else if (titleLower.includes('password') || titleLower.includes('2fa') || titleLower.includes('credential') || titleLower.includes('phishing')) {
      return 'This workflow revokes all active digital banking session tokens, invalidates current passwords, and enforces Out-of-Band 2FA authentication to eliminate unauthorized access from compromised devices.';
    } else if (titleLower.includes('account') || titleLower.includes('lock') || titleLower.includes('takeover')) {
      return 'Freezing online banking access temporarily halts all outgoing wire transfers, ACH debits, and bill payments until full identity verification is completed by SentinelBank Compliance Operations.';
    }
    return 'This recommended protocol enforces automated fraud mitigations designed by SentinelBank AI Risk Engine to safeguard your financial accounts against detected security indicators.';
  };

  const steps = [
    {
      id: 1,
      title: 'Identity & Account Verification',
      desc: 'Verify customer credentials and multi-factor authorization tokens'
    },
    {
      id: 2,
      title: 'Configure & Execute Security Action',
      desc: 'Confirm action parameters, scope, and target payment instruments'
    },
    {
      id: 3,
      title: 'Remediation & Protocol Safeguards',
      desc: 'Issue replacement credentials, provisional credit, and ticket logging'
    },
    {
      id: 4,
      title: 'Final Audit & Protocol Submission',
      desc: 'Review completed security steps and receive official confirmation'
    }
  ];

  const calculateProgress = () => {
    if (isFinished) return 100;
    return Math.round(((currentStep - 1) / steps.length) * 100);
  };

  const handleCompleteStep = (stepNumber: number) => {
    if (!completedSteps.includes(stepNumber)) {
      setCompletedSteps(prev => [...prev, stepNumber]);
    }

    if (stepNumber < steps.length) {
      setCurrentStep(stepNumber + 1);
    } else {
      setIsFinished(true);
    }
  };

  const getStepStatus = (stepNumber: number) => {
    if (completedSteps.includes(stepNumber)) return 'Completed';
    if (currentStep === stepNumber && !isFinished) return 'In Progress';
    if (isFinished) return 'Completed';
    return 'Pending';
  };

  const handleExportReceipt = () => {
    const data = {
      title: 'SentinelBank Security Action Resolution Workflow',
      referenceId,
      caseTicketId,
      actionRequested: actionTitle,
      timestamp: new Date().toISOString(),
      customer: {
        name: 'Priya Sharma',
        customerId: 'CUST-1001',
        primaryAccount: 'Checking ****-9128'
      },
      assessmentContext: assessment ? {
        category: assessment.category,
        severity: assessment.severity,
        financialRisk: assessment.financialRisk
      } : 'User Initiated Action',
      stepsCompleted: [
        'Step 1: Identity & Token Verification - PASSED',
        'Step 2: Execution of Target Security Action - SUCCESSFUL',
        'Step 3: Remediation Protocols & Case Logging - COMPLETED',
        'Step 4: Final Compliance Audit - VERIFIED'
      ]
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Security_Action_${referenceId}.json`;
    a.click();
    URL.revokeObjectURL(url);

    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 2500);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 font-sans text-white">
      {/* Top Navigation Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBackToDashboard}
            className="px-3 py-1.5 rounded-lg bg-[#181818] hover:bg-[#222222] border border-white/10 text-xs text-slate-300 hover:text-white flex items-center space-x-1.5 font-mono transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </button>
          <span className="text-slate-600">/</span>
          <button
            onClick={onBackToChat}
            className="px-3 py-1.5 rounded-lg bg-[#181818] hover:bg-[#222222] border border-white/10 text-xs text-slate-300 hover:text-white flex items-center space-x-1.5 font-mono transition-colors"
          >
            <span>AI Support Chat</span>
          </button>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs">
          <span className="text-slate-400">Ref ID:</span>
          <span className="font-bold text-orange-400">{referenceId}</span>
        </div>
      </div>

      {/* Main Workflow Header */}
      <div className="bg-[#111111] border border-white/10 rounded-xl p-6 shadow-2xl relative overflow-hidden space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-mono font-bold uppercase px-2.5 py-0.5 rounded bg-orange-500/15 text-orange-400 border border-orange-500/30 flex items-center gap-1">
                <Zap className="w-3 h-3 text-orange-400" /> DEDICATED SECURITY ACTION WORKFLOW
              </span>
              {assessment && (
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-white/10">
                  CATEGORY: {assessment.category}
                </span>
              )}
            </div>

            <h1 className="text-xl sm:text-2xl font-light text-white tracking-tight leading-snug">
              {actionTitle}
            </h1>

            <p className="text-xs text-slate-300 leading-relaxed bg-[#080808] p-3 rounded-lg border border-white/5">
              <strong className="text-white">Action Rationale & Purpose:</strong> {getActionExplanation()}
            </p>

            {createdIncident && (
              <div className="bg-[#0a0a0a] border border-orange-500/30 p-3 rounded-lg text-xs space-y-1.5 font-mono">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-orange-400 font-bold flex items-center gap-1.5">
                    <Building className="w-3.5 h-3.5" /> ADMIN PORTAL REAL-TIME INCIDENT DISPATCHED
                  </span>
                  <span className="bg-orange-500/20 text-orange-300 px-2 py-0.5 rounded font-bold uppercase text-[10px] border border-orange-500/40">
                    ID: {createdIncident.incidentId}
                  </span>
                </div>
                <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-300 pt-1 border-t border-white/5">
                  <span>Current Status: <strong className="text-emerald-400 uppercase font-bold">{createdIncident.status}</strong></span>
                  <span>Assigned Analyst: <strong className="text-slate-200">{createdIncident.assignedAnalyst || 'Fraud Ops Analyst Queue'}</strong></span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Metrics Badge */}
          <div className="bg-[#080808] p-4 rounded-xl border border-white/10 space-y-2 flex-shrink-0 min-w-[220px]">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 font-mono">Workflow Progress</span>
              <span className="font-bold font-mono text-orange-400">{calculateProgress()}%</span>
            </div>

            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-orange-500 to-amber-400 transition-all duration-500"
                style={{ width: `${calculateProgress()}%` }}
              />
            </div>

            <div className="pt-1 flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span>Status:</span>
              <span className={`font-bold uppercase ${isFinished ? 'text-emerald-400' : 'text-orange-400'}`}>
                {isFinished ? 'Resolution Complete' : 'In Progress'}
              </span>
            </div>
          </div>
        </div>

        {/* Overall Resolution Progress Bar / Steps */}
        <div className="pt-2">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {steps.map((s) => {
              const status = getStepStatus(s.id);
              const isComp = status === 'Completed';
              const isCurr = status === 'In Progress';

              return (
                <div
                  key={s.id}
                  className={`p-3 rounded-lg border text-xs transition-all ${
                    isComp
                      ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                      : isCurr
                      ? 'bg-orange-950/20 border-orange-500/50 text-orange-300 font-semibold shadow-md'
                      : 'bg-[#151515] border-white/5 text-slate-500'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1 font-mono text-[10px]">
                    <span className="uppercase">STEP 0{s.id}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded uppercase font-bold text-[9px] ${
                        isComp
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : isCurr
                          ? 'bg-orange-500/20 text-orange-400'
                          : 'bg-slate-800 text-slate-500'
                      }`}
                    >
                      {status}
                    </span>
                  </div>
                  <div className="font-medium truncate text-[11px]">{s.title}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Interactive Resolution Content */}
      {!isFinished ? (
        <div className="bg-[#111111] border border-white/10 rounded-xl p-6 shadow-xl space-y-6">
          <div className="border-b border-white/10 pb-3 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase text-orange-400 font-bold block">
                ACTIVE WORKFLOW STEP {currentStep} OF {steps.length}
              </span>
              <h2 className="text-lg font-medium text-white">{steps[currentStep - 1].title}</h2>
              <p className="text-xs text-slate-400 font-mono">{steps[currentStep - 1].desc}</p>
            </div>
          </div>

          {/* STEP 1: Identity & Account Verification */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div className="bg-[#080808] p-4 rounded-lg border border-white/5 space-y-3">
                <div className="flex items-center space-x-3 text-xs">
                  <div className="p-2 rounded bg-orange-500/20 text-orange-400">
                    <UserCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-white">Authenticated Customer Profile</h4>
                    <p className="text-slate-400 font-mono">Priya Sharma • Customer ID: CUST-1001</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
                  <div className="bg-[#121212] p-2.5 rounded border border-white/5 font-mono">
                    <span className="text-slate-500 block text-[10px] uppercase">Primary Account</span>
                    <span className="text-slate-200">Checking ****-9128 (Active)</span>
                  </div>
                  <div className="bg-[#121212] p-2.5 rounded border border-white/5 font-mono">
                    <span className="text-slate-500 block text-[10px] uppercase">Auth Token Status</span>
                    <span className="text-emerald-400">MFA Verified via Device Biometrics</span>
                  </div>
                </div>
              </div>

              <div className="bg-[#0c0c0c] p-4 rounded-lg border border-white/5 space-y-3">
                <label className="flex items-start space-x-3 cursor-pointer text-xs">
                  <input
                    type="checkbox"
                    checked={stepData.verifyIdentity}
                    onChange={(e) => setStepData(prev => ({ ...prev, verifyIdentity: e.target.checked }))}
                    className="mt-0.5 rounded border-slate-700 text-orange-600 focus:ring-orange-500 bg-slate-900"
                  />
                  <span className="text-slate-300">
                    I confirm that I am the authorized account owner (Priya Sharma) and am explicitly requesting the execution of security protocol <strong className="text-white font-mono">{actionTitle}</strong>.
                  </span>
                </label>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  disabled={!stepData.verifyIdentity}
                  onClick={() => handleCompleteStep(1)}
                  className={`px-5 py-2.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center space-x-2 ${
                    stepData.verifyIdentity
                      ? 'bg-orange-600 hover:bg-orange-500 text-white shadow-lg shadow-orange-600/20'
                      : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  <span>VERIFY IDENTITY & PROCEED</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: Configure & Execute Security Action */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="bg-[#080808] p-4 rounded-lg border border-white/5 space-y-3">
                <h4 className="text-xs font-bold text-white uppercase font-mono flex items-center gap-2">
                  <Lock className="w-4 h-4 text-orange-400" /> Configure Action Parameters
                </h4>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-slate-400 font-mono mb-1 text-[11px]">Primary Fraud Reason Code:</label>
                    <select
                      value={stepData.reasonSelected}
                      onChange={(e) => setStepData(prev => ({ ...prev, reasonSelected: e.target.value }))}
                      className="w-full bg-[#141414] border border-white/10 rounded-lg p-2.5 text-white font-mono focus:border-orange-500 focus:outline-none"
                    >
                      <option value="unauthorized_charge">Unauthorized Transaction / Unknown Merchant</option>
                      <option value="stolen_card">Stolen or Lost Physical Payment Instrument</option>
                      <option value="phishing_compromise">Credential Leak via Phishing / Deceptive Link</option>
                      <option value="skimming_clone">Cloned Card / ATM Skimmer Suspected</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-400 font-mono mb-1 text-[11px]">Action Audit Notes:</label>
                    <textarea
                      rows={2}
                      value={stepData.notes}
                      onChange={(e) => setStepData(prev => ({ ...prev, notes: e.target.value }))}
                      className="w-full bg-[#141414] border border-white/10 rounded-lg p-2.5 text-white font-mono focus:border-orange-500 focus:outline-none"
                    />
                  </div>

                  {actionTitle.toLowerCase().includes('card') && (
                    <div className="bg-[#141414] p-3 rounded-lg border border-white/5 flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <CreditCard className="w-4 h-4 text-orange-400" />
                        <div>
                          <span className="font-bold text-white block">Target Debit Card</span>
                          <span className="text-slate-400 font-mono text-[10px]">VISA Debit ****-4832</span>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded uppercase font-bold">
                        TO BE BLOCKED
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-between pt-2">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="px-4 py-2 rounded-lg bg-[#1a1a1a] text-slate-300 text-xs font-mono border border-white/10 hover:text-white"
                >
                  Back
                </button>
                <button
                  onClick={() => handleCompleteStep(2)}
                  className="px-5 py-2.5 rounded-lg bg-orange-600 hover:bg-orange-500 text-white text-xs font-mono font-bold transition-all shadow-lg shadow-orange-600/20 flex items-center space-x-2"
                >
                  <span>EXECUTE SECURITY PROTOCOL</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: Remediation & Protocol Safeguards */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="bg-[#080808] p-4 rounded-lg border border-white/5 space-y-3 text-xs">
                <h4 className="text-xs font-bold text-white uppercase font-mono flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" /> Automated Remediation Actions
                </h4>

                <div className="space-y-2">
                  <label className="flex items-center space-x-3 bg-[#121212] p-3 rounded-lg border border-white/5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={stepData.replacementRequested}
                      onChange={(e) => setStepData(prev => ({ ...prev, replacementRequested: e.target.checked }))}
                      className="rounded border-slate-700 text-orange-600 focus:ring-orange-500 bg-slate-900"
                    />
                    <div>
                      <span className="font-bold text-white block">Issue Replacement EMV Chip Card</span>
                      <span className="text-slate-400 font-mono text-[10px]">
                        Free expedited shipping to billing address on record (Expected delivery: 2 business days)
                      </span>
                    </div>
                  </label>

                  <div className="bg-[#121212] p-3 rounded-lg border border-white/5 flex items-center justify-between">
                    <div>
                      <span className="font-bold text-white block">Fraud Incident Ticket Logging</span>
                      <span className="text-slate-400 font-mono text-[10px]">
                        Escalated to Fraud Operations Analyst Queue under ticket <strong className="text-orange-400">{caseTicketId}</strong>
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded uppercase font-bold">
                      READY
                    </span>
                  </div>

                  <div className="bg-[#121212] p-3 rounded-lg border border-white/5 flex items-center justify-between">
                    <div>
                      <span className="font-bold text-white block">SentinelBank Zero Liability Ledger</span>
                      <span className="text-slate-400 font-mono text-[10px]">
                        Protects account holder against unauthorized liability for flagged transactions
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded uppercase font-bold">
                      ACTIVE
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-2">
                <button
                  onClick={() => setCurrentStep(2)}
                  className="px-4 py-2 rounded-lg bg-[#1a1a1a] text-slate-300 text-xs font-mono border border-white/10 hover:text-white"
                >
                  Back
                </button>
                <button
                  onClick={() => handleCompleteStep(3)}
                  className="px-5 py-2.5 rounded-lg bg-orange-600 hover:bg-orange-500 text-white text-xs font-mono font-bold transition-all shadow-lg shadow-orange-600/20 flex items-center space-x-2"
                >
                  <span>APPLY REMEDIATION PROTOCOLS</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 4: Final Audit & Protocol Submission */}
          {currentStep === 4 && (
            <div className="space-y-4">
              <div className="bg-[#080808] p-4 rounded-lg border border-white/5 space-y-3 text-xs">
                <h4 className="text-xs font-bold text-white uppercase font-mono flex items-center gap-2">
                  <FileText className="w-4 h-4 text-orange-400" /> Review Resolution Summary
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono">
                  <div className="bg-[#121212] p-3 rounded border border-white/5 space-y-1">
                    <span className="text-slate-500 text-[10px] uppercase block">Action Title</span>
                    <span className="text-orange-400 font-bold">{actionTitle}</span>
                  </div>
                  <div className="bg-[#121212] p-3 rounded border border-white/5 space-y-1">
                    <span className="text-slate-500 text-[10px] uppercase block">Reference Ticket</span>
                    <span className="text-white font-bold">{caseTicketId}</span>
                  </div>
                  <div className="bg-[#121212] p-3 rounded border border-white/5 space-y-1">
                    <span className="text-slate-500 text-[10px] uppercase block">Target Account / Instrument</span>
                    <span className="text-slate-200">Checking ****-9128 / Card ****-4832</span>
                  </div>
                  <div className="bg-[#121212] p-3 rounded border border-white/5 space-y-1">
                    <span className="text-slate-500 text-[10px] uppercase block">Compliance Status</span>
                    <span className="text-emerald-400 font-bold">100% Verified & Compliant</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-2">
                <button
                  onClick={() => setCurrentStep(3)}
                  className="px-4 py-2 rounded-lg bg-[#1a1a1a] text-slate-300 text-xs font-mono border border-white/10 hover:text-white"
                >
                  Back
                </button>
                <button
                  onClick={() => handleCompleteStep(4)}
                  className="px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold transition-all shadow-lg shadow-emerald-600/20 flex items-center space-x-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>FINALIZE & SUBMIT SECURITY PROTOCOL</span>
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* FINAL SUCCESS SCREEN WHEN 100% COMPLETED */
        <div className="bg-[#111111] border border-emerald-500/40 rounded-xl p-8 shadow-2xl space-y-6 text-center animate-fadeIn">
          <div className="w-16 h-16 rounded-full bg-emerald-500/10 border-2 border-emerald-500 text-emerald-400 flex items-center justify-center mx-auto shadow-inner">
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <div className="space-y-2 max-w-xl mx-auto">
            <span className="text-[11px] font-mono font-bold uppercase px-3 py-1 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              RESOLUTION COMPLETED
            </span>
            <h2 className="text-2xl font-light text-white tracking-tight pt-2">
              Security Protocol Executed Successfully
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              The requested action <strong className="text-white font-mono">"{actionTitle}"</strong> has been executed and logged in the SentinelBank Security Ledger. Your account and payment instruments are fully protected.
            </p>
          </div>

          {/* Summary Box */}
          <div className="bg-[#080808] p-5 rounded-xl border border-white/10 max-w-2xl mx-auto text-left space-y-3 font-mono text-xs">
            <div className="flex justify-between items-center border-b border-white/10 pb-2.5">
              <span className="text-slate-400">Action Reference Code:</span>
              <span className="font-bold text-orange-400">{referenceId}</span>
            </div>
            <div className="flex justify-between items-center border-b border-white/10 pb-2.5">
              <span className="text-slate-400">Fraud Operations Ticket:</span>
              <span className="font-bold text-white">{caseTicketId}</span>
            </div>
            <div className="flex justify-between items-center border-b border-white/10 pb-2.5">
              <span className="text-slate-400">Timestamp:</span>
              <span className="text-slate-300">{new Date().toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Account Protection Status:</span>
              <span className="text-emerald-400 font-bold uppercase flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> SECURED
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={handleExportReceipt}
              className="px-4 py-2.5 rounded-lg bg-[#1c1c1c] hover:bg-[#282828] text-slate-200 hover:text-white border border-white/10 text-xs font-mono transition-colors flex items-center space-x-2"
            >
              <Download className="w-4 h-4 text-orange-400" />
              <span>{downloadSuccess ? 'RECEIPT EXPORTED!' : 'EXPORT RESOLUTION RECEIPT'}</span>
            </button>

            <button
              onClick={onBackToDashboard}
              className="px-5 py-2.5 rounded-lg bg-orange-600 hover:bg-orange-500 text-white text-xs font-mono font-bold transition-all shadow-lg shadow-orange-600/20"
            >
              RETURN TO CUSTOMER DASHBOARD
            </button>

            <button
              onClick={onBackToChat}
              className="px-5 py-2.5 rounded-lg bg-[#222222] hover:bg-[#2c2c2c] text-white text-xs font-mono border border-white/10 transition-colors"
            >
              RETURN TO AI SUPPORT CHAT
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
