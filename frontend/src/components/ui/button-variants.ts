import { cn } from '@/lib/utils/cn';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

export const buttonVariantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-brand-600 text-white shadow-sm hover:bg-brand-700 active:bg-brand-800',
  secondary: 'bg-surface-3 text-fg hover:bg-border-subtle active:bg-border-strong',
  outline: 'border border-border-strong bg-surface text-fg hover:bg-surface-3 active:bg-border-subtle',
  ghost: 'text-muted hover:bg-surface-3 hover:text-fg active:bg-border-subtle',
  danger: 'bg-rose-600 text-white shadow-sm hover:bg-rose-700 active:bg-rose-800',
  success: 'bg-emerald-600 text-white shadow-sm hover:bg-emerald-700 active:bg-emerald-800',
};

export const buttonSizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 gap-1.5 px-3 text-[13px]',
  md: 'h-9.5 gap-2 px-3.5 text-sm',
  lg: 'h-11 gap-2 px-5 text-sm',
  icon: 'size-9 justify-center',
};

/**
 * Shared class recipe for buttons.
 *
 * Kept in its own module (no components) so `<button>` elements and `<Link>`s
 * can render identically — and so React Fast Refresh stays happy.
 */
export function buttonVariants({
  variant = 'primary',
  size = 'md',
  className,
}: {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
} = {}): string {
  return cn(
    'inline-flex select-none items-center justify-center rounded-lg font-medium transition-colors',
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500',
    'disabled:pointer-events-none disabled:opacity-60',
    buttonVariantStyles[variant],
    buttonSizeStyles[size],
    className,
  );
}
