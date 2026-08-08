import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SseCursorStore {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  String _key(String conversationId) => 'sse_cursor_$conversationId';

  Future<String?> getLastEventId(String conversationId) async {
    return await _storage.read(key: _key(conversationId));
  }

  Future<void> saveLastEventId(String conversationId, String eventId) async {
    await _storage.write(key: _key(conversationId), value: eventId);
  }

  Future<void> clearConversation(String conversationId) async {
    await _storage.delete(key: _key(conversationId));
  }
}
