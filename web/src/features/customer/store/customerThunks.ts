import { createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { asArray, asObject, booleanValue, firstValue, numberValue, optionalString, stringValue } from '@/api/mappers';
import type { AccountSummary, CustomerDashboard, Transaction } from '../types/customer.types';

function mapAccount(value: unknown, index: number): AccountSummary {
  const item = asObject(value);
  const mask = stringValue(firstValue(item, ['mask', 'masked_number', 'account_mask']));
  return {
    id: stringValue(firstValue(item, ['account_id', 'id']), `account-${index}`),
    name: stringValue(firstValue(item, ['name', 'official_name', 'type']), 'Account'),
    maskedNumber: mask ? `•••• ${mask.slice(-4)}` : 'Number unavailable',
    balance: numberValue(firstValue(item, ['current_balance', 'balance', 'available_balance'])),
    currency: stringValue(firstValue(item, ['currency', 'iso_currency_code']), 'USD').toUpperCase(),
  };
}

function mapTransaction(value: unknown, index: number): Transaction {
  const item = asObject(value);
  const categories = asArray(item.category).map(String);
  return {
    id: stringValue(firstValue(item, ['transaction_id', 'id']), `transaction-${index}`),
    description: stringValue(firstValue(item, ['merchant_name', 'transaction_name', 'name', 'description']), 'Transaction'),
    amount: numberValue(item.amount),
    currency: stringValue(firstValue(item, ['currency', 'iso_currency_code']), 'USD').toUpperCase(),
    occurredAt: stringValue(firstValue(item, ['date', 'authorized_date', 'occurred_at', 'created_at'])),
    pending: booleanValue(item.pending),
    category: optionalString(categories[0]),
  };
}

function mapDashboard(value: unknown): CustomerDashboard {
  const root = asObject(value);
  const profile = asObject(root.profile);
  const accountSummary = asObject(root.account_summary);
  const recent = asObject(root.recent_transactions);
  const accountValues = asArray(accountSummary.accounts ?? root.account_summary);
  const transactionValues = asArray(recent.transactions ?? root.recent_transactions);
  const accounts = accountValues.map(mapAccount);
  return {
    profile: {
      id: stringValue(firstValue(profile, ['customer_id', 'id'])),
      displayName: stringValue(firstValue(profile, ['display_name', 'name']), 'Customer'),
      email: optionalString(profile.email),
    },
    accounts,
    recentTransactions: transactionValues.map(mapTransaction),
    totalBalance: numberValue(firstValue(accountSummary, ['total_balance', 'total_current_balance']), accounts.reduce((sum, account) => sum + account.balance, 0)),
    cards: asArray(root.cards),
  };
}

export const fetchCustomerDashboard = createAsyncThunk(
  'customer/dashboard',
  async (_, { signal }) => mapDashboard(await apiRequest<unknown>(endpoints.customer.dashboard, { signal })),
);
