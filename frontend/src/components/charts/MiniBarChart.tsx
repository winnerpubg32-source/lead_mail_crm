import { cn } from '@/lib/utils/cn';

export interface MiniBarChartProps {
  data: Array<{ hour: string; sent: number }>;
  className?: string;
  /** Upper bound for the bar height; defaults to the largest value. */
  max?: number;
  color?: string;
  height?: number;
  ariaLabel?: string;
}

/**
 * Compact bar chart for intraday sending volume.
 * Pure SVG so it renders identically in the sidebar-sized dashboard cards and
 * in printed/PDF reports.
 */
export function MiniBarChart({
  data,
  className,
  max,
  color = 'var(--color-brand-500)',
  height = 56,
  ariaLabel,
}: MiniBarChartProps) {
  const maxValue = max ?? Math.max(1, ...data.map((point) => point.sent));
  const showLabels = data.length <= 10;

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-end gap-1.5" style={{ height }} role="img" aria-label={ariaLabel}>
        {data.map((point) => {
          const ratio = maxValue > 0 ? point.sent / maxValue : 0;
          const barHeight = point.sent === 0 ? 3 : Math.max(6, ratio * height);
          return (
            <div
              key={point.hour}
              className="group relative flex-1"
              title={`${point.hour} · ${point.sent} sent`}
            >
              <div
                className="w-full rounded-sm transition-all duration-500"
                style={{
                  height: barHeight,
                  backgroundColor: point.sent === 0 ? 'var(--app-surface-3)' : color,
                  opacity: point.sent === 0 ? 1 : 0.85,
                }}
              />
            </div>
          );
        })}
      </div>
      {showLabels ? (
        <div className="mt-1.5 flex gap-1.5">
          {data.map((point) => (
            <span key={point.hour} className="flex-1 text-center text-[10px] text-subtle">
              {point.hour.slice(0, 2)}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
