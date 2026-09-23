import { cn } from '@/lib/utils/cn';
import { initialsFromName } from '@/lib/utils/format';

const sizes = {
  xs: 'size-6 text-[10px]',
  sm: 'size-7 text-[11px]',
  md: 'size-9 text-xs',
  lg: 'size-11 text-sm',
};

export interface AvatarProps {
  name: string;
  size?: keyof typeof sizes;
  className?: string;
  tone?: 'brand' | 'neutral';
}

export function Avatar({ name, size = 'sm', className, tone = 'brand' }: AvatarProps) {
  return (
    <span
      aria-hidden="true"
      title={name}
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-full font-semibold',
        tone === 'brand'
          ? 'bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-200'
          : 'bg-surface-3 text-muted',
        sizes[size],
        className,
      )}
    >
      {initialsFromName(name)}
    </span>
  );
}
