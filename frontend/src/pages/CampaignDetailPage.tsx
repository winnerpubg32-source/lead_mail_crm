import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Megaphone, Play, Pause, StopCircle, Pencil, Users } from 'lucide-react';

import { ErrorState } from '@/components/feedback/ErrorState';
import { LoadingState } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { CampaignWizard } from '@/features/campaigns/components/CampaignWizard';
import {
  useCampaign,
  useCampaignStatus,
  usePrepareCampaign,
} from '@/hooks/useCampaigns';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { campaignStatusConfig } from '@/config/status';
import { formatDateTime, formatNumber } from '@/lib/utils/format';
import { toast } from '@/lib/utils/toast';

export function CampaignDetailPage() {
  const { id } = useParams();
  const cid = Number(id);
  useDocumentTitle(`Campaign #${id}`);
  const { data: campaign, isPending, isError, error, refetch } = useCampaign(cid);
  const setStatus = useCampaignStatus();
  const prepare = usePrepareCampaign();
  const [editing, setEditing] = useState(false);

  if (isPending) {
    return (
      <div>
        <PageHeader eyebrow="Outreach" title="Campaign detail" description="" />
        <LoadingState label="Loading campaign…" />
      </div>
    );
  }
  if (isError || !campaign) {
    return (
      <div>
        <PageHeader eyebrow="Outreach" title="Campaign detail" description="" />
        <ErrorState
          title="Could not load campaign"
          details={error instanceof Error ? error.message : undefined}
          onRetry={() => void refetch()}
        />
      </div>
    );
  }

  const status = campaignStatusConfig[campaign.status];
  const size = campaign.eligible_count;

  const doStatus = async (next: typeof campaign.status) => {
    try {
      await setStatus.mutateAsync({ id: campaign.id, status: next });
      toast.success(`Campaign ${next.toLowerCase()}`);
    } catch (err) {
      toast.error((err as Error).message || 'Could not update status');
    }
  };

  const doPrepare = async () => {
    try {
      const res = await prepare.mutateAsync(campaign.id);
      toast.success(res.message);
    } catch (err) {
      toast.error((err as Error).message || 'Prepare failed');
    }
  };

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Outreach"
        title={campaign.name}
        description={campaign.description || 'Campaign detail view.'}
        actions={
          <>
            <Link to="/campaigns">
              <Button variant="ghost" size="sm" leadingIcon={<ArrowLeft className="size-3.5" />}>
                All campaigns
              </Button>
            </Link>
            <Button variant="outline" size="sm" leadingIcon={<Pencil className="size-3.5" />} onClick={() => setEditing(true)}>
              Edit
            </Button>
            {campaign.status === 'DRAFT' && (
              <Button size="sm" onClick={doPrepare} isLoading={prepare.isPending} leadingIcon={<Play className="size-3.5" />}>
                Prepare launch
              </Button>
            )}
            {campaign.status === 'READY' && (
              <Button size="sm" onClick={() => doStatus('RUNNING')} isLoading={setStatus.isPending} leadingIcon={<Play className="size-3.5" />}>
                Launch (dry-run)
              </Button>
            )}
            {campaign.status === 'RUNNING' && (
              <Button size="sm" variant="outline" onClick={() => doStatus('PAUSED')} leadingIcon={<Pause className="size-3.5" />}>
                Pause
              </Button>
            )}
            {campaign.status === 'PAUSED' && (
              <Button size="sm" onClick={() => doStatus('RUNNING')} leadingIcon={<Play className="size-3.5" />}>
                Resume
              </Button>
            )}
            {(campaign.status === 'READY' || campaign.status === 'RUNNING' || campaign.status === 'PAUSED') && (
              <Button size="sm" variant="danger" onClick={() => doStatus('CANCELLED')} leadingIcon={<StopCircle className="size-3.5" />}>
                Cancel
              </Button>
            )}
            {campaign.status === 'RUNNING' && (
              <Button size="sm" variant="outline" onClick={() => doStatus('COMPLETED')}>
                Mark complete
              </Button>
            )}
          </>
        }
      />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Megaphone className="size-5 text-brand-500" />
            <h2 className="text-base font-semibold text-fg">{campaign.name}</h2>
            <Badge tone={status.tone} size="sm" dot>{status.label}</Badge>
            <Badge tone="warning" size="sm">Phase 6 · no emails sent</Badge>
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Stat label="Eligible leads" value={formatNumber(size)} icon={<Users className="size-4" />} />
            <Stat label="Sent" value={formatNumber(campaign.sent_count)} />
            <Stat label="Replies" value={formatNumber(campaign.reply_count)} />
            <Stat label="Meetings" value={formatNumber(campaign.meeting_count)} />
          </div>

          {size > 0 && (
            <div className="mt-4">
              <div className="mb-1 flex items-center justify-between text-[12px] text-muted">
                <span>Progress</span>
                <span className="tabular">{campaign.progress_pct}%</span>
              </div>
              <Progress value={campaign.progress_pct} />
            </div>
          )}

          {campaign.launch_errors.length > 0 && campaign.status !== 'RUNNING' && (
            <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-[12.5px] text-rose-800 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
              <strong>Not ready to launch:</strong>
              <ul className="mt-1 list-disc pl-5">
                {campaign.launch_errors.map((e) => <li key={e}>{e}</li>)}
              </ul>
            </div>
          )}

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <DetailList
              title="Audience"
              items={[
                ['Industry', campaign.industry || 'Any'],
                ['Sub-industry', campaign.sub_industry || 'Any'],
                ['Location', campaign.location || 'Any'],
                ['Min. lead score', String(campaign.minimum_lead_score || 0)],
              ]}
            />
            <DetailList
              title="Delivery"
              items={[
                ['Daily limit', `${formatNumber(campaign.daily_limit)} / day`],
                ['Recommended service', campaign.recommended_service || '—'],
                ['Scheduled start', campaign.scheduled_start_at ? formatDateTime(campaign.scheduled_start_at) : 'As soon as approved'],
                ['Scheduled end', campaign.scheduled_end_at ? formatDateTime(campaign.scheduled_end_at) : '—'],
              ]}
            />
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="mb-2 text-sm font-semibold text-fg">Template</h3>
          {campaign.template_detail ? (
            <div>
              <p className="text-[13px] font-medium text-fg">{campaign.template_detail.name}</p>
              {campaign.template_detail.description && (
                <p className="text-[12px] text-subtle">{campaign.template_detail.description}</p>
              )}
              <div className="mt-3 rounded-lg border border-border-subtle bg-surface-1 p-3">
                <p className="text-[12px] font-medium text-fg">{campaign.template_detail.subject}</p>
                <p className="mt-2 line-clamp-6 whitespace-pre-wrap text-[12px] text-muted">
                  {campaign.template_detail.body}
                </p>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {campaign.template_detail.used_variables.map((v) => (
                  <Badge key={v} tone="neutral" size="sm">{`{{${v}}}`}</Badge>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-[12.5px] text-subtle">
              No template attached. Use Edit to pick one before launching.
            </p>
          )}
        </Card>
      </div>

      {editing && (
        <CampaignWizard
          existing={campaign}
          onClose={() => setEditing(false)}
        />
      )}
    </div>
  );
}

function Stat({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border-subtle bg-surface-1 p-3">
      <div className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-subtle">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-xl font-semibold tabular text-fg">{value}</p>
    </div>
  );
}

function DetailList({ title, items }: { title: string; items: Array<[string, string]> }) {
  return (
    <div>
      <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-subtle">{title}</p>
      <dl className="space-y-1.5">
        {items.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3 text-[13px]">
            <dt className="text-muted">{k}</dt>
            <dd className="text-right font-medium text-fg">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
