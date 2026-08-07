import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { LoginInput, SessionResponse } from '../types/auth.types';

interface BackendSession {
  user_id: string;
  email: string;
  role: string;
  customer_id?: string | null;
}

const mapSession = (session: BackendSession): SessionResponse => ({
  id: session.user_id,
  email: session.email,
  displayName: session.email.split('@')[0] || session.email,
  role: session.role.toLowerCase() as SessionResponse['role'],
  customerId: session.customer_id || undefined,
});

export const authApi = {
  restore: async (signal?: AbortSignal) => mapSession(await apiRequest<BackendSession>(endpoints.auth.me, { signal })),
  login: async (input: LoginInput) => mapSession(await apiRequest<BackendSession>(endpoints.auth.login, { method: 'POST', body: input })),
  logout: () => apiRequest<void>(endpoints.auth.logout, { method: 'POST' }),
};
