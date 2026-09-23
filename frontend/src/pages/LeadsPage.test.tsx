import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LeadsPage } from '@/pages/LeadsPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import type { Lead } from '@/types/lead';

const fetchLeads = vi.hoisted(() => vi.fn());
const fetchLeadStatuses = vi.hoisted(() => vi.fn());
const fetchLeadFilterOptions = vi.hoisted(() => vi.fn());
const exportLeadsCsv = vi.hoisted(() => vi.fn());
const bulkAction = vi.hoisted(() => vi.fn());

vi.mock('@/services/leads.service', async () => {
  const actual = await vi.importActual<typeof import('@/services/leads.service')>(
    '@/services/leads.service',
  );
  return {
    ...actual,
    fetchLeads,
    fetchLeadStatuses,
    fetchLeadFilterOptions,
    exportLeadsCsv,
    bulkAction,
  };
});

function lead(overrides: Partial<Lead> = {}): Lead {
  return {
    id: 1,
    company: 1,
    company_name: 'Northwind Logistics, Inc.',
    contact: 1,
    contact_name: 'Marcus Whitfield',
    job_title: 'VP Operations',
    email: 'm.whitfield@northwindlogistics.com',
    phone: '(614) 555-0142',
    website: 'https://northwindlogistics.com',
    website_domain: 'northwindlogistics.com',
    industry: 'Transportation & Logistics',
    sub_industry: 'Freight',
    city: 'Columbus',
    state: 'OH',
    country: 'US',
    lead_score: 92,
    score_classification: 'HOT',
    lead_status: 'QUALIFIED',
    lead_status_display: 'Qualified',
    crm_status: 'QUALIFIED',
    crm_status_display: 'Qualified',
    email_status: 'VALID',
    email_status_display: 'Valid',
    source: 'dataset_import',
    source_file: 'us_businesses_q3_2026.csv',
    source_row_number: 4287,
    last_contact: '2026-09-20T10:00:00Z',
    is_contactable: true,
    created_at: '2026-09-23T10:00:00Z',
    updated_at: '2026-09-23T10:00:00Z',
    ...overrides,
  };
}

function page(
  results: Lead[],
  overrides: Partial<{ count: number; next: string | null; previous: string | null }> = {},
) {
  return { count: results.length, next: null, previous: null, results, ...overrides };
}

describe('LeadsPage', () => {
  beforeEach(() => {
    fetchLeads.mockReset();
    fetchLeadStatuses.mockReset();
    fetchLeadFilterOptions.mockReset();
    bulkAction.mockReset();
    exportLeadsCsv.mockReset();
    fetchLeadStatuses.mockResolvedValue({
      lead_status: [],
      email_status: [],
      total: 0,
      defaults: { lead_status: 'NEW', email_status: 'UNKNOWN' },
    });
    fetchLeadFilterOptions.mockResolvedValue({
      industries: [],
      sub_industries: [],
      cities: [],
      states: [],
      sources: [],
      score_points: {},
    });
  });

  it('renders the lead table with every required column', async () => {
    fetchLeads.mockResolvedValue(page([lead()]));
    renderWithProviders(<LeadsPage />, { route: '/leads' });

    const headers = await screen.findAllByRole('columnheader');
    const headerLabels = headers.map((header) => header.textContent?.trim() ?? '');
    expect(headerLabels).toEqual(
      expect.arrayContaining([
        'Business',
        'Contact',
        'Email',
        'Phone',
        'Industry',
        'Sub-industry',
        'City',
        'State',
        'Lead Score',
        'Email Status',
        'CRM Status',
        'Source',
        'Last Contact',
      ]),
    );

    const table = screen.getByRole('table');
    for (const cell of [
      'Northwind Logistics, Inc.',
      'Marcus Whitfield',
      'VP Operations',
      'm.whitfield@northwindlogistics.com',
      'Valid',
      '(614) 555-0142',
      'Transportation & Logistics',
      'Columbus',
      'OH',
      '92',
      'Qualified',
      'Hot',
    ]) {
      expect(within(table).getByText(cell)).toBeInTheDocument();
    }
  });

  it('shows a loading skeleton before data arrives', async () => {
    fetchLeads.mockReturnValue(new Promise(() => undefined));
    renderWithProviders(<LeadsPage />, { route: '/leads' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Leads' })).toBeInTheDocument();
    expect(document.querySelectorAll('[aria-busy="true"]').length).toBeGreaterThan(0);
  });

  it('shows the empty state when the database has no leads', async () => {
    fetchLeads.mockResolvedValue(page([]));
    renderWithProviders(<LeadsPage />, { route: '/leads' });

    expect(await screen.findByText('No leads yet')).toBeInTheDocument();
  });

  it('shows a filter-specific empty state when a query matches nothing', async () => {
    fetchLeads.mockResolvedValue(page([]));
    renderWithProviders(<LeadsPage />, { route: '/leads' });

    await userEvent.type(screen.getByLabelText(/search business/i), 'zzz');

    expect(await screen.findByText('No leads match these filters')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /clear filters/i }));
    await waitFor(() => expect(fetchLeads).toHaveBeenCalled());
  });

  it('sends the search term to the API after debouncing', async () => {
    fetchLeads.mockResolvedValue(page([lead()]));
    renderWithProviders(<LeadsPage />, { route: '/leads' });
    await screen.findByText('Northwind Logistics, Inc.');

    await userEvent.type(screen.getByLabelText(/search business/i), 'vertex');

    await waitFor(
      () => {
        const calls = fetchLeads.mock.calls.map(([params]) => params.search);
        expect(calls).toContain('vertex');
      },
      { timeout: 2000 },
    );
    const lastCall = fetchLeads.mock.calls.at(-1)?.[0];
    expect(lastCall.page).toBe(1);
  });

  it('sends status and e-mail filters to the API', async () => {
    fetchLeads.mockResolvedValue(page([lead()]));
    renderWithProviders(<LeadsPage />, { route: '/leads' });
    await screen.findByText('Northwind Logistics, Inc.');

    await userEvent.selectOptions(screen.getByLabelText('All statuses'), 'REPLIED');

    await waitFor(() => {
      const lastCall = fetchLeads.mock.calls.at(-1)?.[0];
      expect(lastCall.lead_status).toBe('REPLIED');
      expect(lastCall.page).toBe(1);
    });

    await userEvent.selectOptions(screen.getByLabelText('All e-mail status'), 'BOUNCED');
    await waitFor(() => {
      const lastCall = fetchLeads.mock.calls.at(-1)?.[0];
      expect(lastCall.email_status).toBe('BOUNCED');
    });
  });

  it('toggles ordering when a sortable header is clicked', async () => {
    fetchLeads.mockResolvedValue(page([lead()]));
    renderWithProviders(<LeadsPage />, { route: '/leads' });
    await screen.findByText('Northwind Logistics, Inc.');

    await userEvent.click(screen.getByRole('button', { name: 'Sort by Lead Score' }));

    await waitFor(() => {
      expect(fetchLeads.mock.calls.at(-1)?.[0].ordering).toBe('lead_score');
    });
  });

  it('shows an error state with retry when the API fails', async () => {
    fetchLeads.mockRejectedValueOnce(new Error('Network unreachable'));
    fetchLeads.mockResolvedValue(page([lead()]));

    renderWithProviders(<LeadsPage />, { route: '/leads' });

    expect(await screen.findByText('Could not load leads')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(await screen.findByText('Northwind Logistics, Inc.')).toBeInTheDocument();
  });
});
