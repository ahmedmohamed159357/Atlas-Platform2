import { useState, useMemo } from 'react';
import { Panel, Input, Badge } from '@components/shared';
import type { SearchResultItem } from '../types';

export function GlobalSearch({ searchIndex }: { searchIndex: SearchResultItem[] }) {
  const [query, setQuery] = useState('');

  const results = useMemo(
    () => searchIndex.filter((r) => r.label.toLowerCase().includes(query.toLowerCase())),
    [searchIndex, query]
  );

  return (
    <Panel title="Global Search">
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search everything..."
        className="w-full mb-3"
      />
      <ul className="space-y-1 text-sm">
        {results.map((r) => (
          <li key={r.id} className="flex justify-between">
            <span className="text-rk-text">{r.label}</span>
            <Badge>{r.kind}</Badge>
          </li>
        ))}
        {query && results.length === 0 && (
          <li className="text-rk-muted text-xs">No results.</li>
        )}
      </ul>
    </Panel>
  );
}
