import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ImportHistoryPage } from '@/pages/ImportHistoryPage';
import { historyJob } from '@/test/fixtures/imports';
import { renderWithProviders } from '@/test/renderWithProviders';
import type { ImportJob } from '@/types/import';

const fetchImportJobs = vi.hoisted(() => vi.fn());
const deleteImport = vi.hoisted(() => vi.fn());

vi.mock('@/services/imports.service', async () => {
  const actual = await vi.importActual<typeof import('@/services/imports.service')>(
    '@/services/imports.service',
  );
  return { ...actual, fetchImportJobs, deleteImport };
});

function page(results: ImportJob[], overrides: Partial<{ count: number; next: string | null; previous: string | null }> = {}) {
  return { count: results.length, next: null, previous: null, results, ...overrides };
}

describe('ImportHistoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders every run with its row counts', async () => {
    fetchImportJobs.mockResolvedValue(page([historyJob()]));
    renderWithProviders(<ImportHistoryPage />, { route: '/imports/history' });

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Import history' }),
    ).toBeInTheDocument();
    await screen.findByText('sample_businesses.csv');

    const table = screen.getByRole('table');
    const headers = within(table)
      .getAllByRole('columnheader')
      .map((header) => header.textContent?.trim() ?? '');
    expect(headers).toEqual([
      'File',
      'Status',
      'Rows',
      'Imported',
      'Duplicates',
      'Invalid',
      'Missing e-mail',
      'Started',
      'Duration',
      'Actions',
    ]);

    const row = within(table).getByRole('row', { name: /sample_businesses\.csv/ });
    expect(within(row).getByText('Completed')).toBeInTheDocument();
    expect(within(row).getByText('14')).toBeInTheDocument(); // rows
    expect(within(row).getByText('12')).toBeInTheDocument(); // imported
    // One duplicate, one invalid and one row stored without an address.
    expect(within(row).getAllByText('1')).toHaveLength(3);
  });

  it('shows a failed run with its error message', async () => {
    fetchImportJobs.mockResolvedValue(
      page([
        historyJob({
          id: 40,
          filename: 'broken.csv',
          status: 'FAILED',
          status_display: 'Failed',
          error_message: 'FileNotFoundError: media/imports/40/broken.csv',
          duration_seconds: null,
        }),
      ]),
    );

    renderWithProviders(<ImportHistoryPage />, { route: '/imports/history' });

    const row = await screen.findByRole('row', { name: /broken\.csv/ });
    expect(within(row).getByText('Failed')).toBeInTheDocument();
    expect(within(row).getByText(/FileNotFoundError/)).toBeInTheDocument();
  });

  it('filters by status through the API', async () => {
    fetchImportJobs.mockResolvedValue(page([historyJob()]));
    renderWithProviders(<ImportHistoryPage />, { route: '/imports/history' });
    await screen.findByText('sample_businesses.csv');

    await userEvent.click(screen.getByRole('tab', { name: 'Failed' }));

    await waitFor(() => {
      expect(fetchImportJobs.mock.calls.at(-1)?.[0]?.status).toBe('FAILED');
    });

    await userEvent.click(screen.getByRole('tab', { name: 'All' }));
    await waitFor(() => {
      expect(fetchImportJobs.mock.calls.at(-1)?.[0]?.status).toBeUndefined();
    });
  });

  it('deletes a history entry', async () => {
    fetchImportJobs.mockResolvedValue(page([historyJob()]));
    deleteImport.mockResolvedValue(undefined);
    renderWithProviders(<ImportHistoryPage />, { route: '/imports/history' });
    await screen.findByText('sample_businesses.csv');

    await userEvent.click(screen.getByRole('button', { name: 'Delete sample_businesses.csv' }));

    await waitFor(() => expect(deleteImport).toHaveBeenCalledWith(41));
  });

  it('shows the empty state before the first import', async () => {
    fetchImportJobs.mockResolvedValue(page([]));
    renderWithProviders(<ImportHistoryPage />, { route: '/imports/history' });

    expect(await screen.findByText('No imports yet')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Start an import' })).toHaveAttribute('href', '/imports');
  });

  it('shows an error state when the API fails', async () => {
    fetchImportJobs.mockRejectedValueOnce(new Error('boom'));
    fetchImportJobs.mockResolvedValue(page([historyJob()]));

    renderWithProviders(<ImportHistoryPage />, { route: '/imports/history' });

    expect(await screen.findByText('Could not load the import history')).toBeInTheDocument();
  });
});
