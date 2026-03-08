# Yuho Statute Library

Pre-built statute implementations in v5 syntax.

> **Disclaimer:** These models are provided for educational purposes only and do not constitute legal advice. Each statute was verified against the official SSO text at the URL listed in its `metadata.toml`. Always cross-reference with the [official SSO text](https://sso.agc.gov.sg/).

## Structure

Each statute directory contains:

```
s<number>_<name>/
  statute.yh         # main statute definition
  illustrations.yh   # case illustrations (if any)
  test_statute.yh    # automated tests
  metadata.toml      # metadata (section, title, jurisdiction, version)
```

## Available Statutes (Penal Code)

| Section | Offense |
|---------|---------|
| S299 | Culpable Homicide |
| S300 | Murder |
| S319 | Hurt |
| S378 | Theft |
| S383 | Extortion |
| S390 | Robbery |
| S403 | Dishonest Misappropriation |
| S415 | Cheating |
| S420 | Cheating and Inducing Delivery |
| S463 | Forgery |
| S499 | Defamation |
| S503 | Criminal Breach of Trust |

## Usage

Reference a library statute from your `.yh` file:

```yh
referencing penal_code/s415_cheating
```

Or via CLI:

```bash
yuho library search cheating
yuho library install s415_cheating
```

## metadata.toml Schema

```toml
[statute]
section_number = "415"
title = "Cheating"
jurisdiction = "Singapore"
version = "2.0.0"

[description]
summary = "..."
source = "Singapore Penal Code 1871, Section 415"
notes = "..."

[verification]
last_verified = "2026-03-08"
sso_url = "https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr415-#pr415-"
verified_by = "Yuho Team"
disclaimer = "Educational purposes only. Cross-reference with official SSO text."
```
