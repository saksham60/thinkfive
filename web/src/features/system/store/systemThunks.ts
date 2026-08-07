import { createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { asArray, asObject } from '@/api/mappers';

export interface McpTools { banking: string[]; fraud: string[]; case: string[] }

export const fetchMcpTools = createAsyncThunk('system/mcpTools', async (_, { signal }) => {
  const value = asObject(await apiRequest<unknown>(endpoints.system.mcpTools, { signal }));
  return {
    banking: asArray(value.banking).map(String),
    fraud: asArray(value.fraud).map(String),
    case: asArray(value.case).map(String),
  } satisfies McpTools;
});
