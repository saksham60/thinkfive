import 'dart:async';
import 'app_sse_event.dart';

abstract class ISseClient {
  Stream<AppSseEvent> get stream;
  void close();
}
