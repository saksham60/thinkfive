import { configureStore } from '@reduxjs/toolkit';
import { afterEach, describe, expect, it, vi } from 'vitest';
import chatReducer from './chatSlice';
import { reconcileChatResponse, submitChatMessage } from './chatThunks';

const createStore = () => configureStore({ reducer: { chat: chatReducer } });

describe('chat response reconciliation', () => {
  afterEach(() => vi.restoreAllMocks());

  it('adds the persisted assistant response when SSE delivery is missed', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify({
        conversation_id: 'conversation-1', run_id: 'run-1', status: 'QUEUED',
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{
        message_id: 'message-1', role: 'assistant', content: 'Your balance is $500.',
        created_at: new Date().toISOString(), run_id: 'run-1',
      }]), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    const store = createStore();

    const submitted = await store.dispatch(submitChatMessage({ message: 'What is my balance?' })).unwrap();
    await store.dispatch(reconcileChatResponse(submitted)).unwrap();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(store.getState().chat.messages).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: 'assistant-run-1', role: 'assistant', content: 'Your balance is $500.' }),
    ]));
    expect(store.getState().chat.status).toBe('succeeded');
  });
});
