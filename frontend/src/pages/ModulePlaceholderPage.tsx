import { CheckCircle2, Construction, Layers } from 'lucide-react';
import type { ReactNode } from 'react';

import { EmptyState } from '@/components/feedback/EmptyState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { dataColumns } from '@/config/modules';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { cn } from '@/lib/utils/cn';

export interface ModulePlaceholderPageProps {
  /** Module title shown in the header (also the document title). */
  title: string;
  description: string;
  /** Feature bullets rendered as "planned capabilities". */
  capabilities: string[];
  /** Fields the module will operate on — rendered as a preview table header. */
  columns?: string[];
  /** Backend app that will own this module, shown as technical context. */
  apiPath: string;
  /** Extra content (used by Settings to embed the theme switcher). */
  children?: ReactNode;
  className?: string;
}

/**
 * Professional placeholder used by every module that ships after Phase 1.
 *
 * Rather than a blank screen, each page documents what the module will do, the
 * data it will own and where its API will live — which doubles as the hand-off
 * brief for the next phase.
 */
export function ModulePlaceholderPage({
  title,
  description,
  capabilities,
  columns,
  apiPath,
  children,
  className,
}: ModulePlaceholderPageProps) {
  useDocumentTitle(title);

  return (
    <div className={cn(className)}>
      <PageHeader
        eyebrow="Phase 2 module"
        title={title}
        description={description}
        actions={
          <>
            <Badge tone="warning" dot>
              Planned
            </Badge>
            <Button variant="outline" size="sm" disabled title="Available in a later phase">
              Configure
            </Button>
          </>
        }
      />

      <div className="animate-[var(--animate-slide-up)] grid gap-5 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="space-y-5">
          <Card>
            <CardHeader
              title="Module not available yet"
              description="This screen is part of the Phase 1 navigation skeleton"
              action={
                <span className="hidden items-center gap-1.5 text-[11.5px] text-subtle sm:inline-flex">
                  <Construction className="size-3.5" />
                  Building in Phase 2
                </span>
              }
            />
            <CardBody className="pt-5">
              <EmptyState
                icon={<Layers />}
                title={`${title} ships in a future phase`}
                description="The navigation, routing, layout and API contract are already in place. Only the business logic is missing — no data is written or sent from this screen."
                action={
                  <Button variant="outline" size="sm" disabled>
                    Coming soon
                  </Button>
                }
                secondaryAction={
                  <span className="font-mono text-[11.5px] text-subtle">{apiPath}</span>
                }
                className="border-0 bg-transparent py-6"
              />
            </CardBody>
          </Card>

          {columns && columns.length > 0 ? (
            <Card>
              <CardHeader
                title="Planned data view"
                description="Preview of the table this module will render once its models exist"
              />
              <div className="overflow-x-auto scrollbar-thin">
                <table className="w-full border-collapse text-left text-sm">
                  <thead className="bg-surface-2">
                    <tr>
                      {columns.map((column) => (
                        <th
                          key={column}
                          scope="col"
                          className="border-b border-border-subtle px-4 py-2.5 text-[11px] font-semibold tracking-wide text-subtle uppercase whitespace-nowrap"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[0, 1, 2].map((row) => (
                      <tr key={row} className="border-b border-border-subtle last:border-0">
                        {columns.map((column) => (
                          <td key={column} className="px-4 py-3">
                            <span className="block h-2.5 w-full max-w-[140px] rounded bg-surface-3" />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="border-t border-border-subtle px-5 py-3 text-[12px] text-subtle">
                Empty state shown by design — no placeholder rows are persisted anywhere.
              </div>
            </Card>
          ) : null}
        </div>

        <div className="space-y-5">
          <Card>
            <CardHeader title="Planned capabilities" description="Scope for the next build phase" />
            <ul className="space-y-3 px-5 py-4">
              {capabilities.map((capability) => (
                <li key={capability} className="flex gap-2.5 text-[13px] text-muted">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand-500" />
                  <span>{capability}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <CardHeader title="Technical context" />
            <dl className="divide-y divide-[color:var(--app-border)] text-[12.5px]">
              <div className="flex items-center justify-between gap-3 px-5 py-2.5">
                <dt className="text-subtle">API endpoint</dt>
                <dd className="font-mono text-[11.5px] text-muted">{apiPath}</dd>
              </div>
              <div className="flex items-center justify-between gap-3 px-5 py-2.5">
                <dt className="text-subtle">Status</dt>
                <dd>
                  <Badge tone="neutral" size="sm">
                    Routed · empty
                  </Badge>
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3 px-5 py-2.5">
                <dt className="text-subtle">Sending / writing</dt>
                <dd className="text-muted">Disabled in Phase 1</dd>
              </div>
            </dl>
          </Card>

          {children}
        </div>
      </div>
    </div>
  );
}

/** Convenience wrapper: placeholder page driven by the module registry. */
export function ModulePage({ moduleKey }: { moduleKey: keyof typeof dataColumns }) {
  const config = dataColumns[moduleKey];
  return (
    <ModulePlaceholderPage
      title={config.title}
      description={config.description}
      capabilities={config.capabilities}
      columns={config.columns}
      apiPath={config.apiPath}
    />
  );
}
