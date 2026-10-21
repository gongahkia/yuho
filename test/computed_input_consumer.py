#!/usr/bin/env python3
"""Public executable, schema, provenance, view and saved-replay boundary checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]


def verify(out):
    def load(path):
        return json.loads(path.read_bytes())
    schemas = [load(p) for p in (ROOT / 'schema').glob('*.schema.json')]
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas if '$id' in s)
    def validator(name):
        schema = load(ROOT / 'schema' / name)
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema, registry=registry)
    authored = validator('computed-input-v0.1-experimental.schema.json')
    complete = validator('computed-input-projection-v0.1-experimental.schema.json')
    proof_schema = load(ROOT / 'schema/analysis-projection-v0.1-experimental.schema.json')
    bindings = Draft202012Validator({'$schema': proof_schema['$schema'], '$ref': proof_schema['$id'] + '#/$defs/view'}, registry=registry)
    reports = list(out.glob('*.report.json'))
    actual = [p for p in reports if '.reference.' not in p.name]
    assert len(actual) == 12
    for path in actual:
        name = path.name.removesuffix('.report.json')
        report = load(path)
        document = load(out / (name + '.document.json'))
        authored.validate(document)
        projection = load(out / (name + '.projection.json'))
        complete.validate(projection)
        assert report == projection['computedProjectionReport']
        assert report['computedGeneratedOrigin'] == 'generated_computed_input_bridge'
        generated = report['computedGeneratedAssessment']
        assert generated['assessmentOrigin'] == 'external_assertion'
        assert generated['assessmentBasis'] == 'assumption'
        assert generated['assessmentIssuer'] == 'Yuho explicit computed-input adapter'
        original = document['computedDestination']
        overlay = report['computedExecutionOverlay']
        def base(dest):
            return dest['destinationProof'] or dest['destinationPresumption']['presumptionProofDocument']
        assert generated['assessmentId'] not in [a['assessmentId'] for a in base(original)['documentAssessments']]
        assert base(overlay)['documentAssessments'] == base(original)['documentAssessments'] + [generated]
        assert report['computedOriginalObservation']['typedObservationCategory'] == 'expression'
        assert report['computedOriginalObservation']['typedObservedState'] == 'evaluated'
        assert document['computedBinding']['computedSourceSnapshot'] == report['computedTypedSnapshot']['typedSnapshotId']
        assert load(out / (name + '.replay.json'))['stable']
        assert load(out / (name + '.parity.json'))['equalTechnicalObservations']
        assert not load(out / (name + '.parity.json'))['sameProvenance']
        view = load(out / (name + '.bindings.json'))
        bindings.validate(view)
        nodes = projection['computedProjectionNodes']
        edges = projection['computedProjectionEdges']
        node_ids = [n['projectedNodeId'] for n in nodes]
        edge_ids = [e['projectedEdgeId'] for e in edges]
        assert len(set(node_ids + edge_ids)) == len(node_ids + edge_ids)
        assert set(view['viewIncludedNodes']) | set(view['viewOmittedNodes']) == set(node_ids)
        assert set(view['viewIncludedEdges']) | set(view['viewOmittedEdges']) == set(edge_ids)
        assert all(e['projectedEdgeFrom'] in node_ids and e['projectedEdgeTo'] in node_ids for e in edges)
        components = [projection['computedSourceProjection']]
        component_ids = {components[0]['typedProjectionId']: {n['typedNodeId'] for n in components[0]['typedProjectionNodes']}}
        for field, prefix in [('computedProofProjection', 'projection'), ('computedPresumptionProjection', 'presumptionProjection')]:
            component = projection[field]
            if component:
                component_ids[component[prefix + 'Id']] = {n['projectedNodeId'] for n in component[prefix + 'Nodes']}
        assert projection['computedNavigation']
        for link in projection['computedNavigation']:
            assert link['integrationNode'] in node_ids
            assert link['componentNode'] in component_ids[link['componentProjection']]
        svg = ET.parse(out / (name + '.svg')).getroot()
        ET.parse(out / (name + '.view.xml'))
        load(out / (name + '.view.json'))
        assert len([n for n in svg.iter() if n.get('id', '').startswith('node-')]) == len(view['viewIncludedNodes'])
        assert len([n for n in svg.iter() if n.get('id', '').startswith('edge-')]) == len(view['viewIncludedEdges'])
        assert load(out / (name + '.source-recovery.json'))['excerptText'] == 'Zoë records access for Actor One to Resource R for read.'
    assert len({load(out / (name + '.report.json'))['computedExecutionId'] for name in ['proof-true','proof-false','proof-unresolved']}) == 3
    for name, code in [('wrong-actor', 'CBSCOPE'), ('stale-upstream', 'CBSTALE'), ('stale-changed-tuple', 'CBSTALE'), ('stale-destination', 'CBSTALE'), ('direct-conflict', 'CBCONFLICT')]:
        assert any(d['diagnosticCode'] == code for d in load(out / (name + '.diagnostics.json')))
    skipped = load(out / 'presumption-skipped.report.json')['computedDerivationReport']
    assert skipped['presumptionReportDerivations'][0]['registrationEvaluation'] == 'evaluated'
    assert skipped['presumptionReportDerivations'][0]['registrationRouteState'] == 'active'
    target = next(x for x in skipped['presumptionReportProof']['reportRequirements'] if x['observationNode'] == 'target')
    assert target['observationComputed'] is None and target['observationEvaluation'] == 'not_evaluated'
    assert 'requirements_unresolved' in target['observationSkipReason']
    malformed = load(out / 'unknown-field.input.json')
    assert list(authored.iter_errors(malformed))
    print('computed-input consumer: 12 schema-valid compositions/reference parities, overlays, snapshots/replay, exact sources, navigation/partitions, SVG/XML, conflicts and stale refusals passed')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--verify':
        verify(Path(sys.argv[2]))
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-computed-input-') as directory:
            subprocess.run([str(Path(sys.argv[1]).resolve()), directory], cwd='/private/tmp', check=True, timeout=60)
            verify(Path(directory))
