import '../entities/fraud_alert.dart';

abstract class AlertRepository {
  Future<List<FraudAlertEntity>> getAlerts();
  Future<FraudAlertEntity> getAlertDetail(String id);
}
