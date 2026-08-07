import '../entities/case_entity.dart';

abstract class CaseRepository {
  Future<List<CaseEntity>> getCases();
  Future<CaseEntity> getCaseDetail(String id);
  Future<void> addCaseNote(String id, String note);
}
