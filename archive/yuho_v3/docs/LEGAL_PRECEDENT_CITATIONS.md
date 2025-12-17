# Legal Precedent Citations in Yuho

This document explains the **Legal Precedent Citations** system for annotating code with case law references.

## Overview

Legal reasoning relies heavily on precedent - previous court decisions that establish binding principles. Yuho allows you to annotate struct fields with `@precedent` to link them to authoritative case law.

## Syntax

### Basic Annotation

```yuho
struct Cheating {
    @precedent("Tan Siew Eng v PP [1997] SGHC 123")
    bool deception,
}
```

The annotation links the `deception` field to the cited case, indicating this element comes from established case law.

### Multiple Precedents

```yuho
struct Negligence {
    @precedent("Spandeck Engineering v DSTA [2007] SGCA 37")
    bool duty_of_care,
    
    @precedent("Sunny Metal v Ng Khim Ming [2007] SGCA 36")
    bool breach_of_duty,
}
```

Different fields can reference different precedents.

## Citation Format

### Singapore Cases

Standard Singapore citation format:
```
[Party 1] v [Party 2] [Year] [Court] [Case Number]
```

Examples:
- `Lee Kuan Yew v Davies Derek Gwyn [1989] SGHC 20` (High Court)
- `Spandeck Engineering v DSTA [2007] SGCA 37` (Court of Appeal)
- `PP v Tan Chee Hwee [2008] SGDC 98` (District Court)

### Court Abbreviations

- `SGCA` - Court of Appeal
- `SGHC` - High Court
- `SGDC` - District Court
- `SGMC` - Magistrate's Court

## LaTeX Transpilation

### Without Bibliography

```bash
yuho latex precedents.yh
```

Output includes inline citations:

```latex
\item[\texttt{deception}] A boolean value (type: \texttt{bool}) 
    \textit{(Tan Siew Eng v PP [1997] SGHC 123)}
```

### With Bibliography

```bash
yuho latex --with-citations precedents.yh
```

Output includes numbered references and a bibliography:

```latex
\item[\texttt{deception}] A boolean value (type: \texttt{bool}) 
    \textit{[See precedent 1]}

...

\section*{Legal Precedents}
\begin{enumerate}
  \item[1] Tan Siew Eng v PP [1997] SGHC 123
  \item[2] Gunasegaran s/o Pavadaisamy v PP [1997] SGCA 14
\end{enumerate}
```

## Use Cases

### Criminal Law Elements

```yuho
struct MurderElements {
    @precedent("Ong Pang Siew v PP [2011] SGCA 37")
    bool intention_to_cause_death,
    
    @precedent("Pathip Selvan v PP [2012] SGCA 38")
    bool caused_death,
}
```

Links each element to the case establishing that requirement.

### Tort Law Standards

```yuho
struct DefamationElements {
    @precedent("Lee Kuan Yew v Davies [1989] SGHC 20")
    bool false_statement,
    
    @precedent("Ramachandran v Wuu David [1999] SGHC 82")
    bool published_to_third_party,
}
```

### Contract Law Requirements

```yuho
struct ContractFormation {
    @precedent("Gay Choon Ing v Loh Sze Ti [2009] SGCA 3")
    bool offer_and_acceptance,
    
    @precedent("RDC Concrete v Sato Kogyo [2007] SGCA 39")
    bool consideration,
}
```

## Benefits

### Legal Research

- **Traceability**: Every element links to its source
- **Authority**: Shows established case law support
- **Updates**: Easy to update when cases are overruled

### Documentation

- **Clarity**: Readers understand the legal basis
- **Citations**: Automatic bibliography generation
- **Professional**: Proper legal formatting

### Verification

- **Accuracy**: Ensures elements align with precedent
- **Completeness**: Check all elements are supported
- **Currency**: Validate cases are still good law

## Best Practices

1. **Accurate Citations**: Use exact case names and citations
2. **Relevant Precedents**: Choose cases directly on point
3. **Recent Cases**: Prefer recent authoritative decisions
4. **Binding Authority**: Use Court of Appeal cases when available
5. **Multiple Jurisdictions**: Note if using non-Singapore cases

## Validation

The semantic checker can validate:

- **Citation format**: Proper syntax and structure
- **Court hierarchy**: Appropriate level of authority
- **Year plausibility**: Cases from valid year ranges
- **Completeness**: All critical fields have precedent support

## Integration with Other Features

### With Citations

```yuho
struct Offense {
    @precedent("PP v Tan [2008] SGDC 98")
    Citation<"415", "1", "Penal Code"> statutory_basis,
}
```

Combines statutory citations with case law.

### With Constraints

```yuho
struct AdversePossession {
    @precedent("Balwant Singh v Double L [1996] SGCA 78")
    bool factual_possession,
    
    @precedent("Wong Kok Chin v Mah Ten Kui [2015] SGHC 107")
    bool continuous_possession where duration >= 12,
}
```

Precedents support constrained fields.

### With Temporal Types

```yuho
struct Contract {
    @precedent("Gay Choon Ing v Loh [2009] SGCA 3")
    Temporal<bool, valid_from="01-01-2009"> binding_authority,
}
```

Track when precedent became binding.

## Transpilation Targets

| Target | Precedent Support |
|--------|------------------|
| LaTeX | ✓✓ (Bibliography) |
| English | ✓ (Inline mentions) |
| TypeScript | ✓ (JSDoc comments) |
| JSON | ✓ (Metadata) |
| Mermaid | ✗ |
| Alloy | ✗ |
| Gazette | ~ (Parenthetical notes) |

## Related Features

- **Legal Citations** (`Citation<>`) - Statutory references
- **Presumption Tracking** (`@presumed`) - Legal presumptions
- **Temporal Logic** - Time-bound precedent validity
- **Constraint Inheritance** - Precedents inherited with fields

## Examples

See `examples/precedents.yh` for comprehensive examples:
- Criminal law with murder and cheating precedents
- Tort law with defamation and negligence cases
- Contract law with formation and breach cases
- Property law with adverse possession cases
- Proper citation formatting for all court levels
