// Run against a local isolated verification DB. Exercises real API + UI adapters.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import fs from "node:fs";
const base = process.env.STORESCOUT_TEST_API ?? "http://127.0.0.1:8000/api/v1";
const target = new URL(base);
if (target.protocol !== "http:" || !["127.0.0.1", "localhost"].includes(target.hostname) || target.pathname !== "/api/v1")
  throw Error("Use a local verification API.");
process.env.NEXT_PUBLIC_API_BASE_URL = base;
const originalFetch = globalThis.fetch;
const smokeEmail = `smoke-${crypto.randomUUID()}@example.test`;
const smokePassword = crypto.randomUUID();
const registration = await originalFetch(base + '/auth/register', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({name: 'Smoke account', email: smokeEmail, password: smokePassword}),
});
assert.equal(registration.status, 201);
let sessionCookie = registration.headers.get('set-cookie').split(';')[0];
globalThis.fetch = (input, init = {}) => {
  const headers = new Headers(init.headers);
  if (new URL(String(input)).origin === target.origin) headers.set('Cookie', sessionCookie);
  return originalFetch(input, {...init, headers});
};
const require = createRequire(import.meta.url);
const ts = require("typescript");
require.extensions[".ts"] = (module, file) => module._compile(
  ts.transpileModule(fs.readFileSync(file, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, file);
const api = require("../src/lib/api.ts");
const { isEvaluation, isRescue, isPortfolio } = require("../src/lib/guards.ts");
const project = await api.loadProject();
assert.equal(project.data.sites.length, 10);
assert.equal(project.data.stores.length, 4);
assert.equal(project.data.source_status, "ASSUMED");
const initial = await api.getScenarios();
const baseline = initial.data.find(item => item.scenario_id === "baseline");
assert.ok(baseline);
const original = structuredClone(baseline);
const saved = [];
for (const state of ["current", "opens", "delayed"]) {
  const scenario = await api.createScenario({
    base_scenario_id: "baseline",
    name: "Integration smoke " + state + " " + Date.now(),
    budget_inr: state === "delayed" ? 0 : baseline.budget_inr,
    assumptions: { ...structuredClone(baseline.assumptions),
      rent_multiplier: 1.2, infrastructure_state: state,
      opening_date: state === "current" ? null : "2028-04-01",
      infrastructure_effect_fraction: state === "current" ? 0 : 0.1, delay_months: 24 },
  });
  const evaluation = await api.evaluateScenario(scenario.data.scenario_id);
  assert.ok(isEvaluation(evaluation.data));
  assert.equal(evaluation.data.scenario_id, scenario.data.scenario_id);
  assert.equal(evaluation.data.method_mode, "model_simulated");
  assert.ok(evaluation.data.model_artifact_id);
  const geo = await api.getGeoContext(evaluation.data.evaluation_id);
  assert.equal(geo.data.evaluation_id, evaluation.data.evaluation_id);
  assert.equal(geo.data.catchments.length, 10);
  const dayparts = await api.getDayparts(evaluation.data.evaluation_id, "weekday_lunch");
  assert.equal(dayparts.data.sites.length, 10);
  assert.ok(dayparts.data.sites.every(item => item.profiles.length === 1));
  saved.push(scenario.data);
  if (state === "delayed") {
    const empty = await api.optimisePortfolio({ evaluation_id: evaluation.data.evaluation_id, max_stores: 0 });
    assert.deepEqual(empty.data.selected_site_ids, []);
    assert.equal(empty.data.budget_used_inr, 0);
    assert.equal(empty.data.full_network_npv_inr, 0);
  }
}
const commercial = await api.createScenario({
  base_scenario_id: "baseline", name: "Integration smoke viable case " + Date.now(),
  assumptions: { ...structuredClone(baseline.assumptions),
    demand_multiplier: 3, rent_multiplier: 0.3 },
});
const evaluated = await api.evaluateScenario(commercial.data.scenario_id);
const repeated = await api.evaluateScenario(commercial.data.scenario_id);
assert.equal(evaluated.data.evaluation_id, repeated.data.evaluation_id);
const acknowledgements = evaluated.data.site_analyses.filter(row => row.failfast.status === "AT_RISK").map(row => row.site_id);
const portfolio = await api.optimisePortfolio({
  evaluation_id: evaluated.data.evaluation_id, max_stores: 2, acknowledged_risk_site_ids: acknowledgements,
});
assert.ok(isPortfolio(portfolio.data));
assert.equal(portfolio.data.status, "FULL_NETWORK_EXACT");
assert.equal(portfolio.data.evaluated_subsets, portfolio.data.total_subsets);
assert.ok(portfolio.data.selected_site_ids.length > 0);
assert.ok(portfolio.data.budget_used_inr <= commercial.data.budget_inr);
const report = await api.getSavedReport(evaluated.data.evaluation_id, portfolio.data.portfolio_run_id);
assert.equal(await report.blob.slice(0,5).text(),'%PDF-');
assert.match(report.filename,/\.pdf$/);
const workspaceState = {scenario_id: commercial.data.scenario_id, evaluation_id: evaluated.data.evaluation_id, portfolio_run_id: portfolio.data.portfolio_run_id};
await api.saveWorkspace(workspaceState);
await api.saveWorkspace({scenario_id:'baseline', evaluation_id:null, portfolio_run_id:null});
await api.saveWorkspace(workspaceState);
const signedOut = await originalFetch(base + '/auth/logout', {method:'POST', headers:{Cookie:sessionCookie}});
assert.equal(signedOut.status, 200);
assert.equal((await originalFetch(base + '/auth/me', {headers:{Cookie:sessionCookie}})).status, 401);
const signedIn = await originalFetch(base + '/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:smokeEmail,password:smokePassword})});
assert.equal(signedIn.status, 200);
sessionCookie = signedIn.headers.get('set-cookie').split(';')[0];
const restoredWorkspace = await api.getWorkspace();
for (const [key,value] of Object.entries(workspaceState)) assert.equal(restoredWorkspace.data[key], value);
assert.equal(restoredWorkspace.data.analysis_current, true);
const rescueScenario = await api.createScenario({
  base_scenario_id: "baseline", name: "Integration smoke rescue " + Date.now(),
  assumptions: { ...structuredClone(baseline.assumptions), demand_multiplier: 2 },
});
const rescueEvaluation = await api.evaluateScenario(rescueScenario.data.scenario_id);
const rescue = await api.requestRescue("site-02", {
  evaluation_id: rescueEvaluation.data.evaluation_id, lever: "rent", lower_bound: 0, upper_bound: 1000000,
});
assert.ok(isRescue(rescue.data));
assert.equal(rescue.data.status, "SOLVED");
const applied = await api.createScenario({
  base_scenario_id: rescueScenario.data.scenario_id, name: "Integration smoke applied rescue " + Date.now(),
  assumptions: { ...structuredClone(rescueScenario.data.assumptions),
    site_overrides: { ...rescueScenario.data.assumptions.site_overrides,
      "site-02": { monthly_rent_inr: rescue.data.threshold } } },
});
const rescued = await api.evaluateScenario(applied.data.scenario_id);
assert.ok(Math.abs(rescued.data.site_analyses.find(row => row.site_id === "site-02").npv_inr - rescue.data.npv_at_threshold) <= 1);
const reopened = await api.getScenarios();
assert.deepEqual(reopened.data.find(item => item.scenario_id === "baseline"), original);
for (const item of saved) assert.deepEqual(reopened.data.find(row => row.scenario_id === item.scenario_id), item);
await assert.rejects(api.createScenario({
  base_scenario_id: "baseline", name: "Invalid smoke case", budget_inr: -1,
  assumptions: baseline.assumptions,
}), error => error.status === 422);
console.log(JSON.stringify({
  project: "demo", candidates: 10, branches: 4, method: evaluated.data.method_mode,
  infrastructure_states: saved.map(item => item.assumptions.infrastructure_state),
  geo_and_dayparts: "passed", rescue_and_apply: "passed", baseline_unchanged: true,
  selected_sites: portfolio.data.selected_site_ids, subset_count: portfolio.data.evaluated_subsets,
  portfolio_and_saved_report: "passed", invalid_budget: 422,
  sign_in_and_workspace_restore: "passed",
}, null, 2));
