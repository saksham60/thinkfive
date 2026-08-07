import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/domain/entities/user.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/dashboard/presentation/pages/customer_shell.dart';
import '../../features/dashboard/presentation/pages/analyst_home_page.dart';
import '../../features/supervisor/presentation/pages/supervisor_home_page.dart';
import 'route_names.dart';

class AppRouter {
  static GoRouter createRouter(AuthBloc authBloc) {
    return GoRouter(
      initialLocation: RouteNames.login,
      refreshListenable: _GoRouterRefreshStream(authBloc.stream),
      redirect: (context, state) {
        final authState = authBloc.state;
        final isGoingToLogin = state.matchedLocation == RouteNames.login;

        if (authState is AuthInitial || authState is AuthLoading && isGoingToLogin) {
          return null; 
        }

        if (authState is! AuthAuthenticated) {
          return isGoingToLogin ? null : RouteNames.login;
        }

        if (isGoingToLogin) {
          final role = authState.user.role;
          switch (role) {
            case AppRole.analyst:
              return RouteNames.analystHome;
            case AppRole.supervisor:
            case AppRole.admin:
              return RouteNames.supervisorHome;
            case AppRole.customer:
            default:
              return RouteNames.customerHome;
          }
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
          path: RouteNames.analystHome,
          builder: (context, state) => const AnalystHomePage(),
        ),
        GoRoute(
          path: RouteNames.supervisorHome,
          builder: (context, state) => const SupervisorHomePage(),
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
