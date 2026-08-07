import 'package:equatable/equatable.dart';

class FraudAlertEntity extends Equatable {
  final String id;
  final int riskScore;
  final String severity;
  final String status;
  final String? transactionId;
  final String? caseId;
  final List<String> reasons;

  const FraudAlertEntity({
    required this.id,
    required this.riskScore,
    required this.severity,
    required this.status,
    this.transactionId,
    this.caseId,
    this.reasons = const [],
  });

  factory FraudAlertEntity.fromJson(Map<String, dynamic> json) {
    return FraudAlertEntity(
      id: json['id'] ?? json['alert_id'] ?? '',
      riskScore: json['risk_score'] ?? 0,
      severity: json['severity'] ?? 'LOW',
      status: json['status'] ?? 'OPEN',
      transactionId: json['transaction_id'],
      caseId: json['case_id'],
      reasons: (json['reasons'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }

  @override
  List<Object?> get props => [id, riskScore, severity, status, transactionId, caseId, reasons];
}
