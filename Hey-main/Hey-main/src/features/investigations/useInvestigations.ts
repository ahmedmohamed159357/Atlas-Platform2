import { useEffect, useState } from 'react';
import { logger } from '@utils/logger';
import { loadFeatureDataRemote, saveFeatureData } from '@/lib/api/storageAdapter';
import { mockEvidence, mockInvestigations, mockTimeline } from './data.mock';
import type { Evidence, Investigation, TimelineEvent } from './types';

const STORAGE_KEY = 'red_king.investigations.v1';

interface InvestigationsState {
  investigations: Investigation[];
  timeline: TimelineEvent[];
  evidence: Evidence[];
}

function defaultState(): InvestigationsState {
  return {
    investigations: mockInvestigations,
    timeline: mockTimeline,
    evidence: mockEvidence,
  };
}

function loadState(): InvestigationsState {
  const seed = defaultState();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return seed;

    const parsed = JSON.parse(raw) as Partial<InvestigationsState>;
    return {
      investigations:
        Array.isArray(parsed.investigations) && parsed.investigations.length > 0
          ? parsed.investigations
          : seed.investigations,
      timeline: Array.isArray(parsed.timeline) ? parsed.timeline : seed.timeline,
      evidence: Array.isArray(parsed.evidence) ? parsed.evidence : seed.evidence,
    };
  } catch (error) {
    logger.warn(
      'Failed to read investigations from Local Storage — falling back to defaults',
      { error },
      'investigations'
    );
    return seed;
  }
}

function saveState(state: InvestigationsState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    logger.error('Failed to persist investigations to Local Storage', error, 'investigations');
  }
}

export function useInvestigations() {
  const [state, setState] = useState<InvestigationsState>(defaultState());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    void loadFeatureDataRemote<InvestigationsState>(STORAGE_KEY, defaultState(), 'investigations').then((value) => {
      if (!isMounted) return;
      setState(value);
      setIsLoading(false);
    }).catch((error) => {
      logger.warn('Failed to hydrate investigations from remote storage — falling back to local state', { error }, 'investigations');
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
    void saveFeatureData(STORAGE_KEY, state, 'investigations');
    saveState(state);
  }, [state, isLoading]);

  return {
    investigations: state.investigations,
    timeline: state.timeline,
    evidence: state.evidence,
    isLoading,
  };
}
