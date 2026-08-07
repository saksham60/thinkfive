export interface Approval {
  id: string;
  caseId?: string;
  customerId?: string;
  summary: string;
  status: string;
  requestedAt: string;
  runId?: string;
}
