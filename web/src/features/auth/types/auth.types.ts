import type { User } from '@/types/common.types';
export interface SessionResponse { user: User }
export interface LoginInput { email: string; password: string }
