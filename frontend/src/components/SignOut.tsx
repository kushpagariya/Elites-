'use client';
import {useState} from 'react';
import {clearWorkspacePreference, signOut} from '@/lib/auth';
export default function SignOut() {
  const [busy, setBusy] = useState(false), [error, setError] = useState(false);
  return <div><button className="account-signout" disabled={busy} onClick={async () => {
    setBusy(true); setError(false);
    try { await signOut(); clearWorkspacePreference(); window.location.assign('/login'); }
    catch { setError(true); setBusy(false); }
  }}>{busy ? 'Signing out…' : 'Sign out'}</button>{error && <span role="alert">Could not sign out. Please try again.</span>}</div>;
}
