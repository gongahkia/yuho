"""Run the separately packaged SDK consumer outside the checkout and check schemas."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

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
        verify_projections(directory)
    print("independent authoring consumer: outside-checkout execution, authored/kernel schemas, reports and retained context passed")


def verify_projections(directory):
    schema = json.loads((ROOT / "schema/analysis-projection-v0.1-experimental.schema.json").read_bytes())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def load(name):
        return json.loads((directory / name).read_bytes())

    def validate_definition(key, value):
        Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/" + key},
                             format_checker=FormatChecker()).validate(value)

    projections = {}
    for path in sorted(directory.glob("*.projection.json")):
        projection = json.loads(path.read_bytes())
        validator.validate(projection)
        projections[path.stem.removesuffix(".projection")] = projection
        nodes = projection["projectionNodes"]
        edges = projection["projectionEdges"]
        node_ids = {node["projectedNodeId"] for node in nodes}
        edge_ids = {edge["projectedEdgeId"] for edge in edges}
        assert len(node_ids) == len(nodes) and len(edge_ids) == len(edges)
        assert node_ids.isdisjoint(edge_ids)
        assert all(edge["projectedEdgeFrom"] in node_ids and edge["projectedEdgeTo"] in node_ids for edge in edges)
        if projection["projectionMode"] == "authored":
            assert projection["projectionApplication"] is None
            assert all(node["projectedNodeComputed"] is None for node in nodes)
        else:
            assert projection["projectionApplication"]["reportSnapshot"] == projection["projectionSnapshot"]["snapshotId"]
            compiler = projection["projectionCompiler"]
            generated = {source["generatedSourceId"] for source in compiler["projectionGeneratedSources"]}
            original = {source["sourceId"] for source in projection["projectionSnapshot"]["snapshotDocument"]["documentSources"]}
            assert all(span["sourceMappingSource"] in generated for span in compiler["projectionGeneratedSpans"])
            assert all(ref["referenceSource"] in original for span in compiler["projectionGeneratedSpans"]
                       for ref in span["sourceMappingOriginals"])

    svg_ns = {"s": "http://www.w3.org/2000/svg"}
    graph_ns = {"g": "urn:yuho:semantic-graph:v0.1"}
    new_views = ["case-before", "application-selected", "application-revised",
                 "application-pending", "application-skipped"]
    for name in ["pending-authored", "draft-authored", "satisfied", "pending", "defeated"] + new_views:
        projection = projections[name]
        view = load(name + ".view-bindings.json")
        validate_definition("view", view)
        assert view["viewProjectionId"] == projection["projectionId"]
        assert set(view["viewIncludedNodes"]).isdisjoint(view["viewOmittedNodes"])
        assert set(view["viewIncludedNodes"] + view["viewOmittedNodes"]) == {
            node["projectedNodeId"] for node in projection["projectionNodes"]}
        assert set(view["viewIncludedEdges"]).isdisjoint(view["viewOmittedEdges"])
        assert set(view["viewIncludedEdges"] + view["viewOmittedEdges"]) == {
            edge["projectedEdgeId"] for edge in projection["projectionEdges"]}
        legacy = load(name + ".view.json")
        validate_definition("legacyView", legacy)
        assert legacy["view"] == ("case" if name in new_views else "rule")
        xml = ET.parse(directory / (name + ".view.xml")).getroot()
        svg = ET.parse(directory / (name + ".svg")).getroot()
        assert xml.tag == "{urn:yuho:semantic-graph:v0.1}semantic-graph"
        assert svg.tag == "{http://www.w3.org/2000/svg}svg"
        all_svg_ids = [element.attrib["id"] for element in svg.iter() if "id" in element.attrib]
        assert len(all_svg_ids) == len(set(all_svg_ids)), "SVG identity collision"
        assert {node["id"] for node in legacy["nodes"]} == set(view["viewIncludedNodes"])
        assert {node.attrib["id"] for node in xml.findall("g:nodes/g:node", graph_ns)} == set(view["viewIncludedNodes"])
        group = "objects" if name in new_views else "occurrences"
        rendered_nodes = svg.findall(f"s:g[@id='{group}']/s:g", svg_ns)
        rendered_edges = svg.find("s:g[@id='connections']", svg_ns).findall(".//s:path", svg_ns)
        assert {node.attrib["id"] for node in rendered_nodes} == {
            binding["viewBindingRenderedId"] for binding in view["viewNodeBindings"]}
        assert {edge.attrib["id"] for edge in rendered_edges} == {
            binding["edgeBindingRenderedId"] for binding in view["viewEdgeBindings"]}
        xml_edges = xml.findall("g:edges/g:edge", graph_ns)
        assert len(legacy["edges"]) == len(xml_edges) == len(rendered_edges) == len(view["viewIncludedEdges"])
        rich_edges = {edge["projectedEdgeId"]: edge for edge in projection["projectionEdges"]}
        for binding in view["viewEdgeBindings"]:
            edge = rich_edges[binding["edgeBindingProjectedId"]]
            old = legacy["edges"][binding["edgeBindingIndex"]]
            assert (old["from"], old["to"], old["kind"]) == (
                edge["projectedEdgeFrom"], edge["projectedEdgeTo"], edge["projectedEdgeKind"])
        if name in ["pending", "pending-authored"]:
            guard = next(node for node in rendered_nodes if node.attrib["data-authored-id"] == "f:unsoundness-time")
            visible = " ".join(text.text or "" for text in guard.findall("s:text", svg_ns))
            assert "not_proved" in visible and "No computed result" in visible
            assert ("Not evaluated" if name == "pending" else "Evaluation not requested") in visible
            if name == "pending":
                assert "requirements unresolved" in visible
        if name not in new_views:
            for node in rendered_nodes:
                key = node.attrib["data-authored-id"]
                visible_text = " ".join(text.text or "" for text in node.findall("s:text", svg_ns))
                rich = next(row for row in projection["projectionNodes"]
                            if row["projectedNodeId"] == node.attrib["data-projection-node"])
                if rich["projectedNodeBinding"] and rich["projectedNodeBinding"]["bindingState"] == "selected":
                    assert "Selected assessment" in visible_text
                if rich["projectedNodeRole"] == "all":
                    assert "All required (ALL)" in visible_text
                if rich["projectedNodeRole"] == "any":
                    assert "At least one required (ANY)" in visible_text
                if key in ["f:nature-causation", "f:wrong-causation", "f:control-causation"]:
                    assert "By reason of unsoundness of mind" in visible_text
                    assert "Provision: Penal Code s 84" in visible_text
                if key == "x:section84":
                    assert "Unsoundness of mind exception" in visible_text and "Provision: Penal Code s 84" in visible_text
                if key == "f:deception":
                    assert "Provision: Penal Code s 415" in visible_text
        if name == "draft-authored":
            assert any("Missing assessment" in (text.text or "") for text in svg.findall(".//s:text", svg_ns))
        if name in new_views:
            def visible(authored_id):
                return " ".join(text.text or "" for node in rendered_nodes
                                if node.attrib["data-authored-id"] == authored_id
                                for text in node.findall("s:text", svg_ns))

            for node in projection["projectionNodes"]:
                if node["projectedNodeRole"] in ["assertion", "original_source"]:
                    assert node["projectedNodeComputed"] is None
                    assert node["projectedNodeEvaluation"] == "not_applicable"
            if name == "case-before":
                assert "No assessment link in document" in visible("assertion:weather")
                assert "actor:observer" in visible("assertion:weather")
                assert "none selected for this analysis" in visible("assertion:description")
                assert "DRAFT" in visible("annotation:case-draft")
                assert "no excerpt or precise location invented" in visible("source:registry")
                assert all(node["projectedNodeComputed"] is None for node in projection["projectionNodes"])
            if name == "application-selected":
                assert "SELECTED for this analysis" in visible("assessment:deception")
                alternative_text = visible("assessment:deception-alternative")
                assert "UNSELECTED alternative" in alternative_text and "Supplied: proved" in alternative_text
                assert "actor:buyer" in visible("assertion:message") and "context:message-exchange" in visible("assertion:message")
                assert "Anchored excerpt: 猫 item." in visible("source:case-note")
                assert "assessment:deception-other-context" not in {node.attrib["data-authored-id"] for node in rendered_nodes}
            if name == "application-pending":
                text = visible("assessment:property-fault-pending")
                assert "SELECTED" in text and "Supplied: unresolved" in text and "Unresolved reason: not_determined" in text
                assert "Authored assumption; no case assertion cited." in text
                assert "UNSELECTED" in visible("assessment:property-fraudulent-or-dishonest")
                assert not any(node["projectedNodeRole"] == "assertion" for node in projection["projectionNodes"]
                               if node["projectedNodeId"] in view["viewIncludedNodes"])
            if name == "application-skipped":
                assert "SELECTED" in visible("assessment:unsoundness-time")
                assert "Supplied: not_proved" in visible("assessment:unsoundness-time")
                text = visible("f:unsoundness-time")
                assert "Computed: No computed result" in text and "Not evaluated" in text
                assert "requirements unresolved" in text

    comparison = load("comparison-projection.json")
    validate_definition("comparison", comparison)
    excerpt = load("comparison-excerpt.json")
    assert {row["authoredId"] for row in excerpt} == {
        "f:property-fraudulent-or-dishonest", "f:unsoundness-time", "o:cheating"}
    for row in excerpt:
        mapped = next(change for change in comparison["projectedChangedObservations"]
                      if change["observationChange"]["changeObject"] == row["authoredId"])
        assert row["projectedOccurrence"] == mapped["observationChangeAlignment"]
        assert row["oldObservation"] == mapped["observationChangeOldNode"]
        assert row["newObservation"] == mapped["observationChangeNewNode"]
    changed = comparison["projectedChangedObservations"]
    assert len(comparison["projectedAssessmentChanges"]) == 1
    assert len(changed) == 20 and len(comparison["projectedUnchangedObservations"]) == 6
    assert sum(row["observationComputedValueChanged"] for row in changed) == 5
    assert sum(row["observationEvaluationChanged"] for row in changed) == 15
    assert sum(row["observationBranchReasonChanged"] for row in changed) == 2
    for row in changed + comparison["projectedUnchangedObservations"]:
        assert row["observationChangeOldIdentity"]["observationRunSnapshot"] != row["observationChangeNewIdentity"]["observationRunSnapshot"]
    for prefix, side in [("satisfied", "Old"), ("pending", "New")]:
        ids = {node["projectedNodeId"] for node in projections[prefix]["projectionNodes"]}
        for row in changed + comparison["projectedUnchangedObservations"]:
            assert row["observationChange" + side + "Node"] in ids
            assert row["observationChangeAlignment"] in ids
    alternative = load("alternative-route.comparison-projection.json")
    validate_definition("comparison", alternative)
    assert not alternative["projectedConclusionChanged"] and alternative["projectedChangedObservations"]
    for filename in ["recovered-deception.json", "recovered-law-context.json"]:
        validate_definition("resolution", load(filename))
    assert len(load("recovered-deception.json")["resolvedAssertions"]) == 2
    assert load("recovered-law-context.json")["resolvedAnnotations"][0]["annotationState"] == "draft"
    for filename in ["assessment-resolution.json", "alternative-resolution.json", "skipped-resolution.json"]:
        validate_definition("assessmentInspection", load(filename))
    selected = load("assessment-resolution.json")
    assert selected["inspectionSelected"]
    assert len(selected["inspectionResolution"]["resolvedAssertions"]) == 2
    assert any(row["assertionScope"]["scopeActor"] == "actor:buyer"
               for row in selected["inspectionResolution"]["resolvedAssertions"])
    for recovered in selected["inspectionOriginalSources"]:
        validate_definition("originalSourceExcerpt", recovered)
        if recovered["excerptState"] == "anchored":
            anchor = recovered["excerptReference"]["referenceSpan"]
            original = recovered["excerptSource"]["sourceText"].encode("utf-8")
            assert original[anchor["start"]:anchor["end"]].decode("utf-8") == recovered["excerptText"] == "猫 item."
    alternative = load("alternative-resolution.json")
    assert not alternative["inspectionSelected"]
    assert alternative["inspectionAssessment"]["assessmentClassification"] == {"kind": "proved"}
    assert all(row["applicationComputed"] is None and row["applicationObservation"] is None
               and not row["applicationSelected"] for row in alternative["inspectionApplications"])
    links = load("case-assertion-links.json")
    for row in links:
        validate_definition("assertionLinks", row)
    assert next(row for row in links if row["linkedAssertion"] == "assertion:weather")["linkedAssessments"] == []
    original = projections["application-selected"]["projectionSnapshot"]
    revised = projections["application-revised"]["projectionSnapshot"]
    assert original["snapshotId"] != revised["snapshotId"]
    assert original["snapshotDocument"]["documentAssessments"] == revised["snapshotDocument"]["documentAssessments"]
    def description(snapshot):
        return next(row["assertionDescription"] for row in snapshot["snapshotDocument"]["documentAssertions"]
                    if row["assertionId"] == "assertion:description")
    assert description(original) != description(revised)
    assert any(row["diagnosticCode"] == "PSTALE" for row in load("revision-stale-diagnostics.json"))
    narrative = load("narrative.comparison-projection.json")
    explicit = load("explicit-selection.comparison-projection.json")
    validate_definition("comparison", narrative)
    validate_definition("comparison", explicit)
    assert not narrative["projectedChangedObservations"] and len(narrative["projectedUnchangedObservations"]) == 26
    assert not narrative["projectedConclusionChanged"]
    assert len(narrative["projectedAssessmentChanges"]) == 1
    change = narrative["projectedAssessmentChanges"][0]["assessmentChange"]
    assert change["changeReferencedMaterial"] and not any(change[key] for key in
                                                        ["changeSelection", "changeClassification", "changeAuthorship"])
    assert len(explicit["projectedChangedObservations"]) == 20 and explicit["projectedConclusionChanged"]
    assert load("revision-excerpt.json")["computedObservationChanges"] == "0"
    assert load("resolution-excerpt.json")["originalExcerpt"] == "猫 item."
    print("case/application consumer: drafts, scoped provenance, selected alternatives, exact original excerpts, narrative revision and exports passed")
    print("projection consumer: complete contract, XML/SVG connections and IDs, view bindings, status labels, comparison audit and recovery passed")


if __name__ == "__main__":
    main()
