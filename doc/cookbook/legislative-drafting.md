# Cookbook: Legislative Drafting with CI/CD

Version-control statute definitions and validate on every PR.

## Repository Layout

```
statutes/
  s299_culpable_homicide/
    statute.yh
    test_statute.yh
  s300_murder/
    statute.yh
    test_statute.yh
.github/
  workflows/
    validate.yml
```

## GitHub Actions

```yaml
name: Validate Statutes
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/yuho-check
        with:
          directory: statutes
          format: sarif
```

This produces SARIF annotations directly on the PR diff.

## Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gongahkia/yuho
    rev: v5.1.0
    hooks:
      - id: yuho-check
      - id: yuho-fmt-check
```

## Tracking Amendments

```
statute 300 "Murder" effective 1872-01-01 amends 299 {
  ...
}
```

Use `yuho diff old.yh new.yh` to see semantic changes between versions.
