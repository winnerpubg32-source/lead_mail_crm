import { RefreshCw, ShieldAlert, Workflow } from 'lucide-react';
import { Link } from 'react-router-dom';

import { ErrorState } from '@/components/feedback/ErrorState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { buttonVariants } from '@/components/ui/button-variants';
import { Card } from '@/components/ui/Card';
import { StatsOverviewCard } from '@/features/data-quality/components/StatsOverviewCard';
import { useDataQualityStats, useDetectDuplicates } from '@/hooks/useDataQuality';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';
import { paths } from '@/routes/paths';

/**
 * Data-quality dashboard (Phase 4).
 *
 * Shows the data-health statistics and quick actions for the review workflows.
 */
export function DataQualityPage() {
  useDocumentTitle('Data quality');
  const { data, isPending, isError, error, refetch, isFetching } = useDataQualityStats();
  const detect = useDetectDuplicates();

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Data quality"
        title="Data health"
        description="Normalization, duplicate detection and deliverability coverage across your lead database."
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
              variant="outline"
              size="sm"
              onClick={() => detect.mutate(false)}
              isLoading={detect.isPending}
              leadingIcon={<Workflow className="size-3.5" />}
            >
              Run duplicate scan
            </Button>
          </>
        }
      />

      {isPending ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="h-[102px] animate-pulse rounded-[var(--radius-card)] border border-border-subtle bg-surface"
            />
          ))}
        </div>
      ) : isError ? (
        <ErrorState
          title="Could not load data-quality stats"
          details={error instanceof Error ? error.message : undefined}
          onRetry={() => void refetch()}
        />
      ) : data ? (
        <>
          <StatsOverviewCard stats={data} />

          {detect.variables !== undefined && !detect.isPending && detect.data ? (
            <Card className="p-4">
              <div className="flex items-center gap-2">
                <Badge tone="success">Scan complete</Badge>
                <span className="text-[12.5px] text-muted">
                  Found {formatNumber(detect.data.new_groups)} new potential duplicate pairs.
                </span>
              </div>
            </Card>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            <Card className="p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-medium text-fg">Duplicate review</h3>
                  <p className="mt-1 text-[12.5px] text-subtle">
                    {data.duplicate_groups > 0
                      ? `${formatNumber(data.duplicate_groups)} pairs need your decision.`
                      : 'No duplicates waiting for review.'}
                  </p>
                </div>
                <ShieldAlert className="size-5 text-amber-500" />
              </div>
              <div className="mt-4">
                <Link
                  to={paths.duplicates}
                  className={cn(buttonVariants({ variant: 'primary', size: 'sm' }))}
                >
                  Open duplicate review
                </Link>
              </div>
            </Card>

            <Card className="p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-medium text-fg">Missing e-mail leads</h3>
                  <p className="mt-1 text-[12.5px] text-subtle">
                    {data.missing_emails > 0
                      ? `${formatNumber(data.missing_emails)} leads lack a deliverable address.`
                      : 'Every lead has an e-mail address.'}
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <Link
                  to={paths.missingEmail}
                  className={cn(buttonVariants({ variant: 'primary', size: 'sm' }))}
                >
                  Review missing e-mails
                </Link>
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}
