'use client';
import { useState } from 'react';
import Link from 'next/link';
import RetailScene from './RetailScene';
const checks = [
  {title:'Rent & operating costs',label:'Can the store carry its costs?',body:'Review rent, margins, fit-out and operating costs together. A popular address can still leave too little cash after costs.',change:'Test a rent change in a saved scenario.'},
  {title:'Nearby competition',label:'Who else serves this neighbourhood?',body:'Compare competing destinations and the customers they serve. Nearby activity creates opportunity, but it also creates alternatives.',change:'Review competition and demand assumptions.'},
  {title:'Your existing network',label:'Growth, or customers moving next door?',body:'A new branch may share customers with an existing store. Judge the change across your network, rather than the new store alone.',change:'Compare the whole network before selecting a site.'},
];
export default function FailFastCards({ paused = false }: { paused?: boolean }) {
  const [active,setActive]=useState(0);
  return <div className="story-split risk-story">
    <RetailScene kind="risk" paused={paused}/>
    <div className="decision-panel">
      <div className="story-tabs" role="group" aria-label="Explore investment risks">{checks.map((check,i)=><button key={check.title} aria-pressed={active===i} onClick={()=>setActive(i)}>{check.title}</button>)}</div>
      <div className="risk-explanation" aria-live="polite"><h3 key={active}>{checks[active].label}</h3><p>{checks[active].body}</p><div className="next-question"><span>What to check</span><strong>{checks[active].change}</strong></div></div>
      <p className="availability-note">Run a location analysis to identify risks and assess potential improvements.</p>
      <Link className="text-link" href="/app/scenarios">Explore scenarios <span aria-hidden="true">↗</span></Link>
    </div>
  </div>;
}
