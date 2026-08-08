import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../core/widgets/app_loading/app_loading.dart';
import '../../../../core/widgets/app_error/app_error.dart';
import '../bloc/alerts_bloc.dart';

class FraudAlertDetailPage extends StatelessWidget {
  final String alertId;
  const FraudAlertDetailPage({super.key, required this.alertId});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) =>
          AlertsBloc(Dependencies.alertRepository)
            ..add(LoadAlertDetail(alertId)),
      child: Scaffold(
        appBar: AppBar(title: const Text('Alert Detail')),
        body: BlocBuilder<AlertsBloc, AlertsState>(
          builder: (context, state) {
            if (state.isLoading) {
              return const AppLoading(message: 'Loading alert...');
            }
            if (state.error != null) {
              return AppError(
                message: state.error!,
                onRetry: () =>
                    context.read<AlertsBloc>().add(LoadAlertDetail(alertId)),
              );
            }
            if (state.selectedAlert == null) {
              return const Center(child: Text('Alert not found'));
            }

            final alert = state.selectedAlert!;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  'ID: ${alert.id}',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  'Status: ${alert.status}',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text('Severity: ${alert.severity}'),
                const SizedBox(height: 16),
                Text(
                  'Reasons:',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                ...alert.reasons.map((r) => ListTile(title: Text(r))),
              ],
            );
          },
        ),
      ),
    );
  }
}
