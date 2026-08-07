# ThinkFive web

Pure React, TypeScript, and Vite SPA for ThinkFive. Pages render feature state; Redux Toolkit feature slices and `createAsyncThunk` workflows call the centralized credentialed API client. A single SSE connection projects backend events into Redux.

## Architecture

```
Pages → Components → Redux features → API client / SSE → Backend
```

- `src/app`: store, typed hooks, providers, and router
- `src/features/<feature>`: API adapters, thunks, slices, selectors, hooks, and domain types
- `src/components/<Component>`: one folder per reusable component
- `src/pages/<Page>` and `src/layouts/<Layout>`: one folder per route/layout
- `src/api`: HTTP transport and endpoint registry
- `src/sse`: single credentialed event stream and Redux dispatch mapping
- `src/config/env.ts`: the only raw environment access

Authentication is a secure backend-owned HttpOnly session. On startup the app calls `GET /api/auth/me`; credentials are included on HTTP and SSE requests. Roles and tokens are never stored in local storage. The backend must allow the deployed Vercel origin and credentialed cross-origin cookies.

## Development

Copy `.env.example` to `.env.local` and set the one frontend backend setting:

```
VITE_API_BASE_URL=http://localhost:8000
```

Then run `npm install` and `npm run dev`. Quality commands are `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build`.

## Vercel

Import `web` as the project root, set `VITE_API_BASE_URL`, use `npm run build`, and publish `dist`. `vercel.json` provides the SPA fallback for deep links and requires no Node server, function, or API proxy.
