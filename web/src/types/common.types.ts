export type AsyncStatus = 'idle' | 'loading' | 'succeeded' | 'failed';
export type UserRole = 'customer' | 'analyst' | 'supervisor' | 'admin';
export interface User {
  id: string;
  email: string;
  displayName: string;
  role: UserRole;
  customerId?: string;
}
