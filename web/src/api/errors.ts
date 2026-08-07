export interface ApiError { status: number; code: string; message: string; details?: unknown }

export const isApiError = (value: unknown): value is ApiError =>
  typeof value === 'object' && value !== null && 'status' in value && 'message' in value;
