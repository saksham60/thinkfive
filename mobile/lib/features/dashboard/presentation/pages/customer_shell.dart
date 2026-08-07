import 'package:flutter/material.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import 'customer_home_page.dart';
import '../../chat/presentation/pages/ai_assistant_page.dart';
import '../../alerts/presentation/pages/alerts_page.dart';
import '../../cases/presentation/pages/cases_page.dart';

class CustomerShell extends StatefulWidget {
  const CustomerShell({super.key});

  @override
  State<CustomerShell> createState() => _CustomerShellState();
}

class _CustomerShellState extends State<CustomerShell> {
  int _currentIndex = 0;
  
  final List<Widget> _pages = const [
    CustomerHomePage(),
    AiAssistantPage(),
    AlertsPage(),
    CasesPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(LucideIcons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(LucideIcons.bot), label: 'AI'),
          BottomNavigationBarItem(icon: Icon(LucideIcons.bell), label: 'Alerts'),
          BottomNavigationBarItem(icon: Icon(LucideIcons.briefcase), label: 'Cases'),
        ],
      ),
    );
  }
}
