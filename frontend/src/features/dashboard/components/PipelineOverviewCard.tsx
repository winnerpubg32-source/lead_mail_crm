import { TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Card, CardHeader } from '@/components/ui/Card';
import { buttonVariants } from '@/components/ui/button-variants';
import { pipelineRamp } from '@/config/chart-colors';
import { cn } from '@/lib/utils/cn';
import { formatCompactNumber, formatCurrency } from '@/lib/utils/format';
import type { PipelineStage } from '@/types/dashboard';

export interface PipelineOverviewCardProps {
  stages: PipelineStage[];
  className?: string;
}

/**
 * Funnel view of the pipeline.
 *
 * Bar widths are relative to the first stage so the drop-off is visible at a
 * glance; values are weighted USD from the CRM module (later phase).
 */
export function PipelineOverviewCard({ stages, className }: PipelineOverviewCardProps) {
  const maxCount = Math.max(1, ...stages.map((stage) => stage.count));
  const totalValue = stages.reduce((sum, stage) => sum + stage.value, 0);

  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader
        title="Pipeline Overview"
        description="From first touch to closed won"
        action={
          <Link to="/crm" className={buttonVariants({ variant: 'ghost', size: 'sm' })}>
            Open CRM
          </Link>
        }
      />

      <div className="flex-1 space-y-3.5 px-5 py-4">
        {stages.map((stage, index) => {
          const width = Math.max(6, (stage.count / maxCount) * 100);
          const color = pipelineRamp[index % pipelineRamp.length];
          return (
            <div key={stage.id}>
              <div className="flex items-center justify-between gap-3 text-[12.5px]">
                <span className="flex items-center gap-2">
                  <span
                    aria-hidden="true"
                    className="size-2 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="font-medium text-fg">{stage.label}</span>
                </span>
                <span className="tabular flex items-center gap-3 text-muted">
                  <span>{stage.count.toLocaleString()}</span>
                  <span className="w-14 text-right text-subtle">${formatCompactNumber(stage.value)}</span>
                </span>
              </div>
              <div className="mt-1.5 h-6 w-full overflow-hidden rounded-md bg-surface-2">
                <div
                  className="flex h-full items-center justify-end rounded-md pr-2 transition-[width] duration-700"
                  style={{ width: `${width}%`, backgroundColor: color }}
                >
                  {width > 18 ? (
                    <span className="text-[11px] font-medium text-white/90">{stage.conversion}%</span>
                  ) : null}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between border-t border-border-subtle px-5 py-3 text-[12px]">
        <span className="flex items-center gap-1.5 text-subtle">
          <TrendingUp className="size-3.5" />
          Open + won value
        </span>
        <span className="tabular font-medium text-fg">{formatCurrency(totalValue)}</span>
      </div>
    </Card>
  );
}
