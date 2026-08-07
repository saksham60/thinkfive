import { db } from '../db';
import { MCPGateway } from '../mcp/mcpGateway';

export interface WorkflowTask {
  workflowId: string;
  type: 'FRAUD_DISPUTE_SLA' | 'CARD_FREEZE_APPROVAL' | 'A2A_REMOTE_INVESTIGATION';
  status: 'RUNNING' | 'WAITING_FOR_HUMAN' | 'COMPLETED' | 'ESCALATED';
  caseId?: string;
  alertId?: string;
  createdAt: string;
  slaDeadline: string;
}

export class TemporalWorkflowAdapter {
  private static activeWorkflows = new Map<string, WorkflowTask>();

  public static startFraudDisputeWorkflow(caseId: string, priority: string) {
    const workflowId = `WF-SLA-${caseId}`;
    const deadlineMs = priority === 'critical' ? 15 * 60 * 1000 : 60 * 60 * 1000;

    const task: WorkflowTask = {
      workflowId,
      type: 'FRAUD_DISPUTE_SLA',
      status: 'RUNNING',
      caseId,
      createdAt: new Date().toISOString(),
      slaDeadline: new Date(Date.now() + deadlineMs).toISOString()
    };

    this.activeWorkflows.set(workflowId, task);

    db.addAuditEvent(
      'TemporalWorkflowEngine',
      'system',
      'START_WORKFLOW',
      `Temporal SLA workflow ${workflowId} initiated for Case ${caseId}. SLA Deadline: ${task.slaDeadline}`,
      true,
      'success'
    );

    return task;
  }

  // A2A Remote Fraud Agent Demonstration Endpoint
  public static async invokeRemoteA2AFraudAgent(transactionId: string): Promise<any> {
    db.addAuditEvent(
      'A2A_Gateway',
      'A2A_RemoteAgent',
      'A2A_INVOKE',
      `Invoking Remote Fraud Investigation Agent via Agent-to-Agent (A2A) Protocol for Txn ${transactionId}`,
      true,
      'success'
    );

    // Call Fraud MCP server via Gateway
    const fraudScore = await MCPGateway.executeTool(
      'FraudMCP',
      'calculate_fraud_score',
      { transactionId },
      { userRole: 'agent' }
    );

    const related = await MCPGateway.executeTool(
      'FraudMCP',
      'get_related_entities',
      { customerId: 'CUST-1001' },
      { userRole: 'agent' }
    );

    return {
      a2aStatus: 'SUCCESS',
      protocolVersion: 'A2A-v1.0-REGIONAL',
      agentId: 'remote-fraud-risk-specialist-01',
      evaluation: fraudScore,
      graphEntities: related,
      signature: 'SIG-A2A-VERIFIED-ED25519'
    };
  }

  public static getActiveWorkflows(): WorkflowTask[] {
    return Array.from(this.activeWorkflows.values());
  }
}
