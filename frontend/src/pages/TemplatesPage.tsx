import { useState } from 'react';
import { FileText, LayoutTemplate, Pencil, Plus, Trash2 } from 'lucide-react';

import { EmptyState } from '@/components/feedback/EmptyState';
import { ErrorState } from '@/components/feedback/ErrorState';
import { LoadingState } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { TemplateEditor } from '@/features/campaigns/components/TemplateEditor';
import { useDeleteTemplate, useTemplates } from '@/hooks/useCampaigns';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { toast } from '@/lib/utils/toast';
import type { EmailTemplate } from '@/types/campaign';

export function TemplatesPage() {
  useDocumentTitle('Templates');
  const { data: templates, isPending, isError, error, refetch } = useTemplates();
  const del = useDeleteTemplate();

  const [editing, setEditing] = useState<EmailTemplate | null>(null);
  const [creating, setCreating] = useState(false);

  if (isPending) {
    return (
      <div>
        <PageHeader eyebrow="Toolkit" title="Email templates" description="" />
        <LoadingState label="Loading templates…" />
      </div>
    );
  }

  if (isError) {
    return (
      <div>
        <PageHeader eyebrow="Toolkit" title="Email templates" description="" />
        <ErrorState title="Could not load templates" details={error instanceof Error ? error.message : undefined} onRetry={() => void refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Toolkit"
        title="Email templates"
        description="Reusable outreach copy with {{variable}} placeholders. Every campaign picks one template."
        actions={
          <>
            <Button
              size="sm"
              onClick={() => {
                setEditing(null);
                setCreating(true);
              }}
              leadingIcon={<Plus className="size-3.5" />}
            >
              New template
            </Button>
          </>
        }
      />

      {templates && templates.length === 0 && !creating ? (
        <Card>
          <EmptyState
            icon={<LayoutTemplate />}
            title="No templates yet"
            description="Create your first email template with subject, body and {{variables}}. Try the live preview against sample lead data."
            action={
              <Button
                size="sm"
                onClick={() => setCreating(true)}
                leadingIcon={<Plus className="size-3.5" />}
              >
                New template
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {templates?.map((tpl: import('@/types/campaign').EmailTemplate) => (
            <Card key={tpl.id} className="flex flex-col p-4">
              <div className="mb-2 flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <FileText className="size-4 text-brand-500" />
                    <h3 className="truncate text-sm font-semibold text-fg">{tpl.name}</h3>
                  </div>
                  {tpl.description && <p className="mt-0.5 line-clamp-2 text-[12px] text-subtle">{tpl.description}</p>}
                </div>
              </div>
              <p className="line-clamp-1 font-mono text-[11.5px] text-muted">{tpl.subject}</p>
              <p className="mt-2 line-clamp-3 whitespace-pre-wrap text-[12px] text-muted">{tpl.body}</p>
              <div className="mt-3 flex flex-wrap gap-1">
                {tpl.used_variables.slice(0, 6).map((v) => (
                  <Badge key={v} tone="neutral" size="sm">
                    {`{{${v}}}`}
                  </Badge>
                ))}
                {tpl.unknown_variables.length > 0 && (
                  <Badge tone="danger" size="sm">{tpl.unknown_variables.length} unknown</Badge>
                )}
              </div>
              <div className="mt-4 flex items-center justify-end gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  leadingIcon={<Trash2 className="size-3" />}
                  onClick={() => {
                    if (confirm(`Delete template "${tpl.name}"?`)) {
                      del.mutate(tpl.id, {
                        onSuccess: () => toast.success('Template deleted'),
                        onError: (err: Error) => toast.error(err.message || 'Delete failed'),
                      });
                    }
                  }}
                >
                  Delete
                </Button>
                <Button size="sm" leadingIcon={<Pencil className="size-3" />} onClick={() => setEditing(tpl)}>
                  Edit
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {(creating || editing) && (
        <div className="fixed inset-0 z-40 overflow-y-auto bg-black/40 p-4 backdrop-blur-sm">
          <div className="mx-auto max-w-5xl py-8">
            <TemplateEditor
              template={editing}
              onSaved={() => {
                setCreating(false);
                setEditing(null);
                toast.success(creating ? 'Template created' : 'Template saved');
                void refetch();
              }}
              onCancel={() => {
                setCreating(false);
                setEditing(null);
              }}
              onDelete={() => {
                if (editing) {
                  del.mutate(editing.id, {
                    onSuccess: () => {
                      toast.success('Template deleted');
                      setEditing(null);
                      void refetch();
                    },
                  });
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
