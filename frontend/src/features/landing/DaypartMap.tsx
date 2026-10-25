'use client';
import { useEffect, useRef, useState } from 'react';
import { apiRequest } from '@/lib/api';
import { record, isEnvelope } from '@/lib/guards';
import { PERIODS, compactMoney } from '@/lib/presentation';
import { money } from '@/lib/format';
import type { DaypartProfile, InfrastructureEvent } from '@/lib/types';

type InfraState = 'current' | 'opens' | 'delayed';
type Preview = {
  city: string; site_name: string; dayparts: DaypartProfile[];
  infrastructure: InfrastructureEvent; projection_years: number;
  scenarios: {state: InfraState; npv_inr: number; delta_npv_inr: number; annual_revenue_inr: number}[];
};
const labels: Record<InfraState, string> = {current: 'Current network', opens: 'Opening scenario', delayed: 'Delayed opening'};
function isPreview(x: unknown): x is Preview {
  return record(x) && typeof x.city === 'string' && typeof x.site_name === 'string' &&
    typeof x.projection_years === 'number' && record(x.infrastructure) &&
    typeof x.infrastructure.name === 'string' && Array.isArray(x.dayparts) && x.dayparts.length === 6 &&
    x.dayparts.every(p => record(p) && PERIODS.some(([key]) => key === p.time_bin) &&
      (p.opportunity_index === null || typeof p.opportunity_index === 'number' && Number.isFinite(p.opportunity_index) && p.opportunity_index >= 0 && p.opportunity_index <= 100) &&
      typeof p.support_count === 'number') && Array.isArray(x.scenarios) && x.scenarios.length === 3 &&
    x.scenarios.every(s => record(s) && ['current', 'opens', 'delayed'].includes(String(s.state)) &&
      typeof s.npv_inr === 'number' && Number.isFinite(s.npv_inr) && typeof s.delta_npv_inr === 'number' && Number.isFinite(s.delta_npv_inr));
}

export default function DaypartMap() {
  const ref = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<Preview | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [period, setPeriod] = useState('weekday_lunch');
  const [infra, setInfra] = useState<InfraState>('current');
  useEffect(() => {
    const controller = new AbortController();
    let started = false;
    async function load() {
      if (started) return;
      started = true; setError(false);
      try {
        const result = await apiRequest<unknown>('/showcase', {signal: controller.signal});
        if (!isEnvelope(result, isPreview)) throw new Error('Invalid model preview');
        if (!controller.signal.aborted) setData(result.data);
      } catch { if (!controller.signal.aborted) setError(true); }
    }
    const observer = new IntersectionObserver(entries => {if (entries.some(e => e.isIntersecting)) {void load(); observer.disconnect();}}, {rootMargin: '400px'});
    if (ref.current) observer.observe(ref.current);
    return () => {controller.abort(); observer.disconnect();};
  }, [attempt]);
  const profile = data?.dayparts.find(p => p.time_bin === period);
  const scenario = data?.scenarios.find(s => s.state === infra);
  return <div className="rhythm-demo" ref={ref}>
    <p className="rhythm-demo-notice">Live engine preview · synthetic-trained model · assumed business inputs. Account data stays private.</p>
    {!data ? <div role="status"><h3>{error ? 'Preview unavailable' : 'Loading the model preview…'}</h3><p>{error ? 'The calculation service could not return a verified result.' : 'Connecting the Bengaluru source snapshot and fitted model.'}</p>{error && <button type="button" onClick={() => setAttempt(v => v + 1)}>Try again</button>}</div> : <>
      <div className="rhythm-grid">
        <div className="rhythm-chart">
          <h3>One place. Different peaks.</h3>
          <p>Share of weekly POI opportunity. Select a period.</p>
          <div className="rhythm-bars" role="group" aria-label="Daypart selection">
            {PERIODS.map(([key, label]) => {
              const value = data.dayparts.find(p => p.time_bin === key)?.opportunity_index;
              return <button type="button" className="rhythm-bar" key={key} aria-pressed={period === key} onClick={() => setPeriod(key)} aria-label={`${label}: ${value == null ? 'unknown' : value.toFixed(1) + '% of weekly opportunity'}`}>
                <span>{label.split(' · ')[0]}</span><span className="rhythm-track" aria-hidden="true"><span className="rhythm-fill" style={{width: value == null ? '0%' : `${value}%`}}/></span><strong>{value == null ? '—' : value.toFixed(1) + '%'}</strong>
              </button>;
            })}
          </div>
          <div className="rhythm-scale" aria-hidden="true"><span>0%</span><span>100%</span></div>
        </div>
        <div className="rhythm-detail" aria-live="polite">
          <p className="rhythm-time">{PERIODS.find(([key]) => key === period)?.[1]}</p>
          <h3>{data.site_name}</h3><p>{data.city} · {profile?.support_count ?? 'Unknown'} mapped destinations within the model catchment.</p>
          <p>Calculated from POI categories, distance and opening-hour evidence. It represents opportunity, not measured visits.</p>
        </div>
      </div>
      <div className="infra-demo">
        <h3>And when the neighbourhood changes?</h3>
        <div className="story-tabs" role="group" aria-label="Infrastructure scenario">{(['current', 'opens', 'delayed'] as const).map(key => <button type="button" key={key} aria-pressed={infra === key} onClick={() => setInfra(key)}>{labels[key]}</button>)}</div>
        <div className="infra-demo-result" aria-live="polite">
          <div><div className="infra-demo-value" title={money(scenario?.npv_inr)}>{compactMoney(scenario?.npv_inr)}</div><p>{data.projection_years}-year incremental NPV</p><p>Change vs current: {money(scenario?.delta_npv_inr)}</p></div>
          <div><strong>{data.infrastructure.name}</strong><p>Opening dates and commercial effects are scenario assumptions. The engine applies exposure and timing before calculating network value.</p><p>Compare and change these inputs in your workspace.</p></div>
        </div>
      </div>
    </>}
  </div>;
}
