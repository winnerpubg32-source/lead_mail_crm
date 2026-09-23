import type { SelectHTMLAttributes } from 'react';
import { forwardRef } from 'react';

import { cn } from '@/lib/utils/cn';

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  selectSize?: 'sm' | 'md';
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, selectSize = 'md', children, ...props },
  ref,
) {
  return (
    <select
      ref={ref}
      className={cn(
        'w-full appearance-none rounded-lg border border-border-subtle bg-surface text-fg',
        'bg-[url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 20 20\' fill=\'%2398a2b3\'%3E%3Cpath fill-rule=\'evenodd\' d=\'M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.06l3.71-3.83a.75.75 0 1 1 1.08 1.04l-4.25 4.39a.75.75 0 0 1-1.08 0L5.21 8.27a.75.75 0 0 1 .02-1.06Z\' clip-rule=\'evenodd\'/%3E%3C/svg%3E")]',
        'bg-[length:18px_18px] bg-[position:right_0.6rem_center] bg-no-repeat pr-9',
        'transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-500/20 focus:outline-none',
        selectSize === 'sm' ? 'h-8 pl-2.5 text-[13px]' : 'h-9.5 pl-3 text-sm',
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
});
