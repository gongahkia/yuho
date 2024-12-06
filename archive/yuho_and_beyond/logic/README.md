# Logic evaluation 

Boolean and Heuristic minimization

## Rationale
  
There are many benefits to implementing a logic engine capable of heuristic and boolean minimization.  
  
By substituting truth values with statutory elements, complex statements evaluate to less complex ones.   
  
### Rightful examples

Rightful formulas are minimized to their fundamental propositions.

<details>
<summary>Example 1</summary>
<br>

```txt
"Driving while intoxicated" IS NOT NOT NOT NOT OFFENCE
```

```txt
"Driving while intoxicated" IS OFFENCE
```

</details>

<details>
<summary>Example 2</summary>
<br>

```txt
("Carrying a concealed weapon" AND "Committing theft") IS OFFENCE
```

```txt
"Committing theft" IS OFFENCE AND "Carrying a concealed weapon" IS OFFENCE
```

</details>

<details>
<summary>Example 3</summary>
<br>

```txt
"Resisting arrest" AND NOT "Under the influence of alcohol" IS OFFENCE
```

```txt
"Resisting arrest" IS OFFENCE AND "Under the influence of alcohol" NOT OFFENCE
```

</details>

<details>
<summary>Example 4</summary>
<br>

```txt
"Entering the premises without permission" IF AND ONLY IF "Breaking a window"
```

```txt
"Breaking a window" THEN ONLY "Entering the premises without permission"
```

```txt
ONLY "Breaking a window" -> "Entering the premises without permission"
```

</details>

<details>
<summary>Example 5</summary>
<br>

```txt
NOT "Assaulting a police officer" IF AND ONLY IF "Acting in self-defense"
```

```txt
"Acting in self-defense" THEN ONLY NOT "Assaulting a police officer"
```

```txt
ONLY "Acting in self-defense" -> NOT "Assaulting a police officer"
```

</details>

<details>
<summary>Example 6</summary>
<br>

```txt
NOT ("Possessing stolen goods" AND "Fleeing from police") IF AND ONLY IF "Being innocent"
```

```txt
"Being innocent" THEN ONLY NOT "Possessing stolen goods" OR NOT "Fleeing from police"
```

```txt
ONLY "Being innocent" -> NOT "Posessing stolen goods" OR NOT "Fleeing from police"
```

</details>

### Wrongful examples

Wrongful formulas are flagged.

<details>
<summary>Example 1</summary>
<br>

```txt
"Selling prohibited substances" IS OFFENCE AND IS NOT OFFENCE
```

```txt
WRONGFUL: CONTRADICTION
```

</details>

<details>
<summary>Example 2</summary>
<br>

```txt
"Selling prohibited substances" IS OFFENCE OR IS NOT OFFENCE
```

```txt
WRONGFUL: TAUTOLOGY
```

</details>

<details>
<summary>Example 3</summary>
<br>

```txt
"Selling prohibited substances" IS OFFENCE IF "Selling prohibited substances IS OFFENCE
```

```txt
WRONGFUL: CIRCULAR_REASONING
```

</details>

## Usage

```console
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ python3 learn.py
```
