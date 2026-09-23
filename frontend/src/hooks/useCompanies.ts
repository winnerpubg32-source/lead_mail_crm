import { useQuery } from '@tanstack/react-query';

import { companyKeys, fetchCompanies } from '@/services/companies.service';
import type { ListParams } from '@/types/lead';

/** Paginated company list. */
export function useCompanies(params: ListParams) {
  return useQuery({
    queryKey: companyKeys.list(params),
    queryFn: () => fetchCompanies(params),
    placeholderData: (previous) => previous,
  });
}
