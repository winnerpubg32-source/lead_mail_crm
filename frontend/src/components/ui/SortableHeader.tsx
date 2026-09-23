import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';

import { TH } from '@/components/ui/Table';
import { cn } from '@/lib/utils/cn';
import type { SortDirection } from '@/hooks/useListQuery';

export interface SortableHeaderProps {
  label: string;
  /** DRF ordering field, e.g. `lead_score` or `company__name`. */
  field: string;
  direction: SortDirection | null;
  onToggle: (field: string) => void;
  className?: string;
  align?: 'left' | 'right' | 'center';
}

/** Table header cell that cycles asc → desc → default when clicked. */
export function SortableHeader({
  label,
  field,
  direction,
  onToggle,
  className,
  align = 'left',
}: SortableHeaderProps) {
  const Icon = direction === 'asc' ? ArrowUp : direction === 'desc' ? ArrowDown : ChevronsUpDown;

  return (
    <TH className={cn(align === 'right' && 'text-right', align === 'center' && 'text-center', className)}>
      <button
        type="button"
        onClick={() => onToggle(field)}
        aria-label={`Sort by ${label}`}
        aria-sort={direction === 'asc' ? 'ascending' : direction === 'desc' ? 'descending' : 'none'}
        className={cn(
          'inline-flex items-center gap-1 rounded text-[11px] font-semibold tracking-wide uppercase transition-colors',
          'hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500',
          direction ? 'text-fg' : 'text-subtle',
          align === 'right' && 'flex-row-reverse',
        )}
      >
        {label}
        <Icon className={cn('size-3', direction ? 'opacity-100' : 'opacity-50')} />
      </button>
    </TH>
  );
}
