import { Mail, Phone, RefreshCw, Users } from 'lucide-react';

import { EmptyState } from '@/components/feedback/EmptyState';
import { ErrorState } from '@/components/feedback/ErrorState';
import { TableSkeleton } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';
import { SortableHeader } from '@/components/ui/SortableHeader';
import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import { TableToolbar } from '@/components/ui/TableToolbar';
import { industryOptions, phoneTypeOptions, stateOptions } from '@/config/list-options';
import { phoneTypeLabels } from '@/config/status';
import { useContacts } from '@/hooks/useContacts';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useListQuery } from '@/hooks/useListQuery';
import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';
import type { Contact } from '@/types/lead';

function ContactRow({ contact }: { contact: Contact }) {
  const deliverable = Boolean(contact.normalized_email);

  return (
    <TR>
      <TD>
        <div className="flex items-center gap-2.5">
          <Avatar name={contact.full_name} size="sm" tone="neutral" />
          <div className="min-w-0">
            <p className="truncate font-medium text-fg" title={contact.full_name}>
              {contact.full_name || '—'}
            </p>
            <p className="truncate text-[11.5px] text-subtle">{contact.job_title || 'No title'}</p>
          </div>
        </div>
      </TD>

      <TD className="text-[12.5px] text-muted">
        <span className="block max-w-[190px] truncate" title={contact.company_name}>
          {contact.company_name || '—'}
        </span>
      </TD>

      <TD>
        {contact.email ? (
          <a href={`mailto:${contact.email}`} className="group inline-flex max-w-[230px] items-center gap-1.5" title={contact.email}>
            <Mail className="size-3.5 shrink-0 text-subtle" />
            <span className="truncate font-mono text-[12px] text-muted group-hover:text-brand-600 group-hover:underline dark:group-hover:text-brand-300">
              {contact.email}
            </span>
          </a>
        ) : (
          <span className="text-subtle">No e-mail</span>
        )}
        <Badge tone={deliverable ? 'success' : 'neutral'} size="sm" className="mt-1">
          {deliverable ? 'Deliverable' : 'No address'}
        </Badge>
      </TD>

      <TD>
        {contact.phone ? (
          <div>
            <span className="tabular inline-flex items-center gap-1.5 text-[12.5px] whitespace-nowrap text-muted">
              <Phone className="size-3.5 shrink-0 text-subtle" />
              {contact.phone}
            </span>
            <p className="mt-0.5 pl-5 text-[11px] text-subtle">
              {phoneTypeLabels[contact.phone_type] ?? contact.phone_type}
            </p>
          </div>
        ) : (
          <span className="text-subtle">—</span>
        )}
      </TD>

      <TD className="text-[12.5px] text-muted">
        <span className="block max-w-[160px] truncate" title={contact.company_industry}>
          {contact.company_industry || '—'}
        </span>
      </TD>

      <TD className="text-[12.5px] whitespace-nowrap text-muted">
        {contact.company_city || contact.company_state
          ? `${contact.company_city}${contact.company_city && contact.company_state ? ', ' : ''}${contact.company_state}`
          : '—'}
      </TD>
    </TR>
  );
}

/**
 * Contacts — real list backed by `GET /api/v1/contacts/`.
 * Rows carry their company context (name, industry, location) from the join.
 */
export function ContactsPage() {
  useDocumentTitle('Contacts');

  const list = useListQuery({ pageSize: 25 });
  const { data, isPending, isError, error, refetch, isFetching } = useContacts(list.params);

  const contacts = data?.results ?? [];
  const count = data?.count ?? 0;

  const directionFor = (field: string) =>
    list.ordering === field ? ('asc' as const) : list.ordering === `-${field}` ? ('desc' as const) : null;

  return (
    <div>
      <PageHeader
        eyebrow="Lead database"
        title="Contacts"
        description="Decision makers behind each company: names, job titles, e-mail addresses and phone numbers."
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

      <Card className="animate-[var(--animate-slide-up)] overflow-hidden">
        <TableToolbar
          search={list.search}
          onSearchChange={list.setSearch}
          searchPlaceholder="Search name, title, e-mail or company…"
          filters={[
            {
              name: 'industry',
              label: 'All industries',
              value: list.filters.industry ?? '',
              options: industryOptions,
            },
            {
              name: 'state',
              label: 'All states',
              value: list.filters.state ?? '',
              options: stateOptions,
            },
            {
              name: 'phone_type',
              label: 'All phone types',
              value: list.filters.phone_type ?? '',
              options: phoneTypeOptions,
            },
            {
              name: 'has_email',
              label: 'E-mail',
              value: list.filters.has_email ?? '',
              options: [
                { value: 'true', label: 'Has e-mail' },
                { value: 'false', label: 'Missing e-mail' },
              ],
            },
          ]}
          onFilterChange={list.setFilter}
          onReset={list.reset}
          hasActiveQuery={list.hasActiveQuery}
          extra={
            <span className="hidden text-[12.5px] whitespace-nowrap text-subtle lg:inline">
              <span className="tabular font-medium text-muted">{formatNumber(count)}</span> contacts
            </span>
          }
        />

        {isPending ? (
          <TableSkeleton rows={8} columns={6} />
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              title="Could not load contacts"
              description="The contacts API did not respond. Make sure the Django backend is running."
              details={error instanceof Error ? error.message : undefined}
              onRetry={() => void refetch()}
            />
          </div>
        ) : contacts.length === 0 ? (
          <div className="p-5">
            {list.hasActiveQuery ? (
              <EmptyState
                icon={<Users />}
                title="No contacts match these filters"
                description="Try a different search term or clear the filters to see the full contact list."
                action={
                  <Button variant="outline" size="sm" onClick={list.reset}>
                    Clear filters
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={<Users />}
                title="No contacts yet"
                description="No people have been added to the lead database. Contact records arrive with dataset import in the next phase."
                action={
                  <span
                    className={cn(
                      'inline-flex items-center gap-1.5 font-mono text-[11.5px] text-subtle',
                    )}
                  >
                    GET /api/v1/contacts/
                  </span>
                }
              />
            )}
          </div>
        ) : (
          <>
            <TableWrapper>
              <Table>
                <THead>
                  <TR>
                    <SortableHeader
                      label="Contact"
                      field="full_name"
                      direction={directionFor('full_name')}
                      onToggle={list.toggleOrdering}
                      className="min-w-[220px]"
                    />
                    <SortableHeader
                      label="Company"
                      field="company__name"
                      direction={directionFor('company__name')}
                      onToggle={list.toggleOrdering}
                      className="min-w-[200px]"
                    />
                    <TH className="min-w-[240px]">Email</TH>
                    <TH className="min-w-[150px]">Phone</TH>
                    <TH className="min-w-[160px]">Industry</TH>
                    <TH className="min-w-[140px]">Location</TH>
                  </TR>
                </THead>
                <TBody>
                  {contacts.map((contact) => (
                    <ContactRow key={contact.id} contact={contact} />
                  ))}
                </TBody>
              </Table>
            </TableWrapper>
            <Pagination
              count={count}
              page={list.page}
              pageSize={list.pageSize}
              hasNext={Boolean(data?.next)}
              hasPrevious={Boolean(data?.previous)}
              onPageChange={list.setPage}
              onPageSizeChange={list.setPageSize}
              itemLabel="contacts"
            />
          </>
        )}
      </Card>
    </div>
  );
}
