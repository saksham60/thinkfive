import '../../domain/repositories/approval_repository.dart';
import '../../domain/entities/approval.dart';

class FixtureApprovalRepository implements ApprovalRepository {
  final List<ApprovalEntity> _approvals = [
    ApprovalEntity(
      id: 'appr_1',
      type: 'FREEZE_ACCOUNT',
      caseId: 'c_1',
      requestPayload: '{"reason": "High risk fraud detected"}',
      requestedAt: DateTime.now().subtract(const Duration(minutes: 5)),
    )
  ];

  @override
  Future<List<ApprovalEntity>> getPendingApprovals() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return _approvals.toList();
  }
  
  @override
  Future<void> approve(String id) async {
    await Future.delayed(const Duration(milliseconds: 500));
    _approvals.removeWhere((a) => a.id == id);
  }
  
  @override
  Future<void> reject(String id, String reason) async {
    await Future.delayed(const Duration(milliseconds: 500));
    _approvals.removeWhere((a) => a.id == id);
  }
}
