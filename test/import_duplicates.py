"""R01: duplicate selections retain declaration/use ownership and UTF-8 spans.

Oracles use original fixture bytes and explicit authored markers, never production
source-map helpers, diagnostic text parsing, or inferred unqualified origins.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = {'host.yh': '// host-only padding 00 source authority must not be here\n// host-only padding 01 source authority must not be here\n// host-only padding 02 source authority must not be here\n// host-only padding 03 source authority must not be here\n// host-only padding 04 source authority must not be here\n// host-only padding 05 source authority must not be here\n// host-only padding 06 source authority must not be here\n// host-only padding 07 source authority must not be here\n// host-only padding 08 source authority must not be here\n// host-only padding 09 source authority must not be here\n// host-only padding 10 source authority must not be here\n// host-only padding 11 source authority must not be here\n// host-only padding 12 source authority must not be here\n// host-only padding 13 source authority must not be here\n// host-only padding 14 source authority must not be here\n// host-only padding 15 source authority must not be here\n// host-only padding 16 source authority must not be here\n// host-only padding 17 source authority must not be here\n// host-only padding 18 source authority must not be here\n// host-only padding 19 source authority must not be here\n// host-only padding 20 source authority must not be here\n// host-only padding 21 source authority must not be here\n// host-only padding 22 source authority must not be here\n// host-only padding 23 source authority must not be here\n// host-only padding 24 source authority must not be here\n// host-only padding 25 source authority must not be here\n// host-only padding 26 source authority must not be here\n// host-only padding 27 source authority must not be here\n// host-only padding 28 source authority must not be here\n// host-only padding 29 source authority must not be here\ntyped-rules-model Layout {\n module-root "modules"; import review.policy version 1.0.0 as policy; import review.rival version 2.0.0 as other;\n entity-type person; entity-type event;\n entity actor as person; entity incident as event;\n use predicate policy::permitted; use predicate other::permitted;\n requirement-use q:first from policy::q:gate(actor,incident) assessments scenario;\n requirement-use q:second from policy::q:gate(actor,incident) assessments scenario;\n proposition p; rule r establishes proposition p when all(q:first,q:second);\n limitation "Fictional technical source-location control";\n}', 'modules/review.policy@1.0.0.yh': 'typed-rules-module review.policy version 1.0.0 {\n export requirement-template q:gate; export predicate permitted;\n entity-type person; entity-type event;\n predicate permitted(person,event) kind relationship;\n requirement-template q:gate(var:a as person,var:e as event) = permitted(var:a,var:e);\n}', 'modules/review.rival@2.0.0.yh': '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\ntyped-rules-module review.rival version 2.0.0 {\n export predicate permitted;\n predicate permitted(person,event) kind relationship;\n}', 'project.yh': 'checked-project retest version "yuho.dependency-plan/v0.1-experimental" {\n source src locator "urn:independent:diagnostics";\n scope target actor real:actor context real:incident { identity real:actor nominal person; identity real:incident nominal event; }\n component target profile native-typed model "host.yh" scenario "scenario.yh" scope target { nominal person as person; nominal event as event; entity actor as real:actor; entity incident as real:incident; } rationale "Explicit independent diagnostic test";\n}', 'scenario.yh': 'typed-rules-scenario Inputs for Layout { classify permitted(actor,incident) as proved reason "independent fictional classification"; }'}
SDK_PLAN = {'dependencyFormat': 'yuho.dependency-plan/v0.1-experimental', 'dependencyPlan': {'planBindings': [], 'planCandidates': [], 'planComponents': [{'componentEntities': [['actor', 'real:actor'], ['incident', 'real:incident']], 'componentEntry': None, 'componentIdentity': 'target', 'componentLocation': {'locationColumn': 12, 'locationEnd': 273, 'locationLine': 4, 'locationPath': 'project.yh', 'locationStart': 267}, 'componentModel': 'host.yh', 'componentNominals': [['person', 'person'], ['event', 'event']], 'componentProfile': 'native-typed', 'componentRationale': 'Explicit independent diagnostic test', 'componentScenario': 'scenario.yh', 'componentScope': 'target', 'componentTemplate': None}], 'planIdentity': 'retest', 'planOrigins': [{'originIdentity': 'src', 'originLocator': 'urn:independent:diagnostics'}], 'planScopes': [{'scopeActor': 'real:actor', 'scopeAllegation': None, 'scopeCase': None, 'scopeContext': 'real:incident', 'scopeEntities': [['real:actor', 'person'], ['real:incident', 'event']], 'scopeIdentity': 'target'}]}, 'dependencyProjectSource': 'project.yh'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    out = (args.output or Path(tempfile.mkdtemp(prefix='yuho-import-duplicates-'))).resolve()
    out.mkdir(parents=True, exist_ok=True)
    binary = args.binary.resolve()
    assertions, commands, expectations = [], [], []

    def check(name, value):
        assertions.append({'name': name, 'passed': bool(value)})
        (out / 'assertions.json').write_text(json.dumps(assertions, indent=2))
        assert value, name

    def call(name, argv, expected=1, data=None):
        p = subprocess.run(list(map(str, argv)), input=data, cwd=out, capture_output=True)
        commands.append(dict(name=name, argv=list(map(str, argv)), exit=p.returncode,
                             stdout=p.stdout.decode(), stderr=p.stderr.decode()))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2))
        check(name + ' exit', p.returncode == expected)
        return json.loads(p.stdout or p.stderr)

    def site(files, path, marker, token):
        b, m, t = files[path].encode(), marker.encode(), token.encode()
        check('unambiguous oracle ' + marker, b.count(m) == 1 and m.count(t) == 1)
        offset = b.index(m) + m.index(t)
        prefix = b[:offset]
        return dict(path=path, line=prefix.count(b'\n') + 1,
                    column=len(prefix.rsplit(b'\n', 1)[-1]) + 1,
                    start=offset, end=offset + len(t), token=token)

    def located(name, directory, actual, expected, native=False):
        p = Path(actual['path' if native else 'locationPath'])
        check(name + ' owner', p == (directory / expected['path']) if p.is_absolute()
              else p == Path(expected['path']))
        line = actual['line' if native else 'locationLine']
        column = actual['column' if native else 'locationColumn']
        check(name + ' line/byte-column', (line, column) == (expected['line'], expected['column']))
        b = (directory / expected['path']).read_bytes()
        offset = sum(len(x) + 1 for x in b.split(b'\n')[:line - 1]) + column - 1
        check(name + ' source bytes', b[offset:offset + len(expected['token'].encode())]
              == expected['token'].encode() and b[offset:offset + 9] != b'y padding')
        if not native:
            check(name + ' byte interval', (actual['locationStart'], actual['locationEnd'])
                  == (expected['start'], expected['end']))
            check(name + ' interval bytes', b[actual['locationStart']:actual['locationEnd']]
                  == expected['token'].encode())

    def validate(name, directory, d, code, primary, related, native=False):
        check(name + ' code', d['code' if native else 'dependencyCode'] == code)
        located(name + ' primary', directory, d if native else d['dependencyLocation'], primary, native)
        actual = d.get('related') if native else next(iter(d['dependencyRelated']), None)
        check(name + ' related presence', bool(actual) == bool(related))
        if related:
            located(name + ' related', directory, actual, related, native)

    # This consumer uses only the public source-backed SDK facade.
    p = subprocess.run(['cabal', 'exec', '--offline', '--', 'ghc-9.8.4', '-package=yuho',
                        '-outputdir', str(out / 'sdk-build'), '-o', str(out / 'sdk'),
                        str(ROOT / 'test/ImportDiagnosticClient.hs')], cwd=ROOT, capture_output=True)
    (out / 'sdk-build.log').write_bytes(p.stdout + p.stderr)
    check('public SDK builds', p.returncode == 0)

    def negative(name, files, code, primary, related, all_routes=False):
        directory = out / name
        directory.mkdir()
        for f, source in files.items():
            path = directory / f
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(source.encode())
        expectations.append(dict(case=name, code=code, primary=primary, related=related))
        (out / 'expected-before-execution.json').write_text(json.dumps(expectations, indent=2))
        for op in ['check', 'run']:
            d = call(name + '-native-' + op, [binary, op, directory / 'host.yh',
                     '--scenario', directory / 'scenario.yh'])
            validate(name + '-native-' + op, directory, d, code, primary, related, True)
        d = call(name + '-compose', [binary, 'compose', 'check', directory / 'project.yh'])
        validate(name + '-compose', directory, d, code, primary, related)
        if all_routes:
            dest = out / (name + '-must-not-publish')
            d = call(name + '-compose-run', [binary, 'compose', 'run', directory / 'project.yh',
                     '--output', dest])
            validate(name + '-compose-run', directory, d, code, primary, related)
            check(name + ' no CLI publication', not dest.exists())
            for op in ['check', 'run']:
                for transport in ['file', 'stdin']:
                    dest = out / (name + '-refused-' + op + '-' + transport)
                    request = dict(format='yuho.machine-request/v0.2-experimental',
                                   input_kind='dependency-yh', operation=op,
                                   path=str(directory / 'project.yh'))
                    if op == 'run':
                        request['output'] = str(dest)
                    req = directory / (op + '-' + transport + '.json')
                    req.write_text(json.dumps(request))
                    v = call(name + '-machine-' + op + '-' + transport,
                             [binary, 'machine', '-' if transport == 'stdin' else req],
                             data=req.read_bytes() if transport == 'stdin' else None)
                    check(name + ' truthful failed effects ' + op + transport,
                          v['success'] is False and v['payload'] is None and not v['exports']
                          and v['effects']['source_authority'] == 'not_validated'
                          and v['effects']['evaluation'] in ('none', 'not_reported')
                          and v['effects']['writes'] == 'none' and not dest.exists())
                    validate(name + '-machine', directory, v['diagnostics'][0], code, primary, related)
        document = copy.deepcopy(SDK_PLAN)
        document['dependencySources'] = files
        sdk_input = directory / 'sdk-document.json'
        sdk_input.write_text(json.dumps(document))
        d = call(name + '-sdk', [out / 'sdk', sdk_input])
        validate(name + '-sdk', directory, d, code, primary, related)

    primary = site(ORIGINAL, 'host.yh', 'use predicate other::permitted', 'other::permitted')
    related = site(ORIGINAL, 'host.yh', 'use predicate policy::permitted', 'policy::permitted')
    check('literal original primary', (primary['line'], primary['column'], primary['start'], primary['end'])
          == (35, 49, 2020, 2036))
    check('literal original related', (related['line'], related['column'], related['start'], related['end'])
          == (35, 16, 1987, 2004))
    negative('original-R01', ORIGINAL, 'SFT002', primary, related, True)

    # Every category merged and then checked for unique declaration names.
    # Duplicate requirements already use SFDUPLICATE in scoped expansion.
    categories = [
        ('entity-type', 'extra', 'entity-type extra;'),
        ('entity', 'extra', 'entity extra as person;'),
        ('enum-type', 'choice', 'enum-type choice values first,second;'),
        ('scalar', 'amount', 'scalar amount type integer;'),
        ('predicate', 'allowed', 'predicate allowed(person,event) kind relationship;'),
        ('proposition', 'p:choice', 'proposition p:choice;'),
        ('requirement', 'q:choice', 'requirement q:choice = fact(actor,incident);'),
        ('rule', 'r:choice', 'rule r:choice establishes proposition p:local when q:local;'),
        ('norm', 'n:choice', 'norm n:choice subject actor modality required action proposition p:local when q:local;'),
        ('responsibility-route', 'route:choice', 'responsibility-route route:choice subject actor kind instigation target proposition p:local when q:local;'),
    ]
    module1, module2 = 'modules/control.one@1.0.0.yh', 'modules/control.two@2.3.4.yh'

    def fixture(kind, identifier, declaration):
        return {
            'host.yh': '// é漢🙂 host-only source\n' * 24 + f'''typed-rules-model Layout {{
 module-root "modules"; import control.one version 1.0.0 as first; import control.two version 2.3.4 as second;
 entity-type person; entity-type event; entity actor as person; entity incident as event;
 predicate fact(person,event) kind relationship;
 requirement q:local = fact(actor,incident); proposition p:local;
 rule r:local establishes proposition p:local when q:local;
 limitation "é漢🙂"; use {kind} first::{identifier};
 limitation "Other é漢🙂"; use {kind} second::{identifier};
 limitation "Fictional duplicate ownership control";
}}''',
            module1: f'''typed-rules-module control.one version 1.0.0 {{
 export {kind} {identifier};
 limitation "é漢🙂 module one"; {declaration}
}}''',
            module2: '\n' * 9 + f'''typed-rules-module control.two version 2.3.4 {{
 export {kind} {identifier};
 limitation "Other é漢🙂"; {declaration}
}}''',
            'scenario.yh': 'typed-rules-scenario Inputs for Layout { classify fact(actor,incident) as proved reason "independent control"; }',
            'project.yh': ORIGINAL['project.yh']}

    for kind, identifier, declaration in categories:
        f = fixture(kind, identifier, declaration)
        negative('two-' + kind, f, 'SFDUPLICATE' if kind == 'requirement' else 'SFT002',
                 site(f, 'host.yh', f'use {kind} second::{identifier}', f'second::{identifier}'),
                 site(f, 'host.yh', f'use {kind} first::{identifier}', f'first::{identifier}'),
                 kind in ['predicate', 'requirement'])
        # One imported selection versus a real host declaration. This also
        # detects a legacy fallback replacing the correct related local token
        # by the importing use merely because their unqualified names agree.
        f = fixture(kind, identifier, declaration)
        f['host.yh'] = f['host.yh'].replace('predicate fact(', declaration + ' predicate fact(')
        f['host.yh'] = f['host.yh'].replace(f'use {kind} second::{identifier};', '')
        negative('local-versus-' + kind, f,
                 'SFDUPLICATE' if kind == 'requirement' else 'SFT002',
                 site(f, 'host.yh', f'use {kind} first::{identifier}', f'first::{identifier}'),
                 site(f, 'host.yh', declaration, identifier))

    f = fixture('predicate', 'allowed', 'predicate allowed(person,event) kind relationship;')
    f['host.yh'] = f['host.yh'].replace('predicate fact(', 'predicate allowed(person,event) kind relationship; predicate fact(')
    negative('host-versus-module', f, 'SFT002',
             site(f, 'host.yh', 'use predicate first::allowed', 'first::allowed'),
             site(f, 'host.yh', 'predicate allowed(', 'allowed'), True)
    f = fixture('predicate', 'allowed', 'predicate allowed(person,event) kind relationship;')
    f['host.yh'] = f['host.yh'].replace('second::allowed', 'first::allowed')
    # Same text at distinct use-sites: markers include each different prefix.
    negative('repeated-selection', f, 'SFT002',
             site(f, 'host.yh', 'limitation "Other é漢🙂"; use predicate first::allowed', 'first::allowed'),
             site(f, 'host.yh', 'limitation "é漢🙂"; use predicate first::allowed', 'first::allowed'), True)
    f = fixture('predicate', 'allowed', 'predicate allowed(person,event) kind relationship;')
    other = 'modules/control.one@2.3.4.yh'
    f[other] = f.pop(module2).replace('control.two', 'control.one')
    f['host.yh'] = f['host.yh'].replace('import control.two', 'import control.one')
    negative('exact-version', f, 'SFT002',
             site(f, 'host.yh', 'use predicate second::allowed', 'second::allowed'),
             site(f, 'host.yh', 'use predicate first::allowed', 'first::allowed'), True)
    f = fixture('predicate', 'allowed', 'predicate allowed(person,event) kind relationship;')
    f[module2] += ''  # Identical module-relative coordinates in the two owners.
    f[module2] = f[module1].replace('control.one', 'control.two').replace('1.0.0', '2.3.4')
    negative('equal-module-coordinates', f, 'SFT002',
             site(f, 'host.yh', 'use predicate second::allowed', 'second::allowed'),
             site(f, 'host.yh', 'use predicate first::allowed', 'first::allowed'))
    # Invalid original module: both relevant tokens belong to that module.
    f = fixture('predicate', 'allowed', 'predicate allowed(person,event) kind relationship;')
    f['host.yh'] = f['host.yh'].replace('use predicate first::allowed;', '')
    f[module2] = f[module2].replace('kind relationship;', 'kind relationship;\n predicate allowed(person,event) kind circumstance;')
    negative('module-internal', f, 'SFT002',
             site(f, module2, 'predicate allowed(person,event) kind circumstance', 'allowed'),
             site(f, module2, 'predicate allowed(person,event) kind relationship', 'allowed'), True)
    f = fixture('requirement', 'q:choice', 'requirement q:choice = fact(actor,incident);')
    f['host.yh'] = f['host.yh'].replace('use requirement first::q:choice;', '')
    f[module2] = f[module2].replace('fact(actor,incident);',
        'fact(actor,incident);\n requirement q:choice = not(fact(actor,incident));')
    negative('module-internal-requirement', f, 'SFDUPLICATE',
             site(f, module2, 'requirement q:choice = not', 'q:choice'),
             site(f, module2, 'requirement q:choice = fact', 'q:choice'))
    # Word identifiers are ASCII in this source surface. The independent UTF-8
    # oracle is exercised by the multibyte string prefixes in every fixture.
    f = fixture('predicate', 'allowed--x', 'predicate allowed--x(person,event) kind relationship;')
    negative('delimiter-declaration', f, 'SFT002',
             site(f, 'host.yh', 'use predicate second::allowed--x', 'second::allowed--x'),
             site(f, 'host.yh', 'use predicate first::allowed--x', 'first::allowed--x'), True)

    # Import aliases/identities are checked before merging; no foreign tokens.
    f = fixture('predicate', 'allowed', 'predicate allowed(person,event) kind relationship;')
    f['host.yh'] = f['host.yh'].replace('as second;', 'as first;')
    negative('duplicate-alias', f, 'SFT002',
             site(f, 'host.yh', 'import control.two version 2.3.4 as first', 'first'), None)
    f = fixture('predicate', 'allowed', 'predicate allowed(person,event) kind relationship;')
    f['host.yh'] = f['host.yh'].replace('control.two version 2.3.4', 'control.one version 1.0.0')
    negative('duplicate-module-identity', f, 'SFT002',
             site(f, 'host.yh', 'import control.one version 1.0.0 as second', 'control.one'),
             site(f, 'host.yh', 'import control.one version 1.0.0 as first', 'control.one'))

    # Valid disjoint exports: compare technical observations to independent T.
    f = fixture('proposition', 'p:choice', 'proposition p:choice;')
    f[module2] = f[module2].replace('p:choice', 'p:other')
    f['host.yh'] = f['host.yh'].replace('second::p:choice', 'second::p:other')
    directory = out / 'valid-disjoint'
    for name, text in f.items():
        p = directory / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode())
    v = call('valid-disjoint-run', [binary, 'run', directory / 'host.yh', '--scenario', directory / 'scenario.yh'], 0)
    check('independent true result', next(x for x in v['expressions'] if x['id'] == 'q:local')['status'] == 'satisfied')
    call('valid-disjoint-check', [binary, 'compose', 'check', directory / 'project.yh'], 0)
    dest, replay = out / 'valid-export', out / 'valid-replay'
    call('valid-disjoint-export', [binary, 'compose', 'run', directory / 'project.yh', '--output', dest], 0)
    call('valid-disjoint-replay', [binary, 'compose', 'replay', dest / 'artifact.json', '--output', replay], 0)
    check('eight identical replay files', len(list(dest.iterdir())) == 8
          and all(p.read_bytes() == (replay / p.name).read_bytes() for p in dest.iterdir()))
    # Priorities have edge semantics: repeated edges remain admitted, rather
    # than being incorrectly treated as duplicate named declarations.
    f = fixture('priority', 'r:local', 'priority r:local over r:lower;')
    f['host.yh'] = f['host.yh'].replace('limitation "Fictional duplicate ownership control";',
        'rule r:lower defeats proposition p:local when q:local; limitation "Fictional duplicate ownership control";')
    directory = out / 'valid-priority-edges'
    for name, text in f.items():
        p = directory / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode())
    call('valid-priority-edges', [binary, 'run', directory / 'host.yh', '--scenario', directory / 'scenario.yh'], 0)
    call('valid-priority-project', [binary, 'compose', 'check', directory / 'project.yh'], 0)
    (out / 'summary.json').write_text(json.dumps(dict(assertions=len(assertions), invocations=len(commands),
                                                    negative_groups=len(expectations), output=str(out)), indent=2))
    print((out / 'summary.json').read_text())


if __name__ == '__main__':
    main()
