// Isolated map/render verification only: labelled project inputs, no financial responses.
const http = require("node:http"),
  fs = require("node:fs"),
  path = require("node:path");
const root = path.resolve(__dirname, "../../data/demo");
const read = (name) =>
  JSON.parse(fs.readFileSync(path.join(root, name + ".json"), "utf8"));
const assumptions = {
  demand_multiplier: 1,
  rent_multiplier: 1,
  site_overrides: {},
  infrastructure_state: "current",
  infrastructure_effect_fraction: 0,
  opening_date: null,
  delay_months: 24,
  gross_margin_fraction: null,
  operating_cost_multiplier: 1,
  competition_multiplier: 1,
  valuation_date: "2026-10-24",
};
http
  .createServer((req, res) => {
    res.setHeader("Access-Control-Allow-Origin", "http://127.0.0.1:3002");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.setHeader("Content-Type", "application/json");
    if (req.method === "OPTIONS") {
      res.writeHead(204);
      return res.end();
    }
    let value;
    const url = req.url;
    if (url === "/api/v1/projects/demo") value = read("project");
    else if (url === "/api/v1/projects/demo/scenarios")
      value = [
        {
          scenario_id: "baseline",
          project_id: "demo",
          base_scenario_id: null,
          name: "Map preview · synthetic baseline",
          budget_inr: read("project").budget_inr,
          assumptions,
        },
      ];
    else if (url === "/api/v1/projects/demo/infrastructure")
      value = read("infrastructure");
    else {
      res.writeHead(501);
      return res.end(
        JSON.stringify({
          error: {
            code: "UNAVAILABLE",
            message: "Analysis is not part of this isolated map preview.",
            details: [],
          },
        }),
      );
    }
    res.end(
      JSON.stringify({
        data: value,
        meta: { contract_version: "1", fixture_id: "demo-1" },
      }),
    );
  })
  .listen(8400, "127.0.0.1", () =>
    console.log("TEST-ONLY map input server: 8400"),
  );
