import type { HTMLAttributes, ReactNode } from 'react';

import { cn } from '@/lib/utils/cn';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Adds hover affordance for clickable cards. */
  interactive?: boolean;
  padded?: boolean;
}

export function Card({ className, interactive = false, padded = false, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-[var(--radius-card)] border border-border-subtle bg-surface shadow-[var(--shadow-card)]',
        padded && 'p-5',
        interactive &&
          'transition-colors hover:border-border-strong hover:bg-surface-2 focus-within:border-brand-400',
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({
  title,
  description,
  action,
  className,
  children,
}: {
  title?: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-start justify-between gap-3 border-b border-border-subtle px-5 py-4',
        className,
      )}
    >
      {children ?? (
        <div className="min-w-0">
          {title ? <h3 className="truncate text-[15px] font-semibold">{title}</h3> : null}
          {description ? <p className="mt-0.5 text-[13px] text-muted">{description}</p> : null}
        </div>
      )}
      {action ? <div className="flex shrink-0 items-center gap-2">{action}</div> : null}
    </div>
  );
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-5 py-4', className)} {...props} />;
}

export function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3 border-t border-border-subtle px-5 py-3 text-[13px] text-muted',
        className,
      )}
      {...props}
    />
  );
}
