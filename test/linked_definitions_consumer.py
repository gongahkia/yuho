"""Execute the public linked-definition consumer outside the checkout; audit contracts."""
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
    authored = json.loads((ROOT / 'schema/authoring-v0.2-experimental.schema.json').read_bytes())
    projected = json.loads((ROOT / 'schema/analysis-projection-v0.2-experimental.schema.json').read_bytes())
    legacy = {'$defs': projected['$defs'], '$ref': '#/$defs/legacyView'}
    for schema in [authored, projected, legacy]:
        Draft202012Validator.check_schema(schema)
    for name in ['baseline.document.json', 'hypothetical-revision.document.json']:
        Draft202012Validator(authored).validate(load(name))
    baseline = load('baseline.document.json')
    assert sum(n['nodeKind'] == 'definition' for n in baseline['documentLaw']['lawNodes']) == 1
    assert sum(e['edgeKind'] == 'use' for e in baseline['documentLaw']['lawEdges']) == 2
    views = 0
    for path in folder.glob('*.projection.json'):
        data = json.loads(path.read_bytes())
        Draft202012Validator(projected).validate(data)
        nodes = {n['projectedNodeId']: n for n in data['projectionNodes']}
        edges = {e['projectedEdgeId']: e for e in data['projectionEdges']}
        assert len(nodes) == len(data['projectionNodes']) and len(edges) == len(data['projectionEdges'])
        assert nodes.keys().isdisjoint(edges)
        assert all(e['projectedEdgeFrom'] in nodes and e['projectedEdgeTo'] in nodes for e in edges.values())
        assert all(n['projectedNodeComputed'] is None for n in nodes.values() if n['projectedNodeRole'] == 'definition')
        name = path.name.removesuffix('.projection.json')
        binding = folder / (name + '.bindings.json')
        if not binding.exists():
            continue
        view = json.loads(binding.read_bytes())
        Draft202012Validator({'$defs': projected['$defs'], '$ref': '#/$defs/view'}).validate(view)
        inc, omit = set(view['viewIncludedNodes']), set(view['viewOmittedNodes'])
        assert inc.isdisjoint(omit) and inc | omit == nodes.keys()
        ie, oe = set(view['viewIncludedEdges']), set(view['viewOmittedEdges'])
        assert ie.isdisjoint(oe) and ie | oe == edges.keys()
        assert all(edges[e]['projectedEdgeFrom'] in inc and edges[e]['projectedEdgeTo'] in inc for e in ie)
        assert {b['viewBindingProjectedId'] for b in view['viewNodeBindings']} == inc
        Draft202012Validator(legacy).validate(load(name + '.view.json'))
        ET.parse(folder / (name + '.xml'))
        svg = ET.parse(folder / (name + '.svg'))
        ids = [e.attrib['id'] for e in svg.iter() if 'id' in e.attrib]
        assert len(ids) == len(set(ids))
        views += 1
    a, b = load('definition-A.json'), load('definition-B.json')
    assert a['sharedDefinitionDigest'] == b['sharedDefinitionDigest'] and len(a['sharedUses']) == 2
    ra, rb = load('definition-revision-A.json'), load('definition-revision-B.json')
    assert ra['sharedDefinitionDigest'] == rb['sharedDefinitionDigest'] != a['sharedDefinitionDigest']
    assert all(next(n for n in r['sharedBodyNodes'] if n['nodeId'] == 'g:dishonestly')['nodeKind'] == 'all' for r in [ra, rb])
    oa, ob = load('occurrence-A.json')[0], load('occurrence-B.json')[0]
    assert oa['linkedAnalysis']['analysisScope'] != ob['linkedAnalysis']['analysisScope']
    def occurrence(info):
        return info['linkedRequirement']['explanationOccurrence']
    assert occurrence(oa)['projectedNodeId'] != occurrence(ob)['projectedNodeId']
    assert occurrence(oa)['projectedNodeObservation'] != occurrence(ob)['projectedNodeObservation']
    assert all(any(e['edgeKind'] == 'use' for e in o['linkedReferencePath']) for o in [oa, ob])
    assert all(o['linkedKernelMappings'] for o in [oa, ob])
    assert load('source-A.json')['excerptText'] == 'intention of causing wrongful gain'
    summary = load('summary.json')
    assert (summary['baselineA'], summary['baselineB']) == ('satisfied', 'unresolved')
    assert (summary['revisedA'], summary['revisedB']) == ('not_satisfied', 'not_satisfied')
    assert summary['otherActorUnchanged'] == 'unresolved' and summary['oneActorChanged'] == 'not_satisfied'
    for name, code in [('missing.compile-refusal.json', 'AMISSING'), ('wrong-scope.compile-refusal.json', 'ASCOPE'), ('stale-attachment.json', 'PSTALE')]:
        assert any(d['diagnosticCode'] == code for d in load(name))
    assert load('baseline-A.snapshot.json')['snapshotDocument'] == baseline
    assert load('revision-A.snapshot.json')['snapshotId'] != load('baseline-A.snapshot.json')['snapshotId']
    # The overview includes exactly one shared declaration and both authored use edges.
    view = load('one-definition-two-uses.bindings.json')
    projection = load('one-definition-two-uses.projection.json')
    visible = set(view['viewIncludedNodes'])
    assert sum(n['projectedNodeRole'] == 'definition' and n['projectedNodeId'] in visible for n in projection['projectionNodes']) == 1
    assert sum(e['projectedEdgeKind'] == 'use' and e['projectedEdgeId'] in view['viewIncludedEdges'] for e in projection['projectionEdges']) == 2
    print(f'linked definitions consumer: schemas, scope isolation, revision, source recovery and {views} view partitions/encoders passed')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('executable', type=Path)
    parser.add_argument('--existing-artifacts', type=Path)
    args = parser.parse_args()
    if args.existing_artifacts:
        verify(args.existing_artifacts)
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-linked-consumer-') as directory:
            folder = Path(directory)
            subprocess.run([str(args.executable.resolve()), str(folder)], cwd=folder, check=True, capture_output=True, timeout=90)
            verify(folder)

if __name__ == '__main__':
    main()
