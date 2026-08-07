export interface CustomerProfile {
  id: string;
  displayName: string;
  email?: string;
}

export interface AccountSummary {
  id: string;
  name: string;
  maskedNumber: string;
  balance: number;
  currency: string;
}

export interface Transaction {
  id: string;
  description: string;
  amount: number;
  currency: string;
  occurredAt: string;
  pending: boolean;
  category?: string;
}

export interface CustomerDashboard {
  profile: CustomerProfile;
  accounts: AccountSummary[];
  recentTransactions: Transaction[];
  totalBalance: number;
  cards: unknown[];
}
