import { cn } from '@/lib/utils/cn';

export interface CapacityGaugeProps {
  /** E-mails already sent today. */
  value: number;
  /** Product limit — 90 marketing e-mails per day. */
  limit: number;
  size?: number;
  className?: string;
}

/**
 * Radial gauge for the daily sending budget.
 *
 * Reads `value / limit` and renders the exact "0 / 90" fraction the brief asks
 * for, with the remaining quota underneath. The arc colour shifts from brand →
 * amber → rose as the quota is consumed so the operator sees the risk early.
 */
export function CapacityGauge({ value, limit, size = 168, className }: CapacityGaugeProps) {
  const safeLimit = limit > 0 ? limit : 1;
  const ratio = Math.max(0, Math.min(1, value / safeLimit));
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - ratio);

  const strokeColor =
    ratio >= 0.9 ? 'var(--color-rose-500)' : ratio >= 0.7 ? 'var(--color-amber-500)' : 'var(--color-brand-500)';

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label={`${value} of ${limit} daily e-mails sent`}
        className="-rotate-90"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--app-surface-3)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
        <span className="tabular text-[26px] leading-none font-semibold text-fg">
          {value} / {limit}
        </span>
        <span className="text-[11px] font-medium tracking-wide text-subtle uppercase">
          Today’s capacity
        </span>
      </div>
    </div>
  );
}
