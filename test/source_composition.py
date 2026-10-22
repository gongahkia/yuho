"""Source-only composition CLI, source authority and refusal regressions.

Runs copied projects outside the checkout. --output retains all inputs/outputs.
Independent semantic reference comparisons live in SourceCompositionChecks.hs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    'proof/true': ('satisfied', 'satisfied', None),
    'proof/false': ('not_satisfied', 'not_satisfied', None),
    'proof/unresolved': ('unresolved', 'unresolved', None),
    'proof/integer-boundary': ('not_satisfied', 'not_satisfied', None),
    'proof/integer-above': ('satisfied', 'satisfied', None),
    'proof/integer-unknown': ('unresolved', 'unresolved', None),
    'presumption/active': ('satisfied', 'satisfied', 'active'),
    'presumption/inactive': ('not_satisfied', 'not_satisfied', 'inactive'),
    'presumption/unresolved': ('unresolved', 'unresolved', 'unresolved'),
    'presumption/rebutted': ('satisfied', 'not_satisfied', 'rebutted'),
    'presumption/dominance': ('satisfied', 'satisfied', 'rebutted'),
    'presumption/skipped': ('satisfied', 'unresolved', 'active'),
    'presumption/computed-rebuttal': ('satisfied', 'not_satisfied', 'rebutted'),
    'presumption/computed-rebuttal-false': ('not_satisfied', 'satisfied', 'active'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(binary, base):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    schemas = [json.loads(p.read_text()) for p in (ROOT / 'schema').glob('*.json')]
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas if '$id' in s)
    validators = {s['$id'].rsplit('/', 1)[-1]: Draft202012Validator(s, registry=registry) for s in schemas if '$id' in s}
    projects = base / 'projects'
    shutil.copytree(ROOT / 'examples/source-composition', projects)
    before = {str(p.relative_to(projects)): digest(p) for p in projects.rglob('*') if p.is_file()}
    commands, outcomes, failures = [], [], []
    (base / 'runs').mkdir()
    (base / 'negative').mkdir()

    def invoke(name, args, expected=0):
        command = [str(binary), 'compose', *map(str, args)]
        proc = subprocess.run(command, cwd=base, capture_output=True, timeout=45)
        commands.append({'name': name, 'command': command, 'cwd': str(base), 'exit': proc.returncode,
                         'stdout': proc.stdout.decode(), 'stderr': proc.stderr.decode()})
        (base / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        assert proc.returncode == expected, (name, proc.stdout, proc.stderr)
        return proc

    def exported(name, project):
        out = base / 'runs' / name
        invoke(name, ['run', project, '--output', out])
        report = json.loads((out / 'report.json').read_text())
        projection = json.loads((out / 'projection.json').read_text())
        artifact = json.loads((out / 'artifact.json').read_text())
        view = json.loads((out / 'view-bindings.json').read_text())
        for f, schema in [('artifact.json', 'computed-input-v0.1-experimental.schema.json'),
                          ('projection.json', 'computed-input-projection-v0.1-experimental.schema.json')]:
            validators[schema].validate(json.loads((out / f).read_text()))
        for f in ['view.xml', 'view.svg']:
            ET.parse(out / f)
        nodes = {x['projectedNodeId'] for x in projection['computedProjectionNodes']}
        edges = {x['projectedEdgeId'] for x in projection['computedProjectionEdges']}
        assert set(view['viewIncludedNodes']).isdisjoint(view['viewOmittedNodes'])
        assert set(view['viewIncludedNodes']) | set(view['viewOmittedNodes']) == nodes
        assert set(view['viewIncludedEdges']) | set(view['viewOmittedEdges']) == edges
        assert report['computedGeneratedOrigin'] == 'generated_computed_input_bridge'
        assert report['computedOriginalObservation']['typedObservationCategory'] == 'expression'
        assert report['computedOriginalObservation']['typedObservedState'] == 'evaluated'
        binding = artifact['computedBinding']
        assert report['computedTypedSnapshot']['typedSnapshotId'] == binding['computedSourceSnapshot']
        assert binding['computedSourceScope'] == binding['computedDestinationScope']
        sources = artifact['computedTypedSource']['typedOriginalSources']
        for source in sources:
            if source['sourceText'] is not None:
                expected = (project.parent / source['sourceLocator']).read_bytes()
                assert source['sourceText'].encode() == expected
        return out, report, artifact

    results = {}
    for name, (typed, final, route) in CASES.items():
        project = projects / (name + '.project.yh')
        checked = invoke(name + '-check', ['check', project]).stdout
        assert json.loads(checked)['evaluated'] is False
        assert invoke(name + '-check-deterministic', ['check', project]).stdout == checked
        out, report, artifact = exported(name.replace('/', '-'), project)
        assert report['computedOriginalObservation']['typedObservedStatus'] == typed
        assert report['computedDownstreamReport']['reportConclusion'] == final
        actual_route = None
        if route:
            registration = report['computedDerivationReport']['presumptionReportDerivations'][0]
            actual_route = registration['registrationRouteState']
            assert actual_route == route
            assert registration['registrationEvaluation'] == 'evaluated'
        if name.endswith('/skipped'):
            assert any(x['exceptionEvaluation'] == 'not_evaluated' for x in report['computedDownstreamReport']['reportExceptions'])
            assert all(x['registrationEvaluation'] == 'evaluated' for x in report['computedDerivationReport']['presumptionReportDerivations'])
        replay = base / 'runs' / (name.replace('/', '-') + '-replay')
        invoke(name + '-replay', ['replay', out / 'artifact.json', '--output', replay])
        for file in out.iterdir():
            assert file.read_bytes() == (replay / file.name).read_bytes(), (name, file.name)
        invoke(name + '-attach', ['check', project, '--against', out / 'artifact.json'])
        results[name] = (out, report, artifact)
        outcomes.append({'project': name, 'expected': [typed, final, route], 'actual': [typed, final, actual_route],
                         'execution': report['computedExecutionId'], 'native_schema_and_replay': 'pass'})
    (base / 'outcomes.json').write_text(json.dumps(outcomes, indent=2) + '\n')
    assert before == {str(p.relative_to(projects)): digest(p) for p in projects.rglob('*') if p.is_file()}
    (base / 'source-preservation.json').write_text(json.dumps(before, indent=2) + '\n')

    def altered(name, filename, transform, code=None):
        folder = base / 'negative' / name
        shutil.copytree(projects / 'proof', folder)
        path = folder / filename
        path.write_text(transform(path.read_text()))
        project = folder / 'true.project.yh'
        proc = invoke(name, ['check', project], 1)
        error = json.loads(proc.stderr)
        assert not proc.stdout and error['line'] >= 1 and error['column'] >= 1
        if code:
            assert error['code'] == code, (name, error)
        failures.append({'name': name, 'input': str(path.relative_to(base)), 'diagnostic': error})
        (base / 'negative-results.json').write_text(json.dumps(failures, indent=2) + '\n')
        return error

    altered('unknown-expression', 'true.project.yh', lambda s: s.replace('expression q:relationship', 'expression q:missing'), 'SFC003')
    altered('wrong-observation-category', 'true.project.yh', lambda s: s.replace('expression q:relationship', 'expression typed-rule'), 'SFC003')
    altered('wrong-source-rule', 'true.project.yh', lambda s: s.replace('rule typed-rule', 'rule absent'), 'SFC002')
    altered('wrong-actor', 'true.project.yh', lambda s: s.replace('input f:no-authorization actor actor:one', 'input f:no-authorization actor actor:two'))
    altered('wrong-context', 'true.project.yh', lambda s: s.replace('input f:no-authorization actor actor:one context event:fictional', 'input f:no-authorization actor actor:one context event:other'))
    altered('unknown-actor', 'true.project.yh', lambda s: s.replace('expression q:relationship actor actor:one', 'expression q:relationship actor actor:absent'), 'SFC002')
    altered('missing-ground-input', 'true.yh', lambda s: '\n'.join(x for x in s.splitlines() if 'actor:one' not in x), 'SFT011')
    altered('missing-other-proof-input', 'direct.yh', lambda s: s.replace('  f:entry = proved;\n', ''))
    altered('agreeing-direct-conflict', 'direct.yh', lambda s: s.replace('  f:entry = proved;', '  f:entry = proved;\n  f:no-authorization = proved;'))
    altered('wrong-arity', 'relationship.yh', lambda s: s.replace('q:relationship = authorised(actor:one,resource:r,action:read)', 'q:relationship = authorised(actor:one,resource:r)'), 'SFT004')
    altered('wrong-type', 'relationship.yh', lambda s: s.replace('q:relationship = authorised(actor:one', 'q:relationship = authorised(resource:r'), 'SFT005')
    error = altered('unsupported-not', 'relationship.yh', lambda s: s.replace('= authorised(actor:one,resource:r,action:read);', '= not(authorised(actor:one,resource:r,action:read));'), 'SFC002')
    assert error['path'].endswith('relationship.yh') and error['line'] == 14
    altered('unsupported-predicate-category', 'relationship.yh', lambda s: s.replace('kind relationship', 'kind conduct'), 'SFC002')
    altered('multiple-named-expressions', 'relationship.yh', lambda s: s.replace(' rule typed-rule', ' requirement q:extra = authorised(actor:two,resource:r,action:read);\n rule typed-rule'), 'SFC003')
    altered('malformed-project', 'true.project.yh', lambda s: s.replace('source-model "relationship.yh";', 'source-model ;'), 'SFC001')
    altered('forbidden-parent', 'true.project.yh', lambda s: s.replace('"relationship.yh"', '"../relationship.yh"'), 'SFC005')
    altered('forbidden-url', 'true.project.yh', lambda s: s.replace('"relationship.yh"', '"https://example.invalid/model.yh"'), 'SFC005')
    altered('forbidden-import', 'relationship.yh', lambda s: s.replace(' limit 2048;', ' limit 2048;\n import "other.yh" as ext;'))
    altered('unknown-mapping', 'true.project.yh', lambda s: s.replace('yuho.technical-status-to-proof/v1', 'implicit-proof/v1'))
    altered('unknown-unresolved-reason', 'true.project.yh', lambda s: s.replace('unresolved not_determined', 'unresolved absent'))
    altered('nonprimitive-destination', 'true.project.yh', lambda s: s.replace('input f:no-authorization', 'input g:offence-requirements'))
    altered('unsupported-destination-profile', 'true.project.yh', lambda s: s.replace('destination-model "proof.yh"', 'destination-model "relationship.yh"'), 'SFC002')
    altered('unknown-destination', 'true.project.yh', lambda s: s.replace('input f:no-authorization', 'input f:absent'))
    altered('no-silent-label-matching', 'true.project.yh', lambda s: s.replace('label actor:two', 'label actor:unknown'), 'SFC002')
    altered('source-budget', 'true.yh', lambda s: s + ' ' * 65536, 'SFC005')
    utf8 = altered('utf8-diagnostic', 'true.project.yh', lambda s: s.replace('source-model "relationship.yh";', 'source-model "é猫" !'), 'SFE001')

    assert (utf8['line'], utf8['column']) == (2, 23)  # é=2 bytes, 猫=3 bytes

    # Finite groups preserve children and backend observations; they do not
    # acquire the single-predicate assertion support relationship.
    for form, expected in [('all', 'not_satisfied'), ('any', 'satisfied')]:
        folder = base / ('group-' + form)
        shutil.copytree(projects / 'proof', folder)
        model = folder / 'relationship.yh'
        model.write_text(model.read_text().replace(
            'q:relationship = authorised(actor:one,resource:r,action:read);',
            'q:relationship = ' + form + '(authorised(actor:one,resource:r,action:read),authorised(actor:two,resource:r,action:read));'))
        project = folder / 'true.project.yh'
        project.write_text('\n'.join(x for x in project.read_text().splitlines() if 'assertion assertion:' not in x))
        _, report, artifact = exported('group-' + form, project)
        assert report['computedOriginalObservation']['typedObservedStatus'] == expected
        assert len(report['computedUpstreamReport']['typedReportExpressions']) == 3
        assert len(artifact['computedTypedSource']['typedExpressions']) == 3
    # Symlink sources cannot escape the sibling-file policy.
    folder = base / 'symlink'
    shutil.copytree(projects / 'proof', folder)
    (folder / 'relationship.yh').unlink()
    (folder / 'relationship.yh').symlink_to(projects / 'proof/relationship.yh')
    error = invoke('symlink-source', ['check', folder / 'true.project.yh'], 1)
    assert json.loads(error.stderr)['code'] == 'SFC005'

    # Exact tuple change must select actor two's retained false input, not Alex's
    # true input. Keeping the scope unchanged does not change tuple identity.
    changed = base / 'tuple-swap'
    shutil.copytree(projects / 'proof', changed)
    model = changed / 'relationship.yh'
    model.write_text(model.read_text().replace('q:relationship = authorised(actor:one,', 'q:relationship = authorised(actor:two,'))
    _, report, _ = exported('tuple-swap', changed / 'true.project.yh')
    assert report['computedOriginalObservation']['typedObservedStatus'] == 'not_satisfied'

    # A same-status edit changes exact source/snapshots. Frozen replay remains
    # inspectable; explicit attachment to changed live sources must fail.
    changed = base / 'same-status'
    shutil.copytree(projects / 'proof', changed)
    scenario = changed / 'true.yh'
    scenario.write_text(scenario.read_text() + '\n// Zoë revised this source; the supplied status remains proved.\n')
    oldout, oldreport, _ = results['proof/true']
    error = invoke('stale-attachment', ['check', changed / 'true.project.yh', '--against', oldout / 'artifact.json'], 1)
    assert json.loads(error.stderr)['code'] == 'SFCSTALE'
    _, report, _ = exported('same-status-fresh', changed / 'true.project.yh')
    assert report['computedOriginalObservation']['typedObservedStatus'] == oldreport['computedOriginalObservation']['typedObservedStatus']
    assert report['computedTypedSnapshot']['typedSnapshotId'] != oldreport['computedTypedSnapshot']['typedSnapshotId']
    assert report['computedExecutionId'] != oldreport['computedExecutionId']
    (base / 'same-status-revision.json').write_text(json.dumps({'before': oldreport['computedExecutionId'], 'after': report['computedExecutionId'], 'status': 'satisfied', 'stale_attachment': json.loads(error.stderr)}, indent=2) + '\n')
    for size in [1, 119, 120, 127, 128, 129]:
        folder = base / ('binding-id-' + str(size))
        shutil.copytree(projects / 'proof', folder)
        project = folder / 'true.project.yh'
        project.write_text(project.read_text().replace('binding binding:true ', 'binding ' + 'b' * size + ' '))
        if size <= 128:
            exported('binding-id-' + str(size), project)
        else:
            invoke('binding-id-129', ['check', project], 1)
    # Strict artifact decoding / snapshot checks remain the public SDK's path.
    artifact = json.loads((oldout / 'artifact.json').read_text())
    artifact['computedBinding']['unknownField'] = True
    saved = base / 'bad-artifact.json'
    saved.write_text(json.dumps(artifact))
    invoke('unknown-artifact-field', ['replay', saved, '--output', base / 'must-not-exist'], 1)
    assert not (base / 'must-not-exist').exists()
    invoke('no-output-overwrite', ['run', projects / 'proof/true.project.yh', '--output', oldout], 1)
    print(f'source composition: {len(CASES)} independent expected scenarios; schemas, replay, {len(failures)} refusal cases, tuple isolation, long IDs and same-status revision passed; {len(commands)} CLI executions outside checkout')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=False)
        run(args.executable.resolve(), args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-source-composition-') as directory:
            run(args.executable.resolve(), Path(directory))


if __name__ == '__main__':
    main()
