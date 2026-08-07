import { z } from 'zod';
import { db } from '../db';

export class BankingMCPServer {
  public static readonly SERVER_NAME = 'BankingMCPServer';

  // 1. get_customer_profile
  public static getCustomerProfile(params: { customerId: string; userRole?: string }) {
    const schema = z.object({ customerId: z.string() });
    const parsed = schema.parse(params);
    const customer = db.getCustomer(parsed.customerId);

    db.addAuditEvent('BankingMCP', params.userRole || 'agent', 'MCP_CALL:get_customer_profile', `Looked up profile for ${parsed.customerId}`, true, 'success', 'BankingMCP');

    if (!customer) throw new Error(`Customer ${parsed.customerId} not found`);
    return {
      customerId: customer.id,
      name: customer.name,
      email: customer.email,
      phone: customer.phone,
      ssnMasked: customer.ssnMasked,
      riskTier: customer.riskTier,
      kycStatus: customer.kycStatus,
      travelNoticeActive: customer.travelNoticeActive,
      travelDestination: customer.travelDestination
    };
  }

  // 2. get_account_summary
  public static getAccountSummary(params: { customerId: string; userRole?: string }) {
    const schema = z.object({ customerId: z.string() });
    const parsed = schema.parse(params);
    const accounts = db.getCustomerAccounts(parsed.customerId);

    db.addAuditEvent('BankingMCP', params.userRole || 'agent', 'MCP_CALL:get_account_summary', `Fetched accounts for ${parsed.customerId}`, true, 'success', 'BankingMCP');

    return accounts.map(a => ({
      accountId: a.accountId,
      accountType: a.accountType,
      accountNumberMasked: a.accountNumberMasked,
      balance: a.balance,
      currency: a.currency,
      status: a.status
    }));
  }

  // 3. get_transaction
  public static getTransaction(params: { transactionId: string; userRole?: string }) {
    const schema = z.object({ transactionId: z.string() });
    const parsed = schema.parse(params);
    const txn = db.getTransaction(parsed.transactionId);

    db.addAuditEvent('BankingMCP', params.userRole || 'agent', 'MCP_CALL:get_transaction', `Inspected transaction ${parsed.transactionId}`, true, 'success', 'BankingMCP');

    if (!txn) throw new Error(`Transaction ${parsed.transactionId} not found`);
    return txn;
  }

  // 4. get_recent_transactions
  public static getRecentTransactions(params: { customerId: string; limit?: number; userRole?: string }) {
    const schema = z.object({ customerId: z.string(), limit: z.number().optional() });
    const parsed = schema.parse(params);
    const txns = db.getRecentTransactions(parsed.customerId, parsed.limit || 10);

    db.addAuditEvent('BankingMCP', params.userRole || 'agent', 'MCP_CALL:get_recent_transactions', `Retrieved ${txns.length} recent transactions for ${parsed.customerId}`, true, 'success', 'BankingMCP');

    return txns;
  }

  // 5. get_card_status
  public static getCardStatus(params: { customerId: string; userRole?: string }) {
    const schema = z.object({ customerId: z.string() });
    const parsed = schema.parse(params);
    const cards = db.getCustomerCards(parsed.customerId);

    db.addAuditEvent('BankingMCP', params.userRole || 'agent', 'MCP_CALL:get_card_status', `Checked card status for ${parsed.customerId}`, true, 'success', 'BankingMCP');

    return cards;
  }

  // 6. freeze_card (REQUIRES HUMAN APPROVAL CHECK)
  public static freezeCard(params: {
    cardId: string;
    reason: string;
    approvedByAnalyst?: boolean;
    analystName?: string;
    idempotencyKey?: string;
    userRole?: string;
  }) {
    const schema = z.object({
      cardId: z.string(),
      reason: z.string().min(3),
      approvedByAnalyst: z.boolean().optional(),
      analystName: z.string().optional(),
      idempotencyKey: z.string().optional()
    });
    const parsed = schema.parse(params);

    // HUMAN APPROVAL ENFORCEMENT
    if (!parsed.approvedByAnalyst && params.userRole !== 'analyst' && params.userRole !== 'supervisor') {
      db.addAuditEvent(
        'BankingMCP',
        params.userRole || 'agent',
        'MCP_CALL_BLOCKED:freeze_card',
        `Blocked attempt to freeze card ${parsed.cardId} without human analyst approval`,
        true,
        'denied',
        'BankingMCP'
      );
      return {
        success: false,
        requiresHumanApproval: true,
        status: 'APPROVAL_REQUIRED',
        message: 'High-impact card freeze operation requires human analyst approval per Banking SOP FRAUD-SOP-001 Section 1.3.'
      };
    }

    const frozenCard = db.freezeCard(parsed.cardId, parsed.reason);
    if (!frozenCard) throw new Error(`Card ${parsed.cardId} not found`);

    return {
      success: true,
      status: 'FROZEN',
      cardId: frozenCard.cardId,
      cardNumberMasked: frozenCard.cardNumberMasked,
      frozenAt: new Date().toISOString(),
      approvedBy: parsed.analystName || 'Analyst Supervisor'
    };
  }
}
