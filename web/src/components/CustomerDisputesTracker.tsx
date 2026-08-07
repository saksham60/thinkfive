import React, { useState } from 'react';
import {
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ShieldCheck,
  FileText,
  Lock,
  Bell
} from 'lucide-react';
import { CaseRecord, SecurityIncident, FraudAlert, FraudAssessment } from '../types';
import { CustomerFraudNoticeCard } from './CustomerFraudNoticeCard';

interface CustomerDisputesTrackerProps {
  cases?: CaseRecord[];
  incidents?: SecurityIncident[];
  alerts?: FraudAlert[];
  assessmentItems?: Array<{
    id: string;
    queryText: string;
    timestamp: string;
    assessment: FraudAssessment;
  }>;
  onExecuteAction: (actionText: string) => void;
}

export const CustomerDisputesTracker: React.FC<CustomerDisputesTrackerProps> = ({
  cases = [],
  incidents = [],
  alerts = [],
  assessmentItems = [],
  onExecuteAction
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  // Combine cases into a clean list for the customer
  const totalItems = [
    ...incidents.map(inc => ({
      id: inc.incidentId,
      title: inc.fraudCategory,
      category: inc.fraudCategory,
      severity: inc.severity,
      status: inc.status,
      timestamp: inc.timestamp,
      summary: inc.aiAssessmentSummary,
      incident: inc
    })),
    ...cases.map(c => ({
      id: c.caseId,
      title: c.title,
      category: c.title,
      severity: c.priority,
      status: c.status,
      timestamp: c.createdAt,
      summary: c.description,
      caseRecord: c
    })),
    ...assessmentItems.map(item => ({
      id: item.id,
      title: item.assessment.category,
      category: item.assessment.category,
      severity: item.assessment.severity,
      status: item.assessment.caseId ? 'Under Review' : 'Reported',
      timestamp: item.timestamp,
      summary: item.assessment.summaryText,
      assessment: item.assessment
    }))
  ];

  if (totalItems.length === 0) {
    return (
      <div className="bg-[#111111] border border-white/10 rounded-xl p-6 text-slate-400 font-mono text-xs flex flex-col items-center justify-center space-y-3 text-center shadow-lg">
        <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white uppercase font-sans">Security & Fraud Case Tracker</h3>
          <p className="text-slate-400 text-xs mt-1 max-w-md">
            No active disputes or fraud cases on record. You can report suspicious activity anytime via the AI Banking Concierge or Real-Time Fraud Alert Center.
          </p>
        </div>
      </div>
    );
  }

  const activeItem = totalItems[selectedIndex] || totalItems[0];

  return (
    <div className="bg-[#111111] border border-white/10 rounded-xl shadow-2xl overflow-hidden font-sans">
      {/* Top Header Bar */}
      <div className="p-4 bg-[#080808] border-b border-white/10 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-orange-600/20 border border-orange-500/30 text-orange-400 flex items-center justify-center shadow-inner">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-white tracking-tight uppercase">
                Your Fraud Disputes & Security Cases
              </h3>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
                {totalItems.length} {totalItems.length === 1 ? 'CASE' : 'CASES'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Live Customer Case Status • Direct Sync with SentinelBank Analyst Operations Hub
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs">
          <span className="text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> ZERO LIABILITY PROTECTED
          </span>
        </div>
      </div>

      {/* Case Selector Tabs if multiple */}
      {totalItems.length > 1 && (
        <div className="p-3 bg-[#0a0a0a] border-b border-white/5 flex items-center gap-2 overflow-x-auto custom-scrollbar">
          {totalItems.map((item, idx) => (
            <button
              key={item.id}
              onClick={() => setSelectedIndex(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center space-x-2 flex-shrink-0 ${
                selectedIndex === idx
                  ? 'bg-orange-600 text-white font-bold shadow-md'
                  : 'bg-[#141414] text-slate-400 hover:text-white border border-white/5'
              }`}
            >
              <span>{item.id}</span>
              <span className="text-[10px] opacity-80">({item.status})</span>
            </button>
          ))}
        </div>
      )}

      {/* Case Detail Display */}
      <div className="p-4">
        <CustomerFraudNoticeCard
          assessment={'assessment' in activeItem ? activeItem.assessment : undefined}
          caseRecord={'caseRecord' in activeItem ? activeItem.caseRecord : undefined}
          incident={'incident' in activeItem ? activeItem.incident : undefined}
          onActionClick={onExecuteAction}
        />
      </div>
    </div>
  );
};
