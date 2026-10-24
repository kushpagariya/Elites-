// TEST-ONLY synthetic state; no application fixture mode or live backend.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
for (const ext of [".ts", ".tsx"])
  require.extensions[ext] = (module, file) =>
    module._compile(
      ts.transpileModule(fs.readFileSync(file, "utf8"), {
        compilerOptions: {
          module: ts.ModuleKind.CommonJS,
          target: ts.ScriptTarget.ES2022,
          jsx: ts.JsxEmit.ReactJSX,
          esModuleInterop: true,
        },
      }).outputText,
      file,
    );
let workspace;
const original = Module._load;
Module._load = function (name, parent, isMain) {
  if (name === "@/lib/workspace") return { useWorkspace: () => workspace };
  if (name === "next/link")
    return ({ children, ...props }) =>
      React.createElement("a", props, children);
  if (name === "./LocationMap" || name === "@/features/explore/LocationMap")
    return {
      __esModule: true,
      default: () => React.createElement("div", null, "Map surface"),
    };
  if (name.startsWith("@/"))
    name = path.resolve(__dirname, "../src", name.slice(2));
  return original.call(this, name, parent, isMain);
};
const Explore = require("../src/features/explore/Explore.tsx").default;
const CashflowComparison = require("../src/features/explore/CashflowComparison.tsx").default;
const Scenarios = require("../src/features/scenarios/Scenarios.tsx").default;
const Portfolio = require("../src/features/portfolio/Portfolio.tsx").default;
const guards = require("../src/lib/guards.ts");
const assumptions = {
  demand_multiplier: 1,
  rent_multiplier: 1,
  site_overrides: {},
  infrastructure_state: "current",
  infrastructure_effect_fraction: 0,
  opening_date: null,
  delay_months: 24,
  operating_cost_multiplier: 1,
  competition_multiplier: 1,
  gross_margin_fraction: null,
};
function setup() {
  const sites = ["a", "b"].map((id, i) => ({
    site_id: id,
    name: "Candidate " + id,
    store_size_sqm: 100,
    capex_inr: 100,
    monthly_rent_inr: 10,
    annual_opex_inr: 10,
    gross_margin_fraction: 0.3,
  }));
  const scenario = {
    scenario_id: "saved",
    project_id: "demo",
    name: "Saved",
    budget_inr: 1000,
    assumptions,
  };
  const analyses = sites.map((s) => ({
    site_id: s.site_id,
    annual_revenue_inr: 1000,
    operating_profit_inr: 200,
    npv_inr: 100,
    roi_fraction: 0.2,
    payback_years: null,
    lost_existing_contribution_inr: 5,
    annual_cashflows_inr: [195],
    drivers: ["Computed driver"],
    source_ids: ["synthetic-unit"],
    failfast: {
      status: "VIABLE",
      failed_rule_ids: [],
      reasons: [],
      rescue_status: "NOT_REQUESTED",
      max_viable_monthly_rent_inr: null,
      required_sales_multiplier: null,
    },
    dayparts: [
      {
        time_bin: "weekday_lunch",
        opportunity_index: 0,
        raw_opportunity: 0,
        support_count: 1,
        categories: [{ category: "office", count: 1, weighted_opportunity: 0 }],
        source_ids: ["synthetic-unit"],
        source_status: "ASSUMED",
        reliability: "Unit proxy",
        observed_at: null,
        reason: null,
      },
    ],
  }));
  workspace = {
    project: {
      data: {
        city: "Unit city",
        category: "grocery",
        source_status: "SYNTHETIC",
        sites,
        stores: [],
      },
    },
    scenario,
    draft: {
      base_scenario_id: "saved",
      name: "New",
      budget_inr: 1000,
      assumptions,
    },
    current: true,
    evaluation: {
      data: {
        evaluation_id: "eval-unit",
        scenario_id: "saved",
        site_analyses: analyses,
        rankings: ["a", "b"],
      },
    },
    selection: ["a", "b"],
    activePeriod: "weekday_lunch",
    focusedSiteId: "a",
    infrastructure: [],
    acknowledged: [],
    maxStores: 2,
  };
  return workspace;
}
test("comparison renders saved financials and six daypart controls; supported zero differs from missing", () => {
  setup();
  let html = renderToStaticMarkup(React.createElement(Explore));
  assert.match(html, /Operating profit/);
  assert.match(html, /0\.0 \/ 100/);
  assert.match(html, /Supported evidence indicates zero/);
  assert.equal((html.match(/aria-pressed=/g) || []).length, 16);
  assert.match(html, /Detailed Comparison/);
  assert.match(html, /Night · weekdays 20–06/);
  workspace.evaluation.data.site_analyses[0].dayparts[0].opportunity_index =
    null;
  workspace.evaluation.data.site_analyses[0].dayparts[0].reason =
    "No supported evidence";
  html = renderToStaticMarkup(React.createElement(Explore));
  assert.match(html, /Unknown/);
  assert.match(html, /No supported evidence/);
});
test("advanced scenario fields are enabled with labelled ranges and immutable save action", () => {
  setup();
  const html = renderToStaticMarkup(React.createElement(Scenarios));
  assert.match(html, /Operating cost change/);
  assert.match(html, /Competition adjustment/);
  assert.match(html, /Gross margin/);
  assert.match(html, /max="100"/);
  assert.doesNotMatch(html, /<fieldset disabled/);
  assert.match(html, /Save &amp; analyse changes/);
  assert.doesNotMatch(html, /awaiting agreement|contract support|TODO/);
});
test("unavailable optimization has no displayed financial recommendation and disables export", () => {
  setup();
  workspace.portfolio = {
    portfolio_run_id: "unit",
    evaluation_id: "eval-unit",
    selected_site_ids: [],
    budget_used_inr: 0,
    budget_unused_inr: 1000,
    full_network_npv_inr: 0,
    status: "UNKNOWN",
    solver_status: "UNAVAILABLE",
    evaluated_subsets: 0,
    total_subsets: 4,
  };
  let html = renderToStaticMarkup(React.createElement(Portfolio));
  assert.match(html, /No investment recommendation/);
  assert.match(html, /<button[^>]*disabled=""[^>]*>Download decision report/);
  workspace.portfolio.solver_status = "OPTIMAL";
  workspace.portfolio.status = "FULL_NETWORK_EXACT";
  html = renderToStaticMarkup(React.createElement(Portfolio));
  assert.match(html, /Empty portfolio/);
  assert.doesNotMatch(
    html,
    /<button[^>]*disabled=""[^>]*>Download decision report/,
  );
});
test("rescue guard rejects unverified, foreign-shape or out-of-bounds thresholds", () => {
  const valid = {
    evaluation_id: "e",
    site_id: "a",
    lever: "rent",
    status: "SOLVED",
    lower_bound: 0,
    upper_bound: 100,
    threshold: 20,
    verified: true,
    npv_at_threshold: 0,
    reasons: [],
    remaining_failed_rule_ids: ["CAPEX_OVER_BUDGET"],
  };
  assert.equal(guards.isRescue(valid), true);
  assert.equal(guards.isRescue({ ...valid, verified: false }), false);
  assert.equal(guards.isRescue({ ...valid, threshold: 101 }), false);
  assert.equal(guards.isRescue({ ...valid, npv_at_threshold: NaN }), false);
});

