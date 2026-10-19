"""Exercise public editing and caller admission, with native schema/export checks."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def verify(directory):
    data = directory / "data"

    def load(name):
        return json.loads((data / name).read_bytes())

    def schema(name):
        value = json.loads((ROOT / "schema" / name).read_bytes())
        Draft202012Validator.check_schema(value)
        return value

    contract = schema("analysis-projection-v0.1-experimental.schema.json")

    def definition(name, value):
        Draft202012Validator({"$defs": contract["$defs"], "$ref": "#/$defs/" + name},
                             format_checker=FormatChecker()).validate(value)

    for suffix, name in [("document", "authoring-v0.1-experimental.schema.json"),
                         ("request", "request.schema.json"), ("result", "result.schema.json")]:
        validator = Draft202012Validator(schema(name), format_checker=FormatChecker())
        paths = list(data.glob("*." + suffix + ".json"))
        assert paths
        for path in paths:
            validator.validate(json.loads(path.read_bytes()))
    for suffix, name in [("application", "application"), ("comparison", "comparison"), ("inspection", "assessmentInspection")]:
        for path in data.glob("*." + suffix + ".json"):
            definition(name, json.loads(path.read_bytes()))

    projections = {}
    ns = {"s": "http://www.w3.org/2000/svg", "g": "urn:yuho:semantic-graph:v0.1"}
    for path in sorted(data.glob("*.projection.json")):
        stem = path.name.removesuffix(".projection.json")
        projection = json.loads(path.read_bytes())
        projections[stem] = projection
        Draft202012Validator(contract, format_checker=FormatChecker()).validate(projection)
        view = load(stem + ".view-bindings.json")
        definition("view", view)
        assert view["viewProjectionId"] == projection["projectionId"]
        nodes = {n["projectedNodeId"]: n for n in projection["projectionNodes"]}
        edges = {e["projectedEdgeId"]: e for e in projection["projectionEdges"]}
        assert len(nodes) == len(projection["projectionNodes"]) and len(edges) == len(projection["projectionEdges"])
        assert all(e["projectedEdgeFrom"] in nodes and e["projectedEdgeTo"] in nodes for e in edges.values())
        for kind, all_ids in [("Nodes", nodes), ("Edges", edges)]:
            included, omitted = view["viewIncluded" + kind], view["viewOmitted" + kind]
            assert set(included).isdisjoint(omitted) and set(included + omitted) == set(all_ids)
        assert all(edges[e]["projectedEdgeFrom"] in view["viewIncludedNodes"] and
                   edges[e]["projectedEdgeTo"] in view["viewIncludedNodes"] for e in view["viewIncludedEdges"])
        svg = ET.parse(directory / (stem + ".svg")).getroot()
        xml = ET.parse(data / (stem + ".view.xml")).getroot()
        legacy = load(stem + ".view.json")
        definition("legacyView", legacy)
        law = stem in ["hurt-baseline", "hurt-label-revision", "hurt-SDK-EXPERIMENT-all"]
        assert legacy["view"] == ("rule" if law else "case")
        assert svg.tag == "{http://www.w3.org/2000/svg}svg" and xml.tag == "{urn:yuho:semantic-graph:v0.1}semantic-graph"
        group = "occurrences" if law else "objects"
        cards = svg.findall(f"s:g[@id='{group}']/s:g", ns)
        paths = svg.findall("s:g[@id='connections']//s:path", ns)
        ids = [x.attrib["id"] for x in svg.iter() if "id" in x.attrib]
        assert len(ids) == len(set(ids))
        assert {c.attrib["id"] for c in cards} == {b["viewBindingRenderedId"] for b in view["viewNodeBindings"]}
        assert {e.attrib["id"] for e in paths} == {b["edgeBindingRenderedId"] for b in view["viewEdgeBindings"]}
        assert len(paths) == len(legacy["edges"]) == len(view["viewIncludedEdges"]) == len(xml.findall("g:edges/g:edge", ns))
        assert {n["id"] for n in legacy["nodes"]} == set(view["viewIncludedNodes"])
        for binding in view["viewEdgeBindings"]:
            edge = edges[binding["edgeBindingProjectedId"]]
            row = legacy["edges"][binding["edgeBindingIndex"]]
            assert (row["from"], row["to"], row["kind"]) == (edge["projectedEdgeFrom"], edge["projectedEdgeTo"], edge["projectedEdgeKind"])
        visible = {c.attrib["data-projection-node"]: " ".join(x.text or "" for x in c.findall("s:text", ns)) for c in cards}
        for key, text in visible.items():
            node = nodes[key]
            if node["projectedNodeRole"] == "assessment":
                assert ("SELECTED for this analysis" if node["projectedNodeSelected"] else "UNSELECTED alternative") in text
            if node["projectedNodeKind"] == "occurrence" and node["projectedNodeEvaluation"] == "not_evaluated":
                assert "No computed result" in text and "Not evaluated" in text
        if stem == "hurt-SDK-EXPERIMENT-all":
            assert any("SDK EXPERIMENT" in s for s in visible.values())
            assert any("All required (ALL)" in s and "intention AND knowledge" in s for s in visible.values())
        if projection["projectionMode"] == "authored":
            assert projection["projectionApplication"] is None and all(n["projectedNodeComputed"] is None for n in nodes.values())
    assert len(projections) == 6

    baseline = load("hurt-baseline.document.json")
    labelled = load("hurt-label-revision.document.json")
    experiment = load("hurt-SDK-EXPERIMENT-all.document.json")
    assert load("hurt-repaired.document.json") == experiment
    assert [n["nodeId"] for n in baseline["documentLaw"]["lawNodes"]] == [n["nodeId"] for n in labelled["documentLaw"]["lawNodes"]]
    assert experiment["documentLaw"]["lawRevision"] == "sdk-experiment-any-to-all-v1"
    assert next(n for n in experiment["documentLaw"]["lawNodes"] if n["nodeId"] == "g:section321-fault")["nodeKind"] == "all"
    for doc in [labelled, experiment, load("hurt-invalid.document.json")]:
        for key in ["documentSources", "documentAssertions", "documentAssessments", "documentAnalyses", "documentAnnotations", "documentRelationships", "documentPresentation"]:
            assert doc[key] == baseline[key], key
    trace = {row["stage"]: row for row in load("editing-session.json")}
    assert trace["baseline"]["conclusion"] == trace["label_revision"]["conclusion"] == "satisfied"
    assert trace["baseline"]["snapshot"] != trace["label_revision"]["snapshot"]
    assert trace["SDK_EXPERIMENT_any_to_all"]["conclusion"] == "not_satisfied"
    assert trace["SDK_EXPERIMENT_any_to_all"]["faultComputed"] == "not_satisfied"
    assert trace["SDK_EXPERIMENT_any_to_all"]["guardEvaluation"] == "not_evaluated"
    assert trace["invalid_disconnected_edge"]["snapshot"] is None and trace["invalid_disconnected_edge"]["conclusion"] is None
    assert not (data / "hurt-invalid.application.json").exists()
    assert not (data / "hurt-invalid.projection.json").exists()
    assert any(d["diagnosticCode"] == "AREFERENCE" and "edge:g:section321-fault/f:knowledge-hurt-likely" in d["diagnosticObjects"]
               for d in load("hurt-invalid.compile-diagnostics.json"))
    assert load("hurt-repaired.result.json") == load("hurt-SDK-EXPERIMENT-all.result.json")
    for name, code in [("label-comparison-rejected.json", "AINCOMPATIBLE"), ("structural-comparison-rejected.json", "AINCOMPATIBLE"),
                       ("label-stale-rejected.json", "PSTALE"), ("narrative-stale-rejected.json", "PSTALE")]:
        assert any(d["diagnosticCode"] == code for d in load(name))
    old_occurrences = {n["projectedNodeId"] for n in projections["hurt-baseline"]["projectionNodes"] if n["projectedNodeKind"] == "occurrence"}
    label_occurrences = {n["projectedNodeId"] for n in projections["hurt-label-revision"]["projectionNodes"] if n["projectedNodeKind"] == "occurrence"}
    assert old_occurrences.isdisjoint(label_occurrences)
    narrative, added, selected = [load("hurt-" + name + ".document.json") for name in ["narrative", "alternative-added", "alternative-selected"]]
    assert narrative["documentAssertions"] != baseline["documentAssertions"]
    assert narrative["documentAssessments"] == baseline["documentAssessments"]
    assert narrative["documentAnalyses"] == added["documentAnalyses"] == baseline["documentAnalyses"]
    assert added["documentAssessments"] == selected["documentAssessments"]
    assert len(added["documentAssessments"]) == len(baseline["documentAssessments"]) + 1
    for name in ["narrative", "addition"]:
        comparison = load(name + ".comparison.json")
        assert not comparison["projectedConclusionChanged"] and not comparison["projectedChangedObservations"]
    assert any(c["assessmentChange"]["changeReferencedMaterial"] for c in load("narrative.comparison.json")["projectedAssessmentChanges"])
    change = load("selection.comparison.json")
    assert change["projectedConclusionChanged"] and len(change["projectedAssessmentChanges"]) == 1
    assert trace["alternative_explicitly_selected"]["conclusion"] == "unresolved"
    assert load("selected.inspection.json")["inspectionSelected"]
    retained = load("retained.inspection.json")
    assert not retained["inspectionSelected"] and retained["inspectionAssessment"]["assessmentClassification"] == {"kind": "proved"}
    assert all(a["applicationObservation"] is None for a in retained["inspectionApplications"])
    skipped = load("skipped.inspection.json")
    assert skipped["inspectionSelected"] and all(a["applicationEvaluation"] == "not_evaluated" and a["applicationComputed"] is None for a in skipped["inspectionApplications"])
    assert [x["openState"] for x in projections["hurt-missing-case"]["projectionOpenInputs"]] == ["missing"]

    receipt = load("ack-success.accepted.json")
    assert receipt["checkedSnapshot"] == load("ack-success.application.json")["reportSnapshot"]
    assert receipt["checkedPolicy"]["requiredAssumptions"] == receipt["checkedAcknowledgements"]["acknowledgedAssumptions"]
    for name, code in [("missing-1", "ACKMISSING"), ("missing-2", "ACKMISSING"), ("missing-3", "ACKMISSING"),
                       ("unknown", "ACKUNKNOWN"), ("duplicate", "ACKDUPLICATE"), ("wrong-policy-model", "ACKCONTEXT"),
                       ("wrong-ack-analysis", "ACKCONTEXT"), ("unknown-analysis", "ACKCONTEXT")]:
        failure = load("ack-" + name + ".rejected.json")
        assert code in [d["acknowledgementCode"] for d in failure["acknowledgementDiagnostics"]]
        assert not failure["authoringDiagnostics"]
        assert not (data / ("ack-" + name + ".application.json")).exists()
        assert not (data / ("ack-" + name + ".accepted.json")).exists()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--existing-artifacts", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="yuho-editing-consumer-") as folder:
        directory = Path(folder)
        completed = subprocess.run([str(args.executable.resolve()), "--edit-demo", "--artifacts", str(directory)],
                                   cwd=directory, capture_output=True, timeout=60, check=False)
        assert completed.returncode == 0 and not completed.stderr, completed.stderr.decode()
        assert len(completed.stdout.splitlines()) == 1
        verify(directory)
    if args.existing_artifacts:
        verify(args.existing_artifacts)
    print("editing consumer: outside-checkout editing/repair/selection, admission rejections, schemas and six JSON/XML/SVG exports passed")


if __name__ == "__main__":
    main()
