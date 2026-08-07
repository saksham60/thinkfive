import { createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { arrayFromEnvelope, asObject, firstValue, numberValue, optionalString, stringValue } from '@/api/mappers';
import type { SimulatorInput, SupervisorMetrics, SupervisorRun } from '../types/supervisor.types';

const numberRecord = (value: unknown): Record<string, number> =>
  Object.fromEntries(Object.entries(asObject(value)).map(([key, item]) => [key, numberValue(item)]));

export const fetchSupervisorMetrics = createAsyncThunk('supervisor/metrics', async (_, { signal }) => {
  const value = asObject(await apiRequest<unknown>(endpoints.supervisor.metrics, { signal }));
  return {
    runs: numberRecord(value.runs),
    eventCounts: numberRecord(value.event_counts),
    waitingHitlCount: numberValue(value.waiting_hitl_count),
  } satisfies SupervisorMetrics;
});

export const fetchSupervisorRuns = createAsyncThunk('supervisor/runs', async (_, { signal }) => {
  const value = await apiRequest<unknown>(`${endpoints.supervisor.runs}?limit=25`, { signal });
  return arrayFromEnvelope(value, 'runs').map((raw, index): SupervisorRun => {
    const item = asObject(raw);
    return {
      id: stringValue(firstValue(item, ['run_id', 'id']), `run-${index}`),
      status: stringValue(item.status, 'unknown'),
      customerId: optionalString(item.customer_id),
      startedAt: optionalString(firstValue(item, ['started_at', 'created_at'])),
      completedAt: optionalString(item.completed_at),
    };
  });
});

export const triggerSimulator = createAsyncThunk('supervisor/simulator', (input: SimulatorInput) =>
  apiRequest<unknown>(endpoints.supervisor.simulator, {
    method: 'POST',
    body: { customer_id: input.customerId, amount: input.amount, description: input.description },
  }),
);

export const runEvaluation = createAsyncThunk('supervisor/evaluation', () =>
  apiRequest<unknown>(endpoints.supervisor.evaluation, { method: 'POST' }),
);
