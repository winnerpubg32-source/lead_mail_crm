import { AlertTriangle, Mail, MailX, Rows3, Users } from 'lucide-react';
import type { ReactNode } from 'react';

import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';
import type { PreviewCounts } from '@/types/import';

interface StatConfig {
  key: keyof PreviewCounts;
  label: string;
  icon: ReactNode;
  tone: string;
  hint: string;
}

const STATS: StatConfig[] = [
  {
    key: 'total_rows',
    label: 'Total rows',
    icon: <Rows3 className="size-4" />,
    tone: 'text-fg',
    hint: 'Data rows found in the file (header excluded)',
  },
  {
    key: 'rows_with_email',
    label: 'Rows with e-mail',
    icon: <Mail className="size-4" />,
    tone: 'text-emerald-600 dark:text-emerald-400',
    hint: 'Rows carrying a syntactically valid address',
  },
  {
    key: 'rows_without_email',
    label: 'Rows without e-mail',
    icon: <MailX className="size-4" />,
    tone: 'text-amber-600 dark:text-amber-400',
    hint: 'Stored anyway — these leads just cannot be e-mailed yet',
  },
  {
    key: 'potential_duplicates',
    label: 'Potential duplicates',
    icon: <Users className="size-4" />,
    tone: 'text-sky-600 dark:text-sky-400',
    hint: 'Matching an existing record or another row in this file',
  },
  {
    key: 'invalid_emails',
    label: 'Invalid e-mails',
    icon: <AlertTriangle className="size-4" />,
    tone: 'text-rose-600 dark:text-rose-400',
    hint: 'Failed syntax validation — the address is dropped, the row is kept',
  },
];

/** The five preview numbers shown before the user confirms the import. */
export function PreviewStats({ counts }: { counts: PreviewCounts }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {STATS.map((stat) => (
        <Card key={stat.key} className="p-4" title={stat.hint}>
          <div className="flex items-center justify-between gap-2">
            <p className="text-[12px] font-medium text-muted">{stat.label}</p>
            <span className={cn('shrink-0', stat.tone)}>{stat.icon}</span>
          </div>
          <p className={cn('tabular mt-2 text-2xl font-semibold', stat.tone)}>
            {formatNumber(counts[stat.key])}
          </p>
          <p className="mt-1 text-[11.5px] text-subtle">{stat.hint}</p>
        </Card>
      ))}
    </div>
  );
}
