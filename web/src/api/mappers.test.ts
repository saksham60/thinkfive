import { describe, expect, it } from 'vitest';
import { mapAlert } from '@/features/alerts/store/alertsThunks';
import { mapCase } from '@/features/cases/store/casesThunks';
import { mapApproval } from '@/features/approvals/store/approvalsThunks';

describe('backend contract mappers', () => {
  it('maps snake_case fraud alerts', () => {
    expect(mapAlert({ alert_id: 'a-1', alert_type: 'CARD_NOT_PRESENT', risk_score: '92', severity: 'HIGH' })).toMatchObject({
      id: 'a-1', title: 'CARD_NOT_PRESENT', riskScore: 92, severity: 'high', status: 'open',
    });
  });

  it('maps MCP cases and notes', () => {
    expect(mapCase({ case_id: 'c-1', case_type: 'FRAUD', status: 'OPEN', notes: [{ note_id: 'n-1', content: 'Reviewed' }] })).toMatchObject({
      id: 'c-1', title: 'FRAUD', status: 'open', notes: [{ id: 'n-1', body: 'Reviewed' }],
    });
  });

  it('maps workflow interrupts to approvals', () => {
    expect(mapApproval({ approval_id: 'p-1', case_id: 'c-1', status: 'WAITING', metadata: { reason: 'Block card' } })).toMatchObject({
      id: 'p-1', caseId: 'c-1', status: 'waiting', summary: 'Block card',
    });
  });
});
