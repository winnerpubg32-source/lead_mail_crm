import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';
import { ImportsPage } from '@/pages/ImportsPage';
import { historyJob, pendingJob, workbookJob } from '@/test/fixtures/imports';
import { renderWithProviders } from '@/test/renderWithProviders';

const uploadImportFile = vi.hoisted(() => vi.fn());
const fetchImportJob = vi.hoisted(() => vi.fn());
const applyImportMapping = vi.hoisted(() => vi.fn());
const startImport = vi.hoisted(() => vi.fn());
const cancelImport = vi.hoisted(() => vi.fn());
const fetchSystemFields = vi.hoisted(() => vi.fn());

vi.mock('@/services/imports.service', async () => {
  const actual = await vi.importActual<typeof import('@/services/imports.service')>(
    '@/services/imports.service',
  );
  return {
    ...actual,
    uploadImportFile,
    fetchImportJob,
    applyImportMapping,
    startImport,
    cancelImport,
    fetchSystemFields,
  };
});

function csvFile(name = 'sample_businesses.csv'): File {
  return new File(['Business_Name,Contact\nAcme,Jane\n'], name, { type: 'text/csv' });
}

async function uploadThroughDropzone(file = csvFile()) {
  const input = screen.getByTestId('import-file-input');
  await userEvent.upload(input, file);
}

