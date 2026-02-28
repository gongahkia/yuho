"""
Live preview mode with file watching for Yuho.

Watches a .yh file, auto-transpiles to mermaid/english on changes,
and serves the result in a browser with live reload.
"""

import os
import sys
import time
import webbrowser
import hashlib
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Dict, Any
import json

import click

# Bundled static assets used by preview mode.
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"


class PreviewState:
    """Shared state for preview server."""
    
    def __init__(self):
        self.content: str = ""
        self.format: str = "english"
        self.last_error: Optional[str] = None
        self.file_path: str = ""
        self.last_modified: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "format": self.format,
            "error": self.last_error,
            "file": self.file_path,
            "modified": self.last_modified,
        }


# Global state
_preview_state = PreviewState()


def transpile_file(path: Path, target: str) -> tuple[Optional[str], Optional[str]]:
    """
    Transpile a file to the target format.
    
    Returns:
        (content, error) - one will be None
    """
    try:
        from yuho.parser import get_parser
        from yuho.ast.builder import ASTBuilder
        from yuho.transpile.registry import TranspilerRegistry
        from yuho.transpile.base import TranspileTarget

        source = path.read_text()

        parser = get_parser()
        result = parser.parse(source, str(path))

        if result.errors:
            errors = "; ".join(e.message for e in result.errors[:3])
            return None, f"Parse errors: {errors}"

        builder = ASTBuilder(source, str(path))
        ast = builder.build(result.tree.root_node)

        # Convert string target to TranspileTarget enum
        target_enum = TranspileTarget.from_string(target)

        registry = TranspilerRegistry.instance()
        transpiler = registry.get(target_enum)

        if transpiler is None:
            return None, f"Unknown target format: {target}"

        output = transpiler.transpile(ast)
        return output, None

    except Exception as e:
        return None, str(e)