test("cash flow chart preserves saved negative, zero and missing values alongside exact data", () => {
  const sites = [{ site_id: "a", name: "Site A" }, { site_id: "b", name: "Site B" }];
  const analyses = new Map([
    ["a", { annual_cashflows_inr: [-100, 0, 100] }],
    ["b", { annual_cashflows_inr: [50] }],
  ]);
  const html = renderToStaticMarkup(React.createElement(CashflowComparison, { sites, analyses }));
  assert.match(html, /Annual incremental cash flow chart/);
  assert.match(html, /-₹100\.00/);
  assert.match(html, /₹0\.00/);
  assert.match(html, /Unavailable/);
  assert.match(html, /View exact cash flows/);
  assert.match(html, /width:50%;left:0%/);
  assert.match(html, /width:50%;left:50%/);
  assert.match(html, /width:25%;left:50%/);
  assert.doesNotMatch(html, /NaN|Infinity/);
});
test("cash flow chart has an honest unavailable state without saved series", () => {
  const html = renderToStaticMarkup(React.createElement(CashflowComparison, {
    sites: [{ site_id: "a", name: "Site A" }], analyses: new Map(),
  }));
  assert.match(html, /have not been supplied/);
  assert.doesNotMatch(html, /cashflow-track/);
});
module.exports = {
  Explore,
  setup,
  setWorkspace: (value) => {
    workspace = value;
  },
};
