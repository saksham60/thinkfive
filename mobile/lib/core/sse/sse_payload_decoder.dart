import 'dart:convert';
import 'sse_event.dart';
import 'app_sse_event.dart';
import 'backend_event_types.dart';

class SsePayloadDecoder {
  static AppSseEvent decode(SseEvent event) {
    final id = event.id ?? '';
    final eventType = event.event;
    if (eventType == null) return GenericEvent(id, 'unknown', null);

    Map<String, dynamic> data = {};
    if (event.data.isNotEmpty) {
      try {
        final decoded = jsonDecode(event.data);
        if (decoded is Map<String, dynamic>) {
          if (decoded.containsKey('payload')) {
            if (decoded['payload'] is Map<String, dynamic>) {
              data = decoded['payload'] as Map<String, dynamic>;
            } else if (decoded['payload'] is String) {
              data = {'message': decoded['payload']};
            }
          } else {
            data = decoded;
          }
        }
      } catch (_) {
        data = {'message': event.data};
      }
    }

    switch (eventType) {
      case BackendEventTypes.chatAccepted:
        return ChatAcceptedEvent(id);
      case BackendEventTypes.chatCompleted:
        final response =
            data['response']?.toString() ??
            data['message']?.toString() ??
            'Chat completed';
        return ChatCompletedEvent(id, response);
      case BackendEventTypes.chatFailed:
        final error =
            data['error']?.toString() ??
            data['message']?.toString() ??
            'Chat failed';
        return ChatFailedEvent(id, error);
      case BackendEventTypes.agentStarted:
        final agentName = data['agent_name']?.toString() ?? 'Agent';
        return AgentStartedEvent(id, agentName);
      case BackendEventTypes.agentToolStarted:
        final toolName = data['tool_name']?.toString() ?? 'Tool';
        return ToolStartedEvent(id, toolName);
      case BackendEventTypes.fraudAssessmentCreated:
        return FraudAssessmentEvent(id, data);
      case BackendEventTypes.caseCreated:
        final caseId = data['case_id']?.toString() ?? 'Unknown Case';
        return CaseCreatedEvent(id, caseId);
      case BackendEventTypes.approvalRequested:
        final approvalId = data['approval_id']?.toString() ?? '';
        final caseId = data['case_id']?.toString() ?? '';
        return ApprovalRequestedEvent(id, approvalId, caseId);
      case BackendEventTypes.workflowInterrupted:
        return WorkflowInterruptedEvent(id);
      case BackendEventTypes.workflowResumed:
        return WorkflowResumedEvent(id);
      case BackendEventTypes.approvalApproved:
        return ApprovalResultEvent(id, 'Approved');
      case BackendEventTypes.approvalRejected:
        return ApprovalResultEvent(id, 'Rejected');
      default:
        return GenericEvent(id, eventType, data);
    }
  }
}
