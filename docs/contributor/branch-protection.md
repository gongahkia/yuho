# Branch Protection

Protect `main` before tagging a release.

Required settings:

- Require pull requests before merging.
- Require at least one approving review.
- Require conversation resolution.
- Require status checks to pass before merging.
- Require branches to be up to date before merging.
- Block force pushes.
- Block deletions.

Required checks:

- `Lint & Type Check`
- `Test (Python 3.10)`
- `Test (Python 3.11)`
- `Test (Python 3.12)`
- `Test (Python 3.13)`
- `Akoma Ntoso XSD round-trip`
- `Build Package`
- `CodeQL`
- `OpenSSF Scorecard`
- `pip-audit`

Release tags should be created only after `python scripts/release_audit.py
--full` passes locally or in an equivalent clean CI environment.
