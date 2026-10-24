// TEST-ONLY synthetic transport payloads. They are never imported by the application.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const ts = require("typescript");
require.extensions[".ts"] = (module, file) =>
  module._compile(
    ts.transpileModule(fs.readFileSync(file, "utf8"), {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
      },
    }).outputText,
    file,
  );
const model = require("../src/lib/workspace-model.ts");
const guards = require("../src/lib/guards.ts");
const api = require("../src/lib/api.ts");
const format = require("../src/lib/format.ts");
const assumptions = {
  demand_multiplier: 1,
  rent_multiplier: 1,
  site_overrides: { a: { monthly_rent_inr: 0 } },
  infrastructure_state: "current",
  infrastructure_effect_fraction: 0,
  opening_date: null,
  delay_months: 24,
};
const scenario = {
  scenario_id: "baseline",
  project_id: "demo",
  base_scenario_id: null,
  name: "Current baseline",
  budget_inr: 0,
  assumptions,
};
const project = {
  project_id: "demo",
  city: "Synthetic test city",
  category: "grocery",
  budget_inr: 0,
  discount_rate_fraction: 0.12,
  projection_years: 5,
  source_status: "SYNTHETIC",
  stores: [],
  sites: [
    {
      site_id: "a",
      name: "Test candidate",
      latitude: 19,
      longitude: 73,
      store_size_sqm: 100,
      capex_inr: 0,
      monthly_rent_inr: 0,
      annual_opex_inr: 0,
      gross_margin_fraction: 0.3,
    },
  ],
};
const analysis = {
  site_id: "a",
  annual_revenue_inr: 0,
  lost_existing_contribution_inr: 0,
  annual_cashflows_inr: [0],
  npv_inr: 0,
  roi_fraction: null,
  payback_years: null,
  failfast: {
    status: "VIABLE",
    failed_rule_ids: [],
    reasons: [],
    max_viable_monthly_rent_inr: null,
    required_sales_multiplier: null,
    rescue_status: "NOT_REQUESTED",
  },
  drivers: [],
  source_ids: ["synthetic-test"],
};
const evaluation = {
  evaluation_id: "test-evaluation",
  project_id: "demo",
  scenario_id: "baseline",
  created_at_utc: "2026-10-24T00:00:00Z",
  method_mode: "scenario_assumptions",
  model_artifact_id: null,
  rankings: ["a"],
  site_analyses: [analysis],
};
const portfolio = {
  portfolio_run_id: "test-run",
  evaluation_id: "test-evaluation",
  selected_site_ids: [],
  budget_used_inr: 0,
  budget_unused_inr: 0,
  full_network_npv_inr: 0,
  status: "FULL_NETWORK_EXACT",
  evaluated_subsets: 1,
  total_subsets: 1,
};
const envelope = (data) => ({
  data,
  meta: { contract_version: "1", fixture_id: "test-only" },
});
const response = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });
function mock(t, fetch) {
  const original = global.fetch;
  global.fetch = fetch;
  t.after(() => {
    global.fetch = original;
  });
}

test("reverse completion order cannot commit an obsolete request", async () => {
  const clock = new model.RequestClock();
  const old = clock.next();
  const next = clock.next();
  const committed = [];
  await Promise.all([
    new Promise((r) =>
      setTimeout(() => {
        if (clock.accepts(old)) committed.push("old");
        r();
      }, 15),
    ),
    Promise.resolve().then(() => {
      if (clock.accepts(next)) committed.push("new");
    }),
  ]);
  assert.deepEqual(committed, ["new"]);
});
test("an edit invalidates an in-flight request even without a replacement request", () => {
  const clock = new model.RequestClock();
  const request = clock.next();
  clock.next();
  assert.equal(clock.accepts(request), false);
});
test("stale, busy and mismatched evaluations disable dependent actions", () => {
  assert.equal(
    model.isCurrentEvaluation(evaluation, "baseline", false, false),
    true,
  );
  for (const values of [
    [evaluation, "other", false, false],
    [evaluation, "baseline", true, false],
    [evaluation, "baseline", false, true],
    [null, "baseline", false, false],
  ])
    assert.equal(model.isCurrentEvaluation(...values), false);
});
test("scenario drafts preserve complete snapshots and never mutate baseline", () => {
  const draft = model.scenarioDraft(scenario);
  draft.assumptions.site_overrides.a.monthly_rent_inr = 999;
  assert.equal(scenario.assumptions.site_overrides.a.monthly_rent_inr, 0);
  assert.deepEqual(
    Object.keys(draft.assumptions).sort(),
    Object.keys(assumptions).sort(),
  );
  assert.equal(draft.base_scenario_id, "baseline");
});
test("runtime guards accept zero values and nullable ROI/payback", () => {
  assert.ok(guards.isProject(project));
  assert.ok(guards.isScenario(scenario));
  assert.ok(guards.isEvaluation(evaluation));
  assert.ok(guards.isPortfolio(portfolio));
});
test("partial evaluation and non-finite financial responses are rejected", () => {
  assert.equal(
    guards.isEvaluation({
      ...evaluation,
      site_analyses: [{ ...analysis, npv_inr: NaN }],
    }),
    false,
  );
  assert.equal(
    guards.isEvaluation({
      ...evaluation,
      site_analyses: [{ ...analysis, failfast: { status: "VIABLE" } }],
    }),
    false,
  );
  assert.equal(
    model.matchesEvaluation(
      { ...evaluation, site_analyses: [] },
      "baseline",
      project,
    ),
    false,
  );
});
test("evaluation identity, candidate identity and model mode are checked", () => {
  assert.ok(model.matchesEvaluation(evaluation, "baseline", project));
  assert.equal(
    model.matchesEvaluation(
      { ...evaluation, scenario_id: "late" },
      "baseline",
      project,
    ),
    false,
  );
  assert.equal(
    model.matchesEvaluation(
      { ...evaluation, site_analyses: [{ ...analysis, site_id: "foreign" }] },
      "baseline",
      project,
    ),
    false,
  );
  assert.equal(
    model.matchesEvaluation(
      { ...evaluation, method_mode: "model_simulated" },
      "baseline",
      project,
    ),
    false,
  );
});
test("duplicate candidate IDs cannot pass project validation", () =>
  assert.equal(
    guards.isProject({
      ...project,
      sites: [project.sites[0], project.sites[0]],
    }),
    false,
  ));
