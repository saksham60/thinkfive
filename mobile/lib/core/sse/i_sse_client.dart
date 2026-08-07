import 'dart:async';
import 'sse_event.dart';

abstract class ISseClient {
  Stream<SseEvent> get stream;
  void close();
}
