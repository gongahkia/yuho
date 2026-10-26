"""Executable language witnesses and opt-in compiler inspection CLI regressions.

Run from any directory: python3 test/compiler_inspection.py /absolute/path/to/yuho
Optional --output retains commands, inspection records and diagnostics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'yuho.compiler-inspection/v0.1-experimental'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    binary = str(args.executable.resolve())
    records = []
    output = args.output
    if output:
        output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix='yuho-inspection-') as directory:
        cwd = Path(directory)

        def invoke(name, command, expected=0):
            actual = subprocess.run([binary, *map(str, command)], cwd=cwd, capture_output=True, timeout=30)
            records.append({'name': name, 'cwd': str(cwd), 'command': [binary, *map(str, command)],
                            'exit': actual.returncode, 'stdout_sha256': hashlib.sha256(actual.stdout).hexdigest(),
                            'stderr': actual.stderr.decode()})
            if output:
                (output / f'{name}.stdout').write_bytes(actual.stdout)
                (output / f'{name}.stderr').write_bytes(actual.stderr)
                (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
            assert actual.returncode == expected, (name, actual.stdout, actual.stderr)
            return actual

        proof = ROOT / 'examples/synthetic/restricted_entry.yh'
        scenario = ROOT / 'examples/synthetic/scenario_all_proved.yh'
        typed = ROOT / 'test/fixtures/typed-authoring/permission.yh'
        typed_scenario = ROOT / 'test/fixtures/typed-authoring/permission.yhs'
        presumption = ROOT / 'examples/synthetic/presumption_active.yh'
        fixtures = [('proof', [proof, '--scenario', scenario], ['parsed', 'checked', 'normalized', 'lowered']),
                    ('typed', [typed, '--scenario', typed_scenario], ['parsed', 'checked', 'lowered']),
                    ('presumption', [presumption], ['parsed', 'lowered', 'checked']),
                    ('threshold', [ROOT / 'test/fixtures/typed-authoring/threshold.yh', '--scenario', ROOT / 'test/fixtures/typed-authoring/threshold.yhs'], ['parsed', 'checked', 'lowered'])]
        for name, command, expected_stages in fixtures:
            inspected = invoke(name + '-inspection', ['inspect', *command]).stdout
            assert invoke(name + '-repeated', ['inspect', *command]).stdout == inspected
            view = json.loads(inspected)
            assert view['format'] == VERSION and view['evaluated'] is False
            assert [s['stage'] for s in view['stages']] == expected_stages
            lowered = next(s for s in view['stages'] if s['stage'] == 'lowered')
            assert lowered['depends_on'] == (['parsed'] if name == 'presumption' else ['checked'])
            assert lowered['data']['executed'] is False
            if name == 'presumption':
                assert view['stages'][-1]['depends_on'] == ['lowered']
            compiled = invoke(name + '-compile', ['compile', *command]).stdout
            assert json.loads(compiled) == lowered['data']['request']
            assert hashlib.sha256(compiled).hexdigest() == lowered['data']['request_sha256']
            for mapping in lowered['data']['mappings']:
                node = lowered['data']['request']
                for segment in mapping['kernel_pointer'].split('/')[1:]:
                    node = node[int(segment)] if isinstance(node, list) else node[segment]
                assert node.get('id', node.get('presumption_id')) == mapping['kernel_id']
                original = mapping['authored']
                original_bytes = Path(original['source']).read_bytes()
                token_bytes = original['text'].encode()
                assert original_bytes[original['byte_offset']:original['byte_offset'] + len(token_bytes)] == token_bytes
            for op in ['compile', 'run', 'explain']:
                result = invoke(name + '-' + op + '-compatibility', [op, *command]).stdout
                if args.baseline:
                    assert result == (args.baseline / f'{name}-{op}.json').read_bytes(), (name, op, 'changed bytes')
            for stage in expected_stages:
                one = json.loads(invoke(name + '-' + stage, ['inspect', *command, '--stage', stage]).stdout)
                assert one['stages'] == [s for s in view['stages'] if s['stage'] == stage]
            for fmt in ['json', 'xml', 'svg']:
                diagram = cwd / f'{name}-diagram.{fmt}'
                invoke(f'{name}-diagram-{fmt}', ['diagram', *command, '--view', 'trace', '--format', fmt, '--output', diagram])
                if output:
                    (output / diagram.name).write_bytes(diagram.read_bytes())
                if args.baseline:
                    previous = cwd / f'{name}-previous.{fmt}'
                    prior = subprocess.run([str((args.baseline / 'yuho').resolve()), 'diagram', *map(str, command),
                        '--view', 'trace', '--format', fmt, '--output', str(previous)], cwd=cwd, capture_output=True)
                    assert prior.returncode == 0, prior.stderr
                    assert previous.read_bytes() == diagram.read_bytes(), (name, fmt, 'diagram changed')
            filename = cwd / (name + '.inspection.json')
            invoke(name + '-save', ['inspect', *command, '--output', filename])
            assert filename.read_bytes() == inspected
            invoke(name + '-no-overwrite', ['inspect', *command, '--output', filename], 1)

        def negative(name, command, code, line=None, column=None):
            actual = invoke(name, command, 1)
            assert not actual.stdout
            diagnostic = json.loads(actual.stderr)
            assert diagnostic['code'] == code, (name, diagnostic)
            if line is not None:
                assert diagnostic['line'] == line, (name, diagnostic)
            if column is not None:
                assert diagnostic['column'] == column, (name, diagnostic)
            return diagnostic

        negative('unavailable-normalized', ['inspect', typed, '--stage', 'normalized'], 'SFI003')
        negative('unsupported-stage', ['inspect', proof, '--stage', 'evaluated'], 'SFI001')
        negative('duplicate-option', ['inspect', proof, '--stage', 'parsed', '--stage', 'parsed'], 'SFI001')
        negative('unsupported-composition', ['inspect', ROOT / 'examples/synthetic/temporal_restricted_entry.yh'], 'SFI002')
        negative('sdk-json-is-not-source', ['inspect', ROOT / 'examples/authoring-consumer/fixtures/section441.document.json'], 'SFI002')
        negative('external-presumption-scenario', ['inspect', presumption, '--scenario', scenario], 'SFI002')
        # A parsed stage succeeds before checking unresolved names or demanding inputs.
        bad = cwd / 'bad.yh'
        bad.write_text(typed.read_text().replace('q:ada = permission(', 'q:ada = unknown('))
        invoke('parse-before-resolve', ['inspect', bad, '--stage', 'parsed'])
        negative('unresolved-name', ['inspect', bad, '--scenario', typed_scenario], 'SFT003', 14, 14)
        bad.write_text(typed.read_text().replace('q:ada = permission(actor:ada,resource:r,kind:read)', 'q:ada = permission(actor:ada,resource:r)'))
        diagnostic = negative('predicate-arity', ['check', bad, '--scenario', typed_scenario], 'SFT004', 14, 14)
        assert diagnostic['related']['line'] == 12
        bad.write_text(typed.read_text().replace('q:ada = permission(actor:ada,', 'q:ada = permission(resource:r,'))
        negative('predicate-type', ['inspect', bad, '--scenario', typed_scenario], 'SFT005', 14, 14)
        missing = cwd / 'missing.yhs'
        missing.write_text('\n'.join(line for line in typed_scenario.read_text().splitlines() if 'actor:ada' not in line))
        negative('missing-classification', ['inspect', typed, '--scenario', missing], 'SFT011', 1)
        bad.write_text(proof.read_text().replace('element conduct', 'element sentence'))
        negative('wrong-declaration-kind', ['inspect', bad, '--scenario', scenario], 'SFE017')
        bad.write_text('model Broken {\n  variant ;\n}')
        negative('parse-location', ['inspect', bad], 'SFE001', 2, 11)
        bad.write_text('model M { purpose "é猫" ! }')
        negative('utf8-error', ['inspect', bad], 'SFE001', 1, 27)
        # Exercise the existing temporal path. Do not introduce a second selector.
        for file in (ROOT / 'examples/synthetic').glob('*.yh'):
            shutil.copyfile(file, cwd / file.name)
        cyclic = cwd / 'presumption_cycle.yh'
        cyclic.write_text(presumption.read_text().replace('trigger f:knowledge', 'trigger f:no-authorization'))
        invoke('presumption-lower-before-validation', ['inspect', cyclic, '--stage', 'lowered'])
        negative('presumption-validate-after-lowering', ['inspect', cyclic, '--stage', 'checked'], 'SFR004')
        temporal = cwd / 'temporal_restricted_entry.yh'
        temporal.write_text(temporal.read_text().replace('effective-from 2024-01-01', 'effective-from 2024-02-01'))
        negative('invalid-interval-gap', ['check', temporal, '--scenario', cwd / 'temporal_at_boundary.yh'], 'SFT005', 3)
        modules = cwd / 'typed-modules'
        shutil.copytree(ROOT / 'examples/typed-finite', modules)
        imported = modules / 'modules/fictional.typed-rules@1.0.0.yh'
        imported.write_text(imported.read_text().replace('possesses(actor:modular-person,item:modular-item)', 'possesses(actor:modular-person)'))
        imported_issue = negative('imported-expression-origin', ['check', modules / 'modular-typed-rules.yh',
            '--scenario', modules / 'modular-typed-rules-scenario.yh'], 'SFT004', 6, 15)
        # Selection now retains the defining origin rather than falling back to
        # the host use-site. Check both real source/token pairs, not a filename.
        vocabulary = modules / 'modules/fictional.typed-vocabulary@1.0.0.yh'
        for location, source, line, column, token in [
                (imported_issue, imported, 6, 15, b'q:modular-possession'),
                (imported_issue['related'], vocabulary, 12, 13, b'possesses')]:
            assert location['path'] == str(source)
            assert (location['line'], location['column']) == (line, column)
            raw = source.read_bytes()
            offset = sum(len(x) + 1 for x in raw.split(b'\n')[:line - 1]) + column - 1
            assert raw[offset:offset + len(token)] == token
        host = modules / 'modular-typed-rules.yh'
        host.write_text(host.read_text().replace('use predicate vocab::possesses', 'use entity vocab::possesses'))
        negative('wrong-reference-kind', ['check', host, '--scenario', modules / 'modular-typed-rules-scenario.yh'], 'SFT014', 10)
        # Broader language witnesses are intentionally separate from inspection's bounded subset.
        capabilities = json.loads((ROOT / 'test/compiler_capabilities.json').read_text())
        for entry in capabilities:
            command = [str(ROOT / arg[1:]) if arg.startswith('@') else arg for arg in entry['command']]
            result = invoke('capability-' + entry['id'], command)
            if args.baseline:
                assert result.stdout == (args.baseline / ('capability-' + entry['id'] + '.stdout')).read_bytes(), entry['id']
        if output:
            (output / 'capabilities.json').write_text(json.dumps(capabilities, indent=2) + '\n')
    print(f'compiler inspection: {len(records)} CLI calls; stage, diagnostics, source mappings, capabilities and compatibility passed')


if __name__ == '__main__':
    main()
