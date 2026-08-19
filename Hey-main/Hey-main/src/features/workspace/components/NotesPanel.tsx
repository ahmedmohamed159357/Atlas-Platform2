import { useState } from 'react';
import { Panel, Input, Button } from '@components/shared';
import type { WorkspaceNoteItem } from '../types';

export function NotesPanel({ notes, addNote }: { notes: WorkspaceNoteItem[]; addNote: (text: string) => void }) {
  const [draft, setDraft] = useState('');

  const handleAdd = () => {
    if (!draft.trim()) return;
    addNote(draft);
    setDraft('');
  };

  return (
    <Panel title="Notes">
      <div className="flex gap-2 mb-3">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add a note..."
          className="flex-1"
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
        />
        <Button onClick={handleAdd}>Add</Button>
      </div>
      <ul className="space-y-2 text-sm">
        {notes.map((n) => (
          <li key={n.id} className="text-rk-text border-s-2 border-rk-border ps-2">
            {n.text}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
