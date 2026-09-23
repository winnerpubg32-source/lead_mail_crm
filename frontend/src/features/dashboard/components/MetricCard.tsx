import {
  BarChart3,
  Building2,
  CalendarCheck,
  Handshake,
  MailCheck,
  Send,
  ShieldCheck,
  Target,
  type LucideIcon,
} from 'lucide-react';

import { Sparkline } from '@/components/charts/Sparkline';
import { TrendDelta } from '@/components/charts/TrendDelta';
import { Skeleton } from '@/components/ui/Skeleton';
import { chartPalette } from '@/config/chart-colors';
import { cn } from '@/lib/utils/cn';
import type { MetricCardData, MetricTone } from '@/types/dashboard';

/** Icon per metric id, falling back to a neutral chart glyph. */
const metricIcons: Record<string, LucideIcon> = {
  'total-leads': Building2,
  'valid-emails': ShieldCheck,
  'qualified-leads': Target,
  'emails-sent-today': Send,
  'daily-capacity': BarChart3,
  replies: MailCheck,
  meetings: CalendarCheck,
  opportunities: Handshake,
};

const toneStyles: Record<MetricTone, { icon: string; stroke: string }> = {
  brand: {
    icon: 'bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300',
    stroke: chartPalette.brand,
  },
  emerald: {
    icon: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300',
    stroke: chartPalette.emerald,
  },
  amber: {
    icon: 'bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300',
    stroke: chartPalette.amber,
  },
  violet: {
    icon: 'bg-violet-50 text-violet-600 dark:bg-violet-500/15 dark:text-violet-300',
    stroke: chartPalette.violet,
  },
  sky: {
    icon: 'bg-sky-50 text-sky-600 dark:bg-sky-500/15 dark:text-sky-300',
    stroke: chartPalette.sky,
  },
  rose: {
    icon: 'bg-rose-50 text-rose-600 dark:bg-rose-500/15 dark:text-rose-300',
    stroke: chartPalette.rose,
  },
};

export interface MetricCardProps {
  metric: MetricCardData;
  className?: string;
}

/**
 * KPI tile: label, value, optional sparkline and period-over-period trend.
 * Values arrive pre-formatted from the data layer so the card stays dumb.
 */
export function MetricCard({ metric, className }: MetricCardProps) {
  const Icon = metricIcons[metric.id] ?? BarChart3;
  const tone = toneStyles[metric.tone];
  const hasSparkline = Boolean(metric.sparkline && metric.sparkline.length > 1);

  return (
    <article
      className={cn(
        'group relative flex flex-col rounded-[var(--radius-card)] border border-border-subtle bg-surface p-4 shadow-[var(--shadow-card)] transition-colors hover:border-border-strong',
        className,
      )}
    >
      <header className="flex items-start justify-between gap-2">
        <h3 className="text-[12.5px] font-medium text-muted">{metric.label}</h3>
        <span className={cn('grid size-7 shrink-0 place-items-center rounded-lg', tone.icon)}>
          <Icon className="size-3.5" />
        </span>
      </header>

      <p className="tabular mt-2.5 text-[26px] leading-none font-semibold tracking-tight text-fg">
        {metric.displayValue}
      </p>

      <div className="mt-3 flex items-end justify-between gap-3">
        <div className="min-w-0 space-y-1.5">
          {metric.trend ? <TrendDelta trend={metric.trend} /> : null}
          {metric.hint ? (
            <p className="truncate text-[11.5px] text-subtle" title={metric.hint}>
              {metric.hint}
            </p>
          ) : null}
        </div>
        {hasSparkline ? (
          <Sparkline
            data={metric.sparkline ?? []}
            stroke={tone.stroke}
            ariaLabel={`${metric.label} trend`}
            className="shrink-0 opacity-90"
          />
        ) : null}
      </div>
    </article>
  );
}

export function MetricCardSkeleton() {
  return (
    <div className="rounded-[var(--radius-card)] border border-border-subtle bg-surface p-4 shadow-[var(--shadow-card)]">
      <div className="flex items-start justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="size-7 rounded-lg" />
      </div>
      <Skeleton className="mt-3 h-6.5 w-24" />
      <div className="mt-3 flex items-end justify-between gap-3">
        <div className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-2.5 w-20" />
        </div>
        <Skeleton className="h-7 w-24" />
      </div>
    </div>
  );
}
