'use client';
import { useState } from 'react';

type DaypartKey = 'morning' | 'lunch' | 'evening' | 'weekend';
type InfraKey = 'today' | 'future' | 'delayed';

const daypartConfig: Record<DaypartKey, {
  label: string;
  hours: string;
  peakZone: string;
  driver: string;
  score: number;
  highlightCategory: string;
  poiHighlights: string[];
}> = {
  morning: {
    label: 'Morning',
    hours: '07:00 – 10:30',
    peakZone: 'Transit Junction & Coffee Corridor',
    driver: 'Commuters & college transit',
    score: 82,
    highlightCategory: 'Transit & Grab-and-Go',
    poiHighlights: ['Metro Stn', 'Bus Terminal', 'Coffee Roasters', 'Corporate Gates'],
  },
  lunch: {
    label: 'Lunch',
    hours: '12:00 – 15:00',
    peakZone: 'Commercial Tech Corridor',
    driver: 'Office workers & business dining',
    score: 94,
    highlightCategory: 'Offices & Fast Casual',
    poiHighlights: ['Tech Towers A-D', 'Coworking Hub', 'Food Court', 'Bank HQ'],
  },
  evening: {
    label: 'Evening',
    hours: '17:30 – 21:30',
    peakZone: 'Central High Street',
    driver: 'After-work leisure & social dining',
    score: 88,
    highlightCategory: 'Dining & High Street',
    poiHighlights: ['Boutique Street', 'Bistro Row', 'Fitness Center', 'Supermarket'],
  },
  weekend: {
    label: 'Weekend',
    hours: '11:00 – 21:00',
    peakZone: 'Shopping Mall & Lifestyle District',
    driver: 'Families, shoppers & weekend destinations',
    score: 91,
    highlightCategory: 'Retail & Entertainment',
    poiHighlights: ['Grand Mall', 'Cinema Complex', 'City Park', 'Lifestyle Stores'],
  },
};

const infraConfig: Record<InfraKey, {
  label: string;
  statusText: string;
  badgeClass: string;
  accessScore: number;
  travelTime: string;
  catchmentPop: string;
  summary: string;
}> = {
  today: {
    label: 'Today',
    statusText: 'Current baseline network',
    badgeClass: 'badge-today',
    accessScore: 62,
    travelTime: '34 min average transit time',
    catchmentPop: '18,400 residents within 15 min',
    summary: 'Existing bus and arterial road network. Candidate site relies on personal vehicles and local buses.',
  },
  future: {
    label: 'Future Project Opens',
    statusText: 'Metro Purple Line operational',
    badgeClass: 'badge-future',
    accessScore: 92,
    travelTime: '13 min direct metro connection',
    catchmentPop: '34,200 residents within 15 min (+86%)',
    summary: 'New Station at 150m from Candidate Site 1. Direct connection to IT corridor unlocks major accessibility uplift.',
  },
  delayed: {
    label: 'Project Delayed',
    statusText: 'Commissioning deferred (+18 months)',
    badgeClass: 'badge-delayed',
    accessScore: 64,
    travelTime: '32 min (construction detours active)',
    catchmentPop: '19,100 residents within 15 min',
    summary: 'Infrastructure completion pushed to late 2028. Footfall boost deferred; traffic diversion dampens immediate walkability.',
  },
};

