import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/sse/sse_parser.dart';

void main() {
  group('SseParser', () {
    test('parses single complete event', () {
      final parser = SseParser();
      final chunks = parser.parseChunk('event: message\ndata: hello\n\n');
      expect(chunks.length, 1);
      expect(chunks[0].event, 'message');
      expect(chunks[0].data, 'hello');
    });

    test('parses fragmented events', () {
      final parser = SseParser();
      var chunks = parser.parseChunk('event: mes');
      expect(chunks.length, 0);
      chunks = parser.parseChunk('sage\ndata: ');
      expect(chunks.length, 0);
      chunks = parser.parseChunk('world\n\n');
      expect(chunks.length, 1);
      expect(chunks[0].event, 'message');
      expect(chunks[0].data, 'world');
    });

    test('parses multiple events in one chunk', () {
      final parser = SseParser();
      final chunks = parser.parseChunk('event: e1\ndata: d1\n\nevent: e2\ndata: d2\n\n');
      expect(chunks.length, 2);
      expect(chunks[0].event, 'e1');
      expect(chunks[0].data, 'd1');
      expect(chunks[1].event, 'e2');
      expect(chunks[1].data, 'd2');
    });
  });
}
