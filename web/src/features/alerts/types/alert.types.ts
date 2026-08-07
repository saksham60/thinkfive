export interface FraudAlert {
  id: string;
  customerId?: string;
  transactionId?: string;
  title: string;
  description?: string;
  riskScore: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: string;
  createdAt: string;
}
