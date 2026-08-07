import { z } from 'zod';
import { db } from '../db';
import { FraudDetectionEngine } from '../fraudEngine';

export class FraudMCPServer {
  public static readonly SERVER_NAME = 'FraudMCPServer';

  // 1. get_active_alerts
  public static getActiveAlerts(params: { limit?: number; userRole?: string }) {
    const alerts = db.getActiveAlerts();
    db.addAuditEvent('FraudMCP', params.userRole || 'agent', 'MCP_CALL:get_active_alerts', `Retrieved ${alerts.length} active fraud alerts`, true, 'success', 'FraudMCP');
    return alerts;
  }

  // 2. calculate_fraud_score
  public static calculateFraudScore(params: { transactionId: string; userRole?: string }) {
    const schema = z.object({ transactionId: z.string() });
    const parsed = schema.parse(params);
    const result = FraudDetectionEngine.evaluateTransaction(parsed.transactionId);

    db.addAuditEvent('FraudMCP', params.userRole || 'agent', 'MCP_CALL:calculate_fraud_score', `Calculated risk score ${result.riskScore}/100 for Txn ${parsed.transactionId}`, true, 'success', 'FraudMCP');
    return result;
  }

  // 3. get_device_risk
  public static getDeviceRisk(params: { deviceHash: string; userRole?: string }) {
    const schema = z.object({ deviceHash: z.string() });
    const parsed = schema.parse(params);
    const risk = db.getDeviceRisk(parsed.deviceHash);

    db.addAuditEvent('FraudMCP', params.userRole || 'agent', 'MCP_CALL:get_device_risk', `Inspected device risk profile for ${parsed.deviceHash}`, true, 'success', 'FraudMCP');

    if (!risk) {
      return { deviceHash: parsed.deviceHash, isNewDevice: true, riskScore: 50, knownAssociatedCustomers: [] };
    }
    return risk;
  }

  // 4. get_related_entities (Graph relationship explorer)
  public static getRelatedEntities(params: { customerId: string; userRole?: string }) {
    const schema = z.object({ customerId: z.string() });
    const parsed = schema.parse(params);
    const customer = db.getCustomer(parsed.customerId);
    const accounts = db.getCustomerAccounts(parsed.customerId);
    const txns = db.getRecentTransactions(parsed.customerId, 5);

    const devices = Array.from(new Set(txns.map(t => t.deviceHash)));
    const ips = Array.from(new Set(txns.map(t => t.ipHash)));
    const merchants = Array.from(new Set(txns.map(t => t.merchantName)));

    db.addAuditEvent('FraudMCP', params.userRole || 'agent', 'MCP_CALL:get_related_entities', `Graph lookup for entities connected to customer ${parsed.customerId}`, true, 'success', 'FraudMCP');

    return {
      customerNode: { id: customer?.id, name: customer?.name, riskTier: customer?.riskTier },
      accountNodes: accounts.map(a => ({ id: a.accountId, mask: a.accountNumberMasked })),
      deviceNodes: devices.map(d => ({ id: d, risk: db.getDeviceRisk(d)?.riskScore || 20 })),
      ipNodes: ips.map(ip => ({ id: ip, flag: ip.includes('Lagos') ? 'GEO_MISMATCH' : 'NORMAL' })),
      merchantNodes: merchants.map(m => ({ name: m }))
    };
  }

  // 5. get_customer_risk_profile
  public static getCustomerRiskProfile(params: { customerId: string; userRole?: string }) {
    const schema = z.object({ customerId: z.string() });
    const parsed = schema.parse(params);
    const customer = db.getCustomer(parsed.customerId);
    const txns = db.getRecentTransactions(parsed.customerId, 20);
    const cases = db.getCustomerCases(parsed.customerId);

    db.addAuditEvent('FraudMCP', params.userRole || 'agent', 'MCP_CALL:get_customer_risk_profile', `Assessed comprehensive risk profile for ${parsed.customerId}`, true, 'success', 'FraudMCP');

    if (!customer) throw new Error(`Customer ${parsed.customerId} not found`);

    const flaggedCount = txns.filter(t => t.status === 'flagged').length;

    return {
      customerId: customer.id,
      riskTier: customer.riskTier,
      kycStatus: customer.kycStatus,
      historicalAvgTxnAmount: customer.avgTransactionAmount,
      totalTxnsChecked: txns.length,
      flaggedTxnsCount: flaggedCount,
      priorFraudCases: cases.length,
      travelNoticeActive: customer.travelNoticeActive,
      travelDestination: customer.travelDestination
    };
  }

  // 6. get_fraud_evidence
  public static getFraudEvidence(params: { alertId: string; userRole?: string }) {
    const schema = z.object({ alertId: z.string() });
    const parsed = schema.parse(params);
    const alert = db.getAlert(parsed.alertId);

    db.addAuditEvent('FraudMCP', params.userRole || 'agent', 'MCP_CALL:get_fraud_evidence', `Retrieved fraud evidence package for alert ${parsed.alertId}`, true, 'success', 'FraudMCP');

    if (!alert) throw new Error(`Alert ${parsed.alertId} not found`);
    return alert.evidence;
  }
}