def get_html_template(format_type: str) -> str:
    """Get HTML template for preview."""
    
    mermaid_script = ""
    if format_type == "mermaid":
        mermaid_script = """
        <script src="/assets/mermaid.min.js"></script>
        <script>mermaid.initialize({startOnLoad: true, theme: 'dark'});</script>
        """
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yuho Live Preview</title>
    {mermaid_script}
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --text-primary: #eee;
            --text-secondary: #aaa;
            --accent: #4cc9f0;
            --error: #ff6b6b;
            --success: #4ecdc4;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}
        .header {{
            background: var(--bg-secondary);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{
            font-size: 1.25rem;
            color: var(--accent);
        }}
        .status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
        }}
        .status-dot.error {{
            background: var(--error);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .preview-content {{
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 2rem;
            white-space: pre-wrap;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.9rem;
            overflow-x: auto;
        }}
        .preview-content.mermaid-container {{
            background: #fff;
            color: #333;
            text-align: center;
        }}
        .error-message {{
            background: rgba(255, 107, 107, 0.1);
            border: 1px solid var(--error);
            border-radius: 8px;
            padding: 1rem;
            color: var(--error);
            margin-bottom: 1rem;
        }}
        .file-info {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-bottom: 1rem;
        }}
        .mermaid {{
            background: #fff;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📜 Yuho Live Preview</h1>
        <div class="status">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">Watching...</span>
        </div>
    </div>
    <div class="container">
        <div class="file-info" id="fileInfo"></div>
        <div id="errorBox" class="error-message" style="display:none;"></div>
        <div id="content" class="preview-content"></div>
    </div>
    <script>
        let lastModified = 0;
        
        async function fetchPreview() {{
            try {{
                const res = await fetch('/api/preview');
                const data = await res.json();
                
                const dot = document.getElementById('statusDot');
                const status = document.getElementById('statusText');
                const errorBox = document.getElementById('errorBox');
                const content = document.getElementById('content');
                const fileInfo = document.getElementById('fileInfo');
                
                if (data.modified !== lastModified) {{
                    lastModified = data.modified;
                    
                    fileInfo.textContent = 'File: ' + data.file + ' • Format: ' + data.format;
                    
                    if (data.error) {{
                        dot.classList.add('error');
                        status.textContent = 'Error';
                        errorBox.textContent = data.error;
                        errorBox.style.display = 'block';
                    }} else {{
                        dot.classList.remove('error');
                        status.textContent = 'Updated ' + new Date().toLocaleTimeString();
                        errorBox.style.display = 'none';
                        
                        if (data.format === 'mermaid') {{
                            content.className = 'preview-content mermaid-container';
                            content.innerHTML = '<pre class="mermaid">' + data.content + '</pre>';
                            if (window.mermaid) {{
                                mermaid.contentLoaded();
                            }}
                        }} else {{
                            content.className = 'preview-content';
                            content.textContent = data.content;
                        }}
                    }}
                }}
            }} catch (e) {{
                console.error('Fetch error:', e);
            }}
        }}
        
        // Poll for updates
        setInterval(fetchPreview, 500);
        fetchPreview();
    </script>
</body>
</html>
"""


class PreviewHandler(SimpleHTTPRequestHandler):
    """HTTP handler for preview server."""
    
    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass
    
    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = get_html_template(_preview_state.format)
            self.wfile.write(html.encode())
        
        elif self.path == "/api/preview":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(_preview_state.to_dict()).encode())

        elif self.path == "/assets/mermaid.min.js":
            asset_path = ASSET_DIR / "mermaid.min.js"
            if not asset_path.exists():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-type", "application/javascript")
            self.end_headers()
            self.wfile.write(asset_path.read_bytes())
        
        else:
            self.send_error(404)


def watch_file(path: Path, target: str, interval: float = 0.5) -> None:
    """Watch file for changes and update preview state."""
    global _preview_state
    
    last_hash = ""
    
    while True:
        try:
            if path.exists():
                content = path.read_bytes()
                current_hash = hashlib.md5(content).hexdigest()
                
                if current_hash != last_hash:
                    last_hash = current_hash
                    _preview_state.last_modified = time.time()
                    
                    result, error = transpile_file(path, target)
                    
                    if error:
                        _preview_state.last_error = error
                    else:
                        _preview_state.content = result or ""
                        _preview_state.last_error = None
            
        except Exception as e:
            _preview_state.last_error = str(e)
        
        time.sleep(interval)


def run_preview(
    file: str,
    target: str = "english",
    port: int = 8000,
    no_browser: bool = False,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """
    Run live preview server.
    
    Args:
        file: Input .yh file to watch
        target: Transpile target (english, mermaid)
        port: Server port
        no_browser: Don't auto-open browser
        verbose: Verbose output
        color: Use colors
    """
    global _preview_state
    
    path = Path(file)
    
    if not path.exists():
        click.echo(f"Error: File not found: {file}", err=True)
        raise SystemExit(1)
    
    # Validate target
    valid_targets = ["english", "mermaid"]
    if target not in valid_targets:
        click.echo(f"Error: Preview supports: {', '.join(valid_targets)}", err=True)
        raise SystemExit(1)
    
    # Initialize state
    _preview_state.file_path = str(path)
    _preview_state.format = target
    
    # Initial transpile
    result, error = transpile_file(path, target)
    if error:
        _preview_state.last_error = error
    else:
        _preview_state.content = result or ""
    _preview_state.last_modified = time.time()
    
    # Start file watcher thread
    watcher = threading.Thread(target=watch_file, args=(path, target), daemon=True)
    watcher.start()
    
    # Start server
    server = HTTPServer(("127.0.0.1", port), PreviewHandler)
    
    url = f"http://127.0.0.1:{port}"
    
    click.echo(click.style("🔴 Yuho Live Preview", fg="cyan", bold=True))
    click.echo(f"   Watching: {click.style(str(path), fg='yellow')}")
    click.echo(f"   Format:   {click.style(target, fg='green')}")
    click.echo(f"   Server:   {click.style(url, fg='blue')}")
    click.echo("")
    click.echo("   Press Ctrl+C to stop")
    click.echo("")
    
    # Open browser
    if not no_browser:
        webbrowser.open(url)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\n\nStopping preview server...")
        server.shutdown()
