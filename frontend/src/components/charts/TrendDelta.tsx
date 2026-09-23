import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';

import { cn } from '@/lib/utils/cn';
import type { MetricTrend } from '@/types/dashboard';

export interface TrendDeltaProps {
  trend: MetricTrend;
  className?: string;
  showLabel?: boolean;
}

/**
 * Renders a percentage movement with the correct business sentiment:
 * `positive: false` inverts the colour (e.g. rising bounce rate is bad).
 */
export function TrendDelta({ trend, className, showLabel = true }: TrendDeltaProps) {
  const isUp = trend.direction === 'up';
  const isFlat = trend.direction === 'flat';
  const goodFraming = isFlat ? false : isUp === trend.positive;

  return (
    <span className={cn('inline-flex items-center gap-1 text-[12px] font-medium', className)}>
      <span
        className={cn(
          'inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 tabular',
          isFlat && 'bg-surface-3 text-muted',
          !isFlat && goodFraming && 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300',
          !isFlat && !goodFraming && 'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300',
        )}
      >
        {isFlat ? (
          <Minus className="size-3" />
        ) : isUp ? (
          <ArrowUpRight className="size-3" />
        ) : (
          <ArrowDownRight className="size-3" />
        )}
        {isFlat ? `${trend.value}%` : `${trend.value}%`}
      </span>
      {showLabel ? <span className="text-subtle">{trend.label}</span> : null}
    </span>
  );
}
