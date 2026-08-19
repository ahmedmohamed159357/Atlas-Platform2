import { Panel } from '@components/shared/Panel';
import type { RecentActivityItem } from '../types';

export function RecentActivityPanel({ recentActivity }: { recentActivity: RecentActivityItem[] }) {

  return (
    <Panel title="Recent Activity">
      <ul className="space-y-2 text-sm">
        {recentActivity.map((r) => (
          <li key={r.id} className="flex justify-between">
            <span className="text-rk-text">{r.label}</span>
            <span className="text-rk-muted text-xs">{r.time}</span>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
