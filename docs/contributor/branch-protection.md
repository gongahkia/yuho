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
- `Clean Release Gate`
- `Build Package`
- `CodeQL`
- `OpenSSF Scorecard`
- `pip-audit`

Configure these checks in the repository ruleset or branch-protection rule;
the `Clean Release Gate` runs the same locked `scripts/release_audit.py --full`
plan on pull requests, `main`, and release tags. A release tag should be
created only after that check has passed for the exact commit being tagged.
