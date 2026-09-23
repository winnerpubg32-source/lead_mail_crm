import { AlertTriangle } from 'lucide-react';

import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import { cn } from '@/lib/utils/cn';
import type { PreviewSampleRow } from '@/types/import';

export interface PreviewTableProps {
  /** Source headers — the columns are shown exactly as they appear in the file. */
  headers: string[];
  rows: PreviewSampleRow[];
  /** How many rows the file has in total (the preview is capped at 50). */
  totalRows: number;
}

/** First 50 rows of the uploaded file, as they will be read. */
export function PreviewTable({ headers, rows, totalRows }: PreviewTableProps) {
  return (
    <div>
      <TableWrapper>
        <Table>
          <THead>
            <TR>
              <TH className="w-14 text-right">#</TH>
              {headers.map((header, index) => (
                <TH key={`${header}-${index}`} className="min-w-[150px]">
                  {header}
                </TH>
              ))}
              <TH className="min-w-[120px]">Row notes</TH>
            </TR>
          </THead>
          <TBody>
            {rows.map((row) => (
              <TR key={row.row}>
                <TD className="tabular text-right text-[12px] text-subtle">{row.row}</TD>
                {headers.map((header, index) => {
                  const value = row.values[index] ?? '';
                  return (
                    <TD
                      key={`${row.row}-${header}-${index}`}
                      className={cn('max-w-[260px] truncate text-[12.5px]', value ? 'text-fg' : 'text-subtle')}
                      title={value || undefined}
                    >
                      {value || '—'}
                    </TD>
                  );
                })}
                <TD>
                  {row.notes.length === 0 ? (
                    <span className="text-[12px] text-subtle">—</span>
                  ) : (
                    <span
                      className="inline-flex items-center gap-1.5 text-[12px] text-amber-700 dark:text-amber-300"
                      title={row.notes.join(' · ')}
                    >
                      <AlertTriangle className="size-3.5 shrink-0" />
                      {row.notes[0]}
                    </span>
                  )}
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </TableWrapper>

      <p className="border-t border-border-subtle px-5 py-2.5 text-[12.5px] text-subtle">
        Showing the first {rows.length} of {totalRows} row{totalRows === 1 ? '' : 's'} — the full file is
        processed in the background.
      </p>
    </div>
  );
}
