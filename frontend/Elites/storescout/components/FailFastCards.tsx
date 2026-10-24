'use client';
import { useState } from 'react';
import Link from 'next/link';

export default function FailFastCards() {
  const [rentRescued, setRentRescued] = useState(false);

  return (
    <div className="failfast-container">
      {/* Interactive Rent Rescue Trigger Banner */}
      <div className="failfast-banner">
        <div className="banner-text">
          <span className="banner-kicker">Interactive Simulation</span>
          <strong>Example: Can a failing store be saved by renegotiating rent?</strong>
          <p>
            {rentRescued
              ? 'Rent reduced by 33%. Watch how the financial threshold and viability status transform in real time.'
              : 'Site B is currently rejected due to high rent burden and cannibalization. Test a rent-rescue negotiation.'}
          </p>
        </div>
        <button
          type="button"
          className={`rescue-toggle-btn ${rentRescued ? 'active' : ''}`}
          onClick={() => setRentRescued(!rentRescued)}
          aria-pressed={rentRescued}
        >
          <span className="toggle-indicator" />
          {rentRescued ? 'Reset to Baseline' : 'Apply -33% Rent Rescue'}
        </button>
      </div>

      {/* Two Candidate Site Cards */}
      <div className="failfast-cards-grid">
        {/* Card 1: Viable Candidate */}
        <div className="site-card viable">
          <div className="card-top-bar">
            <div>
              <span className="card-site-tag">Candidate Site 01</span>
              <h3 className="card-site-name">Metro Junction Plaza</h3>
              <span className="card-site-loc">Koramangala 80ft Road</span>
            </div>
            <span className="status-badge viable">● VIABLE</span>
          </div>

          <div className="card-metrics-grid">
            <div className="metric-cell">
              <span className="m-label">Est. Monthly Revenue</span>
              <span className="m-val">₹24.0 L</span>
              <span className="m-sub">Projected demand</span>
            </div>
            <div className="metric-cell">
              <span className="m-label">Monthly Rent</span>
              <span className="m-val">₹2.2 L</span>
              <span className="m-sub">9.2% of revenue</span>
            </div>
            <div className="metric-cell">
              <span className="m-label">Cannibalization Risk</span>
              <span className="m-val positive">6%</span>
              <span className="m-sub">Low network overlap</span>
            </div>
            <div className="metric-cell">
              <span className="m-label">Net Profit Margin</span>
              <span className="m-val positive">18.2%</span>
              <span className="m-sub">Payback: 2.2 yrs</span>
            </div>
          </div>

          <div className="card-diagnosis">
            <span className="diag-title">FailFast Diagnosis:</span>
            <p>
              Strong captive commuter footfall with an independent trade catchment. Minimal overlap with existing stores
              ensures 94% of sales represent true incremental network value.
            </p>
          </div>

          <div className="card-verdict positive">
            <span className="verdict-icon">✓</span>
            <span>Recommended for expansion portfolio within capital budget.</span>
          </div>
        </div>

        {/* Card 2: Risky / Rescued Candidate */}
        <div className={`site-card ${rentRescued ? 'rescued' : 'risky'}`}>
          <div className="card-top-bar">
            <div>
              <span className="card-site-tag">Candidate Site 02</span>
              <h3 className="card-site-name">Central High Street</h3>
              <span className="card-site-loc">Indiranagar 100ft Road</span>
            </div>
            <span className={`status-badge ${rentRescued ? 'rescued' : 'rejected'}`}>
              {rentRescued ? '● RESCUED' : '▲ AT RISK / REJECTED'}
            </span>
          </div>

          <div className="card-metrics-grid">
            <div className="metric-cell">
              <span className="m-label">Est. Monthly Revenue</span>
              <span className="m-val">₹28.5 L</span>
              <span className="m-sub">High gross footfall</span>
            </div>
            <div className={`metric-cell ${rentRescued ? 'highlight-rescue' : ''}`}>
              <span className="m-label">Monthly Rent</span>
              <span className="m-val">{rentRescued ? '₹3.2 L' : '₹4.8 L'}</span>
              <span className="m-sub">{rentRescued ? '11.2% (Rescued)' : '16.8% (Unsustainable)'}</span>
            </div>
            <div className="metric-cell">
              <span className="m-label">Cannibalization Risk</span>
              <span className="m-val danger">38%</span>
              <span className="m-sub">Diverts ₹10.8L from East Store</span>
            </div>
            <div className={`metric-cell ${rentRescued ? 'highlight-rescue' : ''}`}>
              <span className="m-label">Net Profit Margin</span>
              <span className={`m-val ${rentRescued ? 'positive' : 'negative'}`}>
                {rentRescued ? '+12.4%' : '-3.8%'}
              </span>
              <span className="m-sub">{rentRescued ? 'Payback: 3.1 yrs' : 'Payback: > 7 yrs'}</span>
            </div>
          </div>

          <div className="card-diagnosis">
            <span className="diag-title">FailFast Diagnosis:</span>
            <p>
              {rentRescued ? (
                <>
                  <strong>Rescue condition met:</strong> Reducing base rent from ₹4.8L to ₹3.2L absorbs the 38% customer
                  cannibalization drag, generating positive return on investment.
                </>
              ) : (
                <>
                  <strong>High footfall hides weak returns:</strong> Despite having higher raw footfall, ₹4.8L rent and 38%
                  demand diversion from your nearby branch pushes store economics into net monthly losses.
                </>
              )}
            </p>
          </div>

          <div className={`card-verdict ${rentRescued ? 'positive' : 'negative'}`}>
            <span className="verdict-icon">{rentRescued ? '✓' : '×'}</span>
            <span>
              {rentRescued
                ? 'Condition validated: Viable strictly at renegotiated lease terms.'
                : 'Rejected at current asking rent. Would require lease renegotiation to reach viability.'}
            </span>
          </div>
        </div>
      </div>

      {/* Action CTA */}
      <div className="failfast-action-row">
        <Link className="button" href="/app/">
          See Why a Location Might Fail
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="1.6" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
