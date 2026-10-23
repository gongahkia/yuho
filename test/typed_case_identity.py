"""Native scoped-observation correspondence, using public CLI/machine entrypoints.

The original reviewer inputs are retained verbatim. Expected tuples are specified
independently of graph key construction; outputs and probes stay outside checkout.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ORIGINAL = {
    'case.yh': """typed-rules-case case:collision model "law.yh" {
 allegation a:visit scenario "mei.yhs";
 allegation a:visit--p:one scenario "ravi.yhs";
}
""",
    'law.yh': """// Fixed PC 2020 RE s319: alternatives and unconsciousness explanation.
// Original source locator: official 21rs8334.pdf, s319. No actual-law applicability selection.
typed-rules-model ClinicShared {
 limit 2048;
 entity-type person;
 entity actor:mei as person;
 entity actor:ravi as person;
 entity patient:lin as person;
 predicate pain(person) kind circumstance;
 predicate disease(person) kind circumstance;
 predicate infirmity(person) kind circumstance;
 predicate unconscious(person) kind circumstance;
 predicate causes(person,person) kind relationship;
 proposition p:one--p:two;
 proposition p:two;
 requirement q:shared-hurt = any(pain(patient:lin),disease(patient:lin),infirmity(patient:lin),unconscious(patient:lin));
 requirement q:mei = all(causes(actor:mei,patient:lin),q:shared-hurt);
 requirement q:ravi = all(causes(actor:ravi,patient:lin),q:shared-hurt);
 rule r:mei establishes proposition p:one--p:two when q:mei;
 rule r:ravi establishes proposition p:two when q:ravi;
 limitation "Only hurt-result definition and externally assessed causal attribution; no s321 fault or offence conclusion.";
}
""",
    'mei.yhs': """typed-rules-scenario Cmei for ClinicShared {
 classify pain(patient:lin) as proved reason "synthetic pain classification";
 classify disease(patient:lin) as not_proved reason "synthetic";
 classify infirmity(patient:lin) as not_proved reason "synthetic";
 classify unconscious(patient:lin) as not_proved reason "synthetic";
 classify causes(actor:mei,patient:lin) as proved reason "separately selected mei context";
 classify causes(actor:ravi,patient:lin) as not_proved reason "separately selected mei context";
}
""",
    'ravi.yhs': """typed-rules-scenario Cravi for ClinicShared {
 classify pain(patient:lin) as proved reason "synthetic pain classification";
 classify disease(patient:lin) as not_proved reason "synthetic";
 classify infirmity(patient:lin) as not_proved reason "synthetic";
 classify unconscious(patient:lin) as not_proved reason "synthetic";
 classify causes(actor:mei,patient:lin) as not_proved reason "separately selected ravi context";
 classify causes(actor:ravi,patient:lin) as proved reason "separately selected ravi context";
}
""",
}
NS = {'g': 'urn:yuho:semantic-graph:v0.2', 's': 'http://www.w3.org/2000/svg'}


def exercise(binary, base):
    commands, summaries = [], []
    base.mkdir(parents=True, exist_ok=True)

    def call(directory, *args, stdin=None, expected=0):
        p = subprocess.run([str(binary), *map(str, args)], cwd=directory,
                           input=stdin, capture_output=True, text=True, timeout=60)
        commands.append(dict(command=p.args, cwd=str(directory), exit=p.returncode,
                             stdin=stdin, stdout=p.stdout, stderr=p.stderr))
        (base/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        assert p.returncode == expected, commands[-1]
        if expected == 0:
            assert not p.stderr, commands[-1]
        return p.stdout if expected == 0 else p.stdout+p.stderr

    def verify(name, files, expected):
        d = base/name
        d.mkdir()
        for n, content in files.items():
            (d/n).write_text(content)
        entry = d/'case.yh'
        assert json.loads(call(d, 'check', entry))['status'] == 'valid'
        raw = call(d, 'run', entry)
        (d/'report.json').write_text(raw)
        report = json.loads(raw)
        backend = sorted((a['id'], p['id'], p['status'], p['state'])
                         for a in report['allegations'] for p in a['result']['propositions'])
        assert backend == sorted(expected), (name, backend, expected)
        for fmt in ('json', 'xml', 'svg'):
            for suffix in ('', '-repeat'):
                call(d, 'diagram', entry, '--view', 'case', '--format', fmt,
                     '--output', d/('graph'+suffix+'.'+fmt))
            assert (d/('graph.'+fmt)).read_bytes() == (d/('graph-repeat.'+fmt)).read_bytes()
        g = json.loads((d/'graph.json').read_text())
        assert g['format'] == 'yuho.semantic-graph/v0.2'
        nodes = g['nodes']
        assert len({n['id'] for n in nodes}) == len(nodes)
        propositions = [n for n in nodes if n['kind'] in ('proposition', 'conflict')]
        actual = sorted((n['boundary'], *n['label'].split('\n')[:1], n['status'],
                         n['label'].split('\n')[1]) for n in propositions)
        assert actual == sorted(expected), (name, actual, expected)
        assert len({n['id'] for n in propositions}) == len(expected)
        # Join using scope + authored proposition, never reconstructed graph IDs.
        for allegation, proposition, status, state in expected:
            matches = [n for n in propositions if n['boundary'] == allegation and
                       n['label'] == proposition+'\n'+state and n['status'] == status]
            assert len(matches) == 1
            node = matches[0]
            # Independently decode the documented pair contract, rather than
            # generating an expected ID with the production key algorithm.
            payload = node['id'].removeprefix('case-proposition:')
            components = []
            for _ in range(2):
                length, payload = payload.split(':', 1)
                size = int(length)
                assert str(size) == length
                components.append(payload[:size])
                payload = payload[size:]
            assert not payload and components == [allegation, proposition]
            relationships = [e for e in g['edges'] if e['from'] == node['id']]
            assert len(relationships) == 1
            edge = relationships[0]
            target = next(n for n in nodes if n['id'] == edge['to'])
            assert edge['kind'] == 'technical-result'
            assert target['kind'] == 'allegation' and target['label'] == allegation
        ids = {n['id'] for n in nodes}
        assert all(e['from'] in ids and e['to'] in ids for e in g['edges'])
        xml = ET.parse(d/'graph.xml').getroot()
        xn = [n.attrib for n in xml.findall('g:nodes/g:node', NS)]
        assert sorted(xn, key=lambda n:n['id']) == sorted(nodes, key=lambda n:n['id'])
        xe = [e.attrib for e in xml.findall('g:edges/g:edge', NS)]
        assert sorted(xe, key=lambda e:tuple(sorted(e.items()))) == sorted(
            g['edges'], key=lambda e:tuple(sorted(e.items())))
        svg = ET.parse(d/'graph.svg').getroot()
        allids = [n.attrib['id'] for n in svg.iter() if 'id' in n.attrib]
        assert len(allids) == len(set(allids))
        groups = {n.attrib['data-semantic-id']: n for n in svg.findall('.//s:g', NS)
                  if 'data-semantic-id' in n.attrib}
        assert set(groups) == ids
        for n in nodes:
            group = groups[n['id']]
            assert group.attrib['data-kind'] == n['kind']
            text = [''.join(t.itertext()) for t in group.findall('s:text', NS)]
            # Wrapping is allowed; nothing essential is truncated. SVG labels use
            # authored identities/scope, rather than the internal pair encoding.
            visible = ''.join(text)
            assert n['label'].replace('\n', '').replace(' ', '') in visible.replace(' ', '')
            if n.get('boundary'):
                assert ('scope:'+n['boundary']).replace(' ', '') in visible.replace(' ', '')
            if n.get('status'):
                assert 'status:'+n['status'] in visible.replace(' ', '')
            width = float(group.attrib['data-width'])
            for t in group.findall('s:text', NS):
                cells = sum(2 if ord(c) >= 0x1100 else 1 for c in (t.text or ''))
                assert cells*8 <= width-32
                assert float(t.attrib['y']) < float(group.attrib['data-y'])+float(group.attrib['data-height'])
        se = sorted((n.attrib['data-from'], n.attrib['data-to'], n.attrib['data-kind'])
                    for n in svg.findall('.//s:g', NS) if 'data-from' in n.attrib)
        assert se == sorted((e['from'], e['to'], e['kind']) for e in g['edges'])
        for route in ('file', 'stdin'):
            req = dict(format='yuho.machine-request/v0.1-experimental', input_kind='native-yh',
                       operation='diagram', path=str(entry), view='case', encoding='json',
                       output=str(d/('machine-'+route+'.json')))
            request = json.dumps(req, ensure_ascii=False)
            if route == 'file':
                (d/'request.json').write_text(request)
                stdout = call(d, 'machine', d/'request.json')
            else:
                stdout = call(d, 'machine', '-', stdin=request)
            response = json.loads(stdout)
            assert response['success'] and response['exports']
            assert response['exports'] == [dict(contract='simplified-semantic-graph',
                                                path=req['output'])]
            assert json.loads((d/('machine-'+route+'.json')).read_text()) == g
            (d/('response-'+route+'.json')).write_text(stdout)
        summaries.append(dict(name=name, observations=expected, node_count=len(propositions),
                              unique_svg_ids=len(allids), deterministic_formats=3, machine_routes=2))
        return g, (d/'graph.svg').read_bytes()

    original_expected = [('a:visit','p:one--p:two','satisfied','established'),
                         ('a:visit','p:two','not_satisfied','not_established'),
                         ('a:visit--p:one','p:one--p:two','not_satisfied','not_established'),
                         ('a:visit--p:one','p:two','satisfied','established')]
    g, svg = verify('reviewer-original', ORIGINAL, original_expected)
    reordered = dict(ORIGINAL)
    reordered['case.yh'] = """typed-rules-case case:collision model "law.yh" {
 allegation a:visit--p:one scenario "ravi.yhs";
 allegation a:visit scenario "mei.yhs";
}
"""
    reverse, reverse_svg = verify('reordered', reordered, original_expected)
    assert sorted(g['nodes'], key=lambda n:n['id']) == sorted(reverse['nodes'], key=lambda n:n['id'])
    assert svg == reverse_svg

    def control(allegations, propositions):
        left, right = propositions
        model = f"""typed-rules-model IndependentSignals {{
 limit 2048;
 entity-type person;
 entity actor:one as person;
 entity actor:two as person;
 predicate signal(person) kind circumstance;
 proposition {left};
 proposition {right};
 requirement q:left = signal(actor:one);
 requirement q:right = signal(actor:two);
 rule r:left establishes proposition {left} when q:left;
 rule r:right establishes proposition {right} when q:right;
 limitation "Synthetic independently scoped signals — 独立 café";
}}
"""
        scenario = """typed-rules-scenario IndependentInput for IndependentSignals {
 classify signal(actor:one) as proved reason "synthetic true — 真";
 classify signal(actor:two) as not_proved reason "synthetic false — 偽";
}
"""
        case = 'typed-rules-case case:independent model "law.yh" {\n'+''.join(
            f' allegation {a} scenario "input.yhs";\n' for a in allegations)+'}\n'
        expected = [(a,p,s,v) for a in allegations for p,s,v in
                    [(left,'satisfied','established'),(right,'not_satisfied','not_established')]]
        return dict(zip(('case.yh','law.yh','input.yhs'),(case,model,scenario))),expected

    for name, allegations, propositions in [
        ('different-values', ['a:scope','a:scope--p:left'], ['p:left--p:right','p:right']),
        ('svg-punctuation', ['a:one-p:two','a:one:p:two'], ['p:left-p:right','p:left:p:right']),
        ('long Unicode 路径', ['a:'+('long-scope-'*10)+'alpha','a:'+('long-scope-'*10)+'beta'],
         ['p:'+('proposition-'*9)+'left','p:'+('proposition-'*9)+'right']),
        ('ordinary', ['a:first','a:second'], ['p:left','p:right'])]:
        files, expected = control(allegations, propositions)
        verify(name, files, expected)
    # The frontend's duplicate-proposition contract refuses unsupported duplicates;
    # the graph builder does not invent a winning observation for them.
    d=base/'duplicate-source';d.mkdir()
    files,_=control(['a:first'],['p:same','p:same'])
    for n,c in files.items(): (d/n).write_text(c)
    failure=json.loads(call(d,'check',d/'case.yh',expected=1))
    assert 'SFT002' in json.dumps(failure)
    result=dict(cases=summaries, cli_calls=len(commands), duplicate_refused=True)
    (base/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', type=Path)
    args=parser.parse_args()
    if args.output:
        exercise(args.binary.resolve(), args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-scoped-identity-') as temp:
            exercise(args.binary.resolve(), Path(temp))
