"""External public presumption workflow and full-contract/schema checks."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def verify(folder):
    def load(name):
        return json.loads((folder / name).read_bytes())
    authored = json.loads((ROOT / 'schema/authoring-v0.4-experimental.schema.json').read_bytes())
    projection = json.loads((ROOT / 'schema/presumption-projection-v0.4-experimental.schema.json').read_bytes())
    for schema in [authored, projection]:
        Draft202012Validator.check_schema(schema)
    for path in folder.glob('*.document.json'):
        Draft202012Validator(authored).validate(json.loads(path.read_bytes()))
    for path in folder.glob('*.projection.json'):
        data = json.loads(path.read_bytes())
        Draft202012Validator(projection).validate(data)
        nodes = {n['projectedNodeId']: n for n in data['presumptionProjectionNodes']}
        edges = {e['projectedEdgeId']: e for e in data['presumptionProjectionEdges']}
        assert len(nodes) == len(data['presumptionProjectionNodes'])
        assert len(edges) == len(data['presumptionProjectionEdges'])
        assert nodes.keys().isdisjoint(edges)
        assert all(e['projectedEdgeFrom'] in nodes and e['projectedEdgeTo'] in nodes for e in edges.values())
        snapshot = data['presumptionProjectionSnapshot']
        assert snapshot['presumptionSnapshotDocument']['presumptionDocumentFormat'] == 'yuho.authoring/v0.4-experimental'
        for n in nodes.values():
            obs = n['projectedNodeObservation']
            if obs:
                assert obs['observationRunSnapshot'] == snapshot['presumptionSnapshotId']
                assert n['projectedNodeOrigin']['originKind'] == 'projection_generated'
                assert n['projectedNodeEvaluation'] == 'evaluated'
            if n['projectedNodeRole'] in {'assessment', 'assertion', 'original_source'}:
                assert n['projectedNodeComputed'] is None
        compiler = data['presumptionProjectionCompiler']
        if compiler:
            originals = {s['sourceId'] for s in snapshot['presumptionSnapshotDocument']['presumptionProofDocument']['documentSources']}
            generated = {s['generatedSourceId']: s for s in compiler['projectionGeneratedSources']}
            assert originals.isdisjoint(generated)
            for mapping in compiler['projectionGeneratedSpans']:
                assert mapping['sourceMappingSource'] in generated
                assert all(r['referenceSource'] in originals for r in mapping['sourceMappingOriginals'])
            for m in data['presumptionProjectionMappings']:
                source = generated[m['presumptionMappingSource']]['generatedSourceText']
                span = m['presumptionMappingSpan']
                assert source.encode()[span['start']:span['end']].decode() == source
        name = path.name.removesuffix('.projection.json')
        if name == 'draft':
            assert data['presumptionProjectionReport'] is None
            assert {x['openState'] for x in data['presumptionProjectionOpenInputs']} == {'missing'}
            continue
        report = load(name + '.report.json')
        assert report == data['presumptionProjectionReport']
        assert report['presumptionReportSnapshot'] == snapshot['presumptionSnapshotId']
        view = load(name + '.bindings.json')
        # Reuse the unchanged companion binding schema.
        old = json.loads((ROOT / 'schema/analysis-projection-v0.1-experimental.schema.json').read_bytes())
        Draft202012Validator({'$defs': old['$defs'], '$ref': '#/$defs/view'}).validate(view)
        inc, omit = set(view['viewIncludedNodes']), set(view['viewOmittedNodes'])
        ie, oe = set(view['viewIncludedEdges']), set(view['viewOmittedEdges'])
        assert inc.isdisjoint(omit) and inc | omit == nodes.keys()
        assert ie.isdisjoint(oe) and ie | oe == edges.keys()
        assert all(edges[e]['projectedEdgeFrom'] in inc and edges[e]['projectedEdgeTo'] in inc for e in ie)
        assert {b['viewBindingProjectedId'] for b in view['viewNodeBindings']} == inc
        svg = ET.parse(folder / (name + '.svg'))
        ids = [node.attrib['id'] for node in svg.iter() if 'id' in node.attrib]
        assert len(ids) == len(set(ids))
        assert all(b['viewBindingRenderedId'] in ids for b in view['viewNodeBindings'])
        assert all(b['edgeBindingRenderedId'] in ids for b in view['viewEdgeBindings'])
        ET.parse(folder / (name + '.view.xml'))
        Draft202012Validator({'$defs': old['$defs'], '$ref': '#/$defs/legacyView'}).validate(load(name + '.view.json'))
        assert nodes[view['viewIncludedNodes'][0]]['projectedNodeRole'] == 'input'
    for name, state, direct, effective, conclusion in [
        ('P1-active', 'active', 'not_satisfied', 'satisfied', 'satisfied'),
        ('P2-rebutted', 'rebutted', 'not_satisfied', 'not_satisfied', 'not_satisfied'),
        ('P3-direct-dominance', 'rebutted', 'satisfied', 'satisfied', 'satisfied'),
        ('P4-inactive', 'inactive', 'not_satisfied', 'not_satisfied', 'not_satisfied'),
        ('P5-unresolved', 'unresolved', 'not_satisfied', 'unresolved', 'unresolved')]:
        report = load(name + '.report.json')
        assert [r['registrationRouteState'] for r in report['presumptionReportDerivations']] == [state]
        target = next(x for x in report['presumptionReportLeaves'] if x['effectiveInput'] == 'K')
        assert target['effectiveDirectValue'] == direct and target['effectiveValue'] == effective
        assert report['presumptionReportProof']['reportConclusion'] == conclusion
    report = load('P7-skipped-guard.report.json')
    assert report['presumptionReportDerivations'][0]['registrationEvaluation'] == 'evaluated'
    target = next(x for x in report['presumptionReportLeaves'] if x['effectiveInput'] == 'K')
    assert target['effectiveValue'] == 'satisfied'
    assert target['effectiveDownstream'][0]['observationComputed'] is None
    assert target['effectiveDownstream'][0]['observationEvaluation'] == 'not_evaluated'
    assert 'requirements_unresolved' in target['effectiveDownstream'][0]['observationSkipReason']
    multiple = load('P6-multiple.report.json')
    assert len(multiple['presumptionReportDerivations']) == 2
    source = load('mda18-source-recovery.json')
    assert source['excerptState'] == 'anchored' and source['excerptText'].startswith('Any person who is proved or presumed')
    revision = load('revision.json')
    assert revision['originalSnapshot'] != revision['revisedSnapshot']
    assert revision['original']['presumptionReportDerivations'][0]['registrationRouteState'] == 'active'
    assert revision['revised']['presumptionReportDerivations'][0]['registrationRouteState'] == 'rebutted'
    print('presumption consumer: document/projection schemas, bindings, endpoints, original/generated sources, direct/effective/skip distinctions, revision and XML/SVG checks passed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('executable')
    parser.add_argument('--artifacts', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.artifacts:
        args.artifacts.mkdir(parents=True, exist_ok=True)
        if not args.verify_only:
            subprocess.run([str(Path(args.executable).resolve()), str(args.artifacts.resolve())], cwd='/private/tmp', check=True)
        verify(args.artifacts)
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-presumptions-') as directory:
            folder = Path(directory)
            subprocess.run([str(Path(args.executable).resolve()), str(folder)], cwd=directory, check=True)
            verify(folder)


if __name__ == '__main__':
    main()
