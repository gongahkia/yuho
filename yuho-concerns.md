# Yuho Concerns

This document records the current engineering and product concerns identified
in a repository-local audit. It does not assess legal correctness or any
external claims beyond what the repository itself states.

## Critical: primary CI can report success after a failed check

Several required commands in `.github/workflows/ci.yml` pipe their output to
`tee` without enabling `pipefail`. In the default GitHub Actions Bash shell,
the pipeline status is therefore the successful `tee` status rather than the
status of `black`, `mypy`, `pytest`, or the preceding command.

Affected examples include the dependency install, formatter, type-check,
parser smoke, and test steps. A failed test suite can consequently leave the
job successful and allow the build job to proceed. The workflow should enable
`pipefail` or otherwise preserve each command's exit status before its public
verification claims are relied upon.

## High: public verification wording exceeds the documented boundary

The README describes Yuho as a "formally verified" DSL. The feature status
matrix instead states that the runtime evaluator, Z3 backend, and Lean surface
are partial, and explicitly says Yuho does not prove end-to-end legal
correctness. The README should use the same bounded terminology as
`docs/positioning/status-matrix.md` and `docs/release/evidence.md`.

## Medium: the dependency story is not consistently reproducible

`uv.lock` exists, but the installation instructions and CI generally use
unconstrained `pip install` commands. The CI also installs the latest
`tree-sitter-cli` globally. This makes the lockfile ineffective as a shared
environment contract and leaves grammar generation and CI outcomes exposed to
upstream changes.

The release process is otherwise unusually strong: action SHAs are pinned,
release artifacts receive SBOM/provenance treatment, and the container image
is signed. The dependency installation path should match that standard.

## Medium: contributor documentation is stale

`.github/CONTRIBUTING.md` describes a `doc/` directory and links to
`doc/ARCHITECTURE.md`, neither of which exists. It also names an older Python
baseline than the package metadata. A new contributor can complete the main
setup but will encounter dead navigation when looking for the architecture
guide.

## Medium: the public product story should be more precise

Yuho is strongest as a developer-facing statute-encoding and review tool. Its
own release evidence says there is no hosted decision-service implementation,
and the status matrix identifies important partial surfaces. The front page
would be more credible if it led with a bounded workflow such as encoding,
checking, reviewing, and exporting a statute rather than implying a general
legal-correctness guarantee.

## Low: a few error-handling paths hide degraded behavior

- `src/yuho/services/analysis.py` loads cache entries with `pickle`. A process
  that can write to the user's Yuho cache can influence deserialization on a
  later analysis run. The exposure is local, but a data-only cache format would
  be safer.
- `src/yuho/library/reference_graph.py` silently skips files when analysis
  raises. A reference graph can therefore be incomplete without informing the
  caller.

## Scope and maintenance pressure

The repository contains a large encoded corpus and generated parser source,
while several central modules are over one thousand lines long. This is
defensible for the project, but it raises the review cost of parser, AST,
runtime, verifier, and transpiler changes. The existing corpus checks, status
matrix, and evidence ledger are valuable safeguards; they become trustworthy
only once the primary CI exit-status issue is corrected.

