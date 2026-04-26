# Paper reproducibility

Methodological audit trail for the encoded library. The two scripts in
this directory are the **original prompt generators** that produced the
524-section Singapore Penal Code corpus. They are kept as scientific
record of *how the corpus was made*, not as active tooling — the
encoding shipped, and these files exist so an independent reader (peer
reviewer, replicating researcher, skeptical practitioner) can inspect
the exact agent prompt that was used.

## Files

- `phase_c_prompt.py` — the Phase C "encode this section from scratch"
  prompt generator. Renders `docs/researcher/phase-d-reencoding-prompt.md`
  with the section number substituted, prefixes a context block (marginal
  note, SSO anchor, suggested slug), and emits a paste-ready prompt.
- `phase_d_reencode.py` — the Phase D "re-encode this section using the
  new grammar primitives we landed (G1–G14)" dispatcher. Same shape:
  renders the prompt, optionally invokes Codex via `codex exec`.

## Why these are not in `scripts/`

The active-tooling scripts in `scripts/` are things a contributor would
run today: building the corpus, generating coverage reports, running
the AKN round-trip. The two files here are scoped to the original
encoding sweep; running them again would not improve the corpus and
isn't part of any standing workflow. Keeping them under
`paper/reproducibility/` makes their role explicit.

## How to verify the corpus from these prompts

A reader who wants to confirm "the published encoding of section N
matches what an agent would produce given the documented prompt" can:

1. Read `docs/researcher/phase-d-reencoding-prompt.md` for the prompt
   template.
2. Run `python paper/reproducibility/phase_d_reencode.py <N>` to see
   the exact rendered prompt that was handed to the agent.
3. Compare the output of running that prompt through their own coder
   to `library/penal_code/sN_*/statute.yh`.

This is the falsifiable methodological claim from the paper's
evaluation section.
