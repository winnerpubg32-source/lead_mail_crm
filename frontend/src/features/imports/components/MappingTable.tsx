import { AlertTriangle, Check, Sparkles, Wand2 } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Select } from '@/components/ui/Select';
import { Table, TableWrapper, TBody, TD, TH, THead, TR } from '@/components/ui/Table';
import { cn } from '@/lib/utils/cn';
import type { ColumnMapping, MappingColumn, SystemField } from '@/types/import';

const GROUP_LABELS: Record<string, string> = {
  company: 'Company',
  contact: 'Contact',
  meta: 'Other',
};

const IGNORE = '__ignore__';

/** How the current value got there — shown as a small badge per row. */
function MethodBadge({ column, field, detected }: { column: MappingColumn; field: string | null; detected: string | null }) {
  if (field === null) {
    return (
      <Badge tone="neutral" size="sm">
        Ignored
      </Badge>
    );
  }
  if (field !== detected) {
    return (
      <Badge tone="violet" size="sm" className="gap-1">
        <Wand2 className="size-3" />
        Manual
      </Badge>
    );
  }
  if (column.method === 'exact') {
    return (
      <Badge tone="success" size="sm" className="gap-1">
        <Check className="size-3" />
        Exact match
      </Badge>
    );
  }
  if (column.method === 'alias' || column.method === 'containment') {
    return (
      <Badge tone="brand" size="sm" className="gap-1">
        <Check className="size-3" />
        Alias match
        {column.confidence > 0 && column.confidence < 1 ? ` · ${Math.round(column.confidence * 100)}%` : ''}
      </Badge>
    );
  }
  if (column.method === 'fuzzy') {
    return (
      <Badge tone="warning" size="sm" className="gap-1">
        <Sparkles className="size-3" />
        Fuzzy · {Math.round(column.confidence * 100)}%
      </Badge>
    );
  }
  return (
    <Badge tone="info" size="sm">
      Detected
    </Badge>
  );
}

export interface MappingTableProps {
  columns: MappingColumn[];
  systemFields: SystemField[];
  /** Current (possibly hand-edited) mapping — source column to system field. */
  mapping: ColumnMapping;
  onChange: (column: string, field: string | null) => void;
}

/**
 * SOURCE COLUMN → SYSTEM FIELD table.
 *
 * Detection never depends on exact column names: each row shows how the column
 * was recognised (exact, alias or fuzzy) and every field can be overridden.
 */
export function MappingTable({ columns, systemFields, mapping, onChange }: MappingTableProps) {
  const grouped = systemFields.reduce<Record<string, SystemField[]>>((accumulator, field) => {
    (accumulator[field.group] ??= []).push(field);
    return accumulator;
  }, {});

  const usage = new Map<string, number>();
  for (const field of Object.values(mapping)) {
    if (field) usage.set(field, (usage.get(field) ?? 0) + 1);
  }

  const missingRequired = systemFields
    .filter((field) => field.required)
    .filter((field) => !Object.values(mapping).includes(field.key));

  return (
    <div>
      {missingRequired.length > 0 ? (
        <div
          role="alert"
          className="flex items-start gap-2 border-b border-amber-200 bg-amber-50/70 px-5 py-3 text-[13px] text-amber-800 dark:border-amber-500/25 dark:bg-amber-500/10 dark:text-amber-200"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <p>
            Map a column to{' '}
            <span className="font-semibold">
              {missingRequired.map((field) => `“${field.label}”`).join(', ')}
            </span>{' '}
            before importing — rows without it are rejected.
          </p>
        </div>
      ) : null}

      <TableWrapper>
        <Table>
          <THead>
            <TR>
              <TH className="min-w-[220px]">Source column</TH>
              <TH className="min-w-[160px]">Detection</TH>
              <TH className="min-w-[260px]">System field</TH>
            </TR>
          </THead>
          <TBody>
            {columns.map((column) => {
              const field = mapping[column.column] ?? null;
              const duplicate = field !== null && (usage.get(field) ?? 0) > 1;

              return (
                <TR key={column.column}>
                  <TD>
                    <p className="font-mono text-[12.5px] text-fg">{column.column}</p>
                    {column.matched_on ? (
                      <p className="mt-0.5 text-[11.5px] text-subtle">matched “{column.matched_on}”</p>
                    ) : (
                      <p className="mt-0.5 text-[11.5px] text-subtle">no match found — pick a field</p>
                    )}
                  </TD>

                  <TD>
                    <MethodBadge column={column} field={field} detected={column.field} />
                  </TD>

                  <TD>
                    <div className="flex items-center gap-2">
                      <Select
                        selectSize="sm"
                        aria-label={`System field for ${column.column}`}
                        value={field ?? IGNORE}
                        onChange={(event) =>
                          onChange(column.column, event.target.value === IGNORE ? null : event.target.value)
                        }
                        className={cn(duplicate && 'border-amber-400')}
                      >
                        <option value={IGNORE}>— Ignore this column —</option>
                        {Object.entries(grouped).map(([group, fields]) => (
                          <optgroup key={group} label={GROUP_LABELS[group] ?? group}>
                            {fields.map((entry) => (
                              <option key={entry.key} value={entry.key}>
                                {entry.label}
                                {entry.required ? ' *' : ''}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </Select>
                      {duplicate ? (
                        <span
                          className="text-amber-600 dark:text-amber-400"
                          title="Another column already maps to this field — the last value wins"
                        >
                          <AlertTriangle className="size-4" />
                        </span>
                      ) : null}
                    </div>
                  </TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      </TableWrapper>
    </div>
  );
}
