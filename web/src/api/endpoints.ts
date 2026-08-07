export const endpoints = {
  auth: { me: '/api/auth/me', login: '/api/auth/login', logout: '/api/auth/logout' },
  customer: { dashboard: '/api/customer/dashboard' },
  chat: '/api/chat', alerts: '/api/alerts', cases: '/api/cases', approvals: '/api/approvals',
  supervisor: { metrics: '/api/supervisor/metrics', simulator: '/api/simulator/trigger' },
  agents: '/api/agents', capabilities: '/api/mcp/capabilities', evaluations: '/api/evaluations', events: '/api/events',
} as const;
