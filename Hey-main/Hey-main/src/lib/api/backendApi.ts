import { apiGet } from './apiClient';

export interface BackendStatus {
  system: string;
  hive_mind: string;
  uplink: string;
  stealth: string;
  active_nodes: number;
  threat_level: string;
  security_mode: string;
}

export interface BackendHealth {
  [key: string]: unknown;
}

export interface BackendAgent {
  [key: string]: unknown;
}

export interface BackendGraph {
  [key: string]: unknown;
}

export function getBackendStatus(): Promise<BackendStatus> {
  return apiGet<BackendStatus>('/api/status');
}

export function getBackendHealth(): Promise<BackendHealth> {
  return apiGet<BackendHealth>('/api/system/health');
}

export function getBackendAgents(): Promise<BackendAgent[]> {
  return apiGet<BackendAgent[]>('/api/agents');
}

export function getBackendGraph(): Promise<BackendGraph> {
  return apiGet<BackendGraph>('/api/graph');
}

export function getBackendDnaMap(): Promise<unknown> {
  return apiGet('/api/dna_map');
}