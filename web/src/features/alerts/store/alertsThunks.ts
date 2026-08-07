import { createAsyncThunk } from '@reduxjs/toolkit'; import { apiRequest } from '@/api/client'; import { endpoints } from '@/api/endpoints'; import type { FraudAlert } from '../types/alert.types';
export const fetchAlerts = createAsyncThunk('alerts/fetch', (_, { signal }) => apiRequest<FraudAlert[]>(endpoints.alerts, { signal }));
