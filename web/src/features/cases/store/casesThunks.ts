import { createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { arrayFromEnvelope, asArray, asObject, firstValue, optionalString, stringValue } from '@/api/mappers';
import type { CaseNote, CaseRecord } from '../types/case.types';

function mapNote(value: unknown, index: number): CaseNote {
  const item = asObject(value);
  return {
    id: stringValue(firstValue(item, ['note_id', 'id']), `note-${index}`),
    body: stringValue(firstValue(item, ['content', 'body'])),
    createdAt: stringValue(item.created_at),
  };
}

export function mapCase(value: unknown, index = 0): CaseRecord {
  const item = asObject(value);
  return {
    id: stringValue(firstValue(item, ['case_id', 'id']), `case-${index}`),
    customerId: optionalString(item.customer_id),
    alertId: optionalString(item.alert_id),
    title: stringValue(firstValue(item, ['title', 'case_type', 'summary']), 'Investigation case'),
    status: stringValue(item.status, 'open').toLowerCase(),
    priority: optionalString(item.priority),
    updatedAt: stringValue(firstValue(item, ['updated_at', 'created_at'])),
    notes: asArray(item.notes).map(mapNote),
  };
}

export const fetchCases = createAsyncThunk(
  'cases/fetch',
  async (customerId: string | undefined, { signal }) => {
    const query = customerId ? `?customer_id=${encodeURIComponent(customerId)}` : '';
    const result = await apiRequest<unknown>(`${endpoints.cases}${query}`, { signal });
    return arrayFromEnvelope(result, 'cases').map(mapCase);
  },
);

export const addCaseNote = createAsyncThunk(
  'cases/addNote',
  async ({ id, body }: { id: string; body: string }) => {
    await apiRequest<unknown>(`${endpoints.cases}/${encodeURIComponent(id)}/notes`, {
      method: 'POST',
      body: { content: body, note_type: 'GENERAL' },
    });
    return { id, body };
  },
);
