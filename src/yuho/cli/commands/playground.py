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
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#0d1117;color:#c9d1d9;padding:12px}
h1{font-size:1.3em;margin-bottom:8px;color:#58a6ff}
.toolbar{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.toolbar select,.toolbar button{background:#21262d;color:#c9d1d9;border:1px solid #30363d;padding:4px 8px;border-radius:4px;font-size:0.85em;cursor:pointer}
.toolbar button:hover{background:#30363d}
.toolbar button.active{background:#1f6feb;border-color:#1f6feb;color:#fff}
.toolbar label{font-size:0.85em;color:#8b949e}
.columns{display:flex;gap:8px;height:calc(100vh - 100px)}
.col{flex:1;display:flex;flex-direction:column;min-width:0}
.col-header{font-size:0.8em;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px}
#source{flex:1;background:#161b22;color:#c9d1d9;border:1px solid #30363d;border-radius:4px;padding:8px;font-family:'SF Mono',Menlo,monospace;font-size:0.85em;resize:none;tab-size:4}
#source:focus{outline:none;border-color:#1f6feb}
.output-wrap{flex:1;background:#161b22;border:1px solid #30363d;border-radius:4px;overflow:auto;position:relative}
#output{padding:8px;font-family:'SF Mono',Menlo,monospace;font-size:0.85em;white-space:pre-wrap;word-break:break-word}
#rendered{padding:12px;display:none;overflow:auto;height:100%}
#rendered svg{max-width:100%}
.status{font-size:0.75em;color:#8b949e;margin-top:4px}
.status.error{color:#f85149}
.status.ok{color:#3fb950}
.json-key{color:#79c0ff}.json-str{color:#a5d6ff}.json-num{color:#d2a8ff}.json-bool{color:#ff7b72}.json-null{color:#8b949e}
.rendered-english{font-family:system-ui,sans-serif;font-size:0.95em;line-height:1.6;color:#c9d1d9}
.rendered-english h1,.rendered-english h2,.rendered-english h3{color:#58a6ff;margin:12px 0 4px}
.rendered-english p{margin:4px 0}
.rendered-english ul,.rendered-english ol{margin:4px 0 4px 20px}
.katex-block{margin:8px 0;overflow-x:auto}
</style>
</head>
<body>
<h1>Yuho Playground</h1>
<div class="toolbar">
  <label for="target">Target:</label>
  <select id="target">
    <option value="english" selected>English</option>
    <option value="json">JSON</option>
    <option value="jsonld">JSON-LD</option>
    <option value="mermaid">Mermaid</option>
    <option value="latex">LaTeX</option>
    <option value="alloy">Alloy</option>
    <option value="graphql">GraphQL</option>
    <option value="blocks">Blocks</option>
    <option value="bibtex">BibTeX</option>
    <option value="comparative">Comparative</option>
    <option value="akomantoso">Akoma Ntoso</option>
    <option value="prolog">Prolog</option>
  </select>
  <button onclick="run()">Transpile</button>
  <button id="toggle-render" onclick="toggleRender()" title="Toggle rendered/raw view">Rendered</button>
</div>
<div class="columns">
<div class="col">
  <div class="col-header">Source (.yh)</div>
  <textarea id="source" spellcheck="false" placeholder="// enter Yuho code here...
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
<div class="col">
  <div class="col-header">Output &mdash; <span id="target-label">english</span></div>
  <div class="output-wrap">
    <pre id="output"></pre>
    <div id="rendered"></div>
  </div>
</div>
</div>
<p class="status" id="status">Ready</p>
<script>
mermaid.initialize({startOnLoad:false,theme:'dark',securityLevel:'loose'});
const src=document.getElementById('source'),out=document.getElementById('output'),ren=document.getElementById('rendered');
const tgt=document.getElementById('target'),lbl=document.getElementById('target-label'),sts=document.getElementById('status');
const togBtn=document.getElementById('toggle-render');
let debounce=null,lastOutput='',showRendered=true;
const RENDERABLE=new Set(['mermaid','json','jsonld','latex','english']);

tgt.addEventListener('change',()=>{lbl.textContent=tgt.value;updateToggleState();run()});
src.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(run,500)});
src.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();run()}
  if(e.key==='Tab'){e.preventDefault();const s=src.selectionStart;src.value=src.value.substring(0,s)+'    '+src.value.substring(src.selectionEnd);src.selectionStart=src.selectionEnd=s+4}
});

function updateToggleState(){
  const can=RENDERABLE.has(tgt.value);
  togBtn.style.display=can?'':'none';
  if(!can){showRendered=false;showRaw()}
}

function toggleRender(){
  showRendered=!showRendered;
  togBtn.classList.toggle('active',showRendered);
  togBtn.textContent=showRendered?'Rendered':'Raw';
  if(lastOutput)displayOutput(lastOutput,tgt.value);
}

function showRaw(){out.style.display='block';ren.style.display='none';togBtn.classList.remove('active');togBtn.textContent='Raw'}
function showRenderedView(){out.style.display='none';ren.style.display='block';togBtn.classList.add('active');togBtn.textContent='Rendered'}

function displayOutput(text,target){
  lastOutput=text;
  if(showRendered&&RENDERABLE.has(target)){
    showRenderedView();
    renderOutput(text,target);
  } else {
    showRaw();
    out.textContent=text;
  }
}

async function renderOutput(text,target){
  if(target==='mermaid'){
    try{
      const{svg}=await mermaid.render('mermaid-'+Date.now(),text);
      ren.innerHTML=svg;
    }catch(e){ren.innerHTML='<pre style="color:#f85149">Mermaid render error: '+esc(e.message)+'</pre>'}
  } else if(target==='json'||target==='jsonld'){
    try{
      const obj=JSON.parse(text);
      ren.innerHTML=highlightJson(obj);
    }catch(e){ren.innerHTML='<pre>'+esc(text)+'</pre>'}
  } else if(target==='latex'){
    renderLatex(text);
  } else if(target==='english'){
    ren.innerHTML='<div class="rendered-english">'+renderEnglish(text)+'</div>';
  }
}

function highlightJson(obj,indent){
  indent=indent||0;
  const pad='  '.repeat(indent);
  if(obj===null)return'<span class="json-null">null</span>';
  if(typeof obj==='boolean')return'<span class="json-bool">'+obj+'</span>';
  if(typeof obj==='number')return'<span class="json-num">'+obj+'</span>';
  if(typeof obj==='string')return'<span class="json-str">"'+esc(obj)+'"</span>';
  if(Array.isArray(obj)){
    if(obj.length===0)return'[]';
    let s='[\\n';
    obj.forEach((v,i)=>{s+='  '.repeat(indent+1)+highlightJson(v,indent+1)+(i<obj.length-1?',':'')+'\\n'});
    return s+pad+']';
  }
  const keys=Object.keys(obj);
  if(keys.length===0)return'{}';
  let s='{\\n';
  keys.forEach((k,i)=>{s+='  '.repeat(indent+1)+'<span class="json-key">"'+esc(k)+'"</span>: '+highlightJson(obj[k],indent+1)+(i<keys.length-1?',':'')+'\\n'});
  return s+pad+'}';
}

function renderLatex(text){
  const lines=text.split('\\n');
  let html='';
  const mathEnv=/^\\s*\\\\begin\\{(equation|align|gather|displaymath)\\*?\\}/;
  let inMath=false,mathBuf='';
  for(const line of lines){
    if(!inMath&&mathEnv.test(line)){inMath=true;mathBuf=line+'\\n';continue}
    if(inMath){mathBuf+=line+'\\n';if(/\\\\end\\{/.test(line)){inMath=false;try{const clean=mathBuf.replace(/\\\\begin\\{[^}]+\\}/g,'').replace(/\\\\end\\{[^}]+\\}/g,'').replace(/&/g,'').replace(/\\\\\\\\/g,'\\n').trim();html+='<div class="katex-block">';katex.render(clean,document.createElement('span'),{throwOnError:false,displayMode:true});html+=katex.renderToString(clean,{throwOnError:false,displayMode:true})+'</div>'}catch(e){html+='<pre>'+esc(mathBuf)+'</pre>'}mathBuf=''}continue}
    const inlineRendered=line.replace(/\\$([^$]+)\\$/g,(_,m)=>{try{return katex.renderToString(m,{throwOnError:false})}catch(e){return m}});
    if(inlineRendered!==line){html+='<p>'+inlineRendered+'</p>';continue}
    if(/^\\s*\\\\(section|subsection|title)\\{/.test(line)){const m=line.match(/\\\\(section|subsection|title)\\{(.*)\\}/);if(m){const tag=m[1]==='title'?'h1':m[1]==='section'?'h2':'h3';html+='<'+tag+'>'+esc(m[2])+'</'+tag+'>';continue}}
    if(/^\\s*\\\\item\\s/.test(line)){html+='<li>'+esc(line.replace(/^\\s*\\\\item\\s*/,''))+'</li>';continue}
    if(line.trim()==='')html+='<br>';
    else html+='<p>'+esc(line.replace(/\\\\textbf\\{([^}]*)\\}/g,'<b>$1</b>').replace(/\\\\textit\\{([^}]*)\\}/g,'<i>$1</i>'))+'</p>';
  }
  ren.innerHTML=html||'<pre>'+esc(text)+'</pre>';
}

function renderEnglish(text){
  return text.split('\\n\\n').map(para=>{
    const trimmed=para.trim();
    if(!trimmed)return'';
    if(/^#{1,3}\\s/.test(trimmed)){const m=trimmed.match(/^(#{1,3})\\s+(.*)/);const lvl=m[1].length;return'<h'+lvl+'>'+esc(m[2])+'</h'+lvl+'>'}
    if(/^[-*]\\s/.test(trimmed)){const items=trimmed.split('\\n').map(l=>'<li>'+esc(l.replace(/^[-*]\\s+/,''))+'</li>').join('');return'<ul>'+items+'</ul>'}
    if(/^\\d+\\.\\s/.test(trimmed)){const items=trimmed.split('\\n').map(l=>'<li>'+esc(l.replace(/^\\d+\\.\\s+/,''))+'</li>').join('');return'<ol>'+items+'</ol>'}
    return'<p>'+esc(trimmed).replace(/\\n/g,'<br>')+'</p>';
  }).join('');
}

async function run(){
  sts.textContent='Transpiling...';sts.className='status';
  try{
    const r=await fetch('/api/transpile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:src.value,target:tgt.value})});
    const d=await r.json();
    if(d.error){out.style.display='block';ren.style.display='none';out.innerHTML='<span style="color:#f85149"><b>Error:</b> '+esc(d.error)+'</span>';sts.textContent='Error';sts.className='status error'}
    else{displayOutput(d.output,d.target);sts.textContent='OK ('+d.target+')';sts.className='status ok'}
  }catch(e){out.style.display='block';ren.style.display='none';out.innerHTML='<span style="color:#f85149"><b>Error:</b> '+esc(e.message)+'</span>';sts.textContent='Error';sts.className='status error'}
}

function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
updateToggleState();
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
