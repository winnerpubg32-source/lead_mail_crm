import { ArrowLeft, Calendar, RefreshCw } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/feedback/ErrorState';
import { LoadingState } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { ActivityTimeline } from '@/features/leads/components/ActivityTimeline';
import { ContactCard } from '@/features/leads/components/ContactCard';
import { NotesPanel } from '@/features/leads/components/NotesPanel';
import { ScoreBreakdown } from '@/features/leads/components/ScoreBreakdown';
import { useAddLeadNote, useLead, useRescoreLead } from '@/hooks/useLeads';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { formatDateTime } from '@/lib/utils/format';
import { toast } from '@/lib/utils/toast';
import { scoreClassification } from '@/config/status';

export function LeadDetailPage() {
  const { id } = useParams();
  const leadId = Number(id);
  useDocumentTitle(`Lead #${id}`);

  const { data: lead, isPending, isError, error, refetch, isFetching } = useLead(leadId);
  const addNote = useAddLeadNote();
  const rescore = useRescoreLead();

  if (isPending) {
    return (
      <div>
        <PageHeader eyebrow="Lead database" title="Lead detail" description="" />
        <LoadingState label="Loading lead…" />
      </div>
    );
  }

  if (isError || !lead) {
    return (
      <div>
        <PageHeader eyebrow="Lead database" title="Lead detail" description="" />
        <ErrorState
          title="Could not load lead"
          details={error instanceof Error ? error.message : undefined}
          onRetry={() => void refetch()}
        />
      </div>
    );
  }

  const code = scoreClassification(lead.score_classification, lead.lead_score);

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Lead database"
        title={lead.company_name || `Lead #${lead.id}`}
        description={lead.contact_name || lead.industry || 'Detailed view of the prospect.'}
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void refetch()}
              isLoading={isFetching}
              leadingIcon={<RefreshCw className="size-3.5" />}
            >
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                rescore.mutate(lead.id, {
                  onSuccess: () => toast.success('Score recomputed'),
                  onError: (err: Error) => toast.error(err.message || 'Failed to rescore'),
                })
              }
              isLoading={rescore.isPending}
            >
              Recompute score
            </Button>
            <Link to="/leads">
              <Button variant="ghost" size="sm" leadingIcon={<ArrowLeft className="size-3.5" />}>
                Back to leads
              </Button>
            </Link>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <ContactCard lead={lead} />

          <Card className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-fg">Campaign history</h3>
              <Badge tone="neutral" size="sm">Coming soon</Badge>
            </div>
            <p className="text-[12.5px] text-subtle">
              Once campaigns ship, every outreach sequence this lead is part of will appear here. The bulk action already records assignments in the activity timeline for future-proofing.
            </p>
            <div className="mt-4 flex items-center gap-2 rounded-lg border border-dashed border-border-subtle p-4 text-[12px] text-subtle">
              <Calendar className="size-4" />
              No campaigns yet.
            </div>
          </Card>

          <NotesPanel
            notes={lead.notes}
            onAdd={(body) =>
              addNote.mutate(
                { id: lead.id, body },
                {
                  onSuccess: () => toast.success('Note added'),
                  onError: (err: Error) => toast.error(err.message || 'Failed to add note'),
                },
              )
            }
            isAdding={addNote.isPending}
          />
        </div>

        <div className="space-y-5">
          <ScoreBreakdown
            score={lead.lead_score}
            classificationCode={code}
            breakdown={lead.score_breakdown}
          />

          <Card className="p-5">
            <h3 className="mb-2 text-sm font-semibold text-fg">Record details</h3>
            <dl className="space-y-1.5 text-[12.5px] text-muted">
              <DetailRow label="Lead ID">#{lead.id}</DetailRow>
              <DetailRow label="Source">{lead.source || '—'}</DetailRow>
              <DetailRow label="Source file">{lead.source_file || '—'}</DetailRow>
              <DetailRow label="Source row">{lead.source_row_number ?? '—'}</DetailRow>
              <DetailRow label="Created">{formatDateTime(lead.created_at)}</DetailRow>
              <DetailRow label="Last updated">{formatDateTime(lead.updated_at)}</DetailRow>
            </dl>
          </Card>

          <ActivityTimeline activities={lead.activities} />
        </div>
      </div>
    </div>
  );
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-subtle">{label}</dt>
      <dd className="text-right font-mono text-[12px] text-fg">{children}</dd>
    </div>
  );
}
