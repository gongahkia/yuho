"""Public temporal consumer: schemas, bindings, snapshots and export integrity."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from jsonschema import Draft202012Validator
ROOT = Path(__file__).resolve().parents[1]


def verify(out):
    def load(path):
        return json.loads(path.read_bytes())
    doc_schema = load(ROOT / 'schema/authoring-v0.5-experimental.schema.json')
    projection_schema = load(ROOT / 'schema/temporal-projection-v0.5-experimental.schema.json')
    for schema in [doc_schema, projection_schema]:
        Draft202012Validator.check_schema(schema)
    for name in ['synthetic-authored.json', 'pc24-authored.json', 'law-revision-authored.json', 'interval-revision-authored.json']:
        Draft202012Validator(doc_schema).validate(load(out / 'data' / name))
    count = 0
    for path in (out / 'data').glob('*-projection.json'):
        if path.name.endswith('-selected-law-projection.json'):
            continue
        data = load(path)
        Draft202012Validator(projection_schema).validate(data)
        ns = {n['projectedNodeId']: n for n in data['temporalProjectionNodes']}
        es = {e['projectedEdgeId']: e for e in data['temporalProjectionEdges']}
        assert len(ns) == len(data['temporalProjectionNodes'])
        assert len(es) == len(data['temporalProjectionEdges'])
        assert ns.keys().isdisjoint(es)
        assert all(e['projectedEdgeFrom'] in ns and e['projectedEdgeTo'] in ns for e in es.values())
        selection = data['temporalProjectionSelection']
        proof = data['temporalProjectionProof']
        assert selection['selectionUnderlyingSnapshot'] == proof['projectionSnapshot']['snapshotId']
        for n in ns.values():
            if n['projectedNodeRole'] == 'temporal_expression':
                assert n['projectedNodeComputed'] is None
                assert n['projectedNodeObservation'] is None
        assert all(n['projectedNodeComputed'] is None for n in ns.values()
                   if n['projectedNodeRole'] in {'temporal_original_source', 'original_source', 'assertion', 'assessment'})
        assert all(n['projectedNodeObservation']['observationRunSnapshot'] == selection['selectionUnderlyingSnapshot']
                   for n in ns.values() if n['projectedNodeObservation'])
        prefix = path.name.removesuffix('-projection.json')
        for view_name in ['selection', 'provenance']:
            view = load(path.parent / (prefix + '-' + view_name + '-bindings.json'))
            inc = set(view['viewIncludedNodes'])
            edges = set(view['viewIncludedEdges'])
            assert view['viewProjectionId'] == data['temporalProjectionId']
            assert inc | set(view['viewOmittedNodes']) == ns.keys()
            assert inc.isdisjoint(view['viewOmittedNodes'])
            assert edges | set(view['viewOmittedEdges']) == es.keys()
            assert edges.isdisjoint(view['viewOmittedEdges'])
            assert all(es[e]['projectedEdgeFrom'] in inc and es[e]['projectedEdgeTo'] in inc for e in edges)
            roles = [ns[key]['projectedNodeRole'] for key in view['viewIncludedNodes']]
            if roles: assert roles[0] == 'conduct_date'
            selected_indices = [i for i, key in enumerate(view['viewIncludedNodes'])
                                if ns[key]['projectedNodeRole'] == 'temporal_expression' and ns[key]['projectedNodeSelected']]
            assert selected_indices == [1]
            svg = ET.parse(out / (prefix + '-' + view_name + '.svg'))
            ids = {e.attrib['id'] for e in svg.iter() if 'id' in e.attrib}
            assert all(b['viewBindingRenderedId'] in ids for b in view['viewNodeBindings'])
            assert all(b['edgeBindingRenderedId'] in ids for b in view['viewEdgeBindings'])
        count += 1
    assert count == 5
    for path in list(out.glob('*.svg')) + list(out.glob('*.xml')):
        ET.parse(path)
    lifecycle = load(out / 'data' / 'revision-lifecycle.json')
    assert lifecycle['outcomes'] == ['not_satisfied', 'satisfied', 'not_satisfied', 'satisfied', 'satisfied']
    assert lifecycle['staleAttachmentRejected'] and lifecycle['crossVersionComparisonRejected']
    assert lifecycle['initial']['selectionSnapshot']['temporalSnapshotId'] != lifecycle['withinInterval']['selectionSnapshot']['temporalSnapshotId']
    assert lifecycle['initial']['selectionUnderlyingSnapshot'] == lifecycle['withinInterval']['selectionUnderlyingSnapshot']
    assert lifecycle['sourceExpansionSnapshotUnchanged']
    for path in (out / 'data').glob('*source-recovery.json'):
        for excerpt in load(path):
            if excerpt['excerptReference']['referenceSpan'] is not None:
                span = excerpt['excerptReference']['referenceSpan']
                content = excerpt['excerptSource']['sourceText'].encode()
                assert excerpt['excerptText'] == content[span['start']:span['end']].decode()
    print('temporal public consumer: five complete/schema-valid projections, ten view partitions, all SVG/XML, snapshots and exact original recovery passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', nargs='?')
    parser.add_argument('--outputs', type=Path)
    args = parser.parse_args()
    if args.outputs:
        verify(args.outputs)
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-temporal-public-') as folder:
            subprocess.run([str(Path(args.binary).resolve()), folder], cwd='/private/tmp', check=True)
            verify(Path(folder))
