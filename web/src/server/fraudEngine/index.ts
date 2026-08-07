import { db } from '../db';
import { Transaction, FraudEvidence } from '../../types';

export interface FraudEngineResult {
  transactionId: string;
  riskScore: number; // 0 to 100
  priority: 'critical' | 'high' | 'medium' | 'low';
  modelScore: number;
  ruleScore: number;
  anomalyScore: number;
  graphScore: number;
  reasons: string[];
  recommendedAction: 'temporary_card_freeze' | 'customer_verification' | 'monitor' | 'none';
  humanApprovalRequired: boolean;
  evidence: FraudEvidence;
}

export class FraudDetectionEngine {
  public static evaluateTransaction(transactionId: string): FraudEngineResult {
    const txn = db.getTransaction(transactionId);
    if (!txn) {
      throw new Error(`Transaction ${transactionId} not found in Fraud Engine`);
    }

    const customer = db.getCustomer(txn.customerId);
    const deviceRisk = db.getDeviceRisk(txn.deviceHash);
    const recentTxns = db.getRecentTransactions(txn.customerId, 10);

    const reasons: string[] = [];
    const ruleViolations: string[] = [];

    // 1. RULE EVALUATION
    let rulePoints = 0;

    // Check customer average amount multiplier
    const avgAmount = customer ? customer.avgTransactionAmount : 50;
    const amountMultiplier = txn.amount / Math.max(avgAmount, 10);

    if (amountMultiplier > 10) {
      rulePoints += 35;
      const multiplierText = amountMultiplier.toFixed(1);
      reasons.push(`Transaction amount (₹${txn.amount.toFixed(2)}) is ${multiplierText}x higher than customer average (₹${avgAmount.toFixed(2)})`);
      ruleViolations.push('RULE_HIGH_AMOUNT_MULTIPLIER');
    } else if (amountMultiplier > 4) {
      rulePoints += 15;
      reasons.push(`Transaction amount (₹${txn.amount.toFixed(2)}) significantly exceeds typical spending pattern`);
      ruleViolations.push('RULE_ELEVATED_AMOUNT');
    }

    // New device & Location mismatch check
    if (deviceRisk) {
      if (deviceRisk.isNewDevice) {
        rulePoints += 25;
        reasons.push(`Unrecognized new device fingerprint (${txn.deviceHash})`);
        ruleViolations.push('RULE_NEW_DEVICE');
      }

      if (deviceRisk.failedLogins24h > 3) {
        rulePoints += 20;
        reasons.push(`${deviceRisk.failedLogins24h} failed authentication attempts recorded in last 24 hours`);
        ruleViolations.push('RULE_FAILED_LOGINS_SPIKE');
      }

      // Graph network cluster check (shared devices)
      if (deviceRisk.knownAssociatedCustomers.length > 1) {
        rulePoints += 30;
        reasons.push(`Device & IP hash shared across ${deviceRisk.knownAssociatedCustomers.length} distinct customer accounts (Potential Fraud Ring)`);
        ruleViolations.push('RULE_GRAPH_SHARED_DEVICE_CLUSTER');
      }
    }

    // Velocity check (multiple txns in 15 mins)
    const fifteenMinsAgo = new Date(new Date(txn.timestamp).getTime() - 15 * 60 * 1000);
    const rapidTxns = recentTxns.filter(t => new Date(t.timestamp) >= fifteenMinsAgo);
    if (rapidTxns.length >= 3) {
      rulePoints += 20;
      reasons.push(`Rapid transaction velocity: ${rapidTxns.length} transactions initiated within 15 minutes`);
      ruleViolations.push('RULE_RAPID_VELOCITY');
    }

    // Location / Geo Mismatch Check
    if (txn.location.includes('Lagos') || txn.location.includes('Geo-Mismatch') || txn.location.includes('Unrecognized')) {
      rulePoints += 25;
      reasons.push(`Geographical IP mismatch: ${txn.location}`);
      ruleViolations.push('RULE_GEO_MISMATCH');
    }

    // Special Handling for Travel False Positives
    if (customer && customer.travelNoticeActive && customer.travelDestination) {
      if (txn.location.toLowerCase().includes(customer.travelDestination.toLowerCase().split(',')[0])) {
        // Customer explicitly logged travel notice! Reduce false positive score.
        rulePoints = Math.max(10, rulePoints - 50);
        reasons.push(`[SUPPRESSED] Location matches active customer travel notice for ${customer.travelDestination}`);
      }
    }

    const ruleScore = Math.min(1.0, rulePoints / 100);

    // 2. ML & ISOLATION FOREST ANOMALY SIMULATION
    const mlScore = Math.min(0.99, ruleScore * 0.9 + (txn.amount > 1000 ? 0.15 : 0.05));
    const anomalyScore = Math.min(0.98, ruleScore * 0.85 + (deviceRisk?.isNewDevice ? 0.2 : 0.05));
    const graphScore = deviceRisk && deviceRisk.knownAssociatedCustomers.length > 1 ? 0.92 : 0.20;

    // Combined Weighted Risk Score (0 - 100)
    const combinedWeight = (ruleScore * 0.35) + (mlScore * 0.25) + (anomalyScore * 0.20) + (graphScore * 0.20);
    let riskScore = Math.round(combinedWeight * 100);

    // Clamp score
    if (reasons.some(r => r.includes('SUPPRESSED'))) {
      riskScore = Math.min(35, riskScore);
    }

    // Priority & Action Determination
    let priority: 'critical' | 'high' | 'medium' | 'low' = 'low';
    let recommendedAction: 'temporary_card_freeze' | 'customer_verification' | 'monitor' | 'none' = 'none';

    if (riskScore >= 80) {
      priority = 'critical';
      recommendedAction = 'temporary_card_freeze';
    } else if (riskScore >= 60) {
      priority = 'high';
      recommendedAction = 'customer_verification';
    } else if (riskScore >= 35) {
      priority = 'medium';
      recommendedAction = 'monitor';
    }

    const humanApprovalRequired = riskScore >= 75 || recommendedAction === 'temporary_card_freeze';

    const evidence: FraudEvidence = {
      evidenceId: `EVD-${Math.floor(1000 + Math.random() * 9000)}`,
      transactionId,
      ruleViolations,
      mlScore: parseFloat(mlScore.toFixed(2)),
      anomalyScore: parseFloat(anomalyScore.toFixed(2)),
      graphScore: parseFloat(graphScore.toFixed(2)),
      reasons,
      graphClusterInfo: {
        sharedDeviceCustomers: deviceRisk ? deviceRisk.knownAssociatedCustomers.length : 1,
        sharedIpCustomers: deviceRisk ? deviceRisk.knownAssociatedCustomers.length + 1 : 1,
        suspiciousBeneficiaryLinks: riskScore > 70
      }
    };

    return {
      transactionId,
      riskScore,
      priority,
      modelScore: parseFloat(mlScore.toFixed(2)),
      ruleScore: parseFloat(ruleScore.toFixed(2)),
      anomalyScore: parseFloat(anomalyScore.toFixed(2)),
      graphScore: parseFloat(graphScore.toFixed(2)),
      reasons,
      recommendedAction,
      humanApprovalRequired,
      evidence
    };
  }
}
