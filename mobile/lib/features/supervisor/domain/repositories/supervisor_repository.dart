abstract class SupervisorRepository {
  Future<Map<String, dynamic>> getMetrics();
  Future<List<dynamic>> getRuns();
  Future<List<dynamic>> getTraces(String runId);
}
