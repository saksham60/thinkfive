import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { ChatMessage } from '../types/chat.types';
import { reconcileChatResponse, submitChatMessage } from './chatThunks';

type ChatStatus = 'idle' | 'loading' | 'succeeded' | 'failed';

const initialState = {
  messages: [] as ChatMessage[],
  conversationId: null as string | null,
  runId: null as string | null,
  status: 'idle' as ChatStatus,
  error: null as string | null,
};

function upsertMessage(messages: ChatMessage[], message: ChatMessage) {
  const index = messages.findIndex((item) => item.id === message.id);
  if (index >= 0) messages[index] = message;
  else messages.push(message);
}

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    messageReceived: (state, action: PayloadAction<ChatMessage>) => {
      upsertMessage(state.messages, action.payload);
      if (action.payload.id === `assistant-${state.runId}`) {
        state.status = action.payload.role === 'assistant' ? 'succeeded' : 'failed';
        state.error = action.payload.role === 'assistant' ? null : action.payload.content;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitChatMessage.pending, (state, action) => {
        state.status = 'loading';
        state.error = null;
        state.messages.push({ id: crypto.randomUUID(), role: 'user', content: action.meta.arg.message });
      })
      .addCase(submitChatMessage.fulfilled, (state, action) => {
        state.status = 'loading';
        state.conversationId = action.payload.conversationId;
        state.runId = action.payload.runId;
      })
      .addCase(submitChatMessage.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Unable to send message';
      })
      .addCase(reconcileChatResponse.fulfilled, (state, action) => {
        upsertMessage(state.messages, action.payload);
        if (action.meta.arg.runId === state.runId) {
          state.status = 'succeeded';
          state.error = null;
        }
      })
      .addCase(reconcileChatResponse.rejected, (state, action) => {
        if (action.meta.aborted || action.meta.arg.runId !== state.runId || state.status === 'succeeded') return;
        state.status = 'failed';
        state.error = action.error.message || 'Unable to retrieve the response';
      });
  },
});

export const { messageReceived } = chatSlice.actions;
export default chatSlice.reducer;
