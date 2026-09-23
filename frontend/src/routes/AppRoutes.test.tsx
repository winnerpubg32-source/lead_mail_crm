import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { AppRoutes } from '@/routes/AppRoutes';
import { renderWithProviders } from '@/test/renderWithProviders';

// The shell fetches the dashboard payload for the sidebar capacity widget.
vi.mock('@/services/dashboard.service', async () => {
  const actual = await vi.importActual<typeof import('@/services/dashboard.service')>(
    '@/services/dashboard.service',
  );
  return {
    ...actual,
    fetchDashboardOverview: vi.fn().mockResolvedValue({
      generatedAt: new Date().toISOString(),
      metrics: [],
      capacity: {
        sent: 0,
        limit: 90,
        remaining: 90,
        queued: 0,
        failed: 0,
        windowLabel: '09:00 – 17:00',
        hourly: [],
      },
      todaysOutreach: [],
      recentLeads: [],
      leadSources: [],
      campaigns: [],
      pipeline: [],
    }),
  };
});

// The health probe would otherwise hit the network in jsdom.
vi.mock('@/services/health.service', () => ({
  healthKeys: { all: ['health'] },
  fetchHealth: vi.fn().mockRejectedValue(new Error('offline')),
}));

// The imports screens fetch from the API — mocked so the router test stays offline.
vi.mock('@/services/imports.service', async () => {
  const actual = await vi.importActual<typeof import('@/services/imports.service')>(
    '@/services/imports.service',
  );
  return {
    ...actual,
    fetchImportJobs: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }),
    fetchSystemFields: vi.fn().mockResolvedValue([]),
  };
});

// Modules that still render the shared placeholder page.
const placeholderRoutes: Array<[string, string]> = [
  ['/campaigns', 'Campaigns'],
  ['/email', 'Email'],
  ['/follow-ups', 'Follow-ups'],
  ['/crm', 'CRM'],
  ['/analytics', 'Analytics'],
  ['/templates', 'Templates'],
  ['/ai', 'AI'],
  ['/suppression', 'Suppression'],
];

describe('routing', () => {
  it.each(placeholderRoutes)('renders the %s placeholder module', async (path, heading) => {
    renderWithProviders(<AppRoutes />, { route: path });

    expect(
      await screen.findByRole('heading', { level: 1, name: heading }),
    ).toBeInTheDocument();
    expect(screen.getByText(/ships in a future phase/i)).toBeInTheDocument();
  });

  it('renders the imports upload screen', async () => {
    renderWithProviders(<AppRoutes />, { route: '/imports' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Imports' })).toBeInTheDocument();
    expect(screen.getByText('Drag & drop your file here')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /import history/i })).toHaveAttribute(
      'href',
      '/imports/history',
    );
  });

  it('renders the import history page', async () => {
    renderWithProviders(<AppRoutes />, { route: '/imports/history' });

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Import history' }),
    ).toBeInTheDocument();
    expect(await screen.findByText('No imports yet')).toBeInTheDocument();
  });

  it('marks the lead database modules as live in the sidebar', () => {
    renderWithProviders(<AppRoutes />, { route: '/imports' });

    // No "ships in a future phase" hint belongs to a shipped module.
    expect(screen.queryByText(/ships in a future phase/i)).not.toBeInTheDocument();
  });

  it('renders the settings page with the theme switcher', async () => {
    renderWithProviders(<AppRoutes />, { route: '/settings' });

    expect(await screen.findByRole('heading', { level: 1, name: /settings/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dark theme/i })).toBeInTheDocument();
    expect(screen.getByText('Daily marketing e-mail limit')).toBeInTheDocument();
  });

  it('renders the 404 page for unknown routes', async () => {
    renderWithProviders(<AppRoutes />, { route: '/does-not-exist' });

    expect(await screen.findByRole('heading', { level: 1, name: /page not found/i })).toBeInTheDocument();
  });
});
