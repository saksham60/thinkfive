enum MessageRole { user, ai, system, progress }

class ChatMessage {
  final String id;
  final String text;
  final MessageRole role;
  final dynamic payload;
  final DateTime timestamp;

  ChatMessage({
    required this.id,
    required this.text,
    required this.role,
    this.payload,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}
