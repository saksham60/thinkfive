import type { RootState } from '@/app/store';
export const selectCurrentUser = (state: RootState) => state.auth.user;
export const selectIsAuthenticated = (state: RootState) => state.auth.user !== null;
export const selectUserRole = (state: RootState) => state.auth.user?.role;
export const selectAuthInitialized = (state: RootState) => state.auth.initialized;
