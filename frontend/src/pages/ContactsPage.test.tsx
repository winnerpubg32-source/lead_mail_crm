import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ContactsPage } from '@/pages/ContactsPage';
import { renderWithProviders } from '@/test/renderWithProviders';
import type { Contact } from '@/types/lead';

const fetchContacts = vi.hoisted(() => vi.fn());

vi.mock('@/services/contacts.service', async () => {
  const actual = await vi.importActual<typeof import('@/services/contacts.service')>(
    '@/services/contacts.service',
  );
  return { ...actual, fetchContacts };
});

function contact(overrides: Partial<Contact> = {}): Contact {
  return {
    id: 1,
    company: 1,
    company_name: 'Northwind Logistics, Inc.',
    first_name: 'Marcus',
    last_name: 'Whitfield',
    full_name: 'Marcus Whitfield',
    job_title: 'VP Operations',
    email: 'm.whitfield@northwindlogistics.com',
    normalized_email: 'm.whitfield@northwindlogistics.com',
    phone: '(614) 555-0142',
    normalized_phone: '6145550142',
    phone_type: 'MOBILE',
    company_industry: 'Transportation & Logistics',
    company_city: 'Columbus',
    company_state: 'OH',
    created_at: '2026-09-23T10:00:00Z',
    updated_at: '2026-09-23T10:00:00Z',
    ...overrides,
  };
}

function page(results: Contact[]) {
  return { count: results.length, next: null, previous: null, results };
}

describe('ContactsPage', () => {
  beforeEach(() => {
    fetchContacts.mockReset();
  });

  it('renders contact rows with company context', async () => {
    fetchContacts.mockResolvedValue(page([contact()]));
    renderWithProviders(<ContactsPage />, { route: '/contacts' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Contacts' })).toBeInTheDocument();
    await screen.findByText('Marcus Whitfield');

    const table = screen.getByRole('table');
    expect(within(table).getByText('Marcus Whitfield')).toBeInTheDocument();
    expect(within(table).getByText('VP Operations')).toBeInTheDocument();
    expect(within(table).getByText('Northwind Logistics, Inc.')).toBeInTheDocument();
    expect(within(table).getByText('m.whitfield@northwindlogistics.com')).toBeInTheDocument();
    expect(within(table).getByText('(614) 555-0142')).toBeInTheDocument();
    expect(within(table).getByText('Mobile')).toBeInTheDocument();
    expect(within(table).getByText('Columbus, OH')).toBeInTheDocument();
    expect(within(table).getByText('Transportation & Logistics')).toBeInTheDocument();
  });

  it('marks contacts without an address as undeliverable', async () => {
    fetchContacts.mockResolvedValue(
      page([contact({ id: 2, full_name: 'Front Desk', email: '', normalized_email: '', phone: '' })]),
    );
    renderWithProviders(<ContactsPage />, { route: '/contacts' });

    expect(await screen.findByText('Front Desk')).toBeInTheDocument();
    expect(screen.getByText('No e-mail')).toBeInTheDocument();
    expect(screen.getByText('No address')).toBeInTheDocument();
  });

  it('shows the empty state when there are no contacts', async () => {
    fetchContacts.mockResolvedValue(page([]));
    renderWithProviders(<ContactsPage />, { route: '/contacts' });

    expect(await screen.findByText('No contacts yet')).toBeInTheDocument();
  });

  it('filters by phone type through the API', async () => {
    fetchContacts.mockResolvedValue(page([contact()]));
    renderWithProviders(<ContactsPage />, { route: '/contacts' });
    await screen.findByText('Marcus Whitfield');

    await userEvent.selectOptions(screen.getByLabelText('All phone types'), 'MOBILE');

    await waitFor(() => {
      expect(fetchContacts.mock.calls.at(-1)?.[0].phone_type).toBe('MOBILE');
    });
  });

  it('shows an error state when the API fails', async () => {
    fetchContacts.mockRejectedValueOnce(new Error('offline'));
    fetchContacts.mockResolvedValue(page([contact()]));
    renderWithProviders(<ContactsPage />, { route: '/contacts' });

    expect(await screen.findByText('Could not load contacts')).toBeInTheDocument();
  });
});
