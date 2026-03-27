"""SARIF v2.1.0 output for GitHub Code Scanning."""

import json
from typing import Any, Dict, List, Optional
from yuho import __version__


def make_sarif_result(
    rule_id: str,
    message: str,
    file: str,
    line: int = 1,
    col: int = 1,
    level: str = "error",
) -> Dict[str, Any]:
    """Create a single SARIF result entry."""
    return {
        "ruleId": rule_id,
        "level": level,
        "message": {"text": message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": file, "uriBaseId": "%SRCROOT%"},
                    "region": {"startLine": line, "startColumn": col},
                }
            }
        ],
    }


def to_sarif(
    results: List[Dict[str, Any]],
    rules: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Convert results to SARIF JSON string."""
    tool_rules = []
    if rules:
        for r in rules:
            tool_rules.append(
                {
                    "id": r.get("id", "unknown"),
                    "shortDescription": {"text": r.get("description", "")},
                    "defaultConfiguration": {"level": r.get("level", "warning")},
                }
            )
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "yuho",
                        "version": __version__,
                        "informationUri": "https://github.com/gongahkia/yuho",
                        "rules": tool_rules,
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(sarif, indent=2)
