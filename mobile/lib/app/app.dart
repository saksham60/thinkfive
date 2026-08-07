import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'di/dependencies.dart';
import 'router/app_router.dart';
import 'theme/app_theme.dart';
import '../features/auth/presentation/bloc/auth_bloc.dart';

class ThinkFiveApp extends StatefulWidget {
  const ThinkFiveApp({super.key});

  @override
  State<ThinkFiveApp> createState() => _ThinkFiveAppState();
}

class _ThinkFiveAppState extends State<ThinkFiveApp> {
  late final AuthBloc _authBloc;
  late final GoRouter _router;

  @override
  void initState() {
    super.initState();
    _authBloc = AuthBloc(Dependencies.authRepository)..add(AuthCheckRequested());
    _router = AppRouter.createRouter(_authBloc);
  }

  @override
  void dispose() {
    _authBloc.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _authBloc,
      child: MaterialApp.router(
        title: 'ThinkFive',
        theme: AppTheme.darkTheme,
        themeMode: ThemeMode.dark,
        routerConfig: _router,
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
