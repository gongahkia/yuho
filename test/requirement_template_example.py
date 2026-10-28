"""Local requirement templates: the retained example parses, expands and evaluates.

Oracles are the authored example bytes and expected statuses written here, never
production helpers. Each negative mutation names the refusing diagnostic code.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/typed-finite-templates'
MODEL = EXAMPLE / 'workplace-safety.yh'
SCENARIO = EXAMPLE / 'workplace-safety-scenario.yh'
EXPECTED_EXPRESSIONS = {
    'q:ana-unprotected': 'satisfied', 'q:ben-unprotected': 'not_satisfied',
    'q:ana-trained': 'satisfied', 'q:ben-trained': 'not_satisfied',
    'q:any-unprotected': 'satisfied', 'q:any-untrained': 'satisfied',
    'q:small-employer': 'not_satisfied'}
EXPECTED_RULES = {'r:s12-equipment': 'satisfied', 'r:s12-small-employer': 'not_satisfied',
                  'r:s14-training': 'satisfied'}
EXPECTED_PROPOSITIONS = {'p:s12-equipment-contravention': 'established',
                         'p:s14-training-contravention': 'established'}
USES = ['q:ana-unprotected', 'q:ben-unprotected', 'q:ana-trained', 'q:ben-trained']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    out = (args.output or Path(tempfile.mkdtemp(prefix='yuho-requirement-template-'))).resolve()
    out.mkdir(parents=True, exist_ok=True)
    binary = args.binary.resolve()
    model_text, scenario_text = MODEL.read_text(), SCENARIO.read_text()
    assertions = []

    def check(name, value):
        assertions.append({'name': name, 'passed': bool(value)})
        (out / 'assertions.json').write_text(json.dumps(assertions, indent=2))
        assert value, name

    def call(name, argv, expected=0):
        p = subprocess.run([str(binary)] + list(map(str, argv)), cwd=out, capture_output=True)
        check(name + ' exit', p.returncode == expected)
        return p.stdout.decode() or p.stderr.decode()

    def json_call(name, argv, expected=0):
        return json.loads(call(name, argv, expected))

    def variant(name, model=None, scenario=None):
        folder = out / name
        folder.mkdir()
        (folder / 'm.yh').write_text(model_text if model is None else model)
        (folder / 's.yh').write_text(scenario_text if scenario is None else scenario)
        return folder / 'm.yh', folder / 's.yh'

    with_scenario = ['--scenario', SCENARIO]
    check('check valid', json_call('check', ['check', MODEL] + with_scenario)
          == {'kind': 'typed-finite-rules', 'status': 'valid'})

    result = json_call('run', ['run', MODEL] + with_scenario)
    check('expanded expression statuses',
          {e['id']: e['status'] for e in result['expressions']} == EXPECTED_EXPRESSIONS)
    check('rule statuses', {r['id']: r['status'] for r in result['rules']} == EXPECTED_RULES)
    check('proposition states',
          {p['id']: p['state'] for p in result['propositions']} == EXPECTED_PROPOSITIONS)

    call('compile first', ['compile', MODEL] + with_scenario + ['--output', out / 'request-a.json'])
    call('compile second', ['compile', MODEL] + with_scenario + ['--output', out / 'request-b.json'])
    request_bytes = (out / 'request-a.json').read_bytes()
    check('deterministic compile', request_bytes == (out / 'request-b.json').read_bytes())
    request = json.loads(request_bytes)
    check('typed kernel fragment', request['fragment'] == 'TypedFiniteRules-v1')
    requirements = {r['id']: r['expression'] for r in request['program']['requirements']}
    check('every use is an ordinary requirement', all(u in requirements for u in USES))
    check('no template construct reaches the kernel', 'template' not in request_bytes.decode())
    ana = requirements['q:ana-unprotected']
    check('unprotected body expanded with actual arguments',
          ana['kind'] == 'all' and json.dumps(ana).count('worker:ana') == 3
          and 'var:' not in json.dumps(ana))
    check('quantified body keeps its own bound variable',
          requirements['q:ben-trained']['kind'] == 'forall'
          and 'worker:ben' in json.dumps(requirements['q:ben-trained']))

    explanation = call('explain', ['explain', MODEL] + with_scenario)
    check('explanation shows expanded body',
          'Requirement q:ana-unprotected: satisfied — all(assigned-hazardous(org:acme,worker:ana)' in explanation)

    call('diagram svg', ['diagram', MODEL] + with_scenario
         + ['--view', 'rule', '--format', 'svg', '--output', out / 'rule.svg'])
    check('svg emitted', (out / 'rule.svg').read_bytes().startswith(b'<?xml'))
    call('diagram json', ['diagram', MODEL] + with_scenario
         + ['--view', 'rule', '--format', 'json', '--output', out / 'rule.json'])
    graph = json.loads((out / 'rule.json').read_bytes())
    check('each use is a diagram node',
          all('finite-requirement:' + u in {n['id'] for n in graph['nodes']} for u in USES))

    parsed = json_call('inspect parsed', ['inspect', MODEL, '--stage', 'parsed'])['stages'][0]['data']
    check('parsed templates and uses', len(parsed['scoped_templates']) == 2 and len(parsed['scoped_uses']) == 4)
    check('checked inspection remains explicitly unsupported',
          json_call('inspect checked', ['inspect', MODEL] + with_scenario + ['--stage', 'checked'], 1)['code'] == 'SFI002')
    check('scenario is required',
          json_call('check without scenario', ['check', MODEL], 1)['code'] == 'SFT011')

    revised_model, revised_scenario = variant('revised-scenario', scenario=scenario_text.replace(
        'trained-for(worker:ben,task:welding) as not_proved', 'trained-for(worker:ben,task:welding) as proved'))
    revised = json_call('revised run', ['run', revised_model, '--scenario', revised_scenario])
    check('scenario revision changes only the training route',
          {p['id']: p['state'] for p in revised['propositions']}
          == {'p:s12-equipment-contravention': 'established', 'p:s14-training-contravention': 'not_established'})

    negatives = [
        ('capture', 'not(provided-equipment(var:employer,var:worker))', 'not(provided-equipment(org:acme,var:worker))', 'SFCAPTURE'),
        ('recursion', '= forall var:task as task (trained-for(var:worker,var:task));', '= q:fully-trained;', 'SFCAPTURE'),
        ('free-variable', 'trained-for(var:worker,var:task)', 'trained-for(var:other,var:task)', 'SFT006'),
        ('missing-argument', 'q:fully-trained(worker:ana)', 'q:fully-trained()', 'SFARITY'),
        ('wrong-role', 'q:unprotected-assignment(org:acme,worker:ana)', 'q:unprotected-assignment(worker:ana,org:acme)', 'SFT005'),
        ('unknown-template', 'from q:fully-trained(worker:ben)', 'from q:fully-qualified(worker:ben)', 'SFNAME'),
        ('duplicate-use', 'requirement-use q:ben-trained', 'requirement-use q:ana-trained', 'SFDUPLICATE'),
    ]
    for name, old, new, code in negatives:
        check(name + ' mutation applies', old in model_text)
        m, s = variant(name, model=model_text.replace(old, new))
        check(name + ' refused', json_call(name, ['check', m, '--scenario', s], 1)['code'] == code)
    m, s = variant('missing-classification', scenario=scenario_text.replace(
        '  classify trained-for(worker:ben,task:welding) as not_proved reason "synthetic supplied classification";\n', ''))
    check('missing ground classification refused',
          json_call('missing-classification', ['check', m, '--scenario', s], 1)['code'] == 'SFT011')
    print('requirement template example: parse, expansion, evaluation, compile, explain, diagram and refusals passed')


if __name__ == '__main__':
    main()
