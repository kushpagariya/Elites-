'use client';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useReducedMotion } from 'motion/react';
import FallbackCity from './FallbackCity';
import DaypartMap from './DaypartMap';
import FailFastCards from './FailFastCards';
import FinancialPlanner from './FinancialPlanner';

const City = dynamic(() => import('./City'), { ssr: false });

export type SceneState = {
  chapter: number;
  progress: number;
  daypart: number;
  delayed: boolean;
  rescued: boolean;
  reduced: boolean;
  paused: boolean;
};

function Arrow({ down = false }: { down?: boolean }) {
  return (
    <svg
      aria-hidden="true"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      style={down ? { transform: 'rotate(90deg)' } : undefined}
    >
      <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function Mark() {
  return (
    <svg aria-hidden="true" viewBox="0 0 32 36" width="28" height="32">
      <path d="M16 1 30 9v18l-14 8L2 27V9Z" fill="currentColor" />
      <path d="m9 13 7-4 7 4v10l-7 4-7-4Z" fill="var(--paper)" />
      <path d="m16 15 4 2v5l-4 2-4-2v-5Z" fill="currentColor" />
    </svg>
  );
}

export default function Landing() {
  const reduced = useReducedMotion();
  const [flat, setFlat] = useState(false);
  const [ready, setReady] = useState(false);

  const onSceneFailure = useCallback(() => setFlat(true), []);

  const scene = useRef<SceneState>({
    chapter: 0,
    progress: 0.2,
    daypart: 1,
    delayed: false,
    rescued: false,
    reduced: !!reduced,
    paused: false,
  });

  useEffect(() => {
    const connection = (navigator as Navigator & { connection?: { saveData: boolean } }).connection;
    if (connection?.saveData || new URLSearchParams(location.search).has('flat')) setFlat(true);

    let frame = 0;
    const first = requestAnimationFrame(() => {
      frame = requestAnimationFrame(() => setReady(true));
    });

    return () => {
      cancelAnimationFrame(first);
      cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <>
      {/* Navigation */}
      <header className="header">
        <Link className="wordmark" href="/" aria-label="StoreScout home">
          <Mark />
          StoreScout
        </Link>
        <nav className="header-nav" aria-label="Main navigation">
          <a href="#how-it-works">How It Works</a>
          <a href="#daypart-dna">Features</a>
          <a href="#failfast">Why StoreScout</a>
        </nav>
        <Link className="nav-cta" href="/app/">
          Explore Demo
          <Arrow />
        </Link>
      </header>

      <main id="landing-content">
        {/* ==========================================================
            Section 1 — Hero
            Keep existing animated 3D city, logo, headline, and two CTAs
           ========================================================== */}
        <section id="hero" className="hero-section">
          <div className="hero-grid">
            <div className="hero-copy">
              <h1 className="hero-title">
                Know where to open your next store.
              </h1>
              <p className="hero-lede">
                Don’t just look for busy places. Find locations that make business sense.
              </p>
              <p className="hero-body">
                StoreScout helps retailers compare locations, estimate sales and profits, spot risky investments, and
                choose the best stores to open within their budget.
              </p>
              <div className="hero-actions">
                <Link className="button" href="/app/">
                  Explore StoreScout
                  <Arrow />
                </Link>
                <a className="button-secondary" href="#how-it-works">
                  See How It Works
                  <Arrow down />
                </a>
              </div>
              <div className="hero-kicker">
                <span className="hero-kicker-dot" />
                Smarter retail expansion, backed by location data and clear financial reasoning.
              </div>
            </div>

            {/* Visual: Animated 3D City */}
            <div className="hero-3d-wrapper" aria-hidden="true">
              <div className="hero-scene-container">
                {!ready || flat || reduced ? (
                  <FallbackCity chapter={0} daypart={1} delayed={false} rescued={false} />
                ) : (
                  <City state={scene} onFailure={onSceneFailure} />
                )}
              </div>
              <div className="hero-scene-badge">
                <span className="small-hex" />
                Interactive Retail Landscape
              </div>
            </div>
          </div>
        </section>

        {/* ==========================================================
            Section 2 — How StoreScout Works
            Three compact steps with simple icons, not another large 3D city
           ========================================================== */}
        <section id="how-it-works" className="section-wrapper tint-bg">
          <div className="section-header-block">
            <span className="section-kicker">How StoreScout Works</span>
            <h2>From possible locations to a clear investment plan.</h2>
            <p className="section-intro-text">
              Opening a new store involves more than finding a crowded street. StoreScout brings the important factors
              together in three steps.
            </p>
          </div>

          <div className="steps-grid">
            {/* Step 1 */}
            <div className="step-card">
              <div className="step-header-row">
                <span className="step-num">STEP 01</span>
                <div className="step-icon-box">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M12 3v18M3 12h18M8 8l8 8M16 8l-8 8" opacity="0.3" />
                    <circle cx="12" cy="12" r="3" fill="var(--purple)" />
                  </svg>
                </div>
              </div>
              <h3 className="step-title">1. Tell us your expansion plan</h3>
              <p className="step-desc">
                Choose your city, type of store, available budget and existing store locations.
              </p>
            </div>

            {/* Step 2 */}
            <div className="step-card">
              <div className="step-header-row">
                <span className="step-num">STEP 02</span>
                <div className="step-icon-box">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <rect x="3" y="3" width="18" height="18" rx="2" />
                    <path d="M3 9h18M9 21V9" />
                    <circle cx="15" cy="15" r="2" fill="var(--purple)" />
                  </svg>
                </div>
              </div>
              <h3 className="step-title">2. Compare locations</h3>
              <p className="step-desc">
                Explore nearby customers, competitors, travel access, estimated sales, costs and possible risks.
              </p>
            </div>

            {/* Step 3 */}
            <div className="step-card">
              <div className="step-header-row">
                <span className="step-num">STEP 03</span>
                <div className="step-icon-box">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M4 19h16M7 15l3-4 4 4 6-8" />
                    <circle cx="20" cy="7" r="2" fill="var(--purple)" />
                  </svg>
                </div>
              </div>
              <h3 className="step-title">3. Find the best investment</h3>
              <p className="step-desc">
                See which locations are worth considering, which may fail, and which combination fits your budget.
              </p>
            </div>
          </div>
        </section>

        {/* ==========================================================
            Section 3 — DaypartDNA + Future Infrastructure
            Interactive map with Daypart + Metro route/station overlay
           ========================================================== */}
        <section id="daypart-dna" className="section-wrapper">
          <div className="section-header-block">
            <span className="section-kicker">DaypartDNA + Future Infrastructure</span>
            <h2>The same location can be busy at different times.</h2>
            <p className="section-subhead">
              When will a location have the most opportunity?
            </p>
            <p className="section-intro-text">
              An area near offices may be attractive during weekday lunch hours, while a shopping neighbourhood may have
              more opportunity on weekends. DaypartDNA studies nearby offices, colleges, shops and transport stops to
              estimate these differences.
            </p>
          </div>

          {/* Interactive Map Visual with Metro Overlay */}
          <DaypartMap />

          <div style={{ marginTop: '56px' }}>
            <h3 style={{ fontSize: '24px', fontWeight: 650, letterSpacing: '-0.02em', marginBottom: '12px' }}>
              What if a new metro station opens nearby?
            </h3>
            <p className="section-intro-text" style={{ marginTop: 0 }}>
              A location that is difficult to reach today could become more attractive in the future. Compare today’s
              conditions with scenarios where a planned metro line, transport link or other major project opens—or gets
              delayed.
            </p>
            <p className="footnote-callout">
              * These are estimates based on nearby places and infrastructure assumptions, not measured footfall or
              guaranteed future demand.
            </p>
          </div>
        </section>

        {/* ==========================================================
            Section 4 — FailFast
            Two candidate-site cards: one viable, one risky with rent-rescue
           ========================================================== */}
        <section id="failfast" className="section-wrapper tint-bg">
          <div className="section-header-block">
            <span className="section-kicker">FailFast Risk Diagnosis</span>
            <h2>A good location. A bad investment?</h2>
            <p className="section-subhead">
              Some promising locations cost more than they’re worth.
            </p>
            <p className="section-intro-text">
              High rent, strong competition or customers shifting away from your existing stores can make a new outlet less
              profitable than expected.
            </p>
            <div style={{ marginTop: '20px' }}>
              <p style={{ fontWeight: 600, fontSize: '15px', color: 'var(--ink)', marginBottom: '8px' }}>
                FailFast helps you understand:
              </p>
              <ul style={{ paddingLeft: '22px', fontSize: '15px', color: 'var(--muted)', display: 'grid', gap: '6px' }}>
                <li>Why a location may be risky.</li>
                <li>How it could affect your existing stores.</li>
                <li>What would need to change to make the investment worthwhile.</li>
              </ul>
            </div>
          </div>

          {/* FailFast Interactive Candidate Comparison */}
          <FailFastCards />
        </section>

        {/* ==========================================================
            Section 5 — Financial Analysis + What-If + Budget Optimisation
            Small investment comparison, what-if slider, selected combination
           ========================================================== */}
        <section id="financial-planning" className="section-wrapper">
          <div className="section-header-block">
            <span className="section-kicker">Financial Analysis & Budget Optimisation</span>
            <h2>Don’t just choose a location. Choose a better investment.</h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px', marginTop: '32px' }}>
              <div>
                <h4 style={{ fontSize: '16px', fontWeight: 650, color: 'var(--ink)', marginBottom: '6px' }}>
                  Know what each store could earn
                </h4>
                <p style={{ fontSize: '14px', color: 'var(--muted)', lineHeight: '1.6' }}>
                  Compare estimated sales, operating costs, profit, return on investment and payback time.
                </p>
              </div>

              <div>
                <h4 style={{ fontSize: '16px', fontWeight: 650, color: 'var(--ink)', marginBottom: '6px' }}>
                  See what happens when things change
                </h4>
                <p style={{ fontSize: '14px', color: 'var(--muted)', lineHeight: '1.6' }}>
                  What if rent increases? What if customer demand drops? What if a new competitor opens nearby? Change the
                  assumptions and see how the results respond.
                </p>
              </div>

              <div>
                <h4 style={{ fontSize: '16px', fontWeight: 650, color: 'var(--ink)', marginBottom: '6px' }}>
                  Make the most of your expansion budget
                </h4>
                <p style={{ fontSize: '14px', color: 'var(--muted)', lineHeight: '1.6' }}>
                  The three best individual locations may not be the best three to open together. StoreScout considers your
                  budget and existing network to find the optimal combination.
                </p>
              </div>
            </div>
          </div>

          {/* Interactive What-If Simulator + Financial Table + Portfolio Combination */}
          <FinancialPlanner />
        </section>

        {/* ==========================================================
            Section 6 — Evidence + Final CTA
            Evidence-backed approach + Clear final CTA
           ========================================================== */}
        <section id="evidence" className="section-wrapper dark-bg">
          <div className="section-header-block">
            <span className="section-kicker" style={{ color: 'var(--tint)' }}>
              Transparent Reasoning
            </span>
            <h2 style={{ color: 'var(--white)' }}>
              Know why a location is recommended.
            </h2>
            <p className="section-intro-text">
              Every recommendation should show what the platform knows, what it estimates and what it assumes. StoreScout
              makes these differences clear so retailers can understand the reasoning behind each decision.
            </p>
          </div>

          <div className="evidence-pillars-grid">
            <article className="evidence-pillar-card">
              <div className="pillar-symbol solid" />
              <h3 className="pillar-title">Real information</h3>
              <p className="pillar-desc">
                Available population, roads, nearby destinations, existing store coordinates, and retailer-provided
                data. Grounded in verifiable geographic reality.
              </p>
            </article>

            <article className="evidence-pillar-card">
              <div className="pillar-symbol modeled" />
              <h3 className="pillar-title">Estimates</h3>
              <p className="pillar-desc">
                Possible customer demand, DaypartDNA profiles, financial outcomes, and network sensitivity under
                different macroeconomic scenarios.
              </p>
            </article>

            <article className="evidence-pillar-card">
              <div className="pillar-symbol assumed" />
              <h3 className="pillar-title">Assumptions</h3>
              <p className="pillar-desc">
                Base rent, fit-out costs, operating margins, future infrastructure completion dates, and other editable
                parameters that can be calibrated anytime.
              </p>
            </article>
          </div>

          {/* Final Call to Action */}
          <div className="final-cta-box">
            <h2>Your next store deserves a smarter decision.</h2>
            <p className="final-cta-sub">
              Compare locations. Understand the risks. Plan your expansion.
            </p>
            <Link className="button" href="/app/">
              Explore StoreScout
              <Arrow />
            </Link>
          </div>
        </section>
      </main>

      {/* Clean, Non-Oversized Footer */}
      <footer className="footer-clean">
        <div className="footer-inner">
          <div className="footer-identity">
            <span className="footer-title">
              <Mark /> StoreScout
            </span>
            <span className="footer-subtitle">
              StoreScout · Team Elites · Retail Expansion Intelligence Platform
            </span>
          </div>
          <a href="#hero" className="footer-back-link">
            Back to top <Arrow />
          </a>
        </div>
      </footer>
    </>
  );
}
