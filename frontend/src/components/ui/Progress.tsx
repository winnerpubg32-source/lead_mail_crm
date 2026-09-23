import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/utils/cn';

export interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  size?: 'sm' | 'md';
}

/**Minimal horizontal progress bar used in list tables + cards. */
export function Progress({ value, max = 100, size = 'md', className, ...props }: ProgressProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cn(
        'w-full overflow-hidden rounded-full bg-surface-3',
        size === 'sm' ? 'h-1' : 'h-1.5',
        className,
      )}
      {...props}
    >
      <div
        className="h-full rounded-full bg-brand-500 transition-all"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
