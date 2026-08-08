import '../../domain/entities/customer_dashboard.dart';
import '../../domain/repositories/dashboard_repository.dart';
import '../../../transactions/domain/entities/transaction.dart';
import '../../../alerts/domain/entities/fraud_alert.dart';
import '../../../cases/domain/entities/case_entity.dart';

class FixtureDashboardRepository implements DashboardRepository {
  @override
  Future<CustomerDashboardEntity> getCustomerDashboard() async {
    await Future.delayed(const Duration(seconds: 1));
    return CustomerDashboardEntity(
      accountSummary: const AccountSummary(
        accountCount: 1,
        accountTypes: {'CHECKING': 1},
        accounts: [],
        totalsByCurrency: [
          CurrencyTotal(currency: 'USD', currentBalance: 5240.50, availableBalance: 5240.50),
        ],
      ),
      recentTransactions: [
        TransactionEntity(
          id: 't_1',
          merchant: 'Apple Store',
          amount: 1299.00,
          currency: 'USD',
          timestamp: DateTime.now().subtract(const Duration(hours: 2)),
          status: 'COMPLETED',
          hasFraudRisk: true,
        ),
        TransactionEntity(
          id: 't_2',
          merchant: 'Whole Foods',
          amount: 84.20,
          currency: 'USD',
          timestamp: DateTime.now().subtract(const Duration(hours: 24)),
          status: 'COMPLETED',
          hasFraudRisk: false,
        ),
      ],
      fraudAlerts: const [
        FraudAlertEntity(
          id: 'a_1',
          riskScore: 89,
          severity: 'HIGH',
          status: 'OPEN',
          transactionId: 't_1',
          reasons: ['High amount for category', 'Unusual location'],
        ),
      ],
      cases: const [
        CaseEntity(
          id: 'c_1',
          type: 'FRAUD',
          priority: 'HIGH',
          status: 'INVESTIGATING',
          alertId: 'a_1',
          transactionId: 't_1',
        ),
      ],
    );
  }
}
