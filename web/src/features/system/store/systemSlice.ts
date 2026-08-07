import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { fetchMcpTools, type McpTools } from './systemThunks';

export type ConnectionState = 'connecting' | 'live' | 'reconnecting' | 'offline';

const slice = createSlice({
  name: 'system',
  initialState: {
    connection: 'offline' as ConnectionState,
    mcpTools: null as McpTools | null,
    mcpStatus: 'idle' as 'idle' | 'loading' | 'succeeded' | 'failed',
  },
  reducers: {
    connectionChanged: (state, action: PayloadAction<ConnectionState>) => { state.connection = action.payload; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMcpTools.pending, (state) => { state.mcpStatus = 'loading'; })
      .addCase(fetchMcpTools.fulfilled, (state, action) => { state.mcpTools = action.payload; state.mcpStatus = 'succeeded'; })
      .addCase(fetchMcpTools.rejected, (state) => { state.mcpStatus = 'failed'; });
  },
});

export const { connectionChanged } = slice.actions;
export default slice.reducer;
