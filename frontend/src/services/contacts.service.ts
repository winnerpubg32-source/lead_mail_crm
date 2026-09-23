/** Contacts data access — `GET /api/v1/contacts/`. */

import { api } from '@/lib/api/client';
import type { PaginatedResponse } from '@/types/api';
import type { Contact, ListParams } from '@/types/lead';

export const contactKeys = {
  all: ['contacts'] as const,
  list: (params: ListParams) => [...contactKeys.all, 'list', params] as const,
  detail: (id: number) => [...contactKeys.all, 'detail', id] as const,
};

export function fetchContacts(params: ListParams = {}): Promise<PaginatedResponse<Contact>> {
  return api.get<PaginatedResponse<Contact>>('v1/contacts/', { query: params });
}

export function fetchContact(id: number): Promise<Contact> {
  return api.get<Contact>(`v1/contacts/${id}/`);
}
