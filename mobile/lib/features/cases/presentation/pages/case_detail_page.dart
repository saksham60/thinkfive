import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../core/widgets/app_loading/app_loading.dart';
import '../../../../core/widgets/app_error/app_error.dart';
import '../bloc/cases_bloc.dart';

class CaseDetailPage extends StatelessWidget {
  final String caseId;
  const CaseDetailPage({super.key, required this.caseId});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) =>
          CasesBloc(Dependencies.caseRepository)..add(LoadCaseDetail(caseId)),
      child: Scaffold(
        appBar: AppBar(title: const Text('Case Detail')),
        body: BlocBuilder<CasesBloc, CasesState>(
          builder: (context, state) {
            if (state.isLoading) {
              return const AppLoading(message: 'Loading case...');
            }
            if (state.error != null) {
              return AppError(
                message: state.error!,
                onRetry: () =>
                    context.read<CasesBloc>().add(LoadCaseDetail(caseId)),
              );
            }
            if (state.selectedCase == null) {
              return const Center(child: Text('Case not found'));
            }

            final caseEntity = state.selectedCase!;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  'ID: ${caseEntity.id}',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  'Status: ${caseEntity.status}',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 16),
                if (caseEntity.alertId != null) ...[
                  const SizedBox(height: 8),
                  Text('Alert ID: ${caseEntity.alertId}'),
                ],
                if (caseEntity.transactionId != null) ...[
                  const SizedBox(height: 8),
                  Text('Transaction ID: ${caseEntity.transactionId}'),
                ],
              ],
            );
          },
        ),
      ),
    );
  }
}
