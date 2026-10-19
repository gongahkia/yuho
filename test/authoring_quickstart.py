"""Build the documented public SDK quickstart as an external Cabal project."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def verify_projection(directory, stem, contract):
    load = lambda suffix: json.loads((directory / (stem + suffix)).read_bytes())
    projection = load(".projection.json")
    Draft202012Validator(contract, format_checker=FormatChecker()).validate(projection)
    view = load(".view-bindings.json")
    definition(contract, "view", view)
    assert view["viewProjectionId"] == projection["projectionId"]
    nodes = {n["projectedNodeId"]: n for n in projection["projectionNodes"]}
    edges = {e["projectedEdgeId"]: e for e in projection["projectionEdges"]}
    assert len(nodes) == len(projection["projectionNodes"]) and len(edges) == len(projection["projectionEdges"])
    for kind, ids in [("Nodes", nodes), ("Edges", edges)]:
        included, omitted = view["viewIncluded" + kind], view["viewOmitted" + kind]
        assert set(included).isdisjoint(omitted) and set(included + omitted) == set(ids)
    assert all(e["projectedEdgeFrom"] in nodes and e["projectedEdgeTo"] in nodes for e in edges.values())
    assert all(edges[e]["projectedEdgeFrom"] in view["viewIncludedNodes"] and
               edges[e]["projectedEdgeTo"] in view["viewIncludedNodes"] for e in view["viewIncludedEdges"])
    definition(contract, "legacyView", load(".view.json"))
    ns = {"s": "http://www.w3.org/2000/svg", "g": "urn:yuho:semantic-graph:v0.1"}
    svg = ET.parse(directory / (stem + ".svg")).getroot()
    xml = ET.parse(directory / (stem + ".view.xml")).getroot()
    ids = [x.attrib["id"] for x in svg.iter() if "id" in x.attrib]
    assert len(ids) == len(set(ids))
    cards = svg.findall("s:g[@id='objects']/s:g", ns)
    paths = svg.findall("s:g[@id='connections']//s:path", ns)
    assert {c.attrib["id"] for c in cards} == {b["viewBindingRenderedId"] for b in view["viewNodeBindings"]}
    assert {p.attrib["id"] for p in paths} == {b["edgeBindingRenderedId"] for b in view["viewEdgeBindings"]}
    assert len(xml.findall("g:edges/g:edge", ns)) == len(paths) == len(view["viewIncludedEdges"])
    return projection


def definition(contract, name, value):
    Draft202012Validator({"$defs": contract["$defs"], "$ref": "#/$defs/" + name},
                         format_checker=FormatChecker()).validate(value)


def verify_outputs(review):
    contract = json.loads((ROOT / "schema/analysis-projection-v0.1-experimental.schema.json").read_bytes())
    authored = json.loads((ROOT / "schema/authoring-v0.1-experimental.schema.json").read_bytes())
    for item in [contract, authored]:
        Draft202012Validator.check_schema(item)
    anchors = review / "anchors"
    success = json.loads((anchors / "anchors-success.json").read_bytes())
    assert len(success) == 14
    for row in success:
        expected = row["anchorInput"]
        assert row["byteReference"] == row["codePointReference"]
        assert row["byteReference"]["referenceSpan"] == expected["exampleExpected"]
        assert row["recoveredOriginal"]["excerptText"] == expected["exampleExcerpt"]
        assert row["recoveredOriginal"]["excerptSource"]["sourceText"] == expected["exampleText"]
        definition(contract, "originalSourceExcerpt", row["recoveredOriginal"])
    cat = next(r for r in success if r["anchorInput"]["exampleName"] == "multibyte")
    assert cat["byteReference"]["referenceSpan"] == {
        "start": 2, "end": 5, "startLine": 1, "startColumn": 3, "endLine": 1, "endColumn": 6}
    failures = json.loads((anchors / "anchors-invalid.json").read_bytes())
    assert len(failures) == 14
    for request, diagnostics in failures:
        assert any(d["diagnosticCode"] == request["invalidExpectedCode"] and
                   request["invalidSource"]["sourceId"] in d["diagnosticObjects"] for d in diagnostics)
    old = verify_projection(anchors, "source-before", contract)
    new = verify_projection(anchors, "source-replaced", contract)
    assert old["projectionSnapshot"]["snapshotId"] != new["projectionSnapshot"]["snapshotId"]
    before, after = json.loads((anchors / "source-revision-excerpts.json").read_bytes())
    assert before["excerptReference"] == after["excerptReference"]
    assert before["excerptText"] == "猫" and after["excerptText"] == "犬"
    assert any(d["diagnosticCode"] == "PSTALE" for d in json.loads((anchors / "source-stale-diagnostics.json").read_bytes()))
    assert any(d["diagnosticCode"] == "ASPAN" for d in json.loads((anchors / "source-shifted-diagnostics.json").read_bytes()))
    output = review / "quickstart/output"
    for folder in [anchors, output]:
        for path in folder.glob("*.document.json"):
            Draft202012Validator(authored).validate(json.loads(path.read_bytes()))
        for path in folder.glob("*.application.json"):
            definition(contract, "application", json.loads(path.read_bytes()))
        for path in folder.glob("*.comparison.json"):
            definition(contract, "comparison", json.loads(path.read_bytes()))
    summary = json.loads((output / "summary.json").read_bytes())
    assert summary["before"] == summary["after"] == "satisfied" and summary["savedReloaded"] == "true"
    assert summary["oldSnapshot"] != summary["newSnapshot"]
    assert summary["excerpt"] == "Mei reports pain (痛) in her arm after the push."
    verify_projection(output, "application", contract)
    for name, key in [("assessment-inspection.json", "assessmentInspection"), ("original-excerpt.json", "originalSourceExcerpt")]:
        definition(contract, key, json.loads((output / name).read_bytes()))
    comparison = json.loads((output / "narrative.comparison.json").read_bytes())
    assert not comparison["projectedConclusionChanged"] and not comparison["projectedChangedObservations"]
    assert any(r["assessmentChange"]["changeReferencedMaterial"] for r in comparison["projectedAssessmentChanges"])
    assert any(d["diagnosticCode"] == "PSTALE" for d in json.loads((output / "stale-diagnostics.json").read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--review-dir", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    review = args.review_dir.resolve()
    assert not review.is_relative_to(ROOT), "the integration project must be outside the checkout"
    project = review / "quickstart"
    project.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(command, cwd, log_name):
        print("running:", " ".join(map(str, command)), "in", cwd, flush=True)
        result = subprocess.run(list(map(str, command)), cwd=cwd, capture_output=True, timeout=600, check=False)
        (review / log_name).write_bytes(result.stdout + result.stderr)
        commands.append({"command": list(map(str, command)), "cwd": str(cwd), "returncode": result.returncode, "log": log_name})
        (review / "executed-commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        assert result.returncode == 0, (review / log_name).read_text()[-12000:]
        return result

    with tempfile.TemporaryDirectory(prefix="yuho-quickstart-input-") as folder:
        temporary = Path(folder)
        run([executable, "--model", "hurt", "--artifacts", temporary / "hurt"], temporary, "hurt-consumer.log")
        (project / "input").mkdir(exist_ok=True)
        shutil.copyfile(temporary / "hurt/data/hurt-01_intention_no_exception.document.json", project / "input/hurt.document.json")
        # Keep representative outputs from BOTH existing validated-anchor consumers.
        run([executable, "--artifacts", temporary / "cheating"], temporary, "cheating-consumer.log")
        for model, stem, folder in [("hurt", "hurt-05-application", temporary / "hurt"),
                                    ("cheating", "application-selected", temporary / "cheating")]:
            target = review / "integration" / model
            target.mkdir(parents=True, exist_ok=True)
            for suffix in [".svg", ".projection.json", ".view-bindings.json", ".view.json", ".view.xml"]:
                origin = folder / (stem + suffix)
                if not origin.exists():
                    origin = folder / "data" / (stem + suffix)
                shutil.copyfile(origin, target / (stem + suffix))
    run([executable, "--anchors-demo", "--artifacts", review / "anchors"], project, "anchor-consumer.log")
    for name in ["Main.hs", "yuho-sdk-quickstart.cabal"]:
        shutil.copyfile(ROOT / "examples/authoring-quickstart" / name, project / name)
    shutil.copyfile(ROOT / "cabal.project.freeze", project / "cabal.project.freeze")
    (project / "cabal.project").write_text(
        f'packages: .\n          "{ROOT}"\nwith-compiler: ghc-9.8.4\nindex-state: 2026-09-12T03:17:42Z\njobs: 1\n')
    run(["cabal", "v2-build", "exe:yuho-sdk-quickstart", "--offline", "-j1", "--with-compiler=ghc-9.8.4"], project, "quickstart-build.log")
    located = run(["cabal", "list-bin", "exe:yuho-sdk-quickstart", "--offline", "--with-compiler=ghc-9.8.4"], project, "quickstart-list-bin.log")
    binary = Path(located.stdout.decode().strip())
    run([binary, project / "input/hurt.document.json", project / "output"], project, "quickstart-run.log")
    verify_outputs(review)
    assert (project / "cabal.project.freeze").read_bytes() == (ROOT / "cabal.project.freeze").read_bytes()
    (review / "INDEX.md").write_text(
        "# Tranche 06: validated anchors and external SDK quickstart\n\n"
        "- anchors/INDEX.md: 14 literal coordinate cases, 14 invalid requests and source-revision behaviour.\n"
        "- quickstart/: copied public-only consumer source/config, unchanged dependency freeze and explicit input JSON.\n"
        "- quickstart/output/: saved/reloaded authored documents, reports, complete projection, focused SVG/XML/JSON and view bindings.\n"
        "- integration/cheating/ and integration/hurt/: regenerated existing views and complete supporting data with unchanged stored anchors.\n"
        "- executed-commands.json: actual external working directories, build/run commands, exit codes and associated logs.\n"
        "- quickstart-build.log and quickstart-run.log: separate-project compilation and lifecycle results.\n\n"
        "No renderer or public serialization contract changes. SVGs can be previewed using rsvg-convert.\n")
    print("quickstart: separate offline Cabal build/run, pinned freeze, public imports, lifecycle/schema/export checks and source-anchor examples passed", flush=True)


if __name__ == "__main__":
    main()
