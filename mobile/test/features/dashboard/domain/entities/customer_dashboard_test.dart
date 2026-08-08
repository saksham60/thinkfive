import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/dashboard/domain/entities/customer_dashboard.dart';

void main() {
  group('CustomerDashboardEntity', () {
    test('parses REALISTIC production payload (Test 1 & 4)', () {
      final payload = {
        "profile": {
          "customer_id": "cust-1",
          "display_name": "John Doe",
          "email": "john@example.com"
        },
        "account_summary": {
          "account_count": 2,
          "account_types": {"CHECKING": 1, "SAVINGS": 1},
          "accounts": [],
          "totals_by_currency": [
            {
              "currency": "USD",
              "current_balance": 1500.50,
              "available_balance": "1400.00" // Mixed types for parsing check
            }
          ]
        },
        "recent_transactions": {
          "results": [
            {
              "transaction_id": "txn-1",
              "merchant_name": "Starbucks",
              "amount": "5.50",
              "currency": "USD",
              "date": "2023-01-01T12:00:00Z"
            }
          ]
        },
        "fraud_alerts": {
          "count": 1,
          "results": [
            {
              "alert_id": "alert-1",
              "transaction_id": "txn-1",
              "risk_score": 0.727,
              "severity": "HIGH",
              "status": "OPEN"
            }
          ]
        },
        "cases": [
          {
            "case_id": "case-1",
            "case_type": "FRAUD_INVESTIGATION",
            "priority": "HIGH",
            "status": "OPEN",
            "fraud_alert_id": "alert-1",
            "transaction_id": "txn-1"
          }
        ],
        "degraded_services": []
      };

      final db = CustomerDashboardEntity.fromJson(payload);

      expect(db.profile!.displayName, 'John Doe');
      expect(db.accountSummary!.accountCount, 2);
      expect(db.accountSummary!.totalsByCurrency.first.currency, 'USD');
      expect(db.accountSummary!.totalsByCurrency.first.availableBalance, 1400.0);

      expect(db.recentTransactions.length, 1);
      expect(db.recentTransactions.first.merchant, 'Starbucks');
      expect(db.recentTransactions.first.amount, 5.5);

      expect(db.fraudAlerts.length, 1);
      expect(db.fraudAlerts.first.id, 'alert-1');
      expect(db.fraudAlerts.first.riskScore, 0.727);

      expect(db.cases.length, 1);
      expect(db.cases.first.id, 'case-1');
      expect(db.cases.first.type, 'FRAUD_INVESTIGATION');
      expect(db.cases.first.alertId, 'alert-1');

      expect(db.degradedServices.isEmpty, true);
    });

    test('parses empty dashboard (Test 8)', () {
      final db = CustomerDashboardEntity.fromJson({});

      expect(db.profile, isNull);
      expect(db.accountSummary, isNull);
      expect(db.recentTransactions.isEmpty, true);
      expect(db.fraudAlerts.isEmpty, true);
      expect(db.cases.isEmpty, true);
      expect(db.degradedServices.isEmpty, true);
    });

    test('parses partially degraded dashboard (Test 9)', () {
      final payload = {
        "profile": {
          "customer_id": "cust-1",
          "display_name": "Jane Doe"
        },
        "account_summary": null, // Missing due to degraded service
        "degraded_services": ["banking.account_summary"]
      };

      final db = CustomerDashboardEntity.fromJson(payload);
      expect(db.profile!.displayName, 'Jane Doe');
      expect(db.accountSummary, isNull);
      expect(db.degradedServices, contains("banking.account_summary"));
      expect(db.recentTransactions.isEmpty, true);
    });

    test('malformed response should produce controlled error, not crash (Test 12)', () {
      final payload = {
        "account_summary": "this is a string, not a map",
        "recent_transactions": {"invalid": "shape"},
        "degraded_services": {"not": "a list"}
      };

      final db = CustomerDashboardEntity.fromJson(payload);
      expect(db.accountSummary, isNotNull);
      // It falls back to safe parsing in JsonUtils.asMap which returns empty map for string
      expect(db.accountSummary!.accountCount, 0);
      expect(db.recentTransactions.isEmpty, true);
      expect(db.degradedServices.isEmpty, true);
    });
  });
}
