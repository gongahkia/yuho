"""Execute the public interaction driver outside the checkout and audit its outputs."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/authoring-consumer/fixtures/section441.document.json"
VIEWS = ["s441-focus", "s441-source", "s441-alternatives", "s441-revised", "s441-P-E-law",
         "hurt-focus", "hurt-skipped-guard"]


def verify(directory):
    data = directory / "data"
    load = lambda name: json.loads((data / name).read_bytes())
    contract = json.loads((ROOT / "schema/analysis-projection-v0.1-experimental.schema.json").read_bytes())
    authored = json.loads((ROOT / "schema/authoring-v0.1-experimental.schema.json").read_bytes())
    for schema in [contract, authored]:
        Draft202012Validator.check_schema(schema)

    def definition(name, value):
        Draft202012Validator({"$defs": contract["$defs"], "$ref": "#/$defs/" + name},
                             format_checker=FormatChecker()).validate(value)

    for path in data.glob("*.projection.json"):
        Draft202012Validator(contract, format_checker=FormatChecker()).validate(json.loads(path.read_bytes()))
    for path in data.glob("*.document.json"):
        Draft202012Validator(authored, format_checker=FormatChecker()).validate(json.loads(path.read_bytes()))
    for path in data.glob("*.application-report.json"):
        definition("application", json.loads(path.read_bytes()))
    for path in data.glob("*.comparison.json"):
        definition("comparison", json.loads(path.read_bytes()))

    ns = {"s": "http://www.w3.org/2000/svg", "g": "urn:yuho:semantic-graph:v0.1"}
    for name in VIEWS:
        p = load(name + ".projection.json")
        view = load(name + ".view-bindings.json")
        definition("view", view)
        assert view["viewProjectionId"] == p["projectionId"]
        nodes = {n["projectedNodeId"]: n for n in p["projectionNodes"]}
        edges = {e["projectedEdgeId"]: e for e in p["projectionEdges"]}
        assert len(nodes) == len(p["projectionNodes"]) and len(edges) == len(p["projectionEdges"])
        for category, all_ids in [("Nodes", nodes), ("Edges", edges)]:
            included, omitted = view["viewIncluded" + category], view["viewOmitted" + category]
            assert set(included).isdisjoint(omitted)
            assert len(included) + len(omitted) == len(all_ids) and set(included + omitted) == set(all_ids)
        assert all(e["projectedEdgeFrom"] in nodes and e["projectedEdgeTo"] in nodes for e in edges.values())
        assert all(edges[e]["projectedEdgeFrom"] in view["viewIncludedNodes"] and
                   edges[e]["projectedEdgeTo"] in view["viewIncludedNodes"] for e in view["viewIncludedEdges"])
        definition("legacyView", load(name + ".view.json"))
        svg = ET.parse(directory / (name + ".svg")).getroot()
        xml = ET.parse(data / (name + ".view.xml")).getroot()
        assert xml.tag == "{urn:yuho:semantic-graph:v0.1}semantic-graph"
        ids = [n.attrib["id"] for n in svg.iter() if "id" in n.attrib]
        assert len(ids) == len(set(ids))
        group = "occurrences" if name == "s441-P-E-law" else "objects"
        cards = svg.findall(f"s:g[@id='{group}']/s:g", ns)
        assert [c.attrib["data-projection-node"] for c in cards] == view["viewIncludedNodes"]
        assert {c.attrib["id"] for c in cards} == {b["viewBindingRenderedId"] for b in view["viewNodeBindings"]}
        connections = svg.findall("s:g[@id='connections']//s:path", ns)
        assert {c.attrib["id"] for c in connections} == {b["edgeBindingRenderedId"] for b in view["viewEdgeBindings"]}
        assert len(xml.findall("g:edges/g:edge", ns)) == len(connections) == len(view["viewIncludedEdges"])
        assert json.loads(svg.find("s:metadata[@id='projection-view']", ns).text) == view
        if name != "s441-P-E-law":
            assert nodes[cards[0].attrib["data-projection-node"]]["projectedNodeKind"] == "occurrence"
            assert nodes[cards[1].attrib["data-projection-node"]]["projectedNodeRole"] == "assessment"
        source_nodes = [nodes[key] for key in view["viewIncludedNodes"] if nodes[key]["projectedNodeRole"] == "original_source"]
        assert len(source_nodes) == (1 if name == "s441-source" else 0)
        if name == "s441-alternatives":
            included_edges = [edges[key] for key in view["viewIncludedEdges"]]
            assert len([e for e in included_edges if e["projectedEdgeKind"] == "assessment_input"]) == 3
            assert len([e for e in included_edges if e["projectedEdgeKind"] == "selected_assessment"]) == 1
        for card in cards:
            node = nodes[card.attrib["data-projection-node"]]
            text = " ".join(t.text or "" for t in card.findall("s:text", ns))
            if node["projectedNodeRole"] == "assessment":
                assert ("SELECTED for this analysis" if node["projectedNodeSelected"] else "UNSELECTED alternative") in text
            if node["projectedNodeRole"] in ["assertion", "original_source"]:
                assert node["projectedNodeComputed"] is None and node["projectedNodeEvaluation"] == "not_applicable"
        if name == "hurt-skipped-guard":
            text = " ".join(svg.itertext())
            assert "No computed result" in text and "Not evaluated" in text and "Main branch: requirements unresolved" in text
        for binding in view["viewEdgeBindings"]:
            edge = edges[binding["edgeBindingProjectedId"]]
            legacy = load(name + ".view.json")["edges"][binding["edgeBindingIndex"]]
            assert (legacy["from"], legacy["to"], legacy["kind"]) == (
                edge["projectedEdgeFrom"], edge["projectedEdgeTo"], edge["projectedEdgeKind"])
        if name in ["s441-revised", "s441-P-E-law"]:
            highlights = load(name + ".highlights.json")
            assert len(highlights) == 20
            changed = [h for h in highlights if h["computedChanged"] and h["includedInView"]]
            assert len(changed) == (4 if name == "s441-P-E-law" else 1)
            styles = " ".join(n.text or "" for n in svg.findall("s:style", ns))
            assert all("#node-" + h["alignment"] + " > rect" in styles for h in changed)

    for model, original_selection, revised_selection, assertion_count in [
            ("s441", "position:P", "position:E", 2),
            ("hurt", "assessment:hurt:hurt-caused-by-act:unresolved-not-determined", "assessment:hurt:hurt-caused-by-act:proved", 3)]:
        interaction = load(model + ".interaction.json")
        before, after = interaction["before"], interaction["after"]
        definition("comparison", interaction["alignedComparison"])
        definition("originalSourceExcerpt", interaction["revealedSource"])
        assert len(interaction["steps"]) == 9
        assert before["explanationSnapshot"] != after["explanationSnapshot"]
        assert before["explanationOccurrence"]["projectedNodeId"] == after["explanationOccurrence"]["projectedNodeId"]
        selected = before["explanationSelected"]
        assert selected["contextAssessment"]["assessmentId"] == original_selection
        assert selected["contextSelected"] and len(selected["contextAssertions"]) == assertion_count
        assert after["explanationSelected"]["contextAssessment"]["assessmentId"] == revised_selection
        assert all(not a["contextSelected"] for a in before["explanationAlternatives"])
        assert all(app["applicationComputed"] is None and app["applicationObservation"] is None
                   for a in before["explanationAlternatives"] for app in a["contextApplications"])
        assert interaction["revision"]["validation"]["analysisReady"]
        assert any(d["diagnosticCode"] == "PSTALE" for d in interaction["staleAttachment"])
        for key in ["sourceView", "alternativesView", "focusView"]:
            assert interaction[key]["viewProjectionId"] == before["explanationProjection"]
        old_p = load(model + "-before.projection.json")
        new_p = load(model + "-after.projection.json")
        assert old_p["projectionSnapshot"]["snapshotId"] == before["explanationSnapshot"]
        assert new_p["projectionSnapshot"]["snapshotId"] == after["explanationSnapshot"]
        assert old_p["projectionSnapshot"]["snapshotDocument"]["documentAssessments"] == new_p["projectionSnapshot"]["snapshotDocument"]["documentAssessments"]
        old_nodes = {n["projectedNodeId"] for n in old_p["projectionNodes"]}
        new_nodes = {n["projectedNodeId"] for n in new_p["projectionNodes"]}
        for row in interaction["alignedComparison"]["projectedChangedObservations"] + interaction["alignedComparison"]["projectedUnchangedObservations"]:
            assert row["observationChangeOldNode"] in old_nodes and row["observationChangeNewNode"] in new_nodes
            assert row["observationChangeAlignment"] in old_nodes & new_nodes
        text = interaction["revealedSource"]["excerptText"]
        assert text == ("At 10:15 I asked Jun to leave." if model == "s441" else "Mei reports pain (痛) in her arm after the push.")

    assert (data / "s441-before.document.json").read_bytes() == FIXTURE.read_bytes()
    assert len(load("s441.comparison.json")["projectedChangedObservations"]) == 4
    assert len(load("s441.comparison.json")["projectedUnchangedObservations"]) == 16
    guard = load("hurt-skipped-guard.explanation.json")
    assert guard["explanationSelected"]["contextAssessment"]["assessmentClassification"] == {"kind": "not_proved"}
    assert guard["explanationOccurrence"]["projectedNodeComputed"] is None
    assert guard["explanationOccurrence"]["projectedNodeEvaluation"] == "not_evaluated"
    routes = load("hurt-routes.comparison.json")
    assert not routes["projectedConclusionChanged"] and routes["projectedNewConclusion"] == "satisfied"
    assert len(routes["projectedAssessmentChanges"]) == 2
    assert len(routes["projectedChangedObservations"]) == 2 and len(routes["projectedUnchangedObservations"]) == 21
    summary = json.loads((directory / "summary.json").read_bytes())
    assert [(r["entry"], r["remaining"], r["conclusion"]) for r in summary["section441"]] == [
        ("not_satisfied", "unresolved", "unresolved"), ("not_satisfied", "satisfied", "satisfied"),
        ("not_satisfied", "not_satisfied", "not_satisfied")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--existing-artifacts", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="yuho-interaction-") as temporary:
        out = Path(temporary)
        completed = subprocess.run([str(args.executable.resolve()), "--interact", str(FIXTURE), str(out)],
                                   cwd=out, capture_output=True, check=False, timeout=60)
        assert completed.returncode == 0, completed.stderr.decode()
        assert not completed.stderr and len(completed.stdout.splitlines()) == 1
        verify(out)
    if args.existing_artifacts:
        verify(args.existing_artifacts)
    print("interaction consumer: two public-model workflows, seven views, schemas/bindings, source recovery, immutable revisions and mapped comparisons passed")


if __name__ == "__main__":
    main()
