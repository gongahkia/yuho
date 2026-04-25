# s259 — L3 flag

- failed: 7, 8
- reason: The canonical penalty is cumulative ("shall be punished with imprisonment ... and shall also be liable to fine"), but the encoding uses `penalty or_both`, which incorrectly makes imprisonment optional.
- suggested fix: Replace the `penalty or_both` structure with a cumulative/default penalty form that preserves mandatory imprisonment plus liability to an unlimited fine.
