import { useEffect, useMemo, useState } from 'react';
import { Eye, Save, Trash2 } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { useCreateTemplate, useTemplateVariables, useUpdateTemplate } from '@/hooks/useCampaigns';
import { toast } from '@/lib/utils/toast';
import type { EmailTemplate } from '@/types/campaign';
import { TEMPLATE_VARIABLES } from '@/types/campaign';

interface Props {
  template?: EmailTemplate | null;
  onSaved?: (tpl: EmailTemplate) => void;
  onCancel?: () => void;
  onDelete?: () => void;
}

/**
 * Standalone template editor with live preview.
 *
 * Uses the inline preview endpoint (debounced) so users see variables
 * substituted against sample lead data as they type.
 */
export function TemplateEditor({ template, onSaved, onCancel, onDelete }: Props) {
  const isNew = !template;
  const [name, setName] = useState(template?.name ?? '');
  const [description, setDescription] = useState(template?.description ?? '');
  const [subject, setSubject] = useState(template?.subject ?? '');
  const [body, setBody] = useState(template?.body ?? '');
  const [service, setService] = useState(template?.default_recommended_service ?? '');

  const vars = useTemplateVariables();
  const create = useCreateTemplate();
  const update = useUpdateTemplate();

  // Live preview (debounced client-side using sample data so the editor feels instant).
  const sample = vars.data?.sample_lead ?? {};
  const preview = useMemo(() => {
    const sampleWithService: Record<string, string> = { ...sample, recommended_service: service || sample.recommended_service || '' };
  const render = (src: string) =>
      src.replace(/\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g, (_m, k: string) => {
        return sampleWithService[k] ?? '';
      });
    return { subject: render(subject), body: render(body) };
  }, [subject, body, service, sample]);

  const unknownInSubject = findUnknown(subject);
  const unknownInBody = findUnknown(body);
  const unknown = Array.from(new Set([...unknownInSubject, ...unknownInBody]));
  const used = Array.from(
    new Set([...findVars(subject), ...findVars(body)]),
  );

  const dirty =
    name !== (template?.name ?? '') ||
    description !== (template?.description ?? '') ||
    subject !== (template?.subject ?? '') ||
    body !== (template?.body ?? '') ||
    service !== (template?.default_recommended_service ?? '');

  const save = async () => {
    if (!name.trim() || !subject.trim() || body.trim().length < 10) {
      toast.error('Name, subject and a body (≥ 10 chars) are required.');
      return;
    }
    const payload = {
      name: name.trim(),
      description: description.trim(),
      subject: subject.trim(),
      body: body.trim(),
      default_recommended_service: service.trim(),
    };
    try {
      const saved = isNew
        ? await create.mutateAsync(payload)
        : await update.mutateAsync({ id: template!.id, patch: payload });
      toast.success('Template saved');
      onSaved?.(saved);
    } catch (err) {
      toast.error((err as Error).message || 'Save failed');
    }
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        void save();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <Card className="space-y-4 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-fg">{isNew ? 'New template' : 'Edit template'}</h3>
            <p className="text-[12px] text-subtle">Variables are substituted with lead data at send time.</p>
          </div>
          <div className="flex items-center gap-2">
            {onDelete && template && (
              <Button
                size="sm"
                variant="danger"
                leadingIcon={<Trash2 className="size-3" />}
                onClick={() => {
                  if (confirm('Delete this template?')) onDelete();
                }}
              >
                Delete
              </Button>
            )}
            {onCancel && (
              <Button size="sm" variant="ghost" onClick={onCancel}>
                Close
              </Button>
            )}
            <Button
              size="sm"
              onClick={save}
              isLoading={create.isPending || update.isPending}
              disabled={!dirty}
              leadingIcon={<Save className="size-3" />}
            >
              Save
            </Button>
          </div>
        </div>

        <div className="space-y-3">
          <Field label="Template name">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Cold intro — Logistics" />
          </Field>
          <Field label="Description (internal)">
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Used for the first-touch email in Q3 logistics push." />
          </Field>
          <Field label="Default recommended service">
            <Input
              value={service}
              onChange={(e) => setService(e.target.value)}
              placeholder="Used for {{recommended_service}} when the campaign leaves it blank"
            />
          </Field>
          <Field label="Subject line">
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Quick question for {{company_name}}"
            />
          </Field>
          <Field label="Body">
            <Textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={14}
              placeholder={`Hi {{first_name}},\n\nSaw {{company_name}} is in {{industry}} in {{city}}, {{state}} and thought {{recommended_service}} might help…`}
            />
          </Field>
        </div>

        <div>
          <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-subtle">Supported variables</p>
          <div className="flex flex-wrap gap-1">
            {TEMPLATE_VARIABLES.map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => {
                  const tag = `{{${v}}}`;
                  setBody((prev) => prev + tag);
                }}
                className={
                  'rounded-md px-1.5 py-0.5 font-mono text-[11px] ring-1 ring-inset transition-colors ' +
                  (used.includes(v)
                    ? 'bg-brand-50 text-brand-700 ring-brand-200 dark:bg-brand-500/10 dark:text-brand-200'
                    : 'bg-surface-2 text-muted ring-border-subtle hover:bg-surface-3')
                }
              >
                {`{{${v}}}`}
              </button>
            ))}
          </div>
          {unknown.length > 0 && (
            <p className="mt-2 text-[11px] text-rose-600">
              Unknown variables: {unknown.map((u) => `{{${u}}}`).join(', ')}
            </p>
          )}
        </div>
      </Card>

      <Card className="p-5">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="size-4 text-subtle" />
            <h3 className="text-sm font-semibold text-fg">Live preview</h3>
          </div>
          <Badge tone="info" size="sm">Sample lead</Badge>
        </div>
        <p className="mb-1 text-[13px] font-medium text-fg">{preview.subject || <span className="text-subtle">(no subject yet)</span>}</p>
        <div className="mt-3 whitespace-pre-wrap rounded-lg border border-border-subtle bg-surface-1 p-4 text-[13px] leading-relaxed text-fg">
          {preview.body || <span className="text-subtle">(start typing to see a preview)</span>}
        </div>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[12px] font-medium text-fg">{label}</span>
      {children}
    </label>
  );
}

function findVars(src: string): string[] {
  return Array.from(src.matchAll(/\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g)).map((m) => m[1]);
}
function findUnknown(src: string): string[] {
  const allowed = new Set<string>(TEMPLATE_VARIABLES);
  return findVars(src).filter((v) => !allowed.has(v));
}
