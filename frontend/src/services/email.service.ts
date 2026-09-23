import { api } from '@/lib/api/client';
import type { DailyEmailUsage } from '@/types/email';

export const emailKeys = {
  all: ['email'] as const,
  usage: () => [...emailKeys.all, 'usage'] as const,
};

export function fetchDailyEmailUsage(): Promise<DailyEmailUsage> {
  return api.get<DailyEmailUsage>('v1/email/usage/');
}
