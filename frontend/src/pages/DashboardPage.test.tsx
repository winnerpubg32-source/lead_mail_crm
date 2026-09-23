import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { DashboardPage } from '@/pages/DashboardPage';
import { renderWithProviders } from '@/test/renderWithProviders';

// The dashboard talks to the data layer only through this service — the test
// substitutes it, which is exactly the seam that will connect to Django later.
const fetchDashboardOverview = vi.hoisted(() => vi.fn());

vi.mock('@/services/dashboard.service', async () => {
  const actual = await vi.importActual<typeof import('@/services/dashboard.service')>(
    '@/services/dashboard.service',
  );
  return { ...actual, fetchDashboardOverview };
});

function overviewPayload() {
  return {
    generatedAt: new Date().toISOString(),
    metrics: [
      {
        id: 'total-leads',
        label: 'Total Leads',
        value: 28490,
        displayValue: '28,490',
        unit: 'count' as const,
        tone: 'brand' as const,
        trend: { value: 8.4, direction: 'up' as const, positive: true, label: 'vs. last week' },
        sparkline: [1, 2, 3, 4, 5],
        hint: 'All leads in the workspace',
      },
      {
        id: 'daily-capacity',
        label: 'Daily Capacity',
        value: 90,
        displayValue: '0 / 90',
        unit: 'count' as const,
        tone: 'amber' as const,
        hint: '90 sends remaining today',
      },
    ],
    capacity: {
      sent: 0,
      limit: 90,
      remaining: 90,
      queued: 148,
      failed: 0,
      windowLabel: '09:00 – 17:00',
      hourly: [
        { hour: '09:00', sent: 0 },
        { hour: '10:00', sent: 0 },
      ],
    },
    todaysOutreach: [],
    recentLeads: [],
    leadSources: [],
    campaigns: [],
    pipeline: [],
  };
}

describe('DashboardPage', () => {
  beforeEach(() => {
    fetchDashboardOverview.mockReset();
  });

  it('renders the loading state before data resolves', async () => {
    fetchDashboardOverview.mockReturnValue(new Promise(() => undefined));
    renderWithProviders(<DashboardPage />, { route: '/dashboard' });

    // Header renders immediately; the body is replaced by the skeleton grid.
    expect(await screen.findByRole('heading', { level: 1, name: 'Dashboard' })).toBeInTheDocument();
    expect(document.querySelectorAll('[aria-busy="true"]').length).toBeGreaterThan(0);
    expect(screen.queryByText('Total Leads')).not.toBeInTheDocument();
  });

  it('renders KPI cards, sections and the 0 / 90 daily capacity', async () => {
    fetchDashboardOverview.mockResolvedValue(overviewPayload());
    renderWithProviders(<DashboardPage />, { route: '/dashboard' });

    // Top cards
    expect(await screen.findByText('Total Leads')).toBeInTheDocument();
    expect(screen.getByText('28,490')).toBeInTheDocument();
    // "Daily Capacity" is both a KPI card and the capacity panel heading.
    expect(screen.getAllByText('Daily Capacity').length).toBeGreaterThan(0);

    // Daily email capacity: "0 / 90" with the remaining quota
    expect(screen.getAllByText('0 / 90').length).toBeGreaterThan(0);
    expect(screen.getByText('Remaining today')).toBeInTheDocument();
    expect(screen.getByText(/148/)).toBeInTheDocument();

    // Required dashboard sections
    expect(screen.getByText('Today’s Outreach')).toBeInTheDocument();
    expect(screen.getByText('Recent Leads')).toBeInTheDocument();
    expect(screen.getByText('Lead Sources')).toBeInTheDocument();
    expect(screen.getByText('Campaign Overview')).toBeInTheDocument();
    expect(screen.getByText('Pipeline Overview')).toBeInTheDocument();
  });

  it('renders empty states when the API returns no rows', async () => {
    fetchDashboardOverview.mockResolvedValue(overviewPayload());
    renderWithProviders(<DashboardPage />, { route: '/dashboard' });

    expect(await screen.findByText('No outreach activity yet today')).toBeInTheDocument();
    expect(screen.getByText('No leads yet')).toBeInTheDocument();
    expect(screen.getByText('No campaigns yet')).toBeInTheDocument();
  });

  it('renders an error state with a retry action when the request fails', async () => {
    fetchDashboardOverview.mockRejectedValueOnce(new Error('API is unreachable'));
    fetchDashboardOverview.mockResolvedValue(overviewPayload());

    renderWithProviders(<DashboardPage />, { route: '/dashboard' });

    expect(await screen.findByText('Could not load the dashboard')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /try again/i }));
    await waitFor(() => expect(screen.getByText('Total Leads')).toBeInTheDocument());
  });
});
