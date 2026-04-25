# Deployment Guide

## Docker

```bash
docker build -t yuho .
docker run -p 8080:8080 yuho
```

Override command for MCP:

```bash
docker run -p 8081:8081 yuho serve --host 0.0.0.0 --port 8081
```

## Docker Compose

```bash
docker compose up -d        # start API + MCP
docker compose logs -f      # tail logs
docker compose down         # stop
```

Services: `yuho-api` (port 8080), `yuho-mcp` (port 8081).

## Kubernetes (Helm)

```bash
helm install yuho deploy/helm/yuho/ \
  --set config.authToken=<token> \
  --set replicaCount=3
```

Override image:

```bash
helm install yuho deploy/helm/yuho/ \
  --set image.repository=myregistry.io/yuho \
  --set image.tag=5.1.0
```

## Cloud Run

```bash
gcloud run deploy yuho \
  --image ghcr.io/gongahkia/yuho:latest \
  --port 8080 \
  --allow-unauthenticated
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `YUHO_LOG_LEVEL` | Log level (debug/info/warning/error) | `info` |
| `YUHO_API_AUTH_TOKEN` | Bearer token for API auth | none |
| `YUHO_API_HOST` | API bind host | `127.0.0.1` |
| `YUHO_API_PORT` | API bind port | `8080` |
| `YUHO_API_CORS_ORIGINS` | Comma-separated allowed origins | `*` |
| `YUHO_API_RATE_LIMIT_RPS` | Requests per second | `10` |

## Health Check

```bash
curl http://localhost:8080/health
```

Returns `{"success": true, "data": {"status": "healthy", ...}}`.
