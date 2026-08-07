import 'package:equatable/equatable.dart';

class ApprovalEntity extends Equatable {
  final String id;
  final String type;
  final String caseId;
  final String requestPayload;
  final DateTime requestedAt;

  const ApprovalEntity({
    required this.id,
    required this.type,
    required this.caseId,
    required this.requestPayload,
    required this.requestedAt,
  });

  factory ApprovalEntity.fromJson(Map<String, dynamic> json) {
    return ApprovalEntity(
      id: json['id'] ?? json['approval_id'] ?? '',
      type: json['type'] ?? 'FREEZE_ACCOUNT',
      caseId: json['case_id'] ?? '',
      requestPayload: json['request_payload']?.toString() ?? '',
      requestedAt: json['requested_at'] != null ? DateTime.parse(json['requested_at']) : DateTime.now(),
    );
  }

  @override
  List<Object?> get props => [id, type, caseId, requestPayload, requestedAt];
}
