const test = require("node:test"),
  assert = require("node:assert/strict"),
  fs = require("node:fs"),
  ts = require("typescript");
require.extensions[".ts"] = (m, f) =>
  m._compile(
    ts.transpileModule(fs.readFileSync(f, "utf8"), {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
      },
    }).outputText,
    f,
  );
const ui = require("../src/lib/presentation.ts");
test("percentage edits preserve canonical multiplier semantics, including zero demand", () => {
  for (const [percent, multiplier] of [
    [-100, 0],
    [-25, 0.75],
    [0, 1],
    [20, 1.2],
    [200, 3],
  ]) {
    assert.equal(ui.changeMultiplier(percent), multiplier);
    assert.equal(ui.changePercent(multiplier), percent);
  }
});
test("business status labels retain all four distinct analytical classifications", () => {
  assert.deepEqual(
    ["VIABLE", "AT_RISK", "REJECTED", "REVIEW_REQUIRED"].map(ui.statusLabel),
    ["Viable", "At Risk", "Rejected", "Needs Review"],
  );
  assert.equal(ui.statusLabel(undefined), "Not evaluated");
});
test("six canonical periods remain accessible and monetary missing values differ from zero", () => {
  assert.equal(new Set(ui.PERIODS.map((p) => p[0])).size, 6);
  assert.equal(ui.compactMoney(null), "—");
  assert.equal(ui.compactMoney(NaN), "—");
  assert.notEqual(ui.compactMoney(0), "—");
  assert.ok(ui.compactMoney(100000).includes("L"));
});

const mapData = require("../src/lib/map-data.ts");
test("only valid supplied geographic geometry is eligible for infrastructure overlays", () => {
  const base = {};
  assert.equal(mapData.hasMapGeometry(base), false);
  assert.equal(
    mapData.hasMapGeometry({
      geometry: { type: "Point", coordinates: [73.06, 19.065] },
    }),
    true,
  );
  assert.equal(
    mapData.hasMapGeometry({
      geometry: { type: "Point", coordinates: [200, 100] },
    }),
    false,
  );
  assert.equal(
    mapData.hasMapGeometry({
      geometry: {
        type: "LineString",
        coordinates: [
          [73, 19],
          [73.1, 19.1],
        ],
      },
    }),
    true,
  );
  assert.equal(
    mapData.hasMapGeometry({
      geometry: { type: "Point", coordinates: [NaN, 19] },
    }),
    false,
  );
});
