# Section 84 research record

This directory retains the saved sources, mappings, scoped review records, executable model and regression artifacts for Yuho’s bounded Penal Code section 84 research representation.

- [`surface/section84.yh`](surface/section84.yh) is the human-readable standalone model.
- [`prototype/request.json`](prototype/request.json) is the frozen 7,599-byte KernelInput fixture.
- [`AUTHORITY-REGISTER.json`](AUTHORITY-REGISTER.json), [`PROPOSITION-REVIEW-MATRIX.json`](PROPOSITION-REVIEW-MATRIX.json), [`TEMPORAL-APPLICABILITY-MATRIX.json`](TEMPORAL-APPLICABILITY-MATRIX.json) and [`SOURCE-LOCK.json`](SOURCE-LOCK.json) state the source and applicability boundaries.
- [`QUALIFIED-REVIEW-RECORD.json`](QUALIFIED-REVIEW-RECORD.json) and [`IMPLEMENTATION-CONFORMANCE-RECORD.json`](IMPLEMENTATION-CONFORMANCE-RECORD.json) are privacy-safe, scoped records; they do not authenticate the reviewer or transfer review to changed bytes.
- [`records/`](records/) contains the retained research reports named by those records.

The current Haskell models also reuse section 84 through exact-version modules and actor-scoped attachments. Run the root test suite for byte and semantic regressions.

Nothing here establishes legal currency, assesses evidence or diagnosis, or determines guilt, conviction, acquittal, sentence, fitness or a court disposition.
