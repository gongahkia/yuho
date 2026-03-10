"""
Web playground - browser-based Yuho editor with live transpilation.

Serves a single-page app with a code editor, target selector,
and live output panel. Uses the same analysis + transpile pipeline
as the CLI.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs

import click


_PLAYGROUND_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Yuho Playground</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; background: #1e1e2e; color: #cdd6f4; }
.header { background: #313244; padding: .75rem 1.5rem; display: flex; align-items: center; gap: 1rem; border-bottom: 1px solid #45475a; }
.header h1 { font-size: 1.1rem; color: #89b4fa; }
.header select, .header button { padding: .4rem .8rem; border-radius: 6px; border: 1px solid #585b70; background: #45475a; color: #cdd6f4; cursor: pointer; font-size: .85rem; }
.header button { background: #89b4fa; color: #1e1e2e; font-weight: 600; }
.header button:hover { background: #74c7ec; }
.container { display: grid; grid-template-columns: 1fr 1fr; height: calc(100vh - 50px); }
.pane { display: flex; flex-direction: column; }
.pane-header { background: #313244; padding: .5rem 1rem; font-size: .8rem; color: #a6adc8; border-bottom: 1px solid #45475a; }
textarea { flex: 1; background: #1e1e2e; color: #cdd6f4; border: none; padding: 1rem; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: .9rem; resize: none; tab-size: 4; line-height: 1.6; }
textarea:focus { outline: none; }
pre { flex: 1; background: #181825; padding: 1rem; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: .85rem; overflow: auto; white-space: pre-wrap; line-height: 1.6; }
.error { color: #f38ba8; }
.status { padding: .3rem 1rem; background: #313244; font-size: .75rem; color: #a6adc8; border-top: 1px solid #45475a; text-align: right; }
</style>
</head>
<body>
<div class="header">
  <h1>Yuho Playground</h1>
  <select id="target">
    <option value="english" selected>English</option>
    <option value="json">JSON</option>
    <option value="mermaid">Mermaid</option>
    <option value="latex">LaTeX</option>
    <option value="alloy">Alloy</option>
    <option value="graphql">GraphQL</option>
    <option value="bibtex">BibTeX</option>
    <option value="html">HTML</option>
  </select>
  <button onclick="run()">Transpile</button>
</div>
<div class="container">
  <div class="pane">
    <div class="pane-header">Source (.yh)</div>
    <textarea id="source" spellcheck="false" placeholder="// Enter Yuho code here...
statute 1 &quot;Example&quot; {
    definitions {
        example := &quot;An example definition&quot;;
    }
    elements {
        actus_reus act := &quot;The prohibited conduct&quot;;
        mens_rea intent := &quot;The required mental state&quot;;
    }
    penalty {
        imprisonment := 0 days .. 5 years;
    }
}"></textarea>
  </div>
  <div class="pane">
    <div class="pane-header">Output — <span id="target-label">english</span></div>
    <pre id="output"></pre>
  </div>
</div>
<div class="status" id="status">Ready</div>
<script>
const src = document.getElementById('source');
const out = document.getElementById('output');
const tgt = document.getElementById('target');
const lbl = document.getElementById('target-label');
const sts = document.getElementById('status');
let debounce = null;

tgt.addEventListener('change', () => { lbl.textContent = tgt.value; run(); });
src.addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(run, 500); });
src.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); }
  if (e.key === 'Tab') { e.preventDefault(); const s=src.selectionStart; src.value=src.value.substring(0,s)+'    '+src.value.substring(src.selectionEnd); src.selectionStart=src.selectionEnd=s+4; }
});

async function run() {
  sts.textContent = 'Transpiling...';
  try {
    const r = await fetch('/api/transpile', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({source: src.value, target: tgt.value})
    });
    const d = await r.json();
    if (d.error) { out.innerHTML = '<span class="error">' + esc(d.error) + '</span>'; sts.textContent = 'Error'; }
    else { out.textContent = d.output; sts.textContent = 'OK (' + d.target + ')'; }
  } catch(e) { out.innerHTML = '<span class="error">' + esc(e.message) + '</span>'; sts.textContent = 'Error'; }
}

function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
</script>
</body>
</html>"""


def run_playground(*, port: int = 8080, host: str = "127.0.0.1", verbose: bool = False) -> None:
    """Start the web playground server."""
    from yuho.services.analysis import analyze_source
    from yuho.transpile import TranspileTarget, get_transpiler

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            if verbose:
                BaseHTTPRequestHandler.log_message(self, format, *args)

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(_PLAYGROUND_HTML.encode("utf-8"))

        def do_POST(self):
            if self.path != "/api/transpile":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            source = body.get("source", "")
            target_name = body.get("target", "english")

            result = analyze_source(source)
            if not result.is_valid or result.ast is None:
                errors = "; ".join(str(e) for e in result.errors)
                resp = {"error": errors or "Parse failed"}
            else:
                try:
                    target = TranspileTarget.from_string(target_name)
                    transpiler = get_transpiler(target)
                    output = transpiler.transpile(result.ast)
                    resp = {"output": output, "target": target_name}
                except Exception as e:
                    resp = {"error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))

    server = HTTPServer((host, port), Handler)
    click.echo(f"Yuho Playground running at http://{host}:{port}")
    click.echo("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nStopped.")
        server.server_close()
