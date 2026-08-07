import 'package:equatable/equatable.dart';

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
    return TransactionEntity(
      id: json['id'] ?? json['transaction_id'] ?? '',
      merchant: json['merchant'] ?? 'Unknown',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      currency: json['currency'] ?? 'USD',
      timestamp: json['timestamp'] != null ? DateTime.parse(json['timestamp']) : DateTime.now(),
      status: json['status'] ?? 'COMPLETED',
      category: json['category'],
      hasFraudRisk: json['has_fraud_risk'] ?? false,
    );
  }
  
  @override
  List<Object?> get props => [id, merchant, amount, currency, timestamp, status, category, hasFraudRisk];
}
