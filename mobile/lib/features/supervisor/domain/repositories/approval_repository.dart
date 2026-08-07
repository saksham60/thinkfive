import '../entities/approval.dart';

abstract class ApprovalRepository {
  Future<List<ApprovalEntity>> getPendingApprovals();
  Future<void> approve(String id);
  Future<void> reject(String id, String reason);
}
