import 'i_sse_client.dart';
import 'sse_client.dart';
import 'fixture_sse_client.dart';
import '../network/api_client.dart';
import '../network/api_endpoints.dart';
import '../config/app_config.dart';

class SseClientFactory {
  static ISseClient create(ApiClient apiClient, String conversationId) {
    if (AppConfig.useFixtures) {
      return FixtureSseClient(conversationId);
    }
    return SseClient(apiClient, AppConfig.apiBaseUrl + ApiEndpoints.sse(conversationId));
  }
}
