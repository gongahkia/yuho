// Tiny HTTPS static server for local Office Add-in development.
//
// Office Add-ins must be served over HTTPS from `https://localhost:3000`
// (matching the URLs in the manifest). This script:
//
//   1. resolves the dev SSL cert installed by office-addin-dev-certs,
//   2. serves files from this directory at /src/ /assets/ /commands/
//      /taskpane/ /data/, and
//   3. logs requests so you can see what Word is fetching.
//
// Run via `npm start` (which spawns this alongside office-addin-debugging).
// No third-party deps; uses Node's built-in https + fs.

"use strict";

const fs = require("fs");
const https = require("https");
const path = require("path");
const os = require("os");

const PORT = 3000;
const ROOT = path.resolve(__dirname, "src");
const DATA = path.resolve(__dirname, "data");

// office-addin-dev-certs installs into ~/.office-addin-dev-certs/.
const certDir = path.join(os.homedir(), ".office-addin-dev-certs");
const KEY = path.join(certDir, "localhost.key");
const CERT = path.join(certDir, "localhost.crt");
const CA = path.join(certDir, "ca.crt");

if (!fs.existsSync(KEY) || !fs.existsSync(CERT)) {
  console.error("[Yuho dev server] localhost cert not found.");
  console.error("Generate one first:");
  console.error("  npx office-addin-dev-certs install");
  process.exit(1);
}

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js":   "application/javascript; charset=utf-8",
  ".css":  "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg":  "image/svg+xml",
  ".png":  "image/png",
  ".ico":  "image/x-icon",
  ".txt":  "text/plain; charset=utf-8",
};

function mimeFor(filePath) {
  return MIME[path.extname(filePath).toLowerCase()] || "application/octet-stream";
}

// Map a request URL onto a filesystem path. /data/* maps to data/, /assets/*
// to src/assets/, anything else to src/. Resolved paths are sandboxed to
// the repo so a "../" segment can't escape.
function resolvePath(reqUrl) {
  const u = decodeURIComponent(reqUrl.split("?")[0]);
  if (u === "/" || u === "/index.html") {
    return path.join(ROOT, "taskpane", "taskpane.html");
  }
  let target;
  if (u.startsWith("/data/")) {
    target = path.join(DATA, u.slice("/data/".length));
  } else if (u.startsWith("/assets/")) {
    target = path.join(ROOT, "assets", u.slice("/assets/".length));
  } else {
    target = path.join(ROOT, u.replace(/^\/+/, ""));
  }
  // Sandbox: only allow paths inside the project.
  const repo = path.resolve(__dirname);
  if (!path.resolve(target).startsWith(repo)) return null;
  return target;
}

const server = https.createServer(
  {
    key: fs.readFileSync(KEY),
    cert: fs.readFileSync(CERT),
    ca: fs.existsSync(CA) ? fs.readFileSync(CA) : undefined,
  },
  (req, res) => {
    const filePath = resolvePath(req.url);
    if (!filePath) {
      res.writeHead(403); res.end("forbidden"); return;
    }
    fs.stat(filePath, (err, st) => {
      if (err || !st.isFile()) {
        console.warn(`[404] ${req.url} -> ${filePath}`);
        res.writeHead(404); res.end("not found"); return;
      }
      console.log(`[200] ${req.url} -> ${path.relative(__dirname, filePath)}`);
      res.writeHead(200, {
        "content-type": mimeFor(filePath),
        // Office sandbox needs CORS to fetch data/sections.json.
        "access-control-allow-origin": "*",
        "cache-control": "no-store",
      });
      fs.createReadStream(filePath).pipe(res);
    });
  }
);

server.listen(PORT, () => {
  console.log(`[Yuho dev server] serving ${ROOT} on https://localhost:${PORT}`);
});
