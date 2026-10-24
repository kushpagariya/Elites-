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
    statusText: 'Illustrative metro line operational',
    badgeClass: 'badge-future',
    accessScore: 92,
    travelTime: '13 min direct metro connection',
    catchmentPop: '34,200 residents within 15 min (+86%)',
    summary: 'New Station at 150m from Candidate Site 1. Direct connection to IT corridor unlocks major accessibility uplift.',
  },
  delayed: {
    label: 'Project Delayed',
    statusText: 'Commissioning deferred (+24 months)',
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
  const dp = daypartConfig[activeDaypart];
  const inf = infraConfig[activeInfra];
  return (
    <div className="rhythm-demo">
      <p className="rhythm-demo-notice">Illustrative opportunity scores using synthetic data. Figures do not represent measured footfall.</p>
      <div className="rhythm-grid">
        <div className="rhythm-chart">
          <h3>One place. Different peaks.</h3>
          <p>Select a time to see what brings people nearby.</p>
          <div className="rhythm-bars" role="group" aria-label="Daypart selection">
            {(Object.keys(daypartConfig) as DaypartKey[]).map(key => (
              <button type="button" className="rhythm-bar" key={key} aria-pressed={activeDaypart === key} onClick={() => setActiveDaypart(key)} aria-label={`${daypartConfig[key].label}: illustrative opportunity ${daypartConfig[key].score} out of 100`}>
                <span>{daypartConfig[key].label}</span>
                <span className="rhythm-track" aria-hidden="true"><span className="rhythm-fill" style={{width: `${daypartConfig[key].score}%`}}/></span>
                <strong>{daypartConfig[key].score}</strong>
              </button>
            ))}
          </div>
          <div className="rhythm-scale" aria-hidden="true"><span>0</span><span>100</span></div>
        </div>
        <div className="rhythm-detail" aria-live="polite">
          <p className="rhythm-time">{dp.label} · {dp.hours}</p>
          <h3 key={activeDaypart}>{dp.peakZone}</h3>
          <p>{dp.driver}. Nearby destinations shape the opportunity for this period.</p>
          <ul className="rhythm-place-list">{dp.poiHighlights.map(place => <li key={place}>{place}</li>)}</ul>
        </div>
      </div>
      <div className="infra-demo">
        <h3>And when the neighbourhood changes?</h3>
        <div className="story-tabs" role="group" aria-label="Infrastructure scenario">
          {(Object.keys(infraConfig) as InfraKey[]).map(key => <button type="button" key={key} aria-pressed={activeInfra === key} onClick={() => setActiveInfra(key)}>{infraConfig[key].label}</button>)}
        </div>
        <div className="infra-demo-result" aria-live="polite">
          <div><div className="infra-demo-value">{inf.accessScore}<small> / 100</small></div><p>Illustrative access</p></div>
          <div><strong key={activeInfra}>{inf.statusText}</strong><p>{inf.summary}</p><p>{inf.travelTime} · {inf.catchmentPop}</p></div>
        </div>
      </div>
    </div>
  );
}
