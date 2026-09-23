import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { scoreClassificationConfig } from '@/config/status';
import { cn } from '@/lib/utils/cn';
import type { ScoreBreakdown as ScoreBreakdownType } from '@/types/lead';

interface Props {
  score: number;
  classificationCode: 'HOT' | 'WARM' | 'COLD' | 'UNQUALIFIED';
  breakdown?: ScoreBreakdownType;
}

const labelMap: Record<string, string> = {
  valid_email: 'Valid e-mail',
  website: 'Has website',
  contact: 'Named contact',
  phone: 'Phone number',
  industry: 'Industry known',
  location: 'Location (city/state)',
  website_accessible: 'Website accessible',
  invalid_email: 'Invalid e-mail',
  suppressed: 'Suppressed',
  unsubscribed: 'Unsubscribed',
  bounced: 'Bounced',
};

export function ScoreBreakdown({ score, classificationCode, breakdown }: Props) {
  const cfg = scoreClassificationConfig[classificationCode];
  const components = breakdown?.components ?? {};
  const positives = Object.entries(components).filter(([, v]) => v > 0);
  const negatives = Object.entries(components).filter(([, v]) => v < 0);

  return (
    <Card className="p-5">
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <h3 className="text-sm font-semibold text-fg">Lead Score</h3>
          <p className="text-[12px] text-subtle">Configurable point-based qualification.</p>
        </div>
        <Badge tone={cfg.tone} size="sm">
          {cfg.label}
        </Badge>
      </div>

      <div className="mb-4 flex items-end gap-3">
        <span
          className={cn(
            'tabular text-4xl font-bold tracking-tight',
            classificationCode === 'HOT' && 'text-emerald-600 dark:text-emerald-400',
            classificationCode === 'WARM' && 'text-amber-600 dark:text-amber-400',
            classificationCode === 'COLD' && 'text-sky-600 dark:text-sky-400',
            classificationCode === 'UNQUALIFIED' && 'text-muted',
          )}
        >
          {score}
        </span>
        <span className="text-[12px] text-subtle">/ 100</span>
      </div>

      <div className="space-y-2">
        {positives.map(([key, points]) => (
          <div key={key} className="flex items-center justify-between text-[12.5px]">
            <span className="text-muted">{labelMap[key] ?? key.replace(/_/g, ' ')}</span>
            <span className="tabular font-medium text-emerald-600">+{points}</span>
          </div>
        ))}
        {negatives.map(([key, points]) => (
          <div key={key} className="flex items-center justify-between text-[12.5px]">
            <span className="text-muted">{labelMap[key] ?? key.replace(/_/g, ' ')}</span>
            <span className="tabular font-medium text-rose-600">{points}</span>
          </div>
        ))}
        {positives.length === 0 && negatives.length === 0 && (
          <p className="text-[12px] text-subtle">No signals yet.</p>
        )}
      </div>
    </Card>
  );
}
