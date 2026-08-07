class ApiEndpoints {
  static const String login = '/api/auth/login';
  static const String logout = '/api/auth/logout';
  static const String customerMe = '/api/customers/me';
  static const String customerDashboard = '/api/customers/me/dashboard';
  static const String chat = '/api/chat';
  
  static String sse(String conversationId) => '/api/events?conversation_id=$conversationId';
  
  static const String alerts = '/api/alerts';
  static String alertDetail(String id) => '/api/alerts/$id';
  
  static const String cases = '/api/cases';
  static String caseDetail(String id) => '/api/cases/$id';
  static String caseNotes(String id) => '/api/cases/$id/notes';
  
  static const String approvalsPending = '/api/approvals/pending';
  static String approve(String id) => '/api/approvals/$id/approve';
  static String reject(String id) => '/api/approvals/$id/reject';
  
  static const String supervisorMetrics = '/api/supervisor/metrics';
  static const String supervisorRuns = '/api/supervisor/runs';
  static String runTraces(String id) => '/api/supervisor/runs/$id/traces';
  
  static const String systemMcpTools = '/api/system/mcp/tools';
  static const String health = '/health';
  static const String ready = '/ready';
}
