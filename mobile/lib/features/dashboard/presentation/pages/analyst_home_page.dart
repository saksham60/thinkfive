import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../../../app/di/dependencies.dart';
import '../../../../core/widgets/app_loading/app_loading.dart';
import '../../../../core/widgets/app_error/app_error.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../supervisor/domain/entities/approval.dart';

class AnalystHomePage extends StatefulWidget {
  const AnalystHomePage({super.key});

  @override
  State<AnalystHomePage> createState() => _AnalystHomePageState();
}

class _AnalystHomePageState extends State<AnalystHomePage> {
  late Future<List<ApprovalEntity>> _approvalsFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    setState(() {
      _approvalsFuture = Dependencies.approvalRepository.getPendingApprovals();
    });
  }

  Future<void> _approve(String id) async {
    await Dependencies.approvalRepository.approve(id);
    _load();
  }

  Future<void> _reject(String id) async {
    await Dependencies.approvalRepository.reject(id, 'Rejected by analyst');
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analyst Queue'),
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.logOut),
            onPressed: () => context.read<AuthBloc>().add(AuthLogoutRequested()),
          )
        ],
      ),
      body: FutureBuilder<List<ApprovalEntity>>(
        future: _approvalsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) return const AppLoading(message: 'Loading queue...');
          if (snapshot.hasError) return AppError(message: snapshot.error.toString(), onRetry: _load);
          
          final approvals = snapshot.data ?? [];
          if (approvals.isEmpty) return const Center(child: Text('Queue is empty'));

          return RefreshIndicator(
            onRefresh: () async => _load(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: approvals.length,
              itemBuilder: (context, i) {
                final app = approvals[i];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Approval Needed: ${app.type}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        const SizedBox(height: 8),
                        Text('Case ID: ${app.caseId}'),
                        Text('Details: ${app.requestPayload}'),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            TextButton(
                              onPressed: () => _reject(app.id),
                              child: const Text('Reject', style: TextStyle(color: Colors.redAccent)),
                            ),
                            const SizedBox(width: 8),
                            ElevatedButton(
                              onPressed: () => _approve(app.id),
                              child: const Text('Approve'),
                            ),
                          ],
                        )
                      ],
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
