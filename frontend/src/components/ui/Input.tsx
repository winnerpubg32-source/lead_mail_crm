import type { InputHTMLAttributes, ReactNode } from 'react';
import { forwardRef } from 'react';

import { cn } from '@/lib/utils/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  inputSize?: 'sm' | 'md';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, leadingIcon, trailingIcon, inputSize = 'md', ...props },
  ref,
) {
  const field = (
    <input
      ref={ref}
      className={cn(
        'w-full rounded-lg border border-border-subtle bg-surface text-fg placeholder:text-subtle',
        'transition-colors focus:border-brand-400 focus:outline-none focus-visible:outline-none',
        'focus:ring-2 focus:ring-brand-500/20 disabled:cursor-not-allowed disabled:opacity-60',
        leadingIcon ? 'pl-9' : 'pl-3',
        trailingIcon ? 'pr-9' : 'pr-3',
        inputSize === 'sm' ? 'h-8 text-[13px]' : 'h-9.5 text-sm',
        className,
      )}
      {...props}
    />
  );

  if (!leadingIcon && !trailingIcon) return field;

  return (
    <div className="relative w-full">
      {leadingIcon ? (
        <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-subtle [&>svg]:size-4">
          {leadingIcon}
        </span>
      ) : null}
      {field}
      {trailingIcon ? (
        <span className="absolute top-1/2 right-3 -translate-y-1/2 text-subtle [&>svg]:size-4">
          {trailingIcon}
        </span>
      ) : null}
    </div>
  );
});
