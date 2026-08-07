import React, { useState, useMemo } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Search,
  Filter,
  CheckCircle2,
  Lock,
  Clock,
  ChevronRight,
  ShieldCheck,
  CreditCard,
  FileText,
  Activity,
  Sparkles,
  RefreshCw,
  XCircle,
  Calendar,
  DollarSign,
  MapPin,
  SlidersHorizontal,
  PhoneCall,
  ChevronDown,
  ChevronUp,
  RefreshCcw,
  Check,
  UserCheck,
  ShieldX
} from 'lucide-react';
import { FraudAlert, SecurityIncident, Transaction } from '../types';

interface FraudAlertCenterProps {
  alerts: FraudAlert[];
  incidents?: SecurityIncident[];
  transactions?: Transaction[];
  initialSearchQuery?: string;
  onConfirmAuthorized: (alertId: string) => Promise<void>;
  onConfirmUnauthorized: (alertId: string, actionType: 'freeze' | 'report') => Promise<void>;
  onRefreshAlerts?: () => void;
  onOpenChatWithQuery?: (queryText: string) => void;
  onReportFraudTransaction?: (txnId: string) => void;
}

export const FraudAlertCenter: React.FC<FraudAlertCenterProps> = ({
  alerts,
  incidents = [],
  transactions = [],
  initialSearchQuery = '',
  onConfirmAuthorized,
  onConfirmUnauthorized,
  onRefreshAlerts,
  onOpenChatWithQuery,
  onReportFraudTransaction
}) => {
  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery);
  const [dateRange, setDateRange] = useState<'all' | 'today' | '7days' | '30days'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'pending' | 'flagged' | 'reversed'>('all');
  const [amountPreset, setAmountPreset] = useState<'all' | 'under_500' | '500_2000' | 'over_2000' | 'custom'>('all');
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');
  const [merchantFilter, setMerchantFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<'all' | 'low' | 'medium' | 'high' | 'critical'>('all');
  const [cardTypeFilter, setCardTypeFilter] = useState<'all' | 'debit' | 'credit'>('all');

  // UI state
  const [selectedTxnId, setSelectedTxnId] = useState<string | null>(null);
  const [processingAlertId, setProcessingAlertId] = useState<string | null>(null);
  const [authorizedTxnIds, setAuthorizedTxnIds] = useState<string[]>([]);
  const [actionFeedback, setActionFeedback] = useState<{ message: string; type: 'success' | 'danger' | 'info' } | null>(null);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState<boolean>(true);

  // Default synthetic transactions if none passed
  const allTransactions: Transaction[] = useMemo(() => {
    if (transactions && transactions.length > 0) return transactions;
    const now = Date.now();
    return [
      {
        id: 'TXN-10452',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-4832',
        amount: 2499.99,
        currency: 'INR',
        merchantName: 'Luxure Electronics Overseas Ltd',
        merchantCategory: 'Consumer Electronics & Crypto Hardware',
        mcc: '5732',
        location: 'Lagos, Nigeria (IP Geo-Mismatch)',
        timestamp: new Date(now - 12 * 60 * 1000).toISOString(),
        deviceHash: 'DEV-RING-X992',
        ipHash: 'IP-45-133-19-88',
        isUnrecognized: true,
        status: 'flagged'
      },
      {
        id: 'TXN-10451',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-4832',
        amount: 18.50,
        currency: 'INR',
        merchantName: 'Corner Coffee Roasters',
        merchantCategory: 'Dining & Cafes',
        mcc: '5812',
        location: 'Mumbai, India',
        timestamp: new Date(now - 3 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-F89A-PROD',
        ipHash: 'IP-192-168-1-100',
        isUnrecognized: false,
        status: 'completed'
      },
      {
        id: 'TXN-10450',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-4832',
        amount: 42.10,
        currency: 'INR',
        merchantName: 'Metro Transit System',
        merchantCategory: 'Transportation',
        mcc: '4111',
        location: 'Mumbai, India',
        timestamp: new Date(now - 24 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-F89A-PROD',
        ipHash: 'IP-192-168-1-100',
        isUnrecognized: false,
        status: 'completed'
      },
      {
        id: 'TXN-10449',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-4832',
        amount: 1850.00,
        currency: 'INR',
        merchantName: 'Reliance Fresh Supermarket',
        merchantCategory: 'Groceries',
        mcc: '5411',
        location: 'Mumbai, India',
        timestamp: new Date(now - 2 * 24 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-F89A-PROD',
        ipHash: 'IP-192-168-1-100',
        isUnrecognized: false,
        status: 'completed'
      },
      {
        id: 'TXN-10448',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-9182',
        amount: 480.00,
        currency: 'INR',
        merchantName: 'Zomato Gourmet Food',
        merchantCategory: 'Dining',
        mcc: '5812',
        location: 'Mumbai, India',
        timestamp: new Date(now - 3 * 24 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-F89A-PROD',
        ipHash: 'IP-192-168-1-100',
        isUnrecognized: false,
        status: 'completed'
      },
      {
        id: 'TXN-10447',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-9182',
        amount: 1299.00,
        currency: 'INR',
        merchantName: 'Apex Digital Gaming Outlet',
        merchantCategory: 'Digital Media & Software',
        mcc: '5816',
        location: 'Bucharest, Romania',
        timestamp: new Date(now - 4 * 24 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-UNKNOWN-88',
        ipHash: 'IP-91-200-11-05',
        isUnrecognized: true,
        status: 'pending'
      },
      {
        id: 'TXN-10446',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-4832',
        amount: 3499.00,
        currency: 'INR',
        merchantName: 'Amazon India Online Store',
        merchantCategory: 'E-Commerce',
        mcc: '5311',
        location: 'Mumbai, India',
        timestamp: new Date(now - 5 * 24 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-F89A-PROD',
        ipHash: 'IP-192-168-1-100',
        isUnrecognized: false,
        status: 'completed'
      },
      {
        id: 'TXN-10445',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-4832',
        amount: 2100.00,
        currency: 'INR',
        merchantName: 'Shell Fuel Outlet',
        merchantCategory: 'Automotive & Gas',
        mcc: '5541',
        location: 'Pune, India',
        timestamp: new Date(now - 6 * 24 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-F89A-PROD',
        ipHash: 'IP-192-168-1-100',
        isUnrecognized: false,
        status: 'completed'
      },
      {
        id: 'TXN-10444',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-9182',
        amount: 5800.00,
        currency: 'INR',
        merchantName: 'Taj Hotels & Luxury Dining',
        merchantCategory: 'Hospitality',
        mcc: '7011',
        location: 'Mumbai, India',
        timestamp: new Date(now - 8 * 24 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-F89A-PROD',
        ipHash: 'IP-192-168-1-100',
        isUnrecognized: false,
        status: 'completed'
      },
      {
        id: 'TXN-10443',
        accountId: 'ACC-8801',
        customerId: 'CUST-1001',
        cardId: 'CARD-9182',
        amount: 8500.00,
        currency: 'INR',
        merchantName: 'QuickPay Overseas Remittance',
        merchantCategory: 'Financial Services',
        mcc: '6012',
        location: 'London, UK',
        timestamp: new Date(now - 12 * 24 * 3600 * 1000).toISOString(),
        deviceHash: 'DEV-RING-X992',
        ipHash: 'IP-45-133-19-88',
        isUnrecognized: true,
        status: 'reversed'
      }
    ];
  }, [transactions]);

  // Unique list of merchants for dropdown
  const merchantOptions = useMemo(() => {
    const set = new Set<string>();
    allTransactions.forEach(t => set.add(t.merchantName));
    return Array.from(set);
  }, [allTransactions]);

  // Helper function to resolve Risk Score & Details for any transaction
  const getTxnRiskInfo = (txn: Transaction) => {
    // Check if an explicit alert exists in `alerts`
    const matchingAlert = alerts.find(
      a => a.transactionId === txn.id || (a.merchantName === txn.merchantName && Math.abs(a.amount - txn.amount) < 0.01)
    );

    const isExplicitlyAuthorized =
      authorizedTxnIds.includes(txn.id) ||
      (matchingAlert && (matchingAlert.status === 'rejected_safe' || matchingAlert.status === 'resolved')) ||
      (txn.status === 'completed' && !txn.isUnrecognized && !matchingAlert);

    if (isExplicitlyAuthorized) {
      return {
        score: 0,
        level: 'low' as const,
        reasons: [
          'Verified & Authorized: Customer Priya Sharma explicitly confirmed this charge as legitimate.',
          'Sentinel Surveillance Status: Fraud alert dismissed; transaction marked safe.'
        ],
        alertId: matchingAlert?.alertId,
        alertStatus: 'rejected_safe' as const,
        humanReview: false,
        isAuthorized: true
      };
    }

    if (matchingAlert) {
      return {
        score: matchingAlert.riskScore,
        level: matchingAlert.priority as 'critical' | 'high' | 'medium' | 'low',
        reasons: matchingAlert.reasons,
        alertId: matchingAlert.alertId,
        alertStatus: matchingAlert.status,
        humanReview: matchingAlert.humanApprovalRequired,
        isAuthorized: false
      };
    }

    if (txn.status === 'flagged' || txn.isUnrecognized) {
      return {
        score: 94,
        level: 'critical' as const,
        reasons: [
          'Unrecognized device hash (DEV-RING-X992)',
          'IP Geo-mismatch: Lagos, Nigeria vs Billing Mumbai',
          'Amount is 55.5x customer historical average'
        ],
        alertId: 'ALT-9921',
        alertStatus: 'open' as const,
        humanReview: true,
        isAuthorized: false
      };
    }

    if (txn.status === 'pending') {
      return {
        score: 65,
        level: 'high' as const,
        reasons: ['Foreign merchant IP address', 'High risk merchant category (Gaming Outlet)'],
        alertId: undefined,
        alertStatus: undefined,
        humanReview: false,
        isAuthorized: false
      };
    }

    if (txn.status === 'reversed') {
      return {
        score: 78,
        level: 'high' as const,
        reasons: ['Overseas remittance flagged by AML rules', 'Automatic payment reversal initiated'],
        alertId: undefined,
        alertStatus: undefined,
        humanReview: true,
        isAuthorized: false
      };
    }

    if (txn.amount > 5000) {
      return {
        score: 35,
        level: 'medium' as const,
        reasons: ['Elevated amount transaction', 'Standard post-auth verification clear'],
        alertId: undefined,
        alertStatus: undefined,
        humanReview: false,
        isAuthorized: false
      };
    }

    return {
      score: 12,
      level: 'low' as const,
      reasons: ['Chip-and-PIN authenticated transaction', 'Verified trusted customer device'],
      alertId: undefined,
      alertStatus: undefined,
      humanReview: false,
      isAuthorized: false
    };
  };

  // Filter transactions
  const filteredTransactions = useMemo(() => {
    const searchLower = searchQuery.trim().toLowerCase();
    const now = Date.now();

    return allTransactions.filter(txn => {
      const riskInfo = getTxnRiskInfo(txn);

      // 1. Search Query
      if (searchLower) {
        const matchesSearch =
          txn.id.toLowerCase().includes(searchLower) ||
          txn.merchantName.toLowerCase().includes(searchLower) ||
          txn.merchantCategory.toLowerCase().includes(searchLower) ||
          txn.mcc.includes(searchLower) ||
          txn.location.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      // 2. Date Range
      const txnTime = new Date(txn.timestamp).getTime();
      if (dateRange === 'today') {
        if (now - txnTime > 24 * 3600 * 1000) return false;
      } else if (dateRange === '7days') {
        if (now - txnTime > 7 * 24 * 3600 * 1000) return false;
      } else if (dateRange === '30days') {
        if (now - txnTime > 30 * 24 * 3600 * 1000) return false;
      }

      // 3. Status Filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'completed' && txn.status !== 'completed') return false;
        if (statusFilter === 'pending' && txn.status !== 'pending') return false;
        if (statusFilter === 'flagged' && txn.status !== 'flagged') return false;
        if (statusFilter === 'reversed' && txn.status !== 'reversed') return false;
      }

      // 4. Amount Filter
      if (amountPreset === 'under_500' && txn.amount >= 500) return false;
      if (amountPreset === '500_2000' && (txn.amount < 500 || txn.amount > 2000)) return false;
      if (amountPreset === 'over_2000' && txn.amount <= 2000) return false;
      if (amountPreset === 'custom') {
        if (minAmount && txn.amount < parseFloat(minAmount)) return false;
        if (maxAmount && txn.amount > parseFloat(maxAmount)) return false;
      }

      // 5. Merchant Filter
      if (merchantFilter !== 'all' && txn.merchantName !== merchantFilter) return false;

      // 6. Fraud Risk Filter
      if (riskFilter === 'low' && riskInfo.score >= 20) return false;
      if (riskFilter === 'medium' && (riskInfo.score < 20 || riskInfo.score >= 50)) return false;
      if (riskFilter === 'high' && (riskInfo.score < 50 || riskInfo.score >= 80)) return false;
      if (riskFilter === 'critical' && riskInfo.score < 80) return false;

      // 7. Debit / Credit Card Filter
      const isCredit = txn.cardId?.includes('9182') || txn.cardId?.includes('credit');
      if (cardTypeFilter === 'debit' && isCredit) return false;
      if (cardTypeFilter === 'credit' && !isCredit) return false;

      return true;
    });
  }, [
    allTransactions,
    searchQuery,
    dateRange,
    statusFilter,
    amountPreset,
    minAmount,
    maxAmount,
    merchantFilter,
    riskFilter,
    cardTypeFilter,
    alerts
  ]);

  // Display top 10 most recent transactions
  const top10Transactions = useMemo(() => {
    return [...filteredTransactions]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 10);
  }, [filteredTransactions]);

  // Active selected transaction
  const activeTxn = useMemo(() => {
    if (selectedTxnId) {
      return allTransactions.find(t => t.id === selectedTxnId) || top10Transactions[0];
    }
    return top10Transactions[0] || allTransactions[0];
  }, [selectedTxnId, top10Transactions, allTransactions]);

  const activeTxnRisk = activeTxn ? getTxnRiskInfo(activeTxn) : null;

  // Actions
  const handleConfirmTxn = async (txn: Transaction) => {
    const riskInfo = getTxnRiskInfo(txn);
    setProcessingAlertId(txn.id);
    setAuthorizedTxnIds(prev => Array.from(new Set([...prev, txn.id])));
    try {
      await fetch(`/api/transactions/${txn.id}/confirm-authorized`, { method: 'POST' });
      if (riskInfo.alertId) {
        await onConfirmAuthorized(riskInfo.alertId);
      }
      setActionFeedback({
        message: `✅ Transaction ${txn.id} at ${txn.merchantName} verified as authorized by Priya Sharma. It is no longer flagged or considered fraud.`,
        type: 'success'
      });
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingAlertId(null);
      if (onRefreshAlerts) onRefreshAlerts();
    }
  };

  const handleBlockCard = async (txn: Transaction) => {
    const riskInfo = getTxnRiskInfo(txn);
    setProcessingAlertId(txn.id);
    try {
      if (riskInfo.alertId) {
        await onConfirmUnauthorized(riskInfo.alertId, 'freeze');
      } else {
        await fetch('/api/cards/CARD-4832/freeze', { method: 'POST' });
      }
      setActionFeedback({
        message: `🚫 Card associated with ${txn.id} blocked immediately. Temporary account freeze applied.`,
        type: 'danger'
      });
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingAlertId(null);
      if (onRefreshAlerts) onRefreshAlerts();
    }
  };

  const handleReportFraud = async (txn: Transaction) => {
    const riskInfo = getTxnRiskInfo(txn);
    setProcessingAlertId(txn.id);
    try {
      if (riskInfo.alertId) {
        await onConfirmUnauthorized(riskInfo.alertId, 'report');
      }
      if (onReportFraudTransaction) {
        onReportFraudTransaction(txn.id);
      }
      setActionFeedback({
        message: `🚨 Fraud dispute initiated for ₹${txn.amount.toLocaleString('en-IN')} at ${txn.merchantName}. Multi-Agent AI Workflow dispatched case CASE-REG-9182 under Reg E Zero Liability.`,
        type: 'danger'
      });
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingAlertId(null);
      if (onRefreshAlerts) onRefreshAlerts();
    }
  };

  const handleFreezeOnlineBanking = async () => {
    try {
      await fetch('/api/cards/CARD-4832/freeze', { method: 'POST' });
      setActionFeedback({
        message: '🔒 Online Banking & All Digital Payment Cards frozen for customer Priya Sharma.',
        type: 'danger'
      });
    } catch (e) {
      console.error(e);
    }
  };

  const resetFilters = () => {
    setSearchQuery('');
    setDateRange('all');
    setStatusFilter('all');
    setAmountPreset('all');
    setMinAmount('');
    setMaxAmount('');
    setMerchantFilter('all');
    setRiskFilter('all');
    setCardTypeFilter('all');
  };

  const activeFiltersCount =
    (searchQuery ? 1 : 0) +
    (dateRange !== 'all' ? 1 : 0) +
    (statusFilter !== 'all' ? 1 : 0) +
    (amountPreset !== 'all' ? 1 : 0) +
    (merchantFilter !== 'all' ? 1 : 0) +
    (riskFilter !== 'all' ? 1 : 0) +
    (cardTypeFilter !== 'all' ? 1 : 0);

  const getStatusBadge = (status: Transaction['status'], riskInfo?: { isAuthorized?: boolean }) => {
    if (riskInfo?.isAuthorized) {
      return (
        <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[11px] font-mono px-2.5 py-0.5 rounded-md flex items-center gap-1 font-bold">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Successful / Authorized
        </span>
      );
    }
    switch (status) {
      case 'completed':
        return (
          <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[11px] font-mono px-2.5 py-0.5 rounded-md flex items-center gap-1 font-bold">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Successful
          </span>
        );
      case 'pending':
        return (
          <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[11px] font-mono px-2.5 py-0.5 rounded-md flex items-center gap-1 font-bold">
            <Clock className="w-3 h-3 text-amber-400 animate-spin-slow" /> Pending
          </span>
        );
      case 'flagged':
        return (
          <span className="bg-red-500/10 text-red-400 border border-red-500/30 text-[11px] font-mono px-2.5 py-0.5 rounded-md flex items-center gap-1 font-bold animate-pulse">
            <AlertTriangle className="w-3 h-3 text-red-400" /> Flagged / Suspicious
          </span>
        );
      case 'reversed':
        return (
          <span className="bg-purple-500/10 text-purple-400 border border-purple-500/30 text-[11px] font-mono px-2.5 py-0.5 rounded-md flex items-center gap-1 font-bold">
            <RefreshCcw className="w-3 h-3 text-purple-400" /> Reversed
          </span>
        );
      default:
        return null;
    }
  };

  const getRiskBadge = (score: number) => {
    if (score >= 80) {
      return (
        <span className="bg-red-500/20 text-red-400 border border-red-500/40 text-[10px] font-mono font-bold px-2 py-0.5 rounded">
          CRITICAL ({score}/100)
        </span>
      );
    }
    if (score >= 50) {
      return (
        <span className="bg-orange-500/20 text-orange-400 border border-orange-500/40 text-[10px] font-mono font-bold px-2 py-0.5 rounded">
          HIGH ({score}/100)
        </span>
      );
    }
    if (score >= 20) {
      return (
        <span className="bg-amber-500/20 text-amber-400 border border-amber-500/40 text-[10px] font-mono font-bold px-2 py-0.5 rounded">
          MEDIUM ({score}/100)
        </span>
      );
    }
    return (
      <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-mono font-bold px-2 py-0.5 rounded">
        LOW ({score}/100)
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* 1. Header Banner & Security Status */}
      <div className="bg-[#111111] border border-white/10 rounded-xl p-6 text-white shadow-2xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-orange-600/20 text-orange-500 border border-orange-500/40 flex items-center justify-center shadow-lg">
              <ShieldAlert className="w-6 h-6 text-orange-400 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold tracking-tight text-white">Real-Time Fraud Alerts & Recent Transactions</h2>
                <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded flex items-center gap-1">
                  <Activity className="w-3 h-3 text-emerald-400" /> Active Surveillance
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                SentinelBank AI Surveillance • Customer Priya Sharma (CUST-1001)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="bg-[#080808] px-3.5 py-2 rounded-lg border border-white/10 text-center">
              <span className="text-[10px] text-slate-500 uppercase font-bold block">Critical Flags</span>
              <span className="text-red-400 font-bold text-sm">1 Active Alert</span>
            </div>
            <div className="bg-[#080808] px-3.5 py-2 rounded-lg border border-white/10 text-center">
              <span className="text-[10px] text-slate-500 uppercase font-bold block">Recent Transactions</span>
              <span className="text-white font-bold text-sm">{top10Transactions.length} Displayed</span>
            </div>
            {onRefreshAlerts && (
              <button
                onClick={onRefreshAlerts}
                className="bg-[#1f1f1f] hover:bg-[#2a2a2a] text-slate-200 border border-white/10 p-2.5 rounded-lg transition-all"
                title="Refresh Real-Time Data"
              >
                <RefreshCw className="w-4 h-4 text-orange-400" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 2. Action Feedback Notification Banner */}
      {actionFeedback && (
        <div
          className={`p-4 rounded-xl border text-xs font-mono font-medium flex items-center justify-between shadow-xl animate-fade-in ${
            actionFeedback.type === 'danger'
              ? 'bg-red-950/80 text-red-200 border-red-500/50'
              : actionFeedback.type === 'success'
              ? 'bg-emerald-950/80 text-emerald-200 border-emerald-500/50'
              : 'bg-blue-950/80 text-blue-200 border-blue-500/50'
          }`}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-orange-400 flex-shrink-0" />
            <span>{actionFeedback.message}</span>
          </div>
          <button
            onClick={() => setActionFeedback(null)}
            className="text-slate-400 hover:text-white ml-3 text-xs uppercase underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 3. Powerful Filter & Search Controls Section */}
      <div className="bg-[#111111] border border-white/10 rounded-xl p-5 text-white shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-orange-400" />
            <h3 className="text-xs uppercase font-mono font-bold tracking-wider text-slate-200">
              Transaction Search & Multi-Criteria Filter Controls
            </h3>
            {activeFiltersCount > 0 && (
              <span className="bg-orange-500/20 text-orange-400 border border-orange-500/30 text-[10px] font-mono px-2 py-0.5 rounded-full font-bold">
                {activeFiltersCount} Active Filters
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            {activeFiltersCount > 0 && (
              <button
                onClick={resetFilters}
                className="text-orange-400 hover:text-orange-300 underline text-[11px] font-bold"
              >
                Clear All Filters
              </button>
            )}
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="bg-[#1a1a1a] hover:bg-[#262626] text-slate-300 px-3 py-1.5 rounded-lg border border-white/10 flex items-center gap-1.5 text-xs transition-all"
            >
              <span>{showAdvancedFilters ? 'Hide Advanced Filters' : 'Show Advanced Filters'}</span>
              {showAdvancedFilters ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Primary Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search transactions by Merchant Name, Transaction ID (e.g. TXN-10452), MCC code, or Location..."
            className="w-full bg-[#080808] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 transition-all font-mono"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-2.5 text-slate-400 hover:text-white text-xs font-mono"
            >
              Clear
            </button>
          )}
        </div>

        {/* Filter Dropdowns Grid */}
        {showAdvancedFilters && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 font-mono text-xs pt-1">
            {/* 1. Date Range */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
                <Calendar className="w-3 h-3 text-orange-400" /> Date Range
              </label>
              <select
                value={dateRange}
                onChange={e => setDateRange(e.target.value as any)}
                className="w-full bg-[#080808] border border-white/10 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-orange-500"
              >
                <option value="all">All Dates</option>
                <option value="today">Today (Last 24h)</option>
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
              </select>
            </div>

            {/* 2. Transaction Status */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-orange-400" /> Status
              </label>
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value as any)}
                className="w-full bg-[#080808] border border-white/10 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-orange-500"
              >
                <option value="all">All Statuses</option>
                <option value="completed">Successful / Completed</option>
                <option value="pending">Pending</option>
                <option value="flagged">Failed / Flagged</option>
                <option value="reversed">Reversed</option>
              </select>
            </div>

            {/* 3. Amount Range */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
                <DollarSign className="w-3 h-3 text-orange-400" /> Amount Range
              </label>
              <select
                value={amountPreset}
                onChange={e => setAmountPreset(e.target.value as any)}
                className="w-full bg-[#080808] border border-white/10 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-orange-500"
              >
                <option value="all">All Amounts</option>
                <option value="under_500">Under ₹500</option>
                <option value="500_2000">₹500 – ₹2,000</option>
                <option value="over_2000">Over ₹2,000</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>

            {/* 4. Merchant Name */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
                <FileText className="w-3 h-3 text-orange-400" /> Merchant
              </label>
              <select
                value={merchantFilter}
                onChange={e => setMerchantFilter(e.target.value)}
                className="w-full bg-[#080808] border border-white/10 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-orange-500 truncate"
              >
                <option value="all">All Merchants</option>
                {merchantOptions.map((m, i) => (
                  <option key={i} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            {/* 5. Fraud Risk */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-orange-400" /> Fraud Risk
              </label>
              <select
                value={riskFilter}
                onChange={e => setRiskFilter(e.target.value as any)}
                className="w-full bg-[#080808] border border-white/10 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-orange-500"
              >
                <option value="all">All Risk Levels</option>
                <option value="critical">Critical Risk (&gt;80)</option>
                <option value="high">High Risk (50–80)</option>
                <option value="medium">Medium Risk (20–50)</option>
                <option value="low">Low Risk (&lt;20)</option>
              </select>
            </div>

            {/* 6. Debit / Credit */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
                <CreditCard className="w-3 h-3 text-orange-400" /> Debit / Credit
              </label>
              <select
                value={cardTypeFilter}
                onChange={e => setCardTypeFilter(e.target.value as any)}
                className="w-full bg-[#080808] border border-white/10 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-orange-500"
              >
                <option value="all">All Card Types</option>
                <option value="debit">Debit Card (****-4832)</option>
                <option value="credit">Credit Card (****-9182)</option>
              </select>
            </div>
          </div>
        )}

        {/* Custom Amount Inputs if selected */}
        {amountPreset === 'custom' && (
          <div className="flex items-center gap-3 font-mono text-xs pt-1 border-t border-white/5">
            <span className="text-[11px] text-slate-400">Min Amount (₹):</span>
            <input
              type="number"
              value={minAmount}
              onChange={e => setMinAmount(e.target.value)}
              placeholder="0"
              className="bg-[#080808] border border-white/10 rounded px-2 py-1 text-xs text-white w-28 focus:outline-none focus:border-orange-500"
            />
            <span className="text-[11px] text-slate-400">Max Amount (₹):</span>
            <input
              type="number"
              value={maxAmount}
              onChange={e => setMaxAmount(e.target.value)}
              placeholder="10000"
              className="bg-[#080808] border border-white/10 rounded px-2 py-1 text-xs text-white w-28 focus:outline-none focus:border-orange-500"
            />
          </div>
        )}
      </div>

      {/* 4. Selected Transaction Detail & Fraud Action Panel */}
      {activeTxn && activeTxnRisk && (
        <div className={`bg-[#111111] border-2 ${activeTxnRisk.isAuthorized ? 'border-emerald-500/50' : 'border-orange-500/50'} rounded-xl p-6 text-white shadow-2xl space-y-5 relative overflow-hidden`}>
          {/* Action Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/10 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded ${activeTxnRisk.isAuthorized ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'}`}>
                  {activeTxnRisk.isAuthorized ? 'Verified Authorized Transaction' : 'Selected Transaction Details & AI Action Panel'}
                </span>
                {getStatusBadge(activeTxn.status, activeTxnRisk)}
                {getRiskBadge(activeTxnRisk.score)}
              </div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                {activeTxn.merchantName}
              </h3>
              <p className="text-xs font-mono text-slate-400">
                Transaction Ref: <strong className="text-white">{activeTxn.id}</strong> • MCC: {activeTxn.mcc} ({activeTxn.merchantCategory})
              </p>
            </div>

            <div className="text-left md:text-right space-y-0.5 font-mono">
              <span className="text-2xl font-bold text-white">
                ₹{activeTxn.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} {activeTxn.currency}
              </span>
              <p className="text-[11px] text-slate-400">
                {new Date(activeTxn.timestamp).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
              </p>
            </div>
          </div>

          {/* Transaction Metadata Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            {/* Card Info */}
            <div className="bg-[#080808] p-3.5 rounded-xl border border-white/10 space-y-1.5">
              <span className="text-[10px] text-slate-500 uppercase font-bold block flex items-center gap-1">
                <CreditCard className="w-3.5 h-3.5 text-orange-400" /> Payment Instrument
              </span>
              <p className="text-white font-bold text-sm">
                {activeTxn.cardId?.includes('9182') ? 'Credit Card (****-9182)' : 'Debit Card (****-4832)'}
              </p>
              <p className="text-[11px] text-slate-400">Primary Checking ACC-8801</p>
            </div>

            {/* Device & Location */}
            <div className="bg-[#080808] p-3.5 rounded-xl border border-white/10 space-y-1.5">
              <span className="text-[10px] text-slate-500 uppercase font-bold block flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-orange-400" /> Location & Device
              </span>
              <p className="text-white font-bold text-sm">{activeTxn.location}</p>
              <p className="text-[11px] text-slate-400">Device Hash: {activeTxn.deviceHash}</p>
            </div>

            {/* AI Risk Score Bar */}
            <div className="bg-[#080808] p-3.5 rounded-xl border border-white/10 space-y-1.5 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5 text-orange-400" /> AI Risk Score
                </span>
                <span className={activeTxnRisk.isAuthorized ? "text-emerald-400 font-bold" : "text-orange-400 font-bold"}>
                  {activeTxnRisk.score}/100
                </span>
              </div>
              <div className="w-full h-2 bg-[#1a1a1a] rounded-full overflow-hidden border border-white/10 p-0.5">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    activeTxnRisk.isAuthorized ? 'bg-emerald-400' : (activeTxnRisk.score >= 80 ? 'bg-gradient-to-r from-orange-500 to-red-600' : 'bg-emerald-400')
                  }`}
                  style={{ width: `${activeTxnRisk.score}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-400 flex items-center justify-between">
                <span>Surveillance Status:</span>
                <strong className={activeTxnRisk.isAuthorized ? "text-emerald-400 font-bold" : "text-white"}>
                  {activeTxnRisk.isAuthorized ? 'VERIFIED SAFE & AUTHORIZED' : (activeTxnRisk.humanReview ? 'HUMAN REVIEW REQUIRED' : 'PASS')}
                </strong>
              </p>
            </div>
          </div>

          {/* AI Risk Signals & Multi-Agent Explanation Box */}
          <div className="bg-[#080808] p-4 rounded-xl border border-white/10 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <h4 className={`text-xs uppercase font-mono font-bold flex items-center gap-1.5 ${activeTxnRisk.isAuthorized ? 'text-emerald-400' : 'text-orange-400'}`}>
                <Sparkles className="w-3.5 h-3.5 text-orange-400" /> Multi-Agent AI Fraud Explanation & Signals
              </h4>
              <span className="text-[10px] text-slate-500 font-mono">LangGraph Sentinel Agent</span>
            </div>

            <ul className="space-y-1.5 font-sans text-slate-300">
              {activeTxnRisk.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2 bg-[#111111] p-2 rounded border border-white/5">
                  <span className={activeTxnRisk.isAuthorized ? "text-emerald-400 font-mono font-bold" : "text-orange-500 font-mono font-bold"}>•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>

            <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono text-slate-400 border-t border-white/5">
              <span className="flex items-center gap-1 text-[11px]">
                <FileText className="w-3.5 h-3.5 text-orange-500" />
                Grounded Banking Policy: <strong className="text-slate-200">FRAUD-SOP-001 (Reg E Zero Liability)</strong>
              </span>

              {onOpenChatWithQuery && (
                <button
                  onClick={() =>
                    onOpenChatWithQuery(
                      `Explain why transaction ${activeTxn.id} of ₹${activeTxn.amount} at ${activeTxn.merchantName} was processed`
                    )
                  }
                  className="text-[11px] text-orange-400 hover:text-orange-300 underline flex items-center gap-1"
                >
                  Ask AI Concierge About This Charge <ChevronRight className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* Complete Fraud Action Panel */}
          <div className="pt-2 space-y-3">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
              Customer Immediate Action Panel
            </span>

            {activeTxnRisk.isAuthorized ? (
              <div className="bg-emerald-950/40 border border-emerald-500/40 p-4 rounded-xl flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 flex-shrink-0">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-emerald-300">Transaction Confirmed as Authorized</h4>
                    <p className="text-xs text-slate-300 font-mono mt-0.5">
                      You confirmed this transaction of ₹{activeTxn.amount.toLocaleString('en-IN')} at {activeTxn.merchantName} as legitimate. It is no longer flagged or considered fraud.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setAuthorizedTxnIds(prev => prev.filter(id => id !== activeTxn.id))}
                  className="text-xs font-mono text-slate-400 hover:text-slate-200 underline whitespace-nowrap bg-white/5 px-3 py-1.5 rounded border border-white/10"
                >
                  Re-flag as Suspicious
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
                {/* Option 1: Confirm Authorized */}
                <button
                  onClick={() => handleConfirmTxn(activeTxn)}
                  disabled={processingAlertId === activeTxn.id}
                  className="bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-500/40 font-semibold text-xs py-3 px-3 rounded-lg transition-all flex flex-col items-center justify-center text-center gap-1 disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>✅ Confirm Authorized</span>
                  <span className="text-[9px] text-emerald-400/80 font-normal">I made this charge</span>
                </button>

                {/* Option 2: Block Card */}
                <button
                  onClick={() => handleBlockCard(activeTxn)}
                  disabled={processingAlertId === activeTxn.id}
                  className="bg-red-950/80 hover:bg-red-900/80 text-red-200 border border-red-500/50 font-semibold text-xs py-3 px-3 rounded-lg transition-all flex flex-col items-center justify-center text-center gap-1 disabled:opacity-50"
                >
                  <Lock className="w-4 h-4 text-red-400" />
                  <span>🚫 Block Card</span>
                  <span className="text-[9px] text-red-300/80 font-normal">Block physical / virtual card</span>
                </button>

                {/* Option 3: Report Fraud */}
                <button
                  onClick={() => handleReportFraud(activeTxn)}
                  disabled={processingAlertId === activeTxn.id}
                  className="bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs py-3 px-3 rounded-lg transition-all flex flex-col items-center justify-center text-center gap-1 shadow-lg border border-orange-400/40 disabled:opacity-50"
                >
                  <AlertTriangle className="w-4 h-4 text-white" />
                  <span>🚨 Report Fraud</span>
                  <span className="text-[9px] text-orange-100 font-normal">Open AI dispute case</span>
                </button>

                {/* Option 4: Freeze Online Banking */}
                <button
                  onClick={handleFreezeOnlineBanking}
                  disabled={processingAlertId === activeTxn.id}
                  className="bg-[#1f1f1f] hover:bg-[#2a2a2a] text-slate-200 border border-white/10 font-semibold text-xs py-3 px-3 rounded-lg transition-all flex flex-col items-center justify-center text-center gap-1 disabled:opacity-50"
                >
                  <ShieldX className="w-4 h-4 text-orange-400" />
                  <span>🔒 Freeze Account</span>
                  <span className="text-[9px] text-slate-400 font-normal">Pause all transactions</span>
                </button>

                {/* Option 5: Contact Support */}
                <button
                  onClick={() =>
                    onOpenChatWithQuery &&
                    onOpenChatWithQuery(
                      `I need support connecting with a human analyst regarding transaction ${activeTxn.id}`
                    )
                  }
                  className="bg-[#1f1f1f] hover:bg-[#2a2a2a] text-slate-200 border border-white/10 font-semibold text-xs py-3 px-3 rounded-lg transition-all flex flex-col items-center justify-center text-center gap-1"
                >
                  <PhoneCall className="w-4 h-4 text-sky-400" />
                  <span>📞 Contact Support</span>
                  <span className="text-[9px] text-slate-400 font-normal">Speak with AI Concierge</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. Clean 10 Most Recent Transactions List (Banking Table / Cards UI) */}
      <div className="bg-[#111111] border border-white/10 rounded-xl p-6 text-white shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-orange-500" /> 10 Most Recent Transactions
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Click any transaction below to view details and open the Fraud Action Panel.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Showing <strong className="text-white">{top10Transactions.length}</strong> of {filteredTransactions.length} matching records
          </span>
        </div>

        {top10Transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-[10px] font-mono text-slate-400 uppercase tracking-wider bg-[#080808]">
                  <th className="py-3 px-4">Merchant & Category</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Card Used</th>
                  <th className="py-3 px-4">Location</th>
                  <th className="py-3 px-4">Risk Level</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-xs">
                {top10Transactions.map(txn => {
                  const riskInfo = getTxnRiskInfo(txn);
                  const isSelected = activeTxn?.id === txn.id;
                  const isCredit = txn.cardId?.includes('9182') || txn.cardId?.includes('credit');

                  return (
                    <tr
                      key={txn.id}
                      onClick={() => setSelectedTxnId(txn.id)}
                      className={`cursor-pointer transition-all hover:bg-orange-500/10 ${
                        isSelected ? 'bg-orange-500/15 border-l-4 border-l-orange-500' : 'bg-[#0d0d0d]'
                      }`}
                    >
                      {/* Merchant Name & Category */}
                      <td className="py-3.5 px-4">
                        <div className="space-y-0.5">
                          <p className="font-bold text-white flex items-center gap-1.5 font-sans text-xs">
                            {txn.merchantName}
                          </p>
                          <p className="text-[10px] text-slate-400 font-mono">
                            Ref: {txn.id} • {txn.merchantCategory}
                          </p>
                        </div>
                      </td>

                      {/* Amount */}
                      <td className="py-3.5 px-4 font-bold text-white">
                        ₹{txn.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>

                      {/* Date & Time */}
                      <td className="py-3.5 px-4 text-slate-300 text-[11px]">
                        {new Date(txn.timestamp).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4">{getStatusBadge(txn.status, riskInfo)}</td>

                      {/* Card Used */}
                      <td className="py-3.5 px-4 text-slate-300 text-[11px]">
                        {isCredit ? 'Credit ****-9182' : 'Debit ****-4832'}
                      </td>

                      {/* Location */}
                      <td className="py-3.5 px-4 text-slate-300 text-[11px] truncate max-w-[150px]">
                        {txn.location}
                      </td>

                      {/* Risk Level */}
                      <td className="py-3.5 px-4">{getRiskBadge(riskInfo.score)}</td>

                      {/* Action */}
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            setSelectedTxnId(txn.id);
                          }}
                          className={`text-[11px] font-bold px-2.5 py-1 rounded transition-all flex items-center gap-1 ml-auto ${
                            isSelected
                              ? 'bg-orange-500 text-white'
                              : 'bg-[#1a1a1a] text-slate-300 hover:text-white hover:bg-[#2a2a2a] border border-white/10'
                          }`}
                        >
                          <span>{isSelected ? 'Viewing' : 'Details'}</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-[#080808] border border-white/10 rounded-xl p-12 text-center text-white shadow-md space-y-3">
            <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mx-auto text-slate-400 border border-white/10">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-base font-semibold text-white">No Matching Transactions Found</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto font-sans">
              No recent transactions matched your active filter criteria. Try adjusting your Date Range, Merchant Name, Amount Range, or Status filters.
            </p>
            <button
              onClick={resetFilters}
              className="bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs px-4 py-2 rounded-lg transition-all font-mono"
            >
              Reset All Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
