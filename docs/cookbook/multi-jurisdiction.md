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

For an interoperable interchange format, transpile each side to Akoma
Ntoso and diff the XML — most legislative tooling consumes AKN
natively:

```bash
yuho transpile -t akomantoso singapore/s300.yh > sg_s300.akn.xml
yuho transpile -t akomantoso uk/murder.yh        > uk_murder.akn.xml
diff sg_s300.akn.xml uk_murder.akn.xml
```

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

See [PORTING_GUIDE.md](../contributor/porting-guide.md) for mapping new jurisdictions to Yuho syntax.

Key differences across jurisdictions:
- Element naming (actus reus vs conduct element)
- Penalty structures (death penalty availability)
- Burden of proof defaults
- Exception frameworks (general vs specific)
