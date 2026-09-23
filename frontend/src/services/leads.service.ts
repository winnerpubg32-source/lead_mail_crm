/**
 * Leads data access — `GET /api/v1/leads/` and friends.
 *
 * Unlike the dashboard service these endpoints are real (Phase 2), so there is
 * no mock branch here: the pages always read from Django.
 */

import { api } from '@/lib/api/client';
import type { Lead, LeadStatusVocabulary, ListParams } from '@/types/lead';
import type { PaginatedResponse } from '@/types/api';

export const leadKeys = {
  all: ['leads'] as const,
  list: (params: ListParams) => [...leadKeys.all, 'list', params] as const,
  detail: (id: number) => [...leadKeys.all, 'detail', id] as const,
  statuses: () => [...leadKeys.all, 'statuses'] as const,
};

export function fetchLeads(params: ListParams = {}): Promise<PaginatedResponse<Lead>> {
  return api.get<PaginatedResponse<Lead>>('v1/leads/', { query: params });
}

export function fetchLead(id: number): Promise<Lead> {
  return api.get<Lead>(`v1/leads/${id}/`);
}

export function fetchLeadStatuses(): Promise<LeadStatusVocabulary> {
  return api.get<LeadStatusVocabulary>('v1/leads/statuses/');
}
