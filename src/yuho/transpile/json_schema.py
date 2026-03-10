"""
JSON Schema generator for Yuho AST JSON output.

Produces a JSON Schema (draft 2020-12) that validates the output
of the JSON transpiler, enabling downstream tool integration.
"""

import json


def generate_json_schema() -> str:
    """Return JSON Schema for Yuho JSON transpiler output."""
    return json.dumps(_SCHEMA, indent=2)


_STRING_LIT = {
    "type": "object",
    "properties": {
        "_type": {"const": "StringLit"},
        "value": {"type": "string"},
    },
    "required": ["_type", "value"],
}

_DURATION = {
    "type": "object",
    "properties": {
        "_type": {"const": "DurationNode"},
        "years": {"type": "integer"},
        "months": {"type": "integer"},
        "days": {"type": "integer"},
        "hours": {"type": "integer"},
        "minutes": {"type": "integer"},
        "seconds": {"type": "integer"},
    },
    "required": ["_type"],
}

_MONEY = {
    "type": "object",
    "properties": {
        "_type": {"const": "MoneyNode"},
        "currency": {"type": "string"},
        "amount": {"type": "string"},
    },
    "required": ["_type", "currency", "amount"],
}

_DEFINITION_ENTRY = {
    "type": "object",
    "properties": {
        "_type": {"const": "DefinitionEntry"},
        "term": {"type": "string"},
        "definition": {"type": "object"},
    },
    "required": ["_type", "term", "definition"],
}

_ELEMENT_NODE = {
    "type": "object",
    "properties": {
        "_type": {"const": "ElementNode"},
        "element_type": {"type": "string", "enum": ["actus_reus", "mens_rea", "circumstance"]},
        "name": {"type": "string"},
        "description": {"type": "object"},
    },
    "required": ["_type", "element_type", "name", "description"],
}

_PENALTY_NODE = {
    "type": "object",
    "properties": {
        "_type": {"const": "PenaltyNode"},
        "imprisonment_min": {"$ref": "#/$defs/duration"},
        "imprisonment_max": {"$ref": "#/$defs/duration"},
        "fine_min": {"$ref": "#/$defs/money"},
        "fine_max": {"$ref": "#/$defs/money"},
        "caning_min": {"type": ["integer", "null"]},
        "caning_max": {"type": ["integer", "null"]},
        "death_penalty": {"type": ["boolean", "null"]},
    },
    "required": ["_type"],
}

_ILLUSTRATION_NODE = {
    "type": "object",
    "properties": {
        "_type": {"const": "IllustrationNode"},
        "label": {"type": ["string", "null"]},
        "description": {"type": "object"},
    },
    "required": ["_type", "description"],
}

_EXCEPTION_NODE = {
    "type": "object",
    "properties": {
        "_type": {"const": "ExceptionNode"},
        "label": {"type": ["string", "null"]},
        "condition": {"type": "object"},
        "effect": {"type": ["object", "null"]},
    },
    "required": ["_type", "condition"],
}

_CASELAW_NODE = {
    "type": "object",
    "properties": {
        "_type": {"const": "CaseLawNode"},
        "case_name": {"$ref": "#/$defs/stringLit"},
        "citation": {"$ref": "#/$defs/stringLit"},
        "holding": {"$ref": "#/$defs/stringLit"},
        "element_ref": {"type": ["string", "null"]},
    },
    "required": ["_type", "case_name"],
}

_STATUTE_NODE = {
    "type": "object",
    "properties": {
        "_type": {"const": "StatuteNode"},
        "section_number": {"type": "string"},
        "title": {"$ref": "#/$defs/stringLit"},
        "definitions": {"type": "array", "items": {"$ref": "#/$defs/definitionEntry"}},
        "elements": {"type": "array", "items": {"type": "object"}},
        "penalty": {"$ref": "#/$defs/penalty"},
        "illustrations": {"type": "array", "items": {"$ref": "#/$defs/illustration"}},
        "exceptions": {"type": "array", "items": {"$ref": "#/$defs/exception"}},
        "case_law": {"type": "array", "items": {"$ref": "#/$defs/caselaw"}},
    },
    "required": ["_type", "section_number", "definitions", "elements"],
}

AST_SCHEMA_VERSION = "1.0.0"

_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://yuho.dev/schemas/ast.json",
    "title": "Yuho AST JSON",
    "description": "Schema for Yuho JSON transpiler output (ModuleNode).",
    "version": AST_SCHEMA_VERSION,
    "type": "object",
    "properties": {
        "_type": {"const": "ModuleNode"},
        "_schema_version": {"const": AST_SCHEMA_VERSION},
        "imports": {"type": "array", "items": {"type": "object"}},
        "type_defs": {"type": "array", "items": {"type": "object"}},
        "function_defs": {"type": "array", "items": {"type": "object"}},
        "statutes": {"type": "array", "items": {"$ref": "#/$defs/statute"}},
        "variables": {"type": "array", "items": {"type": "object"}},
    },
    "required": ["_type", "imports", "type_defs", "function_defs", "statutes", "variables"],
    "$defs": {
        "stringLit": _STRING_LIT,
        "duration": _DURATION,
        "money": _MONEY,
        "definitionEntry": _DEFINITION_ENTRY,
        "element": _ELEMENT_NODE,
        "penalty": _PENALTY_NODE,
        "illustration": _ILLUSTRATION_NODE,
        "exception": _EXCEPTION_NODE,
        "caselaw": _CASELAW_NODE,
        "statute": _STATUTE_NODE,
    },
}
