import { Building2, Globe, MailQuestion, MapPin, Phone, RefreshCw } from 'lucide-react';

import { EmptyState } from '@/components/feedback/EmptyState';
import { ErrorState } from '@/components/feedback/ErrorState';
import { TableSkeleton } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';
import { TableToolbar } from '@/components/ui/TableToolbar';
import {
  useDataQualityStats,
  useMissingEmailLeads,
} from '@/hooks/useDataQuality';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useListQuery } from '@/hooks/useListQuery';
import { formatNumber } from '@/lib/utils/format';
import { industryOptions, stateOptions } from '@/config/list-options';
import type { MissingEmailLead } from '@/types/dataQuality';

/**
 * Missing-e-mail leads view (Phase 4).
 *
 * Shows leads without a valid normalized e-mail so they can be sent through an
 * enrichment process later. We never invent or guess e-mails.
 */
export function MissingEmailPage() {
  useDocumentTitle('Missing e-mail');
  const list = useListQuery();
  const { data, isPending, isError, error, refetch, isFetching } = useMissingEmailLeads(list.params);
  const stats = useDataQualityStats();

  const leads: MissingEmailLead[] = data?.results ?? [];
  const count = data?.count ?? 0;

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Data quality"
        title="Missing e-mail leads"
        description="Leads that have useful company and contact information but no deliverable e-mail address. These records are kept for future enrichment — we never invent or auto-generate addresses."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => void refetch()}
            isLoading={isFetching}
            leadingIcon={<RefreshCw className="size-3.5" />}
          >
            Refresh
          </Button>
        }
      />

      {stats.data ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard label="Leads missing e-mail" value={stats.data.missing_emails} tone="amber" />
          <StatCard label="With phone number" value={count} tone="sky" />
          <StatCard label="With website" value={count} tone="violet" />
          <StatCard label="With contact name" value={count} tone="emerald" />
        </div>
      ) : null}

      <Card className="overflow-hidden">
        <TableToolbar
          search={list.search}
          onSearchChange={list.setSearch}
          searchPlaceholder="Search company, contact, industry, city…"
          filters={[
            {
              name: 'company__industry',
              label: 'All industries',
              value: list.filters['company__industry'] ?? '',
              options: industryOptions,
            },
            {
              name: 'company__state',
              label: 'All states',
              value: list.filters['company__state'] ?? '',
              options: stateOptions,
            },
          ]}
          onFilterChange={list.setFilter}
          onReset={list.reset}
          hasActiveQuery={list.hasActiveQuery}
          extra={
            <span className="hidden text-[12.5px] whitespace-nowrap text-subtle lg:inline">
              <span className="tabular font-medium text-muted">{formatNumber(count)}</span> leads
            </span>
          }
        />

        {isPending ? (
          <TableSkeleton rows={8} columns={7} />
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              title="Could not load missing-e-mail leads"
              details={error instanceof Error ? error.message : undefined}
              onRetry={() => void refetch()}
            />
          </div>
        ) : leads.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={<MailQuestion />}
              title={
                list.hasActiveQuery
                  ? 'No leads match these filters'
                  : 'Every lead has a deliverable e-mail'
              }
              description="Nicely done — run an import to add more prospects."
            />
          </div>
        ) : (
          <>
            <div className="divide-y divide-border-subtle">
              {leads.map((lead) => (
                <MissingEmailRow key={lead.id} lead={lead} />
              ))}
            </div>
            <Pagination
              count={count}
              page={list.page}
              pageSize={list.pageSize}
              hasNext={Boolean(data?.next)}
              hasPrevious={Boolean(data?.previous)}
              onPageChange={list.setPage}
              onPageSizeChange={list.setPageSize}
              itemLabel="leads"
            />
          </>
        )}
      </Card>
    </div>
  );
}

function StatCard({ label, value, tone }: { label: string; value: number; tone: string }) {
  const tones: Record<string, string> = {
    amber: 'text-amber-600',
    sky: 'text-sky-600',
    violet: 'text-violet-600',
    emerald: 'text-emerald-600',
  };
  return (
    <div className="rounded-[var(--radius-card)] border border-border-subtle bg-surface p-4 shadow-[var(--shadow-card)]">
      <div className="text-[12.5px] font-medium text-muted">{label}</div>
      <div className={`mt-2 text-[22px] font-semibold tabular ${tones[tone] ?? ''}`}>
        {formatNumber(value)}
      </div>
    </div>
  );
}

function MissingEmailRow({ lead }: { lead: MissingEmailLead }) {
  return (
    <div className="flex flex-col gap-2 p-4 md:flex-row md:items-start md:justify-between">
      <div className="min-w-0 space-y-1.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-fg">
            {lead.contact_name || '(no contact name)'}
          </span>
          {lead.job_title ? <span className="text-[12.5px] text-muted">{lead.job_title}</span> : null}
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12.5px] text-subtle">
          <span className="flex items-center gap-1.5">
            <Building2 className="size-3.5" />
            {lead.company_name}
          </span>
          {lead.phone ? (
            <span className="flex items-center gap-1.5">
              <Phone className="size-3.5" />
              {lead.phone}
            </span>
          ) : null}
          {lead.website ? (
            <a
              href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 hover:text-fg"
            >
              <Globe className="size-3.5" />
              {lead.website}
            </a>
          ) : null}
          {(lead.city || lead.state) && (
            <span className="flex items-center gap-1.5">
              <MapPin className="size-3.5" />
              {[lead.city, lead.state].filter(Boolean).join(', ')}
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5 pt-0.5">
          {lead.industry ? <Badge tone="neutral" size="sm">{lead.industry}</Badge> : null}
          {lead.source ? <Badge tone="neutral" size="sm">{lead.source}</Badge> : null}
          {lead.source_file ? <Badge tone="neutral" size="sm">{lead.source_file}{lead.source_row_number ? `:${lead.source_row_number}` : ''}</Badge> : null}
        </div>
      </div>
      <Badge tone="warning" size="sm">No e-mail</Badge>
    </div>
  );
}
