import React, { useState } from 'react';
import { ShieldCheck, AlertOctagon, CheckCircle2, Lock, X } from 'lucide-react';
import { FraudAlert } from '../types';

interface FraudInvestigationModalProps {
  alert: FraudAlert;
  isOpen: boolean;
  onClose: () => void;
  onConfirmFreeze: (analystName: string, reason: string) => void;
}

export const FraudInvestigationModal: React.FC<FraudInvestigationModalProps> = ({
  alert,
  isOpen,
  onClose,
  onConfirmFreeze
}) => {
  const [analystName, setAnalystName] = useState('Analyst Sarah Jenkins');
  const [reason, setReason] = useState('Confirmed fraudulent activity. Unauthorized high-amount charge from suspicious IP cluster.');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    setSubmitting(true);
    await onConfirmFreeze(analystName, reason);
    setSubmitting(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#111111] border border-white/10 rounded-xl max-w-lg w-full p-6 text-white shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-red-500/20 text-red-500 rounded border border-red-500/30">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-light text-white">Human Approval: Temporary Card Freeze</h3>
              <p className="text-xs text-slate-400 font-mono">SOP Compliance Requirement • Banking SOP FRAUD-SOP-001</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Alert Details Summary */}
        <div className="bg-[#080808] p-4 rounded border border-white/10 space-y-2 font-mono">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Target Customer:</span>
            <span className="font-semibold text-white">{alert.customerName} ({alert.customerId})</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Transaction:</span>
            <span className="font-semibold text-red-500">₹{alert.amount.toFixed(2)} @ {alert.merchantName}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Risk Score:</span>
            <span className="font-mono font-bold text-red-500">{alert.riskScore}/100 (CRITICAL)</span>
          </div>
        </div>

        {/* Analyst Inputs */}
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 font-mono uppercase">Analyst Identity Signature</label>
            <input
              type="text"
              value={analystName}
              onChange={(e) => setAnalystName(e.target.value)}
              className="w-full bg-[#080808] text-white text-xs px-3 py-2 rounded border border-white/10 focus:outline-none focus:border-orange-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 font-mono uppercase">Freeze Action Justification Notes</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="w-full bg-[#080808] text-white text-xs px-3 py-2 rounded border border-white/10 focus:outline-none focus:border-orange-500 font-mono"
            />
          </div>
        </div>

        <div className="bg-orange-600/10 border border-orange-500/20 p-3 rounded text-xs text-orange-300 flex items-start gap-2 font-mono">
          <Lock className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            Executing this action will call <strong className="text-white">BankingMCP:freeze_card</strong>, transition Case state, emit an Audit Log event, and notify the customer via SMS.
          </span>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded text-xs font-mono font-medium text-slate-300 bg-[#080808] border border-white/10 hover:text-white transition-colors"
          >
            CANCEL
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-5 py-2 rounded text-xs font-mono font-bold text-white bg-red-600 hover:bg-red-500 shadow-lg shadow-red-600/30 transition-all flex items-center gap-1.5 uppercase"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{submitting ? 'Executing Freeze...' : 'Approve & Freeze Card'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
