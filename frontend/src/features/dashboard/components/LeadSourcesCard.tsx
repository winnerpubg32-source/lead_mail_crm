import { SourceDonut } from '@/components/charts/SourceDonut';
import { Card, CardHeader } from '@/components/ui/Card';
import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';
import type { LeadSourceBreakdown } from '@/types/dashboard';

export interface LeadSourcesCardProps {
  sources: LeadSourceBreakdown[];
  className?: string;
}

/**
 * Where leads come from.
 *
 * Donut for the shape of the mix, list for the exact numbers — the pattern the
 * analytics module will reuse for campaign and industry breakdowns.
 */
export function LeadSourcesCard({ sources, className }: LeadSourcesCardProps) {
  const total = sources.reduce((sum, source) => sum + source.count, 0);
  const topSource = sources[0];

  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader
        title="Lead Sources"
        description="Attribution across all imported and captured leads"
        action={<span className="tabular text-[12px] text-subtle">{formatNumber(total)} total</span>}
      />

      <div className="grid gap-4 px-5 py-4 sm:grid-cols-[minmax(0,180px)_1fr] sm:items-center">
        <SourceDonut
          data={sources}
          centerValue={formatNumber(total)}
          centerLabel="leads"
          className="mx-auto sm:mx-0"
        />

        <ul className="space-y-2.5">
          {sources.map((source) => (
            <li key={source.id}>
              <div className="flex items-center justify-between gap-3 text-[12.5px]">
                <span className="flex min-w-0 items-center gap-2">
                  <span
                    aria-hidden="true"
                    className="size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: source.color }}
                  />
                  <span className="truncate font-medium text-fg">{source.label}</span>
                </span>
                <span className="tabular shrink-0 text-muted">
                  {formatNumber(source.count)}
                  <span className="ml-1.5 text-subtle">{source.share}%</span>
                </span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-surface-3">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${Math.max(2, source.share)}%`, backgroundColor: source.color }}
                />
              </div>
            </li>
          ))}
        </ul>
      </div>

      {topSource ? (
        <div className="border-t border-border-subtle px-5 py-3 text-[12px] text-subtle">
          Top source: <span className="font-medium text-muted">{topSource.label}</span> ·{' '}
          {topSource.share}% of the database
        </div>
      ) : null}
    </Card>
  );
}
