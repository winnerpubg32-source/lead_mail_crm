import { useMemo, useState } from 'react';
import { Check, ChevronLeft, ChevronRight, Megaphone, Sparkles } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { useCreateCampaign, usePrepareCampaign, useTemplates, useUpdateCampaign } from '@/hooks/useCampaigns';
import { toast } from '@/lib/utils/toast';
import type { Campaign, CampaignWizardDraft, EmailTemplate } from '@/types/campaign';

interface Props {
  existing?: Campaign | null;
  onClose: () => void;
  onCreated?: (campaign: Campaign) => void;
}

const STEPS = [
  { id: 1, label: 'Audience', description: 'Who should this campaign reach?' },
  { id: 2, label: 'Service', description: 'What service are you offering?' },
  { id: 3, label: 'Template', description: 'Pick an email template.' },
  { id: 4, label: 'Schedule', description: 'Daily volume + timing.' },
  { id: 5, label: 'Review', description: 'Double-check and launch.' },
] as const;

const DEFAULTS: CampaignWizardDraft = {
  name: '',
  description: '',
  industry: '',
  sub_industry: '',
  location: '',
  minimum_lead_score: 0,
  recommended_service: '',
  template: null,
  daily_limit: 90,
  scheduled_start_at: null,
  scheduled_end_at: null,
};

