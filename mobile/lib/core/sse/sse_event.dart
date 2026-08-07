class SseEvent {
  final String? id;
  final String? event;
  final String data;
  final int? retry;

  SseEvent({this.id, this.event, required this.data, this.retry});

  @override
  String toString() {
    return 'SseEvent(id: $id, event: $event, data: $data, retry: $retry)';
  }
}
