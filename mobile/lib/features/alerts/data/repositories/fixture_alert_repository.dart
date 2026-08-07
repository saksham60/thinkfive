import '../../domain/repositories/alert_repository.dart';
import '../../domain/entities/fraud_alert.dart';

class FixtureAlertRepository implements AlertRepository {
  final _alerts = [
    const FraudAlertEntity(
      id: 'a_1', riskScore: 89, severity: 'HIGH', status: 'OPEN',
      transactionId: 't_1', reasons: ['High amount for category', 'Unusual location'],
    )
  ];

  @override
  Future<List<FraudAlertEntity>> getAlerts() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return _alerts;
  }
  
  @override
  Future<FraudAlertEntity> getAlertDetail(String id) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return _alerts.firstWhere((a) => a.id == id, orElse: () => _alerts.first);
  }
}
