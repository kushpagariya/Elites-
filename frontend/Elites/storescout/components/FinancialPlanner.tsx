'use client';
import { useState, useMemo } from 'react';
import Link from 'next/link';

interface BaseSite {
  id: number;
  name: string;
  location: string;
  baseMonthlySales: number; // in Lakhs
  baseRent: number; // in Lakhs
  baseOtherOpex: number; // in Lakhs
  capex: number; // in Lakhs
  cannibalizationRate: number; // percentage
}

const baseSites: BaseSite[] = [
  {
    id: 1,
    name: 'South Metro Crossing',
    location: 'Koramangala 80ft Road',
    baseMonthlySales: 24.0,
    baseRent: 2.2,
    baseOtherOpex: 17.4,
    capex: 48.0,
    cannibalizationRate: 0.06,
  },
  {
    id: 2,
    name: 'High Street Central',
    location: 'Indiranagar 100ft Road',
    baseMonthlySales: 28.5,
    baseRent: 4.8,
    baseOtherOpex: 20.8,
    capex: 70.0,
    cannibalizationRate: 0.38,
  },
  {
    id: 3,
    name: 'Tech Park Galleria',
    location: 'Outer Ring Road Bellandur',
    baseMonthlySales: 22.8,
    baseRent: 2.6,
    baseOtherOpex: 15.6,
    capex: 54.0,
    cannibalizationRate: 0.04,
  },
];

