import { afterEach, describe, expect, it, vi } from 'vitest';
import eventsProxy from '../../api/events';

describe('Vercel SSE proxy', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('forwards the session cookie and event cursor to Render', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('event: connection.ready\n\n', {
      status: 200,
      headers: { 'Content-Type': 'text/event-stream' },
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await eventsProxy.fetch(new Request('https://thinkfive.vercel.app/api/events?conversation_id=conversation-1', {
      headers: { Cookie: 'thinkfive_session=session', 'Last-Event-ID': '12' },
    }));

    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toBe('text/event-stream');
    expect(fetchMock).toHaveBeenCalledWith(
      expect.objectContaining({ href: expect.stringContaining('conversation_id=conversation-1') }),
      expect.objectContaining({ headers: expect.objectContaining({}) }),
    );
    const options = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = options.headers as Headers;
    expect(headers.get('cookie')).toBe('thinkfive_session=session');
    expect(headers.get('last-event-id')).toBe('12');
  });
});
