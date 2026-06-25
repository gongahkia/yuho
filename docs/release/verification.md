# Release Verification

Use these checks against a downloaded release artifact set.

## Python Artifacts

```bash
shasum -a 256 -c SHA256SUMS
python -m pip install --upgrade twine
twine check dist/*.whl dist/*.tar.gz
```

Verify GitHub artifact attestations:

```bash
gh attestation verify dist/*.whl --repo gongahkia/yuho
gh attestation verify dist/*.tar.gz --repo gongahkia/yuho
gh attestation verify dist/*.spdx.json --repo gongahkia/yuho
```

Inspect the SPDX SBOM:

```bash
jq '.spdxVersion, .packages | length' dist/yuho.spdx.json
```

## Container Image

Verify the keyless Sigstore signature:

```bash
cosign verify \
  --certificate-identity-regexp 'https://github.com/gongahkia/yuho/.github/workflows/release.yml@refs/tags/v.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/gongahkia/yuho:<tag>
```

Inspect the attached SBOM and provenance:

```bash
docker buildx imagetools inspect ghcr.io/gongahkia/yuho:<tag>
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp 'https://github.com/gongahkia/yuho/.github/workflows/release.yml@refs/tags/v.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/gongahkia/yuho:<tag>
```

## Source Claims

Public correctness claims must cite `docs/release/evidence.md`, not README
marketing text. Legal correctness remains out of scope beyond the listed
covered fragments.
