# Cookbook: Multi-Jurisdiction Statutes

Manage statutes across different legal systems.

## Package Namespacing

Organize by jurisdiction:

```
library/
  singapore/
    penal_code/
      s299_culpable_homicide/
      s300_murder/
  indonesia/
    kuhp/
      pasal_338_pembunuhan/
  uk/
    theft_act_1968/
      s1_theft/
```

## Cross-jurisdiction Comparison

```bash
yuho diff singapore/s300.yh uk/murder.yh
```

Use `yuho transpile -t comparative` to generate side-by-side markdown.

## Registry Per Jurisdiction

```toml
# config.toml
[library]
registry_url = "https://registry.yuho.dev"
```

```bash
yuho library search --namespace singapore
yuho library install singapore/s300
```

## Porting Guide

See [PORTING_GUIDE.md](../PORTING_GUIDE.md) for mapping new jurisdictions to Yuho syntax.

Key differences across jurisdictions:
- Element naming (actus reus vs conduct element)
- Penalty structures (death penalty availability)
- Burden of proof defaults
- Exception frameworks (general vs specific)
