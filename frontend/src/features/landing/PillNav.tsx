'use client';
import Link from 'next/link';
import {useEffect,useRef,useState,type ReactNode} from 'react';
type Item={label:string;href:string};
type Props={logo:ReactNode|string;logoAlt?:string;items:Item[];activeHref?:string;itemStyle?:'pill';hoverEffect?:'fill';indicator?:'dot'};
export default function PillNav({logo,logoAlt='StoreScout',items,activeHref='#hero'}:Props){
 const [active,setActive]=useState(activeHref),[open,setOpen]=useState(false);
 const ref=useRef<HTMLElement>(null),toggle=useRef<HTMLButtonElement>(null);
 useEffect(()=>{
  const observer=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting)setActive('#'+e.target.id);},{rootMargin:'-15% 0px -65% 0px'});
  items.forEach(item=>{if(item.href.startsWith('#')){const node=document.querySelector(item.href);if(node)observer.observe(node);}});
  return()=>observer.disconnect();
 },[items]);
 useEffect(()=>{
  if(!open)return;
  const outside=(e:PointerEvent)=>{if(!ref.current?.contains(e.target as Node))setOpen(false);};
  const escape=(e:KeyboardEvent)=>{if(e.key==='Escape'){setOpen(false);toggle.current?.focus();}};
  document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape);
  return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);};
 },[open]);
 return <header ref={ref} className="pill-header">
  <Link className="wordmark" href="/" aria-label={logoAlt+' home'}>{typeof logo==='string'?<img src={logo} alt="" width={36} height={40}/>:logo}<span>Store<span className="wordmark-light">Scout</span></span></Link>
  <nav id="landing-pill-nav" className={'pill-nav-links'+(open?' is-open':'')} aria-label="Main navigation">
   {items.map(item=><a key={item.href} className={'pill-link'+(active===item.href?' is-active':'')} href={item.href} aria-current={active===item.href?'location':undefined} onClick={()=>{setActive(item.href);setOpen(false);}}><span className="pill-fill" aria-hidden="true"/><span className="pill-label"><span>{item.label}</span><span aria-hidden="true" className="pill-label-hover">{item.label}</span></span><span className="pill-dot" aria-hidden="true"/></a>)}
  </nav>
  <div className="pill-actions"><Link className="pill-demo" href="/app/">Explore demo <span aria-hidden="true">↗</span></Link><button ref={toggle} className="pill-toggle" aria-label={open?'Close navigation':'Open navigation'} aria-expanded={open} aria-controls="landing-pill-nav" onClick={()=>setOpen(!open)}><span/><span/></button></div>
 </header>;
}
