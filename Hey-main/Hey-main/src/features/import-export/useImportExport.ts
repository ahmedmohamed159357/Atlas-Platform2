import { useEffect, useMemo, useState } from 'react';
import { logger } from '@utils/logger';
import {
  mockBackupHistory,
  mockImportPreview,
  mockModules,
  mockValidationChecks,
} from './data.mock';
import type { BackupEntry, ImportPreviewItem, ModuleOption, OperationStatus, ValidationCheck } from './types';

const MODULES_STORAGE_KEY = 'red_king.import_export.modules.v1';
const BACKUP_HISTORY_STORAGE_KEY = 'red_king.import_export.backup_history.v1';
const IMPORT_PREVIEW_STORAGE_KEY = 'red_king.import_export.import_preview.v1';
const VALIDATION_CHECKS_STORAGE_KEY = 'red_king.import_export.validation_checks.v1';
const BACKUP_DATA_PREFIX = 'red_king.backup.data.';
const PROGRESS_STEP_MS = 180;

interface BackupPayload {
  version: 1;
  createdAt: string;
  modules: Record<string, unknown>;
}

function createBackupPayload(): BackupPayload {
  const modules: Record<string, unknown> = {};
  for (let index = 0; index < localStorage.length; index += 1) {
    const key = localStorage.key(index);
    if (!key || !key.startsWith('red_king.') || key.startsWith(BACKUP_DATA_PREFIX)) continue;
    const raw = localStorage.getItem(key);
    if (raw === null) continue;
    modules[key] = JSON.parse(raw);
  }
  return { version: 1, createdAt: new Date().toISOString(), modules };
}

function downloadBackup(payload: BackupPayload, fileName: string): void {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}

function restoreBackup(raw: string): boolean {
  const parsed = JSON.parse(raw) as Partial<BackupPayload>;
  if (parsed.version !== 1 || !parsed.modules || typeof parsed.modules !== 'object' || Array.isArray(parsed.modules)) {
    throw new Error('Invalid backup format');
  }

  const entries = Object.entries(parsed.modules);
  if (entries.some(([key, value]) => !key.startsWith('red_king.') || key.startsWith(BACKUP_DATA_PREFIX) || value === undefined)) {
    throw new Error('Invalid backup module data');
  }

  const previous = new Map(entries.map(([key]) => [key, localStorage.getItem(key)]));
  try {
    entries.forEach(([key, value]) => localStorage.setItem(key, JSON.stringify(value)));
  } catch (error) {
    previous.forEach((value, key) => {
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, value);
    });
    throw error;
  }
  return true;
}

function loadModules(): ModuleOption[] {
  try {
    const raw = localStorage.getItem(MODULES_STORAGE_KEY);
    if (!raw) return mockModules;
    const parsed = JSON.parse(raw) as ModuleOption[];
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : mockModules;
  } catch (error) {
    logger.warn('Failed to read modules from Local Storage — falling back to mock data', { error }, 'import-export');
    return mockModules;
  }
}

function saveModules(modules: ModuleOption[]): void {
  try {
    localStorage.setItem(MODULES_STORAGE_KEY, JSON.stringify(modules));
  } catch (error) {
    logger.error('Failed to persist modules to Local Storage', error, 'import-export');
  }
}

function loadBackupHistory(): BackupEntry[] {
  try {
    const raw = localStorage.getItem(BACKUP_HISTORY_STORAGE_KEY);
    if (!raw) return mockBackupHistory;
    const parsed = JSON.parse(raw) as BackupEntry[];
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : mockBackupHistory;
  } catch (error) {
    logger.warn('Failed to read backup history from Local Storage — falling back to mock data', { error }, 'import-export');
    return mockBackupHistory;
  }
}

function saveBackupHistory(backupHistory: BackupEntry[]): void {
  try {
    localStorage.setItem(BACKUP_HISTORY_STORAGE_KEY, JSON.stringify(backupHistory));
  } catch (error) {
    logger.error('Failed to persist backup history to Local Storage', error, 'import-export');
  }
}

function loadImportPreview(): ImportPreviewItem[] {
  try {
    const raw = localStorage.getItem(IMPORT_PREVIEW_STORAGE_KEY);
    if (!raw) return mockImportPreview;
    const parsed = JSON.parse(raw) as ImportPreviewItem[];
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : mockImportPreview;
  } catch (error) {
    logger.warn('Failed to read import preview from Local Storage — falling back to mock data', { error }, 'import-export');
    return mockImportPreview;
  }
}

function loadValidationChecks(): ValidationCheck[] {
  try {
    const raw = localStorage.getItem(VALIDATION_CHECKS_STORAGE_KEY);
    if (!raw) return mockValidationChecks;
    const parsed = JSON.parse(raw) as ValidationCheck[];
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : mockValidationChecks;
  } catch (error) {
    logger.warn('Failed to read validation checks from Local Storage — falling back to mock data', { error }, 'import-export');
    return mockValidationChecks;
  }
}

