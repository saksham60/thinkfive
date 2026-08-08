import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../core/widgets/app_loading/app_loading.dart';
import '../../../../core/widgets/app_error/app_error.dart';
import '../widgets/case_status_card/case_status_card.dart';
import '../bloc/cases_bloc.dart';

class CasesPage extends StatelessWidget {
  const CasesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) =>
          CasesBloc(Dependencies.caseRepository)..add(LoadCases()),
      child: Scaffold(
        appBar: AppBar(title: const Text('Cases')),
        body: BlocBuilder<CasesBloc, CasesState>(
          builder: (context, state) {
            if (state.isLoading && state.cases.isEmpty) {
              return const AppLoading(message: 'Loading cases...');
            }
            if (state.error != null && state.cases.isEmpty) {
              return AppError(
                message: state.error!,
                onRetry: () => context.read<CasesBloc>().add(LoadCases()),
              );
            }
            if (state.cases.isEmpty) {
              return const Center(child: Text('No active cases'));
            }
            return RefreshIndicator(
              onRefresh: () async {
                context.read<CasesBloc>().add(LoadCases());
              },
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: state.cases.length,
                itemBuilder: (context, i) => Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: InkWell(
                    onTap: () =>
                        context.push('/analyst/cases/${state.cases[i].id}'),
                    child: CaseStatusCard(caseEntity: state.cases[i]),
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
