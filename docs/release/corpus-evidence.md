# Corpus Evidence Model

The checked-in Penal Code ledger currently proves only that the repository's
raw section text and `.yh` source match their recorded SHA-256 digests. It
does not establish that the snapshot is current official text, that an
encoding has the intended legal meaning, or that every record has human or
independent review.

New corpus work must use the versioned
[evidence-record schema](corpus-evidence-schema.json). Historical L3 stamps
are retained as historical evidence and must not be upgraded to a stronger
review state without the required records.

Canonical IR now has a deterministic semantic artifact at
`yuho.canonical-ir` v1.1. Its semantic digest deliberately excludes the
optional normalized source-text digest, so formatting/source retrieval provenance cannot
be mistaken for a semantic equivalence claim. This does not materialize the
source snapshots, source spans, or review records required below; that work
remains subject to the evidence schema.

## Required record chain

1. Fetch authoritative source bytes and store an immutable raw snapshot at a
   digest-addressed path. Record the retrieval time, source URL, jurisdiction,
   version metadata, and SHA-256 of the exact bytes.
2. Normalize only through a versioned, deterministic process. Retain both raw
   and normalized hashes; changing either creates a new evidence record rather
   than rewriting the prior one.
3. Link each source span, by byte offsets in the normalized snapshot, to the
   canonical-IR node or nodes it supports. The record must carry the v1
   canonical semantic hash, `.yh` byte hash, grammar version, and compiler
   version used to create it.
4. Record automated triage as automated assistance, including model, prompt,
   and tool versions. It may prioritise work or flag defects, but cannot
   certify legal fidelity.
5. Record human review with a named reviewer, rubric version, decision,
   reviewed input hashes, and timestamp. A high-risk approval requires an
   independent named reviewer whose identifier differs from the first
   reviewer. Review records become invalid when any reviewed input hash
   changes.

The schema describes the target record; it is intentionally stricter than the
legacy ledger. Until all required fields exist and validate, public claims
remain limited to the legacy hash and review-category evidence in
[`capability-claims.json`](capability-claims.json).
