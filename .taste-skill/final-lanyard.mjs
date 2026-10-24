import {Browser} from 'file:///C:/Users/ashut_2urnib0/.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs';
const b=await Browser.launch();try{
 for(const width of [1440,390]){
  const p=await b.newPage({width,height:900});await p.goto('http://127.0.0.1:3000',{settleMs:100});
  await new Promise(r=>setTimeout(r,900));await p.screenshot({path:'frontend/docs/retail-review-v3/final-drop-'+width+'.jpg'});
  await new Promise(r=>setTimeout(r,2500));await p.screenshot({path:'frontend/docs/retail-review-v3/final-hero-'+width+'.jpg'});
  if(width===1440){const rect=await p.eval(()=>{const b=document.querySelectorAll('.pill-link')[1].getBoundingClientRect();return{x:b.x+b.width/2,y:b.y+b.height/2};});await p.send('Input.dispatchMouseEvent',{type:'mouseMoved',...rect});await new Promise(r=>setTimeout(r,400));await p.screenshot({path:'frontend/docs/retail-review-v3/final-hover.jpg'});}
  await p.eval(()=>document.querySelector('.motion-control').click());console.log(JSON.stringify({width,pause:await p.eval(()=>document.querySelector('.motion-control').getAttribute('aria-pressed')),errors:p.consoleErrors}));
 }
}finally{await b.close();}
