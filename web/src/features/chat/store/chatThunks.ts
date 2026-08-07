import { createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { ChatResponse } from '../types/chat.types';

interface BackendChatResponse { conversation_id: string; run_id: string; status: string }

export const submitChatMessage = createAsyncThunk(
  'chat/submit',
  async (input: { message: string; conversationId?: string }) => {
    const response = await apiRequest<BackendChatResponse>(endpoints.chat, {
      method: 'POST',
      body: { message: input.message, conversation_id: input.conversationId || null },
    });
    return {
      conversationId: response.conversation_id,
      runId: response.run_id,
      status: response.status,
    } satisfies ChatResponse;
  },
);
