import { WebSocketServer, WebSocket } from 'ws';
import { Server as HttpServer } from 'http';
import { db } from './db';
import { FraudDetectionEngine } from './fraudEngine';
import { FraudAlert, Transaction } from '../types';

export class LiveAlertWebSocketServer {
  private static wss: WebSocketServer | null = null;
  private static clients: Set<WebSocket> = new Set();

  public static initialize(server: HttpServer) {
    this.wss = new WebSocketServer({ server, path: '/ws' });

    this.wss.on('connection', (ws: WebSocket) => {
      this.clients.add(ws);
      console.log(`[WebSocket] Client connected. Total active connections: ${this.clients.size}`);

      // Send initial active alerts payload
      const initialPayload = {
        type: 'INITIAL_STATE',
        alerts: db.getActiveAlerts(),
        incidents: db.getIncidents(),
        auditEvents: db.getAuditEvents().slice(0, 15),
        cases: db.getCases()
      };
      ws.send(JSON.stringify(initialPayload));

      ws.on('close', () => {
        this.clients.delete(ws);
        console.log(`[WebSocket] Client disconnected. Total active connections: ${this.clients.size}`);
      });
    });
  }

  public static broadcast(event: { type: string; payload: any }) {
    const data = JSON.stringify(event);
    for (const client of this.clients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(data);
      }
    }
  }

  // Live Synthetic Event Generator Trigger
  public static triggerSyntheticScenario(scenarioType: string): FraudAlert | Transaction {
    const now = new Date().toISOString();
    const randomId = Math.floor(1000 + Math.random() * 9000);

    let customerId = 'CUST-1001';
    let customerName = 'Priya Sharma';

    if (scenarioType === 'travel_false_positive') {
      customerId = 'CUST-1002';
      customerName = 'Rahul Verma';
    } else if (scenarioType === 'fraud_ring') {
      customerId = 'CUST-1003';
      customerName = 'Anita Desai';
    }

    const txnId = `TXN-${randomId}`;

    let amount = 1200.00;
    let merchantName = 'Luxury Jewelry Boutique';
    let location = 'Miami, FL (New Device)';
    let deviceHash = `DEV-SIM-${randomId}`;
    let ipHash = `IP-192-0-${Math.floor(Math.random() * 255)}-10`;

    if (scenarioType === 'stolen_card') {
      amount = 3890.00;
      merchantName = 'Global Crypto Hardware Exchange';
      location = 'Eastern Europe (IP Geo-Mismatch)';
      deviceHash = 'DEV-RING-X992';
      ipHash = 'IP-45-133-19-88';
    } else if (scenarioType === 'travel_false_positive') {
      amount = 410.00;
      merchantName = 'London Transit & Hotel';
      location = 'London, UK';
      deviceHash = 'DEV-RAHUL-MOBILE';
      ipHash = 'IP-82-14-10-22';
    } else if (scenarioType === 'fraud_ring') {
      amount = 5400.00;
      merchantName = 'Unverified Offshore Wire Service';
      location = 'Unrecognized TOR Gateway';
      deviceHash = 'DEV-RING-X992';
      ipHash = 'IP-45-133-19-88';
    }

    const newTxn: Transaction = {
      id: txnId,
      accountId: 'ACC-8801',
      customerId,
      cardId: 'CARD-4832',
      amount,
      currency: 'INR',
      merchantName,
      merchantCategory: 'Electronics & Luxury Goods',
      mcc: '5944',
      location,
      timestamp: now,
      deviceHash,
      ipHash,
      isUnrecognized: scenarioType !== 'travel_false_positive',
      status: 'flagged'
    };

    db.addTransaction(newTxn);

    // Evaluate via Fraud Engine
    const evalResult = FraudDetectionEngine.evaluateTransaction(txnId);

    const newAlert: FraudAlert = {
      alertId: `ALT-${randomId}`,
      transactionId: txnId,
      customerId,
      customerName,
      amount,
      merchantName,
      timestamp: now,
      riskScore: evalResult.riskScore,
      priority: evalResult.priority,
      status: 'open',
      reasons: evalResult.reasons,
      recommendedAction: evalResult.recommendedAction,
      humanApprovalRequired: evalResult.humanApprovalRequired,
      evidence: evalResult.evidence
    };

    db.addAlert(newAlert);

    db.addAuditEvent(
      'EventSimulator',
      'system',
      'TRIGGER_SYNTHETIC_SCENARIO',
      `Simulated ${scenarioType.toUpperCase()} event for Txn ${txnId}. Risk Score: ${evalResult.riskScore}/100`,
      true,
      evalResult.riskScore > 75 ? 'warning' : 'success'
    );

    // Broadcast WebSocket update
    const incidentId = `INC-${newAlert.alertId.replace('ALT-', '')}`;
    const incident = db.getIncident(incidentId);

    this.broadcast({
      type: 'NEW_FRAUD_ALERT',
      payload: {
        alert: newAlert,
        auditEvent: db.getAuditEvents()[0]
      }
    });

    if (incident) {
      this.broadcast({
        type: 'NEW_INCIDENT',
        payload: { incident }
      });
    }

    return newAlert;
  }
}
