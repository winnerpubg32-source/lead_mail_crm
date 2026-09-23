import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  addLeadNote,
  bulkAction,
  exportLeadsCsv,
  fetchLead,
  fetchLeadFilterOptions,
  fetchLeads,
  fetchLeadStatuses,
  leadKeys,
  rescoreLead,
  updateLead,
} from '@/services/leads.service';
import type { BulkActionPayload, ListParams } from '@/types/lead';

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

export function useLeadFilterOptions() {
  return useQuery({
    queryKey: leadKeys.filters(),
    queryFn: fetchLeadFilterOptions,
    staleTime: 120_000,
  });
}

/** Single lead detail. */
export function useLead(id: number) {
  return useQuery({
    queryKey: leadKeys.detail(id),
    queryFn: () => fetchLead(id),
    enabled: Number.isFinite(id) && id > 0,
  });
}

export function useUpdateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Parameters<typeof updateLead>[1] }) =>
      updateLead(id, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: leadKeys.all }),
  });
}

export function useAddLeadNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: string }) => addLeadNote(id, body),
    onSuccess: (_data, { id }) => qc.invalidateQueries({ queryKey: leadKeys.detail(id) }),
  });
}

export function useRescoreLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => rescoreLead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: leadKeys.all }),
  });
}

export function useBulkAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkActionPayload) => bulkAction(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: leadKeys.all }),
  });
}

export function useExportLeads() {
  return useMutation({
    mutationFn: (params: ListParams) => exportLeadsCsv(params),
  });
}
