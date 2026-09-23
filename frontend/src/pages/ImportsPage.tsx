import { AlertTriangle, CheckCircle2, History, Info, Sparkles, Upload } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { ErrorState } from '@/components/feedback/ErrorState';
import { LoadingState } from '@/components/feedback/LoadingState';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader } from '@/components/ui/Card';
import { buttonVariants } from '@/components/ui/button-variants';
import { FileDropzone } from '@/features/imports/components/FileDropzone';
import { FileSummaryCard } from '@/features/imports/components/FileSummaryCard';
import { ImportProgressCard } from '@/features/imports/components/ImportProgressCard';
import { ImportResultCard } from '@/features/imports/components/ImportResultCard';
import { MappingTable } from '@/features/imports/components/MappingTable';
import { PreviewStats } from '@/features/imports/components/PreviewStats';
import { PreviewTable } from '@/features/imports/components/PreviewTable';
import {
  useApplyMapping,
  useCancelImport,
  useImportJob,
  useStartImport,
  useSystemFields,
  useUploadImport,
} from '@/hooks/useImports';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { apiErrorMessage } from '@/lib/api/errors';
import { formatNumber } from '@/lib/utils/format';
import { paths } from '@/routes/paths';
import type { ColumnMapping } from '@/types/import';

type Stage = 'idle' | 'review' | 'running' | 'done' | 'failed';

/** The steps shown on the empty screen — sets expectations before uploading. */
const STEPS = [
  {
    icon: Upload,
    title: '1 · Upload',
    body: 'Drop a CSV or Excel file. The file type, sheet list and row count are detected automatically.',
  },
  {
    icon: Sparkles,
    title: '2 · Review',
    body: 'Columns are matched to system fields by name, aliases and fuzzy matching — never by exact spelling only. Correct anything by hand.',
  },
  {
    icon: CheckCircle2,
    title: '3 · Import',
    body: 'Large files are processed in the background in chunks. Duplicates are merged, invalid e-mails are dropped, rows without an address are still stored.',
  },
];

/**
 * Imports — CSV/XLSX ingestion with column mapping, preview and background
 * processing (`/api/v1/imports/`).
 */
