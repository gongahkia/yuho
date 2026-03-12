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
<link rel="icon" href="data:,">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
</head>
<body>
<h1>Yuho Playground</h1>
<p>
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
  <button id="toggle-render" onclick="toggleRender()">Rendered</button>
</p>
<hr>
<table width="100%"><tr>
<td width="50%" valign="top">
  <p><b>Source (.yh)</b></p>
  <textarea id="source" rows="30" cols="60" spellcheck="false" placeholder="// enter Yuho code here...
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
  <div id="rendered" style="display:none"></div>
</td>
</tr></table>
<hr>
<p id="status">Ready</p>
<script>
mermaid.initialize({startOnLoad:false,theme:'default',securityLevel:'loose'});
const src=document.getElementById('source'),out=document.getElementById('output'),ren=document.getElementById('rendered');
const tgt=document.getElementById('target'),lbl=document.getElementById('target-label'),sts=document.getElementById('status');
const togBtn=document.getElementById('toggle-render');
let debounce=null,lastOutput='',showRendered=true;
const RENDERABLE=new Set(['mermaid','json','jsonld','latex','english','blocks']);

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
  togBtn.textContent=showRendered?'Rendered':'Raw';
  if(lastOutput)displayOutput(lastOutput,tgt.value);
}

function showRaw(){out.style.display='block';ren.style.display='none';togBtn.textContent='Raw'}
function showRenderedView(){out.style.display='none';ren.style.display='block';togBtn.textContent='Rendered'}

function displayOutput(text,target){
  lastOutput=text;
  if(showRendered&&RENDERABLE.has(target)){showRenderedView();renderOutput(text,target)}
  else{showRaw();out.textContent=text}
}

let mermaidCounter=0;
async function renderOutput(text,target){
  if(target==='mermaid'){
    try{
      const id='mmd'+(mermaidCounter++);
      const container=document.createElement('div');
      container.id=id;
      container.style.display='none';
      document.body.appendChild(container);
      const{svg}=await mermaid.render(id,text,container);
      container.remove();
      ren.innerHTML=svg;
    }
    catch(e){ren.innerHTML='<pre>Mermaid render error: '+esc(e.message)+'</pre>'}
  } else if(target==='blocks'){
    ren.innerHTML='<pre style="font-family:monospace;line-height:1.4">'+esc(text)+'</pre>';
  } else if(target==='json'||target==='jsonld'){
    try{const obj=JSON.parse(text);ren.innerHTML='<pre>'+highlightJson(obj)+'</pre>'}
    catch(e){ren.innerHTML='<pre>'+esc(text)+'</pre>'}
  } else if(target==='latex'){
    renderLatex(text);
  } else if(target==='english'){
    ren.innerHTML=renderEnglish(text);
  }
}

function highlightJson(obj,indent){
  indent=indent||0;
  const pad='  '.repeat(indent);
  if(obj===null)return'<b>null</b>';
  if(typeof obj==='boolean')return'<b>'+obj+'</b>';
  if(typeof obj==='number')return''+obj;
  if(typeof obj==='string')return'"'+esc(obj)+'"';
  if(Array.isArray(obj)){
    if(obj.length===0)return'[]';
    let s='[\\n';
    obj.forEach((v,i)=>{s+='  '.repeat(indent+1)+highlightJson(v,indent+1)+(i<obj.length-1?',':'')+'\\n'});
    return s+pad+']';
  }
  const keys=Object.keys(obj);
  if(keys.length===0)return'{}';
  let s='{\\n';
  keys.forEach((k,i)=>{s+='  '.repeat(indent+1)+'<b>"'+esc(k)+'"</b>: '+highlightJson(obj[k],indent+1)+(i<keys.length-1?',':'')+'\\n'});
  return s+pad+'}';
}

function renderLatex(text){
  const lines=text.split('\\n');
  let html='';
  const mathEnv=/^\\s*\\\\begin\\{(equation|align|gather|displaymath)\\*?\\}/;
  let inMath=false,mathBuf='';
  for(const line of lines){
    if(!inMath&&mathEnv.test(line)){inMath=true;mathBuf=line+'\\n';continue}
    if(inMath){mathBuf+=line+'\\n';if(/\\\\end\\{/.test(line)){inMath=false;try{const clean=mathBuf.replace(/\\\\begin\\{[^}]+\\}/g,'').replace(/\\\\end\\{[^}]+\\}/g,'').replace(/&/g,'').replace(/\\\\\\\\/g,'\\n').trim();html+=katex.renderToString(clean,{throwOnError:false,displayMode:true})}catch(e){html+='<pre>'+esc(mathBuf)+'</pre>'}mathBuf=''}continue}
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
  sts.textContent='Transpiling...';
  try{
    const r=await fetch('/api/transpile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:src.value,target:tgt.value})});
    const d=await r.json();
    if(d.error){out.style.display='block';ren.style.display='none';out.innerHTML='<b>Error:</b> '+esc(d.error);sts.textContent='Error'}
    else{displayOutput(d.output,d.target);sts.textContent='OK ('+d.target+')'}
  }catch(e){out.style.display='block';ren.style.display='none';out.innerHTML='<b>Error:</b> '+esc(e.message);sts.textContent='Error'}
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
            if self.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
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
