import { Link } from 'react-router-dom';
import { Send } from 'lucide-react';

import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/feedback/EmptyState';
import { buttonVariants } from '@/components/ui/button-variants';
import { outreachEventConfig } from '@/config/status';
import { cn } from '@/lib/utils/cn';
import { formatRelativeTime } from '@/lib/utils/format';
import type { OutreachEvent } from '@/types/dashboard';

export interface TodaysOutreachCardProps {
  events: OutreachEvent[];
  className?: string;
}

/** Live feed of today's activity: queued, sent, replies, bounces, meetings. */
export function TodaysOutreachCard({ events, className }: TodaysOutreachCardProps) {
  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader
        title="Today’s Outreach"
        description="Everything scheduled and delivered since 00:00"
        action={
          <Badge tone="neutral" size="sm">
            {events.length} events
          </Badge>
        }
      />

      {events.length === 0 ? (
        <div className="p-5">
          <EmptyState
            compact
            icon={<Send />}
            title="No outreach activity yet today"
            description="Once a campaign starts sending, every queued and delivered e-mail appears here in real time."
            action={
              <Link to="/campaigns" className={buttonVariants({ variant: 'outline', size: 'sm' })}>
                Review campaigns
              </Link>
            }
          />
        </div>
      ) : (
        <ul className="scrollbar-thin max-h-[420px] divide-y divide-[color:var(--app-border)] overflow-y-auto">
          {events.map((event) => {
            const presentation = outreachEventConfig[event.type];
            const Icon = presentation.icon;
            return (
              <li key={event.id} className="flex items-start gap-3 px-5 py-3.5">
                <span
                  className={cn(
                    'mt-0.5 grid size-7 shrink-0 place-items-center rounded-lg',
                    event.type === 'reply' || event.type === 'meeting'
                      ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300'
                      : event.type === 'bounce'
                        ? 'bg-rose-50 text-rose-600 dark:bg-rose-500/15 dark:text-rose-300'
                        : 'bg-surface-3 text-muted',
                  )}
                >
                  <Icon className="size-3.5" />
                </span>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <p className="truncate text-[13.5px] font-medium text-fg">{event.companyName}</p>
                    <Badge tone={presentation.tone} size="sm">
                      {presentation.label}
                    </Badge>
                  </div>
                  <p className="mt-0.5 truncate text-[12.5px] text-muted" title={event.subject}>
                    {event.subject}
                  </p>
                  <p className="mt-1 flex flex-wrap items-center gap-x-2 text-[11.5px] text-subtle">
                    <span className="truncate">{event.contactName}</span>
                    <span aria-hidden="true">·</span>
                    <span className="truncate">{event.campaignName}</span>
                  </p>
                </div>

                <time
                  dateTime={event.occurredAt}
                  className="shrink-0 text-[11.5px] whitespace-nowrap text-subtle"
                >
                  {formatRelativeTime(event.occurredAt)}
                </time>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