export default function FinancialPlanner() {
  const [rentDelta, setRentDelta] = useState<number>(0); // -20 to +30 %
  const [demandDelta, setDemandDelta] = useState<number>(0); // -25 to +25 %
  const [hasCompetitor, setHasCompetitor] = useState<boolean>(false);
  const [activeCombo, setActiveCombo] = useState<'recommended' | 'naive'>('recommended');

  // Compute calculated metrics for each site
  const computedSites = useMemo(() => {
    const competitorFactor = hasCompetitor ? 0.88 : 1.0;
    const demandMultiplier = (1 + demandDelta / 100) * competitorFactor;
    const rentMultiplier = 1 + rentDelta / 100;

    return baseSites.map((site) => {
      const grossSales = Math.round(site.baseMonthlySales * demandMultiplier * 10) / 10;
      const rent = Math.round(site.baseRent * rentMultiplier * 10) / 10;
      const otherOpex = Math.round(site.baseOtherOpex * (1 + (demandMultiplier - 1) * 0.4) * 10) / 10;
      const totalCost = Math.round((rent + otherOpex) * 10) / 10;
      const netProfit = Math.round((grossSales - totalCost) * 10) / 10;
      const margin = Math.round((netProfit / grossSales) * 1000) / 10;
      const annualProfit = netProfit * 12;
      const roi = site.capex > 0 ? Math.round((annualProfit / site.capex) * 100) : 0;
      const payback = annualProfit > 0 ? (site.capex / annualProfit).toFixed(1) : '> 7';
      const viable = roi >= 15 && netProfit > 0;

      return {
        ...site,
        grossSales,
        rent,
        totalCost,
        netProfit,
        margin,
        roi,
        payback,
        viable,
      };
    });
  }, [rentDelta, demandDelta, hasCompetitor]);

  const resetAssumptions = () => {
    setRentDelta(0);
    setDemandDelta(0);
    setHasCompetitor(false);
  };

  return (
    <div className="financial-planner-container">
      {/* Simulation Controls: What-If Simulator */}
      <div className="whatif-simulator-card">
        <div className="simulator-header">
          <div>
            <span className="card-site-tag">Dynamic What-If Simulation</span>
            <h4 className="simulator-title">See what happens when market assumptions shift</h4>
          </div>
          <button
            type="button"
            className="reset-btn"
            onClick={resetAssumptions}
            disabled={rentDelta === 0 && demandDelta === 0 && !hasCompetitor}
          >
            Reset Assumptions
          </button>
        </div>

        <div className="sliders-grid">
          {/* Rent Slider */}
          <div className="slider-item">
            <div className="slider-label-row">
              <span className="s-label">Rent Assumption Change</span>
              <span className={`s-value ${rentDelta > 0 ? 'bad' : rentDelta < 0 ? 'good' : ''}`}>
                {rentDelta > 0 ? `+${rentDelta}%` : `${rentDelta}%`}
              </span>
            </div>
            <input
              type="range"
              min="-20"
              max="30"
              step="5"
              value={rentDelta}
              onChange={(e) => setRentDelta(Number(e.target.value))}
              className="styled-range"
              aria-label="Rent assumption adjustment percentage"
            />
            <div className="range-bounds">
              <span>-20% (Negotiated)</span>
              <span>Baseline (0%)</span>
              <span>+30% (Escalated)</span>
            </div>
          </div>

          {/* Demand Slider */}
          <div className="slider-item">
            <div className="slider-label-row">
              <span className="s-label">Customer Demand Shift</span>
              <span className={`s-value ${demandDelta > 0 ? 'good' : demandDelta < 0 ? 'bad' : ''}`}>
                {demandDelta > 0 ? `+${demandDelta}%` : `${demandDelta}%`}
              </span>
            </div>
            <input
              type="range"
              min="-25"
              max="25"
              step="5"
              value={demandDelta}
              onChange={(e) => setDemandDelta(Number(e.target.value))}
              className="styled-range"
              aria-label="Customer demand adjustment percentage"
            />
            <div className="range-bounds">
              <span>-25% (Downturn)</span>
              <span>Baseline (0%)</span>
              <span>+25% (Uplift)</span>
            </div>
          </div>

          {/* Competitor Toggle */}
          <div className="slider-item toggle-box">
            <div className="slider-label-row">
              <span className="s-label">New Competitor Opens Nearby</span>
              <span className={`s-badge ${hasCompetitor ? 'active' : ''}`}>
                {hasCompetitor ? '-12% Demand' : 'None'}
              </span>
            </div>
            <button
              type="button"
              className={`competitor-toggle ${hasCompetitor ? 'active' : ''}`}
              onClick={() => setHasCompetitor(!hasCompetitor)}
              aria-pressed={hasCompetitor}
            >
              <span className="toggle-switch" />
              {hasCompetitor ? 'Competitor active within 500m' : 'No new competitor nearby'}
            </button>
            <span className="range-bounds-text">Models footfall dilution from rival brands</span>
          </div>
        </div>
      </div>

      {/* Financial Comparison Table */}
      <div className="fin-table-card">
        <div className="fin-table-header">
          <span className="section-sub-kicker">Unit Economics by Location</span>
          <p className="fin-table-desc">
            Estimated sales, operating costs, profit, return on investment and payback time responding live to your assumptions.
          </p>
        </div>

        <div className="table-responsive">
          <table className="financial-table">
            <thead>
              <tr>
                <th scope="col">Candidate Location</th>
                <th scope="col" className="text-right">Est. Monthly Sales</th>
                <th scope="col" className="text-right">Operating Costs</th>
                <th scope="col" className="text-right">Net Profit / mo</th>
                <th scope="col" className="text-right">ROI (IRR)</th>
                <th scope="col" className="text-right">Payback</th>
                <th scope="col" className="text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {computedSites.map((site) => (
                <tr key={site.id} className={site.viable ? 'row-viable' : 'row-risky'}>
                  <td>
                    <div className="site-name-cell">
                      <span className="site-cell-title">{site.name}</span>
                      <span className="site-cell-sub">{site.location}</span>
                    </div>
                  </td>
                  <td className="text-right font-mono font-medium">₹{site.grossSales.toFixed(1)} L</td>
                  <td className="text-right font-mono text-muted">₹{site.totalCost.toFixed(1)} L</td>
                  <td className={`text-right font-mono font-semibold ${site.netProfit >= 0 ? 'text-positive' : 'text-danger'}`}>
                    ₹{site.netProfit.toFixed(1)} L
                    <span className="table-margin-sub">({site.margin}%)</span>
                  </td>
                  <td className={`text-right font-mono font-medium ${site.roi >= 15 ? 'text-positive' : 'text-danger'}`}>
                    {site.roi}%
                  </td>
                  <td className="text-right font-mono text-muted">{site.payback} yrs</td>
                  <td className="text-center">
                    <span className={`status-pill-table ${site.viable ? 'viable' : 'at-risk'}`}>
                      {site.viable ? '● VIABLE' : '▲ AT RISK'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Budget Optimisation & Selected Combination */}
      <div className="portfolio-optimisation-card">
        <div className="portfolio-opt-header">
          <div>
            <span className="card-site-tag">Budget Optimisation</span>
            <h4 className="portfolio-opt-title">Make the most of your expansion budget</h4>
            <p className="portfolio-opt-desc">
              The three best individual locations may not be the best three to open together. Compare the naive top-grossing
              pick versus StoreScout’s network-optimised combination.
            </p>
          </div>
          <div className="budget-capsule">
            <span className="b-label">Expansion Budget</span>
            <span className="b-amount">₹1.20 Crore</span>
          </div>
        </div>

        <div className="combo-picker-bar">
          <button
            type="button"
            className={`combo-btn ${activeCombo === 'recommended' ? 'active' : ''}`}
            onClick={() => setActiveCombo('recommended')}
          >
            ★ StoreScout Optimal Combo (Site 1 + Site 3)
          </button>
          <button
            type="button"
            className={`combo-btn ${activeCombo === 'naive' ? 'active' : ''}`}
            onClick={() => setActiveCombo('naive')}
          >
            Naive Top-Grossing Combo (Site 1 + Site 2)
          </button>
        </div>

        <div className="combo-results-grid">
          {activeCombo === 'recommended' ? (
            <div className="combo-card recommended">
              <div className="combo-status-row">
                <span className="combo-badge green">✓ Recommended Portfolio Combination</span>
                <span className="budget-tag">Capital Required: ₹1.02 Cr (Fits ₹1.2 Cr Budget)</span>
              </div>
              <div className="combo-metrics-row">
                <div className="c-metric">
                  <span className="cm-label">Stores Opened</span>
                  <span className="cm-val">Site 1 & Site 3</span>
                  <span className="cm-sub">Koramangala + ORR Bellandur</span>
                </div>
                <div className="c-metric">
                  <span className="cm-label">Customer Overlap / Cannibalization</span>
                  <span className="cm-val positive">4% (Negligible)</span>
                  <span className="cm-sub">Distinct non-competing catchments</span>
                </div>
                <div className="c-metric">
                  <span className="cm-label">Net Incremental Network Value</span>
                  <span className="cm-val positive">+₹31.8 L / mo</span>
                  <span className="cm-sub">+48% higher true gain</span>
                </div>
                <div className="c-metric">
                  <span className="cm-label">Unused Capital Buffer</span>
                  <span className="cm-val">₹18 Lakhs</span>
                  <span className="cm-sub">Safe working capital reserve</span>
                </div>
              </div>
              <p className="combo-verdict-text">
                <strong>Why this combination wins:</strong> Sites 1 and 3 target entirely complementary market catchments with
                near-zero cannibalization, while leaving a healthy ₹18 Lakh contingency buffer in your capital budget.
              </p>
            </div>
          ) : (
            <div className="combo-card naive">
              <div className="combo-status-row">
                <span className="combo-badge warning">▲ Naive High-Grossing Strategy (Sub-optimal)</span>
                <span className="budget-tag">Capital Required: ₹1.18 Cr (Budget Exhausted)</span>
              </div>
              <div className="combo-metrics-row">
                <div className="c-metric">
                  <span className="cm-label">Stores Opened</span>
                  <span className="cm-val">Site 1 & Site 2</span>
                  <span className="cm-sub">Koramangala + Indiranagar</span>
                </div>
                <div className="c-metric">
                  <span className="cm-label">Customer Overlap / Cannibalization</span>
                  <span className="cm-val danger">34% (Severe drag)</span>
                  <span className="cm-sub">Steals customers from East Store</span>
                </div>
                <div className="c-metric">
                  <span className="cm-label">Net Incremental Network Value</span>
                  <span className="cm-val">+₹21.4 L / mo</span>
                  <span className="cm-sub">Reduced by customer diversion</span>
                </div>
                <div className="c-metric">
                  <span className="cm-label">Unused Capital Buffer</span>
                  <span className="cm-val text-muted">₹2 Lakhs</span>
                  <span className="cm-sub">High liquidity vulnerability</span>
                </div>
              </div>
              <p className="combo-verdict-text">
                <strong>The hidden trap:</strong> Selecting the two individually highest grossing sites causes ₹10.4L/mo of
                cannibalization drag from your existing network and exhausts 98% of your expansion capital.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Action CTA */}
      <div className="financial-action-row">
        <Link className="button" href="/app/">
          Explore the Investment Plan
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="1.6" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
