export interface ApiError { status: number; code: string; message: string; details?: unknown }

export const isApiError = (value: unknown): value is ApiError =>
  typeof value === 'object' && value !== null && 'status' in value && 'message' in value;

export function apiErrorMessage(value: unknown): string {
  if (!isApiError(value)) return value instanceof Error ? value.message : 'Request failed';
  if (typeof value.details === 'object' && value.details !== null && 'detail' in value.details) {
    const detail = (value.details as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
  }
  return value.message;
}
