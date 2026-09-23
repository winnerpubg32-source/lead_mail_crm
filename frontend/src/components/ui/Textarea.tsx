import type { TextareaHTMLAttributes } from 'react';

import { cn } from '@/lib/utils/cn';

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

export function Textarea({ className, ...props }: TextareaProps) {
  return (
    <textarea
      className={cn(
        'w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-[13px] text-fg placeholder:text-subtle',
        'focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20',
        'disabled:opacity-60',
        className,
      )}
      {...props}
    />
  );
}
