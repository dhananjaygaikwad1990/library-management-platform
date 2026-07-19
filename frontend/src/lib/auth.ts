import { LoginForm, UserSession } from '../types';
import { setToken, getToken, clearToken, apiFetch } from './api';

export async function login(form: LoginForm): Promise<UserSession> {
  const response = await apiFetch<{ access_token: string; token_type: string; roles: string[] }>(
    '/token',
    {
      method: 'POST',
      body: JSON.stringify(form),
    }
  );

  const session: UserSession = {
    accessToken: response.access_token,
    roles: response.roles as UserSession['roles'],
    email: form.email,
  };

  setToken(session);
  return session;
}

export function logout(): void {
  clearToken();
}

export function getSession(): UserSession | null {
  return getToken();
}

export function hasRole(role: string): boolean {
  const session = getToken();
  return !!session && session.roles.includes(role as any);
}
