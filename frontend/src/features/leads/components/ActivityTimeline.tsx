import { Card } from '@/components/ui/Card';
import { ACTIVITY_ICONS } from '@/config/status';
import { formatDateTime, formatRelativeTime } from '@/lib/utils/format';
import type { LeadActivity } from '@/types/lead';

interface Props {
  activities?: LeadActivity[];
}

export function ActivityTimeline({ activities }: Props) {
  if (!activities || activities.length === 0) {
    return (
      <Card className="p-5">
        <h3 className="mb-3 text-sm font-semibold text-fg">Activity</h3>
        <p className="text-[12.5px] text-subtle">No activity recorded for this lead yet.</p>
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <h3 className="mb-4 text-sm font-semibold text-fg">Activity timeline</h3>
      <ol className="relative ml-2 space-y-4 border-l border-border-subtle pl-5">
        {activities.map((event) => (
          <li key={event.id} className="relative">
            <span
              className="absolute -left-[27px] top-0 grid size-5 place-items-center rounded-full bg-surface-2 text-[11px] ring-4 ring-surface"
              aria-hidden
            >
              {ACTIVITY_ICONS[event.activity_type] ?? '•'}
            </span>
            <p className="text-[13px] font-medium text-fg">{event.title}</p>
            {event.description && (
              <p className="mt-0.5 text-[12px] text-muted">{event.description}</p>
            )}
            <p
              className="mt-1 text-[11px] text-subtle"
              title={formatDateTime(event.created_at)}
            >
              {formatRelativeTime(event.created_at)}
              {event.actor ? ` · ${event.actor}` : ''}
            </p>
          </li>
        ))}
      </ol>
    </Card>
  );
}
