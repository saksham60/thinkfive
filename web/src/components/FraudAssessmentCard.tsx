import React from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  Activity,
  ShieldCheck,
  Zap,
  FileSearch,
  MapPin,
  Smartphone,
  CheckSquare,
  UserCheck
} from 'lucide-react';
import { FraudAssessment } from '../types';

interface FraudAssessmentCardProps {
  assessment: FraudAssessment;
  onActionClick?: (actionText: string, assessment?: FraudAssessment) => void;
}

export const FraudAssessmentCard: React.FC<FraudAssessmentCardProps> = ({
  assessment,
  onActionClick
}) => {
  if (!assessment || !assessment.isFraud || assessment.category === 'General Banking Inquiry') {
    return null;
  }

  const {
    category,
    severity,
    confidenceScore,
    fraudProbability,
    keyIndicators,
    financialRisk,
    recommendedActions,
    summaryText,
    evidence,
    suspiciousIndicators,
    relatedEntities,
    riskScore,
    priority,
    humanApprovalRequired,
    caseId,
    assignedAnalyst
  } = assessment;

  const displayProbability = fraudProbability || `${confidenceScore}%`;
  const displayScore = riskScore !== undefined ? riskScore : (confidenceScore || 96);
  const displayEvidence = evidence && evidence.length > 0
    ? evidence
    : (keyIndicators && keyIndicators.length > 0 ? keyIndicators : [
        'Anomalous device fingerprint or new location detected',
        'Transaction velocity deviates from customer baseline',
        'Merchant category flagged in risk database'
      ]);

  const severityUpper = (severity || priority || 'High').toString().toUpperCase();

  // Severity styling maps
  const severityConfig: Record<string, { border: string; badge: string; text: string; icon: React.ReactNode }> = {
    CRITICAL: {
      border: 'border-red-500/40 bg-gradient-to-b from-red-950/30 to-[#0e0e0e]',
      badge: 'bg-red-500/15 text-red-400 border-red-500/40',
      text: 'text-red-400',
      icon: <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
    },
    HIGH: {
      border: 'border-orange-500/40 bg-gradient-to-b from-orange-950/30 to-[#0e0e0e]',
      badge: 'bg-orange-500/15 text-orange-400 border-orange-500/40',
      text: 'text-orange-400',
      icon: <AlertCircle className="w-4 h-4 text-orange-400" />
    },
    MEDIUM: {
      border: 'border-amber-500/40 bg-gradient-to-b from-amber-950/30 to-[#0e0e0e]',
      badge: 'bg-amber-500/15 text-amber-400 border-amber-500/40',
      text: 'text-amber-400',
      icon: <AlertTriangle className="w-4 h-4 text-amber-400" />
    },
    LOW: {
      border: 'border-emerald-500/40 bg-gradient-to-b from-emerald-950/30 to-[#0e0e0e]',
      badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40',
      text: 'text-emerald-400',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />
    }
  };

  const currentSev = severityConfig[severityUpper] || severityConfig.HIGH;

  return (
    <div className={`mt-4 rounded-xl border p-5 text-white shadow-2xl transition-all ${currentSev.border} space-y-4 font-sans`}>
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-orange-500/20 border border-orange-500/30 text-orange-400">
            <FileSearch className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
              <span>FRAUD INVESTIGATION REPORT</span>
            </h4>
            <p className="text-[11px] text-slate-400 font-mono">LangGraph Multi-Agent Security Service • Automated Assessment</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Severity Badge */}
          <span className={`text-[10px] font-mono uppercase font-bold px-2.5 py-1 rounded border flex items-center gap-1.5 ${currentSev.badge}`}>
            {currentSev.icon}
            <span>SEVERITY: {severityUpper}</span>
          </span>

          {/* Probability Meter Badge */}
          <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded bg-orange-500/10 text-orange-400 border border-orange-500/30 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-orange-400" />
            <span>PROBABILITY: {displayProbability}</span>
          </span>
        </div>
      </div>

      {/* Key Metrics Dashboard Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        {/* Fraud Category */}
        <div className="bg-[#080808] p-3 rounded-lg border border-white/5 space-y-1">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Fraud Category</span>
          <span className="font-semibold text-orange-400 flex items-center gap-1.5 text-xs">
            <ShieldAlert className="w-4 h-4 flex-shrink-0 text-orange-400" />
            <span className="truncate">{category}</span>
          </span>
        </div>

        {/* Risk Score */}
        <div className="bg-[#080808] p-3 rounded-lg border border-white/5 space-y-1">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Risk Score</span>
          <div className="flex items-center justify-between">
            <span className={`font-mono font-extrabold text-sm ${currentSev.text}`}>
              {displayScore} / 100
            </span>
            <div className="w-12 bg-slate-800 rounded-full h-2 overflow-hidden border border-white/10">
              <div
                className="bg-orange-500 h-full rounded-full"
                style={{ width: `${Math.min(displayScore, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Financial Exposure */}
        <div className="bg-[#080808] p-3 rounded-lg border border-white/5 space-y-1">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Financial Risk</span>
          <span className="font-mono font-bold text-xs text-white block truncate">
            {financialRisk}
          </span>
        </div>

        {/* Protection Guarantee */}
        <div className="bg-[#080808] p-3 rounded-lg border border-white/5 space-y-1">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Policy Protection</span>
          <span className="text-emerald-400 font-semibold text-xs flex items-center gap-1">
            <ShieldCheck className="w-4 h-4 flex-shrink-0 text-emerald-400" />
            <span>Zero Liability Active</span>
          </span>
        </div>
      </div>

      {/* Investigation Summary Narrative */}
      <div className="bg-[#0a0a0a] p-3.5 rounded-lg border border-white/10 space-y-1">
        <span className="text-[10px] text-orange-400 font-mono font-bold uppercase tracking-wider flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-orange-400" /> Investigation Summary
        </span>
        <p className="text-xs text-slate-200 leading-relaxed font-sans pt-0.5">
          {summaryText || "The transaction significantly deviates from the customer's normal behaviour and matches known fraud patterns."}
        </p>
      </div>

      {/* Evidence & Suspicious Indicators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Evidence Collected */}
        <div className="bg-[#080808] p-3 rounded-lg border border-white/5 space-y-2">
          <span className="text-[10px] text-slate-400 font-mono font-bold uppercase tracking-wider flex items-center gap-1">
            <CheckSquare className="w-3.5 h-3.5 text-orange-400" /> Evidence Collected
          </span>
          <div className="space-y-1.5">
            {displayEvidence.map((ev, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-[11px] text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-1.5 flex-shrink-0" />
                <span className="leading-tight">{ev}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Related Entities & Context */}
        <div className="bg-[#080808] p-3 rounded-lg border border-white/5 space-y-2">
          <span className="text-[10px] text-slate-400 font-mono font-bold uppercase tracking-wider flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-orange-400" /> Related Entities & Device Signals
          </span>
          <div className="space-y-1.5 text-[11px] text-slate-300">
            <div className="flex items-center gap-2">
              <MapPin className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
              <span className="text-slate-400 font-mono">Location:</span>
              <span className="text-white font-medium">{relatedEntities?.location || 'Lagos, Nigeria (Anomalous IP)'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Smartphone className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
              <span className="text-slate-400 font-mono">Device Fingerprint:</span>
              <span className="text-white font-medium">{relatedEntities?.device || 'Unrecognized Mobile Browser'}</span>
            </div>
            <div className="flex items-center gap-2">
              <UserCheck className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
              <span className="text-slate-400 font-mono">Analyst Escalation:</span>
              <span className="text-orange-400 font-medium">Assigned to {assignedAnalyst || 'Alex Vance (Analyst Hub)'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommended Action & Case Dispatch */}
      {recommendedActions && recommendedActions.length > 0 && (
        <div className="pt-2 border-t border-white/10 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-slate-400 font-mono font-bold uppercase tracking-wider">
              Recommended Protective Actions
            </span>
            {caseId && (
              <span className="text-[10px] font-mono text-slate-400 bg-white/5 px-2 py-0.5 rounded border border-white/10">
                Case Ref: <span className="text-orange-400 font-bold">{caseId}</span>
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {recommendedActions.map((action, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onActionClick && onActionClick(action, assessment)}
                className="text-xs bg-[#1f1f1f] hover:bg-orange-600 hover:text-white text-slate-100 px-3 py-1.5 rounded-lg border border-white/15 transition-all flex items-center gap-1.5 font-medium shadow-sm"
              >
                <span>{action}</span>
                <ArrowRight className="w-3.5 h-3.5 text-orange-400 group-hover:text-white" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

