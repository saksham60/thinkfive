import { z } from 'zod';
import { db } from '../db';

export class CaseMCPServer {
  public static readonly SERVER_NAME = 'CaseMCPServer';

  // 1. create_case
  public static createCase(params: {
    customerId: string;
    alertId?: string;
    transactionId?: string;
    title: string;
    description: string;
    priority?: 'critical' | 'high' | 'medium' | 'low';
    assignedTo?: string;
    userRole?: string;
  }) {
    const schema = z.object({
      customerId: z.string(),
      alertId: z.string().optional(),
      transactionId: z.string().optional(),
      title: z.string().min(3),
      description: z.string(),
      priority: z.enum(['critical', 'high', 'medium', 'low']).optional(),
      assignedTo: z.string().optional()
    });

    const parsed = schema.parse(params);

    const record = db.createCase({
      customerId: parsed.customerId,
      alertId: parsed.alertId,
      transactionId: parsed.transactionId,
      title: parsed.title,
      description: parsed.description,
      status: 'open',
      priority: parsed.priority || 'high',
      assignedTo: parsed.assignedTo || 'Unassigned - Fraud Ops Queue',
      notes: [
        {
          id: `NOTE-1`,
          author: 'System Agent',
          text: `Case auto-opened from fraud investigation workflow. Title: ${parsed.title}`,
          timestamp: new Date().toISOString()
        }
      ]
    });

    return record;
  }

  // 2. update_case
  public static updateCase(params: { caseId: string; status?: any; priority?: any; userRole?: string }) {
    const updated = db.updateCase(params.caseId, {
      ...(params.status ? { status: params.status } : {}),
      ...(params.priority ? { priority: params.priority } : {})
    });
    db.addAuditEvent('CaseMCP', params.userRole || 'agent', 'MCP_CALL:update_case', `Updated case ${params.caseId} status to ${params.status}`, true, 'success', 'CaseMCP');
    return updated;
  }

  // 3. assign_case
  public static assignCase(params: { caseId: string; analystName: string; userRole?: string }) {
    const updated = db.updateCase(params.caseId, { assignedTo: params.analystName });
    db.addAuditEvent('CaseMCP', params.userRole || 'agent', 'MCP_CALL:assign_case', `Assigned case ${params.caseId} to analyst ${params.analystName}`, true, 'success', 'CaseMCP');
    return updated;
  }

  // 4. add_case_note
  public static addCaseNote(params: { caseId: string; author: string; text: string; userRole?: string }) {
    const existing = db.getCases().find(c => c.caseId === params.caseId);
    if (!existing) throw new Error(`Case ${params.caseId} not found`);

    const newNote = {
      id: `NOTE-${Date.now()}`,
      author: params.author,
      text: params.text,
      timestamp: new Date().toISOString()
    };

    const updatedNotes = [...existing.notes, newNote];
    const updated = db.updateCase(params.caseId, { notes: updatedNotes });

    db.addAuditEvent('CaseMCP', params.userRole || 'agent', 'MCP_CALL:add_case_note', `Added investigation note to case ${params.caseId}`, true, 'success', 'CaseMCP');
    return updated;
  }

  // 5. request_approval (Human-in-the-Loop workflow trigger)
  public static requestApproval(params: {
    caseId: string;
    requestedBy: string;
    actionType: 'card_freeze' | 'account_block' | 'transaction_reversal';
    userRole?: string;
  }) {
    const existing = db.getCases().find(c => c.caseId === params.caseId);
    if (!existing) throw new Error(`Case ${params.caseId} not found`);

    const updated = db.updateCase(params.caseId, {
      status: 'pending_approval',
      approvalRequest: {
        requestedBy: params.requestedBy,
        actionType: params.actionType,
        status: 'pending',
        timestamp: new Date().toISOString()
      }
    });

    db.addAuditEvent(
      'CaseMCP',
      params.userRole || 'agent',
      'MCP_CALL:request_approval',
      `Approval requested for ${params.actionType} on Case ${params.caseId}`,
      true,
      'warning',
      'CaseMCP'
    );

    return updated;
  }

  // 6. send_customer_notification
  public static sendCustomerNotification(params: {
    customerId: string;
    channel: 'SMS' | 'EMAIL' | 'IN_APP_ALERT';
    message: string;
    userRole?: string;
  }) {
    const customer = db.getCustomer(params.customerId);
    db.addAuditEvent(
      'CaseMCP',
      params.userRole || 'agent',
      'MCP_CALL:send_customer_notification',
      `Sent ${params.channel} notification to Customer ${params.customerId}: "${params.message}"`,
      true,
      'success',
      'CaseMCP'
    );

    return {
      sent: true,
      recipient: customer ? customer.phone : params.customerId,
      channel: params.channel,
      timestamp: new Date().toISOString(),
      deliveredMessage: params.message
    };
  }
}
