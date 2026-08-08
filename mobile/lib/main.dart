import 'package:flutter/material.dart';
import 'app/di/dependencies.dart';
import 'core/config/app_config.dart';
import 'app/app.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  debugPrint(
    'Starting ThinkFive Mobile. Effective API_BASE_URL: ${AppConfig.apiBaseUrl}',
  );
  await Dependencies.init();
  runApp(const ThinkFiveApp());
}
