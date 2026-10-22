# SDK-only inspection proposal

This temporary proposal contains the unchanged public library modules and
schemas, unchanged dependency freeze, owner-authorisation evidence, standard
Apache-2.0 text, a scoped NOTICE and an independently authored synthetic
public-facade example. It is a bounded experimental Singapore legal-modelling
DSL/SDK. No current-law, evidence-sufficiency or judicial determination is
claimed. The package version remains 1.0.0.0; no experimental profile changes.

Copy cabal.project.sdk to cabal.project and use GHC 9.8.4/Cabal 3.12.1.0 with the
pinned index/freeze and a prepared dependency cache. The sole Yuho import in
examples/sdk-distribution-consumer/Main.hs is Yuho.Authoring. Build that example
as a separate Cabal application depending on the extracted library. It asserts
proof, scoped definitions, grounded typed expressions/exact integers,
registered routes, temporal selection, computed binding, structured projection,
synthetic Unicode source recovery and snapshot/replay behaviour.

The schema directory documents the experimental authored/projection formats.
The original full SDK/research regression suites are not shipped in this
proposal because they depend on excluded excerpt-bearing examples and research
resources. No full make verify equivalence is claimed and no existing research
test is weakened. Owner boundary approval and independent file-level review
remain necessary. Repository/history exposure is unchanged.
