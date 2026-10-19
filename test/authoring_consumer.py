"""Run the separately packaged SDK consumer outside the checkout and check schemas."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    executable = parser.parse_args().executable.resolve()
    with tempfile.TemporaryDirectory(prefix="yuho-independent-consumer-") as folder:
        directory = Path(folder)
        completed = subprocess.run(
            [str(executable), "--artifacts", str(directory)], cwd=directory,
            capture_output=True, check=False, timeout=60,
        )
        assert completed.returncode == 0, completed.stderr.decode()
        assert not completed.stderr, completed.stderr
        assert len(completed.stdout.splitlines()) == 2
        for schema_name, artifacts in [
            ("authoring-v0.1-experimental.schema.json", ["document.json", "pending-document.json"]),
            ("request.schema.json", ["request.json"]),
            ("result.schema.json", ["result.json"]),
        ]:
            schema = json.loads((ROOT / "schema" / schema_name).read_bytes())
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            for artifact in artifacts:
                validator.validate(json.loads((directory / artifact).read_bytes()))
        application = json.loads((directory / "application.json").read_bytes())
        pending = json.loads((directory / "pending-application.json").read_bytes())
        comparison = json.loads((directory / "comparison.json").read_bytes())
        assert application["reportConclusion"] == "satisfied"
        assert pending["reportConclusion"] == "unresolved"
        assert comparison["comparisonConclusionChanged"]
        assert application["reportSnapshot"] != pending["reportSnapshot"]
        assert any(row["observationNode"] == "f:deception"
                   and len(row["observationAssertions"]) == 2
                   for row in application["reportRequirements"])
        guards = [row for row in pending["reportRequirements"]
                  if row["observationRule"] == "x:section84"]
        assert guards and all(row["observationEvaluation"] == "not_evaluated"
                              and row["observationComputed"] is None for row in guards)
        snapshot = json.loads((directory / "snapshot.json").read_bytes())
        assert snapshot["snapshotDocument"]["documentRelationships"]
        assert snapshot["snapshotDocument"]["documentAnnotations"][0]["annotationState"] == "draft"
    print("independent authoring consumer: outside-checkout execution, authored/kernel schemas, reports and retained context passed")


if __name__ == "__main__":
    main()
