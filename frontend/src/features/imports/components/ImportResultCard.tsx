import { CheckCircle2, History, RotateCw, Target } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Card } from '@/components/ui/Card';
import { buttonVariants } from '@/components/ui/button-variants';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils/cn';
import { formatDuration, formatNumber } from '@/lib/utils/format';
import { paths } from '@/routes/paths';
import type { ImportJob, ImportSummaryKey } from '@/types/import';

/** The five numbers the brief asks for, in this order. */
const HEADLINE: Array<{ key: ImportSummaryKey; label: string; tone: string }> = [
  { key: 'Total', label: 'Total', tone: 'text-fg' },
  { key: 'Imported', label: 'Imported', tone: 'text-emerald-600 dark:text-emerald-400' },
  { key: 'Duplicates', label: 'Duplicates', tone: 'text-sky-600 dark:text-sky-400' },
  { key: 'Invalid', label: 'Invalid', tone: 'text-amber-600 dark:text-amber-400' },
  { key: 'Missing Email', label: 'Missing email', tone: 'text-muted' },
];

export interface ImportResultCardProps {
  job: ImportJob;
  /** Reset the wizard back to the dropzone. */
  onStartOver: () => void;
}

/** "Import completed" screen with the per-bucket row counts. */
export function ImportResultCard({ job, onStartOver }: ImportResultCardProps) {
  const { summary } = job;

  return (
    <Card className="animate-[var(--animate-slide-up)] overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle bg-emerald-50/60 px-5 py-4 dark:bg-emerald-500/5">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-xl bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300">
            <CheckCircle2 className="size-5" />
          </span>
          <div>
            <h2 className="text-[16px] font-semibold text-fg">Import completed</h2>
            <p className="text-[12.5px] text-muted">
              {job.filename}
              {job.duration_seconds !== null ? ` · finished in ${formatDuration(job.duration_seconds)}` : ''}
            </p>
          </div>
        </div>
        {job.completed_at ? (
          <p className="text-[12px] text-subtle">
            Completed {new Date(job.completed_at).toLocaleTimeString()}
          </p>
        ) : null}
      </div>

      <dl className="grid gap-3 px-5 py-5 sm:grid-cols-3 lg:grid-cols-5">
        {HEADLINE.map((entry) => (
          <div key={entry.key} className="rounded-xl border border-border-subtle bg-surface-2/50 px-4 py-3">
            <dt className="text-[12px] font-medium text-muted">{entry.label}</dt>
            <dd className={cn('tabular mt-1 text-2xl font-semibold', entry.tone)}>
              {formatNumber(summary[entry.key])}
            </dd>
          </div>
        ))}
      </dl>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-border-subtle px-5 py-3 text-[12.5px] text-muted">
        <span>
          New companies:{' '}
          <span className="tabular font-medium text-fg">{formatNumber(summary['New companies'])}</span>
        </span>
        <span>
          New contacts:{' '}
          <span className="tabular font-medium text-fg">{formatNumber(summary['New contacts'])}</span>
        </span>
        <span>
          Errors: <span className="tabular font-medium text-fg">{formatNumber(summary.Errors)}</span>
        </span>
        {summary['Missing Email'] > 0 ? (
          <span className="text-amber-700 dark:text-amber-300">
            {formatNumber(summary['Missing Email'])} row
            {summary['Missing Email'] === 1 ? '' : 's'} stored without an e-mail address
          </span>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-border-subtle px-5 py-4">
        <Button onClick={onStartOver} leadingIcon={<RotateCw className="size-3.5" />}>
          Import another file
        </Button>
        <Link to={paths.leads} className={buttonVariants({ variant: 'outline', size: 'md' })}>
          <Target className="mr-1.5 size-3.5" />
          View leads
        </Link>
        <Link to={paths.importsHistory} className={buttonVariants({ variant: 'ghost', size: 'md' })}>
          <History className="mr-1.5 size-3.5" />
          Import history
        </Link>
      </div>
    </Card>
  );
}
