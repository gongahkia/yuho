"""SARIF v2.1.0 output for CI and code scanning."""

import json
from typing import Any, Dict, List, Optional
from yuho import __version__

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA_URI = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
    "master/Schemata/sarif-schema-2.1.0.json"
)
SARIF_LEVELS = {"error", "warning", "note", "none"}


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


def sarif_rule(
    rule_id: str,
    description: str = "",
    level: str = "warning",
) -> Dict[str, Any]:
    """Create a SARIF reportingDescriptor."""
    return {
        "id": rule_id,
        "shortDescription": {"text": description or rule_id},
        "defaultConfiguration": {"level": level if level in SARIF_LEVELS else "warning"},
    }


def to_sarif(
    results: List[Dict[str, Any]],
    rules: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Convert results to SARIF JSON string."""
    tool_rules: list[dict[str, Any]] = []
    if rules:
        for r in rules:
            tool_rules.append(
                sarif_rule(
                    r.get("id", "unknown"), r.get("description", ""), r.get("level", "warning")
                )
            )
    known_rule_ids = {rule["id"] for rule in tool_rules}
    for rule_id in sorted({result.get("ruleId", "unknown") for result in results} - known_rule_ids):
        tool_rules.append(sarif_rule(rule_id, f"Yuho diagnostic {rule_id}"))
    artifacts = sarif_artifacts(results)
    sarif = {
        "$schema": SARIF_SCHEMA_URI,
        "version": SARIF_VERSION,
        "runs": [
            {
                "automationDetails": {"id": "yuho/check"},
                "tool": {
                    "driver": {
                        "name": "yuho",
                        "version": __version__,
                        "informationUri": "https://github.com/gongahkia/yuho",
                        "rules": tool_rules,
                    }
                },
                "invocations": [{"executionSuccessful": True}],
                "artifacts": artifacts,
                "results": results,
            }
        ],
    }
    errors = validate_sarif_document(sarif)
    if errors:
        raise ValueError("; ".join(errors))
    return json.dumps(sarif, indent=2)


def sarif_artifacts(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    uris = set()
    for result in results:
        for location in result.get("locations", []):
            uri = location.get("physicalLocation", {}).get("artifactLocation", {}).get("uri")
            if uri:
                uris.add(uri)
    return [
        {
            "location": {"uri": uri, "uriBaseId": "%SRCROOT%"},
            "roles": ["analysisTarget"],
        }
        for uri in sorted(uris)
    ]


def validate_sarif_document(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("version") != SARIF_VERSION:
        errors.append("version must be 2.1.0")
    if document.get("$schema") != SARIF_SCHEMA_URI:
        errors.append("schema URI must be SARIF 2.1.0")
    runs = document.get("runs")
    if not isinstance(runs, list) or not runs:
        return errors + ["runs must be a non-empty list"]
    for run_index, run in enumerate(runs):
        driver = run.get("tool", {}).get("driver", {})
        rule_ids = {rule.get("id") for rule in driver.get("rules", [])}
        if driver.get("name") != "yuho":
            errors.append(f"runs[{run_index}].tool.driver.name must be yuho")
        if not run.get("invocations"):
            errors.append(f"runs[{run_index}].invocations must be present")
        for result_index, result in enumerate(run.get("results", [])):
            rule_id = result.get("ruleId")
            if not rule_id:
                errors.append(f"runs[{run_index}].results[{result_index}].ruleId missing")
            elif rule_id not in rule_ids:
                errors.append(f"rule {rule_id} has no reportingDescriptor")
            if result.get("level") not in SARIF_LEVELS:
                errors.append(f"rule {rule_id} has invalid level")
            if not result.get("message", {}).get("text"):
                errors.append(f"rule {rule_id} message.text missing")
            if not result.get("locations"):
                errors.append(f"rule {rule_id} locations missing")
            for location_index, location in enumerate(result.get("locations", [])):
                physical = location.get("physicalLocation", {})
                artifact = physical.get("artifactLocation", {})
                region = physical.get("region", {})
                if not artifact.get("uri"):
                    errors.append(f"rule {rule_id} location {location_index} uri missing")
                if not region.get("startLine") or not region.get("startColumn"):
                    errors.append(f"rule {rule_id} location {location_index} region missing")
    return errors
