import { createAsyncThunk } from '@reduxjs/toolkit';
import { authApi } from '../api/authApi';
import type { LoginInput } from '../types/auth.types';
export const restoreSession = createAsyncThunk('auth/restore', async (_, { signal }) => authApi.restore(signal));
export const login = createAsyncThunk('auth/login', async (input: LoginInput) => authApi.login(input));
export const logout = createAsyncThunk('auth/logout', async () => authApi.logout());
