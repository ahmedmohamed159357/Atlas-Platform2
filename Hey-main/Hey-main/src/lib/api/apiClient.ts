import { requestJson } from './transportClient';

function buildPath(path: string, params?: Record<string, string | number | boolean>): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  if (!params || Object.keys(params).length === 0) return normalized;

  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.set(key, String(value));
    }
  });

  return `${normalized}?${searchParams.toString()}`;
}

export async function apiGet<TResponse = unknown>(path: string, params?: Record<string, string | number | boolean>): Promise<TResponse> {
  return requestJson<TResponse>(buildPath(path, params));
}

export async function apiPost<TResponse = unknown>(path: string, body?: unknown): Promise<TResponse> {
  return requestJson<TResponse>(path, { method: 'POST', body });
}

export async function apiPut<TResponse = unknown>(path: string, body?: unknown): Promise<TResponse> {
  return requestJson<TResponse>(path, { method: 'PUT', body });
}

export async function apiDelete<TResponse = unknown>(path: string): Promise<TResponse> {
  return requestJson<TResponse>(path, { method: 'DELETE' });
}
