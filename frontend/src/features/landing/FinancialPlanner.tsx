'use client';
import { useState } from 'react';
import Link from 'next/link';
import RetailScene from './RetailScene';
const lenses = [
 {name:'Store economics',heading:'Follow the money, past the till.',detail:'Sales are the starting point. Rent, operating costs, upfront investment and the timing of cash flows determine what a store could return.',steps:['Estimated sales','Operating costs','Cash flows','Investment value']},
 {name:'What-if scenarios',heading:'Give the plan a stress test.',detail:'Explore how rent, demand and future infrastructure could change the decision. Keep each assumption set saved so comparisons stay consistent.',steps:['Current conditions','Changed assumptions','New evaluation','Compare outcomes']},
 {name:'Portfolio planning',heading:'Choose stores that work together.',detail:'Review budget, store count and shared demand across the network. The strongest individual sites may compete for the same customers.',steps:['Eligible sites','Available budget','Network overlap','Chosen portfolio']},
];
export default function FinancialPlanner({paused=false}:{paused?:boolean}) {
 const [active,setActive]=useState(0); const lens=lenses[active];
 return <div className="planning-showcase">
   <div className="story-tabs" role="group" aria-label="Explore financial planning">{lenses.map((l,i)=><button key={l.name} onClick={()=>setActive(i)} aria-pressed={active===i}>{l.name}</button>)}</div>
   <div className="story-split"><div className="planning-copy" aria-live="polite"><h3>{lens.heading}</h3><p>{lens.detail}</p><ol className="finance-path">{lens.steps.map((step,i)=><li key={step}><span>{i+1}</span>{step}</li>)}</ol><p className="availability-note">Build your investment plan from the results of your saved analysis.</p><Link className="text-link" href="/app/portfolio">Open portfolio planning <span aria-hidden="true">↗</span></Link></div><RetailScene kind="portfolio" paused={paused}/></div>
 </div>;
}
