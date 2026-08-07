import { createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { arrayFromEnvelope, asObject, firstValue, optionalString, stringValue } from '@/api/mappers';
import type { Approval } from '../types/approval.types';

export function mapApproval(value: unknown, index = 0): Approval {
  const item = asObject(value);
  const metadata = asObject(item.metadata);
  return {
    id: stringValue(firstValue(item, ['approval_id', 'id', 'interrupt_id']), `approval-${index}`),
    caseId: optionalString(item.case_id),
    customerId: optionalString(item.customer_id),
    runId: optionalString(item.run_id),
    summary: stringValue(firstValue(metadata, ['summary', 'reason']) ?? firstValue(item, ['interrupt_type', 'summary']), 'Human review required'),
    status: stringValue(item.status, 'waiting').toLowerCase(),
    requestedAt: stringValue(firstValue(item, ['created_at', 'requested_at'])),
  };
}

export const fetchApprovals = createAsyncThunk('approvals/fetch', async (_, { signal }) => {
  const result = await apiRequest<unknown>(endpoints.approvals.pending, { signal });
  return arrayFromEnvelope(result, 'pending').map(mapApproval);
});

async function decide(id: string, decision: 'approve' | 'reject', note?: string) {
  await apiRequest<unknown>(`${endpoints.approvals.root}/${encodeURIComponent(id)}/${decision}`, {
    method: 'POST',
    body: { note: note || null },
  });
  return { id, status: decision === 'approve' ? 'approved' : 'rejected' };
}

export const approveAction = createAsyncThunk('approvals/approve', ({ id, note }: { id: string; note?: string }) => decide(id, 'approve', note));
export const rejectAction = createAsyncThunk('approvals/reject', ({ id, note }: { id: string; note?: string }) => decide(id, 'reject', note));
