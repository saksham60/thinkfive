import 'package:flutter/material.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../core/widgets/app_loading/app_loading.dart';
import '../../../../core/widgets/app_error/app_error.dart';
import '../widgets/case_status_card/case_status_card.dart';
import '../../domain/entities/case_entity.dart';

class CasesPage extends StatefulWidget {
  const CasesPage({super.key});

  @override
  State<CasesPage> createState() => _CasesPageState();
}

class _CasesPageState extends State<CasesPage> {
  late Future<List<CaseEntity>> _casesFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    setState(() {
      _casesFuture = Dependencies.caseRepository.getCases();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Cases')),
      body: FutureBuilder<List<CaseEntity>>(
        future: _casesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const AppLoading(message: 'Loading cases...');
          }
          if (snapshot.hasError) {
            return AppError(message: snapshot.error.toString(), onRetry: _load);
          }
          final cases = snapshot.data ?? [];
          if (cases.isEmpty) {
            return const Center(child: Text('No active cases'));
          }
          return RefreshIndicator(
            onRefresh: () async => _load(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: cases.length,
              itemBuilder: (context, i) => Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: CaseStatusCard(caseEntity: cases[i]),
              ),
            ),
          );
        },
      ),
    );
  }
}
