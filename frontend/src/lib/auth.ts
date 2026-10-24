import { apiRequest } from './api';

export type Account = { id: string; name: string; email: string };
export const getAccount = (signal?: AbortSignal) => apiRequest<{data: Account}>('/auth/me', {signal});
export const signOut = () => apiRequest('/auth/logout', {method: 'POST'});
export function clearWorkspacePreference() {
  try { localStorage.removeItem('storescout:demo:scenario'); } catch { /* Storage is optional. */ }
}
