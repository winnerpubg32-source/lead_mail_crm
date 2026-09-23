/**
 * Dashboard data access.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * THE SINGLE SWITCH POINT between placeholder data and the Django API.
 *
 * Phase 1: `env.useMockData === true` → resolves `data/mock/dashboard.mock.ts`
 * with simulated latency so loading/error states are exercised in the UI.
 *
 * Phase 2+: `VITE_USE_MOCK_DATA=false` → calls
 * `GET {VITE_API_URL}/v1/analytics/dashboard/`, which must return a
 * `DashboardOverview` payload (see `src/types/dashboard.ts`). Components,
 * hooks and pages stay untouched.
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { buildMockDashboardOverview } from '@/data/mock/dashboard.mock';
import { api } from '@/lib/api/client';
import { MOCK_LATENCY_MS, env } from '@/lib/env';
import type { DashboardOverview } from '@/types/dashboard';

/** React Query cache keys for every dashboard query. */
export const dashboardKeys = {
  all: ['dashboard'] as const,
  overview: () => [...dashboardKeys.all, 'overview'] as const,
  activity: (range: string) => [...dashboardKeys.all, 'activity', range] as const,
};

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(value), ms);
  });
}

/**
 * Fetch everything the dashboard needs in one round trip.
 * The backend counterpart is `apps/analytics` (`GET /api/v1/analytics/dashboard/`).
 */
export async function fetchDashboardOverview(signal?: AbortSignal): Promise<DashboardOverview> {
  if (env.useMockData) {
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
    return delay(buildMockDashboardOverview());
  }

  return api.get<DashboardOverview>('v1/analytics/dashboard/', { signal });
}

/**
 * Placeholder for the "Today's outreach" timeline endpoint
 * (`GET /api/v1/email/activity/?range=today`).
 */
export async function fetchTodaysOutreach(signal?: AbortSignal) {
  const overview = await fetchDashboardOverview(signal);
  return overview.todaysOutreach;
}
