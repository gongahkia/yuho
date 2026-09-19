# Singapore criminal-law research corpus

The canonical coverage artifact is [`research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json`](../research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json), validated against its adjacent schema. It gives every one of the 524 rows in the saved Penal Code export exactly one structural coverage classification.

The current executable research subset connects 55 rows to models: 31 `executable_research` and 24 `executable_partial`. It contains 26 offence families, 13 general-exception families, 22 candidate penalties, 306 valid scenarios, and 16 analysis cases. These counts measure authored repository artifacts, not completeness or legal currency.

```sh
yuho corpus summary
yuho corpus list --category property
yuho corpus show penal-code:84
yuho corpus check
yuho corpus coverage --format json
yuho corpus graph --chapter chapter-xvii --format svg --output chapter-xvii.svg
```

From another working directory, append `--corpus-root /path/to/yuho`. The complete inventory graph is retained as JSON under [`research/singapore/corpus-v0.3/graphs/`](../research/singapore/corpus-v0.3/graphs/); bounded native SVG views avoid an unreadable 524-node drawing.

The generated [corpus index](../research/singapore/CORPUS-INDEX.md) lists categories, modules, scenarios, cases, review status and limitations. A row can be structurally indexed without being executable or legally reviewed. Open-textured propositions remain supplied classifications; Yuho does not assess their evidence.
