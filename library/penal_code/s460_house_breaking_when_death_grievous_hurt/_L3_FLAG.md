# s460 — L3 flag

- failed: 8
- reason: The encoding flattens the statute's disjunctive aggravated-act phrase ("causes or attempts to cause death or grievous hurt") into a single element instead of modeling the alternatives with `any_of`.
- suggested fix: Refine the aggravated-act limb into explicit disjunctive branches so the connective structure matches the English text.
