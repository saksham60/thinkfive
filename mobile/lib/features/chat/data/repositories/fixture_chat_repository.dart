import 'dart:async';
import '../../domain/repositories/chat_repository.dart';

class FixtureChatRepository implements ChatRepository {
  @override
  Future<String> submitMessage(
    String message, {
    String? conversationId,
    String? transactionId,
  }) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return conversationId ?? 'conv_sim_123';
  }
}
