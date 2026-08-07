import { createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { arrayFromEnvelope, asObject, firstValue, numberValue, optionalString, stringValue } from '@/api/mappers';
import type { FraudAlert } from '../types/alert.types';

export function mapAlert(value: unknown, index = 0): FraudAlert {
  const item = asObject(value);
  const rawSeverity = stringValue(item.severity, 'medium').toLowerCase();
  const severity = ['low', 'medium', 'high', 'critical'].includes(rawSeverity) ? rawSeverity as FraudAlert['severity'] : 'medium';
  return {
    id: stringValue(firstValue(item, ['alert_id', 'id']), `alert-${index}`),
    customerId: optionalString(item.customer_id),
    transactionId: optionalString(item.transaction_id),
    title: stringValue(firstValue(item, ['title', 'alert_type', 'reason']), 'Fraud alert'),
    description: optionalString(firstValue(item, ['description', 'reason', 'summary'])),
    riskScore: numberValue(firstValue(item, ['risk_score', 'score'])),
    severity,
    status: stringValue(item.status, 'open').toLowerCase(),
    createdAt: stringValue(firstValue(item, ['created_at', 'detected_at', 'updated_at'])),
  };
}

export const fetchAlerts = createAsyncThunk(
  'alerts/fetch',
  async (customerId: string | undefined, { signal }) => {
    const query = customerId ? `?customer_id=${encodeURIComponent(customerId)}` : '';
    const result = await apiRequest<unknown>(`${endpoints.alerts}${query}`, { signal });
    return arrayFromEnvelope(result, 'alerts').map(mapAlert);
  },
);
