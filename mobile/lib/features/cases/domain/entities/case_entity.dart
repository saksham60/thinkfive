import 'package:equatable/equatable.dart';

class CaseEntity extends Equatable {
  final String id;
  final String type;
  final String priority;
  final String status;
  final String? alertId;
  final String? transactionId;

  const CaseEntity({
    required this.id,
    required this.type,
    required this.priority,
    required this.status,
    this.alertId,
    this.transactionId,
  });

  factory CaseEntity.fromJson(Map<String, dynamic> json) {
    return CaseEntity(
      id: json['id'] ?? json['case_id'] ?? '',
      type: json['type'] ?? 'FRAUD',
      priority: json['priority'] ?? 'MEDIUM',
      status: json['status'] ?? 'OPEN',
      alertId: json['alert_id'],
      transactionId: json['transaction_id'],
    );
  }

  @override
  List<Object?> get props => [id, type, priority, status, alertId, transactionId];
}
