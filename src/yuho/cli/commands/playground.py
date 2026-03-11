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
</head>
<body>
<h1>Yuho Playground</h1>
<p>
  <label for="target">Target:</label>
  <select id="target">
    <option value="english" selected>English</option>
    <option value="json">JSON</option>
    <option value="mermaid">Mermaid</option>
    <option value="latex">LaTeX</option>
    <option value="alloy">Alloy</option>
    <option value="graphql">GraphQL</option>
    <option value="bibtex">BibTeX</option>
  </select>
  <button onclick="run()">Transpile</button>
</p>
<hr>
<table width="100%"><tr>
<td width="50%" valign="top">
  <p><b>Source (.yh)</b></p>
  <textarea id="source" rows="30" cols="60" spellcheck="false" placeholder="// Enter Yuho code here...
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
</td>
<td width="50%" valign="top">
  <p><b>Output &mdash; <span id="target-label">english</span></b></p>
  <pre id="output"></pre>
</td>
</tr></table>
<hr>
<p id="status">Ready</p>
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
    if (d.error) { out.innerHTML = '<b>Error:</b> ' + esc(d.error); sts.textContent = 'Error'; }
    else { out.textContent = d.output; sts.textContent = 'OK (' + d.target + ')'; }
  } catch(e) { out.innerHTML = '<b>Error:</b> ' + esc(e.message); sts.textContent = 'Error'; }
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
