import { rankEntries } from './domain';
import type { RankingEntry } from './types';

interface RankingDashboardProps {
  entries: readonly RankingEntry[];
}

export function RankingDashboard({ entries }: RankingDashboardProps) {
  const rankedEntries = rankEntries(entries);

  return (
    <section className="space-y-4" aria-labelledby="ranking-title">
      <div>
        <p className="text-xs uppercase tracking-wide text-rk-muted">Optional plugin</p>
        <h1 id="ranking-title" className="text-2xl font-semibold text-rk-text">
          Ranking Dashboard
        </h1>
      </div>
      <ol className="divide-y divide-rk-border rounded-md border border-rk-border bg-rk-surface">
        {rankedEntries.map((entry, index) => (
          <li key={entry.id} className="flex items-center justify-between gap-4 px-4 py-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-rk-text">
                {index + 1}. {entry.name}
              </p>
              {entry.category && <p className="text-xs text-rk-muted">{entry.category}</p>}
            </div>
            <span className="shrink-0 text-sm font-semibold text-rk-accent">{entry.score}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
