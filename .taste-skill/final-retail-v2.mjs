import { Browser } from 'file:///C:/Users/ashut_2urnib0/.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs';
const browser=await Browser.launch();
try{for(const width of [1440,390]){
 const p=await browser.newPage({width,height:900});await p.goto('http://127.0.0.1:3000');
 await p.screenshot({path:'frontend/docs/retail-review-v2/final-hero-'+width+'.jpg'});
 await p.eval(()=>document.getElementById('how-it-works').scrollIntoView({behavior:'instant'}));await new Promise(r=>setTimeout(r,250));
 await p.screenshot({path:'frontend/docs/retail-review-v2/final-shops-'+width+'.jpg'});
 await p.eval(()=>document.querySelector('.map-insight-card').scrollIntoView({behavior:'instant'}));await new Promise(r=>setTimeout(r,250));
 await p.screenshot({path:'frontend/docs/retail-review-v2/final-chart-'+width+'.jpg'});
 console.log(JSON.stringify({width,header:await p.eval(()=>getComputedStyle(document.querySelector('.header')).backgroundColor),syntheticLabel:await p.eval(()=>document.querySelector('.insight-kicker').textContent),errors:p.consoleErrors}));
}}finally{await browser.close();}
