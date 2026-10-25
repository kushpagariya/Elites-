import { Browser } from 'file:///C:/Users/ashut_2urnib0/.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs';
import { writeFileSync } from 'node:fs';
const browser = await Browser.launch();
const results = [];
try {
 for (const width of [1440, 768, 390]) {
  const page = await browser.newPage({width, height:900});
  await page.goto('http://127.0.0.1:3000', {settleMs:2500});
  results.push({width, ...await page.eval(() => ({overflow:document.documentElement.scrollWidth > innerWidth,canvas:!!document.querySelector('canvas'),cta:document.querySelector('.hero-actions a').getAttribute('href')}))});
  await page.eval(() => document.querySelector('.motion-control').click());
  await new Promise(r => setTimeout(r,300));
  results.push({width, paused:await page.eval(() => document.querySelector('.motion-control').getAttribute('aria-pressed'))});
  await page.screenshot({path:'frontend/docs/retail-review/final-'+width+'.jpg'});
  await page.eval(() => document.querySelector('.final-cta-box').scrollIntoView({block:'center',behavior:'instant'}));
  await page.screenshot({path:'frontend/docs/retail-review/cta-'+width+'.jpg'});
  results.push({width, errors:page.consoleErrors});
 }
 const reduced = await browser.newPage({width:390,height:900,reducedMotion:true});
 await reduced.goto('http://127.0.0.1:3000');
 results.push({reduced:await reduced.eval(() => ({fallback:!!document.querySelector('.retail-fallback'),canvas:!!document.querySelector('canvas'),pause:!!document.querySelector('.motion-control')}))});
 await reduced.eval(() => document.querySelector('.hero-3d-wrapper').scrollIntoView({block:'center',behavior:'instant'}));
 await reduced.screenshot({path:'frontend/docs/retail-review/reduced.jpg'});
 const app = await browser.newPage(); await app.goto('http://127.0.0.1:3000/app');
 results.push({workspace:await app.eval(()=>location.pathname),errors:app.consoleErrors});
 console.log(JSON.stringify(results,null,2));
 writeFileSync('frontend/docs/retail-review/interaction-results.json',JSON.stringify(results,null,2));
} finally { await browser.close(); }
