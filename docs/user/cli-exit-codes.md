# CLI Exit Codes

| Code | Meaning | Commands |
|------|---------|----------|
| 0 | Success (no errors) | all |
| 1 | Error (parse/semantic/runtime failure) | check, lint, test, eval, verify |
| 2 | Warnings only (no errors) | check, lint |
| 130 | Interrupted (Ctrl+C) | all |

## Usage in CI

```bash
yuho check file.yh
if [ $? -eq 1 ]; then echo "FAIL"; fi
if [ $? -eq 2 ]; then echo "WARN"; fi
```

## Output Formats

| Flag | Format | Use Case |
|------|--------|----------|
| `--json` | JSON | Programmatic consumption |
| `--format sarif` | SARIF v2.1.0 | GitHub Code Scanning |
| `--format junit` | JUnit XML | CI test dashboards |
