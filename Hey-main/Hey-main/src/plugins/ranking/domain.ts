import type { RankingEntry } from './types';

export function rankEntries(entries: readonly RankingEntry[]): RankingEntry[] {
    return [...entries].sort((left, right) => right.score - left.score || left.name.localeCompare(right.name));
}
