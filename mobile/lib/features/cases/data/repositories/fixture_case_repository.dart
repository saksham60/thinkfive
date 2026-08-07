import '../../domain/repositories/case_repository.dart';
import '../../domain/entities/case_entity.dart';

class FixtureCaseRepository implements CaseRepository {
  final _cases = [
    const CaseEntity(
      id: 'c_1', type: 'FRAUD', priority: 'HIGH', status: 'INVESTIGATING',
      alertId: 'a_1', transactionId: 't_1',
    )
  ];

  @override
  Future<List<CaseEntity>> getCases() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return _cases;
  }
  
  @override
  Future<CaseEntity> getCaseDetail(String id) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return _cases.firstWhere((c) => c.id == id, orElse: () => _cases.first);
  }

  @override
  Future<void> addCaseNote(String id, String note) async {
    await Future.delayed(const Duration(milliseconds: 500));
  }
}
