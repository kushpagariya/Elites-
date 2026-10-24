import type { ReactNode } from 'react';
import './landing.css';
export default function Layout({ children }: { children: ReactNode }) {
  return <div className="landing"><a className="skip-link" href="#landing-content">Skip to content</a>{children}</div>;
}
