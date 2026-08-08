import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/dashboard/presentation/pages/customer_shell.dart';
import '../../features/transactions/domain/entities/transaction.dart';
import '../../features/transactions/presentation/pages/transactions_page.dart';
import '../../features/transactions/presentation/pages/transaction_detail_page.dart';
import '../../features/alerts/presentation/pages/fraud_alert_detail_page.dart';
import '../../features/cases/presentation/pages/case_detail_page.dart';
import 'route_names.dart';

class AppRouter {
  static GoRouter createRouter(AuthBloc authBloc) {
    return GoRouter(
      initialLocation: RouteNames.login,
      refreshListenable: _GoRouterRefreshStream(authBloc.stream),
      redirect: (context, state) {
        final authState = authBloc.state;
        final isGoingToLogin = state.matchedLocation == RouteNames.login;

        if (authState is AuthInitial ||
            authState is AuthLoading && isGoingToLogin) {
          return null;
        }

        if (authState is! AuthAuthenticated) {
          return isGoingToLogin ? null : RouteNames.login;
        }

        if (isGoingToLogin) {
          return RouteNames.customerHome;
        }
        return null;
      },
      routes: [
        GoRoute(
          path: RouteNames.login,
          builder: (context, state) => const LoginPage(),
        ),
        GoRoute(
          path: RouteNames.customerHome,
          builder: (context, state) => const CustomerShell(),
        ),
        GoRoute(
          path: RouteNames.transactions,
          builder: (context, state) {
            final transactions = state.extra as List<TransactionEntity>? ?? [];
            return TransactionsPage(transactions: transactions);
          },
        ),
        GoRoute(
          path: RouteNames.transactionDetail,
          builder: (context, state) {
            final transaction = state.extra as TransactionEntity;
            return TransactionDetailPage(transaction: transaction);
          },
        ),
        GoRoute(
          path: RouteNames.alertDetail,
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return FraudAlertDetailPage(alertId: id);
          },
        ),
        GoRoute(
          path: RouteNames.caseDetail,
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return CaseDetailPage(caseId: id);
          },
        ),
      ],
    );
  }
}

class _GoRouterRefreshStream extends ChangeNotifier {
  _GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.asBroadcastStream().listen(
      (dynamic _) => notifyListeners(),
    );
  }

  late final StreamSubscription<dynamic> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
