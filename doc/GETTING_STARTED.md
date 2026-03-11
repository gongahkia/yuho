# Getting Started for Legal Tech Developers

## 5-Minute Quickstart

### 1. Install

```bash
pip install yuho
```

### 2. Parse a statute

```bash
echo 'statute 1 "Theft" {
  elements {
    actus_reus taking := "Takes movable property";
    mens_rea dishonestly := "With dishonest intent";
  }
  penalty {
    imprisonment := 1 year .. 3 years;
  }
}' > theft.yh

yuho check theft.yh
```

### 3. Transpile

```bash
yuho transpile theft.yh -t english   # human-readable
yuho transpile theft.yh -t json      # machine-readable
yuho transpile theft.yh -t graphql   # API schema
yuho transpile theft.yh -t prolog    # logic programming
```

### 4. Start the API server

```bash
yuho api --port 8080
```

```bash
curl -X POST http://localhost:8080/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"source": "statute 1 \"Theft\" { elements { actus_reus x := \"act\"; } }"}'
```

### 5. Docker

```bash
docker build -t yuho .
docker run -p 8080:8080 yuho
```

## Integration Paths

| Path | Best For | Latency |
|------|----------|---------|
| Python SDK | Python apps, embedding | Lowest |
| REST API | Any language, microservices | Low |
| MCP Server | AI assistants (Claude, etc.) | Low |
| CLI | CI/CD, scripts, batch ops | N/A |
| WASM | Browser, client-side | Zero network |

## Next Steps

- [SDK Quickstart](SDK_QUICKSTART.md) - Python/TypeScript/Go/Java examples
- [CLI Reference](CLI_REFERENCE.md) - All 25+ commands
- [OpenAPI Spec](openapi.yaml) - Full API documentation
- [Deployment Guide](DEPLOYMENT.md) - Docker, Kubernetes, Cloud Run
- [Cookbook](cookbook/) - Real-world integration recipes
