export interface ServerEvent {
  type: string;
  payload: Record<string, unknown>;
  id?: string;
}

export const serverEventTypes = [
  'connection.ready', 'heartbeat', 'chat.accepted', 'chat.completed', 'chat.failed',
  'agent.started', 'agent.completed', 'agent.failed',
  'agent.tool.started', 'agent.tool.completed', 'agent.tool.failed',
  'assistant.delta', 'assistant.message',
  'transaction.detected', 'transaction.assessed',
  'fraud.assessment.created', 'fraud.alert.created', 'fraud.alert.updated',
  'case.created', 'case.updated', 'case.note.added',
  'approval.requested', 'approval.approved', 'approval.rejected',
  'workflow.interrupted', 'workflow.resumed', 'card.state.updated',
  'notification.created', 'system.warning',
] as const;
