import { useId, useState } from 'react';

import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';

export interface SourceDonutDatum {
  id: string;
  label: string;
  count: number;
  share: number;
  color: string;
}

export interface SourceDonutProps {
  data: SourceDonutDatum[];
  className?: string;
  /** Rendered in the middle of the ring while nothing is hovered. */
  centerLabel?: string;
  centerValue?: string;
}

const SIZE = 180;
const STROKE = 22;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const GAP = 1.2; // percentage points of blank space between segments

/**
 * Lead source breakdown as a donut, drawn with plain SVG.
 *
 * No charting library is pulled in for this: the geometry is a handful of
 * `stroke-dasharray` arcs, which keeps the bundle small and lets the ring react
 * to hover (centre label swaps to the hovered source).
 */
export function SourceDonut({ data, className, centerLabel, centerValue }: SourceDonutProps) {
  const titleId = useId();
  const [activeId, setActiveId] = useState<string | null>(null);

  const total = data.reduce((sum, item) => sum + item.count, 0);
  const active = data.find((item) => item.id === activeId);

  const fractions = data.map((item) => (total > 0 ? item.count / total : 0));
  const segments = data.map((item, index) => {
    // Cumulative share of the preceding segments — the arc's start position.
    const offset = fractions.slice(0, index).reduce((sum, value) => sum + value, 0) * 100;
    const length = Math.max(fractions[index] * 100 - GAP, 0.6);
    return { ...item, dash: (length / 100) * CIRCUMFERENCE, offset };
  });

  return (
    <div className={cn('relative aspect-square w-full max-w-[200px]', className)}>
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        role="img"
        aria-labelledby={titleId}
        className="size-full -rotate-90"
      >
        <title id={titleId}>Lead source breakdown</title>

        {/* Track */}
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="var(--app-surface-3)"
          strokeWidth={STROKE}
        />

        {segments.map((segment) => {
          const isActive = segment.id === activeId;
          return (
            <circle
              key={segment.id}
              cx={SIZE / 2}
              cy={SIZE / 2}
              r={RADIUS}
              fill="none"
              stroke={segment.color}
              strokeWidth={isActive ? STROKE + 4 : STROKE}
              strokeDasharray={`${segment.dash} ${CIRCUMFERENCE - segment.dash}`}
              strokeDashoffset={-(segment.offset / 100) * CIRCUMFERENCE}
              strokeLinecap="butt"
              className="cursor-pointer transition-[stroke-width] duration-200"
              onMouseEnter={() => setActiveId(segment.id)}
              onMouseLeave={() => setActiveId(null)}
            >
              <title>
                {segment.label}: {formatNumber(segment.count)} leads ({segment.share}%)
              </title>
            </circle>
          );
        })}
      </svg>

      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
        {active ? (
          <>
            <span className="tabular text-lg leading-none font-semibold text-fg">
              {formatNumber(active.count)}
            </span>
            <span className="mt-1 max-w-[110px] truncate text-[11px] text-muted">{active.label}</span>
            <span className="tabular text-[11px] text-subtle">{active.share}%</span>
          </>
        ) : centerValue ? (
          <>
            <span className="tabular text-lg leading-none font-semibold text-fg">{centerValue}</span>
            {centerLabel ? (
              <span className="mt-1 text-[11px] tracking-wide text-subtle uppercase">
                {centerLabel}
              </span>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}
