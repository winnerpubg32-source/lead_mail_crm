import { useState } from 'react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { formatDateTime, formatRelativeTime } from '@/lib/utils/format';
import type { LeadNote } from '@/types/lead';

interface Props {
  notes?: LeadNote[];
  onAdd: (body: string) => void;
  isAdding?: boolean;
}

export function NotesPanel({ notes, onAdd, isAdding }: Props) {
  const [body, setBody] = useState('');
  const submit = () => {
    if (!body.trim()) return;
    onAdd(body.trim());
    setBody('');
  };
  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-fg">Notes</h3>
        <span className="text-[11px] text-subtle">{notes?.length ?? 0} note(s)</span>
      </div>
      <div className="mb-3">
        <Textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Add a note about this lead (context, next step, call notes)…"
          rows={3}
        />
        <div className="mt-2 flex justify-end">
          <Button size="sm" onClick={submit} disabled={!body.trim() || isAdding} isLoading={isAdding}>
            Add note
          </Button>
        </div>
      </div>
      <ul className="space-y-3">
        {(notes ?? []).map((note) => (
          <li key={note.id} className="rounded-lg border border-border-subtle bg-surface-1 p-3">
            <p className="whitespace-pre-wrap text-[13px] text-fg">{note.body}</p>
            <p
              className="mt-1 text-[11px] text-subtle"
              title={formatDateTime(note.created_at)}
            >
              {note.author_display ?? 'System'} · {formatRelativeTime(note.created_at)}
            </p>
          </li>
        ))}
      </ul>
    </Card>
  );
}
