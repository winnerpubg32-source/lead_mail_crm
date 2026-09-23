import { CalendarRange, Download, Plus, RefreshCw } from 'lucide-react';
import { useState } from 'react';

import { ErrorBoundary } from '@/components/feedback/ErrorBoundary';
import { ErrorState } from '@/components/feedback/ErrorState';
import { LoadingState } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { CampaignOverviewCard } from '@/features/dashboard/components/CampaignOverviewCard';
import { CapacityCard } from '@/features/dashboard/components/CapacityCard';
import { LeadSourcesCard } from '@/features/dashboard/components/LeadSourcesCard';
import { MetricCard } from '@/features/dashboard/components/MetricCard';
import { DashboardSkeleton } from '@/features/dashboard/components/DashboardSkeleton';
import { PipelineOverviewCard } from '@/features/dashboard/components/PipelineOverviewCard';
import { RecentLeadsCard } from '@/features/dashboard/components/RecentLeadsCard';
import { TodaysOutreachCard } from '@/features/dashboard/components/TodaysOutreachCard';
import { useDailyEmailUsage } from '@/hooks/useCampaigns';
import { useDashboardOverview } from '@/hooks/useDashboardOverview';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { env } from '@/lib/env';
import { formatDateTime } from '@/lib/utils/format';

type RangeOption = 'today' | '7d' | '30d' | 'quarter';

const rangeOptions: Array<{ value: RangeOption; label: string }> = [
  { value: 'today', label: 'Today' },
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
  { value: 'quarter', label: 'Quarter' },
];

/**
 * Dashboard — the only fully functional module in Phase 1.
 *
 * Data comes from `useDashboardOverview()`, which reads either the placeholder
 * dataset or `GET /api/v1/analytics/dashboard/` (see `lib/env.ts`). Loading,
 * error and empty states are all handled explicitly.
 */
export function DashboardPage() {
  useDocumentTitle('Dashboard');
  const [range, setRange] = useState<RangeOption>('today');
  const { data, isPending, isError, error, refetch, isFetching } = useDashboardOverview();
  const { data: emailUsage } = useDailyEmailUsage(!env.useMockData);

  const header = (
    <PageHeader
      eyebrow="Outreach command centre"
      title="Dashboard"
      description="Live snapshot of the lead database, today's sending budget and the pipeline your sequences are building."
      actions={
        <>
          <div className="hidden items-center gap-2 rounded-lg border border-border-subtle bg-surface px-3 py-2 text-[12.5px] text-muted sm:flex">
            <CalendarRange className="size-3.5 text-subtle" />
            <span>
              Last updated{' '}
              <span className="tabular font-medium text-fg">
                {data ? formatDateTime(data.generatedAt) : '—'}
              </span>
            </span>
          </div>
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
            title="CSV/XLSX export ships in a later phase"
            leadingIcon={<Download className="size-3.5" />}
          >
            Export
          </Button>
          <Button
            variant="primary"
            size="sm"
            disabled
            title="Campaign creation ships in the Campaigns phase"
            leadingIcon={<Plus className="size-3.5" />}
          >
            New campaign
          </Button>
        </>
      }
      toolbar={
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <SegmentedControl options={rangeOptions} value={range} onChange={setRange} />
            <span className="text-[11.5px] text-subtle">Range filters are UI-only in Phase 1</span>
          </div>
          {env.useMockData ? (
            <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[11.5px] font-medium text-amber-700 ring-1 ring-amber-200 ring-inset dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/20">
              Placeholder data · set VITE_USE_MOCK_DATA=false to read from Django
            </span>
          ) : null}
        </div>
      }
    />
  );

  if (isPending) {
    return (
      <>
        {header}
        <DashboardSkeleton />
      </>
    );
  }

  if (isError) {
    return (
      <>
        {header}
        <ErrorState
          title="Could not load the dashboard"
          description="The dashboard data source did not respond. Check the Django API and try again."
          details={error instanceof Error ? error.message : undefined}
          onRetry={() => void refetch()}
        />
      </>
    );
  }

  if (!data) {
    return (
      <>
        {header}
        <LoadingState label="Preparing dashboard…" />
      </>
    );
  }

  const overview = emailUsage
    ? {
        ...data,
        capacity: {
          ...data.capacity,
          sent: emailUsage.sent_today,
          limit: emailUsage.limit,
          remaining: emailUsage.remaining,
          queued: emailUsage.queued,
          failed: emailUsage.failed,
          windowLabel: emailUsage.window_label,
        },
        metrics: data.metrics.map((metric) =>
          metric.id === 'emails-sent-today'
            ? { ...metric, value: emailUsage.sent_today, displayValue: String(emailUsage.sent_today) }
            : metric.id === 'daily-capacity'
              ? { ...metric, value: emailUsage.limit, displayValue: `${emailUsage.sent_today} / ${emailUsage.limit}` }
              : metric,
        ),
      }
    : data;

  return (
    <>
      {header}

      <div className="animate-[var(--animate-slide-up)] space-y-5">
        {/* KPI row: total leads, valid e-mails, qualified, sent today, capacity, replies, meetings, opportunities */}
        <section aria-label="Key metrics">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {overview.metrics.map((metric) => (
              <MetricCard key={metric.id} metric={metric} />
            ))}
          </div>
        </section>

        {/* Today's outreach + daily capacity */}
        <section aria-label="Today">
          <div className="grid gap-5 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <ErrorBoundary>
                <TodaysOutreachCard events={overview.todaysOutreach} className="h-full" />
              </ErrorBoundary>
            </div>
            <ErrorBoundary>
              <CapacityCard capacity={overview.capacity} className="h-full" />
            </ErrorBoundary>
          </div>
        </section>

        {/* Recent leads */}
        <section aria-label="Recent leads">
          <ErrorBoundary>
            <RecentLeadsCard leads={overview.recentLeads} />
          </ErrorBoundary>
        </section>

        {/* Lead sources, campaign overview, pipeline */}
        <section aria-label="Sources, campaigns and pipeline">
          <div className="grid gap-5 xl:grid-cols-3">
            <ErrorBoundary>
              <LeadSourcesCard sources={overview.leadSources} className="h-full" />
            </ErrorBoundary>
            <ErrorBoundary>
              <CampaignOverviewCard campaigns={overview.campaigns} className="h-full" />
            </ErrorBoundary>
            <ErrorBoundary>
              <PipelineOverviewCard stages={overview.pipeline} className="h-full" />
            </ErrorBoundary>
          </div>
        </section>
      </div>
    </>
  );
}
