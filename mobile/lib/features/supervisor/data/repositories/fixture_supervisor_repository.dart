import '../../domain/repositories/supervisor_repository.dart';

class FixtureSupervisorRepository implements SupervisorRepository {
  @override
  Future<Map<String, dynamic>> getMetrics() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return {
      'total_cases': 142,
      'open_cases': 12,
      'avg_resolution_time_hrs': 4.5,
      'automation_rate': 0.85,
    };
  }
  
  @override
  Future<List<dynamic>> getRuns() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return [
      {'run_id': 'r_1', 'status': 'COMPLETED', 'duration_sec': 45},
      {'run_id': 'r_2', 'status': 'FAILED', 'duration_sec': 12},
    ];
  }
  
  @override
  Future<List<dynamic>> getTraces(String runId) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return [
      {'trace_id': 't_1', 'step': 'lookup_user', 'latency': 120},
    ];
  }
}
