import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  dataQualityKeys,
  fetchDataQualityStats,
  fetchDuplicateGroups,
  fetchMergeAudit,
  fetchMissingEmailLeads,
  ignoreGroup,
  keepBothGroup,
  mergeDuplicateGroup,
  runDuplicateDetection,
} from '@/services/dataQuality.service';
import type { ListParams } from '@/types/lead';

/** Data quality dashboard statistics. */
export function useDataQualityStats() {
  return useQuery({
    queryKey: dataQualityKeys.stats(),
    queryFn: fetchDataQualityStats,
    staleTime: 30_000,
  });
}

/** Paginated duplicate groups list (OPEN by default). */
export function useDuplicateGroups(params: ListParams) {
  return useQuery({
    queryKey: dataQualityKeys.duplicates(params),
    queryFn: () => fetchDuplicateGroups(params),
    placeholderData: (previous) => previous,
  });
}

/** Missing-email leads list. */
export function useMissingEmailLeads(params: ListParams) {
  return useQuery({
    queryKey: dataQualityKeys.missingEmail(params),
    queryFn: () => fetchMissingEmailLeads(params),
    placeholderData: (previous) => previous,
  });
}

/** Merge audit log. */
export function useMergeAudit(params: ListParams) {
  return useQuery({
    queryKey: dataQualityKeys.merges(params),
    queryFn: () => fetchMergeAudit(params),
    placeholderData: (previous) => previous,
  });
}

/** Run duplicate detection (mutation). Invalidates stats + duplicates list. */
export function useDetectDuplicates() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (clearExisting: boolean) => runDuplicateDetection(clearExisting),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.duplicates({}) }),
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.stats() }),
      ]);
    },
  });
}

/** Merge a pair (mutation). */
export function useMergeDuplicateGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, winnerId, loserId }: { id: number; winnerId: number; loserId: number }) =>
      mergeDuplicateGroup(id, winnerId, loserId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.duplicates({}) }),
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.stats() }),
        queryClient.invalidateQueries({ queryKey: ['leads'] }),
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.merges({}) }),
      ]);
    },
  });
}

/** Mark group as "keep both". */
export function useKeepBothGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => keepBothGroup(id),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.duplicates({}) }),
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.stats() }),
      ]);
    },
  });
}

/** Ignore group. */
export function useIgnoreGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => ignoreGroup(id),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.duplicates({}) }),
        queryClient.invalidateQueries({ queryKey: dataQualityKeys.stats() }),
      ]);
    },
  });
}
