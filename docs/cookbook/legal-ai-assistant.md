# Cookbook: Legal AI Assistant

Integrate Yuho with Claude or other LLMs via MCP.

## MCP Setup (Claude Desktop)

```json
{
  "mcpServers": {
    "yuho": {
      "command": "yuho",
      "args": ["serve", "--stdio"]
    }
  }
}
```

Claude can now call Yuho tools: `yuho_parse`, `yuho_transpile`, `yuho_lint`, etc.

## REST API + LLM

```python
import httpx

def explain_statute(source: str) -> str:
    # first transpile to English
    resp = httpx.post("http://localhost:8080/v1/transpile", json={
        "source": source,
        "target": "english",
    })
    english = resp.json()["data"]["output"]

    # then pass to your LLM for further explanation
    # ... your LLM call here ...
    return english
```

## Validate LLM-Generated Statutes

```python
def validate_llm_output(generated_yh: str) -> dict:
    resp = httpx.post("http://localhost:8080/v1/validate", json={
        "source": generated_yh,
        "explain_errors": True,
    })
    return resp.json()
```

Feed validation errors back to the LLM for self-correction.
