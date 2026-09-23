import { AlertTriangle, RotateCw } from 'lucide-react';
import type { ReactNode } from 'react';

import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils/cn';

export interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  details?: string;
  action?: ReactNode;
  className?: string;
}

/** Shown when a query fails (network, 4xx/5xx, unhandled error). */
export function ErrorState({
  title = 'Something went wrong',
  description = 'We could not load this data. Check that the API is running and try again.',
  onRetry,
  details,
  action,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border border-rose-200 bg-rose-50/60 px-6 py-10 text-center dark:border-rose-500/25 dark:bg-rose-500/5',
        className,
      )}
    >
      <div className="flex size-11 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-300 [&>svg]:size-5">
        <AlertTriangle />
      </div>
      <div className="max-w-md space-y-1">
        <h3 className="text-sm font-semibold text-fg">{title}</h3>
        <p className="text-[13px] text-muted">{description}</p>
        {details ? (
          <p className="mt-1 font-mono text-[11px] break-all text-subtle">{details}</p>
        ) : null}
      </div>
      {action ??
        (onRetry ? (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            leadingIcon={<RotateCw className="size-3.5" />}
          >
            Try again
          </Button>
        ) : null)}
    </div>
  );
}