export default function DaypartMap() {
  const [activeDaypart, setActiveDaypart] = useState<DaypartKey>('lunch');
  const [activeInfra, setActiveInfra] = useState<InfraKey>('today');
  const [selectedSite, setSelectedSite] = useState<number>(1);

  const dp = daypartConfig[activeDaypart];
  const inf = infraConfig[activeInfra];

  return (
    <div className="daypart-map-container">
      <p>SYNTHETIC illustration. Scores and places explain the concept; they are not measured demand or model output.</p>
      {/* Control Ribbons */}
      <div className="map-controls-bar">
        <div className="control-group">
          <span className="control-label">Explore DaypartDNA:</span>
          <div className="button-group" role="group" aria-label="Daypart selection">
            {(['morning', 'lunch', 'evening', 'weekend'] as DaypartKey[]).map((key) => (
              <button
                key={key}
                type="button"
                aria-pressed={activeDaypart === key}
                className={`control-pill ${activeDaypart === key ? 'active' : ''}`}
                onClick={() => setActiveDaypart(key)}
              >
                {daypartConfig[key].label}
              </button>
            ))}
          </div>
        </div>

        <div className="control-group">
          <span className="control-label">Infrastructure Scenario:</span>
          <div className="button-group" role="group" aria-label="Infrastructure scenario">
            {(['today', 'future', 'delayed'] as InfraKey[]).map((key) => (
              <button
                key={key}
                type="button"
                className={`control-pill ${activeInfra === key ? 'active' : ''}`}
                onClick={() => setActiveInfra(key)}
              >
                {infraConfig[key].label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Map + Data Grid */}
      <div className="map-view-grid">
        {/* SVG Interactive Map */}
        <div className="map-canvas-card">
          <div className="map-canvas-header">
            <div className="map-legend">
              <span className="legend-item"><span className="legend-dot purple" /> Candidate Sites</span>
              <span className="legend-item"><span className="legend-dot black" /> Existing Stores</span>
              {activeInfra !== 'today' && (
                <span className="legend-item">
                  <span className={`legend-line ${activeInfra === 'delayed' ? 'delayed' : 'active'}`} />
                  Metro Line 3 {activeInfra === 'delayed' ? '(Delayed)' : '(Proposed)'}
                </span>
              )}
            </div>
            <span className="map-chip">
              Active: <strong>{dp.label}</strong> ({dp.hours})
            </span>
          </div>

          <svg
            viewBox="0 0 680 440"
            className="interactive-svg-map"
            aria-label="Interactive district map with DaypartDNA and metro line overlay"
          >
            <defs>
              <pattern id="grid-pattern" width="30" height="30" patternUnits="userSpaceOnUse">
                <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(24,24,27,0.04)" strokeWidth="1" />
              </pattern>
              <filter id="glow-purple" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#7244e5" floodOpacity="0.35" />
              </filter>
            </defs>

            {/* Background Grid */}
            <rect width="680" height="440" fill="var(--paper)" />
            <rect width="680" height="440" fill="url(#grid-pattern)" />

            {/* Neighborhood Zones */}
            {/* Zone 1: Tech Office Corridor (North-East) */}
            <g className={`zone-shape ${activeDaypart === 'lunch' ? 'zone-active' : ''}`}>
              <polygon points="340,40 580,30 630,190 410,210" fill={activeDaypart === 'lunch' ? '#e9e1f8' : '#f0efe9'} stroke="#dfded8" strokeWidth="1.5" />
              <text x="480" y="85" textAnchor="middle" className="zone-text-title">Tech Office Corridor</text>
              <text x="480" y="105" textAnchor="middle" className="zone-text-sub">Peak: Lunch hours</text>
            </g>

            {/* Zone 2: University & Transit Hub (South-West) */}
            <g className={`zone-shape ${activeDaypart === 'morning' ? 'zone-active' : ''}`}>
              <polygon points="50,210 270,180 320,390 90,410" fill={activeDaypart === 'morning' ? '#e9e1f8' : '#f0efe9'} stroke="#dfded8" strokeWidth="1.5" />
              <text x="180" y="270" textAnchor="middle" className="zone-text-title">Transit & University Hub</text>
              <text x="180" y="290" textAnchor="middle" className="zone-text-sub">Peak: Morning commute</text>
            </g>

            {/* Zone 3: High Street Retail & Dining (South-East) */}
            <g className={`zone-shape ${activeDaypart === 'evening' ? 'zone-active' : ''}`}>
              <polygon points="360,230 620,210 650,400 380,410" fill={activeDaypart === 'evening' ? '#e9e1f8' : '#f0efe9'} stroke="#dfded8" strokeWidth="1.5" />
              <text x="510" y="310" textAnchor="middle" className="zone-text-title">High Street Dining</text>
              <text x="510" y="330" textAnchor="middle" className="zone-text-sub">Peak: Evening dinner</text>
            </g>

            {/* Zone 4: Central Shopping Center (North-West) */}
            <g className={`zone-shape ${activeDaypart === 'weekend' ? 'zone-active' : ''}`}>
              <polygon points="60,40 320,50 330,170 80,190" fill={activeDaypart === 'weekend' ? '#e9e1f8' : '#f0efe9'} stroke="#dfded8" strokeWidth="1.5" />
              <text x="190" y="95" textAnchor="middle" className="zone-text-title">Lifestyle & Shopping Mall</text>
              <text x="190" y="115" textAnchor="middle" className="zone-text-sub">Peak: Weekends</text>
            </g>

            {/* Main Road Network */}
            <path d="M 60,200 Q 340,210 640,200" fill="none" stroke="#d5d4ce" strokeWidth="5" />
            <path d="M 340,40 L 350,410" fill="none" stroke="#d5d4ce" strokeWidth="5" />

            {/* Future Metro Line Overlay */}
            {activeInfra !== 'today' && (
              <g className={`metro-layer ${activeInfra}`}>
                {/* Metro Line Path */}
                <path
                  d="M 90,370 Q 250,260 440,160 T 620,70"
                  fill="none"
                  stroke={activeInfra === 'future' ? '#7244e5' : '#a19e95'}
                  strokeWidth={activeInfra === 'future' ? '4.5' : '3'}
                  strokeDasharray={activeInfra === 'delayed' ? '8 6' : 'none'}
                />

                {/* Metro Stations */}
                {[
                  { x: 120, y: 350, name: 'Stn: South Terminal' },
                  { x: 310, y: 228, name: 'Stn: Central Crossing' },
                  { x: 495, y: 128, name: 'Stn: Tech Park West' },
                ].map((stn, idx) => (
                  <g key={idx}>
                    {activeInfra === 'future' && (
                      <circle cx={stn.x} cy={stn.y} r="18" fill="#7244e5" opacity="0.16" />
                    )}
                    <circle
                      cx={stn.x}
                      cy={stn.y}
                      r="6.5"
                      fill="#ffffff"
                      stroke={activeInfra === 'future' ? '#7244e5' : '#898680'}
                      strokeWidth="2.5"
                    />
                    <text
                      x={stn.x + 12}
                      y={stn.y - 10}
                      className="stn-label"
                      fill={activeInfra === 'future' ? '#7244e5' : '#62616a'}
                    >
                      {stn.name}
                    </text>
                  </g>
                ))}
              </g>
            )}

            {/* Existing Stores (Black Hex Pins) */}
            {[
              { x: 230, y: 320, label: 'Store #1: South' },
              { x: 540, y: 140, label: 'Store #2: Tech East' },
            ].map((store, i) => (
              <g key={i} className="store-pin existing">
                <polygon
                  points={`${store.x},${store.y - 9} ${store.x + 8},${store.y - 4} ${store.x + 8},${store.y + 5} ${store.x},${store.y + 10} ${store.x - 8},${store.y + 5} ${store.x - 8},${store.y - 4}`}
                  fill="#18181b"
                />
                <circle cx={store.x} cy={store.y} r="2" fill="#ffffff" />
                <text x={store.x} y={store.y + 24} textAnchor="middle" className="pin-text black">
                  {store.label}
                </text>
              </g>
            ))}

            {/* Candidate Sites (Purple Pins) */}
            {[
              { id: 1, x: 325, y: 205, name: 'Candidate 1: Central Junction' },
              { id: 2, x: 450, y: 290, name: 'Candidate 2: High St. Corner' },
              { id: 3, x: 210, y: 130, name: 'Candidate 3: Galleria North' },
            ].map((site) => {
              const isSelected = selectedSite === site.id;
              return (
                <g
                  key={site.id}
                  className={`store-pin candidate ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedSite(site.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {isSelected && (
                    <circle cx={site.x} cy={site.y} r="24" fill="#7244e5" opacity="0.18" />
                  )}
                  <polygon
                    points={`${site.x},${site.y - 12} ${site.x + 10},${site.y - 6} ${site.x + 10},${site.y + 6} ${site.x},${site.y + 12} ${site.x - 10},${site.y + 6} ${site.x - 10},${site.y - 6}`}
                    fill="#7244e5"
                    stroke="#ffffff"
                    strokeWidth="1.5"
                    filter="url(#glow-purple)"
                  />
                  <circle cx={site.x} cy={site.y} r="3" fill="#ffffff" />
                  <text x={site.x} y={site.y - 18} textAnchor="middle" className="pin-text purple">
                    {site.name}
                  </text>
                </g>
              );
            })}
          </svg>

          <div className="map-footer-note">
            <span>* Estimates based on nearby POIs and infrastructure assumptions, not measured footfall.</span>
            <span>Click any purple candidate pin to inspect opportunity.</span>
          </div>
        </div>

        {/* Dynamic Scenario Insights Panel */}
        <div className="map-insight-card">
          <div className="insight-header">
            <span className="insight-kicker">Live Scenario Metrics</span>
            <h4 className="insight-title">
              {selectedSite === 1 ? 'Central Junction Site' : selectedSite === 2 ? 'High Street Corner' : 'Galleria North Site'}
            </h4>
          </div>

          <div className="insight-stat-grid">
            <div className="stat-box">
              <span className="stat-label">Daypart Opportunity</span>
              <div className="stat-num-row">
                <span className="stat-value">{dp.score}</span>
                <span className="stat-unit">/100</span>
              </div>
              <span className="stat-sub">Peak: {dp.peakZone}</span>
            </div>

            <div className="stat-box">
              <span className="stat-label">Transit Access Score</span>
              <div className="stat-num-row">
                <span className="stat-value">{inf.accessScore}</span>
                <span className="stat-unit">/100</span>
              </div>
              <span className="stat-sub">{activeInfra === 'future' ? '+30 pts vs Today' : 'Baseline connectivity'}</span>
            </div>
          </div>

          <div className="insight-details">
            <div className="detail-item">
              <span className="detail-title">Current Daypart Focus</span>
              <p className="detail-desc">
                <strong>{dp.label} ({dp.hours}):</strong> {dp.driver}. High activity across {dp.poiHighlights.join(', ')}.
              </p>
            </div>

            <div className="detail-item">
              <div className="detail-title-row">
                <span className="detail-title">Infrastructure Impact</span>
                <span className={`status-pill ${inf.badgeClass}`}>{inf.label}</span>
              </div>
              <p className="detail-desc">{inf.summary}</p>
              <ul className="impact-bullets">
                <li>{inf.travelTime}</li>
                <li>{inf.catchmentPop}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
