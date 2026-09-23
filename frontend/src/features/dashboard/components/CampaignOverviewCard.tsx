import { Megaphone, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

import { EmptyState } from '@/components/feedback/EmptyState';
import { Badge } from '@/components/ui/Badge';
import { buttonVariants } from '@/components/ui/button-variants';
import { Card, CardHeader } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { campaignStatusConfig } from '@/config/status';
import { cn } from '@/lib/utils/cn';
import { formatDate, formatPercent } from '@/lib/utils/format';
import type { CampaignSummary } from '@/types/dashboard';

export interface CampaignOverviewCardProps {
  campaigns: CampaignSummary[];
  className?: string;
}

/** Sequence-level health: audience, volume, reply rate and completion. */
export function CampaignOverviewCard({ campaigns, className }: CampaignOverviewCardProps) {
  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader
        title="Campaign Overview"
        description="Active, scheduled and finished sequences"
        action={
          <Link to="/campaigns" className={buttonVariants({ variant: 'ghost', size: 'sm' })}>
            Manage
          </Link>
        }
      />

      {campaigns.length === 0 ? (
        <div className="p-5">
          <EmptyState
            compact
            icon={<Megaphone />}
            title="No campaigns yet"
            description="Create your first sequence to start reaching qualified leads within the daily sending budget."
            action={
              <Link to="/campaigns" className={buttonVariants({ variant: 'primary', size: 'sm' })}>
                <Plus className="size-3.5" />
                New campaign
              </Link>
            }
          />
        </div>
      ) : (
        <ul className="divide-y divide-[color:var(--app-border)]">
          {campaigns.map((campaign) => {
            const status = campaignStatusConfig[campaign.status];
            return (
              <li key={campaign.id} className="px-5 py-3.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex min-w-0 items-center gap-2">
                    <p className="truncate text-[13.5px] font-medium text-fg" title={campaign.name}>
                      {campaign.name}
                    </p>
                    <Badge tone={status.tone} size="sm">
                      {status.label}
                    </Badge>
                  </div>
                  <span className="text-[11.5px] whitespace-nowrap text-subtle">
                    {campaign.status === 'completed'
                      ? `Ended ${formatDate(campaign.endsAt)}`
                      : `Ends ${formatDate(campaign.endsAt)}`}
                  </span>
                </div>

                <div className="mt-2 flex items-center gap-3">
                  <Progress
                    value={campaign.progress}
                    size="sm"
                    aria-label={`${campaign.name} progress`}
                    className="flex-1"
                  />
                  <span className="tabular w-9 text-right text-[11.5px] text-subtle">
                    {campaign.progress}%
                  </span>
                </div>

                <dl className="mt-2.5 grid grid-cols-4 gap-2 text-[11.5px]">
                  {[
                    { label: 'Audience', value: campaign.audience.toLocaleString() },
                    { label: 'Sent', value: campaign.sent.toLocaleString() },
                    { label: 'Replies', value: campaign.replies.toLocaleString() },
                    {
                      label: 'Reply rate',
                      value: campaign.sent > 0 ? formatPercent(campaign.replyRate) : '—',
                    },
                  ].map((stat) => (
                    <div key={stat.label}>
                      <dt className="text-subtle">{stat.label}</dt>
                      <dd className="tabular font-medium text-fg">{stat.value}</dd>
                    </div>
                  ))}
                </dl>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
