import type { ReactNode } from 'react';

import { cn } from '@/lib/utils/cn';

export interface PageHeaderProps {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
  /** Tabs/filters row rendered underneath the title block. */
  toolbar?: ReactNode;
  className?: string;
}

export function PageHeader({ title, description, eyebrow, actions, toolbar, className }: PageHeaderProps) {
  return (
    <div className={cn('mb-5 space-y-4', className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          {eyebrow ? (
            <p className="mb-1 text-[11px] font-semibold tracking-wider text-brand-600 uppercase dark:text-brand-300">
              {eyebrow}
            </p>
          ) : null}
          <h1 className="text-xl font-semibold tracking-tight text-fg sm:text-[22px]">{title}</h1>
          {description ? <p className="mt-1 max-w-3xl text-[13.5px] text-muted">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      {toolbar}
    </div>
  );
}
