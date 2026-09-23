/**
 * Backend health probe (`GET /api/health/`).
 *
 * The dashboard calls this in the background to show whether the Django API is
 * reachable. In Phase 1 the mock data switch means the UI works with or without
 * a running backend — but the indicator tells the truth about connectivity.
 */

import { apiUrl } from '@/lib/api/client';
import type { HealthResponse } from '@/types/api';

export const healthKeys = {
  all: ['health'] as const,
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(apiUrl('health/'), { headers: { Accept: 'application/json' } });
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}
