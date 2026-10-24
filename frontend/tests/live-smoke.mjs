// Run only against a local, isolated verification database. Creates labelled scenarios; no resets/deletions.
import assert from 'node:assert/strict';
const base=process.env.STORESCOUT_TEST_API??'http://127.0.0.1:8000/api/v1';
const target=new URL(base); if(target.protocol!=='http:'||!['127.0.0.1','localhost'].includes(target.hostname)||target.pathname!=='/api/v1')throw Error('Use a local verification API.');
async function request(path,body){const response=await fetch(base+path,{headers:{'Content-Type':'application/json'},...(body?{method:'POST',body:JSON.stringify(body)}:{})});return {status:response.status,body:await response.json()};}
const project=await request('/projects/demo');assert.equal(project.status,200);assert.equal(project.body.data.sites.length,10);assert.equal(project.body.data.stores.length,4);assert.equal(project.body.data.source_status,'SYNTHETIC');
const initial=await request('/projects/demo/scenarios');const baseline=initial.body.data.find(s=>s.scenario_id==='baseline');assert.ok(baseline);const original=structuredClone(baseline);
const saved=[];
for(const state of ['current','opens','delayed']){
  const result=await request('/projects/demo/scenarios',{base_scenario_id:'baseline',name:'Frontend smoke — '+state+' — '+Date.now(),budget_inr:state==='delayed'?0:baseline.budget_inr,assumptions:{...structuredClone(baseline.assumptions),rent_multiplier:1.2,infrastructure_state:state,opening_date:state==='current'?null:'2028-04-01',delay_months:24}});
  assert.equal(result.status,201);assert.notEqual(result.body.data.scenario_id,'baseline');saved.push(result.body.data);
  const evaluation=await request('/projects/demo/evaluate',{scenario_id:result.body.data.scenario_id,feature_snapshot_id:'features-demo-1'});assert.equal(evaluation.status,501);assert.equal(evaluation.body.error.code,'NOT_IMPLEMENTED');
}
const reopened=await request('/projects/demo/scenarios');assert.deepEqual(reopened.body.data.find(s=>s.scenario_id==='baseline'),original);
for(const item of saved)assert.deepEqual(reopened.body.data.find(s=>s.scenario_id===item.scenario_id),item);
const invalid=await request('/projects/demo/scenarios',{base_scenario_id:'baseline',name:'Invalid test — must not persist',budget_inr:-1,assumptions:baseline.assumptions});assert.equal(invalid.status,422);
const final=await request('/projects/demo/scenarios');assert.equal(final.body.data.length,reopened.body.data.length);
console.log(JSON.stringify({project:'demo',candidates:10,branches:4,source:'SYNTHETIC',saved:saved.map(s=>({id:s.scenario_id,state:s.assumptions.infrastructure_state,budget_inr:s.budget_inr})),baseline_unchanged:true,reopen_identical:true,evaluate_status:501,invalid_status:422,invalid_saved:false},null,2));
