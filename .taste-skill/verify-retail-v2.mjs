import { Browser } from 'file:///C:/Users/ashut_2urnib0/.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs';
import { mkdirSync,writeFileSync } from 'node:fs';
const out='frontend/docs/retail-review-v2';mkdirSync(out,{recursive:true});
const browser=await Browser.launch();const results=[];
try {
 for(const width of [1440,768,390]){
  const p=await browser.newPage({width,height:900});await p.goto('http://127.0.0.1:3000',{settleMs:2000});
  results.push({width,overview:await p.eval(()=>({overflow:document.documentElement.scrollWidth>innerWidth,canvas:!!document.querySelector('canvas'),shops:document.querySelectorAll('.mini-shop').length,brand:document.querySelectorAll('.brand-mark').length}))});
  await p.screenshot({path:out+'/hero-'+width+'.jpg'});
  for(const id of ['how-it-works','daypart-dna','failfast','financial-planning','evidence']){
   await p.eval(id=>document.getElementById(id).scrollIntoView({behavior:'instant',block:'start'}),id);await new Promise(r=>setTimeout(r,400));
   await p.screenshot({path:out+'/'+id+'-'+width+'.jpg',fullPage:false});
  }
  await p.eval(()=>document.querySelector('#failfast .story-tabs button:last-child').click());
  results.push({width,risk:await p.eval(()=>({pressed:document.querySelector('#failfast .story-tabs button:last-child').getAttribute('aria-pressed'),heading:document.querySelector('.risk-explanation h3').textContent}))});
  await p.eval(()=>document.querySelector('#financial-planning .story-tabs button:last-child').click());
  results.push({width,plan:await p.eval(()=>document.querySelector('.planning-copy h3').textContent)});
  await p.eval(()=>document.querySelector('.motion-control').click());await new Promise(r=>setTimeout(r,100));
  results.push({width,paused:await p.eval(()=>document.querySelector('.landing-experience').dataset.motionPaused),errors:p.consoleErrors});
 }
 const p=await browser.newPage({width:390,height:900,reducedMotion:true});await p.goto('http://127.0.0.1:3000');
 results.push({reduced:await p.eval(()=>({canvas:!!document.querySelector('canvas'),fallback:!!document.querySelector('.retail-fallback'),motion:document.querySelector('.landing-experience').dataset.motionPaused}))});
 console.log(JSON.stringify(results,null,2));writeFileSync(out+'/results.json',JSON.stringify(results,null,2));
} finally {await browser.close();}
