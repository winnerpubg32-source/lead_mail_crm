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
import { emailStatusOptions, industryOptions, leadStatusOptions, stateOptions } from '@/config/list-options';
import { LeadTable } from '@/features/leads/components/LeadTable';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useLeadStatuses, useLeads } from '@/hooks/useLeads';
import { useListQuery } from '@/hooks/useListQuery';
import { env } from '@/lib/env';
import { formatNumber } from '@/lib/utils/format';

/**
 * Leads — the real list backed by `GET /api/v1/leads/`.
 *
 * Search, filters, ordering and pagination are all server-side: every control
 * maps to a DRF query parameter, so the table stays correct as the dataset grows
 * past what the browser should hold.
 */
export function LeadsPage() {
  useDocumentTitle('Leads');

  const list = useListQuery();
  const { data, isPending, isError, error, refetch, isFetching } = useLeads(list.params);
  const statuses = useLeadStatuses();

  const leads = data?.results ?? [];
  const count = data?.count ?? 0;
  const hasRows = leads.length > 0;

  // Prefer the live vocabulary (labels + counts) and fall back to the static
  // enum list while it loads or when the endpoint returns nothing.
  const statusFilterOptions =
    statuses.data && statuses.data.lead_status.length > 0
      ? statuses.data.lead_status.map((entry) => ({
          value: entry.value,
          label: entry.count > 0 ? `${entry.label} (${entry.count})` : entry.label,
        }))
      : leadStatusOptions;

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
              disabled
              title="CSV/XLSX import ships in a later phase"
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
          searchPlaceholder="Search business, contact, e-mail or title…"
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
              options: emailStatusOptions,
            },
            {
              name: 'industry',
              label: 'All industries',
              value: list.filters.industry ?? '',
              options: industryOptions,
            },
            {
              name: 'state',
              label: 'All states',
              value: list.filters.state ?? '',
              options: stateOptions,
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
          <TableSkeleton rows={8} columns={9} />
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
                description="The lead database is empty. Importing business datasets arrives in the next phase — for now you can seed development data with `python manage.py seed_lead_data`."
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
            <LeadTable leads={leads} ordering={list.ordering} onToggleOrdering={list.toggleOrdering} />
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
