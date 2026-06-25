"""Release audit script contract."""

from __future__ import annotations

from pathlib import Path

from scripts.release_audit import audit_commands, git_project_files


def test_release_audit_quick_plan_contains_release_gates() -> None:
    commands = [" ".join(cmd) for cmd in audit_commands(Path("/tmp/yuho"), full=False)]
    joined = "\n".join(commands)

    assert "scripts/verify_action_pins.py" in joined
    assert "scripts/verify_corpus_provenance.py" in joined
    assert "scripts/verify_reproducible_build.py" in joined
    assert "scripts/verify_dsl_spec.py" in joined
    assert "pip_audit --strict" in joined


def test_release_audit_full_plan_runs_pytest_and_verify_core() -> None:
    commands = [" ".join(cmd) for cmd in audit_commands(Path("/tmp/yuho"), full=True)]
    joined = "\n".join(commands)

    assert "-m pytest" in joined
    assert "make verify-core" in joined


def test_release_audit_copy_plan_includes_untracked_release_files() -> None:
    files = {path.as_posix() for path in git_project_files()}

    assert "scripts/release_audit.py" in files
    assert "SECURITY.md" in files
    assert ".github/workflows/security.yml" in files
    assert ".venv" not in "\n".join(files)
