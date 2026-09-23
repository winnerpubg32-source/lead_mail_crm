/**
 * Import contracts.
 *
 * These interfaces mirror the DRF serializers in
 * `backend/apps/imports/serializers.py` exactly — field names are kept
 * identical to the API so no mapping layer is needed.
 */

/** Lifecycle of an import run — values match `apps.imports.models.ImportStatus`. */
export type ImportStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

/** Statuses that mean work is still happening (or about to). */
export const ACTIVE_IMPORT_STATUSES: ImportStatus[] = ['QUEUED', 'PROCESSING'];

export type ImportFileType = 'csv' | 'xlsx' | 'xlsm';

/** File-level metadata captured at upload time (`job.uploaded`). */
export interface UploadedFileInfo {
  file_type: ImportFileType | string;
  file_size: number;
  /** Sheet names discovered inside a workbook (empty for CSV). */
  sheets: string[];
  sheet_count: number;
  selected_sheet: string;
  encoding: string;
  delimiter: string;
  /** Data rows detected while sniffing the file, when available. */
  row_count: number;
}

/** `job.progress` — used by the live progress bar. */
export interface ImportProgress {
  processed: number;
  total: number;
  percent: number;
  is_active: boolean;
  /** True while the file is uploaded but not yet confirmed. */
  awaiting_review: boolean;
}

/** `job.summary` — the exact labels shown on the result screen. */
export interface ImportSummary {
  Total: number;
  Imported: number;
  Duplicates: number;
  Invalid: number;
  'Missing Email': number;
  Errors: number;
  'New companies': number;
  'New contacts': number;
}

export type ImportSummaryKey = keyof ImportSummary;

/** How a source column was matched to a system field. */
export type MappingMethod = 'exact' | 'alias' | 'containment' | 'fuzzy' | 'none' | string;

/** One row of the mapping table: SOURCE COLUMN → SYSTEM FIELD. */
export interface MappingColumn {
  column: string;
  /** System field key, or null when the column is ignored. */
  field: string | null;
  label: string;
  method: MappingMethod;
  /** 0–1 score for alias/fuzzy matches. */
  confidence: number;
  matched_on: string;
  hint: string;
}

/** Canonical mapping shape: `{ source column: system field | null }`. */
export type ColumnMapping = Record<string, string | null>;

/** System field catalogue entry (`GET /api/v1/imports/fields/`). */
export interface SystemField {
  key: string;
  label: string;
  description: string;
  group: string;
  required: boolean;
  aliases: string[];
}

export interface ImportIssue {
  row: number;
  level: string;
  message: string;
  column?: string;
}

/** A single previewed data row (first 50 rows of the file). */
export interface PreviewSampleRow {
  row: number;
  values: string[];
  company_name: string;
  contact_name: string;
  email: string;
  phone: string;
  notes: string[];
}

/** The numbers shown before the user confirms the import. */
export interface PreviewCounts {
  total_rows: number;
  rows_with_email: number;
  rows_without_email: number;
  potential_duplicates: number;
  invalid_emails: number;
}

export interface ImportPreview {
  columns: MappingColumn[];
  mapping: ColumnMapping;
  sample_rows: PreviewSampleRow[];
  system_fields: SystemField[];
  counts: PreviewCounts;
  issues: ImportIssue[];
}

/** `GET /api/v1/imports/` row. */
export interface ImportJob {
  id: number;
  filename: string;
  status: ImportStatus;
  status_display: string;
  /** Populated when a run fails (shown in the history table). */
  error_message?: string;
  file_type: ImportFileType | string;
  file_size: number;
  uploaded: UploadedFileInfo;
  progress: ImportProgress;
  summary: ImportSummary;
  total_rows: number;
  processed_rows: number;
  valid_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  error_rows: number;
  missing_email_rows: number;
  new_companies: number;
  new_contacts: number;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  created_at: string;
  updated_at: string;
}

/** `GET /api/v1/imports/{id}/` — adds the preview, headers and mapping. */
export interface ImportJobDetail extends ImportJob {
  headers: string[];
  column_mapping: ColumnMapping;
  preview: ImportPreview;
  issues: ImportIssue[];
  error_message?: string;
}

/**
 * Query parameters accepted by the history endpoint.
 *
 * Indexed so the object can be handed straight to the query-string builder.
 */
export interface ImportListParams {
  [param: string]: string | number | boolean | undefined;
  page?: number;
  page_size?: number;
  search?: string;
  ordering?: string;
  status?: string;
  file_type?: string;
  with_errors?: string;
}

/** True while the job is queued or processing. */
export function isActiveStatus(status: ImportStatus | undefined): boolean {
  return status === 'QUEUED' || status === 'PROCESSING';
}

/** True when the job is waiting for the user to confirm the mapping. */
export function isAwaitingReview(job: Pick<ImportJob, 'status' | 'progress'> | undefined): boolean {
  return Boolean(job && job.status === 'QUEUED' && job.progress?.awaiting_review);
}
