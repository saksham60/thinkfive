import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { LoginInput, SessionResponse } from '../types/auth.types';
export const authApi = {
  restore: (signal?: AbortSignal) => apiRequest<SessionResponse>(endpoints.auth.me, { signal }),
  login: (input: LoginInput) => apiRequest<SessionResponse>(endpoints.auth.login, { method: 'POST', body: input }),
  logout: () => apiRequest<void>(endpoints.auth.logout, { method: 'POST' }),
};
