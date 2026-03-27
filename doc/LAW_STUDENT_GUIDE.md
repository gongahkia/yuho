# Yuho for Law Students

A practical guide for using Yuho to study Criminal Law. No programming experience needed.

## What Yuho does for you

Yuho helps you break down statutes into their **elements** and see how those elements relate logically. You write a short structured file (`.yh`), and Yuho:

1. **Validates** your breakdown is structurally complete
2. **Explains** it back to you in plain English
3. **Draws** diagrams showing element relationships
4. **Tests** hypothetical fact patterns against your statute model

## Getting started

```bash
pip install yuho
```

## Option A: Use the wizard (no code)

```bash
yuho wizard
```

The wizard walks you through building a statute model step-by-step. It asks for:
- Section number and title
- Definitions (key legal terms)
- Elements: actus reus, mens rea, and circumstances
- Penalties
- Illustrations

It generates a valid `.yh` file you can use immediately.

## Option B: Write `.yh` directly

Here is Section 378 (Theft) modelled in Yuho:

```yh
statute 378 "Theft" {
    definitions {
        moveable_property := "Any corporeal property except land and things permanently attached to the earth";
        dishonestly := "With intention of causing wrongful gain to one person or wrongful loss to another";
    }

    elements {
        all_of {
            actus_reus taking := "Takes any moveable property out of the possession of any person";
            actus_reus moving := "Moves that property in order to such taking";
            mens_rea dishonest_intent := "Intends to take the property dishonestly";
            circumstance without_consent := "Without the consent of the person in possession";
        }
    }

    penalty {
        imprisonment := 1 year .. 7 years;
        fine := $0.00 .. $10,000.00;
    }

    illustration exampleA {
        "A finds a ring on the road, not knowing to whom it belongs. A picks it up. This is not theft. But if A later discovers the owner and keeps it dishonestly, A is guilty of theft."
    }
}
```

### Key concepts

| Yuho keyword | Legal meaning |
|---|---|
| `actus_reus` | Physical/conduct element |
| `mens_rea` | Mental/fault element |
| `circumstance` | Surrounding factual conditions |
| `all_of { }` | ALL elements must be satisfied (AND) |
| `any_of { }` | ANY element suffices (OR) |
| `exception` | Defence or proviso that negates liability |

## Validate your model

```bash
yuho check my_statute.yh
```

Yuho tells you if anything is structurally wrong: missing elements, syntax errors, etc. Error messages explain what went wrong and how to fix it.

## Generate plain English

```bash
yuho transpile my_statute.yh -t english
```

This outputs a structured English explanation of your statute model. Use it to verify your understanding matches the actual statute text.

## Generate diagrams

```bash
yuho transpile my_statute.yh -t mermaid
```

This outputs a Mermaid diagram you can paste into:
- **Obsidian** (renders natively)
- **Notion** (use a Mermaid code block)
- **GitHub** (renders in `.md` files)
- [mermaid.live](https://mermaid.live) (online renderer)

The diagram shows which elements are AND-grouped (`all_of`) vs OR-grouped (`any_of`).

## Test fact patterns

Create a test file that references your statute and asserts outcomes:

```yh
referencing penal_code/s378_theft

struct TheftCase {
    string accused,
    bool tookProperty,
    bool movedProperty,
    bool dishonestIntent,
    bool withoutConsent,
}

TheftCase scenario := TheftCase {
    accused := "Alice",
    tookProperty := TRUE,
    movedProperty := TRUE,
    dishonestIntent := TRUE,
    withoutConsent := TRUE,
}

assert scenario.tookProperty && scenario.dishonestIntent, "Alice satisfies AR + MR"
```

Run with:

```bash
yuho test my_statute.yh
```

## Explore the library

Yuho currently ships with 25 pre-modelled Penal Code sections, including:

| Section | Offence |
|---|---|
| s299 | Culpable Homicide |
| s300 | Murder |
| s302 | Punishment for Murder |
| s304 | Culpable Homicide not amounting to Murder |
| s319 | Hurt |
| s321 | Voluntarily Causing Hurt |
| s323 | Punishment for Voluntarily Causing Hurt |
| s325 | Voluntarily Causing Grievous Hurt |
| s354 | Assault or Criminal Force to Outrage Modesty |
| s363 | Kidnapping |
| s378 | Theft |
| s379 | Punishment for Theft |
| s383 | Extortion |
| s390 | Robbery |
| s392 | Punishment for Robbery |
| s395 | Dacoity |
| s403 | Dishonest Misappropriation |
| s406 | Punishment for Criminal Breach of Trust |
| s411 | Dishonestly Receiving Stolen Property |
| s415 | Cheating |
| s420 | Cheating Inducing Delivery |
| s463 | Forgery |
| s465 | Punishment for Forgery |
| s499 | Defamation |
| s503 | Criminal Breach of Trust |

Transpile any of them:

```bash
yuho transpile library/penal_code/s300_murder/statute.yh -t english
yuho transpile library/penal_code/s300_murder/statute.yh -t mermaid
```

## Tips for exam prep

1. **Model before you memorise**: Building a `.yh` file forces you to identify every element. This is the same exercise your exam requires.
2. **Use `all_of` / `any_of` deliberately**: The grouping reflects the logical structure the court applies. Getting this right means you understand the statute.
3. **Add exceptions**: Statutes like s300 (Murder) have exceptions (provocation, private defence). Modelling these helps you spot defence arguments.
4. **Test edge cases**: Write fact patterns where only some elements are satisfied. Yuho's assertions tell you which elements pass and which don't.
5. **Compare related offences**: Model s299 (Culpable Homicide) alongside s300 (Murder) to see exactly where they differ.

## Further reading

- [Full syntax reference](./SYNTAX.md)
- [5-minute quickstart](./5_MINUTES.md)
- [CLI reference](./CLI_REFERENCE.md)
- [FAQ](./FAQ.md)
