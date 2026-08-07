import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Clock,
  User,
  CreditCard,
  MapPin,
  Sparkles,
  FileText,
  UserCheck,
  ShieldX,
  Lock,
  PhoneCall,
  CheckCircle2,
  XCircle,
  Eye,
  ArrowUpRight,
  ChevronDown,
  ChevronUp,
  AlertOctagon
} from 'lucide-react';
import { FraudAlert, SecurityIncident, IncidentStatus } from '../types';

interface RealTimeFraudAlertBannerProps {
  alerts: FraudAlert[];
  incidents: SecurityIncident[];
  onSelectAlertOrIncident: (item: { alert?: FraudAlert; incident?: SecurityIncident }) => void;
  onRefreshAlerts: () => void;
  onRefreshIncidents?: () => void;
  onOpenModal: () => void;
}

export const RealTimeFraudAlertBanner: React.FC<RealTimeFraudAlertBannerProps> = ({
  alerts,
  incidents,
  onSelectAlertOrIncident,
  onRefreshAlerts,
  onRefreshIncidents,
  onOpenModal
}) => {
  const [assignedAnalyst, setAssignedAnalyst] = useState('Alex Vance (Lead Analyst)');
  const [status, setStatus] = useState<string>('New');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  // Pick the top active alert or incident for prominent top notification
  const activeAlert = alerts.find(a => a.status === 'open' || a.status === 'investigating') || alerts[0];
  const activeIncident = incidents.find(i => i.status !== 'Resolved') || incidents[0];

  if (!activeAlert && !activeIncident) {
    return null;
  }

  // Derive unified field values
  const alertId = activeAlert?.alertId || activeIncident?.incidentId || 'ALT-2026-9921';
  const customerName = activeAlert?.customerName || 'Priya Sharma';
  const customerId = activeAlert?.customerId || 'CUST-1001';
  const merchant = activeAlert?.merchantName || 'Luxure Electronics Overseas Ltd';
  const amount = activeAlert ? `₹${activeAlert.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} INR` : '₹2,499.99 INR';
  const timestamp = activeAlert?.timestamp ? new Date(activeAlert.timestamp).toLocaleString() : new Date().toLocaleString();
  const location = activeAlert?.location || 'Lagos, Nigeria (IP Geo-Mismatch)';
  const category = activeAlert?.reasons[0] || activeIncident?.fraudCategory || 'Unrecognized International Transaction / Card Not Present';
  const riskScore = activeAlert?.riskScore || 94;
  const severity = (activeAlert?.priority || activeIncident?.severity || 'Critical').toUpperCase();
  const summaryText = activeIncident?.aiAssessmentSummary || activeAlert?.summary ||
    'Multi-agent AI surveillance engine flagged high risk score (94/100). Geographical IP mismatch (Lagos vs Mumbai) and velocity limit 55x exceeded.';
  const currentStatus = status || activeIncident?.status || activeAlert?.status || 'New';

  const showFeedback = (msg: string) => {
    setActionFeedback(msg);
    setTimeout(() => setActionFeedback(null), 4000);
  };

  // Action Button Handlers
  const handleAssignToAnalyst = async () => {
    setAssignedAnalyst('Alex Vance (Assigned)');
    setStatus('Assigned');
    showFeedback(`Alert ${alertId} assigned to Analyst Alex Vance.`);
  };

  const handleStartInvestigation = async () => {
    setStatus('Under Review');
    if (activeIncident && onRefreshIncidents) {
      try {
        await fetch(`/api/incidents/${activeIncident.incidentId}/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'Under Review', analystName: 'Alex Vance' })
        });
        onRefreshIncidents();
      } catch (e) {
        console.error('Failed to start investigation', e);
      }
    }
    showFeedback(`Investigation started for Alert ${alertId}. Status updated to UNDER REVIEW.`);
  };

  const handleEscalateCase = async () => {
    setStatus('Escalated');
    showFeedback(`Case ${alertId} escalated to Senior Fraud Risk Lead.`);
  };

  const handleBlockCard = async () => {
    if (activeAlert) {
      try {
        await fetch(`/api/alerts/${activeAlert.alertId}/approve-freeze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ analystName: 'Alex Vance', reason: 'Analyst blocked card via prominent alert banner.' })
        });
        onRefreshAlerts();
      } catch (e) {
        console.error('Failed to freeze card', e);
      }
    }
    showFeedback(`Debit Card CARD-4832 blocked successfully for ${customerName}.`);
  };

  const handleFreezeAccount = async () => {
    showFeedback(`Account ${customerId} frozen. All online transfers temporarily suspended.`);
  };

  const handleContactCustomer = async () => {
    showFeedback(`Push notification & SMS update dispatched to ${customerName} (${customerId}).`);
  };

  const handleMarkFalsePositive = async () => {
    if (activeAlert) {
      try {
        await fetch(`/api/alerts/${activeAlert.alertId}/reject-safe`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ analystName: 'Alex Vance', notes: 'Verified as false positive.' })
        });
        onRefreshAlerts();
      } catch (e) {
        console.error('Failed to reject alert', e);
      }
    }
    setStatus('Resolved');
    showFeedback(`Alert ${alertId} marked as False Positive / Legitimate.`);
  };

  const handleResolveAlert = async () => {
    setStatus('Resolved');
    if (activeIncident && onRefreshIncidents) {
      try {
        await fetch(`/api/incidents/${activeIncident.incidentId}/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'Resolved', analystName: 'Alex Vance', noteText: 'Resolved by analyst from alert banner.' })
        });
        onRefreshIncidents();
      } catch (e) {
        console.error('Failed to resolve incident', e);
      }
    }
    showFeedback(`Alert ${alertId} marked as RESOLVED.`);
  };

  const handleViewReport = () => {
    onSelectAlertOrIncident({ alert: activeAlert, incident: activeIncident });
    onOpenModal();
  };

  return (
    <div className="bg-gradient-to-r from-red-950/80 via-[#120a0a] to-[#0a0a0a] border-2 border-red-500/70 rounded-xl p-5 text-white shadow-2xl space-y-4 font-sans animate-fade-in relative overflow-hidden">
      {/* Top Banner Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-red-500/30 pb-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-red-600/30 border border-red-500/50 text-red-400 flex items-center justify-center flex-shrink-0 animate-pulse">
            <AlertTriangle className="w-6 h-6 text-red-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold text-red-400 bg-red-500/20 px-2.5 py-0.5 rounded border border-red-500/40 uppercase flex items-center gap-1">
                🚨 PROMINENT REAL-TIME FRAUD ALERT
              </span>
              <span className="text-xs font-mono font-bold text-white bg-slate-800 px-2.5 py-0.5 rounded border border-white/10">
                {alertId}
              </span>
            </div>
            <h3 className="text-sm font-bold text-white mt-1 flex items-center gap-2">
              <span>Suspicious Activity Flagged for {customerName}</span>
              <span className="text-xs text-slate-400 font-mono font-normal">({customerId})</span>
            </h3>
          </div>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs">
          {/* Notification Badge */}
          <span className="text-[10px] font-bold bg-red-600 text-white px-2.5 py-1 rounded-full animate-bounce shadow-md">
            🔔 1 CRITICAL REAL-TIME ALERT
          </span>

          {/* Severity Badge */}
          <span className="text-[10px] font-bold px-2.5 py-1 rounded bg-red-500/20 text-red-400 border border-red-500/40 uppercase">
            SEVERITY: {severity}
          </span>

          {/* Risk Score Badge */}
          <span className="text-[10px] font-bold px-2.5 py-1 rounded bg-orange-500/20 text-orange-400 border border-orange-500/40 uppercase">
            RISK SCORE: {riskScore}/100
          </span>

          {/* Status Badge */}
          <span className="text-[10px] font-bold px-2.5 py-1 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 uppercase">
            STATUS: {currentStatus}
          </span>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {actionFeedback && (
        <div className="bg-emerald-950/90 border border-emerald-500/60 p-2.5 rounded-lg text-xs font-mono text-emerald-200 flex items-center justify-between animate-fade-in">
          <span className="flex items-center gap-1.5 font-bold">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> {actionFeedback}
          </span>
          <button onClick={() => setActionFeedback(null)} className="text-slate-400 hover:text-white text-[10px] uppercase">
            Dismiss
          </button>
        </div>
      )}

      {isExpanded && (
        <>
          {/* Transaction & Alert Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
            <div className="bg-[#0c0c0c] p-3 rounded-lg border border-white/10 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Merchant & Amount</span>
              <p className="text-sm font-bold text-white truncate">{merchant}</p>
              <p className="text-orange-400 font-bold">{amount}</p>
            </div>

            <div className="bg-[#0c0c0c] p-3 rounded-lg border border-white/10 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Date, Time & Location</span>
              <p className="text-slate-200 text-xs truncate">{timestamp}</p>
              <p className="text-slate-400 text-[11px] truncate">{location}</p>
            </div>

            <div className="bg-[#0c0c0c] p-3 rounded-lg border border-white/10 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Fraud Category</span>
              <p className="text-red-400 font-bold text-xs truncate">{category}</p>
              <p className="text-slate-400 text-[10px]">Assigned: {assignedAnalyst}</p>
            </div>

            <div className="bg-[#0c0c0c] p-3 rounded-lg border border-white/10 space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">AI Fraud Summary</span>
              <p className="text-slate-300 font-sans text-[11px] line-clamp-2 leading-tight">
                {summaryText}
              </p>
            </div>
          </div>

          {/* Analyst Action Buttons Row */}
          <div className="pt-2 border-t border-white/10 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold uppercase text-slate-400">
                Analyst Immediate Control & Escalation Buttons
              </span>
              <span className="text-[10px] font-mono text-slate-500">Analyst Ops Panel</span>
            </div>

            <div className="flex flex-wrap gap-2 text-xs font-mono font-bold">
              {/* 1. View Investigation Report */}
              <button
                type="button"
                onClick={handleViewReport}
                className="bg-orange-600 hover:bg-orange-500 text-white px-3 py-2 rounded-lg border border-orange-400/40 flex items-center gap-1.5 shadow-lg transition-all"
              >
                <Eye className="w-4 h-4" />
                <span>View Investigation Report</span>
              </button>

              {/* 2. Assign to Analyst */}
              <button
                type="button"
                onClick={handleAssignToAnalyst}
                className="bg-[#1f1f1f] hover:bg-[#2a2a2a] text-slate-200 px-3 py-2 rounded-lg border border-white/10 flex items-center gap-1.5 transition-all"
              >
                <UserCheck className="w-4 h-4 text-blue-400" />
                <span>Assign to Analyst</span>
              </button>

              {/* 3. Start Investigation */}
              <button
                type="button"
                onClick={handleStartInvestigation}
                className="bg-[#1f1f1f] hover:bg-[#2a2a2a] text-slate-200 px-3 py-2 rounded-lg border border-white/10 flex items-center gap-1.5 transition-all"
              >
                <Clock className="w-4 h-4 text-amber-400" />
                <span>Start Investigation</span>
              </button>

              {/* 4. Escalate Case */}
              <button
                type="button"
                onClick={handleEscalateCase}
                className="bg-red-950 hover:bg-red-900 text-red-200 px-3 py-2 rounded-lg border border-red-500/50 flex items-center gap-1.5 transition-all"
              >
                <AlertOctagon className="w-4 h-4 text-red-400" />
                <span>Escalate Case</span>
              </button>

              {/* 5. Block Card */}
              <button
                type="button"
                onClick={handleBlockCard}
                className="bg-red-950 hover:bg-red-900 text-red-200 px-3 py-2 rounded-lg border border-red-500/50 flex items-center gap-1.5 transition-all"
              >
                <Lock className="w-4 h-4 text-red-400" />
                <span>Block Card</span>
              </button>

              {/* 6. Freeze Account */}
              <button
                type="button"
                onClick={handleFreezeAccount}
                className="bg-[#1f1f1f] hover:bg-[#2a2a2a] text-slate-200 px-3 py-2 rounded-lg border border-white/10 flex items-center gap-1.5 transition-all"
              >
                <ShieldX className="w-4 h-4 text-orange-400" />
                <span>Freeze Account</span>
              </button>

              {/* 7. Contact Customer */}
              <button
                type="button"
                onClick={handleContactCustomer}
                className="bg-[#1f1f1f] hover:bg-[#2a2a2a] text-slate-200 px-3 py-2 rounded-lg border border-white/10 flex items-center gap-1.5 transition-all"
              >
                <PhoneCall className="w-4 h-4 text-sky-400" />
                <span>Contact Customer</span>
              </button>

              {/* 8. Mark as False Positive */}
              <button
                type="button"
                onClick={handleMarkFalsePositive}
                className="bg-emerald-950 hover:bg-emerald-900 text-emerald-300 px-3 py-2 rounded-lg border border-emerald-500/50 flex items-center gap-1.5 transition-all"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Mark as False Positive</span>
              </button>

              {/* 9. Resolve Alert */}
              <button
                type="button"
                onClick={handleResolveAlert}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2 rounded-lg border border-emerald-400/40 flex items-center gap-1.5 transition-all"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Resolve Alert</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
