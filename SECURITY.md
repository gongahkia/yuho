# Security policy

## Supported version

Security fixes target Yuho Haskell Research Language v1.0 on `main`.

## Reporting

Report suspected vulnerabilities privately to `gabrielzmong@gmail.com`. Do not file a public issue for an exploitable parser, compiler, filesystem, CI or supply-chain problem before coordinated disclosure is agreed.

Include the affected version or commit, reproduction steps, expected impact and relevant `.yh` inputs.

## Scope

In scope are unsafe handling of untrusted `.yh` input, resource-limit bypasses, unintended file reads or writes, atomic-output failures, manifest verification defects and CI compromise. Legal disagreement with an authored model is not a security vulnerability unless it exposes a software defect.

Release candidates must pass the root Haskell build and test suite, protocol replays, Lean build and theorem audit, Haskell–Lean conformance, corpus validation, documentation checks and offline release-manifest verification described by `make verify`.
