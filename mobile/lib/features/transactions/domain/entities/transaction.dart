import 'package:equatable/equatable.dart';
import '../../../../core/utils/json_utils.dart';

class TransactionEntity extends Equatable {
  final String id;
  final String merchant;
  final double amount;
  final String currency;
  final DateTime timestamp;
  final String status;
  final String? category;
  final bool? hasFraudRisk;

  const TransactionEntity({
    required this.id,
    required this.merchant,
    required this.amount,
    required this.currency,
    required this.timestamp,
    required this.status,
    this.category,
    this.hasFraudRisk,
  });

  factory TransactionEntity.fromJson(Map<String, dynamic> json) {
    final merchant = json['merchant_name'] ?? json['transaction_name'] ?? json['description'] ?? json['merchant'] ?? 'Unknown';
    final timestamp = JsonUtils.parseDateTime(json['datetime'] ?? json['date'] ?? json['transaction_date'] ?? json['timestamp']);
    final isPending = json['pending'] == true;
    final status = json['status'] ?? (isPending ? 'PENDING' : 'COMPLETED');

    String? categoryStr;
    if (json['category'] is List) {
      categoryStr = (json['category'] as List).join(', ');
    } else if (json['category'] is String) {
      categoryStr = json['category'];
    } else if (json['personal_finance_category'] is Map) {
      categoryStr = json['personal_finance_category']['primary'];
    }

    return TransactionEntity(
      id: json['id'] ?? json['transaction_id'] ?? '',
      merchant: merchant.toString(),
      amount: JsonUtils.parseDouble(json['amount']),
      currency: json['currency'] ?? 'USD',
      timestamp: timestamp,
      status: status.toString().toUpperCase(),
      category: categoryStr,
      hasFraudRisk: json['has_fraud_risk'] ?? false,
    );
  }

  @override
  List<Object?> get props => [
    id,
    merchant,
    amount,
    currency,
    timestamp,
    status,
    category,
    hasFraudRisk,
  ];
}
