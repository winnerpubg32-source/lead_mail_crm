import { cn } from '@/lib/utils/cn';

export type ProgressTone = 'brand' | 'emerald' | 'amber' | 'rose' | 'sky' | 'violet';

const toneClasses: Record<ProgressTone, string> = {
  brand: 'bg-brand-500',
  emerald: 'bg-emerald-500',
  amber: 'bg-amber-500',
  rose: 'bg-rose-500',
  sky: 'bg-sky-500',
  violet: 'bg-violet-500',
};

export interface ProgressProps {
  /** 0–100. Values outside the range are clamped. */
  value: number;
  tone?: ProgressTone;
  className?: string;
  label?: string;
  size?: 'sm' | 'md';
}

export function Progress({ value, tone = 'brand', className, label, size = 'md' }: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0));
  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
      className={cn(
        'w-full overflow-hidden rounded-full bg-surface-3',
        size === 'sm' ? 'h-1.5' : 'h-2',
        className,
      )}
    >
      <div
        className={cn('h-full rounded-full transition-[width] duration-500', toneClasses[tone])}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
