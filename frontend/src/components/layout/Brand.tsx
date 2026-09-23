import { cn } from '@/lib/utils/cn';

/** OutreachOS wordmark — monogram tile + product name. */
export function Brand({ collapsed = false, className }: { collapsed?: boolean; className?: string }) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <span className="grid size-8 shrink-0 place-items-center rounded-[10px] bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm">
        <svg viewBox="0 0 24 24" fill="none" className="size-4.5" aria-hidden="true">
          <rect x="3" y="6" width="18" height="12" rx="2.5" stroke="currentColor" strokeWidth="1.8" />
          <path
            d="M3.8 7.5 12 13l8.2-5.5"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      {!collapsed ? (
        <span className="flex min-w-0 flex-col leading-none">
          <span className="truncate text-[15px] font-semibold tracking-tight text-fg">OutreachOS</span>
          <span className="mt-0.5 text-[10.5px] font-medium tracking-wide text-subtle uppercase">
            Outreach &amp; CRM
          </span>
        </span>
      ) : null}
    </div>
  );
}
