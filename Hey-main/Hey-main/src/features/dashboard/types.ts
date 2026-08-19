export interface StatItem {
  label: string;
  value: number | string;
}

export interface ActivityItem {
  id: string;
  label: string;
  time: string;
}

export type SystemStatusTone = 'success' | 'muted';

export interface SystemStatusItem {
  label: string;
  tone: SystemStatusTone;
}
