# s376 — L3 flag

- failed: 8
- reason: The encoding does not preserve the statute's disjunctive structure faithfully because subsection (3) is modeled as `penalty or_both` despite the text saying only "fine or to caning", and subsection (4)'s paragraphs (a), (b), and (c) are not expressed as a formal top-level `any_of`.
- suggested fix: Replace subsection (3) with an alternative additional-penalty encoding and model subsection (4) with an explicit disjunctive `any_of` structure following the s375 gold-standard pattern.
