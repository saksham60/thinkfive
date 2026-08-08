import '../../domain/repositories/case_repository.dart';
import '../../domain/entities/case_entity.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/utils/json_utils.dart';

class RemoteCaseRepository implements CaseRepository {
  final ApiClient _apiClient;

  RemoteCaseRepository(this._apiClient);

  @override
  Future<List<CaseEntity>> getCases() async {
    final response = await _apiClient.dio.get(ApiEndpoints.cases);
    final list = JsonUtils.normalizeResults(response.data, 'cases');
    return list.map((e) => CaseEntity.fromJson(e)).toList();
  }

  @override
  Future<CaseEntity> getCaseDetail(String id) async {
    final response = await _apiClient.dio.get(ApiEndpoints.caseDetail(id));
    return CaseEntity.fromJson(response.data);
  }

  @override
  Future<void> addCaseNote(String id, String note) async {
    await _apiClient.dio.post(ApiEndpoints.caseNotes(id), data: {'note': note});
  }
}
