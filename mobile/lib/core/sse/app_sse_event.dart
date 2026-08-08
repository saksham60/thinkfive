import 'package:equatable/equatable.dart';

abstract class AppSseEvent extends Equatable {
  final String id;
  const AppSseEvent(this.id);

  @override
  List<Object?> get props => [id];
}

class ChatAcceptedEvent extends AppSseEvent {
  const ChatAcceptedEvent(super.id);
}

class ChatCompletedEvent extends AppSseEvent {
  final String response;
  const ChatCompletedEvent(super.id, this.response);
  @override
  List<Object?> get props => [id, response];
}

class ChatFailedEvent extends AppSseEvent {
  final String error;
  const ChatFailedEvent(super.id, this.error);
  @override
  List<Object?> get props => [id, error];
}

class WorkflowInterruptedEvent extends AppSseEvent {
  const WorkflowInterruptedEvent(super.id);
}

class WorkflowResumedEvent extends AppSseEvent {
  const WorkflowResumedEvent(super.id);
}

class ApprovalRequestedEvent extends AppSseEvent {
  final String approvalId;
  final String caseId;
  const ApprovalRequestedEvent(super.id, this.approvalId, this.caseId);
  @override
  List<Object?> get props => [id, approvalId, caseId];
}

class AgentStartedEvent extends AppSseEvent {
  final String agentName;
  const AgentStartedEvent(super.id, this.agentName);
  @override
  List<Object?> get props => [id, agentName];
}

class ToolStartedEvent extends AppSseEvent {
  final String toolName;
  const ToolStartedEvent(super.id, this.toolName);
  @override
  List<Object?> get props => [id, toolName];
}

class FraudAssessmentEvent extends AppSseEvent {
  final Map<String, dynamic> data;
  const FraudAssessmentEvent(super.id, this.data);
  @override
  List<Object?> get props => [id, data];
}

class CaseCreatedEvent extends AppSseEvent {
  final String caseId;
  const CaseCreatedEvent(super.id, this.caseId);
  @override
  List<Object?> get props => [id, caseId];
}

class ApprovalResultEvent extends AppSseEvent {
  final String result;
  const ApprovalResultEvent(super.id, this.result);
  @override
  List<Object?> get props => [id, result];
}

class GenericEvent extends AppSseEvent {
  final String eventType;
  final Map<String, dynamic>? data;
  const GenericEvent(super.id, this.eventType, this.data);
  @override
  List<Object?> get props => [id, eventType, data];
}
