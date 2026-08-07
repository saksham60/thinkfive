import 'package:flutter/material.dart';
import 'app/di/dependencies.dart';
import 'app/app.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Dependencies.init();
  runApp(const ThinkFiveApp());
}
