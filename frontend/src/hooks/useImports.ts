import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  applyImportMapping,
  cancelImport,
  fetchImportJob,
  fetchImportJobs,
  fetchSystemFields,
  importKeys,
  startImport,
  uploadImportFile,
} from '@/services/imports.service';
import { isActiveStatus, type ColumnMapping, type ImportListParams } from '@/types/import';

/** Import history, paginated and filterable. */
export function useImportJobs(params: ImportListParams = {}) {
  return useQuery({
    queryKey: importKeys.list(params),
    queryFn: () => fetchImportJobs(params),
    placeholderData: (previous) => previous,
  });
}

/**
 * One job with its preview.
 *
 * While the job is queued or processing the query polls itself every 1.5s so
 * the progress bar keeps moving; polling stops as soon as the job is no longer
 * active (or on failure).
 */
export function useImportJob(id: number | null, options: { poll?: boolean } = {}) {
  const { poll = true } = options;
  return useQuery({
    queryKey: importKeys.detail(id ?? 0),
    queryFn: () => fetchImportJob(id as number),
    enabled: id !== null,
    refetchInterval: (query) =>
      poll && isActiveStatus(query.state.data?.status) ? 1500 : false,
  });
}

/** The 20 system fields, used to build the mapping selects. */
export function useSystemFields() {
  return useQuery({
    queryKey: importKeys.fields(),
    queryFn: fetchSystemFields,
    staleTime: Infinity,
  });
}

/** Upload a file; the response carries the detected mapping and preview. */
export function useUploadImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, sheet }: { file: File; sheet?: string }) => uploadImportFile(file, sheet),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: importKeys.all }),
  });
}

/** Persist manual mapping edits and receive the recomputed preview. */
export function useApplyMapping(id: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mapping: ColumnMapping) => applyImportMapping(id as number, mapping),
    onSuccess: (job) => {
      queryClient.setQueryData(importKeys.detail(job.id), job);
      void queryClient.invalidateQueries({ queryKey: importKeys.all });
    },
  });
}

/** Confirm the import and hand it to the background worker. */
export function useStartImport(id: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mapping?: ColumnMapping) => startImport(id as number, mapping),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: importKeys.detail(id as number) });
      void queryClient.invalidateQueries({ queryKey: importKeys.all });
    },
  });
}

/** Discard a job that has not run yet (or stop one that has). */
export function useCancelImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => cancelImport(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: importKeys.detail(id) });
      void queryClient.invalidateQueries({ queryKey: importKeys.all });
    },
  });
}
