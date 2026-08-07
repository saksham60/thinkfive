import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../domain/entities/customer_dashboard.dart';
import '../../domain/repositories/dashboard_repository.dart';

class RemoteDashboardRepository implements DashboardRepository {
  final ApiClient _apiClient;

  RemoteDashboardRepository(this._apiClient);

  @override
  Future<CustomerDashboardEntity> getCustomerDashboard() async {
    final response = await _apiClient.dio.get(ApiEndpoints.customerDashboard);
    return CustomerDashboardEntity.fromJson(response.data);
  }
}
