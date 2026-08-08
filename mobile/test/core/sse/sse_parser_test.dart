import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/sse/sse_parser.dart';
import 'dart:convert';

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
      final chunks = parser.parseChunk(
        'event: e1\ndata: d1\n\nevent: e2\ndata: d2\n\n',
      );
      expect(chunks.length, 2);
      expect(chunks[0].event, 'e1');
      expect(chunks[0].data, 'd1');
      expect(chunks[1].event, 'e2');
      expect(chunks[1].data, 'd2');
    });

    test('parses multiline data', () {
      final parser = SseParser();
      final chunks = parser.parseChunk('data: line1\ndata: line2\n\n');
      expect(chunks.length, 1);
      expect(chunks[0].data, 'line1\nline2');
    });

    test('parses id field', () {
      final parser = SseParser();
      final chunks = parser.parseChunk('id: 123\ndata: test\n\n');
      expect(chunks.length, 1);
      expect(chunks[0].id, '123');
      expect(chunks[0].data, 'test');
    });

    test('parses retry field', () {
      final parser = SseParser();
      final chunks = parser.parseChunk('retry: 5000\ndata: test\n\n');
      expect(chunks.length, 1);
      expect(chunks[0].retry, 5000);
      expect(chunks[0].data, 'test');
    });

    test('handles comment heartbeat', () {
      final parser = SseParser();
      final chunks = parser.parseChunk(': heartbeat\n\n');
      expect(chunks.length, 0); // Comments are ignored
    });

    test('handles empty data', () {
      final parser = SseParser();
      final chunks = parser.parseChunk('event: empty\ndata:\n\n');
      expect(chunks.length, 1);
      expect(chunks[0].event, 'empty');
      expect(chunks[0].data, '');
    });

    test('handles CRLF input', () {
      final parser = SseParser();
      final chunks = parser.parseChunk('event: e1\r\ndata: d1\r\n\r\n');
      expect(chunks.length, 1);
      expect(chunks[0].event, 'e1');
      expect(chunks[0].data, 'd1');
    });

    test(
      'handles multibyte UTF-8 split across chunks safely with Utf8Decoder stream transformer',
      () async {
        const text = 'event: msg\ndata: ₹ and € and 🚀\n\n';
        final bytes = utf8.encode(text);

        // Split the bytes in the middle of a multibyte character (e.g. ₹ is 3 bytes)
        final chunk1 = bytes.sublist(0, 18);
        final chunk2 = bytes.sublist(18);

        final stream = Stream.fromIterable([chunk1, chunk2]);
        final stringStream = stream.cast<List<int>>().transform(
          const Utf8Decoder(allowMalformed: true),
        );

        final parser = SseParser();
        final events = <dynamic>[];

        await for (final stringChunk in stringStream) {
          events.addAll(parser.parseChunk(stringChunk));
        }

        expect(events.length, 1);
        expect(events[0].event, 'msg');
        expect(events[0].data, '₹ and € and 🚀');
      },
    );
  });
}
