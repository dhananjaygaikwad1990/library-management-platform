import { UserSession } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export function setToken(session: UserSession): void {
  localStorage.setItem('library_session', JSON.stringify(session));
}

export function getToken(): UserSession | null {
  const stored = localStorage.getItem('library_session');
  if (!stored) return null;
  try {
    return JSON.parse(stored) as UserSession;
  } catch {
    return null;
  }
}

export function clearToken(): void {
  localStorage.removeItem('library_session');
}

export async function apiFetch<T>(path: string, options: RequestInit = {}) {
  const session = getToken();
  const headers = new Headers(options.headers ?? {});

  headers.set('Content-Type', 'application/json');
  if (session?.accessToken) {
    headers.set('Authorization', `Bearer ${session.accessToken}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.detail || payload?.error?.message || response.statusText;
    throw new Error(message ?? 'Request failed');
  }

  return (await response.json()) as T;
}
