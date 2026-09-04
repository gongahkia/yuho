# Release Hardening

Yuho release tags must publish enough supply-chain metadata for downstream CI
to verify what was built and from which repository state.

Required release artifacts:

- Python wheel and sdist.
- SHA-256 checksum manifest for every uploaded artifact.
- SPDX JSON SBOM generated from the release checkout.
- GitHub build-provenance attestation for wheel, sdist, and SBOM.
- Docker image with BuildKit SBOM and provenance metadata enabled.
- Keyless Sigstore signature for the pushed container image digest.

The release workflow uses PyPI trusted publishing through GitHub OIDC. Do not
replace it with long-lived PyPI API tokens.

Workflow actions are pinned by immutable commit SHA. When Dependabot proposes
action updates, resolve the new tag to a commit and update the SHA plus the
release evidence docs in the same pull request.

Before creating a tag, run:

```bash
python scripts/release_audit.py --full
```

The reproducibility gate builds two clean source copies with separately
synchronized locked environments and records the compiler, Python, uv, and
`SOURCE_DATE_EPOCH` inputs in its report. The Docker image uses pinned Python
and uv image digests and records its installed OS/compiler inputs at
`/usr/share/yuho/build-inputs.txt`; release provenance identifies the published
image digest. These controls establish build-input traceability, not legal
correctness.

The release is not a legal-correctness certification. Public claims must map to
`docs/release/evidence.md` and the machine-readable
`docs/release/capability-claims.json` boundary.
