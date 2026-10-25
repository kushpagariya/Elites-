'use client';
import dynamic from 'next/dynamic';
import {useCallback,useState} from 'react';
const Lanyard=dynamic(()=>import('./lanyard/Lanyard'),{ssr:false});
export default function HeroLanyard({still=false,paused=false}:{still?:boolean;paused?:boolean}){
 const [failed,setFailed]=useState(false),[loaded,setLoaded]=useState(false);
 const fail=useCallback(()=>setFailed(true),[]),ready=useCallback(()=>setLoaded(true),[]);
 return <div className={'hero-lanyard'+(loaded?' is-ready':'')}>
  {(still||failed||!loaded)&&<div className="lanyard-fallback" aria-hidden="true"><div className="fallback-strap"/><img src="/images/expansion-pass-front.svg" alt="" width="640" height="900"/></div>}
  {!still&&!failed&&<Lanyard frontImage="/images/expansion-pass-front.svg" backImage="/images/expansion-pass-back.svg" strapImage="/images/expansion-strap.svg" cardColor="#f2e8d5" strapColor="#203c32" metal="gold" finish="matte" size={.59} strapLength={.31} strapWidth={.7} damping={.88} elasticity={.2} breeze={.025} gravity={1} intro interactive={!paused} paused={paused} onFailure={fail} onReady={ready}/>}
  <p className="lanyard-hint">{still||failed?'Your expansion pass':'Drag to explore · Click to turn'}</p>
 </div>;
}
