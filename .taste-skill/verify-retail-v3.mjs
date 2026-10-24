import {Browser} from 'file:///C:/Users/ashut_2urnib0/.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const out='frontend/docs/retail-review-v3';mkdirSync(out,{recursive:true});
const b=await Browser.launch();const results=[];
try{
 for(const width of [1440,768,390]){
  const p=await b.newPage({width,height:900});await p.goto('http://127.0.0.1:3000',{settleMs:300});
  await p.screenshot({path:out+'/intro-'+width+'.jpg'});await new Promise(r=>setTimeout(r,2400));
  await p.screenshot({path:out+'/hero-'+width+'.jpg'});
  results.push({width,hero:await p.eval(()=>({overflow:document.documentElement.scrollWidth>innerWidth,canvas:!!document.querySelector('.lanyard-canvas'),fallback:!!document.querySelector('.hero-lanyard .lanyard-fallback'),nav:document.querySelectorAll('.pill-link').length}))});
  if(width<900){await p.eval(()=>document.querySelector('.pill-toggle').click());await new Promise(r=>setTimeout(r,100));await p.screenshot({path:out+'/menu-'+width+'.jpg'});results.push({width,menu:await p.eval(()=>document.querySelector('.pill-toggle').getAttribute('aria-expanded'))});await p.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});results.push({width,escape:await p.eval(()=>document.querySelector('.pill-toggle').getAttribute('aria-expanded'))});}
  for(const id of ['how-it-works','failfast','financial-planning']){await p.eval(id=>document.getElementById(id).scrollIntoView({behavior:'instant',block:'start'}),id);await new Promise(r=>setTimeout(r,600));await p.screenshot({path:out+'/'+id+'-'+width+'.jpg'});}
  results.push({width,images:await p.eval(()=>Array.from(document.querySelectorAll('.editorial-visual img')).map(i=>({loaded:i.complete&&i.naturalWidth>0,src:i.getAttribute('src')}))),errors:p.consoleErrors});
 }
 const reduced=await b.newPage({width:390,height:900,reducedMotion:true});await reduced.goto('http://127.0.0.1:3000');results.push({reduced:await reduced.eval(()=>({canvas:!!document.querySelector('.lanyard-canvas'),fallback:!!document.querySelector('.lanyard-fallback')}))});
 console.log(JSON.stringify(results,null,2));writeFileSync(out+'/results.json',JSON.stringify(results,null,2));
}finally{await b.close();}
