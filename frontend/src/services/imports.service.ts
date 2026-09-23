/**
 * Imports data access — `/api/v1/imports/`.
 *
 * The upload is a multipart POST (see `api.upload`); every other call is JSON.
 * The endpoints are real (Phase 3), so there is no mock branch here.
 */

import { api } from '@/lib/api/client';
import type { PaginatedResponse } from '@/types/api';
import type {
  ColumnMapping,
  ImportJob,
  ImportJobDetail,
  ImportListParams,
  SystemField,
} from '@/types/import';

export const importKeys = {
  all: ['imports'] as const,
  list: (params: ImportListParams) => [...importKeys.all, 'list', params] as const,
  detail: (id: number) => [...importKeys.all, 'detail', id] as const,
  fields: () => [...importKeys.all, 'fields'] as const,
};

/** Import history, newest first. */
export function fetchImportJobs(params: ImportListParams = {}): Promise<PaginatedResponse<ImportJob>> {
  return api.get<PaginatedResponse<ImportJob>>('v1/imports/', { query: params });
}

/** One job with its preview payload (counts, mapping, sample rows). */
export function fetchImportJob(id: number): Promise<ImportJobDetail> {
  return api.get<ImportJobDetail>(`v1/imports/${id}/`);
}

/** The system field catalogue used to populate the mapping selects. */
export async function fetchSystemFields(): Promise<SystemField[]> {
  const payload = await api.get<{ system_fields: SystemField[] }>('v1/imports/fields/');
  return payload.system_fields;
}

/** Upload a CSV/XLSX file — analysed immediately, returns the preview. */
export function uploadImportFile(file: File, sheet?: string): Promise<ImportJobDetail> {
  const body = new FormData();
  body.append('file', file);
  if (sheet) body.append('sheet', sheet);
  return api.upload<ImportJobDetail>('v1/imports/upload/', body);
}

/** Apply manual mapping changes and get the recomputed preview back. */
export function applyImportMapping(id: number, mapping: ColumnMapping): Promise<ImportJobDetail> {
  return api.post<ImportJobDetail>(`v1/imports/${id}/mapping/`, { column_mapping: mapping });
}

/** Hand the job to the worker; the mapping is sent along with it. */
export function startImport(
  id: number,
  mapping?: ColumnMapping,
): Promise<{ id: number; status: string; status_display: string; dispatch: string }> {
  return api.post(`v1/imports/${id}/start/`, mapping ? { column_mapping: mapping } : {});
}

/** Lightweight polling endpoint (detail without the 50-row sample). */
export function fetchImportProgress(id: number): Promise<ImportJob> {
  return api.get<ImportJob>(`v1/imports/${id}/status/`);
}

/** Discard a job and its uploaded file (drops the row). */
export function cancelImport(id: number): Promise<void> {
  return api.post<void>(`v1/imports/${id}/cancel/`);
}

/** Delete a finished history entry. */
export function deleteImport(id: number): Promise<void> {
  return api.delete<void>(`v1/imports/${id}/`);
}
