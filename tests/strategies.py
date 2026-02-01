"""
Hypothesis strategies for generating valid Yuho code.

These strategies generate random but syntactically valid Yuho
source code for property-based testing.
"""

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy
from typing import List


# =============================================================================
# Literal strategies
# =============================================================================


@st.composite
def yuho_int_literal(draw) -> str:
    """Generate a valid integer literal."""
    value = draw(st.integers(min_value=-1000000, max_value=1000000))
    return str(value)


@st.composite
def yuho_float_literal(draw) -> str:
    """Generate a valid float literal."""
    value = draw(st.floats(min_value=-1000000, max_value=1000000, allow_nan=False, allow_infinity=False))
    return f"{value:.2f}"


@st.composite
def yuho_bool_literal(draw) -> str:
    """Generate a valid boolean literal."""
    return draw(st.sampled_from(["TRUE", "FALSE"]))


@st.composite
def yuho_string_literal(draw) -> str:
    """Generate a valid string literal."""
    # Avoid problematic characters
    text = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "P", "S", "Z"),
                               blacklist_characters='"\\'),
        min_size=0,
        max_size=100
    ))
    return f'"{text}"'


@st.composite
def yuho_money_literal(draw) -> str:
    """Generate a valid money literal."""
    currency = draw(st.sampled_from(["$", "SGD", "USD", "EUR"]))
    dollars = draw(st.integers(min_value=0, max_value=1000000))
    cents = draw(st.integers(min_value=0, max_value=99))
    return f"{currency}{dollars}.{cents:02d}"


@st.composite
def yuho_percent_literal(draw) -> str:
    """Generate a valid percent literal (0-100)."""
    value = draw(st.integers(min_value=0, max_value=100))
    return f"{value}%"


@st.composite
def yuho_date_literal(draw) -> str:
    """Generate a valid ISO8601 date literal."""
    year = draw(st.integers(min_value=1900, max_value=2100))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    return f"{year:04d}-{month:02d}-{day:02d}"


@st.composite
def yuho_duration_literal(draw) -> str:
    """Generate a valid duration literal."""
    parts = []
    if draw(st.booleans()):
        years = draw(st.integers(min_value=1, max_value=100))
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if draw(st.booleans()):
        months = draw(st.integers(min_value=1, max_value=12))
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if draw(st.booleans()) or not parts:
        days = draw(st.integers(min_value=1, max_value=365))
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    return ", ".join(parts)


@st.composite
def yuho_literal(draw) -> str:
    """Generate any valid literal."""
    return draw(st.one_of(
        yuho_int_literal(),
        yuho_float_literal(),
        yuho_bool_literal(),
        yuho_string_literal(),
        yuho_money_literal(),
        yuho_percent_literal(),
    ))


# =============================================================================
# Identifier and type strategies
# =============================================================================


