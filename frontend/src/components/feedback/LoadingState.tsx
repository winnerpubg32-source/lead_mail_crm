import { Skeleton, SkeletonText } from '@/components/ui/Skeleton';
import { Spinner } from '@/components/feedback/Spinner';
import { cn } from '@/lib/utils/cn';

/** Inline "loading…" row for compact areas. */
export function LoadingState({ label = 'Loading', className }: { label?: string; className?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn('flex items-center justify-center gap-2 py-10 text-[13px] text-muted', className)}
    >
      <Spinner className="text-muted" />
      {label}
    </div>
  );
}

/** Skeleton block shaped like a KPI card. */
export function MetricCardSkeleton() {
  return (
    <div className="rounded-[var(--radius-card)] border border-border-subtle bg-surface p-4 shadow-[var(--shadow-card)]">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3.5 w-24" />
        <Skeleton className="size-7 rounded-lg" />
      </div>
      <Skeleton className="mt-3 h-7 w-20" />
      <Skeleton className="mt-3 h-3 w-28" />
    </div>
  );
}

/** Skeleton table rows used while a table query is pending. */
export function TableSkeleton({ rows = 5, columns = 6 }: { rows?: number; columns?: number }) {
  return (
    <div className="divide-y divide-[color:var(--app-border)]" aria-hidden="true">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="grid gap-4 px-4 py-3.5" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
          {Array.from({ length: columns }).map((__, columnIndex) => (
            <Skeleton key={columnIndex} className="h-3.5 w-full" />
          ))}
        </div>
      ))}
    </div>
  );
}

/** Skeleton for a chart/panel body. */
export function PanelSkeleton({ lines = 4 }: { lines?: number }) {
  return (
    <div className="px-5 py-4">
      <SkeletonText lines={lines} />
    </div>
  );
}
