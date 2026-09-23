import { useState } from 'react';

import { Building2, Mail, MergeIcon, ShieldCheck, X } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils/cn';
import { formatDate } from '@/lib/utils/format';
import type { DuplicateGroup } from '@/types/dataQuality';

interface Props {
  group: DuplicateGroup;
  onMerge: (winnerId: number, loserId: number) => void;
  onKeepBoth: () => void;
  onIgnore: () => void;
  isMutating?: boolean;
}

function confidenceTone(confidence: number): 'success' | 'warning' | 'danger' {
  if (confidence >= 90) return 'success';
  if (confidence >= 75) return 'warning';
  return 'danger';
}

function LeadCard({
  lead,
  selected,
  disabled,
  onSelect,
  side,
}: {
  lead: DuplicateGroup['record_a'] | DuplicateGroup['record_b'];
  selected: boolean;
  disabled?: boolean;
  onSelect: () => void;
  side: 'A' | 'B';
}) {
  if (!lead) return null;
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      className={cn(
        'flex w-full flex-col gap-2 rounded-lg border p-4 text-left transition-all',
        selected
          ? 'border-brand-500 bg-brand-50/50 ring-2 ring-brand-200 dark:bg-brand-500/10 dark:ring-brand-500/30'
          : 'border-border-subtle bg-surface hover:border-border-strong',
        disabled && 'cursor-not-allowed opacity-60',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Badge tone={selected ? 'brand' : 'neutral'} size="sm">
            Record {side}
          </Badge>
          {selected && (
            <Badge tone="success" size="sm" dot>
              Keep this one
            </Badge>
          )}
        </div>
      </div>
      <div className="font-medium text-fg">{lead.contact_name || '(no contact name)'}</div>
      {lead.job_title ? <div className="text-[12.5px] text-muted">{lead.job_title}</div> : null}
      <div className="flex items-center gap-1.5 text-[12.5px] text-subtle">
        <Building2 className="size-3.5" />
        {lead.company_name}
      </div>
      {lead.email ? (
        <div className="flex items-center gap-1.5 text-[12.5px] text-subtle">
          <Mail className="size-3.5" />
          {lead.email}
        </div>
      ) : null}
      {(lead.city || lead.state) && (
        <div className="text-[12.5px] text-subtle">
          {[lead.city, lead.state].filter(Boolean).join(', ')}
        </div>
      )}
      <div className="flex flex-wrap gap-1.5 pt-1 text-[11.5px] text-subtle">
        {lead.source ? <Badge tone="neutral" size="sm">{lead.source}</Badge> : null}
        {lead.source_file ? (
          <Badge tone="neutral" size="sm">
            {lead.source_file}
            {lead.source_row_number ? `:${lead.source_row_number}` : ''}
          </Badge>
        ) : null}
      </div>
    </button>
  );
}

/** Pairwise duplicate review card: click a record to mark it as winner. */
export function DuplicateReviewCard({ group, onMerge, onKeepBoth, onIgnore, isMutating }: Props) {
  const a = group.record_a;
  const b = group.record_b;
  const [winner, setWinner] = useState<'A' | 'B' | null>(null);

  const handleMerge = () => {
    if (!winner || !a || !b) return;
    const winnerId = winner === 'A' ? a.id : b.id;
    const loserId = winner === 'A' ? b.id : a.id;
    onMerge(winnerId, loserId);
  };

  return (
    <Card className="p-5">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={confidenceTone(group.confidence)}>{group.confidence}% match</Badge>
            <h3 className="font-medium text-fg">{group.reason_label}</h3>
          </div>
          <p className="text-[12px] text-subtle">
            Detected {formatDate(group.created_at)} · click the record to keep, then merge.
          </p>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <LeadCard
          lead={a}
          side="A"
          selected={winner === 'A'}
          disabled={isMutating}
          onSelect={() => setWinner('A')}
        />
        <LeadCard
          lead={b}
          side="B"
          selected={winner === 'B'}
          disabled={isMutating}
          onSelect={() => setWinner('B')}
        />
      </div>

      <footer className="mt-4 flex flex-wrap items-center justify-end gap-2 border-t border-border-subtle pt-4">
        <Button
          variant="outline"
          size="sm"
          onClick={onIgnore}
          isLoading={isMutating}
          leadingIcon={<X className="size-3.5" />}
        >
          Ignore
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onKeepBoth}
          isLoading={isMutating}
          leadingIcon={<ShieldCheck className="size-3.5" />}
        >
          Keep both
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={handleMerge}
          disabled={!winner}
          isLoading={isMutating}
          leadingIcon={<MergeIcon className="size-3.5" />}
        >
          {winner ? `Merge — keep Record ${winner}` : 'Select record to keep'}
        </Button>
      </footer>
    </Card>
  );
}