function useSimulatedProgress() {
  const [status, setStatus] = useState<OperationStatus>('idle');
  const [percent, setPercent] = useState(0);

  const run = (shouldFail = false) => {
    setStatus('running');
    setPercent(0);
    let current = 0;
    const timer = window.setInterval(() => {
      current += 10 + Math.round(Math.random() * 15);
      if (current >= 100) {
        current = 100;
        window.clearInterval(timer);
        setStatus(shouldFail ? 'error' : 'success');
      }
      setPercent(current);
    }, PROGRESS_STEP_MS);
  };

  const reset = () => {
    setStatus('idle');
    setPercent(0);
  };

  return { status, percent, run, reset };
}

export function useImportExport() {
  const [isLoading, setIsLoading] = useState(true);
  const [modules, setModules] = useState<ModuleOption[]>([]);
  const [selectedModuleIds, setSelectedModuleIds] = useState<string[]>([]);
  const [backupHistory, setBackupHistory] = useState<BackupEntry[]>([]);
  const [importPreview, setImportPreview] = useState<ImportPreviewItem[]>([]);
  const [validationBase, setValidationBase] = useState<ValidationCheck[]>([]);
  const [importFileName, setImportFileName] = useState<string | null>(null);
  const [restoreTargetId, setRestoreTargetId] = useState<string | null>(null);

  const exportOp = useSimulatedProgress();
  const importOp = useSimulatedProgress();

  useEffect(() => {
    const loadedModules = loadModules();
    setModules(loadedModules);
    setSelectedModuleIds(loadedModules.map((m) => m.id));
    setBackupHistory(loadBackupHistory());
    setImportPreview(loadImportPreview());
    setValidationBase(loadValidationChecks());
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (isLoading) return;
    saveModules(modules);
  }, [modules, isLoading]);

  useEffect(() => {
    if (isLoading) return;
    saveBackupHistory(backupHistory);
  }, [backupHistory, isLoading]);

  const toggleModule = (id: string) => {
    setSelectedModuleIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]));
  };

  const startExport = () => {
    if (selectedModuleIds.length === 0) {
      exportOp.run(true);
      return;
    }

    try {
      const payload = createBackupPayload();
      const id = `backup-${Date.now()}`;
      const fileName = `red_king_backup_${new Date().toISOString().slice(0, 10)}.json`;
      localStorage.setItem(`${BACKUP_DATA_PREFIX}${id}`, JSON.stringify(payload));
      setBackupHistory((history) => [
        { id, name: fileName, date: new Date().toLocaleString(), size: `${JSON.stringify(payload).length} B`, modules: selectedModuleIds.length },
        ...history,
      ]);
      downloadBackup(payload, fileName);
      exportOp.run(false);
    } catch (error) {
      logger.error('Failed to create backup', error, 'import-export');
      exportOp.run(true);
    }
  };

  const chooseMockFile = () => {
    const latest = loadBackupHistory()[0];
    setImportFileName(latest?.name ?? null);
    importOp.reset();
  };

  const startImport = () => {
    if (!importFileName) return;
    importOp.run(false);
  };

  const conflictCount = useMemo(
    () => importPreview.filter((p) => p.status === 'conflict').length,
    [importPreview]
  );

  const validationChecks = useMemo(
    () =>
      validationBase.map((c) =>
        c.id === 'v3' && conflictCount > 0 ? { ...c, passed: false } : c
      ),
    [validationBase, conflictCount]
  );

  const requestRestore = (id: string) => setRestoreTargetId(id);
  const cancelRestore = () => setRestoreTargetId(null);
  const confirmRestore = () => {
    if (!restoreTargetId) return;
    try {
      const raw = localStorage.getItem(`${BACKUP_DATA_PREFIX}${restoreTargetId}`);
      if (!raw) throw new Error('Backup data is unavailable');
      restoreBackup(raw);
      setRestoreTargetId(null);
      importOp.run(false);
    } catch (error) {
      logger.warn('Rejected invalid backup restore', { error }, 'import-export');
      importOp.run(true);
    }
  };

  return {
    isLoading,
    modules,
    selectedModuleIds,
    toggleModule,
    exportStatus: exportOp.status,
    exportPercent: exportOp.percent,
    startExport,
    resetExport: exportOp.reset,
    importFileName,
    chooseMockFile,
    importPreview,
    validationChecks,
    importStatus: importOp.status,
    importPercent: importOp.percent,
    startImport,
    resetImport: importOp.reset,
    backupHistory,
    restoreTargetId,
    requestRestore,
    cancelRestore,
    confirmRestore,
  };
}