@st.composite
def yuho_identifier(draw) -> str:
    """Generate a valid identifier."""
    # Start with letter or underscore
    first_char = draw(st.sampled_from(list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")))
    # Rest can include digits
    rest = draw(st.text(
        alphabet=st.sampled_from(list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789")),
        min_size=0,
        max_size=20
    ))
    name = first_char + rest
    # Avoid keywords
    keywords = {"struct", "fn", "match", "case", "consequence", "pass", "return",
                "statute", "definitions", "elements", "penalty", "illustration",
                "import", "from", "TRUE", "FALSE", "int", "float", "bool", "string",
                "money", "percent", "date", "duration", "void"}
    if name.lower() in keywords or name in keywords:
        return "var_" + name
    return name


@st.composite
def yuho_type(draw) -> str:
    """Generate a valid type annotation."""
    base_types = ["int", "float", "bool", "string", "money", "percent", "date", "duration"]
    typ = draw(st.sampled_from(base_types))

    # Optionally make it optional or array
    modifier = draw(st.sampled_from([None, "optional", "array"]))
    if modifier == "optional":
        return f"{typ}?"
    elif modifier == "array":
        return f"[{typ}]"
    return typ


# =============================================================================
# Struct definition strategy
# =============================================================================


@st.composite
def yuho_field_def(draw) -> str:
    """Generate a valid field definition."""
    typ = draw(yuho_type())
    name = draw(yuho_identifier())
    return f"    {typ} {name},"


@st.composite
def yuho_struct_definition(draw) -> str:
    """Generate a valid struct definition."""
    name = draw(yuho_identifier())
    # Capitalize first letter for struct convention
    name = name[0].upper() + name[1:] if name else "Struct"

    num_fields = draw(st.integers(min_value=1, max_value=5))
    fields = [draw(yuho_field_def()) for _ in range(num_fields)]

    return f"struct {name} {{\n" + "\n".join(fields) + "\n}"


# =============================================================================
# Match expression strategy
# =============================================================================


@st.composite
def yuho_pattern(draw) -> str:
    """Generate a valid pattern."""
    kind = draw(st.sampled_from(["wildcard", "literal", "binding"]))
    if kind == "wildcard":
        return "_"
    elif kind == "literal":
        return draw(yuho_literal())
    else:
        return draw(yuho_identifier())


@st.composite
def yuho_match_arm(draw) -> str:
    """Generate a valid match arm."""
    pattern = draw(yuho_pattern())
    body = draw(st.one_of(yuho_literal(), yuho_identifier()))
    return f"    case {pattern} := consequence {body};"


@st.composite
def yuho_match_expression(draw, min_arms: int = 1, max_arms: int = 5) -> str:
    """Generate a valid match expression with N arms."""
    num_arms = draw(st.integers(min_value=min_arms, max_value=max_arms))
    arms = [draw(yuho_match_arm()) for _ in range(num_arms)]

    # Always add wildcard as last arm for exhaustiveness
    if not any("_" in arm for arm in arms):
        arms.append("    case _ := consequence pass;")

    scrutinee = draw(yuho_identifier())
    return f"match ({scrutinee}) {{\n" + "\n".join(arms) + "\n}"


# =============================================================================
# Statute block strategy
# =============================================================================


@st.composite
def yuho_definition_entry(draw) -> str:
    """Generate a definition entry."""
    term = draw(yuho_identifier())
    definition = draw(yuho_string_literal())
    return f"        {term} := {definition};"


@st.composite
def yuho_element_entry(draw) -> str:
    """Generate an element entry."""
    elem_type = draw(st.sampled_from(["actus_reus", "mens_rea", "circumstance"]))
    name = draw(yuho_identifier())
    description = draw(yuho_string_literal())
    return f"        {elem_type} {name} := {description};"


@st.composite
def yuho_penalty_block(draw) -> str:
    """Generate a penalty block."""
    parts = []

    if draw(st.booleans()):
        duration = draw(yuho_duration_literal())
        parts.append(f"        imprisonment := {duration};")

    if draw(st.booleans()) or not parts:
        money = draw(yuho_money_literal())
        parts.append(f"        fine := {money};")

    return "    penalty {\n" + "\n".join(parts) + "\n    }"


@st.composite
def yuho_statute_block(draw) -> str:
    """Generate a valid statute block."""
    section = draw(st.integers(min_value=1, max_value=999))
    title = draw(yuho_string_literal())

    # Definitions (0-3)
    num_defs = draw(st.integers(min_value=0, max_value=3))
    definitions = [draw(yuho_definition_entry()) for _ in range(num_defs)]
    defs_block = ""
    if definitions:
        defs_block = "    definitions {\n" + "\n".join(definitions) + "\n    }\n\n"

    # Elements (1-3)
    num_elems = draw(st.integers(min_value=1, max_value=3))
    elements = [draw(yuho_element_entry()) for _ in range(num_elems)]
    elems_block = "    elements {\n" + "\n".join(elements) + "\n    }\n\n"

    # Penalty
    penalty = draw(yuho_penalty_block())

    return f"""statute {section} {title} {{
{defs_block}{elems_block}{penalty}
}}"""


# =============================================================================
# Complete module strategy
# =============================================================================


@st.composite
def yuho_module(draw) -> str:
    """Generate a complete valid Yuho module."""
    parts = []

    # Structs (0-2)
    num_structs = draw(st.integers(min_value=0, max_value=2))
    for _ in range(num_structs):
        parts.append(draw(yuho_struct_definition()))

    # Statutes (1-2)
    num_statutes = draw(st.integers(min_value=1, max_value=2))
    for _ in range(num_statutes):
        parts.append(draw(yuho_statute_block()))

    return "\n\n".join(parts)
