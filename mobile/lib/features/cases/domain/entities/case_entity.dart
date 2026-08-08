import 'package:equatable/equatable.dart';
import '../../../../core/utils/json_utils.dart';

class CaseEntity extends Equatable {
  final String id;
  final String type;
  final String priority;
  final String status;
  final String? title;
  final String? description;
  final String? customerId;
  final String? alertId;
  final String? assessmentId;
  final String? transactionId;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const CaseEntity({
    required this.id,
    required this.type,
    required this.priority,
    required this.status,
    this.title,
    this.description,
    this.customerId,
    this.alertId,
    this.assessmentId,
    this.transactionId,
    this.createdAt,
    this.updatedAt,
  });

  factory CaseEntity.fromJson(Map<String, dynamic> json) {
    return CaseEntity(
      id: json['id'] ?? json['case_id'] ?? '',
      type: json['case_type'] ?? json['type'] ?? 'FRAUD',
      priority: json['priority'] ?? 'MEDIUM',
      status: json['status'] ?? 'OPEN',
      title: json['title'],
      description: json['description'],
      customerId: json['customer_id'],
      alertId: json['fraud_alert_id'] ?? json['alert_id'],
      assessmentId: json['assessment_id'],
      transactionId: json['transaction_id'],
      createdAt: json['created_at'] != null ? JsonUtils.parseDateTime(json['created_at']) : null,
      updatedAt: json['updated_at'] != null ? JsonUtils.parseDateTime(json['updated_at']) : null,
    );
  }

  @override
  List<Object?> get props => [
    id,
    type,
    priority,
    status,
    title,
    description,
    customerId,
    alertId,
    assessmentId,
    transactionId,
    createdAt,
    updatedAt,
  ];
}
