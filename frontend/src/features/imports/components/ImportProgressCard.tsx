import { Clock, Loader2 } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { formatNumber } from '@/lib/utils/format';
import type { ImportJob } from '@/types/import';

function Counter({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-lg border border-border-subtle bg-surface-2/60 px-3 py-2">
      <dt className="text-[11.5px] text-muted">{label}</dt>
      <dd className={`tabular mt-0.5 text-[15px] font-semibold ${tone ?? 'text-fg'}`}>
        {formatNumber(value)}
      </dd>
    </div>
  );
}

/**
 * Live progress while the worker processes the file.
 *
 * The counters come from the polling endpoint, so they climb as each chunk of
 * rows is committed.
 */
export function ImportProgressCard({ job }: { job: ImportJob }) {
  const { progress } = job;
  const percent = progress.percent;
  const queued = job.status === 'QUEUED';

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
            <Loader2 className="size-4.5 animate-spin" />
          </span>
          <div>
            <p className="text-[15px] font-semibold text-fg">
              {queued ? 'Queued for processing' : 'Importing in the background'}
            </p>
            <p className="text-[12.5px] text-muted">
              {queued
                ? 'The worker picked the job up — it starts as soon as a slot is free.'
                : `Processing ${job.filename} in chunks of 500 rows.`}
            </p>
          </div>
        </div>
        <p className="tabular text-2xl font-semibold text-fg">{percent}%</p>
      </div>

      <div className="space-y-4 px-5 py-4">
        <Progress
          value={percent}
          aria-label="Import progress"
          className="h-2.5"
        />

        <div className="flex flex-wrap items-center justify-between gap-2 text-[12.5px] text-muted">
          <span>
            <span className="tabular font-medium text-fg">{formatNumber(progress.processed)}</span> of{' '}
            <span className="tabular font-medium text-fg">{formatNumber(progress.total)}</span> rows
            processed
          </span>
          <span className="inline-flex items-center gap-1.5 text-subtle">
            <Clock className="size-3.5" />
            This page updates automatically
          </span>
        </div>

        <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
          <Counter label="Imported" value={job.valid_rows} tone="text-emerald-600 dark:text-emerald-400" />
          <Counter label="Duplicates" value={job.duplicate_rows} tone="text-sky-600 dark:text-sky-400" />
          <Counter label="Invalid" value={job.invalid_rows} tone="text-amber-600 dark:text-amber-400" />
          <Counter label="Missing e-mail" value={job.missing_email_rows} tone="text-muted" />
          <Counter label="Errors" value={job.error_rows} tone="text-rose-600 dark:text-rose-400" />
        </dl>
      </div>
    </Card>
  );
}
