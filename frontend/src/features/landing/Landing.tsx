'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { motion, useReducedMotion, useScroll } from 'motion/react';
import BrandMark from '@/components/BrandMark';
import HeroLanyard from './HeroLanyard';
import PillNav from './PillNav';
import RetailScene, { Reveal } from './RetailScene';
import DaypartMap from './DaypartMap';
import FailFastCards from './FailFastCards';
import FinancialPlanner from './FinancialPlanner';
import RetailFilm from './RetailFilm';
import { ExpansionField, useLandingChoreography } from './LandingMotion';
const navItems=[{label:'Overview',href:'#hero'},{label:'How it works',href:'#how-it-works'},{label:'Neighbourhoods',href:'#daypart-dna'},{label:'Planning',href:'#financial-planning'}];
function Arrow({ down=false }:{down?:boolean}) {
 return <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" style={down?{transform:'rotate(90deg)'}:undefined}><path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="1.8"/></svg>;
}
export default function Landing() {
 const surface=useRef<HTMLDivElement>(null);
 const reduced=useReducedMotion();
 const [flat,setFlat]=useState(false), [ready,setReady]=useState(false), [paused,setPaused]=useState(false), [visible,setVisible]=useState(true);
 const {scrollYProgress}=useScroll();
 useEffect(()=>{
  const hero=document.getElementById('hero');
  const observer=new IntersectionObserver(([entry])=>setVisible(entry.isIntersecting));
  if(hero)observer.observe(hero);
  const visibility=()=>setVisible(!document.hidden&&!!hero&&hero.getBoundingClientRect().bottom>0);
  document.addEventListener('visibilitychange',visibility);
  return()=>{observer.disconnect();document.removeEventListener('visibilitychange',visibility);};
 },[]);
 useEffect(()=>{
  const connection=(navigator as Navigator&{connection?:{saveData:boolean}}).connection;
  if(connection?.saveData||new URLSearchParams(location.search).has('flat'))setFlat(true);
  const frame=requestAnimationFrame(()=>setReady(true));return()=>cancelAnimationFrame(frame);
 },[]);
 const still=paused||!!reduced||flat;
 useLandingChoreography(surface, still||!ready);
 return <div ref={surface} className="landing-experience" data-motion-paused={still}>
  {!still&&<motion.div className="reading-progress" style={{scaleX:paused?0:scrollYProgress}} aria-hidden="true"/>}
  <PillNav logo={<BrandMark/>} logoAlt="StoreScout" items={navItems} activeHref="#hero" itemStyle="pill" hoverEffect="fill" indicator="dot"/>
  <main id="landing-content">
   <section id="hero" className="hero-section"><div className="hero-grid">
    <div className="hero-copy"><h1 className="hero-title"><span className="hero-line"><span>Your next store.</span></span><em className="hero-line"><span>A clearer plan.</span></em></h1><p className="hero-lede">Find the right place. Understand the investment.</p><p className="hero-body">Explore neighbourhoods, test the economics and build an expansion plan that fits your budget.</p><div className="hero-actions"><Link className="button" href="/app/">Explore StoreScout <Arrow/></Link><a className="button-secondary" href="#retail-film">Watch the story <Arrow down/></a></div><p className="demo-disclosure">Interactive Navi Mumbai demo · synthetic data</p></div>
    <div className="hero-3d-wrapper" aria-hidden="true"><ExpansionField paused={still||!visible||!ready}><HeroLanyard still={!ready||flat||!!reduced} paused={paused||!visible}/></ExpansionField></div>
   </div></section>
   <div className="retail-strip"><span>Understand the place</span><span>Test the economics</span><span>Plan the network</span></div>
   <RetailFilm paused={still||!ready}/>
   <section id="how-it-works" className="section-wrapper tint-bg">
    <div className="section-heading-row"><div><h2>From place to plan.</h2><p className="section-intro-text">Three connected steps. One considered investment.</p></div><a className="text-link" href="#daypart-dna">Read the neighbourhood <Arrow down/></a></div>
    <div className="journey-layout"><Reveal paused={still}><RetailScene paused={still}/></Reveal><ol className="journey-steps"><li><span>1</span><div><h3>Explore the location</h3><p>See candidate sites, nearby destinations and your existing stores together.</p></div></li><li><span>2</span><div><h3>Test the conditions</h3><p>Change rent, demand or infrastructure timing. See what the plan depends on.</p></div></li><li><span>3</span><div><h3>Choose your expansion</h3><p>Compare network value and select a portfolio within your budget.</p></div></li></ol></div>
   </section>
   <section id="daypart-dna" className="section-wrapper">
    <div className="section-heading-row"><div><h2>Read the<br/>neighbourhood.</h2><p className="section-intro-text">A busy lunch hour tells a different story from a weekend. Explore what changes with the time of day.</p></div></div>
    <DaypartMap/>
    <div className="infrastructure-story"><div className="station-symbol" aria-hidden="true"><span>M</span><i/><i/></div><div><h3>What changes when the metro arrives?</h3><p>Switch between current access, a future opening and a delay. Keep the event assumptions visible before making a decision.</p></div><a className="text-link" href="/app/scenarios">Test a scenario <Arrow/></a></div>
   </section>
   <section id="failfast" className="section-wrapper tint-bg"><div className="section-heading-row"><div><h2>A busy street.<br/>But a viable store?</h2><p className="section-intro-text">Look beyond sales. Understand the costs, competition and impact on your existing stores.</p></div></div><FailFastCards paused={still}/></section>
   <section id="financial-planning" className="section-wrapper"><div className="section-header-block"><h2>Make every store count.</h2><p className="section-intro-text">From a single site to your next portfolio, follow the economics across the whole network.</p></div><FinancialPlanner paused={still}/></section>
   <section id="evidence" className="section-wrapper dark-bg"><div className="section-heading-row"><div><h2>Clarity behind<br/>every decision.</h2><p className="section-intro-text">Keep what is known, estimated and assumed in view.</p></div><div className="evidence-seal" aria-hidden="true"><BrandMark size={62}/></div></div><div className="evidence-pillars-grid">
    <article className="evidence-pillar-card"><h3 className="pillar-title">Know the source.</h3><p className="pillar-desc">Data labels distinguish synthetic locations from the real street map.</p></article>
    <article className="evidence-pillar-card"><h3 className="pillar-title">See the assumptions.</h3><p className="pillar-desc">This prototype uses scenario assumptions. Estimates are not trained-model forecasts.</p></article>
    <article className="evidence-pillar-card"><h3 className="pillar-title">Keep the reasoning.</h3><p className="pillar-desc">Save scenarios, compare results and trace the inputs behind an investment plan.</p></article>
   </div><Reveal paused={still} className="final-cta-box"><div><h2>Plan your next move.</h2><p className="final-cta-sub">Find the place. Understand the investment.</p><Link className="button" href="/app/">Start exploring <Arrow/></Link></div><div className="closing-brand" aria-hidden="true"><BrandMark size={112}/><span>Good places.<br/>Considered decisions.</span></div></Reveal></section>
  </main>
  <footer className="footer-clean"><div className="footer-inner"><div className="footer-identity"><span className="footer-title"><BrandMark size={28}/> StoreScout</span><span className="footer-subtitle">Retail expansion, considered. · Team Elites</span></div><a href="#hero" className="footer-back-link">Back to top <Arrow/></a></div></footer>
  {ready&&!reduced&&!flat&&<button className="motion-control" onClick={()=>setPaused(!paused)} aria-pressed={paused}>{paused?'Resume motion':'Pause motion'}</button>}
 </div>;
}
