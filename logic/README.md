# Logic evaluation 

* Boolean minimization in `prop_eval.py`

> [!WARNING]
> FUA continue to add these in the future!
>
> * Prime Implicant
> * Don’t Care Conditions
> * Tautology
> * SAT Solvers
> * Multi-Level Minimization
> * Factorization
> * Complementation
> * Heuristic minimzation

## Usage

```console
$ python3 learn.py
```

## Rationale

There are benefits to implementing a logic engine capable of heuristic and boolean minimization.  
By substituting truth values with statutory elements, complex statements evaluate to less complex ones and contradictions are easily identified.  

### Examples

<details>
<summary>
<h4>Simple examples</h4>
</summary>
<br>

```txt
"Driving while intoxicated" IS NOT NOT NOT NOT OFFENCE = "Driving while intoxicated" IS OFFENCE
```

```txt
"Carrying a concealed weapon" AND "Committing theft" IS OFFENCE = "Committing theft" IS OFFENCE AND "Carrying a concealed weapon" IS OFFENCE
```

```txt
"Entering the premises without permission" IF AND ONLY IF "Breaking a window" = "Breaking a window" -> "Entering the premises without permission"
```

```txt
NOT "Assaulting a police officer" IF AND ONLY IF "Acting in self-defense" = "Acting in self-defense" -> NOT "Assaulting a police officer"
```

```txt
"Selling prohibited substances" IS OFFENCE AND IS NOT OFFENCE = WRONGFUL_CLAIM: CONTRADICTION
```
</details>

> [!WARNING]
> Continue formatting and logicising the below examples to make sure readable

> [!WARNING]
> Continue adding examples below showing logical fallacies and other contradictions

> [!WARNING]
> Make every evaluated statement as atomic as possible, so should propositional formulas should evaluate to basic truth statements

<details>
<summary>
<h4>Complex examples</h4>
</summary>
<br>

```txt
("Driving while intoxicated" OR ("Committing vandalism" AND NOT "Paying damages")) IS OFFENCE IF AND ONLY IF (NOT "Providing false testimony" OR "Assisting in investigation") = ("Providing false testimony" -> ("Driving while intoxicated" OR ("Committing vandalism" AND NOT "Paying damages"))) AND (("Driving while intoxicated" OR ("Committing vandalism" AND NOT "Paying damages")) -> (NOT "Providing false testimony" OR "Assisting in investigation"))
```

```txt
((NOT "Trespassing" AND "Breaking a window") OR ("Carrying a concealed weapon" AND NOT "Fleeing from the scene")) IS OFFENCE AND (NOT "Committing theft" IF "Breaking a window") IS OFFENCE = 
((NOT "Trespassing" AND "Breaking a window") OR ("Carrying a concealed weapon" AND NOT "Fleeing from the scene")) IS OFFENCE AND ("Breaking a window" -> NOT "Committing theft") IS OFFENCE
```

```txt
("Fraud" OR (NOT "Embezzlement" AND ("Bribery" OR NOT "Tax evasion"))) AND ("Obstruction of justice" OR (NOT "Tax evasion" AND "Perjury")) IS OFFENCE IF AND ONLY IF (NOT "Obstruction of justice" OR "Cooperation with authorities") = ((("Fraud" OR (NOT "Embezzlement" AND ("Bribery" OR NOT "Tax evasion"))) AND ("Obstruction of justice" OR (NOT "Tax evasion" AND "Perjury"))) -> (NOT "Obstruction of justice" OR "Cooperation with authorities")) AND ((NOT "Obstruction of justice" OR "Cooperation with authorities") -> (("Fraud" OR (NOT "Embezzlement" AND ("Bribery" OR NOT "Tax evasion"))) AND ("Obstruction of justice" OR (NOT "Tax evasion" AND "Perjury"))))
```

```txt
(("Forgery" AND "Counterfeiting") OR NOT ("Breaking and entering" AND "Vandalism")) IF "Being an accomplice" IS OFFENCE AND ("Conspiracy" IF "Murder") IS OFFENCE = ("Being an accomplice" -> (("Forgery" AND "Counterfeiting") OR NOT ("Breaking and entering" AND "Vandalism"))) IS OFFENCE AND ("Murder" -> "Conspiracy") IS OFFENCE
```

```txt
NOT (("Money laundering" AND "Identity theft") OR ("Fraud" AND NOT "Forgery")) IS OFFENCE IF ("Assault" AND "Battery") IS NOT OFFENCE = ("Assault" AND "Battery") -> NOT (("Money laundering" AND "Identity theft") OR ("Fraud" AND NOT "Forgery")) IS OFFENCE
```
</details>

> [!WARNING]
> CCLaw talk from today notes
>   
> * ACT, POLICY, REFERENCE, PER, LEGISLATE, INCLUSIVE IF, EXCLUSIVE IF, CASE, STATUTE
> * OBITER, RATIO
> * WRONGFUL, RIGHTFUL
>   * subdivisions of WRONGFUL and RIGHTFUL
> * SHALL, MUST
>   * DSLs need to account for the nuances between SHALL and MUST
>   * What is a necessary compulsary consequence, what is a possible consequence


> * validation for a given equation 
> * basic inconsitency checking and testing facilities for DSLs
> * DSL must include a syntax to define a given thing recursively
> * give me an IDE that has some autocomplete and linting
> * make the linting and snippets comprehensive
> * DSLs must account for subsidiary legislation as well
> * definitions need to be recursive
> * diagrammatic representation should show ALL possible enumeratios and permutations of a given offence so that it can then be checked against an indiivdual's specified situation
> * maybe make these implicit assumptions clear in the base permutations shown
> * the diagrammatic representation DOES NOT account for base assumptions that are implicit within the law, like which court should hear a given case in the flowchart, like which jurisdiction a case should be heard in, like what constitutes a person per the interpretation act
> * eg. s415 the breakdown of a diagram does not even apply for those who are not singaporeans and this could expand to as far as we want
> * make EVERYTHING that is implciit in the understanding of the law EXPLICIT
> * still lacking grammer and diagrammatic representation that can reflect that a given statute is contingent on another statute, there's a specified grammer
> * shows the yuho code representation
> 
> If person must wear seatbelt and they don't, they're in breach of the provision, but could that be interpreted differently
> 
> FUA
>   * also consider changing my code font to iosevka
>   * how can we integrate LLMs that then produce yuho code
>   * https://boostdraft.com
>   * add these as articles to my readme.md
>   * https://www.doc.ic.ac.uk/~rak/papers/British%20Nationality%20Act.pdf
>   * https://www.semanticscholar.org/paper/The-British-Nationality-Act-as-a-logic-program-Sergot-Sadri/16d480717a1d233ae94b09e3b983d8cc96437644
> dont make drafting in pseduo-code a glorified version of form filling