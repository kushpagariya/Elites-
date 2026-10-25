'use client';

import Link from 'next/link';
import { useEffect, useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import BrandMark from '@/components/BrandMark';
import { apiRequest, ApiError } from '@/lib/api';
import { clearWorkspacePreference, getAccount } from '@/lib/auth';

export default function LoginForm() {
  const router = useRouter();
  const [register, setRegister] = useState(false);
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    setRegister(new URLSearchParams(window.location.search).get('mode') === 'register');
    const controller = new AbortController();
    getAccount(controller.signal).then(() => router.replace('/app')).catch(() => {});
    return () => controller.abort();
  }, [router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setError(''); setBusy(true);
    const form = new FormData(event.currentTarget);
    const body = {email: String(form.get('email')).trim(), password: String(form.get('password')), ...(register ? {name: String(form.get('name')).trim()} : {})};
    try {
      await apiRequest(`/auth/${register ? 'register' : 'login'}`, {method: 'POST', body: JSON.stringify(body)});
      clearWorkspacePreference();
      router.replace('/app'); router.refresh();
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status !== 0 ? cause.message : 'We couldn’t connect to the sign-in service. Please try again.');
      setBusy(false);
    }
  }

  return <main className="auth-page" id="main-content">
    <section className="auth-form-side" aria-labelledby="auth-title">
      <Link href="/" className="auth-brand" aria-label="StoreScout home"><BrandMark size={38}/><span>Store<span>Scout</span></span></Link>
      <div className="auth-form-content">
        <h1 id="auth-title">{register ? 'Your next chapter\nstarts here.' : 'Welcome back.'}</h1>
        <p className="auth-intro">{register ? 'Create your account to plan grocery locations in Bengaluru.' : 'Sign in to your Bengaluru grocery planning workspace.'}</p>
        <form onSubmit={submit} aria-busy={busy}>
          <fieldset disabled={busy}>
            {register && <label htmlFor="auth-name">Full name<input id="auth-name" name="name" autoComplete="name" required maxLength={80} placeholder="Your name"/></label>}
            <label htmlFor="auth-email">Email address<input id="auth-email" name="email" type="email" autoComplete="email" required maxLength={254} placeholder="you@company.com"/></label>
            <label htmlFor="auth-password">Password<div className="auth-password"><input id="auth-password" name="password" type={visible ? 'text' : 'password'} autoComplete={register ? 'new-password' : 'current-password'} required minLength={register ? 12 : 1} maxLength={128} aria-describedby={register ? 'password-help' : undefined}/><button type="button" onClick={() => setVisible(!visible)} aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible}>{visible ? 'Hide' : 'Show'}</button></div></label>
            {register && <p id="password-help" className="auth-help">Use at least 12 characters. A memorable passphrase works well.</p>}
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button className="auth-submit" type="submit">{busy ? (register ? 'Creating account…' : 'Signing in…') : (register ? 'Create account' : 'Sign in')}<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M5 12h14m-6-6 6 6-6 6" stroke="currentColor" strokeWidth="1.7"/></svg></button>
          </fieldset>
        </form>
        <p className="auth-switch">{register ? 'Already have an account?' : 'New to StoreScout?'} <button type="button" disabled={busy} onClick={() => {setRegister(!register); setError(''); setVisible(false); window.history.replaceState(null, '', register ? '/login' : '/login?mode=register');}}>{register ? 'Sign in' : 'Create an account'}</button></p>
      </div>
      <Link className="auth-back" href="/">← Back to StoreScout</Link>
    </section>
    <aside className="auth-story" aria-label="Retail expansion with StoreScout">
      <div className="auth-story-copy"><h2>Good places.<br/>Considered decisions.</h2><p>Bring locations, economics and your expansion plans into one clear view.</p></div>
      <img src="/images/retail-network.png" alt="Illustrated neighbourhood of retail storefronts" width="1024" height="1024"/>
      <p className="auth-story-footer">Find the place. Understand the investment.</p>
    </aside>
  </main>;
}
