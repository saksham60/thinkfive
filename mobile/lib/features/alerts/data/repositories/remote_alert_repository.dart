import '../../domain/repositories/alert_repository.dart';
import '../../domain/entities/fraud_alert.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_endpoints.dart';

class RemoteAlertRepository implements AlertRepository {
  final ApiClient _apiClient;
  
  RemoteAlertRepository(this._apiClient);
  
  @override
  Future<List<FraudAlertEntity>> getAlerts() async {
    final response = await _apiClient.dio.get(ApiEndpoints.alerts);
    return (response.data as List).map((e) => FraudAlertEntity.fromJson(e)).toList();
  }
  
  @override
  Future<FraudAlertEntity> getAlertDetail(String id) async {
    final response = await _apiClient.dio.get(ApiEndpoints.alertDetail(id));
    return FraudAlertEntity.fromJson(response.data);
  }
}
