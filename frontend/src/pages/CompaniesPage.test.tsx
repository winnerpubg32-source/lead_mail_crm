import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CompaniesPage } from '@/pages/CompaniesPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import type { Company } from '@/types/lead';

const fetchCompanies = vi.hoisted(() => vi.fn());

vi.mock('@/services/companies.service', async () => {
  const actual = await vi.importActual<typeof import('@/services/companies.service')>(
    '@/services/companies.service',
  );
  return { ...actual, fetchCompanies };
});

function company(overrides: Partial<Company> = {}): Company {
  return {
    id: 1,
    name: 'Northwind Logistics, Inc.',
    industry: 'Transportation & Logistics',
    sub_industry: 'Freight Brokerage',
    website: 'https://www.northwindlogistics.com',
    normalized_website: 'northwindlogistics.com',
    domain: 'northwindlogistics.com',
    phone: '(614) 555-0100',
    street_address: '1200 Meridian Plaza',
    city: 'Columbus',
    state: 'OH',
    zip_code: '43215',
    country: 'United States',
    employee_count: 850,
    source: 'dataset_import',
    location: 'Columbus, OH',
    lead_count: 3,
    contact_count: 4,
    created_at: '2026-09-23T10:00:00Z',
    updated_at: '2026-09-23T10:00:00Z',
    ...overrides,
  };
}

function page(results: Company[], overrides: Partial<{ count: number; next: string | null; previous: string | null }> = {}) {
  return { count: results.length, next: null, previous: null, results, ...overrides };
}

describe('CompaniesPage', () => {
  beforeEach(() => {
    fetchCompanies.mockReset();
  });

  it('renders real company rows with their relation counts', async () => {
    fetchCompanies.mockResolvedValue(page([company()]));
    renderWithProviders(<CompaniesPage />, { route: '/companies' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Companies' })).toBeInTheDocument();
    await screen.findByText('Northwind Logistics, Inc.');

    const table = screen.getByRole('table');
    const headers = within(table)
      .getAllByRole('columnheader')
      .map((header) => header.textContent?.trim() ?? '');
    expect(headers).toEqual([
      'Company',
      'Website',
      'Industry',
      'City',
      'State',
      'Employees',
      'Contacts',
      'Leads',
      'Source',
    ]);

    expect(within(table).getByText('Northwind Logistics, Inc.')).toBeInTheDocument();
    expect(within(table).getByText('northwindlogistics.com')).toBeInTheDocument();
    expect(within(table).getByText('850')).toBeInTheDocument();
    expect(within(table).getByText('4')).toBeInTheDocument(); // contacts
    expect(within(table).getByText('3')).toBeInTheDocument(); // leads
    expect(within(table).getByText('Dataset import')).toBeInTheDocument();
  });

  it('shows the empty state when there are no companies', async () => {
    fetchCompanies.mockResolvedValue(page([]));
    renderWithProviders(<CompaniesPage />, { route: '/companies' });

    expect(await screen.findByText('No companies yet')).toBeInTheDocument();
  });

  it('sends search and filters to the API and resets to page 1', async () => {
    fetchCompanies.mockResolvedValue(page([company()]));
    renderWithProviders(<CompaniesPage />, { route: '/companies' });
    await screen.findByText('Northwind Logistics, Inc.');

    await userEvent.type(screen.getByLabelText(/search company/i), 'vertex');
    await waitFor(() => {
      const calls = fetchCompanies.mock.calls.map(([params]) => params.search);
      expect(calls).toContain('vertex');
    });

    await userEvent.selectOptions(screen.getByLabelText('All states'), 'OH');
    await waitFor(() => {
      const lastCall = fetchCompanies.mock.calls.at(-1)?.[0];
      expect(lastCall.state).toBe('OH');
      expect(lastCall.page).toBe(1);
    });
  });

  it('shows an error state when the API fails', async () => {
    fetchCompanies.mockRejectedValueOnce(new Error('boom'));
    fetchCompanies.mockResolvedValue(page([company()]));
    renderWithProviders(<CompaniesPage />, { route: '/companies' });

    expect(await screen.findByText('Could not load companies')).toBeInTheDocument();
  });
});
