import type { User } from '@/types/common.types';
export type SessionResponse = User;
export interface LoginInput { email: string; password: string }
