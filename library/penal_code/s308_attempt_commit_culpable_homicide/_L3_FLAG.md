# s308 — L3 flag

- failed: 7
- reason: The `hurt_caused` penalty branch omits a structured caning punishment even though the canonical text expressly provides imprisonment, fine, caning, or any combination of those punishments.
- suggested fix: Add the missing `caning :=` punishment to the aggravated `when hurt_caused` penalty branch so every canonical punishment option is encoded.
