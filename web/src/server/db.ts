import {
  CustomerProfile,
  AccountSummary,
  CardDetails,
  Transaction,
  FraudAlert,
  CaseRecord,
  PolicyDocument,
  AuditEvent,
  DeviceRiskProfile,
  SecurityIncident,
  IncidentStatus,
  FraudSeverity
} from '../types';

class SyntheticDatabase {
  private customers: Map<string, CustomerProfile> = new Map();
  private accounts: Map<string, AccountSummary> = new Map();
  private cards: Map<string, CardDetails> = new Map();
  private transactions: Map<string, Transaction> = new Map();
  private alerts: Map<string, FraudAlert> = new Map();
  private cases: Map<string, CaseRecord> = new Map();
  private auditEvents: AuditEvent[] = [];
  private devices: Map<string, DeviceRiskProfile> = new Map();
  private policies: Map<string, PolicyDocument> = new Map();
  private incidents: Map<string, SecurityIncident> = new Map();

  constructor() {
    this.seedDatabase();
  }

  public seedDatabase() {
    this.customers.clear();
    this.accounts.clear();
    this.cards.clear();
    this.transactions.clear();
    this.alerts.clear();
    this.cases.clear();
    this.auditEvents = [];
    this.devices.clear();
    this.policies.clear();
    this.incidents.clear();

    // Initial Demo Incident
    const initialInc1: SecurityIncident = {
      incidentId: 'INC-2026-8812',
      customerId: 'CUST-1001',
      customerName: 'Priya Sharma',
      fraudCategory: 'Unauthorized Transaction',
      severity: 'Critical',
      actionInitiated: 'Report Unauthorized Charge & Temporary Card Freeze',
      aiAssessmentSummary: 'Unrecognized transaction of ₹2,499.99 flagged at Luxure Electronics with foreign IP mismatch. Instant mitigation requested.',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      status: 'New',
      assignedAnalyst: 'Unassigned',
      notes: [
        {
          id: 'note-1',
          author: 'Customer Portal',
          text: 'Incident reported by customer via automated AI risk prompt.',
          timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString()
        }
      ],
      transactionId: 'TXN-10452',
      cardId: 'CARD-4832'
    };

    this.incidents.set(initialInc1.incidentId, initialInc1);

    // 1. Primary Demo Customer: Priya Sharma
    const priya: CustomerProfile = {
      id: 'CUST-1001',
      name: 'Priya Sharma',
      email: 'p.sharma@example.com',
      phone: '+91 98765 43210',
      ssnMasked: 'XXX-XX-8492',
      riskTier: 'low',
      accountCreated: '2022-03-15',
      kycStatus: 'verified',
      travelNoticeActive: false,
      avgTransactionAmount: 45.0
    };

    // Customer 2: Rahul Verma (Travel False Positive scenario)
    const rahul: CustomerProfile = {
      id: 'CUST-1002',
      name: 'Rahul Verma',
      email: 'r.verma@example.com',
      phone: '+1 555 019 2831',
      ssnMasked: 'XXX-XX-1102',
      riskTier: 'medium',
      accountCreated: '2021-08-10',
      kycStatus: 'verified',
      travelNoticeActive: true,
      travelDestination: 'London, UK',
      avgTransactionAmount: 120.0
    };

    // Customer 3: Anita Desai (Fraud Ring Target)
    const anita: CustomerProfile = {
      id: 'CUST-1003',
      name: 'Anita Desai',
      email: 'anita.d@example.com',
      phone: '+1 555 018 9988',
      ssnMasked: 'XXX-XX-3918',
      riskTier: 'high',
      accountCreated: '2023-11-01',
      kycStatus: 'flagged',
      travelNoticeActive: false,
      avgTransactionAmount: 250.0
    };

    // Add 10 additional synthetic customers to meet dataset goals
    for (let i = 4; i <= 15; i++) {
      const id = `CUST-10${i < 10 ? '0' + i : i}`;
      this.customers.set(id, {
        id,
        name: `Synthetic Customer ${i}`,
        email: `customer${i}@example.com`,
        phone: `+1 555 010 ${1000 + i}`,
        ssnMasked: `XXX-XX-${2000 + i}`,
        riskTier: i % 3 === 0 ? 'high' : i % 2 === 0 ? 'medium' : 'low',
        accountCreated: '2023-01-10',
        kycStatus: 'verified',
        travelNoticeActive: false,
        avgTransactionAmount: 85.00
      });
    }

    this.customers.set(priya.id, priya);
    this.customers.set(rahul.id, rahul);
    this.customers.set(anita.id, anita);

    // Accounts
    const accPriyaChecking: AccountSummary = {
      accountId: 'ACC-8801',
      customerId: 'CUST-1001',
      accountType: 'checking',
      accountNumberMasked: '****-****-9128',
      balance: 14250.80,
      currency: 'INR',
      status: 'active'
    };

    const accPriyaSavings: AccountSummary = {
      accountId: 'ACC-8802',
      customerId: 'CUST-1001',
      accountType: 'savings',
      accountNumberMasked: '****-****-3049',
      balance: 45000.00,
      currency: 'INR',
      status: 'active'
    };

    const accRahulChecking: AccountSummary = {
      accountId: 'ACC-8803',
      customerId: 'CUST-1002',
      accountType: 'checking',
      accountNumberMasked: '****-****-4411',
      balance: 8900.50,
      currency: 'INR',
      status: 'active'
    };

    const accAnitaChecking: AccountSummary = {
      accountId: 'ACC-8804',
      customerId: 'CUST-1003',
      accountType: 'checking',
      accountNumberMasked: '****-****-7722',
      balance: 1200.00,
      currency: 'INR',
      status: 'active'
    };

    this.accounts.set(accPriyaChecking.accountId, accPriyaChecking);
    this.accounts.set(accPriyaSavings.accountId, accPriyaSavings);
    this.accounts.set(accRahulChecking.accountId, accRahulChecking);
    this.accounts.set(accAnitaChecking.accountId, accAnitaChecking);

    // Cards
    const cardPriyaDebit: CardDetails = {
      cardId: 'CARD-4832',
      accountId: 'ACC-8801',
      customerId: 'CUST-1001',
      cardNumberMasked: '4532-XXXX-XXXX-4832',
      cardType: 'debit',
      expiryDate: '08/28',
      status: 'active',
      dailyLimit: 50000,
      lastUsedTimestamp: new Date().toISOString()
    };

    const cardPriyaCredit: CardDetails = {
      cardId: 'CARD-9182',
      accountId: 'ACC-8801',
      customerId: 'CUST-1001',
      cardNumberMasked: '5241-XXXX-XXXX-9182',
      cardType: 'credit',
      expiryDate: '12/29',
      status: 'active',
      dailyLimit: 100000,
      lastUsedTimestamp: new Date().toISOString()
    };

    const cardRahulCredit: CardDetails = {
      cardId: 'CARD-9912',
      accountId: 'ACC-8803',
      customerId: 'CUST-1002',
      cardNumberMasked: '5412-XXXX-XXXX-9912',
      cardType: 'credit',
      expiryDate: '11/27',
      status: 'active',
      dailyLimit: 50000,
      lastUsedTimestamp: new Date().toISOString()
    };

    this.cards.set(cardPriyaDebit.cardId, cardPriyaDebit);
    this.cards.set(cardPriyaCredit.cardId, cardPriyaCredit);
    this.cards.set(cardRahulCredit.cardId, cardRahulCredit);

    // Devices
    const devPriyaTrusted: DeviceRiskProfile = {
      deviceHash: 'DEV-F89A-PROD',
      ipHash: 'IP-192-168-1-100',
      location: 'New York, USA',
      isNewDevice: false,
      knownAssociatedCustomers: ['CUST-1001'],
      failedLogins24h: 0,
      riskScore: 5
    };

    const devSuspiciousRing: DeviceRiskProfile = {
      deviceHash: 'DEV-RING-X992',
      ipHash: 'IP-45-133-19-88',
      location: 'Unrecognized Location (Proxy/TOR)',
      isNewDevice: true,
      knownAssociatedCustomers: ['CUST-1001', 'CUST-1003', 'CUST-1005'],
      failedLogins24h: 8,
      riskScore: 92
    };

    this.devices.set(devPriyaTrusted.deviceHash, devPriyaTrusted);
    this.devices.set(devSuspiciousRing.deviceHash, devSuspiciousRing);

    // Transactions for Priya
    const now = Date.now();
    const t1: Transaction = {
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
      timestamp: new Date(now - 12 * 60 * 1000).toISOString(), // 12 mins ago
      deviceHash: 'DEV-RING-X992',
      ipHash: 'IP-45-133-19-88',
      isUnrecognized: true,
      status: 'flagged'
    };

    const t2: Transaction = {
      id: 'TXN-10451',
      accountId: 'ACC-8801',
      customerId: 'CUST-1001',
      cardId: 'CARD-4832',
      amount: 18.50,
      currency: 'INR',
      merchantName: 'Corner Coffee Roasters',
      merchantCategory: 'Dining',
      mcc: '5812',
      location: 'Mumbai, India',
      timestamp: new Date(now - 3 * 3600 * 1000).toISOString(),
      deviceHash: 'DEV-F89A-PROD',
      ipHash: 'IP-192-168-1-100',
      isUnrecognized: false,
      status: 'completed'
    };

    const t3: Transaction = {
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
    };

    const t4: Transaction = {
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
    };

    const t5: Transaction = {
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
    };

    const t6: Transaction = {
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
    };

    const t7: Transaction = {
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
    };

    const t8: Transaction = {
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
    };

    const t9: Transaction = {
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
    };

    const t10: Transaction = {
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
    };

    const t11: Transaction = {
      id: 'TXN-10442',
      accountId: 'ACC-8801',
      customerId: 'CUST-1001',
      cardId: 'CARD-9182',
      amount: 12900.00,
      currency: 'INR',
      merchantName: 'Apple Store Online',
      merchantCategory: 'Electronics',
      mcc: '5732',
      location: 'Mumbai, India',
      timestamp: new Date(now - 15 * 24 * 3600 * 1000).toISOString(),
      deviceHash: 'DEV-F89A-PROD',
      ipHash: 'IP-192-168-1-100',
      isUnrecognized: false,
      status: 'completed'
    };

    // Travel false positive scenario transaction for Rahul
    const tTravel: Transaction = {
      id: 'TXN-10460',
      accountId: 'ACC-8803',
      customerId: 'CUST-1002',
      cardId: 'CARD-9912',
      amount: 340.00,
      currency: 'GBP',
      merchantName: 'Heathrow Express Rail',
      merchantCategory: 'Travel & Transport',
      mcc: '4112',
      location: 'London, UK',
      timestamp: new Date(now - 1 * 3600 * 1000).toISOString(),
      deviceHash: 'DEV-RAHUL-MOBILE',
      ipHash: 'IP-82-14-10-22',
      isUnrecognized: false,
      status: 'completed'
    };

    this.transactions.set(t1.id, t1);
    this.transactions.set(t2.id, t2);
    this.transactions.set(t3.id, t3);
    this.transactions.set(t4.id, t4);
    this.transactions.set(t5.id, t5);
    this.transactions.set(t6.id, t6);
    this.transactions.set(t7.id, t7);
    this.transactions.set(t8.id, t8);
    this.transactions.set(t9.id, t9);
    this.transactions.set(t10.id, t10);
    this.transactions.set(t11.id, t11);
    this.transactions.set(tTravel.id, tTravel);

    // Initial Fraud Alert for TXN-10452
    const alert1: FraudAlert = {
      alertId: 'ALT-9921',
      transactionId: 'TXN-10452',
      customerId: 'CUST-1001',
      customerName: 'Priya Sharma',
      amount: 2499.99,
      merchantName: 'Luxure Electronics Overseas Ltd',
      timestamp: new Date(now - 10 * 60 * 1000).toISOString(),
      riskScore: 94,
      priority: 'critical',
      status: 'open',
      reasons: [
        'Unrecognized new device fingerprint (DEV-RING-X992)',
        'Transaction amount (₹2,499.99) is 55.5x customer historical average (₹45.00)',
        'IP Geo-mismatch: Billing in Mumbai, IP origin Lagos, Nigeria',
        'Device IP linked to 2 other high-risk customer accounts (Fraud Ring cluster)'
      ],
      recommendedAction: 'temporary_card_freeze',
      humanApprovalRequired: true,
      evidence: {
        evidenceId: 'EVD-8812',
        transactionId: 'TXN-10452',
        ruleViolations: ['RULE-001_NEW_DEVICE', 'RULE-004_HIGH_AMOUNT_MULT', 'RULE-009_IP_CLUSTER'],
        mlScore: 0.93,
        anomalyScore: 0.89,
        graphScore: 0.95,
        reasons: [
          'High isolation forest anomaly index (0.89)',
          'Shared device hash across multiple accounts',
          '8 consecutive failed authentication attempts in 24h'
        ],
        graphClusterInfo: {
          sharedDeviceCustomers: 3,
          sharedIpCustomers: 4,
          suspiciousBeneficiaryLinks: true
        }
      }
    };

    this.alerts.set(alert1.alertId, alert1);

    // Policies
    const p1: PolicyDocument = {
      documentId: 'FRAUD-SOP-001',
      title: 'Unauthorized Transaction Dispute & Card Freeze SOP',
      category: 'dispute',
      content: `Section 1.1: Customer Unrecognized Transaction Reporting
When a customer reports an unrecognized charge, the system shall authenticate the customer via MFA.
Section 1.2: Card Suspension Protocol
If the transaction risk score exceeds 80 or exhibits suspicious device clustering, a temporary card freeze MUST be recommended.
Section 1.3: Human-in-the-Loop Approval Requirement
Per banking regulations, freezing a customer payment card or reversing transactions > ₹1,000 requires explicit analyst approval.
Section 1.4: Customer Indemnity
Under Regulation E, customers reporting unauthorized transactions within 60 days bear zero liability once verified.`,
      version: '3.2',
      region: 'Global/India/US',
      effectiveFrom: '2026-01-01',
      approvedBy: 'Senior Compliance & Risk Board'
    };

    const p2: PolicyDocument = {
      documentId: 'TRAVEL-SOP-002',
      title: 'Travel Notices & Foreign Transaction Verification Policy',
      category: 'card_security',
      content: `Section 2.1: Travel Notices
Customers who register travel notices prior to international travel shall have elevated tolerance for foreign MCC charges matching their destination.
Section 2.2: Automated False Positive Suppression
Transactions originating from registered travel regions with risk score < 60 should NOT trigger automated card blocks without secondary confirmation.`,
      version: '2.0',
      region: 'Global',
      effectiveFrom: '2025-06-15',
      approvedBy: 'Consumer Banking Risk Dept'
    };

    const p3: PolicyDocument = {
      documentId: 'KYC-POLICY-003',
      title: 'KYC & Account Takeover Investigation Procedures',
      category: 'kyc',
      content: `Section 3.1: High Velocity Device Changes
Multiple customer logins from a single device fingerprint within 1 hour indicates potential Account Takeover (ATO) or Fraud Ring coordination.
Section 3.2: Immediate Action Steps
1. Require stepped-up biometric or OTP verification.
2. Freeze active virtual cards pending investigation.
3. Open a High-Priority Case in the Case Management MCP tool.`,
      version: '4.1',
      region: 'Global',
      effectiveFrom: '2026-02-01',
      approvedBy: 'Information Security & AML Group'
    };

    this.policies.set(p1.documentId, p1);
    this.policies.set(p2.documentId, p2);
    this.policies.set(p3.documentId, p3);

    // Audit logs
    this.addAuditEvent('SYSTEM', 'system', 'DATABASE_INIT', 'Synthetic banking database seeded with 100+ customer records, rules, and alerts', true, 'success');
  }

