import { Badge, type BadgeTone } from '@/components/ui/Badge';
import type { ImportStatus } from '@/types/import';

const tones: Record<ImportStatus, BadgeTone> = {
  QUEUED: 'info',
  PROCESSING: 'brand',
  COMPLETED: 'success',
  FAILED: 'danger',
};

/** Status pill shared by the import review screen and the history table. */
export function ImportStatusBadge({
  status,
  label,
  dot = true,
}: {
  status: ImportStatus;
  /** Human label from the API (`status_display`). */
  label?: string;
  dot?: boolean;
}) {
  return (
    <Badge tone={tones[status] ?? 'neutral'} dot={dot}>
      {label ?? status}
    </Badge>
  );
}
