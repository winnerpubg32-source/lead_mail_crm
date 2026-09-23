import { Link } from 'react-router-dom';
import { Megaphone, Users } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { SortableHeader } from '@/components/ui/SortableHeader';
import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import { campaignStatusConfig } from '@/config/status';
import type { SortDirection } from '@/hooks/useListQuery';
import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';
import type { Campaign } from '@/types/campaign';

interface Props {
  campaigns: Campaign[];
  ordering: string;
  onToggleOrdering: (field: string) => void;
}

export function CampaignTable({ campaigns, ordering, onToggleOrdering }: Props) {
  const directionFor = (field: string): SortDirection | null =>
    ordering === field ? 'asc' : ordering === `-${field}` ? 'desc' : null;

  return (
    <TableWrapper>
      <Table>
        <THead>
          <TR>
            <SortableHeader
              label="Campaign"
              field="name"
              direction={directionFor('name')}
              onToggle={onToggleOrdering}
              className="min-w-[240px]"
            />
            <TH className="min-w-[200px]">Audience</TH>
            <SortableHeader
              label="Eligible Leads"
              field="eligible_count"
              direction={directionFor('eligible_count')}
              onToggle={onToggleOrdering}
              align="right"
            />
            <SortableHeader
              label="Daily Limit"
              field="daily_limit"
              direction={directionFor('daily_limit')}
              onToggle={onToggleOrdering}
              align="right"
            />
            <SortableHeader
              label="Sent"
              field="sent_count"
              direction={directionFor('sent_count')}
              onToggle={onToggleOrdering}
              align="right"
            />
            <SortableHeader
              label="Replies"
              field="reply_count"
              direction={directionFor('reply_count')}
              onToggle={onToggleOrdering}
              align="right"
            />
            <SortableHeader
              label="Status"
              field="status"
              direction={directionFor('status')}
              onToggle={onToggleOrdering}
            />
          </TR>
        </THead>
        <TBody>
          {campaigns.map((c) => {
            const status = campaignStatusConfig[c.status];
            const size = c.audience_size ?? c.eligible_count;
            return (
              <TR key={c.id} className="group/row hover:bg-surface-2">
                <TD>
                  <Link to={`/campaigns/${c.id}`} className="flex items-start gap-2.5">
                    <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
                      <Megaphone className="size-3.5" />
                    </span>
                    <div className="min-w-0">
                      <p className="truncate font-medium text-fg" title={c.name}>
                        {c.name}
                      </p>
                      <p className="truncate text-[11.5px] text-subtle">
                        {c.description || (c.template_name ? `Template: ${c.template_name}` : 'No description')}
                      </p>
                    </div>
                  </Link>
                </TD>
                <TD>
                  <AudienceChips campaign={c} />
                </TD>
                <TD className="text-right tabular text-[13px] text-muted">{formatNumber(size)}</TD>
                <TD className="text-right tabular text-[13px] text-muted">{formatNumber(c.daily_limit)}/day</TD>
                <TD className="text-right tabular text-[13px] text-muted">
                  {formatNumber(c.sent_count)}
                  {c.eligible_count > 0 && (
                    <div className="mt-1 w-24">
                      <Progress value={c.progress_pct} />
                    </div>
                  )}
                </TD>
                <TD className="text-right tabular text-[13px] text-muted">{formatNumber(c.reply_count)}</TD>
                <TD>
                  <Badge tone={status.tone} size="sm" dot>
                    {status.label}
                  </Badge>
                </TD>
              </TR>
            );
          })}
        </TBody>
      </Table>
    </TableWrapper>
  );
}

function AudienceChips({ campaign }: { campaign: Campaign }) {
  const chips: string[] = [];
  if (campaign.industry) chips.push(campaign.industry);
  if (campaign.location) chips.push(campaign.location);
  if (campaign.minimum_lead_score) chips.push(`Score ≥ ${campaign.minimum_lead_score}`);
  if (chips.length === 0) {
    return (
      <span className="inline-flex items-center gap-1 text-[12px] text-subtle">
        <Users className="size-3" /> All eligible leads
      </span>
    );
  }
  return (
    <div className="flex flex-wrap gap-1">
      {chips.map((c) => (
        <span
          key={c}
          className={cn(
            'inline-flex rounded-md bg-surface-2 px-1.5 py-0.5 text-[11px] text-muted ring-1 ring-inset ring-border-subtle',
          )}
        >
          {c}
        </span>
      ))}
    </div>
  );
}
