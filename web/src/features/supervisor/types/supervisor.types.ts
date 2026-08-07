export interface SupervisorMetrics {
  runs: Record<string, number>;
  eventCounts: Record<string, number>;
  waitingHitlCount: number;
}

export interface SupervisorRun {
  id: string;
  status: string;
  customerId?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface SimulatorInput { customerId: string; amount: number; description: string }
