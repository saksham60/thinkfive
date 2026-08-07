export const endpoints = {
  auth: { me: '/api/auth/me', login: '/api/auth/login', logout: '/api/auth/logout' },
  customer: { profile: '/api/customers/me', dashboard: '/api/customers/me/dashboard' },
  chat: '/api/chat',
  chatMessages: (conversationId: string, runId?: string) => {
    const suffix = runId ? `?run_id=${encodeURIComponent(runId)}` : '';
    return `/api/chat/${encodeURIComponent(conversationId)}/messages${suffix}`;
  },
  alerts: '/api/alerts',
  cases: '/api/cases',
  approvals: { pending: '/api/approvals/pending', root: '/api/approvals' },
  supervisor: {
    metrics: '/api/supervisor/metrics',
    runs: '/api/supervisor/runs',
    simulator: '/api/simulator/transaction',
    evaluation: '/api/evaluation/run',
  },
  system: { mcpTools: '/api/system/mcp/tools' },
  policies: '/api/policies/search',
  events: '/api/events',
} as const;
