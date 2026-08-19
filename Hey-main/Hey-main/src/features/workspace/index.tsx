import { ProjectExplorer } from './components/ProjectExplorer';
import { NotesPanel } from './components/NotesPanel';
import { FavoritesPanel } from './components/FavoritesPanel';
import { RecentActivityPanel } from './components/RecentActivityPanel';
import { QuickActions } from './components/QuickActions';
import { GlobalSearch } from './components/GlobalSearch';
import { PageHeader } from '@components/shared/PageHeader';
import { registerPlugin } from '@plugins-core';
import { useWorkspace } from './useWorkspace';

registerPlugin({ id: 'workspace', name: 'Developer Workspace', version: '0.1.0', slot: 'main' });

export function WorkspacePage() {
  const workspace = useWorkspace();

  return (
    <div>
      <PageHeader title="Workspace" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-4">
          <ProjectExplorer projectTree={workspace.projectTree} />
          <FavoritesPanel favorites={workspace.favorites} />
        </div>
        <div className="space-y-4">
          <GlobalSearch searchIndex={workspace.searchIndex} />
          <QuickActions />
        </div>
        <div className="space-y-4">
          <NotesPanel notes={workspace.notes} addNote={workspace.addNote} />
          <RecentActivityPanel recentActivity={workspace.recentActivity} />
        </div>
      </div>
    </div>
  );
}
