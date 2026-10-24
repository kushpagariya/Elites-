'use client';
import Link from 'next/link';
import { useEffect, useState, type MouseEvent } from 'react';
import { motion, useReducedMotion, useScroll } from 'motion/react';
import BrandMark from '@/components/BrandMark';
import HeroLanyard from './HeroLanyard';
import PillNav from './PillNav';
import RetailScene, { Reveal } from './RetailScene';
import DaypartMap from './DaypartMap';
import FailFastCards from './FailFastCards';
import FinancialPlanner from './FinancialPlanner';
const navItems=[{label:'Overview',href:'#hero'},{label:'How it works',href:'#how-it-works'},{label:'Neighbourhoods',href:'#daypart-dna'},{label:'Planning',href:'#financial-planning'}];
function Arrow({ down=false }:{down?:boolean}) {
 return <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" style={down?{transform:'rotate(90deg)'}:undefined}><path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="1.8"/></svg>;
}
export default function Landing() {
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
 function clickFeedback(e:MouseEvent<HTMLDivElement>){
  if(still||e.detail===0)return;
  const ring=document.createElement('span');ring.className='retail-click-ring';ring.setAttribute('aria-hidden','true');
  ring.style.left=e.clientX+'px';ring.style.top=e.clientY+'px';document.body.appendChild(ring);
  const animation=ring.animate([{transform:'translate(-50%,-50%) scale(.65)',opacity:.5},{transform:'translate(-50%,-50%) scale(2.5)',opacity:0}],{duration:400,easing:'cubic-bezier(0.23,1,0.32,1)'});
  animation.onfinish=()=>ring.remove();
 }
 return <div className="landing-experience" data-motion-paused={still} onClick={clickFeedback}>
  {!reduced&&<motion.div className="reading-progress" style={{scaleX:paused?0:scrollYProgress}} aria-hidden="true"/>}
  <PillNav logo={<BrandMark/>} logoAlt="StoreScout" items={navItems} activeHref="#hero" itemStyle="pill" hoverEffect="fill" indicator="dot"/>
  <main id="landing-content">
   <section id="hero" className="hero-section"><div className="hero-grid">
    <div className="hero-copy"><h1 className="hero-title">Know where to open your <em>next store.</em></h1><p className="hero-lede">Find a neighbourhood that makes business sense.</p><p className="hero-body">Compare locations, understand the costs, and plan a retail network that fits your budget.</p><div className="hero-actions"><Link className="button" href="/app/">Explore StoreScout <Arrow/></Link><a className="button-secondary" href="#how-it-works">Take a closer look <Arrow down/></a></div><p className="hero-kicker"><span className="hero-kicker-dot"/>Local opportunity. Clear financial reasoning.</p></div>
    <div className="hero-3d-wrapper" aria-hidden="true"><HeroLanyard still={!ready||flat||!!reduced} paused={paused||!visible}/></div>
   </div></section>
   <div className="retail-strip"><span>Understand the place</span><span>Test the economics</span><span>Plan the network</span></div>
   <section id="how-it-works" className="section-wrapper tint-bg">
    <div className="section-heading-row"><div><h2>A place. A plan.<br/>A clearer decision.</h2><p className="section-intro-text">Bring your expansion plan into focus, one decision at a time.</p></div><a className="text-link" href="#daypart-dna">Explore the neighbourhood <Arrow down/></a></div>
    <div className="journey-layout"><Reveal paused={still}><RetailScene paused={still}/></Reveal><ol className="journey-steps"><li><span>01</span><div><h3>Set the brief</h3><p>Choose your city, retail format, budget and existing stores.</p></div></li><li><span>02</span><div><h3>Read the neighbourhood</h3><p>Explore nearby customers, competing destinations and travel access.</p></div></li><li><span>03</span><div><h3>Weigh the investment</h3><p>Compare costs, risks and how each site fits your network.</p></div></li></ol></div>
   </section>
   <section id="daypart-dna" className="section-wrapper">
    <div className="section-heading-row"><div><h2>Right place.<br/>Right time.</h2><p className="section-intro-text">Office lunch hours and weekend shopping tell different stories. Explore the rhythm around a potential store.</p></div><p className="section-side-note">DaypartDNA connects nearby places with the times they matter.</p></div>
    <DaypartMap/>
    <div className="infrastructure-story"><div className="station-symbol" aria-hidden="true"><span>M</span><i/><i/></div><div><h3>What changes when the metro arrives?</h3><p>Switch between current access, a future opening and a delay. Keep the event assumptions visible before making a decision.</p></div><a className="text-link" href="/app/scenarios">Test a scenario <Arrow/></a></div>
   </section>
   <section id="failfast" className="section-wrapper tint-bg"><div className="section-heading-row"><div><h2>Look beyond<br/>the busy street.</h2><p className="section-intro-text">A great address still needs the right economics. Explore the questions worth asking before you commit.</p></div><span className="section-side-note">FailFast · Understand the risk and what could change it.</span></div><FailFastCards paused={still}/></section>
   <section id="financial-planning" className="section-wrapper"><div className="section-header-block"><h2>Make every store count.</h2><p className="section-intro-text">From a single site to your next portfolio, follow the economics across the whole network.</p></div><FinancialPlanner paused={still}/></section>
   <section id="evidence" className="section-wrapper dark-bg"><div className="section-heading-row"><div><h2>Clarity behind<br/>every decision.</h2><p className="section-intro-text">Keep what is known, estimated and assumed in view.</p></div><div className="evidence-seal" aria-hidden="true"><BrandMark size={62}/></div></div><div className="evidence-pillars-grid">
    <article className="evidence-pillar-card"><span className="evidence-index">The place</span><h3 className="pillar-title">Source information</h3><p className="pillar-desc">Population, roads, nearby destinations and store locations, with source and coverage labels.</p></article>
    <article className="evidence-pillar-card"><span className="evidence-index">The model</span><h3 className="pillar-title">Estimates</h3><p className="pillar-desc">Demand, financial outcomes and network effects, with the model and evaluation identity preserved.</p></article>
    <article className="evidence-pillar-card"><span className="evidence-index">The plan</span><h3 className="pillar-title">Your assumptions</h3><p className="pillar-desc">Rent, fit-out, operating margins and infrastructure timing. Save a new scenario when these change.</p></article>
   </div><Reveal paused={still} className="final-cta-box"><div><h2>Your next chapter<br/>starts on this street.</h2><p className="final-cta-sub">Find the place. Understand the investment.</p><Link className="button" href="/app/">Start exploring <Arrow/></Link></div><div className="closing-brand" aria-hidden="true"><BrandMark size={112}/><span>Good places.<br/>Considered decisions.</span></div></Reveal></section>
  </main>
  <footer className="footer-clean"><div className="footer-inner"><div className="footer-identity"><span className="footer-title"><BrandMark size={28}/> StoreScout</span><span className="footer-subtitle">Retail expansion, considered. · Team Elites</span></div><a href="#hero" className="footer-back-link">Back to top <Arrow/></a></div></footer>
  {ready&&!reduced&&<button className="motion-control" onClick={()=>setPaused(!paused)} aria-pressed={paused}>{paused?'Resume motion':'Pause motion'}</button>}
 </div>;
}
