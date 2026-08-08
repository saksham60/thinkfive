import 'dart:async';
import 'dart:convert';
import 'sse_event.dart';
import 'i_sse_client.dart';
import 'app_sse_event.dart';
import 'sse_payload_decoder.dart';
import 'backend_event_types.dart';

class FixtureSseClient implements ISseClient {
  final String conversationId;
  final _controller = StreamController<AppSseEvent>.broadcast();
  bool _isClosed = false;

  FixtureSseClient(this.conversationId) {
    _startSimulatedStream();
  }

  @override
  Stream<AppSseEvent> get stream => _controller.stream;

  void _startSimulatedStream() async {
    final sequence = [
      {
        'event': BackendEventTypes.agentStarted,
        'data': jsonEncode({
          'payload': {'agent_name': 'Risk Agent'},
        }),
      },
      {
        'event': BackendEventTypes.agentToolStarted,
        'data': jsonEncode({
          'payload': {'tool_name': 'banking_lookup'},
        }),
      },
      {
        'event': BackendEventTypes.agentToolStarted,
        'data': jsonEncode({
          'payload': {'tool_name': 'fraud_assessment'},
        }),
      },
      {
        'event': BackendEventTypes.fraudAssessmentCreated,
        'data': jsonEncode({
          'payload': {
            'risk_score': 85,
            'severity': 'HIGH',
            'reasons': ['Unusual location'],
          },
        }),
      },
      {
        'event': BackendEventTypes.caseCreated,
        'data': jsonEncode({
          'payload': {'case_id': 'c_sim_1', 'status': 'INVESTIGATING'},
        }),
      },
      {
        'event': BackendEventTypes.approvalRequested,
        'data': jsonEncode({
          'payload': {'approval_id': 'appr_sim_1', 'case_id': 'c_sim_1'},
        }),
      },
      {'event': BackendEventTypes.workflowInterrupted, 'data': ''},
    ];

    for (int i = 0; i < sequence.length; i++) {
      if (_isClosed) return;
      await Future.delayed(const Duration(milliseconds: 1500));
      if (_isClosed) return;

      final rawEvent = SseEvent(
        id: 'msg_$i',
        event: sequence[i]['event'],
        data: sequence[i]['data']!,
      );
      _controller.add(SsePayloadDecoder.decode(rawEvent));
    }
  }

  @override
  void close() {
    _isClosed = true;
    _controller.close();
  }
}
