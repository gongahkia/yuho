# Cookbook: Compliance SaaS

Build a compliance checker that validates business rules against encoded statutes.

## Architecture

```
User uploads facts -> Your API -> Yuho API -> Evaluation result -> Compliance report
```

## Steps

### 1. Encode statutes

```bash
yuho generate 378 --title "Theft" -o statutes/theft.yh
# fill in elements, penalty, exceptions
yuho check statutes/theft.yh
```

### 2. Validate via API

```python
import httpx

YUHO = "http://localhost:8080"

def check_compliance(source: str, facts: dict) -> dict:
    resp = httpx.post(f"{YUHO}/v1/validate", json={
        "source": source,
        "include_metrics": True,
    })
    return resp.json()
```

### 3. CI integration

Add `.pre-commit-hooks.yaml` reference:

```yaml
repos:
  - repo: https://github.com/gongahkia/yuho
    hooks:
      - id: yuho-check
```

### 4. Monitor

```bash
# prometheus scraping
curl http://localhost:8080/v1/metrics
```
