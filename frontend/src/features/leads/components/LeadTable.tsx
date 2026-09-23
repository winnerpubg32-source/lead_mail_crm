import { Link } from 'react-router-dom';
import { Mail, Phone, Building2 } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { SortableHeader } from '@/components/ui/SortableHeader';
import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import {
  emailStatusConfig,
  leadStatusConfig,
  scoreChipClass,
  scoreClassification,
  scoreClassificationConfig,
} from '@/config/status';
import { sourceLabel } from '@/config/list-options';
import { formatRelativeTime } from '@/lib/utils/format';
import type { SortDirection } from '@/hooks/useListQuery';
import { cn } from '@/lib/utils/cn';
import type { Lead } from '@/types/lead';

export interface LeadTableProps {
  leads: Lead[];
  ordering: string;
  onToggleOrdering: (field: string) => void;
  selected?: Set<number>;
  onToggleOne?: (id: number, selected: boolean) => void;
  onToggleAll?: (selected: boolean) => void;
  allSelected?: boolean;
  someSelected?: boolean;
}

/**
 * Lead table (Phase 5).
 *
 * Columns: Business · Contact · Email · Phone · Industry · Sub-industry ·
 * City · State · Lead Score · Email Status · CRM Status · Source · Last Contact.
 *
 * Supports bulk row selection via a checkbox column. Each row links to the
 * lead detail page at `/leads/:id`.
 */
