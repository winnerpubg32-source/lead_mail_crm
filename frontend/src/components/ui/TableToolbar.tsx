import { Search, X } from 'lucide-react';
import type { ReactNode } from 'react';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { cn } from '@/lib/utils/cn';

export interface FilterSelectConfig {
  /** Query parameter name sent to the API, e.g. `lead_status`. */
  name: string;
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
}

export interface TableToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  filters?: FilterSelectConfig[];
  onFilterChange?: (name: string, value: string) => void;
  /** Extra controls rendered before the reset button (e.g. result count). */
  extra?: ReactNode;
  onReset?: () => void;
  hasActiveQuery?: boolean;
  className?: string;
}

/**
 * Search + filter bar shared by the leads, companies and contacts tables.
 *
 * Filters render as native selects so they stay keyboard accessible and work
 * without any custom dropdown machinery.
 */
export function TableToolbar({
  search,
  onSearchChange,
  searchPlaceholder = 'Search…',
  filters = [],
  onFilterChange,
  extra,
  onReset,
  hasActiveQuery = false,
  className,
}: TableToolbarProps) {
  return (
    <div className={cn('flex flex-wrap items-center gap-2 px-5 py-3', className)}>
      <div className="min-w-[220px] flex-1">
        <Input
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={searchPlaceholder}
          aria-label={searchPlaceholder}
          leadingIcon={<Search />}
          inputSize="sm"
        />
      </div>

      {filters.map((filter) => (
        <label key={filter.name} className="flex items-center gap-1.5">
          <span className="sr-only">{filter.label}</span>
          <select
            value={filter.value}
            onChange={(event) => onFilterChange?.(filter.name, event.target.value)}
            aria-label={filter.label}
            className={cn(
              'h-8 max-w-[190px] appearance-none rounded-lg border bg-surface pr-8 pl-2.5 text-[13px] text-fg',
              'bg-[length:16px_16px] bg-[position:right_0.5rem_center] bg-no-repeat',
              "bg-[url(\"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='%2398a2b3'%3E%3Cpath fill-rule='evenodd' d='M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.06l3.71-3.83a.75.75 0 1 1 1.08 1.04l-4.25 4.39a.75.75 0 0 1-1.08 0L5.21 8.27a.75.75 0 0 1 .02-1.06Z' clip-rule='evenodd'/%3E%3C/svg%3E\")]",
              'transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-500/20 focus:outline-none',
              filter.value ? 'border-brand-400 text-fg' : 'border-border-subtle text-muted',
            )}
          >
            <option value="">{filter.label}</option>
            {filter.options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      ))}

      {extra}

      {onReset && hasActiveQuery ? (
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          leadingIcon={<X className="size-3.5" />}
          aria-label="Clear search and filters"
        >
          Clear
        </Button>
      ) : null}
    </div>
  );
}
