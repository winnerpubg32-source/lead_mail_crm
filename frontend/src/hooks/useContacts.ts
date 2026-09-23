import { useQuery } from '@tanstack/react-query';

import { contactKeys, fetchContacts } from '@/services/contacts.service';
import type { ListParams } from '@/types/lead';

/** Paginated contact list. */
export function useContacts(params: ListParams) {
  return useQuery({
    queryKey: contactKeys.list(params),
    queryFn: () => fetchContacts(params),
    placeholderData: (previous) => previous,
  });
}
