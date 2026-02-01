"""
Prompt templates for LLM interactions.
"""

STATUTE_EXPLANATION_PROMPT = """You are a legal expert explaining statute provisions to a general audience.

Your task is to explain the following legal statute in clear, accessible language that a non-lawyer could understand. Keep the legal accuracy but make it readable.

Guidelines:
1. Start with a one-sentence summary of what the statute covers
2. Explain each element of the offense in plain language
3. Describe the penalties in concrete terms
4. Provide a simple example to illustrate (if applicable)
5. Note any important exceptions or defenses

Yuho Statute Code:
```
{yuho_code}
```

Structured Analysis:
{english_explanation}

Please provide a clear, accessible explanation:
"""

STATUTE_TO_YUHO_PROMPT = """You are an expert in the Yuho legal DSL (domain-specific language). Your task is to convert natural language statute text into valid Yuho code.

## Yuho Grammar Summary

A Yuho statute has this structure:

```
statute SECTION_NUMBER "Title" {
    definitions {
        term := "definition";
    }

    elements {
        actus_reus element_name := "physical act description";
        mens_rea element_name := "mental state description";
        circumstance element_name := "circumstantial requirements";
    }

    penalty {
        imprisonment := DURATION;
        fine := MONEY_AMOUNT;
        supplementary := "additional punishment";
    }

    illustration LABEL {
        "Example scenario"
    }
}
```

## Types
- int: integers (e.g., 42)
- float: decimals (e.g., 3.14)
- bool: TRUE or FALSE
- string: "text in quotes"
- money: $100.00 or SGD1000
- percent: 50%
- date: 2024-01-15 (ISO format)
- duration: 3 years, 6 months, 10 days

## Match Expressions
For conditional elements:
```
match (condition) {
    case pattern := consequence result;
    case _ := consequence default_result;
}
```

## Example Statute

```
statute 415 "Cheating" {
    definitions {
        deceive := "to induce a person to believe as true something which is false";
        dishonestly := "with intention to cause wrongful gain or loss";
    }

    elements {
        actus_reus deception := "deceives any person";
        actus_reus inducement := "fraudulently or dishonestly induces the person deceived to deliver any property";
        mens_rea intention := "intention to cause wrongful gain or loss";
    }

    penalty {
        imprisonment := 0 years .. 10 years;
        fine := $0 .. $50,000;
    }
}
```

## Natural Language Statute to Convert

{statute_text}

## Instructions
1. Identify the section number and title
2. Extract key definitions
3. Identify actus reus (physical) elements
4. Identify mens rea (mental) elements
5. Parse the penalty provisions
6. Generate valid Yuho code

Please output only the Yuho code, no explanations:
"""

ANALYZE_COVERAGE_PROMPT = """You are a legal analyst reviewing statute coverage.

Given the following Yuho statutes, analyze:
1. What offenses are covered?
2. Are there any gaps in coverage (common offenses not addressed)?
3. Are the penalty ranges consistent across similar offenses?
4. Any overlapping definitions that might cause ambiguity?

Statutes:
{statutes_json}

Please provide your analysis:
"""

COMPARE_STATUTES_PROMPT = """You are a legal comparator.

Compare the following two statute representations:

Original Natural Language:
{original_text}

Yuho Code:
{yuho_code}

English Transpilation:
{english_output}

Analyze:
1. Does the Yuho code accurately capture all elements?
2. Are there any discrepancies between the original and the transpilation?
3. Are any elements missing or misrepresented?

Please provide your comparison:
"""
