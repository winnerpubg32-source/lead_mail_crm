import { useState } from 'react';
import { Megaphone, Plus, RefreshCw, Target } from 'lucide-react';

import { EmptyState } from '@/components/feedback/EmptyState';
import { ErrorState } from '@/components/feedback/ErrorState';
import { TableSkeleton } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';
import { TableToolbar } from '@/components/ui/TableToolbar';
import { campaignStatusConfig } from '@/config/status';
import { CampaignTable } from '@/features/campaigns/components/CampaignTable';
import { CampaignWizard } from '@/features/campaigns/components/CampaignWizard';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useCampaigns, useCampaignStatuses } from '@/hooks/useCampaigns';
import { useListQuery } from '@/hooks/useListQuery';
import { formatNumber } from '@/lib/utils/format';

/**
 * Campaigns list (Phase 6).
 *
 * Columns: Campaign, Audience, Eligible Leads, Daily Limit, Sent, Replies, Status.
 * Create/Edit wizard walks through Audience → Service → Template → Schedule → Review.
 */
export function CampaignsPage() {
  useDocumentTitle('Campaigns');

  const list = useListQuery();
  const { data, isPending, isError, error, refetch, isFetching } = useCampaigns(list.params);
  const statuses = useCampaignStatuses();
  const [wizardOpen, setWizardOpen] = useState(false);

  const campaigns = data?.results ?? [];
  const count = data?.count ?? 0;

  const statusOptions =
    statuses.data?.campaign_status.map((s) => ({
      value: s.value,
      label: `${campaignStatusConfig[s.value].label}${s.count ? ` (${s.count})` : ''}`,
    })) ??
    Object.entries(campaignStatusConfig).map(([value, cfg]) => ({ value, label: cfg.label }));

  return (
    <div>
      <PageHeader
        eyebrow="Outreach"
        title="Campaigns"
        description="Audience, template and schedule for every outreach sequence. Phase 6 prepares campaigns — Phase 7 sends them."
        actions={
          <>
            <Badge tone="warning" size="sm" dot>Phase 6 · prep only</Badge>
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
              size="sm"
              onClick={() => setWizardOpen(true)}
              leadingIcon={<Plus className="size-3.5" />}
            >
              New campaign
            </Button>
          </>
        }
      />

      <Card className="animate-[var(--animate-slide-up)] overflow-hidden">
        <TableToolbar
          search={list.search}
          onSearchChange={list.setSearch}
          searchPlaceholder="Search campaigns…"
          filters={[
            {
              name: 'status',
              label: 'All statuses',
              value: list.filters.status ?? '',
              options: statusOptions,
            },
          ]}
          onFilterChange={list.setFilter}
          onReset={list.reset}
          hasActiveQuery={list.hasActiveQuery}
          extra={
            <span className="hidden text-[12.5px] whitespace-nowrap text-subtle lg:inline">
              {isFetching && !isPending ? 'Updating…' : (
                <>
                  <span className="tabular font-medium text-muted">{formatNumber(count)}</span> campaigns
                </>
              )}
            </span>
          }
        />

        {isPending ? (
          <TableSkeleton rows={6} columns={7} />
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              title="Could not load campaigns"
              details={error instanceof Error ? error.message : undefined}
              onRetry={() => void refetch()}
            />
          </div>
        ) : campaigns.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={<Megaphone />}
              title={list.hasActiveQuery ? 'No campaigns match these filters' : 'No campaigns yet'}
              description={
                list.hasActiveQuery
                  ? 'Try clearing filters to see every campaign.'
                  : 'Create your first outreach campaign: pick an audience, a service, a template and a schedule.'
              }
              action={
                list.hasActiveQuery ? (
                  <Button variant="outline" size="sm" onClick={list.reset}>Clear filters</Button>
                ) : (
                  <Button size="sm" onClick={() => setWizardOpen(true)} leadingIcon={<Plus className="size-3.5" />}>
                    New campaign
                  </Button>
                )
              }
              secondaryAction={
                <span className="inline-flex items-center gap-1.5 font-mono text-[11.5px] text-subtle">
                  <Target className="size-3.5" />
                  GET /api/v1/campaigns/
                </span>
              }
            />
          </div>
        ) : (
          <>
            <CampaignTable campaigns={campaigns} ordering={list.ordering} onToggleOrdering={list.toggleOrdering} />
            <Pagination
              count={count}
              page={list.page}
              pageSize={list.pageSize}
              hasNext={Boolean(data?.next)}
              hasPrevious={Boolean(data?.previous)}
              onPageChange={list.setPage}
              onPageSizeChange={list.setPageSize}
              itemLabel="campaigns"
            />
          </>
        )}
      </Card>

      {wizardOpen && (
        <CampaignWizard onClose={() => setWizardOpen(false)} />
      )}
    </div>
  );
}
