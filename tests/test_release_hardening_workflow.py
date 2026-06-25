"""Release workflow supply-chain hardening checks."""

from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(".github/workflows/release.yml")
DOC = Path("docs/contributor/release-hardening.md")


def test_release_workflow_generates_sbom_hashes_and_attestations() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "id-token: write" in workflow
    assert "attestations: write" in workflow
    assert "anchore/sbom-action@" in workflow
    assert "format: spdx-json" in workflow
    assert "dist/*.spdx.json" in workflow
    assert "shasum -a 256" in workflow
    assert "actions/attest-build-provenance@" in workflow


def test_release_workflow_enables_docker_sbom_and_provenance() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "sbom: true" in workflow
    assert "provenance: mode=max" in workflow
    assert "sigstore/cosign-installer@" in workflow
    assert "cosign sign --yes" in workflow


def test_release_hardening_doc_tracks_workflow_contract() -> None:
    doc = DOC.read_text(encoding="utf-8")

    for term in ["SPDX", "SHA-256", "attestation", "Docker", "OIDC", "Sigstore"]:
        assert term in doc
