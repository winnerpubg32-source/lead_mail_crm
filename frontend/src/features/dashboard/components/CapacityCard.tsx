import { AlertTriangle, Clock, MailWarning, Send } from 'lucide-react';

import { CapacityGauge } from '@/components/charts/CapacityGauge';
import { MiniBarChart } from '@/components/charts/MiniBarChart';
import { Card, CardHeader } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';
import type { DailyCapacityData } from '@/types/dashboard';

export interface CapacityCardProps {
  capacity: DailyCapacityData;
  className?: string;
}

/**
 * Daily sending budget.
 *
 * Shows the hard product guard rail (90 marketing e-mails/day) as a radial
 * gauge with the literal "sent / limit" fraction, plus the remaining quota —
 * exactly what the brief calls for — and supporting context (queued, failed,
 * sending window, hourly distribution).
 */
export function CapacityCard({ capacity, className }: CapacityCardProps) {
  const usedRatio = capacity.limit > 0 ? capacity.sent / capacity.limit : 0;
  const nearLimit = usedRatio >= 0.8;

  const stats = [
    {
      label: 'Remaining',
      value: formatNumber(capacity.remaining),
      icon: Send,
      accent: 'text-brand-600 dark:text-brand-300',
    },
    {
      label: 'Queued',
      value: formatNumber(capacity.queued),
      icon: Clock,
      accent: 'text-muted',
    },
    {
      label: 'Failed today',
      value: formatNumber(capacity.failed),
      icon: MailWarning,
      accent: capacity.failed > 0 ? 'text-rose-600 dark:text-rose-300' : 'text-muted',
    },
  ];

  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader
        title="Daily Capacity"
        description={`Workspace limit · ${capacity.windowLabel}`}
        action={
          nearLimit ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[11.5px] font-medium text-amber-700 ring-1 ring-amber-200 ring-inset dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/20">
              <AlertTriangle className="size-3" />
              Near limit
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[11.5px] font-medium text-emerald-700 ring-1 ring-emerald-200 ring-inset dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/20">
              <span className="size-1.5 rounded-full bg-emerald-500" />
              Healthy
            </span>
          )
        }
      />

      <div className="flex flex-1 flex-col gap-5 px-5 py-4 sm:flex-row sm:items-center">
        <div className="flex justify-center sm:justify-start">
          <CapacityGauge value={capacity.sent} limit={capacity.limit} />
        </div>

        <div className="flex-1 space-y-4">
          {/* Remaining quota — the headline number for the operator */}
          <div className="rounded-xl bg-surface-2 px-4 py-3 ring-1 ring-border-subtle ring-inset">
            <p className="text-[11px] font-semibold tracking-wider text-subtle uppercase">
              Remaining today
            </p>
            <p className="tabular mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-semibold text-fg">{formatNumber(capacity.remaining)}</span>
              <span className="text-[12.5px] text-muted">of {formatNumber(capacity.limit)} sends</span>
            </p>
          </div>

          <div>
            <div className="mb-1 flex items-center justify-between text-[11px] font-medium uppercase tracking-wide text-subtle">
              <span>Daily progress</span>
              <span className="tabular">{Math.round(Math.max(0, Math.min(1, usedRatio)) * 100)}%</span>
            </div>
            <Progress value={usedRatio * 100} size="sm" aria-label="Daily e-mail sending progress" />
          </div>

          <dl className="grid grid-cols-3 gap-3">
            {stats.map(({ label, value, icon: Icon, accent }) => (
              <div key={label}>
                <dt className="flex items-center gap-1 text-[11px] font-medium tracking-wide text-subtle uppercase">
                  <Icon className={cn('size-3', accent)} />
                  {label}
                </dt>
                <dd className={cn('tabular mt-0.5 text-[15px] font-semibold', accent)}>{value}</dd>
              </div>
            ))}
          </dl>

          <div>
            <p className="mb-1.5 text-[11px] font-medium tracking-wide text-subtle uppercase">
              Sending volume by hour
            </p>
            <MiniBarChart
              data={capacity.hourly}
              max={Math.max(12, ...capacity.hourly.map((point) => point.sent))}
              ariaLabel="E-mails sent per hour today"
            />
          </div>
        </div>
      </div>
    </Card>
  );
}
