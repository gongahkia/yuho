# Security Policy

## Supported Versions

Security fixes target the latest tagged release and `main`.

## Reporting

Report suspected vulnerabilities by email to `gabrielzmong@gmail.com`.

Do not file public issues for exploitable parser, compiler, CI, or supply-chain
problems until coordinated disclosure is agreed.

Include:

- affected version or commit;
- reproduction steps;
- expected impact;
- any relevant input files.

## Scope

In scope:

- parser or transpiler crashes triggered by untrusted `.yh` input;
- arbitrary file read/write outside explicitly requested paths;
- CI or release workflow compromise;
- package, SBOM, provenance, or container signing defects.

Out of scope:

- claims that an encoded statute is legally wrong without a security impact;
- social engineering;
- denial-of-service requiring unrealistic local resource limits.

## Release Security Baseline

Release candidates must pass:

- `make verify-core`;
- `python -m pytest`;
- `make verify-action-pins`;
- `make verify-corpus-provenance`;
- `make verify-reproducible-build`;
- `python scripts/release_audit.py --full`.
