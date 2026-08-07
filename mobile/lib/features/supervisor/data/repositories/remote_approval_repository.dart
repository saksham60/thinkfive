import '../../domain/repositories/approval_repository.dart';
import '../../domain/entities/approval.dart';
import '../../../../core/network/api_client.dart';

class RemoteApprovalRepository implements ApprovalRepository {
  final ApiClient _apiClient;
  
  RemoteApprovalRepository(this._apiClient);
  
  @override
  Future<List<ApprovalEntity>> getPendingApprovals() async {
    final response = await _apiClient.dio.get('/api/approvals/pending');
    return (response.data as List).map((e) => ApprovalEntity.fromJson(e)).toList();
  }
  
  @override
  Future<void> approve(String id) async {
    await _apiClient.dio.post('/api/approvals/$id/approve');
  }
  
  @override
  Future<void> reject(String id, String reason) async {
    await _apiClient.dio.post('/api/approvals/$id/reject', data: {'reason': reason});
  }
}
