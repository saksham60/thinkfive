import 'dart:async';
import 'dart:convert';
import 'sse_event.dart';
import 'i_sse_client.dart';

class FixtureSseClient implements ISseClient {
  final String conversationId;
  final _controller = StreamController<SseEvent>.broadcast();
  bool _isClosed = false;

  FixtureSseClient(this.conversationId) {
    _startSimulatedStream();
  }

  @override
  Stream<SseEvent> get stream => _controller.stream;

  void _startSimulatedStream() async {
    final sequence = [
      {'event': 'agent_started', 'data': 'agent started'},
      {'event': 'tool_call', 'data': 'banking lookup'},
      {'event': 'tool_call', 'data': 'fraud assessment'},
      {'event': 'fraud_assessment', 'data': jsonEncode({'risk_score': 85, 'severity': 'HIGH', 'reasons': ['Unusual location']})},
      {'event': 'case_created', 'data': jsonEncode({'case_id': 'c_sim_1', 'status': 'INVESTIGATING'})},
      {'event': 'waiting_for_human', 'data': 'A human reviewer is required before this action can continue.'},
    ];

    for (int i = 0; i < sequence.length; i++) {
      if (_isClosed) return;
      await Future.delayed(const Duration(milliseconds: 1500));
      if (_isClosed) return;
      
      _controller.add(SseEvent(
        id: 'msg_$i',
        event: sequence[i]['event'],
        data: sequence[i]['data']!,
      ));
    }
  }

  @override
  void close() {
    _isClosed = true;
    _controller.close();
  }
}
