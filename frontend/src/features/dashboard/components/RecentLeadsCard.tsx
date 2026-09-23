import { ArrowUpRight, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

import { EmptyState } from '@/components/feedback/EmptyState';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { buttonVariants } from '@/components/ui/button-variants';
import { Card, CardHeader } from '@/components/ui/Card';
import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import { emailStatusConfig, leadStatusConfig, scoreChipClass } from '@/config/status';
import { cn } from '@/lib/utils/cn';
import { formatRelativeTime } from '@/lib/utils/format';
import type { LeadRow } from '@/types/dashboard';

export interface RecentLeadsCardProps {
  leads: LeadRow[];
  className?: string;
}

/**
 * Latest leads with the columns the outreach operator actually scans:
 * company, decision maker, e-mail validity, qualification score and status.
 */
export function RecentLeadsCard({ leads, className }: RecentLeadsCardProps) {
  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader
        title="Recent Leads"
        description="Newest additions to the lead database"
        action={
          <Link
            to="/leads"
            className={buttonVariants({ variant: 'ghost', size: 'sm' })}
            aria-label="Open leads module"
          >
            View all
            <ArrowUpRight className="size-3.5" />
          </Link>
        }
      />

      {leads.length === 0 ? (
        <div className="p-5">
          <EmptyState
            compact
            icon={<Users />}
            title="No leads yet"
            description="Import a business dataset or connect a lead source to start building the pipeline."
            action={
              <Link to="/imports" className={buttonVariants({ variant: 'primary', size: 'sm' })}>
                Go to imports
              </Link>
            }
          />
        </div>
      ) : (
        <TableWrapper>
          <Table>
            <THead>
              <TR>
                <TH className="min-w-[220px]">Company</TH>
                <TH className="min-w-[190px]">Contact</TH>
                <TH className="min-w-[170px]">E-mail</TH>
                <TH>Location</TH>
                <TH>Status</TH>
                <TH className="text-right">Score</TH>
                <TH className="text-right">Added</TH>
              </TR>
            </THead>
            <TBody>
              {leads.map((lead) => {
                const status = leadStatusConfig[lead.status];
                const emailStatus = emailStatusConfig[lead.emailStatus];
                return (
                  <TR key={lead.id}>
                    <TD>
                      <div className="flex items-center gap-2.5">
                        <Avatar name={lead.companyName} size="sm" tone="neutral" />
                        <div className="min-w-0">
                          <p className="truncate font-medium text-fg" title={lead.companyName}>
                            {lead.companyName}
                          </p>
                          <p className="truncate text-[11.5px] text-subtle" title={lead.industry}>
                            {lead.industry}
                          </p>
                        </div>
                      </div>
                    </TD>
                    <TD>
                      <p className="truncate font-medium text-fg">{lead.contactName}</p>
                      <p className="truncate text-[11.5px] text-subtle">{lead.jobTitle}</p>
                    </TD>
                    <TD>
                      <p className="max-w-[180px] truncate font-mono text-[12px] text-muted" title={lead.email}>
                        {lead.email || '—'}
                      </p>
                      <Badge tone={emailStatus.tone} size="sm" className="mt-1">
                        {emailStatus.label}
                      </Badge>
                    </TD>
                    <TD className="whitespace-nowrap text-[12.5px] text-muted">
                      {lead.city}, {lead.state}
                    </TD>
                    <TD>
                      <Badge tone={status.tone} size="sm" dot>
                        {status.label}
                      </Badge>
                    </TD>
                    <TD className="text-right">
                      <span
                        className={cn(
                          'tabular inline-flex min-w-9 justify-center rounded-md px-1.5 py-0.5 text-[12px] font-semibold ring-1 ring-inset',
                          scoreChipClass(lead.score),
                        )}
                      >
                        {lead.score}
                      </span>
                    </TD>
                    <TD className="text-right text-[12px] whitespace-nowrap text-subtle">
                      <time dateTime={lead.createdAt}>{formatRelativeTime(lead.createdAt)}</time>
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        </TableWrapper>
      )}

      <div className="flex items-center justify-between border-t border-border-subtle px-5 py-3 text-[12px] text-subtle">
        <span>
          Showing <span className="tabular font-medium text-muted">{leads.length}</span> of 28,490 leads
        </span>
        <span className="hidden sm:inline">Lead scoring &amp; full table arrive with the Leads module</span>
      </div>
    </Card>
  );
}
