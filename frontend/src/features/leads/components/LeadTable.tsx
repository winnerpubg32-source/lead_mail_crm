import { Mail, Phone, Building2 } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { SortableHeader } from '@/components/ui/SortableHeader';
import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import { emailStatusConfig, leadStatusConfig, scoreChipClass } from '@/config/status';
import { sourceLabel } from '@/config/list-options';
import type { SortDirection } from '@/hooks/useListQuery';
import { cn } from '@/lib/utils/cn';
import type { Lead } from '@/types/lead';

export interface LeadTableProps {
  leads: Lead[];
  ordering: string;
  onToggleOrdering: (field: string) => void;
}

/**
 * Lead table.
 *
 * Columns follow the product brief: Business · Contact · Email · Phone ·
 * Industry · City · State · Lead Score · Status. Sortable headers map to DRF
 * `ordering` fields (relations use the `__` form).
 */
export function LeadTable({ leads, ordering, onToggleOrdering }: LeadTableProps) {
  const directionFor = (field: string): SortDirection | null =>
    ordering === field ? 'asc' : ordering === `-${field}` ? 'desc' : null;

  return (
    <TableWrapper>
      <Table>
        <THead>
          <TR>
            <SortableHeader
              label="Business"
              field="company__name"
              direction={directionFor('company__name')}
              onToggle={onToggleOrdering}
              className="min-w-[230px]"
            />
            <SortableHeader
              label="Contact"
              field="contact__full_name"
              direction={directionFor('contact__full_name')}
              onToggle={onToggleOrdering}
              className="min-w-[190px]"
            />
            <TH className="min-w-[210px]">Email</TH>
            <TH className="min-w-[140px]">Phone</TH>
            <TH className="min-w-[160px]">Industry</TH>
            <TH className="min-w-[150px]">City</TH>
            <TH>State</TH>
            <SortableHeader
              label="Lead Score"
              field="lead_score"
              direction={directionFor('lead_score')}
              onToggle={onToggleOrdering}
              align="right"
            />
            <SortableHeader
              label="Status"
              field="lead_status"
              direction={directionFor('lead_status')}
              onToggle={onToggleOrdering}
            />
          </TR>
        </THead>
        <TBody>
          {leads.map((lead) => {
            const status = leadStatusConfig[lead.lead_status];
            const emailStatus = emailStatusConfig[lead.email_status];

            return (
              <TR key={lead.id}>
                <TD>
                  <div className="flex items-start gap-2.5">
                    <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-lg bg-surface-3 text-subtle">
                      <Building2 className="size-3.5" />
                    </span>
                    <div className="min-w-0">
                      <p className="truncate font-medium text-fg" title={lead.company_name || 'No company'}>
                        {lead.company_name || '—'}
                      </p>
                      <p className="truncate text-[11.5px] text-subtle">
                        {lead.source ? sourceLabel(lead.source) : 'No source'}
                      </p>
                    </div>
                  </div>
                </TD>

                <TD>
                  {lead.contact_name ? (
                    <>
                      <p className="truncate font-medium text-fg" title={lead.contact_name}>
                        {lead.contact_name}
                      </p>
                      <p className="truncate text-[11.5px] text-subtle">{lead.job_title || '—'}</p>
                    </>
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
                    >
                      <Mail className="size-3.5 shrink-0 text-subtle" />
                      <span className="truncate font-mono text-[12px] text-muted group-hover:text-brand-600 group-hover:underline dark:group-hover:text-brand-300">
                        {lead.email}
                      </span>
                    </a>
                  ) : (
                    <span className="text-subtle">—</span>
                  )}
                  <Badge tone={emailStatus.tone} size="sm" className="mt-1">
                    {emailStatus.label}
                  </Badge>
                </TD>

                <TD>
                  {lead.phone ? (
                    <span className="tabular inline-flex items-center gap-1.5 text-[12.5px] whitespace-nowrap text-muted">
                      <Phone className="size-3.5 shrink-0 text-subtle" />
                      {lead.phone}
                    </span>
                  ) : (
                    <span className="text-subtle">—</span>
                  )}
                </TD>

                <TD className="text-[12.5px] text-muted">
                  <span className="block max-w-[170px] truncate" title={lead.industry}>
                    {lead.industry || '—'}
                  </span>
                </TD>

                <TD className="text-[12.5px] whitespace-nowrap text-muted">{lead.city || '—'}</TD>

                <TD className="text-[12.5px] text-muted">{lead.state || '—'}</TD>

                <TD className="text-right">
                  <span
                    className={cn(
                      'tabular inline-flex min-w-9 justify-center rounded-md px-1.5 py-0.5 text-[12px] font-semibold ring-1 ring-inset',
                      scoreChipClass(lead.lead_score),
                    )}
                    title={`Lead score ${lead.lead_score}`}
                  >
                    {lead.lead_score}
                  </span>
                </TD>

                <TD>
                  <Badge tone={status.tone} size="sm" dot>
                    {status.label}
                  </Badge>
                </TD>
              </TR>
            );
          })}
        </TBody>
      </Table>
    </TableWrapper>
  );
}
