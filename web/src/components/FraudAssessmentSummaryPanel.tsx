import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Zap,
  ArrowRight,
  Activity,
  ShieldCheck,
  Download,
  FileText,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp,
  RefreshCw
} from 'lucide-react';
import { FraudAssessment } from '../types';

interface AssessmentItem {
  id: string;
  queryText: string;
  timestamp: string;
  assessment: FraudAssessment;
}

interface FraudAssessmentSummaryPanelProps {
  assessmentItems: AssessmentItem[];
  onExecuteAction: (actionText: string, assessment?: FraudAssessment) => void;
}

export const FraudAssessmentSummaryPanel: React.FC<FraudAssessmentSummaryPanelProps> = ({
  assessmentItems,
  onExecuteAction
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);

  if (!assessmentItems || assessmentItems.length === 0) {
    return (
      <div className="bg-[#111111] border border-white/10 rounded-xl p-6 text-slate-400 font-mono text-xs flex flex-col items-center justify-center space-y-3 text-center shadow-lg">
        <div className="w-12 h-12 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 flex items-center justify-center">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white uppercase font-sans">AI Fraud Assessment Hub</h3>
          <p className="text-slate-400 text-xs mt-1">
            No fraud queries submitted yet. Ask a question or report a suspicious charge in the chat above to generate an automated AI Fraud Risk Assessment Dossier.
          </p>
        </div>
      </div>
    );
  }

  const activeItem = assessmentItems[selectedIndex] || assessmentItems[0];
  const { assessment } = activeItem;

  const severityConfig = {
    Critical: {
      border: 'border-red-500/40 bg-red-950/30',
      badge: 'bg-red-500/20 text-red-400 border-red-500/40',
      text: 'text-red-400',
      meter: 'bg-red-500',
      icon: <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
    },
    High: {
      border: 'border-orange-500/40 bg-orange-950/30',
      badge: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
      text: 'text-orange-400',
      meter: 'bg-orange-500',
      icon: <AlertCircle className="w-4 h-4 text-orange-400" />
    },
    Medium: {
      border: 'border-amber-500/40 bg-amber-950/30',
      badge: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
      text: 'text-amber-400',
      meter: 'bg-amber-500',
      icon: <AlertTriangle className="w-4 h-4 text-amber-400" />
    },
    Low: {
      border: 'border-emerald-500/40 bg-emerald-950/30',
      badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
      text: 'text-emerald-400',
      meter: 'bg-emerald-500',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />
    }
  };

  const currentSev = severityConfig[assessment.severity] || severityConfig.High;

  const handleDownloadReport = () => {
    const reportData = {
      assessmentTitle: "SentinelBank AI Fraud Assessment Report",
      generatedAt: new Date().toISOString(),
      customerQuery: activeItem.queryText,
      timestamp: activeItem.timestamp,
      classification: {
        category: assessment.category,
        severity: assessment.severity,
        confidenceScore: `${assessment.confidenceScore}%`,
        financialRisk: assessment.financialRisk
      },
      summary: assessment.summaryText,
      keyIndicators: assessment.keyIndicators,
      recommendedActions: assessment.recommendedActions
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Fraud_Assessment_Report_${activeItem.id}.json`;
    a.click();
    URL.revokeObjectURL(url);

    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 2500);
  };

  return (
    <div className="bg-[#111111] border border-white/10 rounded-xl shadow-2xl overflow-hidden font-sans">
      {/* Header Bar */}
      <div className="p-4 bg-[#080808] border-b border-white/10 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-orange-600/20 border border-orange-500/30 text-orange-400 flex items-center justify-center shadow-inner">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-white tracking-tight uppercase">
                AI Fraud Assessment Dossier
              </h3>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
                {assessmentItems.length} {assessmentItems.length === 1 ? 'RECORD' : 'RECORDS'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Automated Risk Classification • Gemini 3.6 Flash & Rule Graph Engine
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Download Report Action */}
          <button
            onClick={handleDownloadReport}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#1a1a1a] hover:bg-[#252525] border border-white/10 text-xs text-slate-200 hover:text-white font-mono transition-colors"
            title="Download JSON Report"
          >
            <Download className="w-3.5 h-3.5 text-orange-400" />
            <span>{downloadSuccess ? 'REPORT DOWNLOADED!' : 'EXPORT DOSSIER'}</span>
          </button>

          {/* Toggle Panel Visibility */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg bg-[#181818] hover:bg-[#222222] border border-white/10 text-slate-400 hover:text-white"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-5 space-y-5 bg-[#0a0a0a]">
          {/* Selector Tabs if multiple assessments exist */}
          {assessmentItems.length > 1 && (
            <div className="flex items-center space-x-2 overflow-x-auto pb-1 border-b border-white/5">
              <span className="text-[10px] font-mono text-slate-500 uppercase font-bold pr-2 flex items-center gap-1">
                <Layers className="w-3 h-3 text-orange-500" /> Assessments:
              </span>
              {assessmentItems.map((item, idx) => (
                <button
                  key={item.id}
                  onClick={() => setSelectedIndex(idx)}
                  className={`px-3 py-1.5 rounded-md text-xs font-mono transition-all flex items-center space-x-2 whitespace-nowrap border ${
                    selectedIndex === idx
                      ? 'bg-orange-600/20 text-orange-400 border-orange-500/50 font-bold shadow-sm'
                      : 'bg-[#121212] text-slate-400 hover:text-white border-white/5'
                  }`}
                >
                  <span className="w-2 h-2 rounded-full bg-orange-500" />
                  <span className="truncate max-w-[140px]">{item.assessment.category}</span>
                  <span className="text-[10px] text-slate-500">({item.timestamp})</span>
                </button>
              ))}
            </div>
          )}

          {/* Active Query Context Pill */}
          <div className="bg-[#121212] p-3 rounded-lg border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div className="space-y-0.5">
              <span className="text-[10px] font-mono text-slate-500 uppercase font-bold">Analyzed User Query</span>
              <p className="text-slate-200 italic font-sans text-xs">"{activeItem.queryText}"</p>
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0 font-mono text-[11px] text-slate-400">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>Timestamp: {activeItem.timestamp}</span>
            </div>
          </div>

          {/* Core Risk Metrics Dashboard */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {/* Category */}
            <div className="bg-[#121212] p-3.5 rounded-lg border border-white/5 flex flex-col justify-between">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-1">
                Fraud Category
              </span>
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-orange-400 flex-shrink-0" />
                <span className="font-bold text-sm text-white truncate">{assessment.category}</span>
              </div>
            </div>

            {/* Severity */}
            <div className={`p-3.5 rounded-lg border flex flex-col justify-between ${currentSev.border}`}>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
                Risk Severity Level
              </span>
              <div className="flex items-center justify-between">
                <span className={`font-mono font-bold text-sm uppercase flex items-center gap-1.5 ${currentSev.text}`}>
                  {currentSev.icon}
                  <span>{assessment.severity}</span>
                </span>
                <span className={`text-[9px] font-mono uppercase font-bold px-2 py-0.5 rounded border ${currentSev.badge}`}>
                  LEVEL {assessment.severity === 'Critical' ? '4' : assessment.severity === 'High' ? '3' : '2'}
                </span>
              </div>
            </div>

            {/* Confidence Score */}
            <div className="bg-[#121212] p-3.5 rounded-lg border border-white/5 flex flex-col justify-between">
              <div className="flex justify-between items-center mb-1">
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                  AI Confidence
                </span>
                <span className="text-xs font-mono font-bold text-orange-400">{assessment.confidenceScore}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full ${currentSev.meter} transition-all duration-500`}
                  style={{ width: `${assessment.confidenceScore}%` }}
                />
              </div>
            </div>

            {/* Financial Risk Exposure */}
            <div className="bg-[#121212] p-3.5 rounded-lg border border-white/5 flex flex-col justify-between">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-1">
                Potential Exposure
              </span>
              <span className={`font-mono font-bold text-sm ${currentSev.text}`}>
                {assessment.financialRisk}
              </span>
            </div>
          </div>

          {/* Assessment Summary Narrative */}
          <div className="bg-[#121212] p-4 rounded-lg border border-white/5 space-y-1.5">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center space-x-2">
              <Sparkles className="w-3.5 h-3.5 text-orange-400" />
              <span>Fraud Risk Assessment Summary</span>
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              {assessment.summaryText}
            </p>
          </div>

          {/* Key Risk Indicators Grid */}
          {assessment.keyIndicators && assessment.keyIndicators.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                <Activity className="w-3.5 h-3.5 text-orange-400" />
                <span>Detected Key Risk Indicators</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {assessment.keyIndicators.map((indicator, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-[#141414] border border-white/5 text-xs text-slate-200 flex items-start space-x-2"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-1.5 flex-shrink-0" />
                    <span className="font-sans text-slate-300">{indicator}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Next Actions */}
          {assessment.recommendedActions && assessment.recommendedActions.length > 0 && (
            <div className="space-y-2.5 pt-2 border-t border-white/10">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Recommended Security Protocol Actions</span>
              </h4>
              <div className="flex flex-wrap gap-2">
                {assessment.recommendedActions.map((action, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onExecuteAction(action, assessment)}
                    className="px-3 py-2 rounded-lg bg-orange-600/10 hover:bg-orange-600 text-orange-400 hover:text-white border border-orange-500/30 hover:border-orange-500 text-xs font-mono font-medium transition-all flex items-center space-x-2 group"
                  >
                    <span>{action}</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
