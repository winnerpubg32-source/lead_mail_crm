/**
 * Leads data access — `GET /api/v1/leads/` and friends (Phase 5).
 */

import { api, apiUrl } from '@/lib/api/client';
import type {
  BulkActionPayload,
  BulkActionSummary,
  LeadDetail,
  LeadFilterOptions,
  LeadNote,
  LeadStatusVocabulary,
  ListParams,
} from '@/types/lead';
import type { Lead } from '@/types/lead';
import type { PaginatedResponse } from '@/types/api';

export const leadKeys = {
  all: ['leads'] as const,
  list: (params: ListParams) => [...leadKeys.all, 'list', params] as const,
  detail: (id: number) => [...leadKeys.all, 'detail', id] as const,
  statuses: () => [...leadKeys.all, 'statuses'] as const,
  filters: () => [...leadKeys.all, 'filters'] as const,
};

export function fetchLeads(params: ListParams = {}): Promise<PaginatedResponse<Lead>> {
  return api.get<PaginatedResponse<Lead>>('v1/leads/', { query: params });
}

export function fetchLead(id: number): Promise<LeadDetail> {
  return api.get<LeadDetail>(`v1/leads/${id}/`);
}

export function fetchLeadStatuses(): Promise<LeadStatusVocabulary> {
  return api.get<LeadStatusVocabulary>('v1/leads/statuses/');
}

export function fetchLeadFilterOptions(): Promise<LeadFilterOptions> {
  return api.get<LeadFilterOptions>('v1/leads/filters/');
}

export function updateLead(id: number, patch: Partial<Lead>): Promise<Lead> {
  return api.patch<Lead>(`v1/leads/${id}/`, patch);
}

export function addLeadNote(id: number, body: string): Promise<LeadNote> {
  return api.post<LeadNote>(`v1/leads/${id}/notes/`, { body });
}

export function rescoreLead(id: number): Promise<{
  lead_score: number;
  classification: string;
  components: Record<string, number>;
}> {
  return api.post(`v1/leads/${id}/rescore/`);
}

export function bulkAction(payload: BulkActionPayload): Promise<BulkActionSummary> {
  return api.post<BulkActionSummary>('v1/leads/bulk-action/', payload);
}

export async function exportLeadsCsv(params: ListParams = {}): Promise<void> {
  // Bypass the JSON parser and download the blob.
  const url = apiUrl('v1/leads/export/');
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === '' || v === null) continue;
    if (Array.isArray(v)) v.forEach((item) => search.append(k, String(item)));
    else search.append(k, String(v));
  }
  const fullUrl = url + (search.toString() ? `?${search.toString()}` : '');
  const res = await fetch(fullUrl, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to export leads');
  const blob = await res.blob();
  const header = res.headers.get('Content-Disposition') || '';
  const match = /filename="?([^";]+)"?/.exec(header);
  const filename = match?.[1] || `leads_${Date.now()}.csv`;
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}
