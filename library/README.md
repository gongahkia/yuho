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

The bundled library currently contains 25 Singapore Penal Code sections:

| Section | Offense |
|---------|---------|
| S299 | Culpable Homicide |
| S300 | Murder |
| S302 | Punishment for Murder |
| S304 | Culpable Homicide not amounting to Murder |
| S319 | Hurt |
| S321 | Voluntarily Causing Hurt |
| S323 | Punishment for Voluntarily Causing Hurt |
| S325 | Voluntarily Causing Grievous Hurt |
| S354 | Assault or Criminal Force to Outrage Modesty |
| S363 | Kidnapping |
| S378 | Theft |
| S379 | Punishment for Theft |
| S383 | Extortion |
| S390 | Robbery |
| S392 | Punishment for Robbery |
| S395 | Dacoity |
| S403 | Dishonest Misappropriation |
| S406 | Punishment for Criminal Breach of Trust |
| S411 | Dishonestly Receiving Stolen Property |
| S415 | Cheating |
| S420 | Cheating and Inducing Delivery |
| S463 | Forgery |
| S465 | Punishment for Forgery |
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

[study]
offence_family = "property_offences"
related_sections = ["378", "379", "390", "392"]
exception_topics = ["claim_of_right"]
doctrine_tags = ["actus_reus", "mens_rea", "dishonesty"]
difficulty = "introductory"

[verification]
last_verified = "2026-03-08"
sso_url = "https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr415-#pr415-"
verified_by = "Yuho Team"
disclaimer = "Educational purposes only. Cross-reference with official SSO text."
```
