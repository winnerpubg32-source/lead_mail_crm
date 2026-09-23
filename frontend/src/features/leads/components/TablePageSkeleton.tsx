import { Skeleton } from '@/components/ui/Skeleton';

/** Suspense fallback for the list pages: header + toolbar + table rows. */
export function TablePageSkeleton() {
  return (
    <div className="space-y-5" aria-busy="true" aria-live="polite">
      <div className="space-y-2">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-3.5 w-full max-w-2xl" />
      </div>
      <div className="rounded-[var(--radius-card)] border border-border-subtle bg-surface">
        <div className="flex flex-wrap items-center gap-2 border-b border-border-subtle px-5 py-3">
          <Skeleton className="h-8 min-w-[220px] flex-1" />
          <Skeleton className="h-8 w-[150px]" />
          <Skeleton className="h-8 w-[150px]" />
          <Skeleton className="h-8 w-[130px]" />
        </div>
        <div className="space-y-3 p-5">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="grid grid-cols-9 items-center gap-3">
              {Array.from({ length: 9 }).map((__, cell) => (
                <Skeleton key={cell} className="h-3.5 w-full" />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
