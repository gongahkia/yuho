# Facts JSON

Yuho commands that evaluate statutes accept the legacy shorthand:

```json
{
  "deception": true,
  "fraudulent": true
}
```

They also accept typed facts:

```json
{
  "facts": {
    "deception": {
      "value": true,
      "type": "bool",
      "source": "complainant statement",
      "date": "2026-06-23",
      "jurisdiction": "SG",
      "evidential_status": "admitted",
      "burden": "prosecution",
      "standard_of_proof": "beyond_reasonable_doubt",
      "confidence": 0.9
    }
  }
}
```

The schema is [facts-schema.json](facts-schema.json).

Compatibility rule: primitive fact values remain valid. Typed fact objects use
their `value` field for truth and preserve metadata for explanation output.
When a Yuho element declares `burden` or a proof standard, typed fact metadata
with `burden` or `standard_of_proof` must match that declaration; primitive
facts and typed facts without those metadata fields keep legacy truth behavior.

Structured objects can back element predicates:

```yh
actus_reus deception := facts.representation.falsehood && facts.accused.knows_falsehood;
```

```json
{
  "representation": {
    "falsehood": true
  },
  "accused": {
    "knows_falsehood": true
  }
}
```
