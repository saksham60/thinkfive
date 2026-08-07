import 'package:equatable/equatable.dart';
import '../../../transactions/domain/entities/transaction.dart';
import '../../../alerts/domain/entities/fraud_alert.dart';
import '../../../cases/domain/entities/case_entity.dart';

class AccountSummary extends Equatable {
  final double balance;
  final String currency;
  final String status;
  
  const AccountSummary({required this.balance, required this.currency, required this.status});
  
  factory AccountSummary.fromJson(Map<String, dynamic> json) {
    return AccountSummary(
      balance: (json['balance'] as num?)?.toDouble() ?? 0.0,
      currency: json['currency'] ?? 'USD',
      status: json['status'] ?? 'ACTIVE',
    );
  }
  
  @override
  List<Object?> get props => [balance, currency, status];
}

class CustomerDashboardEntity extends Equatable {
  final AccountSummary? accountSummary;
  final List<TransactionEntity> recentTransactions;
  final List<FraudAlertEntity> fraudAlerts;
  final List<CaseEntity> cases;

  const CustomerDashboardEntity({
    this.accountSummary,
    this.recentTransactions = const [],
    this.fraudAlerts = const [],
    this.cases = const [],
  });
  
  factory CustomerDashboardEntity.fromJson(Map<String, dynamic> json) {
    return CustomerDashboardEntity(
      accountSummary: json['account_summary'] != null ? AccountSummary.fromJson(json['account_summary']) : null,
      recentTransactions: (json['recent_transactions'] as List<dynamic>?)?.map((e) => TransactionEntity.fromJson(e)).toList() ?? [],
      fraudAlerts: (json['fraud_alerts'] as List<dynamic>?)?.map((e) => FraudAlertEntity.fromJson(e)).toList() ?? [],
      cases: (json['cases'] as List<dynamic>?)?.map((e) => CaseEntity.fromJson(e)).toList() ?? [],
    );
  }

  @override
  List<Object?> get props => [accountSummary, recentTransactions, fraudAlerts, cases];
}