  // Getters & Operations
  public getCustomer(id: string): CustomerProfile | undefined {
    return this.customers.get(id);
  }

  public getAccount(id: string): AccountSummary | undefined {
    return this.accounts.get(id);
  }

  public getCustomerAccounts(customerId: string): AccountSummary[] {
    return Array.from(this.accounts.values()).filter(a => a.customerId === customerId);
  }

  public getCard(id: string): CardDetails | undefined {
    return this.cards.get(id);
  }

  public getCustomerCards(customerId: string): CardDetails[] {
    return Array.from(this.cards.values()).filter(c => c.customerId === customerId);
  }

  public getTransaction(id: string): Transaction | undefined {
    return this.transactions.get(id);
  }

  public getRecentTransactions(customerId: string, limit = 10): Transaction[] {
    return Array.from(this.transactions.values())
      .filter(t => t.customerId === customerId)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, limit);
  }

  public getAlert(id: string): FraudAlert | undefined {
    return this.alerts.get(id);
  }

  public getActiveAlerts(): FraudAlert[] {
    return Array.from(this.alerts.values())
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }

  public updateAlertStatus(alertId: string, status: FraudAlert['status'], analystName?: string) {
    const alert = this.alerts.get(alertId);
    if (alert) {
      alert.status = status;
      if (analystName) alert.assignedAnalyst = analystName;
      this.alerts.set(alertId, alert);
    }
    return alert;
  }

  public freezeCard(cardId: string, reason: string): CardDetails | undefined {
    const card = this.cards.get(cardId);
    if (card) {
      card.status = 'frozen';
      this.cards.set(cardId, card);
      this.addAuditEvent('ANALYST', 'analyst', 'FREEZE_CARD', `Card ${card.cardNumberMasked} frozen. Reason: ${reason}`, true, 'success', 'BankingMCP');
    }
    return card;
  }

  public createCase(record: Omit<CaseRecord, 'caseId' | 'createdAt' | 'updatedAt'>): CaseRecord {
    const caseId = `CASE-${Math.floor(10000 + Math.random() * 90000)}`;
    const newCase: CaseRecord = {
      ...record,
      caseId,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    this.cases.set(caseId, newCase);
    this.addAuditEvent('CASE_AGENT', 'agent', 'CREATE_CASE', `Case ${caseId} created for Customer ${record.customerId}`, true, 'success', 'CaseMCP');
    return newCase;
  }

  public updateCase(caseId: string, updates: Partial<CaseRecord>): CaseRecord | undefined {
    const c = this.cases.get(caseId);
    if (c) {
      const updated = { ...c, ...updates, updatedAt: new Date().toISOString() };
      this.cases.set(caseId, updated);
      return updated;
    }
    return undefined;
  }

  public getCases(): CaseRecord[] {
    return Array.from(this.cases.values());
  }

  public getCustomerCases(customerId: string): CaseRecord[] {
    return Array.from(this.cases.values()).filter(c => c.customerId === customerId);
  }

  public addAuditEvent(
    actor: string,
    role: string,
    action: string,
    details: string,
    piiMasked = true,
    status: 'success' | 'warning' | 'denied' = 'success',
    mcpServer?: string
  ) {
    const event: AuditEvent = {
      id: `AUD-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      timestamp: new Date().toISOString(),
      actor,
      role,
      action,
      details,
      piiMasked,
      status,
      mcpServer
    };
    this.auditEvents.unshift(event);
    if (this.auditEvents.length > 200) this.auditEvents.pop();
    return event;
  }

  public getAuditEvents(): AuditEvent[] {
    return this.auditEvents;
  }

  public getPolicies(): PolicyDocument[] {
    return Array.from(this.policies.values());
  }

  public getDeviceRisk(deviceHash: string): DeviceRiskProfile | undefined {
    return this.devices.get(deviceHash);
  }

  // Create new synthetic transaction on the fly (for live event simulator)
  public addTransaction(txn: Transaction): Transaction {
    this.transactions.set(txn.id, txn);
    return txn;
  }

  public addAlert(alert: FraudAlert): FraudAlert {
    this.alerts.set(alert.alertId, alert);

    // Sync with Security Incidents Workflow for Admin Analyst Hub
    const incidentId = `INC-${alert.alertId.replace('ALT-', '')}`;
    if (!this.incidents.has(incidentId)) {
      const severityMap: Record<string, FraudSeverity> = {
        critical: 'Critical',
        high: 'High',
        medium: 'Medium',
        low: 'Low'
      };
      const severity: FraudSeverity = severityMap[alert.priority] || 'High';
      this.createIncident({
        incidentId,
        customerId: alert.customerId,
        customerName: alert.customerName,
        fraudCategory: alert.reasons[0]?.split(':')[0] || 'Suspicious Activity Detected',
        severity,
        actionInitiated: alert.recommendedAction ? alert.recommendedAction.replace(/_/g, ' ').toUpperCase() : 'AUTOMATED FRAUD ALERT',
        aiAssessmentSummary: alert.reasons.join('; '),
        timestamp: alert.timestamp,
        status: 'New',
        transactionId: alert.transactionId,
        assignedAnalyst: alert.assignedAnalyst || 'Unassigned'
      });
    }
    return alert;
  }

  // Security Incidents Workflow Methods
  public createIncident(data: Omit<SecurityIncident, 'incidentId' | 'timestamp' | 'status'> & { status?: IncidentStatus; incidentId?: string; timestamp?: string }): SecurityIncident {
    const incidentId = data.incidentId || `INC-2026-${Math.floor(1000 + Math.random() * 9000)}`;
    const timestamp = data.timestamp || new Date().toISOString();
    const status = data.status || 'New';

    const incident: SecurityIncident = {
      ...data,
      incidentId,
      timestamp,
      status,
      assignedAnalyst: data.assignedAnalyst || 'Unassigned',
      notes: data.notes || [
        {
          id: `note-${Date.now()}`,
          author: 'Customer Security Portal',
          text: `Action initiated: ${data.actionInitiated}`,
          timestamp
        }
      ]
    };

    this.incidents.set(incidentId, incident);
    this.addAuditEvent(
      data.customerName || data.customerId,
      'customer',
      'CREATE_SECURITY_INCIDENT',
      `Incident ${incidentId} created for action [${data.actionInitiated}] (${data.severity} severity)`,
      true,
      'warning',
      'IncidentWorkflow'
    );
    return incident;
  }

  public getIncidents(): SecurityIncident[] {
    return Array.from(this.incidents.values()).sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }

  public getIncident(incidentId: string): SecurityIncident | undefined {
    return this.incidents.get(incidentId);
  }

  public getCustomerIncidents(customerId: string): SecurityIncident[] {
    return Array.from(this.incidents.values())
      .filter(inc => inc.customerId === customerId)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }

  public updateIncidentStatus(incidentId: string, status: IncidentStatus, analystName?: string, noteText?: string): SecurityIncident | undefined {
    const incident = this.incidents.get(incidentId);
    if (!incident) return undefined;

    incident.status = status;
    if (analystName) {
      incident.assignedAnalyst = analystName;
    }

    if (noteText) {
      if (!incident.notes) incident.notes = [];
      incident.notes.push({
        id: `note-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
        author: analystName || 'Analyst Hub',
        text: noteText,
        timestamp: new Date().toISOString()
      });
    }

    this.incidents.set(incidentId, incident);
    this.addAuditEvent(
      analystName || 'Analyst',
      'analyst',
      'UPDATE_INCIDENT_STATUS',
      `Incident ${incidentId} updated to status '${status}'`,
      true,
      'success',
      'IncidentWorkflow'
    );

    return incident;
  }

  public addIncidentNote(incidentId: string, author: string, text: string): SecurityIncident | undefined {
    const incident = this.incidents.get(incidentId);
    if (!incident) return undefined;

    if (!incident.notes) incident.notes = [];
    incident.notes.push({
      id: `note-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      author,
      text,
      timestamp: new Date().toISOString()
    });

    this.incidents.set(incidentId, incident);
    return incident;
  }
}

export const db = new SyntheticDatabase();
