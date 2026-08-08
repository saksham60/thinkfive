abstract class ChatRepository {
  Future<String> submitMessage(
    String message, {
    String? conversationId,
    String? transactionId,
  });
}
