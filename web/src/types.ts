export type UserRole = 'customer' | 'analyst' | 'supervisor';

export interface CustomerProfile {
  id: string;
  name: string;
  email: string;
  phone: string;
  ssnMasked: string;
  riskTier: 'low' | 'medium' | 'high';
  accountCreated: string;
  kycStatus: 'verified' | 'pending' | 'flagged';
  travelNoticeActive: boolean;
  travelDestination?: string;
  avgTransactionAmount: number;
}

export interface AccountSummary {
  accountId: string;
  customerId: string;
  accountType: 'checking' | 'savings' | 'credit_card';
  accountNumberMasked: string;
  balance: number;
  currency: string;
  status: 'active' | 'frozen' | 'restricted';
}

export interface CardDetails {
  cardId: string;
  accountId: string;
  customerId: string;
  cardNumberMasked: string;
  cardType: 'debit' | 'credit';
  expiryDate: string;
  status: 'active' | 'frozen' | 'blocked_stolen' | 'pending_approval';
  dailyLimit: number;
  lastUsedTimestamp: string;
}

export interface Transaction {
  id: string;
  accountId: string;
  customerId: string;
  cardId?: string;
  amount: number;
  currency: string;
  merchantName: string;
  merchantCategory: string;
  mcc: string;
  location: string;
  timestamp: string;
  deviceHash: string;
  ipHash: string;
  isUnrecognized?: boolean;
  status: 'completed' | 'pending' | 'flagged' | 'reversed';
  beneficiaryName?: string;
}

export interface DeviceRiskProfile {
  deviceHash: string;
  ipHash: string;
  location: string;
  isNewDevice: boolean;
  knownAssociatedCustomers: string[];
  failedLogins24h: number;
  riskScore: number;
}

export interface FraudEvidence {
  evidenceId: string;
  transactionId: string;
  ruleViolations: string[];
  mlScore: number;
  anomalyScore: number;
  graphScore: number;
  reasons: string[];
  graphClusterInfo?: {
    sharedDeviceCustomers: number;
    sharedIpCustomers: number;
    suspiciousBeneficiaryLinks: boolean;
  };
}

export interface FraudAlert {
  alertId: string;
  transactionId: string;
  customerId: string;
  customerName: string;
  amount: number;
  merchantName: string;
  timestamp: string;
  riskScore: number; // 0 to 100
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'investigating' | 'approved_frozen' | 'rejected_safe' | 'escalated';
  reasons: string[];
  recommendedAction: 'temporary_card_freeze' | 'customer_verification' | 'monitor' | 'none';
  humanApprovalRequired: boolean;
  assignedAnalyst?: string;
  evidence: FraudEvidence;
  caseId?: string;
}

export interface CaseRecord {
  caseId: string;
  customerId: string;
  alertId?: string;
  transactionId?: string;
  title: string;
  description: string;
  status: 'open' | 'pending_approval' | 'approved' | 'resolved' | 'closed';
  priority: 'critical' | 'high' | 'medium' | 'low';
  assignedTo: string;
  createdAt: string;
  updatedAt: string;
  notes: Array<{
    id: string;
    author: string;
    text: string;
    timestamp: string;
  }>;
  approvalRequest?: {
    requestedBy: string;
    actionType: 'card_freeze' | 'account_block' | 'transaction_reversal';
    status: 'pending' | 'approved' | 'rejected';
    reviewedBy?: string;
    timestamp: string;
  };
}

export interface PolicyDocument {
  documentId: string;
  title: string;
  content: string;
  version: string;
  region: string;
  effectiveFrom: string;
  approvedBy: string;
  category: 'dispute' | 'kyc' | 'card_security' | 'faq' | 'compliance';
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  role: string;
  action: string;
  details: string;
  piiMasked: boolean;
  status: 'success' | 'warning' | 'denied';
  mcpServer?: string;
}

export interface AgentTrace {
  stepId: string;
  agentName: string;
  timestamp: string;
  input: string;
  output: string;
  toolsCalled?: string[];
  durationMs: number;
  status: 'completed' | 'routing' | 'approval_paused' | 'error';
}

export type FraudCategory =
  | 'Stolen Card'
  | 'Unauthorized Transaction'
  | 'Phishing / Social Engineering'
  | 'Identity Theft'
  | 'Account Takeover'
  | 'Card Skimming'
  | 'Fake Merchant'
  | 'Friendly Fraud'
  | 'General Banking Inquiry';

export type FraudSeverity = 'Low' | 'Medium' | 'High' | 'Critical';

export interface FraudAssessment {
  isFraud: boolean;
  category: FraudCategory;
  severity: FraudSeverity;
  confidenceScore: number;
  fraudProbability?: string;
  keyIndicators: string[];
  financialRisk: string;
  recommendedActions: string[];
  summaryText: string;
  evidence?: string[];
  suspiciousIndicators?: string[];
  relatedEntities?: {
    merchant?: string;
    location?: string;
    device?: string;
    ip?: string;
  };
  riskScore?: number;
  priority?: 'Critical' | 'High' | 'Medium' | 'Low' | 'critical' | 'high' | 'medium' | 'low';
  humanApprovalRequired?: boolean;
  caseId?: string;
  assignedAnalyst?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  agentName?: string;
  text: string;
  timestamp: string;
  intent?: string;
  confidence?: number;
  sources?: Array<{ docId: string; title: string; version: string }>;
  suggestedActions?: string[];
  transactionContext?: Transaction;
  fraudAlertRef?: string;
  traces?: AgentTrace[];
  piiMaskedText?: string;
  fraudAssessment?: FraudAssessment;
}

export type IncidentStatus = 'New' | 'Under Review' | 'Resolved';

export interface SecurityIncident {
  incidentId: string;
  customerId: string;
  customerName: string;
  fraudCategory: string;
  severity: FraudSeverity;
  actionInitiated: string;
  aiAssessmentSummary: string;
  timestamp: string;
  status: IncidentStatus;
  assignedAnalyst?: string;
  notes?: Array<{
    id: string;
    author: string;
    text: string;
    timestamp: string;
  }>;
  transactionId?: string;
  cardId?: string;
}

export interface GoldenTestCase {
  id: string;
  name: string;
  category: 'intent' | 'pii' | 'prompt_injection' | 'rag' | 'fraud_rules' | 'mcp_perm' | 'human_in_loop';
  input: string;
  expectedResult: string;
  actualResult?: string;
  status?: 'passed' | 'failed' | 'running';
  details?: string;
}
