import '../../domain/repositories/supervisor_repository.dart';
import '../../../../core/network/api_client.dart';

class RemoteSupervisorRepository implements SupervisorRepository {
  final ApiClient _apiClient;
  
  RemoteSupervisorRepository(this._apiClient);
  
  @override
  Future<Map<String, dynamic>> getMetrics() async {
    final response = await _apiClient.dio.get('/api/supervisor/metrics');
    return response.data as Map<String, dynamic>;
  }
  
  @override
  Future<List<dynamic>> getRuns() async {
    final response = await _apiClient.dio.get('/api/supervisor/runs');
    return response.data as List<dynamic>;
  }
  
  @override
  Future<List<dynamic>> getTraces(String runId) async {
    final response = await _apiClient.dio.get('/api/supervisor/runs/$runId/traces');
    return response.data as List<dynamic>;
  }
}
