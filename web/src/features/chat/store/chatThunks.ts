import { createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { ChatResponse } from '../types/chat.types';
import type { ChatMessage } from '../types/chat.types';

interface BackendChatResponse { conversation_id: string; run_id: string; status: string }
interface BackendMessageResponse {
  message_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  run_id?: string | null;
}

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

const wait = (milliseconds: number, signal: AbortSignal) => new Promise<void>((resolve, reject) => {
  const onAbort = () => {
    window.clearTimeout(timer);
    reject(new DOMException('Aborted', 'AbortError'));
  };
  const timer = window.setTimeout(() => {
    signal.removeEventListener('abort', onAbort);
    resolve();
  }, milliseconds);
  signal.addEventListener('abort', onAbort, { once: true });
});

export const reconcileChatResponse = createAsyncThunk(
  'chat/reconcile',
  async (input: { conversationId: string; runId: string }, { signal }) => {
    // SSE remains the fast path. Persisted conversation history is the
    // reconciliation path when a serverless stream reconnect loses an event.
    const deadline = Date.now() + 120_000;
    while (Date.now() < deadline) {
      const messages = await apiRequest<BackendMessageResponse[]>(
        endpoints.chatMessages(input.conversationId, input.runId),
        { signal },
      );
      const response = messages.find((message) => message.role === 'assistant' && message.run_id === input.runId);
      if (response) {
        return {
          id: `assistant-${input.runId}`,
          role: 'assistant',
          content: response.content,
        } satisfies ChatMessage;
      }
      await wait(1_500, signal);
    }
    throw new Error('The response is taking longer than expected. Please try again.');
  },
);
