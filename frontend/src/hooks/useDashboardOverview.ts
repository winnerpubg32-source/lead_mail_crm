import { useQuery } from '@tanstack/react-query';

import { dashboardKeys, fetchDashboardOverview } from '@/services/dashboard.service';
import type { DashboardOverview } from '@/types/dashboard';

/**
 * Single hook feeding the whole dashboard.
 *
 * Returns the standard React Query result (isPending / isError / data / refetch)
 * which the page maps onto loading, error and empty states.
 */
export function useDashboardOverview() {
  return useQuery<DashboardOverview>({
    queryKey: dashboardKeys.overview(),
    queryFn: ({ signal }) => fetchDashboardOverview(signal),
  });
}
