import { Building2, ExternalLink, Globe, RefreshCw, Users } from 'lucide-react';

import { EmptyState } from '@/components/feedback/EmptyState';
import { ErrorState } from '@/components/feedback/ErrorState';
import { TableSkeleton } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';
import { SortableHeader } from '@/components/ui/SortableHeader';
import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import { TableToolbar } from '@/components/ui/TableToolbar';
import { industryOptions, sourceLabel, sourceOptions, stateOptions } from '@/config/list-options';
import { useCompanies } from '@/hooks/useCompanies';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useListQuery } from '@/hooks/useListQuery';
import { cn } from '@/lib/utils/cn';
import { formatNumber } from '@/lib/utils/format';
import type { Company } from '@/types/lead';

function CompanyRow({ company }: { company: Company }) {
  const website = company.website || (company.normalized_website ? `https://${company.normalized_website}` : '');

  return (
    <TR>
      <TD>
        <div className="flex items-start gap-2.5">
          <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-lg bg-surface-3 text-subtle">
            <Building2 className="size-3.5" />
          </span>
          <div className="min-w-0">
            <p className="truncate font-medium text-fg" title={company.name}>
              {company.name}
            </p>
            <p className="truncate text-[11.5px] text-subtle">
              {company.sub_industry || company.industry || '—'}
            </p>
          </div>
        </div>
      </TD>

      <TD>
        {website ? (
          <a
            href={website}
            target="_blank"
            rel="noreferrer noopener"
            className="group inline-flex max-w-[220px] items-center gap-1.5"
            title={website}
          >
            <Globe className="size-3.5 shrink-0 text-subtle" />
            <span className="truncate font-mono text-[12px] text-muted group-hover:text-brand-600 group-hover:underline dark:group-hover:text-brand-300">
              {company.normalized_website || website}
            </span>
            <ExternalLink className="size-3 shrink-0 text-subtle" />
          </a>
        ) : (
          <span className="text-subtle">—</span>
        )}
      </TD>

      <TD className="text-[12.5px] text-muted">
        <span className="block max-w-[180px] truncate" title={company.industry}>
          {company.industry || '—'}
        </span>
      </TD>

      <TD className="text-[12.5px] whitespace-nowrap text-muted">{company.city || '—'}</TD>
      <TD className="text-[12.5px] text-muted">{company.state || '—'}</TD>

      <TD className="text-right">
        <span className="tabular text-[12.5px] text-muted">
          {company.employee_count ? formatNumber(company.employee_count) : '—'}
        </span>
      </TD>

      <TD className="text-right">
        <span className="tabular inline-flex min-w-9 justify-center rounded-md bg-surface-3 px-1.5 py-0.5 text-[12px] font-medium text-muted ring-1 ring-border-subtle ring-inset">
          {company.contact_count}
        </span>
      </TD>

      <TD className="text-right">
        <span
          className={cn(
            'tabular inline-flex min-w-9 justify-center rounded-md px-1.5 py-0.5 text-[12px] font-medium ring-1 ring-inset',
            company.lead_count > 0
              ? 'bg-brand-50 text-brand-700 ring-brand-200 dark:bg-brand-500/10 dark:text-brand-200 dark:ring-brand-500/20'
              : 'bg-surface-3 text-subtle ring-border-subtle',
          )}
        >
          {company.lead_count}
        </span>
      </TD>

      <TD className="text-[12px] whitespace-nowrap text-subtle">
        {company.source ? sourceLabel(company.source) : '—'}
      </TD>
    </TR>
  );
}

/**
 * Companies — real list backed by `GET /api/v1/companies/`.
 * Shows how many contacts and leads each business contributes.
 */
export function CompaniesPage() {
  useDocumentTitle('Companies');

  const list = useListQuery({ pageSize: 25, ordering: 'name' });
  const { data, isPending, isError, error, refetch, isFetching } = useCompanies(list.params);

  const companies = data?.results ?? [];
  const count = data?.count ?? 0;

  const directionFor = (field: string) =>
    list.ordering === field ? ('asc' as const) : list.ordering === `-${field}` ? ('desc' as const) : null;

  return (
    <div>
      <PageHeader
        eyebrow="Lead database"
        title="Companies"
        description="The imported business database: websites, industries, locations and how many contacts and leads each company contributes."
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
          searchPlaceholder="Search company, domain, industry or city…"
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
              name: 'source',
              label: 'All sources',
              value: list.filters.source ?? '',
              options: sourceOptions,
            },
            {
              name: 'has_website',
              label: 'Website',
              value: list.filters.has_website ?? '',
              options: [
                { value: 'true', label: 'Has website' },
                { value: 'false', label: 'No website' },
              ],
            },
          ]}
          onFilterChange={list.setFilter}
          onReset={list.reset}
          hasActiveQuery={list.hasActiveQuery}
          extra={
            <span className="hidden text-[12.5px] whitespace-nowrap text-subtle lg:inline">
              <span className="tabular font-medium text-muted">{formatNumber(count)}</span> companies
            </span>
          }
        />

        {isPending ? (
          <TableSkeleton rows={8} columns={9} />
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              title="Could not load companies"
              description="The companies API did not respond. Make sure the Django backend is running."
              details={error instanceof Error ? error.message : undefined}
              onRetry={() => void refetch()}
            />
          </div>
        ) : companies.length === 0 ? (
          <div className="p-5">
            {list.hasActiveQuery ? (
              <EmptyState
                icon={<Building2 />}
                title="No companies match these filters"
                description="Try a different search term or clear the filters to see the full company database."
                action={
                  <Button variant="outline" size="sm" onClick={list.reset}>
                    Clear filters
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={<Building2 />}
                title="No companies yet"
                description="The company database is empty. Dataset import arrives in the next phase — seed development data with `python manage.py seed_lead_data`."
                action={
                  <span className="inline-flex items-center gap-1.5 font-mono text-[11.5px] text-subtle">
                    <Users className="size-3.5" />
                    GET /api/v1/companies/
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
                      label="Company"
                      field="name"
                      direction={directionFor('name')}
                      onToggle={list.toggleOrdering}
                      className="min-w-[240px]"
                    />
                    <TH className="min-w-[200px]">Website</TH>
                    <SortableHeader
                      label="Industry"
                      field="industry"
                      direction={directionFor('industry')}
                      onToggle={list.toggleOrdering}
                      className="min-w-[160px]"
                    />
                    <SortableHeader
                      label="City"
                      field="city"
                      direction={directionFor('city')}
                      onToggle={list.toggleOrdering}
                    />
                    <SortableHeader
                      label="State"
                      field="state"
                      direction={directionFor('state')}
                      onToggle={list.toggleOrdering}
                    />
                    <SortableHeader
                      label="Employees"
                      field="employee_count"
                      direction={directionFor('employee_count')}
                      onToggle={list.toggleOrdering}
                      align="right"
                    />
                    <SortableHeader
                      label="Contacts"
                      field="contact_count"
                      direction={directionFor('contact_count')}
                      onToggle={list.toggleOrdering}
                      align="right"
                    />
                    <SortableHeader
                      label="Leads"
                      field="lead_count"
                      direction={directionFor('lead_count')}
                      onToggle={list.toggleOrdering}
                      align="right"
                    />
                    <TH>Source</TH>
                  </TR>
                </THead>
                <TBody>
                  {companies.map((company) => (
                    <CompanyRow key={company.id} company={company} />
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
              itemLabel="companies"
            />
          </>
        )}
      </Card>
    </div>
  );
}
