import { API_BASE_URL } from '@/config/env';
import { serverEventTypes, type ServerEvent } from './types';

export interface EventStream { close(): void }

export function connectEventStream(
  conversationId: string,
  onMessage: (value: ServerEvent) => void,
  onOpen: () => void,
  onError: () => void,
): EventStream {
  const url = new URL('/api/events', API_BASE_URL || window.location.origin);
  url.searchParams.set('conversation_id', conversationId);
  const source = new EventSource(url, { withCredentials: true });
  source.onopen = onOpen;
  source.onerror = onError;

  for (const eventType of serverEventTypes) {
    source.addEventListener(eventType, (raw) => {
      if (eventType === 'heartbeat' || eventType === 'connection.ready') return;
      try {
        const event = raw as MessageEvent<string>;
        const parsed = JSON.parse(event.data) as unknown;
        const envelope = typeof parsed === 'object' && parsed !== null ? parsed as Record<string, unknown> : {};
        const payload = typeof envelope.payload === 'object' && envelope.payload !== null
          ? envelope.payload as Record<string, unknown>
          : envelope;
        onMessage({ type: typeof envelope.type === 'string' ? envelope.type : eventType, payload, id: event.lastEventId || undefined });
      } catch {
        onError();
      }
    });
  }
  return source;
}
