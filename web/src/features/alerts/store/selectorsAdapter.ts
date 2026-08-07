import { createEntityAdapter } from '@reduxjs/toolkit'; import type { FraudAlert } from '../types/alert.types'; export const alertsAdapter=createEntityAdapter<FraudAlert>();
