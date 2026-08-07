export interface CaseNote { id: string; body: string; createdAt: string }
export interface CaseRecord {
  id: string;
  customerId?: string;
  alertId?: string;
  title: string;
  status: string;
  priority?: string;
  updatedAt: string;
  notes?: CaseNote[];
}
