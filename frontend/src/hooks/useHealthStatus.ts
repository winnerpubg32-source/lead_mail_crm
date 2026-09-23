import { useQuery } from '@tanstack/react-query';

import { fetchHealth, healthKeys } from '@/services/health.service';

/**
 * Polls the Django health endpoint.
 *
 * Used by the topbar status pill: it reports "API connected" when
 * `GET /api/health/` answers `{"status": "ok"}` and "API offline" otherwise —
 * which is expected while only the frontend is running.
 */
export function useHealthStatus() {
  return useQuery({
    queryKey: healthKeys.all,
    queryFn: fetchHealth,
    refetchInterval: 60_000,
    retry: 0,
    staleTime: 30_000,
    // A missing backend is a normal state during Phase 1, so failures are not
    // surfaced as errors anywhere in the UI.
    throwOnError: false,
  });
}
