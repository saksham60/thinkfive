const backendBaseUrl = process.env.BACKEND_BASE_URL || 'https://thinkfive.onrender.com';

export default {
  async fetch(request: Request): Promise<Response> {
    if (request.method !== 'GET') return new Response('Method not allowed', { status: 405 });

    const incomingUrl = new URL(request.url);
    const upstreamUrl = new URL('/api/events', backendBaseUrl);
    upstreamUrl.search = incomingUrl.search;

    const headers = new Headers({ Accept: 'text/event-stream' });
    const cookie = request.headers.get('cookie');
    const lastEventId = request.headers.get('last-event-id');
    if (cookie) headers.set('cookie', cookie);
    if (lastEventId) headers.set('last-event-id', lastEventId);

    const upstream = await fetch(upstreamUrl, {
      headers,
      redirect: 'manual',
      signal: request.signal,
    });

    const responseHeaders = new Headers({
      'Cache-Control': 'no-cache, no-transform',
      'Content-Type': upstream.headers.get('content-type') || 'text/event-stream',
      'X-Accel-Buffering': 'no',
    });
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  },
};
