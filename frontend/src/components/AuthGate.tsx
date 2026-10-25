'use client';
import { useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { ApiError } from '@/lib/api';
import { getAccount } from '@/lib/auth';
import '@/app/login/login.css';

export default function AuthGate({children}: {children: ReactNode}) {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError(false);
    getAccount(controller.signal).then(() => setAllowed(true)).catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.status === 401) router.replace('/login');
      else setError(true);
    });
    return () => controller.abort();
  }, [router, attempt]);
  return allowed ? children : <main className="auth-session" role="status"><p>{error ? 'Unable to connect to your account. Please try again.' : 'Opening your workspace…'}</p>{error && <button onClick={() => setAttempt(attempt + 1)}>Try again</button>}</main>;
}
