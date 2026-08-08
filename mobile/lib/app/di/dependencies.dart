import '../../core/config/app_config.dart';
import '../../core/network/api_client.dart';
import '../../features/auth/domain/repositories/auth_repository.dart';
import '../../features/auth/data/repositories/remote_auth_repository.dart';
import '../../features/auth/data/repositories/fixture_auth_repository.dart';
import '../../features/dashboard/domain/repositories/dashboard_repository.dart';
import '../../features/dashboard/data/repositories/remote_dashboard_repository.dart';
import '../../features/dashboard/data/repositories/fixture_dashboard_repository.dart';
import '../../features/chat/domain/repositories/chat_repository.dart';
import '../../features/chat/data/repositories/remote_chat_repository.dart';
import '../../features/chat/data/repositories/fixture_chat_repository.dart';
import '../../features/alerts/domain/repositories/alert_repository.dart';
import '../../features/alerts/data/repositories/remote_alert_repository.dart';
import '../../features/alerts/data/repositories/fixture_alert_repository.dart';
import '../../features/cases/domain/repositories/case_repository.dart';
import '../../features/cases/data/repositories/remote_case_repository.dart';
import '../../features/cases/data/repositories/fixture_case_repository.dart';

class Dependencies {
  static late final ApiClient apiClient;
  static late final AuthRepository authRepository;
  static late final DashboardRepository dashboardRepository;
  static late final ChatRepository chatRepository;
  static late final AlertRepository alertRepository;
  static late final CaseRepository caseRepository;

  static Future<void> init() async {
    apiClient = ApiClient();
    await apiClient.init();

    if (AppConfig.useFixtures) {
      authRepository = FixtureAuthRepository();
      dashboardRepository = FixtureDashboardRepository();
      chatRepository = FixtureChatRepository();
      alertRepository = FixtureAlertRepository();
      caseRepository = FixtureCaseRepository();
    } else {
      authRepository = RemoteAuthRepository(apiClient);
      dashboardRepository = RemoteDashboardRepository(apiClient);
      chatRepository = RemoteChatRepository(apiClient);
      alertRepository = RemoteAlertRepository(apiClient);
      caseRepository = RemoteCaseRepository(apiClient);
    }
  }
}