test("partial enumeration cannot be labelled exact", () => {
  assert.equal(
    guards.isPortfolio({
      ...portfolio,
      evaluated_subsets: 1,
      total_subsets: 2,
    }),
    false,
  );
  assert.ok(
    guards.isPortfolio({
      ...portfolio,
      status: "FEASIBLE_PARTIAL",
      evaluated_subsets: 1,
      total_subsets: 2,
    }),
  );
  assert.ok(
    guards.isPortfolio({
      ...portfolio,
      status: "UNKNOWN",
      evaluated_subsets: 0,
      total_subsets: 2,
    }),
  );
});
test("empty portfolio and max-count zero are valid", () =>
  assert.ok(model.matchesPortfolio(portfolio, evaluation, 0, [])));
test("risk acknowledgements are required and bound to an evaluation", () => {
  const risk = {
    ...evaluation,
    site_analyses: [
      { ...analysis, failfast: { ...analysis.failfast, status: "AT_RISK" } },
    ],
  };
  const chosen = { ...portfolio, selected_site_ids: ["a"] };
  assert.equal(model.matchesPortfolio(chosen, risk, 1, []), false);
  assert.equal(model.matchesPortfolio(chosen, risk, 1, ["a"]), true);
  assert.equal(
    model.matchesPortfolio({ ...chosen, evaluation_id: "other" }, risk, 1, [
      "a",
    ]),
    false,
  );
  assert.equal(model.matchesPortfolio(chosen, risk, 0, ["a"]), false);
});
test("rejected and review-required sites cannot enter a portfolio", () => {
  for (const status of ["REJECTED", "REVIEW_REQUIRED"])
    assert.equal(
      model.matchesPortfolio(
        { ...portfolio, selected_site_ids: ["a"] },
        {
          ...evaluation,
          site_analyses: [
            { ...analysis, failfast: { ...analysis.failfast, status } },
          ],
        },
        1,
        ["a"],
      ),
      false,
    );
});
test("display formatting distinguishes zero from missing values", () => {
  assert.notEqual(format.money(0), format.money(null));
  assert.equal(format.percent(0.125), "12.5%");
  assert.match(format.years(null), /Not recovered/);
});
test("real adapter sends a complete immutable snapshot and accepts saved identity", async (t) => {
  mock(t, async (url, init) => {
    assert.ok(url.endsWith("projects/demo/scenarios"));
    assert.equal(init.method, "POST");
    const body = JSON.parse(init.body);
    assert.deepEqual(body.assumptions, assumptions);
    return response(
      envelope({
        ...scenario,
        scenario_id: "saved",
        base_scenario_id: "baseline",
      }),
      201,
    );
  });
  const result = await api.createScenario(model.scenarioDraft(scenario));
  assert.equal(result.data.scenario_id, "saved");
});
test("HTTP 501 remains an explicit unavailable capability", async (t) => {
  mock(t, async () =>
    response(
      {
        error: {
          code: "NOT_IMPLEMENTED",
          message: "Not connected",
          details: [],
        },
      },
      501,
    ),
  );
  await assert.rejects(
    () => api.evaluateScenario("baseline"),
    (e) => e instanceof api.ApiError && e.status === 501,
  );
});
test("network and validation failures remain distinguishable", async (t) => {
  mock(t, async () => {
    throw Error("offline");
  });
  await assert.rejects(
    () => api.loadProject(),
    (e) => e.status === 0,
  );
  global.fetch = async () =>
    response(
      {
        error: {
          message: "Correct fields",
          details: [{ field: "budget_inr", reason: "nonnegative required" }],
        },
      },
      422,
    );
  await assert.rejects(
    () => api.createScenario(model.scenarioDraft(scenario)),
    (e) =>
      e.status === 422 && e.details.error.details[0].field === "budget_inr",
  );
});
test("malformed success envelopes never become financial output", async (t) => {
  mock(t, async () => response(envelope({ evaluation_id: "incomplete" })));
  await assert.rejects(
    () => api.evaluateScenario("baseline"),
    (e) => e.status === 502,
  );
});
test("abort signals reach transport and aborted requests are not relabelled as network failure", async (t) => {
  const controller = new AbortController();
  controller.abort();
  mock(t, async (url, init) => {
    assert.equal(init.signal, controller.signal);
    throw new DOMException("aborted", "AbortError");
  });
  await assert.rejects(
    () => api.loadProject(controller.signal),
    (e) => e.name === "AbortError",
  );
});
test("report download rejects foreign identities and reopens matching content unchanged", async (t) => {
  mock(
    t,
    async () =>
      new Response("<p>foreign report</p>", {
        headers: { "content-type": "text/html" },
      }),
  );
  await assert.rejects(
    () => api.getSavedReport("test-evaluation", "test-run"),
    (e) => e.status === 409,
  );
  const text = "<p>SYNTHETIC test-evaluation test-run</p>";
  global.fetch = async () =>
    new Response(text, { headers: { "content-type": "text/html" } });
  const result = await api.getSavedReport("test-evaluation", "test-run");
  assert.equal(await result.blob.text(), text);
  assert.equal(result.text, text);
});
