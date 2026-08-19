import { Panel } from '@components/shared/Panel';
import type { FavoriteItem } from '../types';

export function FavoritesPanel({ favorites }: { favorites: FavoriteItem[] }) {

  return (
    <Panel title="Favorites">
      <ul className="space-y-1 text-sm">
        {favorites.map((f) => (
          <li key={f.id} className="text-rk-text hover:text-rk-accent cursor-pointer">
            ⭐ {f.label}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
