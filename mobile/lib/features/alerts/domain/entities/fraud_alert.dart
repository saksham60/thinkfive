import 'package:equatable/equatable.dart';
import '../../../../core/utils/json_utils.dart';

class FraudAlertEntity extends Equatable {
  final String id;
  final double riskScore;
  final String severity;
  final String status;
  final String? transactionId;
  final String? assessmentId;
  final String? customerId;
  final String? priority;
  final DateTime? createdAt;
  final String? caseId;
  final List<String> reasons;

  const FraudAlertEntity({
    required this.id,
    required this.riskScore,
    required this.severity,
    required this.status,
    this.transactionId,
    this.assessmentId,
    this.customerId,
    this.priority,
    this.createdAt,
    this.caseId,
    this.reasons = const [],
  });

  factory FraudAlertEntity.fromJson(Map<String, dynamic> json) {
    return FraudAlertEntity(
      id: json['id'] ?? json['alert_id'] ?? '',
      riskScore: JsonUtils.parseDouble(json['risk_score']),
      severity: json['severity'] ?? 'LOW',
      status: json['status'] ?? 'OPEN',
      transactionId: json['transaction_id'],
      assessmentId: json['assessment_id'],
      customerId: json['customer_id'],
      priority: json['priority'],
      createdAt: json['created_at'] != null ? JsonUtils.parseDateTime(json['created_at']) : null,
      caseId: json['case_id'],
      reasons: JsonUtils.asList(json['reasons']).map((e) => e.toString()).toList(),
    );
  }

  @override
  List<Object?> get props => [
    id,
    riskScore,
    severity,
    status,
    transactionId,
    assessmentId,
    customerId,
    priority,
    createdAt,
    caseId,
    reasons,
  ];
}
