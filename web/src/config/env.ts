import { z } from 'zod';

const schema = z.string().url().transform((value) => value.replace(/\/$/, ''));
const raw = import.meta.env.VITE_API_BASE_URL as string | undefined;

if (import.meta.env.PROD && !raw) throw new Error('VITE_API_BASE_URL is required in production');

export const API_BASE_URL = schema.parse(raw || 'http://localhost:8000');
