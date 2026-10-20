"""Second-model public consumer: outside-checkout execution and export contracts."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    "01_intention_no_exception": ("satisfied", "satisfied", "not_satisfied"),
    "02_knowledge_no_exception": ("satisfied", "satisfied", "not_satisfied"),
    "03_hurt_not_proved": ("not_satisfied", "requirements_not_satisfied", None),
    "05_offence_causation_unresolved": ("unresolved", "requirements_unresolved", None),
    "06_nature_route": ("not_satisfied", "defeated", "satisfied"),
    "11_section84_unresolved": ("unresolved", "exception_unresolved", "unresolved"),
}


def verify(directory):
    data = directory / "data"

    def load(name):
        return json.loads((data / name).read_bytes())

    def schema(name):
        value = json.loads((ROOT / "schema" / name).read_bytes())
        Draft202012Validator.check_schema(value)
        return value

    contract = schema("analysis-projection-v0.1-experimental.schema.json")
    validator = Draft202012Validator(contract, format_checker=FormatChecker())

    def definition(name, value):
        Draft202012Validator({"$defs": contract["$defs"], "$ref": "#/$defs/" + name},
                             format_checker=FormatChecker()).validate(value)

    for suffix, name in [("document", "authoring-v0.1-experimental.schema.json"),
                         ("request", "request.schema.json"), ("result", "result.schema.json")]:
        check = Draft202012Validator(schema(name), format_checker=FormatChecker())
        for path in sorted(data.glob("*." + suffix + ".json")):
            check.validate(json.loads(path.read_bytes()))

    for path in sorted(data.glob("*.application.json")):
        definition("application", json.loads(path.read_bytes()))
    for path in sorted(data.glob("*.comparison.json")):
        definition("comparison", json.loads(path.read_bytes()))
    for path in sorted(data.glob("*inspection.json")):
        definition("assessmentInspection", json.loads(path.read_bytes()))
    for name in ["hurt-original-excerpt.json", "hurt-locator-only.json"]:
        definition("originalSourceExcerpt", load(name))

    ns = {"s": "http://www.w3.org/2000/svg", "g": "urn:yuho:semantic-graph:v0.1"}
    projections = {}
    for path in sorted(data.glob("*.projection.json")):
        name = path.name.removesuffix(".projection.json")
        projection = json.loads(path.read_bytes())
        projections[name] = projection
        validator.validate(projection)
        nodes = {n["projectedNodeId"]: n for n in projection["projectionNodes"]}
        edges = {e["projectedEdgeId"]: e for e in projection["projectionEdges"]}
        assert len(nodes) == len(projection["projectionNodes"])
        assert len(edges) == len(projection["projectionEdges"])
        assert all(e["projectedEdgeFrom"] in nodes and e["projectedEdgeTo"] in nodes for e in edges.values())
        view = load(name + ".view-bindings.json")
        definition("view", view)
        assert view["viewProjectionId"] == projection["projectionId"]
        for category, all_ids in [("Nodes", nodes), ("Edges", edges)]:
            included, omitted = view["viewIncluded" + category], view["viewOmitted" + category]
            assert set(included).isdisjoint(omitted)
            assert len(included) + len(omitted) == len(all_ids)
            assert set(included + omitted) == set(all_ids)
        assert all(edges[e]["projectedEdgeFrom"] in view["viewIncludedNodes"] and
                   edges[e]["projectedEdgeTo"] in view["viewIncludedNodes"] for e in view["viewIncludedEdges"])
        legacy = load(name + ".view.json")
        definition("legacyView", legacy)
        xml = ET.parse(data / (name + ".view.xml")).getroot()
        svg = ET.parse(directory / (name + ".svg")).getroot()
        assert xml.tag == "{urn:yuho:semantic-graph:v0.1}semantic-graph"
        assert svg.tag == "{http://www.w3.org/2000/svg}svg"
        dom = [x.attrib["id"] for x in svg.iter() if "id" in x.attrib]
        assert len(dom) == len(set(dom))
        group = "occurrences" if name.removeprefix("hurt-") in SCENARIOS else "objects"
        cards = svg.findall(f"s:g[@id='{group}']/s:g", ns)
        connections = svg.findall("s:g[@id='connections']//s:path", ns)
        assert {x.attrib["id"] for x in cards} == {b["viewBindingRenderedId"] for b in view["viewNodeBindings"]}
        assert {x.attrib["id"] for x in connections} == {b["edgeBindingRenderedId"] for b in view["viewEdgeBindings"]}
        assert {n["id"] for n in legacy["nodes"]} == set(view["viewIncludedNodes"])
        assert {n.attrib["id"] for n in xml.findall("g:nodes/g:node", ns)} == set(view["viewIncludedNodes"])
        xml_edges = xml.findall("g:edges/g:edge", ns)
        assert len(legacy["edges"]) == len(xml_edges) == len(connections) == len(view["viewIncludedEdges"])
        for binding in view["viewEdgeBindings"]:
            rich = edges[binding["edgeBindingProjectedId"]]
            row = legacy["edges"][binding["edgeBindingIndex"]]
            assert (row["from"], row["to"], row["kind"]) == (
                rich["projectedEdgeFrom"], rich["projectedEdgeTo"], rich["projectedEdgeKind"])
        for card in cards:
            rich = nodes[card.attrib["data-projection-node"]]
            text = " ".join(t.text or "" for t in card.findall("s:text", ns))
            if rich["projectedNodeRole"] in ["assertion", "original_source"]:
                assert rich["projectedNodeComputed"] is None and rich["projectedNodeEvaluation"] == "not_applicable"
            if rich["projectedNodeRole"] == "assessment":
                assert ("SELECTED for this analysis" if rich["projectedNodeSelected"] else "UNSELECTED alternative") in text
            if rich["projectedNodeKind"] == "occurrence":
                if rich["projectedNodeEvaluation"] == "not_evaluated":
                    assert "No computed result" in text and "Not evaluated" in text and "requirements" in text
        if projection["projectionCompiler"]:
            compiler = projection["projectionCompiler"]
            generated = {s["generatedSourceId"] for s in compiler["projectionGeneratedSources"]}
            original = {s["sourceId"] for s in projection["projectionSnapshot"]["snapshotDocument"]["documentSources"]}
            assert generated.isdisjoint(original)
            assert all(s["sourceMappingSource"] in generated for s in compiler["projectionGeneratedSpans"])
            assert all(r["referenceSource"] in original for s in compiler["projectionGeneratedSpans"]
                       for r in s["sourceMappingOriginals"])

    for name, (conclusion, reason, guard) in SCENARIOS.items():
        application = load("hurt-" + name + ".application.json")
        receipt = load("hurt-" + name + ".acknowledgements.json")
        assert receipt["checkedSnapshot"] == application["reportSnapshot"]
        assert receipt["checkedAnalysis"] == "analysis:hurt"
        assert receipt["checkedPolicy"]["requiredAssumptions"] == receipt["checkedAcknowledgements"]["acknowledgedAssumptions"]
        assert len(receipt["checkedPolicy"]["requiredAssumptions"]) == 3
        assert application["reportConclusion"] == conclusion
        main = next(r for r in application["reportRules"] if r["ruleAuthoredId"] == "o:voluntary-hurt")
        assert main["ruleBranchReason"] == reason
        exception, = application["reportExceptions"]
        assert exception["exceptionComputed"] == guard
        assert exception["exceptionEvaluation"] == ("not_evaluated" if guard is None else "evaluated")
        assert len(application["reportRequirements"]) == 20
        document = load("hurt-" + name + ".document.json")
        assert len([a for a in document["documentAnnotations"] if a["annotationId"].startswith("a:")]) == 3

    draft = projections["hurt-case-before"]
    assert draft["projectionMode"] == "authored" and draft["projectionApplication"] is None
    assert all(n["projectedNodeComputed"] is None for n in draft["projectionNodes"])
    assert len(draft["projectionOpenInputs"]) == 13
    assert all(d["diagnosticCode"] == "AMISSING" for d in load("hurt-case-before.compile-diagnostics.json"))
    links = load("hurt-case-before.assertion-links.json")
    assert next(x for x in links if x["linkedAssertion"] == "assertion:weather")["linkedAssessments"] == []
    assert all(x["linkedSelectedAssessments"] == [] for x in links)

    # Two questions over one existing run: selected explanation vs input alternatives.
    selected_name, input_name = "hurt-05-selected-application", "hurt-05-application"
    selected_projection = projections[selected_name]
    assert selected_projection == projections[input_name] == projections["hurt-05_offence_causation_unresolved"]
    application = load("hurt-05_offence_causation_unresolved.application.json")
    observation, = [r for r in application["reportRequirements"] if r["observationNode"] == "f:hurt-caused-by-act"]
    selected_id = observation["observationAssessment"]["assessmentId"]
    nodes = {n["projectedNodeId"]: n for n in selected_projection["projectionNodes"]}
    views = [load(name + ".view-bindings.json") for name in [selected_name, input_name]]
    selected_nodes, input_nodes = [[nodes[key] for key in v["viewIncludedNodes"]] for v in views]
    selected_assessments = [n for n in selected_nodes if n["projectedNodeRole"] == "assessment"]
    assessment, = selected_assessments
    assert assessment["projectedNodeSelected"]
    assert assessment["projectedNodeOrigin"]["originAuthoredObjects"] == [selected_id]
    assert assessment["projectedNodeBinding"]["bindingSupplied"] == {"kind": "unresolved", "reason": "not_determined"}
    alternatives = [n for n in input_nodes if n["projectedNodeRole"] == "assessment" and not n["projectedNodeSelected"]]
    assert len(alternatives) == 2
    assert all(n["projectedNodeId"] in views[0]["viewOmittedNodes"] for n in alternatives)
    assert all(n["projectedNodeComputed"] is None and n["projectedNodeObservation"] is None for n in alternatives)
    for kind in ["occurrence", "observation"]:
        one, = [n for n in selected_nodes if n["projectedNodeKind"] == kind]
        other, = [n for n in input_nodes if n["projectedNodeKind"] == kind]
        assert one == other  # definition, occurrence and observation are never merged
        assert one["projectedNodeId"] != assessment["projectedNodeId"]
        assert one["projectedNodeComputed"] == "unresolved" and one["projectedNodeEvaluation"] == "evaluated"
    for role, count in [("assertion", 3), ("original_source", 3), ("input", 1)]:
        before = {n["projectedNodeId"] for n in selected_nodes if n["projectedNodeRole"] == role and n["projectedNodeKind"] == "authored"}
        after = {n["projectedNodeId"] for n in input_nodes if n["projectedNodeRole"] == role and n["projectedNodeKind"] == "authored"}
        assert before == after and len(before) == count

    detail = load("hurt-05.assessment-inspection.json")
    assert detail["inspectionSelected"] and detail["inspectionAssessment"]["assessmentClassification"] == {
        "kind": "unresolved", "reason": "not_determined"}
    assert len(detail["inspectionResolution"]["resolvedAssertions"]) == 3
    assert any(a["assertionScope"]["scopeActor"] == "actor:mei" for a in detail["inspectionResolution"]["resolvedAssertions"])
    alternative = load("hurt-05.alternative-inspection.json")
    assert not alternative["inspectionSelected"] and alternative["inspectionAssessment"]["assessmentClassification"] == {"kind": "proved"}
    assert all(a["applicationObservation"] is None and a["applicationComputed"] is None for a in alternative["inspectionApplications"])
    skipped = load("hurt-05.skipped-inspection.json")
    assert skipped["inspectionSelected"] and skipped["inspectionAssessment"]["assessmentClassification"] == {"kind": "not_proved"}
    assert all(a["applicationEvaluation"] == "not_evaluated" and a["applicationComputed"] is None
               and a["applicationSkipReason"].endswith("requirements_unresolved") for a in skipped["inspectionApplications"])
    assumption = load("hurt-11.assumption-inspection.json")["inspectionAssessment"]
    assert assumption["assessmentBasis"] == "assumption" and assumption["assessmentAssertions"] == []
    assert load("hurt-original-excerpt.json")["excerptText"] == "Mei reports pain (痛) in her arm after the push."
    assert load("hurt-locator-only.json")["excerptText"] is None
    assert load("hurt-locator-only.json")["excerptState"] == "locator_only"
    routes = load("hurt-01-vs-02.comparison.json")
    uncertainties = load("hurt-05-vs-11.comparison.json")
    assert not routes["projectedConclusionChanged"] and len(routes["projectedAssessmentChanges"]) == 2
    assert len(routes["projectedChangedObservations"]) == 2 and len(routes["projectedUnchangedObservations"]) == 21
    assert not uncertainties["projectedConclusionChanged"] and len(uncertainties["projectedAssessmentChanges"]) == 4
    assert len(uncertainties["projectedChangedObservations"]) == 18 and len(uncertainties["projectedUnchangedObservations"]) == 5
    old_nodes = {n["projectedNodeId"] for n in projections["hurt-05_offence_causation_unresolved"]["projectionNodes"]}
    new_nodes = {n["projectedNodeId"] for n in projections["hurt-11_section84_unresolved"]["projectionNodes"]}
    for row in uncertainties["projectedChangedObservations"] + uncertainties["projectedUnchangedObservations"]:
        assert row["observationChangeOldNode"] in old_nodes and row["observationChangeNewNode"] in new_nodes
        if row["observationChange"]["changeObservationKind"] != "exception":
            assert row["observationChangeAlignment"] in old_nodes & new_nodes
    narrative = load("hurt-revision.comparison.json")
    assert not narrative["projectedChangedObservations"] and not narrative["projectedConclusionChanged"]
    assert any(c["assessmentChange"]["changeReferencedMaterial"] for c in narrative["projectedAssessmentChanges"])
    assert not any(c["assessmentChange"]["changeClassification"] for c in narrative["projectedAssessmentChanges"])
    assert any(d["diagnosticCode"] == "PSTALE" for d in load("hurt-stale-diagnostics.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--existing-artifacts", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="yuho-hurt-consumer-") as folder:
        directory = Path(folder)
        completed = subprocess.run([str(args.executable.resolve()), "--model", "hurt", "--artifacts", str(directory)],
                                   cwd=directory, capture_output=True, check=False, timeout=60)
        assert completed.returncode == 0, completed.stderr.decode()
        assert not completed.stderr, completed.stderr
        assert len(completed.stdout.splitlines()) == 3
        verify(directory)
    if args.existing_artifacts:
        verify(args.existing_artifacts)
    print("hurt consumer: outside-checkout execution, six scenarios, schemas, all ten JSON/XML/SVG views, both causation focuses, comparisons and recovery passed")


if __name__ == "__main__":
    main()
