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

// Modules that still render the shared placeholder page.
const placeholderRoutes: Array<[string, string]> = [
  ['/imports', 'Imports'],
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
