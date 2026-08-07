import '../../domain/repositories/chat_repository.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_endpoints.dart';

class RemoteChatRepository implements ChatRepository {
  final ApiClient _apiClient;
  
  RemoteChatRepository(this._apiClient);
  
  @override
  Future<String> submitMessage(String message, {String? conversationId, String? transactionId}) async {
    final response = await _apiClient.dio.post(
      ApiEndpoints.chat,
      data: {
        'message': message,
        if (conversationId != null) 'conversation_id': conversationId,
        if (transactionId != null) 'transaction_id': transactionId,
      },
    );
    
    return response.data['conversation_id'] as String;
  }
}
