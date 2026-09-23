import { Skeleton } from '@/components/ui/Skeleton';

/**
 * Full-page dashboard skeleton.
 * Mirrors the real layout so content does not shift when the data resolves —
 * also used as the Suspense fallback for the lazily loaded dashboard chunk.
 */
export function DashboardSkeleton() {
  return (
    <div className="space-y-5" aria-busy="true" aria-live="polite">
      <div className="space-y-2">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-3.5 w-full max-w-xl" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, index) => (
          <Skeleton key={index} className="h-[124px] rounded-[var(--radius-card)]" />
        ))}
      </div>
      <div className="grid gap-5 xl:grid-cols-3">
        <Skeleton className="h-[340px] rounded-[var(--radius-card)] xl:col-span-2" />
        <Skeleton className="h-[340px] rounded-[var(--radius-card)]" />
      </div>
      <Skeleton className="h-[420px] rounded-[var(--radius-card)]" />
      <div className="grid gap-5 xl:grid-cols-3">
        <Skeleton className="h-[380px] rounded-[var(--radius-card)]" />
        <Skeleton className="h-[380px] rounded-[var(--radius-card)]" />
        <Skeleton className="h-[380px] rounded-[var(--radius-card)]" />
      </div>
    </div>
  );
}
