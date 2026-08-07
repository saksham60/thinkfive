const raw = import.meta.env.VITE_API_BASE_URL as string | undefined;

if (raw && !URL.canParse(raw)) throw new Error('VITE_API_BASE_URL must be an absolute URL when set');

// Empty means same-origin. Vercel and the Vite dev server proxy /api to Render,
// which keeps the HttpOnly session cookie first-party in the browser.
export const API_BASE_URL = raw?.replace(/\/$/, '') || '';