export function CampaignWizard({ existing, onClose, onCreated }: Props) {
  const isEdit = Boolean(existing);
  const [step, setStep] = useState(1);
  const [draft, setDraft] = useState<CampaignWizardDraft>(() =>
    existing
      ? {
          name: existing.name,
          description: existing.description,
          industry: existing.industry,
          sub_industry: existing.sub_industry,
          location: existing.location,
          minimum_lead_score: existing.minimum_lead_score,
          recommended_service: existing.recommended_service,
          template: existing.template,
          daily_limit: existing.daily_limit,
          scheduled_start_at: existing.scheduled_start_at,
          scheduled_end_at: existing.scheduled_end_at,
        }
      : DEFAULTS,
  );
  const templates = useTemplates();
  const create = useCreateCampaign();
  const update = useUpdateCampaign();
  const prepare = usePrepareCampaign();

  const set = <K extends keyof CampaignWizardDraft>(key: K, value: CampaignWizardDraft[K]) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  };

  const persist = async () => {
    if (isEdit && existing) {
      return update.mutateAsync({ id: existing.id, patch: draft });
    }
    return create.mutateAsync(draft);
  };

  const advance = async () => {
    if (step === 4) {
      // Persist before review.
      try {
        const saved = await persist();
        onCreated?.(saved);
        setStep(5);
      } catch (err) {
        toast.error((err as Error).message || 'Could not save campaign');
      }
      return;
    }
    setStep((s) => Math.min(5, s + 1));
  };

  const back = () => setStep((s) => Math.max(1, s - 1));

  const launch = async () => {
    try {
      let campaign: Campaign;
      if (isEdit && existing) {
        await update.mutateAsync({ id: existing.id, patch: draft });
        campaign = existing;
      } else {
        campaign = await create.mutateAsync(draft);
        onCreated?.(campaign);
      }
      const result = await prepare.mutateAsync(campaign.id);
      toast.success(result.message);
      onClose();
    } catch (err) {
      toast.error((err as Error).message || 'Could not prepare campaign');
    }
  };

  const isPending = create.isPending || update.isPending || prepare.isPending;

  return (
    <div className="fixed inset-0 z-40 bg-black/40 p-4 backdrop-blur-sm">
      <Card className="mx-auto flex h-full max-h-[90vh] max-w-3xl flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-border-subtle p-5">
          <div>
            <h2 className="text-base font-semibold text-fg">
              {isEdit ? 'Edit campaign' : 'New campaign'}
            </h2>
            <p className="text-[12px] text-subtle">
              Step {step} of {STEPS.length} — {STEPS[step - 1].description}
            </p>
          </div>
          <Badge tone="warning" size="sm" dot>Phase 6 · no emails sent yet</Badge>
        </div>

        <ol className="flex items-center gap-2 border-b border-border-subtle bg-surface-1/50 px-5 py-3">
          {STEPS.map((s, idx) => {
            const done = idx + 1 < step;
            const current = idx + 1 === step;
            return (
              <li key={s.id} className="flex items-center gap-2">
                <span
                  className={
                    'grid size-6 shrink-0 place-items-center rounded-full text-[11px] font-semibold ring-1 ring-inset ' +
                    (done
                      ? 'bg-emerald-500 text-white ring-emerald-500'
                      : current
                        ? 'bg-brand-500 text-white ring-brand-500'
                        : 'bg-surface text-subtle ring-border-subtle')
                  }
                >
                  {done ? <Check className="size-3" /> : s.id}
                </span>
                <span className={current ? 'text-[12px] font-medium text-fg' : 'text-[12px] text-muted'}>
                  {s.label}
                </span>
                {idx < STEPS.length - 1 && <span className="mx-1 text-border-subtle">›</span>}
              </li>
            );
          })}
        </ol>

        <div className="flex-1 overflow-y-auto p-5">
          {step === 1 && <AudienceStep draft={draft} set={set} />}
          {step === 2 && <ServiceStep draft={draft} set={set} />}
          {step === 3 && (
            <TemplateStep
              draft={draft}
              set={set}
              templates={templates.data ?? []}
              isLoading={templates.isLoading}
            />
          )}
          {step === 4 && <ScheduleStep draft={draft} set={set} />}
          {step === 5 && (
            <ReviewStep
              draft={draft}
              existing={existing}
              templates={templates.data ?? []}
            />
          )}
        </div>

        <div className="flex items-center justify-between border-t border-border-subtle bg-surface-1/40 px-5 py-3">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={back} disabled={step === 1 || isPending}>
              <ChevronLeft className="size-3.5" /> Back
            </Button>
            {step < 5 ? (
              <Button size="sm" onClick={advance} isLoading={isPending} disabled={!draft.name.trim() && step === 1}>
                Next <ChevronRight className="size-3.5" />
              </Button>
            ) : (
              <Button size="sm" onClick={launch} isLoading={isPending} leadingIcon={<Megaphone className="size-3.5" />}>
                {isEdit ? 'Save & prepare' : 'Launch (prepare only)'}
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}

// -------- Steps --------
function AudienceStep({ draft, set }: StepProps) {
  return (
    <div className="space-y-4">
      <Field label="Campaign name" required>
        <Input value={draft.name} onChange={(e) => set('name', e.target.value)} placeholder="Q3 Logistics Outreach" autoFocus />
      </Field>
      <Field label="Description">
        <Textarea value={draft.description} onChange={(e) => set('description', e.target.value)} placeholder="What's the goal of this campaign?" rows={3} />
      </Field>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field label="Industry">
          <Input value={draft.industry} onChange={(e) => set('industry', e.target.value)} placeholder="e.g. Manufacturing" />
        </Field>
        <Field label="Sub-industry">
          <Input value={draft.sub_industry} onChange={(e) => set('sub_industry', e.target.value)} placeholder="e.g. CNC Machining" />
        </Field>
        <Field label="Location (city or state)">
          <Input value={draft.location} onChange={(e) => set('location', e.target.value)} placeholder="e.g. OH or Columbus" />
        </Field>
        <Field label={`Minimum lead score (${draft.minimum_lead_score})`}>
          <input
            type="range"
            min={0}
            max={100}
            value={draft.minimum_lead_score}
            onChange={(e) => set('minimum_lead_score', Number(e.target.value))}
            className="w-full accent-brand-600"
          />
        </Field>
      </div>
    </div>
  );
}

function ServiceStep({ draft, set }: StepProps) {
  return (
    <div className="space-y-4">
      <Field label="Recommended service" hint="Inserted as {{recommended_service}} in the template.">
        <Input
          value={draft.recommended_service}
          onChange={(e) => set('recommended_service', e.target.value)}
          placeholder="e.g. Freight Optimization Review"
          autoFocus
        />
      </Field>
      <div className="rounded-lg border border-dashed border-border-subtle bg-surface-1/60 p-4 text-[12.5px] text-subtle">
        <Sparkles className="mb-1 inline size-4 text-brand-500" /> In a later phase AI will recommend
        services based on company industry + website signals. For now just type what you want to offer.
      </div>
    </div>
  );
}

function TemplateStep({
  draft,
  set,
  templates,
  isLoading,
}: StepProps & { templates: EmailTemplate[]; isLoading: boolean }) {
  const selected = useMemo(() => templates.find((t) => t.id === draft.template) ?? null, [templates, draft.template]);
  return (
    <div className="space-y-4">
      <Field label="Email template">
        <Select
          value={draft.template ?? ''}
          onChange={(e) => set('template', e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">— Select a template —</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </Select>
        {isLoading && <p className="mt-1 text-[11px] text-subtle">Loading templates…</p>}
      </Field>
      {selected && (
        <div className="rounded-lg border border-border-subtle bg-surface-1 p-4">
          <p className="text-[11px] font-medium uppercase tracking-wide text-subtle">Preview</p>
          <p className="mt-1 text-[13px] font-medium text-fg">{selected.subject}</p>
          <p className="mt-2 whitespace-pre-wrap text-[12.5px] text-muted line-clamp-3">{selected.body}</p>
        </div>
      )}
      {!selected && !isLoading && (
        <p className="text-[12px] text-subtle">
          Pick an existing template, or create one from the <a href="/templates" className="text-brand-600 underline">Templates page</a>.
        </p>
      )}
    </div>
  );
}

function ScheduleStep({ draft, set }: StepProps) {
  return (
    <div className="space-y-4">
      <Field label={`Daily send limit (${draft.daily_limit} emails/day)`} hint="Phase 7 will enforce this against the SMTP budget.">
        <input
          type="range"
          min={10}
          max={500}
          step={10}
          value={draft.daily_limit}
          onChange={(e) => set('daily_limit', Number(e.target.value))}
          className="w-full accent-brand-600"
        />
      </Field>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field label="Scheduled start (optional)">
          <Input
            type="datetime-local"
            value={toLocalInput(draft.scheduled_start_at)}
            onChange={(e) => set('scheduled_start_at', e.target.value ? new Date(e.target.value).toISOString() : null)}
          />
        </Field>
        <Field label="Scheduled end (optional)">
          <Input
            type="datetime-local"
            value={toLocalInput(draft.scheduled_end_at)}
            onChange={(e) => set('scheduled_end_at', e.target.value ? new Date(e.target.value).toISOString() : null)}
          />
        </Field>
      </div>
    </div>
  );
}

function ReviewStep({ draft, existing, templates }: { draft: CampaignWizardDraft; existing?: Campaign | null; templates: EmailTemplate[] }) {
  const template = templates.find((t) => t.id === draft.template);
  return (
    <div className="space-y-4">
      <SummaryRow label="Name" value={draft.name} />
      <SummaryRow label="Description" value={draft.description || '—'} />
      <SummaryRow label="Audience" value={[draft.industry, draft.sub_industry, draft.location].filter(Boolean).join(' · ') || 'All eligible leads'} />
      <SummaryRow label="Minimum lead score" value={String(draft.minimum_lead_score)} />
      <SummaryRow label="Service" value={draft.recommended_service || '—'} />
      <SummaryRow label="Template" value={template?.name ?? 'None selected'} />
      <SummaryRow label="Daily limit" value={`${draft.daily_limit} emails/day`} />
      {existing?.eligible_count ? (
        <SummaryRow label="Eligible (existing)" value={String(existing.eligible_count)} />
      ) : null}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-[12.5px] text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200">
        <strong>Phase 6 — dry run:</strong> Launching validates the campaign and snapshots the audience but does <strong>not</strong> send emails. SMTP delivery ships in Phase 7.
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border-subtle pb-2 text-[13px] last:border-none">
      <span className="text-subtle">{label}</span>
      <span className="text-right font-medium text-fg">{value}</span>
    </div>
  );
}

function Field({
  label,
  required,
  hint,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-[12px] font-medium text-fg">
        {label} {required && <span className="text-rose-500">*</span>}
      </span>
      {children}
      {hint && <span className="mt-1 block text-[11px] text-subtle">{hint}</span>}
    </label>
  );
}

interface StepProps {
  draft: CampaignWizardDraft;
  set: <K extends keyof CampaignWizardDraft>(key: K, value: CampaignWizardDraft[K]) => void;
}

function toLocalInput(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
