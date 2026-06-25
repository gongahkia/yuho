"""Security baseline and workflow hardening checks."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.verify_action_pins import find_unpinned_actions


def test_security_policy_and_project_governance_files_exist() -> None:
    for path in [
        Path("SECURITY.md"),
        Path("CODE_OF_CONDUCT.md"),
        Path(".github/CODEOWNERS"),
        Path(".github/dependabot.yml"),
        Path("docs/contributor/branch-protection.md"),
    ]:
        assert path.exists(), path


def test_security_workflow_runs_codeql_scorecard_and_pip_audit() -> None:
    workflow = Path(".github/workflows/security.yml").read_text(encoding="utf-8")

    assert "github/codeql-action/init@" in workflow
    assert "github/codeql-action/analyze@" in workflow
    assert "ossf/scorecard-action@" in workflow
    assert "python -m pip_audit --strict" in workflow
    assert "security-events: write" in workflow
    assert "id-token: write" in workflow


def test_dependabot_tracks_package_and_action_ecosystems() -> None:
    config = Path(".github/dependabot.yml").read_text(encoding="utf-8")

    assert "package-ecosystem: pip" in config
    assert "package-ecosystem: github-actions" in config
    assert "package-ecosystem: npm" in config


def test_workflow_actions_are_pinned_to_sha() -> None:
    assert find_unpinned_actions() == []


def test_branch_protection_doc_lists_required_security_checks() -> None:
    doc = Path("docs/contributor/branch-protection.md").read_text(encoding="utf-8")

    for check in ["CodeQL", "OpenSSF Scorecard", "pip-audit", "Build Package"]:
        assert check in doc


def test_remote_action_refs_are_immutable_sha_refs() -> None:
    refs = re.findall(
        r"uses:\s*([^\s#]+)",
        "\n".join(path.read_text(encoding="utf-8") for path in Path(".github").glob("**/*.yml")),
    )
    remote = [ref for ref in refs if not ref.startswith("./")]

    assert remote
    assert all(re.search(r"@[0-9a-f]{40}$", ref) for ref in remote)
