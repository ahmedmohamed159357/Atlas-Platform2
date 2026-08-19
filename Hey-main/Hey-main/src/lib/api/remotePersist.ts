import { logger } from '@utils/logger';
import { hiveGet, hivePost, hivePut, hiveDelete } from './hiveClient';

async function safeGet<T>(path: string, scope: string): Promise<T | null> {
  try {
    const envelope = await hiveGet<T>(path);
    return envelope.data;
  } catch (error) {
    logger.warn(`Backend GET failed for ${scope}`, { error, path }, scope);
    return null;
  }
}

async function safeSave<T>(path: string, value: T, scope: string): Promise<boolean> {
  try {
    await hivePost(path, value);
    return true;
  } catch (error) {
    logger.warn(`Backend save failed for ${scope}`, { error, path }, scope);
    return false;
  }
}

async function safeReplace<T>(path: string, value: T, scope: string): Promise<boolean> {
  try {
    await hivePut(path, value);
    return true;
  } catch (error) {
    logger.warn(`Backend replace failed for ${scope}`, { error, path }, scope);
    return false;
  }
}

async function safeRemove(path: string, scope: string): Promise<boolean> {
  try {
    await hiveDelete(path);
    return true;
  } catch (error) {
    logger.warn(`Backend delete failed for ${scope}`, { error, path }, scope);
    return false;
  }
}

function loadLocal<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch (error) {
    logger.warn(`Failed to parse local storage for ${key}`, { error }, 'remotePersist');
    return fallback;
  }
}

function saveLocal<T>(key: string, value: T, scope: string): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    logger.error(`Failed to persist ${key} to local storage for ${scope}`, error, scope);
  }
}

export async function loadPersistedState<T>(options: {
  apiPath: string;
  storageKey: string;
  fallback: T;
  scope: string;
}): Promise<T> {
  const remote = await safeGet<T>(options.apiPath, options.scope);
  if (remote !== null) return remote;
  return loadLocal(options.storageKey, options.fallback);
}

export async function savePersistedState<T>(options: {
  apiPath: string;
  storageKey: string;
  value: T;
  scope: string;
  usePut?: boolean;
}): Promise<void> {
  const saved = options.usePut
    ? await safeReplace(options.apiPath, options.value, options.scope)
    : await safeSave(options.apiPath, options.value, options.scope);
  if (!saved) {
    saveLocal(options.storageKey, options.value, options.scope);
  }
}

export async function deletePersistedState(options: {
  apiPath: string;
  storageKey: string;
  scope: string;
}): Promise<void> {
  const deleted = await safeRemove(options.apiPath, options.scope);
  if (!deleted) {
    localStorage.removeItem(options.storageKey);
  }
}
