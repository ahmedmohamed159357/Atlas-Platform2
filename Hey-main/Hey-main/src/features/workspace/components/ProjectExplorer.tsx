import { Panel } from '@components/shared/Panel';
import type { ProjectFileNode } from '../types';

export function ProjectExplorer({ projectTree }: { projectTree: ProjectFileNode[] }) {

  return (
    <Panel title="Project Explorer">
      <ul className="text-sm space-y-1">
        {projectTree.map((node) => (
          <li key={node.id}>
            <span className="text-rk-text">📁 {node.name}</span>
            {node.children && (
              <ul className="ms-4 mt-1 space-y-1">
                {node.children.map((c) => (
                  <li key={c.id} className="text-rk-muted">
                    {c.type === 'folder' ? '📁' : '📄'} {c.name}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
