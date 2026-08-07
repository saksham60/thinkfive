import 'sse_event.dart';

class SseParser {
  String _buffer = '';

  /// Parse incoming string chunk (potentially fragmented) and return any complete events.
  List<SseEvent> parseChunk(String chunk) {
    _buffer += chunk;
    final events = <SseEvent>[];

    while (true) {
      // Events are separated by double newline \n\n or \r\n\r\n
      int doubleNewlineIndex = _buffer.indexOf('\n\n');
      int doubleRnIndex = _buffer.indexOf('\r\n\r\n');
      
      int endIndex = -1;
      int separatorLen = 0;
      
      if (doubleNewlineIndex != -1 && doubleRnIndex != -1) {
        if (doubleNewlineIndex < doubleRnIndex) {
          endIndex = doubleNewlineIndex;
          separatorLen = 2;
        } else {
          endIndex = doubleRnIndex;
          separatorLen = 4;
        }
      } else if (doubleNewlineIndex != -1) {
        endIndex = doubleNewlineIndex;
        separatorLen = 2;
      } else if (doubleRnIndex != -1) {
        endIndex = doubleRnIndex;
        separatorLen = 4;
      }

      if (endIndex == -1) {
        // No complete event yet
        break;
      }

      final eventString = _buffer.substring(0, endIndex);
      _buffer = _buffer.substring(endIndex + separatorLen);
      
      final parsedEvent = _parseEvent(eventString);
      if (parsedEvent != null) {
        events.add(parsedEvent);
      }
    }

    return events;
  }

  SseEvent? _parseEvent(String eventString) {
    if (eventString.isEmpty) return null;
    
    final lines = eventString.split(RegExp(r'\r?\n'));
    String? id;
    String? event;
    String data = '';
    int? retry;

    for (final line in lines) {
      if (line.isEmpty || line.startsWith(':')) {
        // Comment or empty line (e.g. heartbeat)
        continue;
      }

      final colonIndex = line.indexOf(':');
      if (colonIndex == -1) {
        // Sometimes a line without colon is treated as the field name with empty value
        if (line == 'data') data += (data.isEmpty ? '' : '\n');
        continue;
      }

      final field = line.substring(0, colonIndex);
      // Skip leading space of value if present
      final valueStartIndex = (colonIndex + 1 < line.length && line[colonIndex + 1] == ' ') 
          ? colonIndex + 2 
          : colonIndex + 1;
      
      final value = line.substring(valueStartIndex);

      switch (field) {
        case 'id':
          id = value;
          break;
        case 'event':
          event = value;
          break;
        case 'data':
          data += (data.isEmpty ? value : '\n$value');
          break;
        case 'retry':
          retry = int.tryParse(value);
          break;
      }
    }

    if (id == null && event == null && data.isEmpty && retry == null) {
      return null;
    }

    return SseEvent(id: id, event: event, data: data, retry: retry);
  }
}
