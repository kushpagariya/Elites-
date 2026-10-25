const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
require.extensions[".tsx"] = (module, file) =>
  module._compile(
    ts.transpileModule(fs.readFileSync(file, "utf8"), {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        jsx: ts.JsxEmit.ReactJSX,
        esModuleInterop: true,
      },
    }).outputText,
    file,
  );
let pathname = "/app";
const original = Module._load;
Module._load = function (name, parent, isMain) {
  if (name === "next/navigation") return { usePathname: () => pathname };
  if (name === "next/link")
    return ({ children, ...props }) =>
      React.createElement("a", props, children);
  return original.call(this, name, parent, isMain);
};
const Navigation = require("../src/components/WorkspaceNavigation.tsx").default;

test("three existing routes expose expandable feature links targeting real sections", () => {
  const targets = {
    "/app": [
      "explore/Explore.tsx",
      ["locations-heading", "dayparts-heading", "comparison-heading"],
    ],
    "/app/scenarios": [
      "scenarios/Scenarios.tsx",
      ["builder-heading", "infra-heading", "risk-heading"],
    ],
    "/app/portfolio": [
      "portfolio/Portfolio.tsx",
      ["portfolio-heading", "report-heading"],
    ],
  };
  for (const route of Object.keys(targets)) {
    pathname = route;
    const html = renderToStaticMarkup(
      React.createElement(Navigation, { contentReady: true }),
    );
    assert.equal((html.match(/aria-current="page"/g) || []).length, 1);
    assert.equal((html.match(/aria-expanded="true"/g) || []).length, 1);
    assert.equal((html.match(/aria-expanded="false"/g) || []).length, 2);
    assert.ok(html.includes('href="' + route + '" aria-current="page"'));
    for (const [href, [source, ids]] of Object.entries(targets)) {
      const feature = fs.readFileSync(
        path.resolve(__dirname, "../src/features", source),
        "utf8",
      );
      for (const id of ids) {
        assert.ok(html.includes('href="' + href + "#" + id + '"'));
        assert.ok(
          feature.includes('id="' + id + '"'),
          "Missing destination: " + id,
        );
      }
    }
  }
});
