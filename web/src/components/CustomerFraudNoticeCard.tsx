import React from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Lock,
  ArrowRight,
  Clock,
  ShieldCheck,
  Check,
  Bell,
  MessageSquare,
  HelpCircle
} from 'lucide-react';
import { FraudAssessment, CaseRecord, SecurityIncident } from '../types';

interface CustomerFraudNoticeCardProps {
  assessment?: FraudAssessment;
  caseRecord?: CaseRecord;
  incident?: SecurityIncident;
  onActionClick?: (actionText: string) => void;
}

export const CustomerFraudNoticeCard: React.FC<CustomerFraudNoticeCardProps> = ({
  assessment,
  caseRecord,
  incident,
  onActionClick
}) => {
  // Extract high-level values
  const category = assessment?.category || incident?.fraudCategory || caseRecord?.title || 'Unrecognized Transaction / Fraud Alert';
  const severityRaw = (assessment?.severity || incident?.severity || caseRecord?.priority || 'High').toString();
  const severityUpper = severityRaw.charAt(0).toUpperCase() + severityRaw.slice(1).toLowerCase();
  
  const caseId = assessment?.caseId || incident?.incidentId || caseRecord?.caseId || 'CASE-2026-8812';
  
  const rawStatus = incident?.status || caseRecord?.status || 'Under Review';
  const displayStatus = rawStatus.replace(/_/g, ' ').toUpperCase();

  // Severity configurations for customer portal
  const severityConfig: Record<string, { badge: string; text: string; bg: string; icon: React.ReactNode }> = {
    Critical: {
      badge: 'bg-red-500/20 text-red-400 border-red-500/40',
      text: 'text-red-400',
      bg: 'border-red-500/30 bg-gradient-to-b from-red-950/30 to-[#0e0e0e]',
      icon: <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
    },
    High: {
      badge: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
      text: 'text-orange-400',
      bg: 'border-orange-500/30 bg-gradient-to-b from-orange-950/30 to-[#0e0e0e]',
      icon: <AlertCircle className="w-4 h-4 text-orange-400" />
    },
    Medium: {
      badge: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
      text: 'text-amber-400',
      bg: 'border-amber-500/30 bg-gradient-to-b from-amber-950/30 to-[#0e0e0e]',
      icon: <AlertTriangle className="w-4 h-4 text-amber-400" />
    },
    Low: {
      badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
      text: 'text-emerald-400',
      bg: 'border-emerald-500/30 bg-gradient-to-b from-emerald-950/30 to-[#0e0e0e]',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />
    }
  };

  const currentSev = severityConfig[severityUpper] || severityConfig.High;

  // Customer friendly actions
  const defaultActions = assessment?.recommendedActions && assessment.recommendedActions.length > 0
    ? assessment.recommendedActions
    : ['Freeze Debit Card', 'Block Online Banking', 'Report Unauthorized Charge', 'Speak with Fraud Specialist'];

  // Customer friendly summary
  const customerSummary = assessment?.summaryText || incident?.aiAssessmentSummary ||
    "Our real-time security surveillance engine flagged this activity for review. Your account is protected under our Zero Liability policy, and our dedicated Fraud Operations team is actively investigating this case.";

  // Determine timeline progress step (1-4)
  let stepNumber = 2; // default: AI Risk Scan completed, sent to hub
  if (rawStatus.toLowerCase().includes('resolve') || rawStatus.toLowerCase().includes('approved')) {
    stepNumber = 4;
  } else if (rawStatus.toLowerCase().includes('review') || rawStatus.toLowerCase().includes('investigat')) {
    stepNumber = 3;
  }

  return (
    <div className={`mt-4 rounded-xl border p-5 text-white shadow-xl transition-all space-y-4 font-sans ${currentSev.bg}`}>
      {/* Top Banner: Fraud Detected Confirmation */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-orange-500/20 border border-orange-500/30 text-orange-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded border border-orange-500/20">
                CASE {caseId}
              </span>
              <span className="text-[10px] font-mono font-bold uppercase text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> ZERO LIABILITY ACTIVE
              </span>
            </div>
            <h4 className="text-sm font-bold tracking-tight text-white mt-1">
              Fraud Protection & Case Confirmation
            </h4>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Risk Level Badge */}
          <span className={`text-[10px] font-mono uppercase font-bold px-2.5 py-1 rounded border flex items-center gap-1.5 ${currentSev.badge}`}>
            {currentSev.icon}
            <span>RISK LEVEL: {severityUpper.toUpperCase()}</span>
          </span>

          {/* Current Status Badge */}
          <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded bg-blue-500/15 text-blue-300 border border-blue-500/30 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span>STATUS: {displayStatus}</span>
          </span>
        </div>
      </div>

      {/* Customer Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Fraud Category */}
        <div className="bg-[#080808] p-3 rounded-lg border border-white/5 space-y-1">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Fraud Category</span>
          <span className="font-semibold text-orange-400 flex items-center gap-1.5 text-xs">
            <ShieldAlert className="w-4 h-4 text-orange-400 flex-shrink-0" />
            <span className="truncate">{category}</span>
          </span>
        </div>

        {/* Current Case Status */}
        <div className="bg-[#080808] p-3 rounded-lg border border-white/5 space-y-1">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Investigation Status</span>
          <span className="font-mono font-bold text-xs text-white flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
            <span>{displayStatus} • Assigned to Analyst Hub</span>
          </span>
        </div>
      </div>

      {/* AI Customer-Friendly Summary */}
      <div className="bg-[#0a0a0a] p-3.5 rounded-lg border border-white/10 space-y-1">
        <span className="text-[10px] text-orange-400 font-mono font-bold uppercase tracking-wider flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-orange-400" /> Security Summary & Guidance
        </span>
        <p className="text-xs text-slate-200 leading-relaxed font-sans pt-0.5">
          {customerSummary}
        </p>
      </div>

      {/* Investigation Progress Timeline */}
      <div className="bg-[#080808] p-3.5 rounded-lg border border-white/5 space-y-2">
        <span className="text-[10px] text-slate-400 font-mono font-bold uppercase tracking-wider block">
          Investigation Progress Timeline
        </span>
        <div className="grid grid-cols-4 gap-2 pt-1 font-mono text-[10px]">
          {/* Step 1 */}
          <div className="flex flex-col items-center text-center space-y-1">
            <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center font-bold">
              <Check className="w-3.5 h-3.5" />
            </div>
            <span className="text-emerald-400 font-semibold">1. Report Submitted</span>
          </div>

          {/* Step 2 */}
          <div className="flex flex-col items-center text-center space-y-1">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${
              stepNumber >= 2 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-slate-800 text-slate-500'
            }`}>
              {stepNumber >= 2 ? <Check className="w-3.5 h-3.5" /> : '2'}
            </div>
            <span className={stepNumber >= 2 ? 'text-emerald-400 font-semibold' : 'text-slate-500'}>2. AI Risk Scan</span>
          </div>

          {/* Step 3 */}
          <div className="flex flex-col items-center text-center space-y-1">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${
              stepNumber >= 3 ? 'bg-orange-500/20 text-orange-400 border border-orange-500/40 animate-pulse' : 'bg-slate-800 text-slate-500'
            }`}>
              {stepNumber >= 3 ? <Clock className="w-3.5 h-3.5" /> : '3'}
            </div>
            <span className={stepNumber >= 3 ? 'text-orange-400 font-semibold' : 'text-slate-500'}>3. Analyst Review</span>
          </div>

          {/* Step 4 */}
          <div className="flex flex-col items-center text-center space-y-1">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${
              stepNumber >= 4 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-slate-800 text-slate-500'
            }`}>
              {stepNumber >= 4 ? <Check className="w-3.5 h-3.5" /> : '4'}
            </div>
            <span className={stepNumber >= 4 ? 'text-emerald-400 font-semibold' : 'text-slate-500'}>4. Resolution</span>
          </div>
        </div>
      </div>

      {/* Notifications & Status Updates */}
      <div className="bg-[#050505] p-3 rounded-lg border border-white/5 space-y-1.5 text-xs font-mono">
        <div className="flex items-center justify-between text-[10px] text-slate-400">
          <span className="flex items-center gap-1 font-bold text-slate-300">
            <Bell className="w-3 h-3 text-orange-400" /> Notifications & Status Updates
          </span>
          <span className="text-emerald-400 font-bold">LIVE SYNC</span>
        </div>
        <p className="text-[11px] text-slate-300">
          • Case created and automatically dispatched to Admin Operations Analyst Hub. You will receive immediate updates as analysts review your report.
        </p>
      </div>

      {/* Recommended Security Actions */}
      <div className="pt-2 border-t border-white/10 space-y-2">
        <span className="text-[10px] text-slate-400 font-mono font-bold uppercase tracking-wider block">
          Recommended Security Actions
        </span>
        <div className="flex flex-wrap gap-2">
          {defaultActions.map((action, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onActionClick && onActionClick(action)}
              className="text-xs bg-[#1f1f1f] hover:bg-orange-600 hover:text-white text-slate-100 px-3 py-1.5 rounded-lg border border-white/15 transition-all flex items-center gap-1.5 font-medium shadow-sm"
            >
              <span>{action}</span>
              <ArrowRight className="w-3.5 h-3.5 text-orange-400 group-hover:text-white" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
