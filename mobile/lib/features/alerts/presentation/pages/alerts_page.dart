import 'package:flutter/material.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../core/widgets/app_loading/app_loading.dart';
import '../../../../core/widgets/app_error/app_error.dart';
import '../widgets/fraud_alert_card/fraud_alert_card.dart';
import '../../domain/entities/fraud_alert.dart';

class AlertsPage extends StatefulWidget {
  const AlertsPage({super.key});

  @override
  State<AlertsPage> createState() => _AlertsPageState();
}

class _AlertsPageState extends State<AlertsPage> {
  late Future<List<FraudAlertEntity>> _alertsFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    setState(() {
      _alertsFuture = Dependencies.alertRepository.getAlerts();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Fraud Alerts')),
      body: FutureBuilder<List<FraudAlertEntity>>(
        future: _alertsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const AppLoading(message: 'Loading alerts...');
          }
          if (snapshot.hasError) {
            return AppError(message: snapshot.error.toString(), onRetry: _load);
          }
          final alerts = snapshot.data ?? [];
          if (alerts.isEmpty) {
            return const Center(child: Text('No active alerts'));
          }
          return RefreshIndicator(
            onRefresh: () async => _load(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: alerts.length,
              itemBuilder: (context, i) => Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: FraudAlertCard(alert: alerts[i]),
              ),
            ),
          );
        },
      ),
    );
  }
}
