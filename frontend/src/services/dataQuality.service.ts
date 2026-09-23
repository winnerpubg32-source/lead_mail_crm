/**
 * Data-quality API client (Phase 4).
 *
 * Endpoints are mounted at /api/v1/data-quality/*.
 */

import { api } from '@/lib/api/client';
import type {
  DataQualityStats,
  DetectDuplicatesResult,
  DuplicateGroup,
  DuplicateGroupList,
  MergeAuditEntry,
  MergeAuditList,
  MissingEmailLead,
  MissingEmailList,
} from '@/types/dataQuality';
import type { Lead, ListParams } from '@/types/lead';

export const dataQualityKeys = {
  all: ['data-quality'] as const,
  stats: () => [...dataQualityKeys.all, 'stats'] as const,
  duplicates: (params: ListParams) => [...dataQualityKeys.all, 'duplicates', params] as const,
  duplicate: (id: number) => [...dataQualityKeys.all, 'duplicate', id] as const,
  missingEmail: (params: ListParams) => [...dataQualityKeys.all, 'missing-email', params] as const,
  merges: (params: ListParams) => [...dataQualityKeys.all, 'merges', params] as const,
};

export function fetchDataQualityStats(): Promise<DataQualityStats> {
  return api.get<DataQualityStats>('v1/data-quality/stats/');
}

export function fetchDuplicateGroups(params: ListParams = {}): Promise<DuplicateGroupList> {
  return api.get<DuplicateGroupList>('v1/data-quality/duplicates/', {
    query: { ...params, status: params.status ?? 'OPEN' },
  });
}

export function fetchDuplicateGroup(id: number): Promise<DuplicateGroup> {
  return api.get<DuplicateGroup>(`v1/data-quality/duplicates/${id}/`);
}

export function runDuplicateDetection(clearExisting = false): Promise<DetectDuplicatesResult> {
  return api.post<DetectDuplicatesResult>('v1/data-quality/duplicates/detect/', {
    clear_existing: clearExisting,
  });
}

export async function mergeDuplicateGroup(
  id: number,
  winnerId: number,
  loserId: number,
): Promise<MergeAuditEntry> {
  return api.post<MergeAuditEntry>(`v1/data-quality/duplicates/${id}/merge/`, {
    winner: winnerId,
    loser: loserId,
  });
}

export async function keepBothGroup(id: number): Promise<DuplicateGroup> {
  return api.post<DuplicateGroup>(`v1/data-quality/duplicates/${id}/keep-both/`, {});
}

export async function ignoreGroup(id: number): Promise<DuplicateGroup> {
  return api.post<DuplicateGroup>(`v1/data-quality/duplicates/${id}/ignore/`, {});
}

export function fetchMissingEmailLeads(params: ListParams = {}): Promise<MissingEmailList> {
  return api.get<MissingEmailList>('v1/data-quality/missing-email/', { query: params });
}

export function fetchMergeAudit(params: ListParams = {}): Promise<MergeAuditList> {
  return api.get<MergeAuditList>('v1/data-quality/merges/', { query: params });
}

export function backfillNormalization(): Promise<{ status: string; counts: Record<string, number> }> {
  return api.post('v1/data-quality/backfill/', {});
}

export type { Lead, MissingEmailLead };
