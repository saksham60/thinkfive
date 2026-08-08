import 'package:equatable/equatable.dart';
import '../../../../core/utils/json_utils.dart';
import '../../../transactions/domain/entities/transaction.dart';
import '../../../alerts/domain/entities/fraud_alert.dart';
import '../../../cases/domain/entities/case_entity.dart';

class CustomerProfile extends Equatable {
  final String customerId;
  final String displayName;
  final String email;

  const CustomerProfile({
    required this.customerId,
    required this.displayName,
    required this.email,
  });

  factory CustomerProfile.fromJson(Map<String, dynamic> json) {
    return CustomerProfile(
      customerId: json['customer_id']?.toString() ?? '',
      displayName: json['display_name']?.toString() ?? 'Customer',
      email: json['email']?.toString() ?? '',
    );
  }

  @override
  List<Object?> get props => [customerId, displayName, email];
}

class CurrencyTotal extends Equatable {
  final String currency;
  final double currentBalance;
  final double availableBalance;

  const CurrencyTotal({
    required this.currency,
    required this.currentBalance,
    required this.availableBalance,
  });

  factory CurrencyTotal.fromJson(Map<String, dynamic> json) {
    return CurrencyTotal(
      currency: json['currency']?.toString() ?? 'USD',
      currentBalance: JsonUtils.parseDouble(json['current_balance']),
      availableBalance: JsonUtils.parseDouble(json['available_balance']),
    );
  }

  @override
  List<Object?> get props => [currency, currentBalance, availableBalance];
}

class AccountSummary extends Equatable {
  final int accountCount;
  final Map<String, dynamic> accountTypes;
  final List<dynamic> accounts;
  final List<CurrencyTotal> totalsByCurrency;

  const AccountSummary({
    required this.accountCount,
    required this.accountTypes,
    required this.accounts,
    required this.totalsByCurrency,
  });

  factory AccountSummary.fromJson(Map<String, dynamic> json) {
    return AccountSummary(
      accountCount: json['account_count'] ?? 0,
      accountTypes: JsonUtils.asMap(json['account_types']),
      accounts: JsonUtils.asList(json['accounts']),
      totalsByCurrency: JsonUtils.asList(json['totals_by_currency'])
          .map((e) => CurrencyTotal.fromJson(JsonUtils.asMap(e)))
          .toList(),
    );
  }

  @override
  List<Object?> get props => [accountCount, accountTypes, accounts, totalsByCurrency];
}

class CustomerDashboardEntity extends Equatable {
  final CustomerProfile? profile;
  final AccountSummary? accountSummary;
  final List<TransactionEntity> recentTransactions;
  final List<FraudAlertEntity> fraudAlerts;
  final List<CaseEntity> cases;
  final List<String> degradedServices;
  final List<dynamic> cards;

  const CustomerDashboardEntity({
    this.profile,
    this.accountSummary,
    this.recentTransactions = const [],
    this.fraudAlerts = const [],
    this.cases = const [],
    this.degradedServices = const [],
    this.cards = const [],
  });

  factory CustomerDashboardEntity.fromJson(Map<String, dynamic> json) {
    return CustomerDashboardEntity(
      profile: json['profile'] != null ? CustomerProfile.fromJson(JsonUtils.asMap(json['profile'])) : null,
      accountSummary: json['account_summary'] != null
          ? AccountSummary.fromJson(JsonUtils.asMap(json['account_summary']))
          : null,
      recentTransactions: JsonUtils.normalizeResults(json['recent_transactions'], 'results')
          .map((e) => TransactionEntity.fromJson(e))
          .toList(),
      fraudAlerts: JsonUtils.normalizeResults(json['fraud_alerts'], 'alerts')
          .map((e) => FraudAlertEntity.fromJson(e))
          .toList(),
      cases: JsonUtils.normalizeResults(json['cases'], 'cases')
          .map((e) => CaseEntity.fromJson(e))
          .toList(),
      degradedServices: JsonUtils.asList(json['degraded_services']).map((e) => e.toString()).toList(),
      cards: JsonUtils.asList(json['cards']),
    );
  }

  @override
  List<Object?> get props => [
        profile,
        accountSummary,
        recentTransactions,
        fraudAlerts,
        cases,
        degradedServices,
        cards,
      ];
}
