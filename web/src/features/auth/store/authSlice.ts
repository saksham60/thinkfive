import { createSlice } from '@reduxjs/toolkit';
import type { User } from '@/types/common.types';
import type { AsyncStatus } from '@/types/common.types';
import { login, logout, restoreSession } from './authThunks';

interface AuthState { user: User | null; status: AsyncStatus; initialized: boolean; error: string | null }
const initialState: AuthState = { user: null, status: 'idle', initialized: false, error: null };
const authSlice = createSlice({ name: 'auth', initialState, reducers: {}, extraReducers: (builder) => {
  builder.addCase(restoreSession.pending, (s) => { s.status = 'loading'; })
    .addCase(restoreSession.fulfilled, (s, a) => { s.user = a.payload.user; s.status = 'succeeded'; s.initialized = true; })
    .addCase(restoreSession.rejected, (s) => { s.user = null; s.status = 'failed'; s.initialized = true; })
    .addCase(login.pending, (s) => { s.status = 'loading'; s.error = null; })
    .addCase(login.fulfilled, (s, a) => { s.user = a.payload.user; s.status = 'succeeded'; s.initialized = true; })
    .addCase(login.rejected, (s, a) => { s.status = 'failed'; s.error = a.error.message || 'Sign in failed'; })
    .addCase(logout.fulfilled, (s) => { s.user = null; s.status = 'idle'; });
} });
export default authSlice.reducer;
