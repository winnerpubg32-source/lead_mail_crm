import { FileSpreadsheet, Trash2 } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import { ImportStatusBadge } from '@/features/imports/components/ImportStatusBadge';
import { cn } from '@/lib/utils/cn';
import { formatBytes, formatDateTime, formatDuration, formatNumber } from '@/lib/utils/format';
import type { ImportJob } from '@/types/import';

export interface ImportHistoryTableProps {
  jobs: ImportJob[];
  onDelete: (job: ImportJob) => void;
  /** Id of the row currently being deleted (disables its button). */
  deletingId?: number | null;
}

function Metric({ value, tone }: { value: number; tone?: string }) {
  return <span className={cn('tabular', tone)}>{formatNumber(value)}</span>;
}

/** Every import ever run, newest first. */
export function ImportHistoryTable({ jobs, onDelete, deletingId = null }: ImportHistoryTableProps) {
  return (
    <TableWrapper>
      <Table>
        <THead>
          <TR>
            <TH className="min-w-[240px]">File</TH>
            <TH>Status</TH>
            <TH className="text-right">Rows</TH>
            <TH className="text-right">Imported</TH>
            <TH className="text-right">Duplicates</TH>
            <TH className="text-right">Invalid</TH>
            <TH className="text-right">Missing e-mail</TH>
            <TH className="min-w-[130px]">Started</TH>
            <TH>Duration</TH>
            <TH className="w-12">
              <span className="sr-only">Actions</span>
            </TH>
          </TR>
        </THead>
        <TBody>
          {jobs.map((job) => (
            <TR key={job.id}>
              <TD>
                <div className="flex items-center gap-2.5">
                  <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-surface-3 text-subtle">
                    <FileSpreadsheet className="size-3.5" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate font-medium text-fg" title={job.filename}>
                      {job.filename}
                    </p>
                    <p className="truncate text-[11.5px] text-subtle">
                      <span className="font-mono uppercase">{job.file_type}</span> · {formatBytes(job.file_size)}
                    </p>
                  </div>
                </div>
              </TD>

              <TD>
                <div className="flex flex-col items-start gap-1">
                  <ImportStatusBadge status={job.status} label={job.status_display} />
                  {job.status === 'FAILED' && job.error_message ? (
                    <span className="max-w-[200px] truncate text-[11px] text-rose-600 dark:text-rose-300" title={job.error_message}>
                      {job.error_message}
                    </span>
                  ) : null}
                </div>
              </TD>

              <TD className="text-right text-[12.5px] text-muted">
                <Metric value={job.total_rows} />
              </TD>
              <TD className="text-right text-[12.5px]">
                <Metric value={job.valid_rows} tone="font-medium text-emerald-600 dark:text-emerald-400" />
              </TD>
              <TD className="text-right text-[12.5px]">
                <Metric value={job.duplicate_rows} tone="text-sky-600 dark:text-sky-400" />
              </TD>
              <TD className="text-right text-[12.5px]">
                <Metric value={job.invalid_rows} tone="text-amber-600 dark:text-amber-400" />
              </TD>
              <TD className="text-right text-[12.5px] text-muted">
                <Metric value={job.missing_email_rows} />
              </TD>

              <TD className="text-[12.5px] whitespace-nowrap text-muted">
                {job.started_at ? formatDateTime(job.started_at) : formatDateTime(job.created_at)}
              </TD>

              <TD className="text-[12.5px] whitespace-nowrap text-muted">
                {job.duration_seconds !== null ? (
                  formatDuration(job.duration_seconds)
                ) : job.status === 'QUEUED' ? (
                  <Badge tone="info" size="sm">
                    Waiting
                  </Badge>
                ) : (
                  '—'
                )}
              </TD>

              <TD className="text-right">
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Delete ${job.filename}`}
                  title="Delete this import record"
                  isLoading={deletingId === job.id}
                  disabled={job.status === 'PROCESSING'}
                  onClick={() => onDelete(job)}
                >
                  <Trash2 className="size-4" />
                </Button>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </TableWrapper>
  );
}
