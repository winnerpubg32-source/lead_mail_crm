import { useQueryClient } from '@tanstack/react-query';
import { FileSpreadsheet, Plus, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { EmptyState } from '@/components/feedback/EmptyState';
import { ErrorState } from '@/components/feedback/ErrorState';
import { TableSkeleton } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { buttonVariants } from '@/components/ui/button-variants';
import { ImportHistoryTable } from '@/features/imports/components/ImportHistoryTable';
import { useImportJobs } from '@/hooks/useImports';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useListQuery } from '@/hooks/useListQuery';
import { apiErrorMessage } from '@/lib/api/errors';
import { formatNumber } from '@/lib/utils/format';
import { paths } from '@/routes/paths';
import { deleteImport, importKeys } from '@/services/imports.service';
import type { ImportJob } from '@/types/import';

const STATUS_TABS: Array<{ value: string; label: string }> = [
  { value: '', label: 'All' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'PROCESSING', label: 'Running' },
  { value: 'QUEUED', label: 'Queued' },
  { value: 'FAILED', label: 'Failed' },
];

/** Import history — every run with its row counts, newest first. */
export function ImportHistoryPage() {
  useDocumentTitle('Import history');

  const queryClient = useQueryClient();
  const list = useListQuery({ pageSize: 25, ordering: '-created_at' });
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data, isPending, isError, error, refetch, isFetching } = useImportJobs({
    page: list.page,
    page_size: list.pageSize,
    ordering: list.ordering,
    status: list.filters.status || undefined,
  });

  const jobs = data?.results ?? [];
  const count = data?.count ?? 0;

  const handleDelete = async (job: ImportJob) => {
    setDeletingId(job.id);
    setDeleteError(null);
    try {
      await deleteImport(job.id);
      await queryClient.invalidateQueries({ queryKey: importKeys.all });
    } catch (caught) {
      setDeleteError(apiErrorMessage(caught, [], 'The import record could not be deleted.'));
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Lead database"
        title="Import history"
        description="Every CSV and Excel ingestion run, with how many rows were imported, merged as duplicates, rejected as invalid or stored without an e-mail address."
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void refetch()}
              isLoading={isFetching}
              leadingIcon={<RefreshCw className="size-3.5" />}
            >
              Refresh
            </Button>
            <Link to={paths.imports} className={buttonVariants({ variant: 'primary', size: 'sm' })}>
              <Plus className="mr-1.5 size-3.5" />
              New import
            </Link>
          </>
        }
      />

      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle px-5 py-3">
          <SegmentedControl
            options={STATUS_TABS}
            value={list.filters.status ?? ''}
            onChange={(value) => list.setFilter('status', value)}
            size="md"
          />
          <span className="text-[12.5px] text-subtle">
            <span className="tabular font-medium text-muted">{formatNumber(count)}</span> run
            {count === 1 ? '' : 's'}
          </span>
        </div>

        {isPending ? (
          <TableSkeleton rows={6} columns={9} />
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              title="Could not load the import history"
              description="The imports API did not respond. Make sure the Django backend is running."
              details={error instanceof Error ? error.message : undefined}
              onRetry={() => void refetch()}
            />
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={<FileSpreadsheet />}
              title={list.filters.status ? 'No imports with this status' : 'No imports yet'}
              description={
                list.filters.status
                  ? 'Try another status filter to see the rest of the history.'
                  : 'Upload a CSV or Excel file and it will show up here with its row-by-row result.'
              }
              action={
                list.filters.status ? (
                  <Button variant="outline" size="sm" onClick={() => list.setFilter('status', '')}>
                    Show all
                  </Button>
                ) : (
                  <Link to={paths.imports} className={buttonVariants({ variant: 'primary', size: 'sm' })}>
                    Start an import
                  </Link>
                )
              }
            />
          </div>
        ) : (
          <>
            <ImportHistoryTable
              jobs={jobs}
              deletingId={deletingId}
              onDelete={(job) => void handleDelete(job)}
            />
            <Pagination
              count={count}
              page={list.page}
              pageSize={list.pageSize}
              hasNext={Boolean(data?.next)}
              hasPrevious={Boolean(data?.previous)}
              onPageChange={list.setPage}
              onPageSizeChange={list.setPageSize}
              itemLabel="imports"
            />
          </>
        )}
      </Card>

      {deleteError ? (
        <p role="alert" className="mt-2 text-[12.5px] text-rose-600 dark:text-rose-300">
          {deleteError}
        </p>
      ) : null}
    </div>
  );
}
