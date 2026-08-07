import { createSlice } from '@reduxjs/toolkit';
import type { SupervisorMetrics, SupervisorRun } from '../types/supervisor.types';
import { fetchSupervisorMetrics, fetchSupervisorRuns, runEvaluation, triggerSimulator } from './supervisorThunks';

const slice = createSlice({
  name: 'supervisor',
  initialState: {
    metrics: null as SupervisorMetrics | null,
    runs: [] as SupervisorRun[],
    status: 'idle' as 'idle' | 'loading' | 'succeeded' | 'failed',
    simulatorStatus: 'idle' as 'idle' | 'loading' | 'succeeded' | 'failed',
    evaluationStatus: 'idle' as 'idle' | 'loading' | 'succeeded' | 'failed',
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSupervisorMetrics.pending, (state) => { state.status = 'loading'; })
      .addCase(fetchSupervisorMetrics.fulfilled, (state, action) => { state.metrics = action.payload; state.status = 'succeeded'; })
      .addCase(fetchSupervisorMetrics.rejected, (state) => { state.status = 'failed'; })
      .addCase(fetchSupervisorRuns.fulfilled, (state, action) => { state.runs = action.payload; })
      .addCase(triggerSimulator.pending, (state) => { state.simulatorStatus = 'loading'; })
      .addCase(triggerSimulator.fulfilled, (state) => { state.simulatorStatus = 'succeeded'; })
      .addCase(triggerSimulator.rejected, (state) => { state.simulatorStatus = 'failed'; })
      .addCase(runEvaluation.pending, (state) => { state.evaluationStatus = 'loading'; })
      .addCase(runEvaluation.fulfilled, (state) => { state.evaluationStatus = 'succeeded'; })
      .addCase(runEvaluation.rejected, (state) => { state.evaluationStatus = 'failed'; });
  },
});

export default slice.reducer;