export function LeadTable({
  leads,
  ordering,
  onToggleOrdering,
  selected,
  onToggleOne,
  onToggleAll,
  allSelected = false,
  someSelected = false,
}: LeadTableProps) {
  const selectable = Boolean(onToggleOne && onToggleAll);
  const directionFor = (field: string): SortDirection | null =>
    ordering === field ? 'asc' : ordering === `-${field}` ? 'desc' : null;

  const blockedEmail = (lead: Lead) =>
    lead.email_status === 'INVALID' ||
    lead.email_status === 'BOUNCED' ||
    lead.email_status === 'UNSUBSCRIBED' ||
    lead.email_status === 'SUPPRESSED';

  return (
    <TableWrapper>
      <Table>
        <THead>
          <TR>
            {selectable && (
              <TH className="w-10 pl-3">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-border bg-white text-brand-600 focus:ring-brand-500 dark:bg-surface-2"
                  checked={allSelected}
                  ref={(el) => {
                    if (el) el.indeterminate = !allSelected && someSelected;
                  }}
                  onChange={(e) => onToggleAll?.(e.target.checked)}
                  aria-label="Select all leads"
                />
              </TH>
            )}
            <SortableHeader
              label="Business"
              field="company__name"
              direction={directionFor('company__name')}
              onToggle={onToggleOrdering}
              className="min-w-[220px]"
            />
            <SortableHeader
              label="Contact"
              field="contact__full_name"
              direction={directionFor('contact__full_name')}
              onToggle={onToggleOrdering}
              className="min-w-[180px]"
            />
            <TH className="min-w-[200px]">Email</TH>
            <TH className="min-w-[140px]">Phone</TH>
            <SortableHeader
              label="Industry"
              field="company__industry"
              direction={directionFor('company__industry')}
              onToggle={onToggleOrdering}
              className="min-w-[150px]"
            />
            <TH className="min-w-[140px]">Sub-industry</TH>
            <SortableHeader
              label="City"
              field="company__city"
              direction={directionFor('company__city')}
              onToggle={onToggleOrdering}
            />
            <SortableHeader
              label="State"
              field="company__state"
              direction={directionFor('company__state')}
              onToggle={onToggleOrdering}
            />
            <SortableHeader
              label="Lead Score"
              field="lead_score"
              direction={directionFor('lead_score')}
              onToggle={onToggleOrdering}
              align="right"
            />
            <SortableHeader
              label="Email Status"
              field="email_status"
              direction={directionFor('email_status')}
              onToggle={onToggleOrdering}
            />
            <SortableHeader
              label="CRM Status"
              field="lead_status"
              direction={directionFor('lead_status')}
              onToggle={onToggleOrdering}
            />
            <TH>Source</TH>
            <SortableHeader
              label="Last Contact"
              field="last_contact_at"
              direction={directionFor('last_contact_at')}
              onToggle={onToggleOrdering}
            />
          </TR>
        </THead>
        <TBody>
          {leads.map((lead) => {
            const crmStatus = leadStatusConfig[lead.lead_status];
            const emailStatus = emailStatusConfig[lead.email_status];
            const isBlocked = blockedEmail(lead);
            const code = scoreClassification(lead.score_classification, lead.lead_score);
            const cls = scoreClassificationConfig[code];

            const isSelected = selected?.has(lead.id) ?? false;

            return (
              <TR
                key={lead.id}
                className={cn(
                  'group/row transition-colors',
                  isSelected && 'bg-brand-50/50 dark:bg-brand-500/5',
                  'hover:bg-surface-2',
                )}
              >
                {selectable && (
                  <TD className="pl-3">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-border bg-white text-brand-600 focus:ring-brand-500 dark:bg-surface-2"
                      checked={isSelected}
                      onChange={(e) => onToggleOne?.(lead.id, e.target.checked)}
                      aria-label={`Select ${lead.company_name}`}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </TD>
                )}
                <TD>
                  <Link
                    to={`/leads/${lead.id}`}
                    className="flex items-start gap-2.5"
                  >
                    <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-lg bg-surface-3 text-subtle">
                      <Building2 className="size-3.5" />
                    </span>
                    <div className="min-w-0">
                      <p className="truncate font-medium text-fg" title={lead.company_name || 'No company'}>
                        {lead.company_name || '—'}
                      </p>
                      <p className="truncate text-[11.5px] text-subtle">{lead.website_domain || ''}</p>
                    </div>
                  </Link>
                </TD>

                <TD>
                  {lead.contact_name ? (
                    <Link to={`/leads/${lead.id}`} className="block">
                      <p className="truncate font-medium text-fg" title={lead.contact_name}>
                        {lead.contact_name}
                      </p>
                      <p className="truncate text-[11.5px] text-subtle">{lead.job_title || '—'}</p>
                    </Link>
                  ) : (
                    <span className="text-subtle">No contact</span>
                  )}
                </TD>

                <TD>
                  {lead.email ? (
                    <a
                      href={`mailto:${lead.email}`}
                      className="group inline-flex max-w-[220px] items-center gap-1.5"
                      title={lead.email}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Mail className="size-3.5 shrink-0 text-subtle" />
                      <span className="truncate font-mono text-[12px] text-muted group-hover:text-brand-600 group-hover:underline dark:group-hover:text-brand-300">
                        {lead.email}
                      </span>
                    </a>
                  ) : (
                    <span className="text-subtle">—</span>
                  )}
                </TD>

                <TD>
                  {lead.phone ? (
                    <a
                      href={`tel:${lead.phone}`}
                      className="tabular inline-flex items-center gap-1.5 text-[12.5px] whitespace-nowrap text-muted hover:text-brand-600"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Phone className="size-3.5 shrink-0 text-subtle" />
                      {lead.phone}
                    </a>
                  ) : (
                    <span className="text-subtle">—</span>
                  )}
                </TD>

                <TD className="text-[12.5px] text-muted">
                  <span className="block max-w-[170px] truncate" title={lead.industry}>
                    {lead.industry || '—'}
                  </span>
                </TD>

                <TD className="text-[12.5px] text-muted">
                  <span className="block max-w-[150px] truncate" title={lead.sub_industry}>
                    {lead.sub_industry || '—'}
                  </span>
                </TD>

                <TD className="text-[12.5px] whitespace-nowrap text-muted">{lead.city || '—'}</TD>

                <TD className="text-[12.5px] text-muted">{lead.state || '—'}</TD>

                <TD className="text-right">
                  <span
                    className={cn(
                      'tabular inline-flex min-w-9 justify-center rounded-md px-1.5 py-0.5 text-[12px] font-semibold ring-1 ring-inset',
                      scoreChipClass(lead.lead_score, isBlocked),
                    )}
                    title={`Lead score ${lead.lead_score} — ${cls.label}`}
                  >
                    {lead.lead_score}
                  </span>
                  <div className="mt-0.5 text-[10px] uppercase tracking-wide text-subtle">
                    {cls.label}
                  </div>
                </TD>

                <TD>
                  <Badge tone={emailStatus.tone} size="sm" dot>
                    {emailStatus.label}
                  </Badge>
                </TD>

                <TD>
                  <Badge tone={crmStatus.tone} size="sm" dot>
                    {crmStatus.label}
                  </Badge>
                </TD>

                <TD className="text-[12px] text-muted">
                  {lead.source ? sourceLabel(lead.source) : <span className="text-subtle">—</span>}
                </TD>

                <TD className="text-[12px] text-muted whitespace-nowrap">
                  {lead.last_contact ? formatRelativeTime(lead.last_contact) : <span className="text-subtle">—</span>}
                </TD>
              </TR>
            );
          })}
        </TBody>
      </Table>
    </TableWrapper>
  );
}
