import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../app/theme/app_colors.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../bloc/dashboard_bloc.dart';
import '../../../../core/widgets/app_loading/app_loading.dart';
import '../../../../core/widgets/app_error/app_error.dart';
import '../widgets/account_summary_card/account_summary_card.dart';
import '../../../transactions/presentation/widgets/transaction_card/transaction_card.dart';
import '../../../alerts/presentation/widgets/fraud_alert_card/fraud_alert_card.dart';
import '../../../cases/presentation/widgets/case_status_card/case_status_card.dart';

class CustomerHomePage extends StatelessWidget {
  const CustomerHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => DashboardBloc(Dependencies.dashboardRepository)..add(LoadDashboard()),
      child: Scaffold(
        appBar: AppBar(
          title: const Text('ThinkFive'),
          actions: [
            IconButton(
              icon: const Icon(LucideIcons.logOut),
              onPressed: () => context.read<AuthBloc>().add(AuthLogoutRequested()),
            )
          ],
        ),
        body: BlocBuilder<DashboardBloc, DashboardState>(
          builder: (context, state) {
            if (state is DashboardLoading) return const AppLoading(message: 'Loading dashboard...');
            if (state is DashboardError) return AppError(message: state.message, onRetry: () => context.read<DashboardBloc>().add(LoadDashboard()));
            
            if (state is DashboardLoaded) {
              final db = state.dashboard;
              return RefreshIndicator(
                onRefresh: () async {
                  context.read<DashboardBloc>().add(LoadDashboard());
                },
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (db.accountSummary != null) ...[
                      AccountSummaryCard(summary: db.accountSummary!),
                      const SizedBox(height: 24),
                    ],
                    
                    if (db.fraudAlerts.isNotEmpty) ...[
                      const Text('Security Alerts', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                      const SizedBox(height: 12),
                      ...db.fraudAlerts.map((a) => Padding(padding: const EdgeInsets.only(bottom: 8), child: FraudAlertCard(alert: a))),
                      const SizedBox(height: 24),
                    ],

                    if (db.cases.isNotEmpty) ...[
                      const Text('Open Cases', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                      const SizedBox(height: 12),
                      ...db.cases.map((c) => Padding(padding: const EdgeInsets.only(bottom: 8), child: CaseStatusCard(caseEntity: c))),
                      const SizedBox(height: 24),
                    ],

                    if (db.recentTransactions.isNotEmpty) ...[
                      const Text('Recent Transactions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                      const SizedBox(height: 12),
                      ...db.recentTransactions.map((t) => Padding(padding: const EdgeInsets.only(bottom: 8), child: TransactionCard(transaction: t))),
                      const SizedBox(height: 24),
                    ],
                  ],
                ),
              );
            }
            return const SizedBox();
          },
        ),
      ),
    );
  }
}