describe('ImportsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchSystemFields.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts with the dropzone and the supported file types', () => {
    renderWithProviders(<ImportsPage />, { route: '/imports' });

    expect(screen.getByRole('heading', { level: 1, name: 'Imports' })).toBeInTheDocument();
    expect(screen.getByText('Drag & drop your file here')).toBeInTheDocument();
    expect(screen.getByText(/\.csv, \.xlsx, \.xlsm — up to 100 MB/)).toBeInTheDocument();
  });

  it('shows file details, preview numbers and the detected mapping after upload', async () => {
    uploadImportFile.mockResolvedValue(pendingJob());
    fetchImportJob.mockResolvedValue(pendingJob());

    renderWithProviders(<ImportsPage />, { route: '/imports' });
    await uploadThroughDropzone();

    // File metadata: name, size, type and the detected row count.
    expect(await screen.findAllByText('sample_businesses.csv')).not.toHaveLength(0);
    expect(screen.getAllByText('12.5 KB').length).toBeGreaterThan(0);
    expect(screen.getByText('CSV', { selector: 'dd' })).toBeInTheDocument();
    expect(screen.getByText('14 data rows')).toBeInTheDocument();

    // The five preview numbers.
    const stats = screen.getByText('Total rows').closest('div.grid') as HTMLElement;
    expect(within(stats).getByText('14')).toBeInTheDocument();
    expect(within(stats).getByText('13')).toBeInTheDocument();
    expect(screen.getByText('Rows with e-mail')).toBeInTheDocument();
    expect(screen.getByText('Rows without e-mail')).toBeInTheDocument();
    expect(screen.getByText('Potential duplicates')).toBeInTheDocument();
    expect(screen.getByText('Invalid e-mails')).toBeInTheDocument();

    // Mapping table: source column → system field, pre-selected from detection.
    expect(screen.getByLabelText('System field for Business_Name')).toHaveValue('company_name');
    expect(screen.getByLabelText('System field for E-mail')).toHaveValue('email');
    expect(screen.getByLabelText('System field for Mobile')).toHaveValue('phone');
    expect(screen.getAllByText('Exact match').length).toBeGreaterThan(0);
    expect(screen.getByText(/Fuzzy · 91%/)).toBeInTheDocument();

    // Preview rows (first 50) plus the action buttons.
    expect(screen.getByText('Dale Kowalski')).toBeInTheDocument();
    expect(screen.getByText(/Showing the first 3 of 14 rows/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Import 14 rows' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('lists the detected sheets of an Excel upload', async () => {
    uploadImportFile.mockResolvedValue(workbookJob());
    fetchImportJob.mockResolvedValue(workbookJob());

    renderWithProviders(<ImportsPage />, { route: '/imports' });
    await uploadThroughDropzone(new File(['x'], 'sample_businesses.xlsx'));

    expect(await screen.findByText('Detected sheets (2)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Leads/ })).toHaveAttribute('aria-pressed', 'true');
    const lookups = screen.getByRole('button', { name: /Lookups/ });
    expect(lookups).toHaveAttribute('aria-pressed', 'false');

    await userEvent.click(lookups);
    await waitFor(() => {
      expect(uploadImportFile).toHaveBeenLastCalledWith(expect.any(File), 'Lookups');
    });
  });

  it('sends manual mapping changes to the API and refreshes the preview', async () => {
    const queued = pendingJob();
    const remapped = pendingJob({
      column_mapping: { ...queued.column_mapping, Town: 'company_name' },
      preview: {
        ...queued.preview,
        mapping: { ...queued.preview.mapping, Town: 'company_name' },
        counts: { ...queued.preview.counts, rows_with_email: 12 },
      },
    });

    let current = queued;
    uploadImportFile.mockResolvedValue(queued);
    fetchImportJob.mockImplementation(() => Promise.resolve(current));
    applyImportMapping.mockImplementation(() => {
      current = remapped;
      return Promise.resolve(remapped);
    });

    renderWithProviders(<ImportsPage />, { route: '/imports' });
    await uploadThroughDropzone();
    await screen.findAllByText('sample_businesses.csv');

    const town = screen.getByLabelText('System field for Town');
    await userEvent.selectOptions(town, 'company_name');
    expect(town).toHaveValue('company_name');

    // The table flags that the change is not applied yet.
    expect(screen.getByText(/Mapping changed — apply it to refresh/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Apply mapping' }));

    await waitFor(() => {
      expect(applyImportMapping).toHaveBeenCalledWith(
        42,
        expect.objectContaining({ Town: 'company_name' }),
      );
    });

    // The recomputed preview replaces the stale numbers and the banner clears.
    const stats = (await screen.findByText('Total rows')).closest('div.grid') as HTMLElement;
    expect(within(stats).getByText('12')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText(/Mapping changed — apply it to refresh/)).toBeNull();
    });

    // "Reset to detected" puts the applied mapping back after a stray edit.
    await userEvent.selectOptions(screen.getByLabelText('System field for Town'), 'city');
    expect(screen.getByText(/Mapping changed — apply it to refresh/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Reset to detected' }));
    expect(screen.getByLabelText('System field for Town')).toHaveValue('company_name');
    expect(screen.queryByText(/Mapping changed — apply it to refresh/)).toBeNull();
  });

  it('prevents importing while the business name column is unmapped', async () => {
    const unmapped = pendingJob({
      column_mapping: { ...pendingJob().column_mapping, Business_Name: null },
    });
    uploadImportFile.mockResolvedValue(unmapped);
    fetchImportJob.mockResolvedValue(unmapped);

    renderWithProviders(<ImportsPage />, { route: '/imports' });
    await uploadThroughDropzone();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /Map a column to “Business name” before importing/,
    );
    expect(screen.getByRole('button', { name: 'Import 14 rows' })).toBeDisabled();
  });

  it('queues the import, shows live progress and finishes on the result screen', async () => {
    const queued = pendingJob();
    const processing = pendingJob({
      status: 'PROCESSING',
      status_display: 'Processing',
      started_at: '2026-09-23T16:01:00Z',
      progress: { processed: 6, total: 14, percent: 43, is_active: true, awaiting_review: false },
      valid_rows: 5,
      duplicate_rows: 1,
    });
    const completed = pendingJob({
      ...historyJob(),
      headers: queued.headers,
      column_mapping: queued.column_mapping,
      preview: queued.preview,
      issues: [],
      error_message: '',
    });

    uploadImportFile.mockResolvedValue(queued);
    startImport.mockResolvedValue({ id: 42, status: 'QUEUED', status_display: 'Queued', dispatch: 'celery' });
    let current = queued;
    fetchImportJob.mockImplementation(() => Promise.resolve(current));

    renderWithProviders(<ImportsPage />, { route: '/imports' });
    await uploadThroughDropzone();
    await screen.findAllByText('sample_businesses.csv');

    current = processing;
    await userEvent.click(screen.getByRole('button', { name: 'Import 14 rows' }));

    expect(startImport).toHaveBeenCalledWith(42, expect.objectContaining({ Business_Name: 'company_name' }));

    // Live progress: percentage, processed counter and the bucket counters.
    expect(await screen.findByText('Importing in the background')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'Import progress' })).toHaveAttribute(
      'aria-valuenow',
      '43',
    );
    const counters = screen.getByText('Imported').closest('dl') as HTMLElement;
    expect(within(counters).getByText('5')).toBeInTheDocument();
    expect(within(counters).getByText('1')).toBeInTheDocument();

    // The poller picks up the completed job.
    current = completed;
    await waitFor(
      () => {
        expect(screen.getByText('Import completed')).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    const headline = screen.getByText('Imported').closest('dl') as HTMLElement;
    for (const label of ['Total', 'Imported', 'Duplicates', 'Invalid', 'Missing email']) {
      expect(within(headline).getByText(label)).toBeInTheDocument();
    }
    expect(within(headline).getByText('12')).toBeInTheDocument(); // imported
    expect(within(headline).getAllByText('1').length).toBeGreaterThan(0); // duplicates + invalid
    expect(screen.getByText('1 row stored without an e-mail address')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Import another file' })).toBeInTheDocument();
  });

  it('cancels an upload after an explicit confirmation', async () => {
    uploadImportFile.mockResolvedValue(pendingJob());
    fetchImportJob.mockResolvedValue(pendingJob());
    cancelImport.mockResolvedValue(undefined);

    renderWithProviders(<ImportsPage />, { route: '/imports' });
    await uploadThroughDropzone();
    await screen.findAllByText('sample_businesses.csv');

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.getByText('Discard this upload and its file?')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Keep it' }));
    expect(screen.queryByText('Discard this upload and its file?')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    await userEvent.click(screen.getByRole('button', { name: 'Yes, discard' }));

    await waitFor(() => expect(cancelImport).toHaveBeenCalledWith(42));
    // Back to the dropzone.
    expect(await screen.findByText('Drag & drop your file here')).toBeInTheDocument();
  });

  it('surfaces the backend message when the file type is rejected', async () => {
    uploadImportFile.mockRejectedValue(
      new ApiError('Request could not be processed.', 400, 'invalid', {
        file: ['Unsupported file type. Upload a .csv, .xlsx or .xlsm file.'],
      }),
    );

    renderWithProviders(<ImportsPage />, { route: '/imports' });
    await uploadThroughDropzone();

    expect(
      await screen.findByText('Unsupported file type. Upload a .csv, .xlsx or .xlsm file.'),
    ).toBeInTheDocument();
  });

  it('refuses unsupported extensions before hitting the API', async () => {
    renderWithProviders(<ImportsPage />, { route: '/imports' });

    // `userEvent.upload` honours the accept attribute, so the change event is
    // fired directly — that is the path a dropped file takes.
    const input = screen.getByTestId('import-file-input');
    fireEvent.change(input, {
      target: { files: [new File(['%PDF'], 'proposal.pdf', { type: 'application/pdf' })] },
    });

    expect(await screen.findByText(/is not a supported file/)).toBeInTheDocument();
    expect(uploadImportFile).not.toHaveBeenCalled();
  });
});
