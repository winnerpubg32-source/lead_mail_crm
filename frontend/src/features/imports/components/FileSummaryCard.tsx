import { FileSpreadsheet, Layers, Table2 } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils/cn';
import { formatBytes, formatNumber } from '@/lib/utils/format';
import type { ImportJobDetail } from '@/types/import';

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-[11px] font-medium tracking-wide text-subtle uppercase">{label}</dt>
      <dd className="mt-0.5 truncate text-[13.5px] font-medium text-fg" title={value}>
        {value}
      </dd>
    </div>
  );
}

export interface FileSummaryCardProps {
  job: ImportJobDetail;
  /** Switch the analysed sheet (workbooks with more than one sheet). */
  onSelectSheet?: (sheet: string) => void;
  switchingSheet?: boolean;
}

/**
 * "What did we just receive?" — filename, size, detected type, sheets and the
 * detected row count, shown above the preview.
 */
export function FileSummaryCard({ job, onSelectSheet, switchingSheet = false }: FileSummaryCardProps) {
  const { uploaded } = job;
  const sheets = uploaded.sheets ?? [];
  const isWorkbook = uploaded.file_type !== 'csv';

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border-subtle px-5 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
            <FileSpreadsheet className="size-5" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-[15px] font-semibold text-fg" title={job.filename}>
              {job.filename}
            </p>
            <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12.5px] text-muted">
              <span>{formatBytes(uploaded.file_size || job.file_size)}</span>
              <span aria-hidden="true">·</span>
              <span className="font-mono text-[11.5px] tracking-wide uppercase">
                {uploaded.file_type}
              </span>
              {uploaded.encoding && uploaded.file_type === 'csv' ? (
                <>
                  <span aria-hidden="true">·</span>
                  <span>{uploaded.encoding}</span>
                </>
              ) : null}
              {uploaded.delimiter && uploaded.file_type === 'csv' ? (
                <>
                  <span aria-hidden="true">·</span>
                  <span>delimiter “{uploaded.delimiter}”</span>
                </>
              ) : null}
            </p>
          </div>
        </div>

        <Badge tone="neutral" size="sm" className="font-mono">
          {formatNumber(job.total_rows)} data rows
        </Badge>
      </div>

      <dl className="grid gap-4 px-5 py-4 sm:grid-cols-2 lg:grid-cols-4">
        <Detail label="File name" value={job.filename} />
        <Detail label="File size" value={formatBytes(uploaded.file_size || job.file_size)} />
        <Detail label="File type" value={uploaded.file_type.toUpperCase()} />
        <Detail
          label="Detected rows"
          value={job.total_rows > 0 ? formatNumber(job.total_rows) : 'Not available'}
        />
      </dl>

      {isWorkbook ? (
        <div className="border-t border-border-subtle px-5 py-4">
          <p className="flex items-center gap-1.5 text-[11px] font-medium tracking-wide text-subtle uppercase">
            <Layers className="size-3.5" />
            Detected sheets ({sheets.length || uploaded.sheet_count})
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {(sheets.length ? sheets : [uploaded.selected_sheet]).filter(Boolean).map((sheet) => {
              const active = sheet === uploaded.selected_sheet;
              return (
                <button
                  key={sheet}
                  type="button"
                  aria-pressed={active}
                  disabled={switchingSheet || active || !onSelectSheet}
                  onClick={() => onSelectSheet?.(sheet)}
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[12.5px] font-medium transition-colors',
                    active
                      ? 'border-brand-300 bg-brand-50 text-brand-700 dark:border-brand-500/25 dark:bg-brand-500/15 dark:text-brand-200'
                      : 'border-border-subtle bg-surface text-muted hover:border-border-strong hover:text-fg',
                    switchingSheet && !active && 'opacity-60',
                  )}
                >
                  <Table2 className="size-3.5" />
                  {sheet}
                  {active ? <span className="text-[11px] opacity-80">· analysed</span> : null}
                </button>
              );
            })}
          </div>
          <p className="mt-2 text-[12px] text-subtle">
            Only the selected sheet is imported. Choose another sheet to preview its columns instead.
          </p>
        </div>
      ) : null}
    </Card>
  );
}
