# s476 — L3 flag

- failed: 7, 8
- reason: The canonical penalty is imprisonment up to 10 years and liability to fine, but the encoding uses `penalty or_both`, which introduces an alternative fine-only branch not stated in the statute.
- suggested fix: Replace the penalty form with a cumulative or otherwise explicitly mandatory imprisonment-plus-fine encoding that matches the canonical text.
