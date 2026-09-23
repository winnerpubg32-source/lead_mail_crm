import { useCallback, useMemo, useState } from 'react';
import { Download, RefreshCw, Target, Users } from 'lucide-react';

import { EmptyState } from '@/components/feedback/EmptyState';
import { ErrorState } from '@/components/feedback/ErrorState';
import { TableSkeleton } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';
import { TableToolbar } from '@/components/ui/TableToolbar';
import {
  emailStatusOptions,
  industryOptions,
  leadStatusOptions,
  sourceOptions,
  stateOptions,
  scoreFilterOptions,
} from '@/config/list-options';
import { BulkActionBar } from '@/features/leads/components/BulkActionBar';
import { LeadTable } from '@/features/leads/components/LeadTable';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useExportLeads, useLeadFilterOptions, useLeads, useLeadStatuses } from '@/hooks/useLeads';
import { useListQuery } from '@/hooks/useListQuery';
import { env } from '@/lib/env';
import { formatNumber } from '@/lib/utils/format';
import { toast } from '@/lib/utils/toast';

/**
 * Leads (Phase 5).
 *
 * Full lead table with search, multi-column filters, sortable headers,
 * pagination, bulk selection + actions, and CSV export.
 */
export function LeadsPage() {
  useDocumentTitle('Leads');

  const list = useListQuery();
  const { data, isPending, isError, error, refetch, isFetching } = useLeads(list.params);
  const statuses = useLeadStatuses();
  const filters = useLeadFilterOptions();
  const exporter = useExportLeads();

  const [selected, setSelected] = useState<Set<number>>(new Set());

  const leads = data?.results ?? [];
  const count = data?.count ?? 0;
  const hasRows = leads.length > 0;

  const statusFilterOptions = useMemo(() => {
    if (statuses.data && statuses.data.lead_status.length > 0) {
      return statuses.data.lead_status
        .filter((entry) => entry.value !== 'MERGED')
        .map((entry) => ({
          value: entry.value,
          label: entry.count > 0 ? `${entry.label} (${entry.count})` : entry.label,
        }));
    }
    return leadStatusOptions;
  }, [statuses.data]);

  const emailStatusFilterOptions = useMemo(() => {
    if (statuses.data && statuses.data.email_status.length > 0) {
      return statuses.data.email_status.map((entry) => ({
        value: entry.value,
        label: entry.count > 0 ? `${entry.label} (${entry.count})` : entry.label,
      }));
    }
    return emailStatusOptions;
  }, [statuses.data]);

  const industryFilterOptions = useMemo(
    () =>
      filters.data?.industries.length
        ? filters.data.industries.map((v: string) => ({ value: v, label: v }))
        : industryOptions,
    [filters.data],
  );
  const stateFilterOptions = useMemo(
    () =>
      filters.data?.states.length
        ? filters.data.states.map((v: string) => ({ value: v, label: v }))
        : stateOptions,
    [filters.data],
  );

  // Row selection helpers.
  const toggleOne = useCallback((id: number, isOn: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (isOn) next.add(id);
      else next.delete(id);
      return next;
    });
  }, []);
  const toggleAll = useCallback(
    (isOn: boolean) => {
      if (isOn) setSelected(new Set(leads.map((l) => l.id)));
      else setSelected(new Set());
    },
    [leads],
  );
  const clearSelection = useCallback(() => setSelected(new Set()), []);

  const allSelected = leads.length > 0 && leads.every((l) => selected.has(l.id));
  const someSelected = selected.size > 0 && !allSelected;

  const handleExport = () => {
    exporter.mutate(list.params, {
      onSuccess: () => toast.success('Export started'),
      onError: (err: Error) => toast.error(err.message || 'Export failed'),
    });
  };

  return (
    <div>
      <PageHeader
        eyebrow="Lead database"
        title="Leads"
        description="Every prospect in the pipeline with its company, decision maker, contactability and qualification score."
        actions={
          <>
            <Badge tone={env.useMockData ? 'warning' : 'success'} size="sm" dot>
              {env.useMockData ? 'Dashboard uses placeholder data' : 'Live Django API'}
            </Badge>
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
              variant="outline"
              size="sm"
              onClick={handleExport}
              isLoading={exporter.isPending}
              leadingIcon={<Download className="size-3.5" />}
            >
              Export
            </Button>
          </>
        }
      />

      <Card className="animate-[var(--animate-slide-up)] overflow-hidden">
        <TableToolbar
          search={list.search}
          onSearchChange={list.setSearch}
          searchPlaceholder="Search business, contact, e-mail, source or title…"
          filters={[
            {
              name: 'lead_status',
              label: 'All statuses',
              value: list.filters.lead_status ?? '',
              options: statusFilterOptions,
            },
            {
              name: 'email_status',
              label: 'All e-mail status',
              value: list.filters.email_status ?? '',
              options: emailStatusFilterOptions,
            },
            {
              name: 'score_classification',
              label: 'All scores',
              value: list.filters.score_classification ?? '',
              options: scoreFilterOptions,
            },
            {
              name: 'industry',
              label: 'All industries',
              value: list.filters.industry ?? '',
              options: industryFilterOptions,
            },
            {
              name: 'sub_industry',
              label: 'All sub-industries',
              value: list.filters.sub_industry ?? '',
              options:
                filters.data?.sub_industries.map((v: string) => ({ value: v, label: v })) ?? [],
            },
            {
              name: 'state',
              label: 'All states',
              value: list.filters.state ?? '',
              options: stateFilterOptions,
            },
            {
              name: 'source',
              label: 'All sources',
              value: list.filters.source ?? '',
              options: sourceOptions,
            },
            {
              name: 'has_email',
              label: 'Any e-mail',
              value: list.filters.has_email ?? '',
              options: [
                { value: 'true', label: 'Has e-mail' },
                { value: 'false', label: 'Missing e-mail' },
              ],
            },
            {
              name: 'has_website',
              label: 'Any website',
              value: list.filters.has_website ?? '',
              options: [
                { value: 'true', label: 'Has website' },
                { value: 'false', label: 'No website' },
              ],
            },
          ]}
          onFilterChange={list.setFilter}
          onReset={list.reset}
          hasActiveQuery={list.hasActiveQuery}
          extra={
            <span className="hidden text-[12.5px] whitespace-nowrap text-subtle lg:inline">
              {isFetching && !isPending ? (
                'Updating…'
              ) : (
                <>
                  <span className="tabular font-medium text-muted">{formatNumber(count)}</span> leads
                </>
              )}
            </span>
          }
        />

        {isPending ? (
          <TableSkeleton rows={8} columns={13} />
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              title="Could not load leads"
              description="The leads API did not respond. Make sure the Django backend is running."
              details={error instanceof Error ? error.message : undefined}
              onRetry={() => void refetch()}
            />
          </div>
        ) : !hasRows ? (
          <div className="p-5">
            {list.hasActiveQuery ? (
              <EmptyState
                icon={<Target />}
                title="No leads match these filters"
                description="Try a different search term or clear the filters to see the full lead database."
                action={
                  <Button variant="outline" size="sm" onClick={list.reset}>
                    Clear filters
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={<Target />}
                title="No leads yet"
                description="The lead database is empty. Import a CSV to get started."
                action={
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => void refetch()}
                    leadingIcon={<RefreshCw className="size-3.5" />}
                  >
                    Reload
                  </Button>
                }
                secondaryAction={
                  <span className="inline-flex items-center gap-1.5 font-mono text-[11.5px] text-subtle">
                    <Users className="size-3.5" />
                    GET /api/v1/leads/
                  </span>
                }
              />
            )}
          </div>
        ) : (
          <>
            <LeadTable
              leads={leads}
              ordering={list.ordering}
              onToggleOrdering={list.toggleOrdering}
              selected={selected}
              onToggleOne={toggleOne}
              onToggleAll={toggleAll}
              allSelected={allSelected}
              someSelected={someSelected}
            />
            {selected.size > 0 && (
              <BulkActionBar selected={selected} onClear={clearSelection} params={list.params} />
            )}
            <Pagination
              count={count}
              page={list.page}
              pageSize={list.pageSize}
              hasNext={Boolean(data?.next)}
              hasPrevious={Boolean(data?.previous)}
              onPageChange={list.setPage}
              onPageSizeChange={list.setPageSize}
              itemLabel="leads"
            />
          </>
        )}
      </Card>
    </div>
  );
}
