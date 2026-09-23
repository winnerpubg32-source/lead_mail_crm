import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  Mail,
  MailQuestion,
  Phone,
  UserX,
  XCircle,
  type LucideIcon,
} from 'lucide-react';

import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';
import type { DataQualityStats } from '@/types/dataQuality';

interface StatTileProps {
  label: string;
  value: number;
  icon: LucideIcon;
  tone: 'emerald' | 'rose' | 'amber' | 'sky' | 'violet' | 'slate';
  href?: string;
  hint?: string;
}

const toneStyles: Record<StatTileProps['tone'], string> = {
  emerald: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300',
  rose: 'bg-rose-50 text-rose-600 dark:bg-rose-500/15 dark:text-rose-300',
  amber: 'bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300',
  sky: 'bg-sky-50 text-sky-600 dark:bg-sky-500/15 dark:text-sky-300',
  violet: 'bg-violet-50 text-violet-600 dark:bg-violet-500/15 dark:text-violet-300',
  slate: 'bg-slate-100 text-slate-600 dark:bg-slate-500/15 dark:text-slate-300',
};

function StatTile({ label, value, icon: Icon, tone, href, hint }: StatTileProps) {
  const Wrapper: React.ElementType = href ? 'a' : 'div';
  return (
    <Wrapper
      href={href}
      className={cn(
        'group relative flex flex-col rounded-[var(--radius-card)] border border-border-subtle bg-surface p-4 shadow-[var(--shadow-card)] transition-colors hover:border-border-strong',
        href && 'cursor-pointer',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-[12.5px] font-medium text-muted">{label}</h3>
        <span className={cn('grid size-7 shrink-0 place-items-center rounded-lg', toneStyles[tone])}>
          <Icon className="size-3.5" />
        </span>
      </div>
      <p className="tabular mt-2.5 text-[24px] leading-none font-semibold tracking-tight text-fg">
        {formatNumber(value)}
      </p>
      {hint ? (
        <p className="mt-2 truncate text-[11.5px] text-subtle" title={hint}>
          {hint}
        </p>
      ) : null}
    </Wrapper>
  );
}

interface Props {
  stats: DataQualityStats;
}

/** Grid of KPI tiles for the Data Quality dashboard. */
export function StatsOverviewCard({ stats }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatTile
        label="Total leads"
        value={stats.total_leads}
        icon={Building2}
        tone="violet"
        hint="Active (non-merged) records"
      />
      <StatTile
        label="Valid e-mails"
        value={stats.valid_emails}
        icon={CheckCircle2}
        tone="emerald"
        href="/leads?email_status=VALID"
        hint="Deliverable addresses"
      />
      <StatTile
        label="Invalid e-mails"
        value={stats.invalid_emails}
        icon={XCircle}
        tone="rose"
        href="/leads?email_status=INVALID"
      />
      <StatTile
        label="Missing e-mails"
        value={stats.missing_emails}
        icon={MailQuestion}
        tone="amber"
        href="/missing-email"
        hint="Awaiting enrichment"
      />
      <StatTile label="Missing phones" value={stats.missing_phones} icon={Phone} tone="amber" />
      <StatTile label="Missing websites" value={stats.missing_websites} icon={Mail} tone="sky" />
      <StatTile label="Missing contact names" value={stats.missing_contact_names} icon={UserX} tone="sky" />
      <StatTile
        label="Open duplicates"
        value={stats.duplicate_groups}
        icon={AlertTriangle}
        tone={stats.duplicate_groups > 0 ? 'rose' : 'slate'}
        href="/duplicates"
        hint="Pairs to review"
      />
    </div>
  );
}
