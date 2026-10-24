'use client';
import dynamic from 'next/dynamic';
import Image from 'next/image';
import {useCallback,useRef,useState,type ReactNode} from 'react';
import {motion,useInView,useReducedMotion,useScroll,useTransform} from 'motion/react';
import RetailBackdrop from './RetailBackdrop';
const City=dynamic(()=>import('./City'),{ssr:false});
export function Reveal({children,className='',paused=false}:{children:ReactNode;className?:string;paused?:boolean}){
 const ref=useRef<HTMLDivElement>(null),reduced=useReducedMotion();
 const {scrollYProgress}=useScroll({target:ref,offset:['start end','end start']});
 const transform=useTransform(scrollYProgress,[0,.45,1],['translateY(24px)','translateY(0px)','translateY(-16px)']);
 return <motion.div ref={ref} className={className} style={{transform:reduced||paused?'none':transform}}>{children}</motion.div>;
}
export default function RetailScene({kind='neighbourhood',paused=false}:{kind?:'neighbourhood'|'risk'|'portfolio';paused?:boolean}){
 const ref=useRef<HTMLDivElement>(null),reduced=useReducedMotion(),inView=useInView(ref,{margin:'100px'});
 const [failed,setFailed]=useState(false);const failure=useCallback(()=>setFailed(true),[]);
 const {scrollYProgress}=useScroll({target:ref,offset:['start end','end start']});
 const transform=useTransform(scrollYProgress,[0,1],['translateY(12px)','translateY(-12px)']);
 if(kind==='neighbourhood')return <div ref={ref} className="neighbourhood-model" aria-hidden="true">{reduced||failed||!inView?<RetailBackdrop/>:<City paused={paused||!inView} onFailure={failure}/>}<span className="model-caption">A neighbourhood, seen in context.</span></div>;
 const risk=kind==='risk';
 return <motion.figure ref={ref} className={'editorial-visual visual-'+kind} style={{transform:reduced||paused?'none':transform}}>
  <Image src={risk?'/images/retail-due-diligence.png':'/images/retail-network.png'} alt={risk?'Miniature corner grocery beside a magnifying glass and a key, illustrating investment due diligence.':'A city planning map with three connected location pins, illustrating portfolio planning.'} width={1536} height={1024} sizes="(max-width:768px) 100vw,50vw"/>
  <figcaption>{risk?'Look closer before you commit.':'A connected plan for your next chapter.'}<span>Concept illustration</span></figcaption>
 </motion.figure>;
}
