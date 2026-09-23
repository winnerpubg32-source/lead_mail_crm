import { useQuery } from '@tanstack/react-query';

import { fetchLeads, fetchLeadStatuses, leadKeys } from '@/services/leads.service';
import type { ListParams } from '@/types/lead';

/** Paginated lead list. `placeholderData` keeps the previous page visible while fetching. */
export function useLeads(params: ListParams) {
  return useQuery({
    queryKey: leadKeys.list(params),
    queryFn: () => fetchLeads(params),
    placeholderData: (previous) => previous,
  });
}

/** Lead + e-mail status vocabulary with per-status counts for the filter chips. */
export function useLeadStatuses() {
  return useQuery({
    queryKey: leadKeys.statuses(),
    queryFn: fetchLeadStatuses,
    staleTime: 60_000,
  });
}
