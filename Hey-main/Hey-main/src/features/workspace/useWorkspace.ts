import { useEffect, useState } from 'react';
import { logger } from '@utils/logger';
import { loadFeatureDataRemote, saveFeatureData } from '@/lib/api/storageAdapter';
import { mockFavorites, mockProjectTree, mockRecent, mockSearchResults } from './data.mock';
import type {
  FavoriteItem,
  ProjectFileNode,
  RecentActivityItem,
  SearchResultItem,
  WorkspaceNoteItem,
} from './types';

const STORAGE_KEY = 'red_king.workspace.v1';

interface WorkspaceState {
  projectTree: ProjectFileNode[];
  favorites: FavoriteItem[];
  recentActivity: RecentActivityItem[];
  searchIndex: SearchResultItem[];
  notes: WorkspaceNoteItem[];
}

function defaultState(): WorkspaceState {
  return {
    projectTree: mockProjectTree,
    favorites: mockFavorites,
    recentActivity: mockRecent,
    searchIndex: mockSearchResults,
    notes: [
      {
        id: 'note-seed-1',
        text: 'First note — مجرد مثال محلي.',
        createdAt: new Date().toISOString(),
      },
    ],
  };
}

function loadState(): WorkspaceState {
  const seed = defaultState();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return seed;

    const parsed = JSON.parse(raw) as Partial<WorkspaceState>;
    return {
      projectTree:
        Array.isArray(parsed.projectTree) && parsed.projectTree.length > 0
          ? parsed.projectTree
          : seed.projectTree,
      favorites: Array.isArray(parsed.favorites) ? parsed.favorites : seed.favorites,
      recentActivity: Array.isArray(parsed.recentActivity) ? parsed.recentActivity : seed.recentActivity,
      searchIndex:
        Array.isArray(parsed.searchIndex) && parsed.searchIndex.length > 0
          ? parsed.searchIndex
          : seed.searchIndex,
      notes: Array.isArray(parsed.notes) ? parsed.notes : seed.notes,
    };
  } catch (error) {
    logger.warn('Failed to read workspace state from Local Storage — falling back to defaults', { error }, 'workspace');
    return seed;
  }
}

function saveState(state: WorkspaceState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    logger.error('Failed to persist workspace state to Local Storage', error, 'workspace');
  }
}

/**
 * Hook responsible for the workspace domain data with the established storage adapter.
 * Remote persistence is the primary path; local storage remains the safe fallback.
 */
export function useWorkspace() {
  const [state, setState] = useState<WorkspaceState>(defaultState);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    void loadFeatureDataRemote<WorkspaceState>(STORAGE_KEY, defaultState(), 'workspace').then((value) => {
      if (!isMounted) return;
      setState(value);
      setIsLoading(false);
    }).catch((error) => {
      logger.warn('Failed to hydrate workspace from remote storage — falling back to local state', { error }, 'workspace');
      if (isMounted) {
        setState(loadState());
        setIsLoading(false);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (isLoading) return;
    void saveFeatureData(STORAGE_KEY, state, 'workspace');
    saveState(state);
  }, [state, isLoading]);

  const addNote = (text: string): void => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const note: WorkspaceNoteItem = {
      id: `wnote-${Date.now()}`,
      text: trimmed,
      createdAt: new Date().toISOString(),
    };
    setState((prev) => ({ ...prev, notes: [note, ...prev.notes] }));
  };

  return {
    projectTree: state.projectTree,
    favorites: state.favorites,
    recentActivity: state.recentActivity,
    searchIndex: state.searchIndex,
    notes: state.notes,
    isLoading,
    addNote,
  };
}

export type WorkspaceController = ReturnType<typeof useWorkspace>;
