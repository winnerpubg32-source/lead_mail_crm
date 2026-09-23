import { FileSpreadsheet, UploadCloud } from 'lucide-react';
import { useRef, useState, type DragEvent, type KeyboardEvent } from 'react';

import { cn } from '@/lib/utils/cn';

/** Extensions the backend accepts (mirrors `parsers.detect_file_type`). */
const ACCEPTED = ['.csv', '.xlsx', '.xlsm'];
const ACCEPT_ATTRIBUTE = '.csv,.xlsx,.xlsm,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

export interface FileDropzoneProps {
  /** Called with a file that passed the client-side extension check. */
  onFile: (file: File) => void;
  /** Disables the zone and shows the upload spinner state. */
  busy?: boolean;
  /** Message shown underneath the zone (server or client validation error). */
  error?: string | null;
  className?: string;
}

function hasAcceptedExtension(name: string): boolean {
  const lower = name.toLowerCase();
  return ACCEPTED.some((extension) => lower.endsWith(extension));
}

/**
 * Drag & drop upload zone.
 *
 * The client-side extension check is a fast fail only — the backend re-detects
 * the type from the file content, so a renamed file is still rejected there.
 */
export function FileDropzone({ onFile, busy = false, error, className }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const accept = (file: File | undefined) => {
    if (!file) return;
    if (!hasAcceptedExtension(file.name)) {
      setLocalError(`“${file.name}” is not a supported file. Upload a .csv, .xlsx or .xlsm file.`);
      return;
    }
    setLocalError(null);
    onFile(file);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    if (busy) return;
    accept(event.dataTransfer.files?.[0]);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      inputRef.current?.click();
    }
  };

  const message = error ?? localError;

  return (
    <div className={className}>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a CSV or XLSX file"
        aria-busy={busy || undefined}
        data-dragging={dragging || undefined}
        onClick={() => !busy && inputRef.current?.click()}
        onKeyDown={handleKeyDown}
        onDragOver={(event) => {
          event.preventDefault();
          if (!busy) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-[var(--radius-card)] border-2 border-dashed px-6 py-12 text-center transition-colors',
          dragging
            ? 'border-brand-400 bg-brand-50/60 dark:bg-brand-500/10'
            : 'border-border-strong bg-surface-2/50 hover:border-brand-300 hover:bg-surface-2',
          busy && 'pointer-events-none opacity-60',
        )}
      >
        <span className="grid size-12 place-items-center rounded-full bg-surface text-brand-600 ring-1 ring-border-subtle ring-inset dark:text-brand-300">
          {busy ? (
            <span
              aria-hidden="true"
              className="size-5 animate-spin rounded-full border-2 border-current border-t-transparent"
            />
          ) : (
            <UploadCloud className="size-6" />
          )}
        </span>

        <div className="space-y-1">
          <p className="text-sm font-semibold text-fg">
            {busy ? 'Uploading and analysing…' : 'Drag & drop your file here'}
          </p>
          <p className="text-[13px] text-muted">
            or <span className="font-medium text-brand-600 dark:text-brand-300">browse</span> to choose a
            CSV or Excel file
          </p>
        </div>

        <p className="flex items-center gap-1.5 text-[12px] text-subtle">
          <FileSpreadsheet className="size-3.5" />
          .csv, .xlsx, .xlsm — up to 100 MB
        </p>

        <input
          ref={inputRef}
          type="file"
          name="file"
          accept={ACCEPT_ATTRIBUTE}
          className="sr-only"
          data-testid="import-file-input"
          onChange={(event) => {
            accept(event.target.files?.[0]);
            event.target.value = '';
          }}
        />
      </div>

      {message ? (
        <p role="alert" className="mt-2 text-[13px] text-rose-600 dark:text-rose-300">
          {message}
        </p>
      ) : null}
    </div>
  );
}
