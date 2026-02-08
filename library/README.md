# Yuho Statute Library

Pre-built statute implementations in v5 syntax.

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
```