export function ImportsPage() {
  useDocumentTitle('Imports');

  const [jobId, setJobId] = useState<number | null>(null);
  /** The File object kept around so a different sheet can be analysed. */
  const [file, setFile] = useState<File | null>(null);
  /**
   * Hand edits to the detected mapping — `null` means "whatever the analysis
   * detected". Keeping only the override in state means an applied mapping is
   * adopted from the server response instead of being copied around.
   */
  const [mappingOverride, setMappingOverride] = useState<ColumnMapping | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [cancelArmed, setCancelArmed] = useState(false);

  const systemFields = useSystemFields();
  const upload = useUploadImport();
  const applyMapping = useApplyMapping(jobId);
  const startImport = useStartImport(jobId);
  const cancelImport = useCancelImport();

  const jobQuery = useImportJob(jobId, { poll: submitted });
  const job = jobQuery.data;

  const detectedMapping = job?.column_mapping ?? {};
  const mapping = mappingOverride ?? detectedMapping;

  // A job that was already handed to the worker (or re-opened mid-run) must not
  // fall back to the review screen.
  const started = submitted || Boolean(job && !job.progress.awaiting_review);

  const stage: Stage = useMemo(() => {
    if (jobId === null) return 'idle';
    if (!job) return 'review';
    if (job.status === 'COMPLETED') return 'done';
    if (job.status === 'FAILED') return 'failed';
    if (job.status === 'PROCESSING') return 'running';
    return started ? 'running' : 'review';
  }, [jobId, job, started]);

  const mappingDirty =
    mappingOverride !== null &&
    Object.keys({ ...detectedMapping, ...mappingOverride }).some(
      (column) => (mappingOverride[column] ?? null) !== (detectedMapping[column] ?? null),
    );
  const companyMapped = Object.values(mapping).includes('company_name');

  const reset = () => {
    setJobId(null);
    setFile(null);
    setMappingOverride(null);
    setSubmitted(false);
    setCancelArmed(false);
    upload.reset();
    startImport.reset();
  };

  const handleFile = async (selected: File) => {
    setFile(selected);
    try {
      const uploaded = await upload.mutateAsync({ file: selected });
      setMappingOverride(null);
      setSubmitted(false);
      setJobId(uploaded.id);
    } catch {
      setFile(null);
    }
  };

  const switchSheet = async (sheet: string) => {
    if (!file) return;
    try {
      const uploaded = await upload.mutateAsync({ file, sheet });
      setMappingOverride(null);
      setSubmitted(false);
      setJobId(uploaded.id);
    } catch {
      /* the error shows up under the dropzone on the next upload attempt */
    }
  };

  const handleCancel = async () => {
    if (jobId === null) return;
    try {
      await cancelImport.mutateAsync(jobId);
    } finally {
      reset();
    }
  };

  const handleStart = async () => {
    if (jobId === null) return;
    // Always send the mapping on screen: an unapplied edit still takes effect.
    await startImport.mutateAsync(mapping);
    setSubmitted(true);
  };

  const uploadError = upload.isError
    ? apiErrorMessage(upload.error, ['file', 'sheet'], 'The file could not be analysed.')
    : null;

  return (
    <div>
      <PageHeader
        eyebrow="Lead database"
        title="Imports"
        description="Ingest CSV and Excel datasets into the lead database. Columns are mapped automatically, the preview shows exactly what will be stored, and large files are processed in the background."
        actions={
          <Link to={paths.importsHistory} className={buttonVariants({ variant: 'outline', size: 'sm' })}>
            <History className="mr-1.5 size-3.5" />
            Import history
          </Link>
        }
      />

      {stage === 'idle' ? (
        <div className="space-y-4">
          <Card className="p-5">
            <FileDropzone
              onFile={(selected) => void handleFile(selected)}
              busy={upload.isPending}
              error={uploadError}
            />
          </Card>

          <div className="grid gap-3 md:grid-cols-3">
            {STEPS.map((step) => (
              <Card key={step.title} className="p-4">
                <div className="flex items-center gap-2 text-brand-600 dark:text-brand-300">
                  <step.icon className="size-4" />
                  <p className="text-[13px] font-semibold text-fg">{step.title}</p>
                </div>
                <p className="mt-2 text-[12.5px] text-muted">{step.body}</p>
              </Card>
            ))}
          </div>
        </div>
      ) : null}

      {stage !== 'idle' && job === undefined && jobQuery.isPending ? (
        <Card className="mt-1">
          <LoadingState label="Analysing file…" />
        </Card>
      ) : null}

      {stage !== 'idle' && jobQuery.isError && !job ? (
        <Card className="mt-1 p-5">
          <ErrorState
            title="Could not load this import"
            description="The import job could not be read from the API. It may have been discarded."
            details={jobQuery.error instanceof Error ? jobQuery.error.message : undefined}
            action={
              <Button variant="outline" size="sm" onClick={reset}>
                Start over
              </Button>
            }
          />
        </Card>
      ) : null}

      {stage === 'review' && job ? (
        <div className="space-y-4">
          <FileSummaryCard
            job={job}
            onSelectSheet={(sheet) => void switchSheet(sheet)}
            switchingSheet={upload.isPending}
          />

          <PreviewStats counts={job.preview.counts} />

          <Card className="overflow-hidden">
            <CardHeader
              title="Column mapping"
              description="Source column → system field. Detection uses normalised names, a synonym list and fuzzy matching, so “Business Name”, “Company” or “Organisation” all land in the same field."
              action={
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={!mappingDirty || applyMapping.isPending}
                    onClick={() => setMappingOverride(null)}
                  >
                    Reset to detected
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    isLoading={applyMapping.isPending}
                    disabled={!mappingDirty}
                    onClick={() => void applyMapping.mutateAsync(mapping).then(() => setMappingOverride(null))}
                  >
                    Apply mapping
                  </Button>
                </>
              }
            />
            {mappingDirty ? (
              <p className="flex items-center gap-2 border-b border-border-subtle bg-amber-50/70 px-5 py-2.5 text-[12.5px] text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
                <Info className="size-3.5 shrink-0" />
                Mapping changed — apply it to refresh the preview numbers below. Importing uses the
                mapping shown here either way.
              </p>
            ) : null}
            {applyMapping.isError ? (
              <div className="px-5 py-3">
                <ErrorState
                  title="Mapping not accepted"
                  description={apiErrorMessage(applyMapping.error, ['column_mapping'], 'The mapping could not be saved.')}
                />
              </div>
            ) : null}
            <MappingTable
              columns={job.preview.columns}
              systemFields={job.preview.system_fields.length ? job.preview.system_fields : systemFields.data ?? []}
              mapping={mapping}
              onChange={(column, field) => setMappingOverride({ ...mapping, [column]: field })}
            />
          </Card>

          <Card className="overflow-hidden">
            <CardHeader
              title="Preview"
              description={`First ${Math.min(50, job.preview.sample_rows.length)} rows of ${formatNumber(job.total_rows)}`}
            />
            <PreviewTable
              headers={job.headers}
              rows={job.preview.sample_rows}
              totalRows={job.total_rows}
            />
          </Card>

          {startImport.isError ? (
            <ErrorState
              title="Import could not start"
              description={apiErrorMessage(
                startImport.error,
                ['column_mapping', 'error'],
                'The import could not be queued.',
              )}
            />
          ) : null}

          <Card className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
            <div className="text-[12.5px] text-muted">
              {cancelArmed ? (
                <span className="flex items-center gap-1.5 text-rose-600 dark:text-rose-300">
                  <AlertTriangle className="size-3.5" />
                  Discard this upload and its file?
                </span>
              ) : (
                <>
                  Nothing is written until you press import.{' '}
                  <span className="text-subtle">
                    {formatNumber(job.preview.counts.total_rows)} rows will be processed.
                  </span>
                </>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {cancelArmed ? (
                <>
                  <Button variant="outline" size="sm" onClick={() => setCancelArmed(false)}>
                    Keep it
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    isLoading={cancelImport.isPending}
                    onClick={() => void handleCancel()}
                  >
                    Yes, discard
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="ghost" size="sm" onClick={() => setCancelArmed(true)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={() => void handleStart()}
                    isLoading={startImport.isPending}
                    disabled={!companyMapped}
                    title={companyMapped ? undefined : 'Map a column to “Business name” first'}
                  >
                    Import {formatNumber(job.preview.counts.total_rows)} rows
                  </Button>
                </>
              )}
            </div>
          </Card>
        </div>
      ) : null}

      {stage === 'running' && job ? (
        <div className="space-y-4">
          <ImportProgressCard job={job} />
          {job.status === 'QUEUED' ? (
            <Card className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
              <p className="text-[12.5px] text-muted">
                The job has been handed to the queue. It can still be cancelled before processing starts.
              </p>
              <Button
                variant="outline"
                size="sm"
                isLoading={cancelImport.isPending}
                onClick={() => void handleCancel()}
              >
                Cancel import
              </Button>
            </Card>
          ) : null}
        </div>
      ) : null}

      {stage === 'done' && job ? <ImportResultCard job={job} onStartOver={reset} /> : null}

      {stage === 'failed' && job ? (
        <Card className="p-5">
          <ErrorState
            title="Import failed"
            description={job.error_message || 'The worker could not process this file.'}
            action={
              <div className="flex flex-wrap items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  isLoading={startImport.isPending}
                  onClick={() => void handleStart()}
                >
                  Try again
                </Button>
                <Button variant="ghost" size="sm" onClick={reset}>
                  Start over
                </Button>
              </div>
            }
          />
        </Card>
      ) : null}
    </div>
  );
}
