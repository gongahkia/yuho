from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


STATUTE = """
statute 1 "Demo" {
    elements {
        actus_reus taking := "takes";
        mens_rea intent := "intends";
    }
}
"""


def test_debug_break_on_element_outputs_hits_for_yh_facts(tmp_path: Path):
    statute = tmp_path / "statute.yh"
    statute.write_text(STATUTE, encoding="utf-8")
    facts = tmp_path / "facts.yh"
    facts.write_text(
        """
        bool taking := TRUE
        bool intent := FALSE
        """,
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["debug", "--break-on", "element", str(facts), str(statute)],
    )

    assert result.exit_code == 0
    assert "debug: section 1 (Demo)" in result.output
    assert "#1 fn element hit 1x: actus_reus taking -> satisfied" in result.output
    assert "#1 fn element hit 2x: mens_rea intent -> not satisfied" in result.output
    assert "overall: not satisfied" in result.output


def test_debug_break_on_element_json_output(tmp_path: Path):
    statute = tmp_path / "statute.yh"
    statute.write_text(STATUTE, encoding="utf-8")
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True, "intent": True}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["debug", "--break-on", "element", "--json", str(facts), str(statute)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["statute"]["overall_satisfied"] is True
    assert payload["hits"][0]["element"] == "taking"
    assert payload["hits"][1]["satisfied"] is True


def test_debug_preserves_nested_group_truth(tmp_path: Path):
    statute = tmp_path / "statute.yh"
    statute.write_text(
        """
        statute 1 "Nested" {
            elements {
                all_of {
                    actus_reus taking := "takes";
                    any_of {
                        mens_rea intent := "intends";
                        mens_rea reckless := "reckless";
                    }
                }
            }
        }
        """,
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(
        json.dumps({"taking": True, "intent": True, "reckless": False}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["debug", "--break-on", "element", str(facts), str(statute)],
    )

    assert result.exit_code == 0
    assert "mens_rea reckless -> not satisfied" in result.output
    assert "overall: satisfied" in result.output
