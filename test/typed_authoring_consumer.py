"""Public typed consumer: schema, identity, state, view and source contracts."""
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
    authored = json.loads((ROOT / 'schema/authoring-v0.3-experimental.schema.json').read_bytes())
    projection = json.loads((ROOT / 'schema/typed-analysis-projection-v0.3-experimental.schema.json').read_bytes())
    for schema in (authored, projection):
        Draft202012Validator.check_schema(schema)
    for suffix, schema_name in [('request', 'typed-finite-rules-request.schema.json'), ('response', 'typed-finite-rules-result.schema.json')]:
        wire = json.loads((ROOT / 'schema' / schema_name).read_bytes())
        Draft202012Validator.check_schema(wire)
        for path in folder.glob('*.' + suffix + '.json'):
            Draft202012Validator(wire).validate(json.loads(path.read_bytes()))
    views = 0
    for path in folder.glob('*.document.json'):
        Draft202012Validator(authored).validate(json.loads(path.read_bytes()))
    for path in folder.glob('*.projection.json'):
        data = json.loads(path.read_bytes())
        Draft202012Validator(projection).validate(data)
        nodes = {n['typedNodeId']: n for n in data['typedProjectionNodes']}
        edges = {e['typedEdgeId']: e for e in data['typedProjectionEdges']}
        assert len(nodes) == len(data['typedProjectionNodes']) and len(edges) == len(data['typedProjectionEdges'])
        assert nodes.keys().isdisjoint(edges)
        assert all(e['typedEdgeFrom'] in nodes and e['typedEdgeTo'] in nodes for e in edges.values())
        assert all(n['typedNodeObservation'] is None for n in nodes.values() if n['typedNodeKind'] in {'assessment','value','source','application','scalar','assertion','entity','predicate'})
        assert all(e['typedEdgeOriginal'] is None or e['typedEdgeKind'] == 'original_source' for e in edges.values())
        name = path.name.removesuffix('.projection.json')
        bindings = folder / (name + '.bindings.json')
        if not bindings.exists():
            continue
        view = json.loads(bindings.read_bytes())
        Draft202012Validator({'$defs': projection['$defs'], '$ref': '#/$defs/view'}).validate(view)
        inc, omit = set(view['viewIncludedNodes']), set(view['viewOmittedNodes'])
        ie, oe = set(view['viewIncludedEdges']), set(view['viewOmittedEdges'])
        assert inc.isdisjoint(omit) and inc | omit == nodes.keys()
        assert ie.isdisjoint(oe) and ie | oe == edges.keys()
        assert all(edges[e]['typedEdgeFrom'] in inc and edges[e]['typedEdgeTo'] in inc for e in ie)
        assert {b['viewBindingProjectedId'] for b in view['viewNodeBindings']} == inc
        assert [b['edgeBindingProjectedId'] for b in view['viewEdgeBindings']] == view['viewIncludedEdges']
        svg = ET.parse(folder / (name + '.svg'))
        ids = [n.attrib['id'] for n in svg.iter() if 'id' in n.attrib]
        assert len(ids) == len(set(ids))
        assert all(b['viewBindingRenderedId'] in ids for b in view['viewNodeBindings'])
        assert all(b['edgeBindingRenderedId'] in ids for b in view['viewEdgeBindings'])
        if (folder / (name + '.xml')).exists():
            ET.parse(folder / (name + '.xml'))
            Draft202012Validator({'$defs': projection['$defs'], '$ref': '#/$defs/legacyView'}).validate(load(name + '.view.json'))
        views += 1
    for name, expected in [('permission-ada','satisfied'),('permission-ben-unresolved','unresolved'),('permission-ben-false','not_satisfied'),('threshold-34','not_satisfied'),('threshold-35','not_satisfied'),('threshold-36','satisfied'),('threshold-unresolved','unresolved'),('threshold-scaled-3501','satisfied')]:
        report = load(name + '.report.json')
        assert [r['typedObservedStatus'] for r in report['typedReportRules']] == [expected]
        assert [r['typedObservedStatus'] for r in report['typedReportPropositions']] == [expected]
        assert report['typedReportProfile'] == 'TypedFiniteRules-v1'
        assert all(r['typedObservationCategory'] == 'expression' for r in report['typedReportExpressions'])
        assert all(m['typedMappingGeneratedReason'] is None or m['typedMappingGeneratedReason'].startswith('generated SDK assessment ') for m in report['typedReportMappings'])
    draft = load('permission-draft.projection.json')
    assert draft['typedProjectionReport'] is None
    assert all(n['typedNodeObservation'] is None for n in draft['typedProjectionNodes'])
    assert {x['typedOpenState'] for x in draft['typedProjectionOpenInputs']} == {'missing'}
    inspection = load('permission-inspection.json')
    assert inspection['typedFocusSelected']['typedAssessmentMeta']['typedId'] == 'assessment:ada'
    assert [x['typedAssessmentMeta']['typedId'] for x in inspection['typedFocusAlternatives']] == ['assessment:ada-alternative']
    assert len(inspection['typedFocusAssertions']) == 2 and len(inspection['typedFocusArguments']) == 3
    assert load('permission-source-recovery.json')['excerptText'] == 'Zoë permits Ada to read Server R.'
    revision = load('permission-revision.json')
    assert revision['oldSnapshot'] != revision['newSnapshot'] and revision['oldResult'] == ['unresolved'] and revision['newResult'] == ['not_satisfied']
    assert revision['staleDiagnostics'][0]['diagnosticCode'] == 'TSTALE'
    for name in ['missing-assessment','wrong-scope','wrong-scalar','tuple-edited']:
        assert not load(name + '.validation.json')['typedAnalysisReady'] and load(name + '.rejection.json')
    print(f'typed consumer: {views} bound views, schemas, supplied/computed distinctions, tuple/scope isolation, exact boundaries and revisions passed')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('executable', type=Path)
    parser.add_argument('--existing-artifacts', type=Path)
    args = parser.parse_args()
    if args.existing_artifacts:
        verify(args.existing_artifacts.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-typed-consumer-') as folder:
            subprocess.run([str(args.executable.resolve()), str(Path(folder)/'out')], cwd=folder, check=True)
            verify(Path(folder)/'out')
