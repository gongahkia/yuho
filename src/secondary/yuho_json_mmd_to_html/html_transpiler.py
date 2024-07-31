def create_html_file(base_name):

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="main.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css">
        <title>Yuho Statute Visualiser</title>
        <style>
            body {{
                background-color: #fbf1c7; 
                color: #3c3836; 
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            header {{
                text-align: center;
                position: relative;
                padding: 20px;
            }}
            #github-link {{
                position: absolute;
                top: 20px;
                right: 20px;
            }}
            #github-logo {{
                width: 32px;
                height: 32px;
            }}
            h1 {{
                color: #b57614; 
                margin-bottom: 10px;
            }}
            .center-text {{
                margin: 0;
                font-size: 1em;
                color: #3c3836; 
            }}
            a {{
                color: #b57614; 
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            main {{
                padding: 20px;
            }}
            #mermaidContainer {{
                background-color: #f2e5bc; 
                border: 2px solid #3c3836; 
                padding: 10px;
                margin-bottom: 20px;
            }}
            section#code {{
                margin-top: 20px;
            }}
            h2 {{
                color: #b57614; 
                margin-bottom: 10px;
            }}
            pre {{
                background-color: #f2e5bc; 
                border: 1px solid #3c3836; 
                padding: 10px;
                overflow: auto;
            }}
        </style>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
            const mermaidFilePath = '../mmd/{base_name}.mmd';
            const yuhoFilePath = '../../dep/yh/{base_name}.yh';
            const jsonFilePath = '../json/{base_name}.json';
            async function loadMermaidDefinition() {{
                const response = await fetch(mermaidFilePath);
                const mermaidDefinition = await response.text();
                const element = document.getElementById('mermaidContainer');
                element.innerHTML = mermaidDefinition;
                mermaid.init(undefined, element);
            }}
            async function loadYuhoFile() {{
                const response = await fetch(yuhoFilePath); 
                const yhContent = await response.text();
                const preElement = document.querySelector('#yuhoCode');
                preElement.textContent = yhContent;
            }}
            async function loadJSONFile() {{
                const response = await fetch(jsonFilePath); 
                const jsonContent = await response.text();
                const preElement = document.querySelector('pre code.language-json');
                preElement.textContent = jsonContent;
                Prism.highlightElement(preElement);
            }}
            document.addEventListener('DOMContentLoaded', () => {{
                loadMermaidDefinition();
                loadYuhoFile();
                loadJSONFile(); 
            }});
        </script>
    </head>
    <body>
        <header>
            <h1>Yuho Statute Visualiser</h1>
            <p class="center-text">Referencing <a href="https://sso.agc.gov.sg/Act/PC1871">Penal Code 1871</a></p>
            <a href="https://github.com/gongahkia" target="_blank" id="github-link">
                <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" alt="GitHub" id="github-logo">
            </a>
        </header>
        <main>
            <section id="diagram">
                <div id="mermaidContainer"></div>
            </section>
            <section id="code">
                <h2>Yuho Code</h2>
                <pre id='yuhoCode'></pre>
                <h2>Transpiled JSON</h2>
                <pre><code class="language-json"></code></pre>
            </section>
        </main>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
    </body>
</html>
"""

    file_name = f"../out/html/{base_name}.html"
    with open(file_name, "w") as file:
        file.write(html_template)