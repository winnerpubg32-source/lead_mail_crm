import { RefreshCw, ShieldCheck, Workflow } from 'lucide-react';

import { EmptyState } from '@/components/feedback/EmptyState';
import { ErrorState } from '@/components/feedback/ErrorState';
import { TableSkeleton } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';
import { TableToolbar } from '@/components/ui/TableToolbar';
import { DuplicateReviewCard } from '@/features/data-quality/components/DuplicateReviewCard';
import {
  useDetectDuplicates,
  useDuplicateGroups,
  useIgnoreGroup,
  useKeepBothGroup,
  useMergeDuplicateGroup,
} from '@/hooks/useDataQuality';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useListQuery } from '@/hooks/useListQuery';
import { formatNumber } from '@/lib/utils/format';
import { toast } from '@/lib/utils/toast';

/**
 * Duplicate review page (Phase 4).
 *
 * Lists open duplicate pairs with pairwise merge/keep/ignore actions.
 */
export function DuplicatesPage() {
  useDocumentTitle('Duplicate review');
  const list = useListQuery();
  const { data, isPending, isError, error, refetch, isFetching } = useDuplicateGroups(list.params);
  const detect = useDetectDuplicates();
  const merge = useMergeDuplicateGroup();
  const keepBoth = useKeepBothGroup();
  const ignore = useIgnoreGroup();

  const groups = data?.results ?? [];
  const count = data?.count ?? 0;

  const statusOptions = [
    { value: '', label: 'All statuses' },
    { value: 'OPEN', label: 'Open' },
    { value: 'MERGED', label: 'Merged' },
    { value: 'KEPT_BOTH', label: 'Kept both' },
    { value: 'IGNORED', label: 'Ignored' },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Data quality"
        title="Duplicate review"
        description="Compare potential duplicate records side by side and decide whether to merge them, keep both, or ignore the match."
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
            <Button
              variant="primary"
              size="sm"
              onClick={() => detect.mutate(false)}
              isLoading={detect.isPending}
              leadingIcon={<Workflow className="size-3.5" />}
            >
              Scan for duplicates
            </Button>
          </>
        }
      />

      <Card className="overflow-hidden">
        <TableToolbar
          search={list.search}
          onSearchChange={list.setSearch}
          searchPlaceholder="Search company, contact or e-mail…"
          filters={[
            {
              name: 'status',
              label: 'Open',
              value: list.filters.status ?? 'OPEN',
              options: statusOptions,
            },
          ]}
          onFilterChange={list.setFilter}
          onReset={list.reset}
          hasActiveQuery={list.hasActiveQuery}
          extra={
            <span className="hidden text-[12.5px] whitespace-nowrap text-subtle lg:inline">
              <span className="tabular font-medium text-muted">{formatNumber(count)}</span> groups
            </span>
          }
        />

        {isPending ? (
          <div className="p-5">
            <TableSkeleton rows={4} columns={3} />
          </div>
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              title="Could not load duplicates"
              details={error instanceof Error ? error.message : undefined}
              onRetry={() => void refetch()}
            />
          </div>
        ) : groups.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={<ShieldCheck />}
              title={list.hasActiveQuery ? 'No groups match these filters' : 'No duplicate pairs to review'}
              description="Run a duplicate scan to detect new potential matches across your lead database."
              action={
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => detect.mutate(false)}
                  isLoading={detect.isPending}
                  leadingIcon={<Workflow className="size-3.5" />}
                >
                  Scan for duplicates
                </Button>
              }
            />
          </div>
        ) : (
          <div className="space-y-4 p-5">
            {groups.map((group) => (
              <DuplicateReviewCard
                key={group.id}
                group={group}
                isMutating={merge.isPending || keepBoth.isPending || ignore.isPending}
                onMerge={(winnerId, loserId) =>
                  merge.mutate(
                    { id: group.id, winnerId, loserId },
                    { onSuccess: () => toast({ title: 'Records merged', tone: 'success' }) },
                  )
                }
                onKeepBoth={() =>
                  keepBoth.mutate(group.id, {
                    onSuccess: () => toast({ title: 'Marked as not duplicates', tone: 'success' }),
                  })
                }
                onIgnore={() =>
                  ignore.mutate(group.id, {
                    onSuccess: () => toast({ title: 'Ignored', tone: 'success' }),
                  })
                }
              />
            ))}
            <Pagination
              count={count}
              page={list.page}
              pageSize={list.pageSize}
              hasNext={Boolean(data?.next)}
              hasPrevious={Boolean(data?.previous)}
              onPageChange={list.setPage}
              onPageSizeChange={list.setPageSize}
              itemLabel="groups"
            />
          </div>
        )}
      </Card>
    </div>
  );
}
