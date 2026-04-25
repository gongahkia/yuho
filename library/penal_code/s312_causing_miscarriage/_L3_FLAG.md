# s312 — L3 flag

- failed: 7, 8
- reason: The encoding invents a `pregnancy_not_more_than_16_weeks` condition and makes pregnancy duration an element-level `any_of`, but the statute states a base offence with a higher penalty only if the pregnancy exceeds 16 weeks.
- suggested fix: Keep the miscarriage elements unconditional and model the `more than 16 weeks` language only as an aggravated penalty branch, with the base penalty as the default.
