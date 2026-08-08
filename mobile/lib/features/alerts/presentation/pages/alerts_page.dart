import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../core/widgets/app_loading/app_loading.dart';
import '../../../../core/widgets/app_error/app_error.dart';
import '../widgets/fraud_alert_card/fraud_alert_card.dart';
import '../bloc/alerts_bloc.dart';

class AlertsPage extends StatelessWidget {
  const AlertsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) =>
          AlertsBloc(Dependencies.alertRepository)..add(LoadAlerts()),
      child: Scaffold(
        appBar: AppBar(title: const Text('Fraud Alerts')),
        body: BlocBuilder<AlertsBloc, AlertsState>(
          builder: (context, state) {
            if (state.isLoading && state.alerts.isEmpty) {
              return const AppLoading(message: 'Loading alerts...');
            }
            if (state.error != null && state.alerts.isEmpty) {
              return AppError(
                message: state.error!,
                onRetry: () => context.read<AlertsBloc>().add(LoadAlerts()),
              );
            }
            if (state.alerts.isEmpty) {
              return const Center(child: Text('No active alerts'));
            }
            return RefreshIndicator(
              onRefresh: () async {
                context.read<AlertsBloc>().add(LoadAlerts());
              },
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: state.alerts.length,
                itemBuilder: (context, i) => Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: InkWell(
                    onTap: () =>
                        context.push('/analyst/alerts/${state.alerts[i].id}'),
                    child: FraudAlertCard(alert: state.alerts[i]),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
