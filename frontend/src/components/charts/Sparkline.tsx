import { useId } from 'react';

import { cn } from '@/lib/utils/cn';

export interface SparklineProps {
  /** Data points, oldest first. */
  data: number[];
  width?: number;
  height?: number;
  stroke?: string;
  className?: string;
  /** Fill the area under the line with a soft gradient. */
  filled?: boolean;
  ariaLabel?: string;
}

/**
 * Lightweight SVG sparkline (no charting library) used inside KPI cards.
 * Renders crisply at small sizes and inherits the theme via CSS variables.
 */
export function Sparkline({
  data,
  width = 96,
  height = 28,
  stroke = 'var(--color-brand-500)',
  className,
  filled = true,
  ariaLabel,
}: SparklineProps) {
  const gradientId = useId();
  const points = data.length > 1 ? data : [0, 0];
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const padding = 2;

  const coordinates = points.map((value, index) => {
    const x = (index / (points.length - 1)) * (width - padding * 2) + padding;
    const y = height - padding - ((value - min) / span) * (height - padding * 2);
    return { x, y };
  });

  const line = coordinates.map(({ x, y }, index) => `${index === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
  const area = `${line} L${(width - padding).toFixed(2)},${height} L${padding},${height} Z`;
  const last = coordinates[coordinates.length - 1];

  return (
    <svg
      role="img"
      aria-label={ariaLabel}
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      className={cn('overflow-visible', className)}
      preserveAspectRatio="none"
    >
      {filled ? (
        <>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity="0.28" />
              <stop offset="100%" stopColor={stroke} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={area} fill={`url(#${gradientId})`} />
        </>
      ) : null}
      <path d={line} fill="none" stroke={stroke} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
      {last ? <circle cx={last.x} cy={last.y} r="2" fill={stroke} /> : null}
    </svg>
  );
}
