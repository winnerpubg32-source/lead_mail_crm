import { ChevronLeft, ChevronRight } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';

export interface PaginationProps {
  /** Total number of records matching the current query. */
  count: number;
  page: number;
  pageSize: number;
  /** Whether DRF reported a next/previous page. */
  hasNext: boolean;
  hasPrevious: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  itemLabel?: string;
  className?: string;
}

/**
 * Pagination footer for list tables.
 * Shows the visible slice ("26–50 of 1,284 leads") and the page controls.
 */
export function Pagination({
  count,
  page,
  pageSize,
  hasNext,
  hasPrevious,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 25, 50, 100],
  itemLabel = 'records',
  className,
}: PaginationProps) {
  const first = count === 0 ? 0 : (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, count);
  const pageCount = Math.max(1, Math.ceil(count / pageSize));

  return (
    <div
      className={cn(
        'flex flex-wrap items-center justify-between gap-3 border-t border-border-subtle px-5 py-3',
        className,
      )}
    >
      <p className="text-[12.5px] text-subtle" data-testid="pagination-summary">
        Showing{' '}
        <span className="tabular font-medium text-muted">
          {formatNumber(first)}–{formatNumber(last)}
        </span>{' '}
        of <span className="tabular font-medium text-muted">{formatNumber(count)}</span> {itemLabel}
      </p>

      <div className="flex flex-wrap items-center gap-2">
        {onPageSizeChange ? (
          <label className="flex items-center gap-1.5 text-[12.5px] text-subtle">
            Rows
            <Select
              selectSize="sm"
              value={String(pageSize)}
              onChange={(event) => onPageSizeChange(Number(event.target.value))}
              aria-label="Rows per page"
              className="w-[72px]"
            >
              {pageSizeOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </Select>
          </label>
        ) : null}

        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={!hasPrevious}
            aria-label="Previous page"
            leadingIcon={<ChevronLeft className="size-3.5" />}
          >
            Prev
          </Button>
          <span className="tabular px-1 text-[12.5px] text-muted">
            {page} / {pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={!hasNext}
            aria-label="Next page"
            trailingIcon={<ChevronRight className="size-3.5" />}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
