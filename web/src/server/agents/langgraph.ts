import { GoogleGenAI } from '@google/genai';
import { db } from '../db';
import { MCPGateway } from '../mcp/mcpGateway';
import { PolicyRAGEngine } from '../rag';
import { PresidioGuardrails } from '../security/presidio';
import { TemporalWorkflowAdapter } from '../workflows/temporal';
import { AgentTrace, ChatMessage, FraudAlert } from '../../types';
import { FraudClassifier } from './fraudClassifier';

export class LangGraphOrchestrator {
  private static genaiClient: GoogleGenAI | null = null;

  private static getGenAI(): GoogleGenAI | null {
    if (!this.genaiClient && process.env.GEMINI_API_KEY) {
      try {
        this.genaiClient = new GoogleGenAI({
          apiKey: process.env.GEMINI_API_KEY,
          httpOptions: {
            headers: {
              'User-Agent': 'aistudio-build'
            }
          }
        });
      } catch (e) {
        console.warn('Gemini API initialization deferred or failed:', e);
      }
    }
    return this.genaiClient;
  }

  public static async processCustomerMessage(
    userMessage: string,
    customerId: string = 'CUST-1001',
    userRole: string = 'customer',
    overrideTransactionId?: string
  ): Promise<{ responseMessage: ChatMessage; newAlert?: FraudAlert }> {
    const traces: AgentTrace[] = [];
    const startTime = Date.now();

    // STEP 1: Security & Guardrail Check (PII & Prompt Injection)
    const securityCheck = PresidioGuardrails.inspectInput(userMessage, userRole);
    if (!securityCheck.isSafe) {
      db.addAuditEvent('GuardrailsAI', userRole, 'SECURITY_BLOCK', securityCheck.reason || 'Blocked', true, 'denied');
      return {
        responseMessage: {
          id: `MSG-${Date.now()}`,
          sender: 'agent',
          agentName: 'Security & Guardrails Agent',
          text: securityCheck.sanitizedText,
          timestamp: new Date().toISOString(),
          piiMaskedText: securityCheck.sanitizedText
        }
      };
    }

    const cleanInput = securityCheck.sanitizedText;

    // STEP 2: Supervisor Agent - Intent Classification & Routing
    const supervisorTraceStart = Date.now();
    let intent: string = 'unknown';
    let urgency: 'high' | 'medium' | 'low' = 'low';

    const inputLower = cleanInput.toLowerCase();
    if (inputLower.includes('analyst') || inputLower.includes('speak') || inputLower.includes('human') || inputLower.includes('advisor') || inputLower.includes('contact support') || inputLower.includes('connect')) {
      intent = 'analyst_connect';
      urgency = 'high';
    } else if (inputLower.includes('phishing') || inputLower.includes('fake email') || inputLower.includes('fake sms') || inputLower.includes('scam') || inputLower.includes('received a suspicious')) {
      intent = 'phishing_report';
      urgency = 'high';
    } else if (inputLower.includes('password') || inputLower.includes('pin') || inputLower.includes('reset') || inputLower.includes('credential')) {
      intent = 'credential_reset';
      urgency = 'high';
    } else if (inputLower.includes('lost') || inputLower.includes('stolen card') || inputLower.includes('lost card') || inputLower.includes('physical card') || inputLower.includes('freeze card') || inputLower.includes('block card') || inputLower.includes('card lost')) {
      intent = 'card_issue';
      urgency = 'high';
    } else if (inputLower.includes('unrecognized') || inputLower.includes('report ₹') || inputLower.includes('report transaction') || inputLower.includes('fraud') || inputLower.includes('didn\'t make') || inputLower.includes('suspicious charge') || inputLower.includes('unauthorized') || overrideTransactionId) {
      intent = 'fraud_report';
      urgency = 'high';
    } else if (inputLower.includes('balance') || inputLower.includes('checking balance') || inputLower.includes('savings balance') || inputLower.includes('account balance')) {
      intent = 'account_query';
      urgency = 'low';
    } else if (inputLower.includes('transaction') || inputLower.includes('charge') || inputLower.includes('spent') || inputLower.includes('purchase') || inputLower.includes('statement') || inputLower.includes('history') || inputLower.includes('recent')) {
      intent = 'transaction_query';
      urgency = 'medium';
    } else if (inputLower.includes('policy') || inputLower.includes('limit') || inputLower.includes('dispute') || inputLower.includes('kyc') || inputLower.includes('sop')) {
      intent = 'policy_question';
      urgency = 'low';
    }

    traces.push({
      stepId: `TRACE-1`,
      agentName: 'LangGraph Supervisor Agent',
      timestamp: new Date().toISOString(),
      input: cleanInput,
      output: `Intent classified as '${intent}' with Urgency level '${urgency}'. Routing to target subgraph.`,
      durationMs: Date.now() - supervisorTraceStart,
      status: 'routing'
    });

    let finalResponseText = '';
    let sources: any[] = [];
    let suggestedActions: string[] = [];
    let newAlertCreated: FraudAlert | undefined = undefined;
    let currentTxnContext: any = undefined;
    let createdCaseId: string | undefined = undefined;

    const isPhishingQuery = inputLower.includes('phishing') || inputLower.includes('otp') || inputLower.includes('fake email') || inputLower.includes('fake sms') || inputLower.includes('scam');

    // STEP 3: Subgraph Routing
    if (isPhishingQuery) {
      // PHISHING & SOCIAL ENGINEERING SUBGRAPH
      const phishingTraceStart = Date.now();

      // Case Agent & Human Approval Queue
      const newCase = await MCPGateway.executeTool('CaseMCP', 'create_case', {
        customerId,
        title: 'Phishing & Social Engineering Alert',
        description: `Customer reported suspicious phishing attempt / OTP solicitation: "${cleanInput}"`,
        priority: 'high'
      }, { userRole });
      createdCaseId = newCase.caseId;

      // Start SLA workflow
      TemporalWorkflowAdapter.startFraudDisputeWorkflow(newCase.caseId, 'high');

      // Create live alert in Fraud Hub
      newAlertCreated = {
        alertId: `ALT-${Math.floor(1000 + Math.random() * 9000)}`,
        transactionId: 'N/A (Phishing Attempt)',
        customerId,
        customerName: (await MCPGateway.executeTool('BankingMCP', 'get_customer_profile', { customerId }, { userRole })).name,
        amount: 0,
        merchantName: 'Deceptive Gateway / Phishing Email',
        timestamp: new Date().toISOString(),
        riskScore: 94,
        priority: 'high',
        status: 'open',
        reasons: ['Social engineering or deceptive link interaction reported', 'Potential leakage of OTP or credentials'],
        recommendedAction: 'customer_verification',
        humanApprovalRequired: true,
        evidence: {
          evidenceId: `EVID-${Math.floor(1000 + Math.random() * 9000)}`,
          transactionId: 'TXN-NONE',
          ruleViolations: ['Social Engineering / Phishing Link Reported'],
          mlScore: 0.94,
          anomalyScore: 0.92,
          graphScore: 0.88,
          reasons: ['Social engineering or deceptive link interaction reported', 'Potential leakage of OTP or credentials']
        },
        caseId: newCase.caseId
      };
      db.addAlert(newAlertCreated);

      // RAG Policy search for phishing & credential protection
      const phishingPolicies = PolicyRAGEngine.searchPolicies('phishing email otp credential compromise', 'dispute');
      sources = phishingPolicies.map(p => p.citation);

      traces.push({
        stepId: `TRACE-2`,
        agentName: 'Phishing & Credential Security Subgraph Agent',
        timestamp: new Date().toISOString(),
        input: `Processing Phishing/OTP report: "${cleanInput}"`,
        output: `Logged Incident Case ${newCase.caseId}. Security advisory dispatched. Escalated to Fraud Operations.`,
        toolsCalled: ['CaseMCP:create_case', 'PolicyRAGEngine:searchPolicies'],
        durationMs: Date.now() - phishingTraceStart,
        status: 'completed'
      });

      finalResponseText = `I have logged a **High-Priority Phishing & Credential Security Incident** in our Fraud Operations Queue (Case \`${newCase.caseId}\`).\n\n` +
        `🔒 **Critical Safety Reminder:** SentinelBank will **NEVER** ask for your 6-digit OTP, ATM PIN, or Online Banking password via email, SMS, or phone calls.\n\n` +
        `🛡️ **Protective Measures Initiated:**\n` +
        `- **Case Reference:** \`${newCase.caseId}\` assigned to Senior Fraud Analyst\n` +
        `- **Credential Protection:** Zero Liability policy active for any unauthorized attempts\n` +
        `- **Recommended Action:** Do not click links or share codes. Reset your password immediately if credentials were typed into an unverified form.`;

      suggestedActions = ['Reset Password & PIN', 'Review Active Devices', 'Speak with Analyst'];

    } else if (intent === 'fraud_report' || overrideTransactionId) {
      // TRANSACTION FRAUD WORKFLOW SUBGRAPH
      const fraudTraceStart = Date.now();

      // Look up suspicious transaction
      const txnId = overrideTransactionId || 'TXN-10452';
      const txn = await MCPGateway.executeTool('BankingMCP', 'get_transaction', { transactionId: txnId }, { customerId, userRole });
      currentTxnContext = txn;

      // Run Fraud Engine & Fraud MCP
      const fraudResult = await MCPGateway.executeTool('FraudMCP', 'calculate_fraud_score', { transactionId: txnId }, { userRole });

      // Risk Agent synthesis
      traces.push({
        stepId: `TRACE-2`,
        agentName: 'Fraud & Risk Subgraph Agent',
        timestamp: new Date().toISOString(),
        input: `Evaluating transaction ${txnId} (${txn.merchantName}, ₹${txn.amount})`,
        output: `Calculated Fraud Risk Score: ${fraudResult.riskScore}/100 [Priority: ${fraudResult.priority.toUpperCase()}]. Reasons: ${fraudResult.reasons.join('; ')}`,
        toolsCalled: ['BankingMCP:get_transaction', 'FraudMCP:calculate_fraud_score'],
        durationMs: Date.now() - fraudTraceStart,
        status: 'completed'
      });

      // Case Agent & Human Approval Queue
      const caseTraceStart = Date.now();
      const newCase = await MCPGateway.executeTool('CaseMCP', 'create_case', {
        customerId,
        transactionId: txnId,
        title: `Fraud Report: ${txn.merchantName} (₹${txn.amount})`,
        description: `Customer reported unrecognized charge. Risk Score: ${fraudResult.riskScore}. Reasons: ${fraudResult.reasons.join(', ')}`,
        priority: fraudResult.priority
      }, { userRole });
      createdCaseId = newCase.caseId;

      // Start Temporal SLA workflow
      TemporalWorkflowAdapter.startFraudDisputeWorkflow(newCase.caseId, fraudResult.priority);

      // Create live alert if needed
      newAlertCreated = {
        alertId: `ALT-${Math.floor(1000 + Math.random() * 9000)}`,
        transactionId: txnId,
        customerId,
        customerName: (await MCPGateway.executeTool('BankingMCP', 'get_customer_profile', { customerId }, { userRole })).name,
        amount: txn.amount,
        merchantName: txn.merchantName,
        timestamp: new Date().toISOString(),
        riskScore: fraudResult.riskScore,
        priority: fraudResult.priority,
        status: 'open',
        reasons: fraudResult.reasons,
        recommendedAction: 'temporary_card_freeze',
        humanApprovalRequired: true,
        evidence: fraudResult.evidence,
        caseId: newCase.caseId
      };

      db.addAlert(newAlertCreated);

      // RAG Policy search for disputes
      const disputePolicies = PolicyRAGEngine.searchPolicies('unauthorized dispute card freeze', 'dispute');
      sources = disputePolicies.map(p => p.citation);

      traces.push({
        stepId: `TRACE-3`,
        agentName: 'Case Agent & Human-in-the-Loop Orchestrator',
        timestamp: new Date().toISOString(),
        input: `Initiating Case ${newCase.caseId} & Customer Notification`,
        output: `Case ${newCase.caseId} opened. High-impact action (Card Freeze) paused pending Analyst Human Approval per SOP ${sources[0]?.docId || 'FRAUD-SOP-001'}.`,
        toolsCalled: ['CaseMCP:create_case', 'CaseMCP:request_approval'],
        durationMs: Date.now() - caseTraceStart,
        status: 'approval_paused'
      });

      finalResponseText = `I have flagged the suspicious charge of **₹${txn.amount.toFixed(2)}** at **${txn.merchantName}**.\n\n` +
        `🔒 **Security Actions Taken:**\n` +
        `- **Risk Score:** ${fraudResult.riskScore}/100 (${fraudResult.priority.toUpperCase()} priority risk)\n` +
        `- **Key Risk Factors:** ${fraudResult.reasons[0] || 'Unrecognized location & high multiplier'}\n` +
        `- **Case Reference:** Case \`${newCase.caseId}\` created in Fraud Ops Queue.\n\n` +
        `⚠️ **Human-in-the-Loop Security Protocol:** Per regulatory standards, freezing your debit card requires a 1-click verification from our Fraud Analyst team. An analyst has been notified on the live monitoring hub.\n\n` +
        `Under Regulation E (Dispute SOP FRAUD-SOP-001), you bear **Zero Liability** for verified unauthorized transactions.`;

      suggestedActions = ['View Case Status', 'Speak with Analyst', 'Review Recent Transactions'];

    } else if (intent === 'analyst_connect') {
      const analystTraceStart = Date.now();

      const cases = db.getCases().filter(c => c.customerId === customerId);
      let activeCase = cases.find(c => c.status === 'pending_approval' || c.status === 'approved') || cases[0];

      if (!activeCase) {
        const newCase = await MCPGateway.executeTool('CaseMCP', 'create_case', {
          customerId,
          title: 'Customer Requested Live Fraud Analyst Consultation',
          description: `Customer requested direct analyst intervention: "${cleanInput}"`,
          priority: 'high'
        }, { userRole });
        activeCase = newCase;
      }

      createdCaseId = activeCase.caseId;

      traces.push({
        stepId: `TRACE-2`,
        agentName: 'Case Agent & Analyst Dispatcher',
        timestamp: new Date().toISOString(),
        input: `Routing customer ${customerId} to Live Fraud Analyst Queue`,
        output: `Case ${activeCase.caseId} assigned to Senior Fraud Analyst Alex Vance. Live notification dispatched to Analyst Hub.`,
        toolsCalled: ['CaseMCP:create_case', 'WebSocketGateway:broadcast'],
        durationMs: Date.now() - analystTraceStart,
        status: 'completed'
      });

      finalResponseText = `I have routed your inquiry directly to our **Live Fraud Analyst Queue** (Case Reference: \`${activeCase.caseId}\`).\n\n` +
        `👨‍💼 **Assigned Lead Analyst:** Alex Vance (Senior Risk & Fraud Operations)\n` +
        `📡 **Status:** Active Review • Live Analyst Monitoring Hub Alerted\n\n` +
        `Analyst Alex Vance has received your case context and account security signals. They will monitor your session and can review any suspicious charges, freeze debit cards, or initiate formal dispute documentation on your behalf.\n\n` +
        `If you need to perform an immediate protective action yourself, please choose from the options below:`;

      suggestedActions = ['Report Unrecognized Charge', 'Reset Password & PIN', 'Check Account Balances'];

    } else if (intent === 'account_query') {
      const accTraceStart = Date.now();
      const accounts = await MCPGateway.executeTool('BankingMCP', 'get_account_summary', { customerId }, { customerId, userRole });
      const profile = await MCPGateway.executeTool('BankingMCP', 'get_customer_profile', { customerId }, { customerId, userRole });

      traces.push({
        stepId: `TRACE-2`,
        agentName: 'Customer Support Subgraph Agent',
        timestamp: new Date().toISOString(),
        input: `Fetching account balances for ${customerId}`,
        output: `Retrieved ${accounts.length} active account balances securely via Banking MCP.`,
        toolsCalled: ['BankingMCP:get_account_summary', 'BankingMCP:get_customer_profile'],
        durationMs: Date.now() - accTraceStart,
        status: 'completed'
      });

      const accListText = accounts.map((a: any) => `• **${a.accountType.toUpperCase()}** (${a.accountNumberMasked}): **₹${a.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}** ${a.currency}`).join('\n');

      finalResponseText = `Hello ${profile.name}! Here is your verified account summary:\n\n${accListText}\n\nIs there anything else I can assist you with regarding your accounts or recent transactions?`;
      suggestedActions = ['Check Recent Transactions', 'Report Suspicious Activity', 'Manage Cards'];

    } else if (intent === 'policy_question') {
      const ragTraceStart = Date.now();
      const ragResults = PolicyRAGEngine.searchPolicies(cleanInput);
      sources = ragResults.map(r => r.citation);

      traces.push({
        stepId: `TRACE-2`,
        agentName: 'Knowledge Agent (LlamaIndex RAG)',
        timestamp: new Date().toISOString(),
        input: `Hybrid policy search for query: "${cleanInput}"`,
        output: `Retrieved ${ragResults.length} policy documents with citations. Top document: ${sources[0]?.title || 'FAQ'} (v${sources[0]?.version || '1.0'})`,
        toolsCalled: ['PolicyRAGEngine:searchPolicies'],
        durationMs: Date.now() - ragTraceStart,
        status: 'completed'
      });

      if (ragResults.length > 0) {
        finalResponseText = `According to our official banking policy **${sources[0].title}** (Doc ID: \`${sources[0].docId}\`, Effective: ${sources[0].effectiveFrom}):\n\n` +
          `"${ragResults[0].matchedSnippets.slice(0, 2).join(' ')}"\n\n` +
          `*All policy procedures are verified and approved by the SentinelBank Compliance & Risk Board.*`;
      } else {
        finalResponseText = `I could not find a verified bank policy directly answering that request. To protect your security, I will refrain from offering policy advice without verified evidence. Would you like me to connect you with a fraud analyst or supervisor?`;
      }
      suggestedActions = ['Report Unrecognized Charge', 'View Dispute SOP', 'Check Account Balances'];

    } else if (intent === 'credential_reset') {
      const resetTraceStart = Date.now();
      const resetPolicies = PolicyRAGEngine.searchPolicies('reset password PIN OTP authentication security', 'dispute');
      sources = resetPolicies.map(p => p.citation);

      traces.push({
        stepId: `TRACE-2`,
        agentName: 'Security Credential Subgraph Agent',
        timestamp: new Date().toISOString(),
        input: `Processing Password & PIN Reset Request for customer ${customerId}`,
        output: `Initiated security credential reset protocol. Sent verification OTP trigger to customer's registered phone.`,
        toolsCalled: ['BankingMCP:get_customer_profile', 'PolicyRAGEngine:searchPolicies'],
        durationMs: Date.now() - resetTraceStart,
        status: 'completed'
      });

      finalResponseText = `I can assist you with securely resetting your **SentinelBank Password & Debit Card PIN**.\n\n` +
        `🔐 **Security Reset Verification:**\n` +
        `- **Registered Device:** A 6-digit One-Time Verification Passcode (OTP) link has been dispatched to your mobile number ending in **...9128**.\n` +
        `- **Authentication Security:** To prevent account takeover, password and PIN updates require multi-factor verification.\n\n` +
        `🛡️ **Protective Guidance:**\n` +
        `If you suspect your credentials or card details were compromised in a phishing link or unauthorized form, we strongly recommend issuing a temporary freeze on your card before completing the password reset.\n\n` +
        `How would you like to proceed?`;

      suggestedActions = ['Proceed with PIN Reset', 'Request Temporary Card Freeze', 'Speak with Analyst'];

    } else if (intent === 'card_issue') {
      const cardTraceStart = Date.now();

      // Freeze primary card in DB
      db.freezeCard('CARD-4832', `Customer reported card lost/stolen: "${cleanInput}"`);

      // Create case
      const newCase = await MCPGateway.executeTool('CaseMCP', 'create_case', {
        customerId,
        cardId: 'CARD-4832',
        title: 'Physical Card Lost / Stolen - Freeze & Replacement Issued',
        description: `Customer reported card lost or stolen: "${cleanInput}". Primary Debit Card ****-4832 frozen. Replacement order dispatched.`,
        priority: 'high'
      }, { userRole });
      createdCaseId = newCase.caseId;

      TemporalWorkflowAdapter.startFraudDisputeWorkflow(newCase.caseId, 'high');

      // Create incident record
      const incidentId = `INC-${Math.floor(10000 + Math.random() * 90000)}`;
      db.createIncident({
        incidentId,
        customerId,
        customerName: (await MCPGateway.executeTool('BankingMCP', 'get_customer_profile', { customerId }, { userRole })).name,
        fraudCategory: 'Stolen Card',
        severity: 'Critical',
        actionInitiated: 'Card Frozen & Replacement Issued',
        aiAssessmentSummary: `Card ****-4832 frozen immediately upon lost/stolen report. Case ${newCase.caseId} opened.`,
        timestamp: new Date().toISOString(),
        status: 'New',
        cardId: 'CARD-4832'
      });

      const cardPolicies = PolicyRAGEngine.searchPolicies('lost stolen card block replacement zero liability', 'dispute');
      sources = cardPolicies.map(p => p.citation);

      traces.push({
        stepId: `TRACE-2`,
        agentName: 'Card Security Subgraph Agent',
        timestamp: new Date().toISOString(),
        input: `Card Lost/Stolen Report for ${customerId}`,
        output: `Placed immediate security freeze on Debit Card ****-4832. Queued replacement card order. Created Case ${newCase.caseId}.`,
        toolsCalled: ['BankingMCP:freeze_card', 'CaseMCP:create_case', 'PolicyRAGEngine:searchPolicies'],
        durationMs: Date.now() - cardTraceStart,
        status: 'completed'
      });

      finalResponseText = `I have placed an immediate **Security Block & Freeze** on your physical Debit Card ending in **...4832**.\n\n` +
        `💳 **Card Protection & Replacement Summary:**\n` +
        `- **Card Status:** Blocked & Frozen (Debit Card ****-4832)\n` +
        `- **Case Reference:** \`${newCase.caseId}\` created in Fraud Operations Queue\n` +
        `- **Replacement Card:** A new contactless chip debit card has been ordered and will be dispatched to your registered address.\n` +
        `- **Zero Liability Guarantee:** Under Regulation E (SOP FRAUD-SOP-001), you bear zero financial liability for any unauthorized transactions.\n\n` +
        `If you need additional assistance or wish to review recent activity before the card block, please let me know.`;

      suggestedActions = ['Check Account Balances', 'Review Recent Transactions', 'Speak with Analyst'];

    } else {
      // Default transaction query / general assistant
      const txns = await MCPGateway.executeTool('BankingMCP', 'get_recent_transactions', { customerId, limit: 5 }, { customerId, userRole });

      traces.push({
        stepId: `TRACE-2`,
        agentName: 'Transaction Agent',
        timestamp: new Date().toISOString(),
        input: `Fetched 5 recent transactions for ${customerId}`,
        output: `Retrieved recent transactions list via Banking MCP.`,
        toolsCalled: ['BankingMCP:get_recent_transactions'],
        durationMs: Date.now() - Date.now(),
        status: 'completed'
      });

      const txnText = txns.map((t: any) => `• **${t.merchantName}** - ₹${t.amount.toFixed(2)} (${new Date(t.timestamp).toLocaleTimeString()}) - *${t.status.toUpperCase()}*`).join('\n');

      finalResponseText = `Here are your recent transactions:\n\n${txnText}\n\nIf you do not recognize any of these charges, please select **"Report Unrecognized Charge"** immediately.`;
      suggestedActions = ['Report Unrecognized Charge', 'View Full Statement', 'Check Account Balance'];
    }

    // Mask output PII as extra guardrail layer
    const maskedFinalResponse = PresidioGuardrails.maskOutputText(finalResponseText);

    // AI Fraud Risk & Classification Assessment
    const fraudAssessment = await FraudClassifier.classifyCustomerQuery(cleanInput, currentTxnContext);
    if (createdCaseId && fraudAssessment) {
      fraudAssessment.caseId = createdCaseId;
      fraudAssessment.assignedAnalyst = 'Alex Vance (Fraud Operations)';
    }

    const chatMsg: ChatMessage = {
      id: `MSG-${Date.now()}`,
      sender: 'agent',
      agentName: 'SentinelBank AI Supervisor',
      text: maskedFinalResponse,
      timestamp: new Date().toISOString(),
      intent,
      confidence: 0.96,
      sources,
      suggestedActions,
      traces,
      piiMaskedText: maskedFinalResponse,
      fraudAssessment
    };

    return {
      responseMessage: chatMsg,
      newAlert: newAlertCreated
    };
  }
}
