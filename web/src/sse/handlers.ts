import type { AppDispatch } from '@/app/store';
import { asObject, firstValue, stringValue } from '@/api/mappers';
import { mapAlert } from '@/features/alerts/store/alertsThunks';
import { alertUpserted } from '@/features/alerts/store/alertsSlice';
import { mapCase } from '@/features/cases/store/casesThunks';
import { caseUpserted } from '@/features/cases/store/casesSlice';
import { mapApproval } from '@/features/approvals/store/approvalsThunks';
import { approvalUpserted } from '@/features/approvals/store/approvalsSlice';
import { messageReceived } from '@/features/chat/store/chatSlice';
import type { ServerEvent } from './types';

export function dispatchServerEvent(dispatch: AppDispatch, event: ServerEvent) {
  const payload = asObject(event.payload);
  const runId = stringValue(firstValue(payload, ['run_id', 'message_id']), event.id || crypto.randomUUID());
  switch (event.type) {
    case 'fraud.alert.created':
    case 'fraud.alert.updated':
      dispatch(alertUpserted(mapAlert(payload)));
      break;
    case 'case.created':
    case 'case.updated':
      dispatch(caseUpserted(mapCase(payload)));
      break;
    case 'approval.requested':
    case 'workflow.interrupted':
      dispatch(approvalUpserted(mapApproval(payload)));
      break;
    case 'assistant.delta':
    case 'assistant.message':
      dispatch(messageReceived({ id: `assistant-${runId}`, role: 'assistant', content: stringValue(firstValue(payload, ['delta', 'content', 'message'])), streaming: event.type === 'assistant.delta' }));
      break;
    case 'chat.completed':
      dispatch(messageReceived({ id: `assistant-${runId}`, role: 'assistant', content: stringValue(firstValue(payload, ['response', 'content', 'message']), 'Completed without a text response.') }));
      break;
    case 'chat.failed':
      dispatch(messageReceived({ id: `assistant-${runId}`, role: 'system', content: stringValue(firstValue(payload, ['error', 'message']), 'The workflow failed. Please try again.') }));
      break;
  }
}
