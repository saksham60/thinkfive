class BackendEventTypes {
  // Connection
  static const String connectionReady = 'connection.ready';
  static const String heartbeat = 'heartbeat';

  // Chat
  static const String chatAccepted = 'chat.accepted';
  static const String chatCompleted = 'chat.completed';
  static const String chatFailed = 'chat.failed';

  // Agent
  static const String agentStarted = 'agent.started';
  static const String agentCompleted = 'agent.completed';
  static const String agentFailed = 'agent.failed';

  // Tool
  static const String agentToolStarted = 'agent.tool.started';
  static const String agentToolCompleted = 'agent.tool.completed';
  static const String agentToolFailed = 'agent.tool.failed';

  // Assistant
  static const String assistantDelta = 'assistant.delta';
  static const String assistantMessage = 'assistant.message';

  // Transaction
  static const String transactionDetected = 'transaction.detected';
  static const String transactionAssessed = 'transaction.assessed';

  // Fraud
  static const String fraudAssessmentCreated = 'fraud.assessment.created';
  static const String fraudAlertCreated = 'fraud.alert.created';
  static const String fraudAlertUpdated = 'fraud.alert.updated';

  // Case
  static const String caseCreated = 'case.created';
  static const String caseUpdated = 'case.updated';
  static const String caseNoteAdded = 'case.note.added';

  // Approval
  static const String approvalRequested = 'approval.requested';
  static const String approvalApproved = 'approval.approved';
  static const String approvalRejected = 'approval.rejected';

  // Workflow
  static const String workflowInterrupted = 'workflow.interrupted';
  static const String workflowResumed = 'workflow.resumed';

  // Card
  static const String cardStateUpdated = 'card.state.updated';

  // Notification
  static const String notificationCreated = 'notification.created';

  // System
  static const String systemWarning = 'system.warning';
}
