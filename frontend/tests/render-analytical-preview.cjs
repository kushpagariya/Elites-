// Isolated visual QA; TEST-ONLY state is never imported by the browser application.
const fs = require("fs"),
  path = require("path"),
  http = require("http"),
  React = require("react"),
  { renderToStaticMarkup } = require("react-dom/server");
const qa = require("./analytical-ui.test.cjs");
qa.setup();
const staticRoot = path.resolve(__dirname, "../.next/static");
const css = fs
  .readdirSync(staticRoot, { recursive: true })
  .filter((f) => f.endsWith(".css"))
  .map((f) => fs.readFileSync(path.join(staticRoot, f), "utf8"))
  .join("\n");
const html =
  '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>StoreScout rendering check</title><style>' +
  css +
  '</style><div style="padding:16px;font:14px system-ui;background:#201b2b;color:white">RENDERING CHECK · TEST-ONLY synthetic component state · static controls · not acceptance evidence</div>' +
  renderToStaticMarkup(
    React.createElement(
      "main",
      { className: "workspace" },
      React.createElement(
        "div",
        { className: "workspace-sheet" },
        React.createElement(qa.Explore),
      ),
    ),
  ) +
  "</html>";
const out = path.resolve(__dirname, "../docs/verification/analytical-ui");
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, "preview.html"), html);
http
  .createServer((req, res) => {
    if (req.url.startsWith("/_next/static/")) {
      const file = path.resolve(staticRoot, req.url.slice(14));
      if (file.startsWith(staticRoot + path.sep) && fs.existsSync(file)) {
        res.writeHead(200, { "Content-Type": "font/woff2" });
        return fs.createReadStream(file).pipe(res);
      }
    }
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(html);
  })
  .listen(3099, "127.0.0.1", () =>
    console.log("Component rendering preview http://127.0.0.1:3099"),
  );
