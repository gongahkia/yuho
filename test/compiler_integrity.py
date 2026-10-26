"""Deterministic byte/parser, lowering and export regressions; no external dependencies.

All generated sources, binaries, command transcripts and actual outputs live outside
this checkout. Expected statuses and byte coordinates are constructed independently.
"""
import argparse
import collections
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SEED = 0x5955484F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    out = args.output or Path(tempfile.mkdtemp(prefix='yuho-compiler-integrity-'))
    out.mkdir(parents=True, exist_ok=True)
    binary = args.binary.resolve()
    calls, checks = [], []

    def check(name, condition):
        assert condition, name
        checks.append(name)

    def call(argv, expected=0, data=None, timeout=20):
        p = subprocess.run(list(map(str, argv)), input=data, capture_output=True,
                           cwd=ROOT, timeout=timeout)
        calls.append(dict(argv=list(map(str, argv)), exit=p.returncode,
                          stdout=p.stdout.decode('utf-8', 'replace'),
                          stderr=p.stderr.decode('utf-8', 'replace')))
        (out / 'commands.json').write_text(json.dumps(calls, indent=2) + '\n')
        check('exit: ' + ' '.join(map(str, argv[1:3])), p.returncode == expected)
        return p

    client = out / 'parser-probe'
    call(['cabal', 'exec', '--offline', '--', 'ghc-9.8.4', '-Wall', '-Werror',
          '-package=yuho', '-outputdir', out / 'build', '-o', client,
          ROOT / 'test/CompilerIntegrityClient.hs'], timeout=120)
    rng = random.Random(SEED)
    cases, expectations = [], {}

    def add(data, expected=None):
        i = len(cases)
        cases.append(data)
        if expected is not None:
            expectations[i] = expected
        return i

    def lexical(words):
        data, expected = b'', []
        for kind, value in words:
            raw = ('"' + value + '"' if kind == 'StringToken' else value).encode()
            expected.append([kind, value, data.count(b'\n') + 1,
                             len(data.rsplit(b'\n', 1)[-1]) + 1])
            data += raw + rng.choice([b' ', b'\t', b'\n', ' // 注释😀\n'.encode()])
        expected.append(['EndToken', '', data.count(b'\n') + 1,
                         len(data.rsplit(b'\n', 1)[-1]) + 1])
        add(data, expected)

    lexical([])
    for _ in range(100):
        lexical([rng.choice([('WordToken', 'abc:12/9.-_'), ('StringToken', ''),
                             ('StringToken', 'é中文😀 // &<>'), ('StringToken', '}'),
                             ('SymbolToken', ';'), ('SymbolToken', '{')])
                 for _ in range(rng.randrange(1, 60))])
    add(b'abc//tail', [['WordToken', 'abc//tail', 1, 1], ['EndToken', '', 1, 10]])
    add(b';//tail', [['SymbolToken', ';', 1, 1], ['EndToken', '', 1, 8]])
    add(b'123abc -1 1.2', [['WordToken', '123abc', 1, 1], ['WordToken', '-1', 1, 8],
                            ['WordToken', '1.2', 1, 11], ['EndToken', '', 1, 14]])
    invalid_utf8 = [bytes([i]) for i in range(128, 256)] + [b'\xc0\xaf', b'\xe2\x82',
        b'\xf0\x9f\x98', b'\xed\xa0\x80', b'\xf4\x90\x80\x80', b'\xe2(\xa1']
    utf8_ids = [add(x) for x in invalid_utf8]
    invalid_lex = [b'\r\n', b'\0', b'"unterminated', b'"a\\"b"', b'//x\0', b'//x\r', b'@', b'"x\ny"']
    bad_ids = [add(x) for x in invalid_lex]
    limit_ids = [(add(b';' * n + suffix), n) for n in [4095, 4096, 4097, 4098]
                 for suffix in [b'', b' ', b'\n', b'//end']]
    size_ids = [(add(b' ' * n), n) for n in [65535, 65536, 65537]]
    add(b'a' * 65536, [['WordToken', 'a' * 65536, 1, 1], ['EndToken', '', 1, 65537]])
    for _ in range(750):
        add(rng.randbytes(rng.randrange(0, 257)))
    proof = (ROOT / 'examples/synthetic/restricted_entry.yh').read_bytes()
    typed = (ROOT / 'test/fixtures/typed-authoring/permission.yh').read_bytes()
    presumption = (ROOT / 'examples/synthetic/presumption_active.yh').read_bytes()
    valid = [add(proof), add(typed), add(presumption)]
    quoted_syntax = []
    for source, parser, keyword in [(proof, 0, b'variant'), (typed, 4, b'limit'),
                                    (presumption, 3, b'base-model')]:
        if source.startswith(b'//'):
            source = source.split(b'\n', 1)[1]
        for needle in [keyword, b'{', b';', b'}']:
            quoted_syntax.append((add(source.replace(needle, b'"'+needle+b'"', 1)), parser))
    truncated = []
    trailing = []
    for source, parser in [(proof, 0), (typed, 4), (presumption, 3)]:
        for cut in sorted(set([0, 1, len(source.rstrip()) - 1] +
                              [rng.randrange(len(source.rstrip())) for _ in range(80)])):
            truncated.append((add(source[:cut]), parser))
        for suffix in [b'word', b'}', b'""', b';']:
            trailing.append((add(source + suffix), parser))
        for _ in range(150):
            at = rng.randrange(len(source))
            mode = rng.randrange(3)
            if mode == 0:
                add(source[:at] + rng.choice([b'{', b'}', b';', b'"', b',', b'()']) + source[at:])
            elif mode == 1:
                add(source[:at] + source[at+1:])
            else:
                add(source[:at] + source[at:at+20] * 4 + source[at+20:])
    # Bounded nested expression syntax, repeated blocks and unknown references.
    for depth in [1, 16, 32, 64, 128, 512, 1000]:
        add(typed.replace(b'permission(actor:ada,resource:r,kind:read);',
            b'not(' * depth + b'permission(actor:ada,resource:r,kind:read)' + b')' * depth + b';', 1))
    for n in [2, 20, 200]:
        add(typed.replace(b' entity-type actor;', b' entity-type actor;' * n))
    add(typed.replace(b'when q:ada', b'when q:missing'))
    wire = b'\n'.join(x.hex().encode() for x in cases) + b'\n'
    (out / 'fuzz-inputs.hex').write_bytes(wire)
    first = call([client], data=wire, timeout=60).stdout
    second = call([client], data=wire, timeout=60).stdout
    check('deterministic fully forced parser/lexer outcomes', first == second)
    (out / 'fuzz-results.jsonl').write_bytes(first)
    results = [json.loads(x) for x in first.splitlines()]
    check('one outcome per input', len(results) == len(cases))
    for i, tokens in expectations.items():
        check('independent lexical token/byte coordinates ' + str(i), results[i]['lexer'] == tokens)
    for i in utf8_ids + bad_ids:
        check('invalid bytes/lexical syntax refused ' + str(i), isinstance(results[i]['lexer'], dict))
    for i, n in limit_ids:
        lex = results[i]['lexer']
        check('token bound ' + str(i), (isinstance(lex, list) and len(lex) == n + 1) if n <= 4096
              else lex['code'] == 'SFE016' and lex['column'] == 4097)
    for i, n in size_ids:
        check('byte bound ' + str(n), isinstance(results[i]['lexer'], list) if n <= 65536
              else results[i]['lexer']['code'] == 'SFE016')
    for i, parser in truncated + trailing + quoted_syntax:
        check('no truncated/trailing acceptance ' + str(i), 'code' in results[i]['parsers'][parser])
    for i, parser in zip(valid, [0, 4, 3]):
        check('valid seed parses', 'ast_show_length' in results[i]['parsers'][parser])
    # Independently recover the exact original token byte slice for every successful lex.
    for data, result in zip(cases, results):
        if not isinstance(result['lexer'], list):
            continue
        lines = data.split(b'\n')
        for kind, value, line, column in result['lexer']:
            offset = sum(len(x) + 1 for x in lines[:line-1]) + column - 1
            raw = ('"' + value + '"' if kind == 'StringToken' else value).encode()
            check('original byte slice', data[offset:offset+len(raw)] == raw)
            if kind == 'EndToken':
                check('EOF byte offset', offset == len(data))

    scenario = ROOT / 'examples/synthetic/scenario_all_proved.yh'
    for name, src, needle in [('keyword', proof, b'variant'), ('delimiter', proof, b'{')]:
        path = out / (name + '.yh')
        path.write_bytes(src.replace(needle, b'"' + needle + b'"', 1))
        p = call([binary, 'check', path, '--scenario', scenario], 1)
        d = json.loads(p.stderr)
        offset = path.read_bytes().index(b'"' + needle + b'"')
        prefix = path.read_bytes()[:offset]
        check('quoted syntax diagnostic owns exact token', d['path'] == str(path) and
              (d['line'], d['column']) == (prefix.count(b'\n')+1, len(prefix.rsplit(b'\n', 1)[-1])+1))
    brace = out / 'brace-label.yh'
    brace.write_bytes(proof.replace(b'Fictional, non-authoritative compiler and kernel conformance fixture only', b'}'))
    call([binary, 'check', brace, '--scenario', scenario])
    req = out / 'bad-request.yh'
    req.write_bytes(proof.replace(b'request S00;', b'request ReviewA;'))
    for op in ['check', 'compile']:
        p = call([binary, op, req, '--scenario', scenario], 1)
        d = json.loads(p.stderr)
        check('bad request diagnosed in model', d['path'] == str(req) and d['code'] == 'SFE004'
              and req.read_bytes().splitlines()[d['line']-1][d['column']-1:].startswith(b'ReviewA'))
    # The remaining source entrances use private parsers behind their public CLI.
    for name, prefix, command in [
        ('temporal', 'temporal-model M', ['check']),
        ('module', 'modular-model M', ['check']),
        ('computed', 'computed-project M', ['compose', 'check']),
        ('dependency', 'checked-project M version "yuho.dependency-plan/v0.1-experimental"', ['compose', 'check'])]:
        path = out / (name+'-quoted.yh')
        path.write_text(prefix+' "{" }')
        refused = call([binary, *command, path], 1)
        check('wrapper quoted opening delimiter '+name, b'expected {' in refused.stderr)
    # A modular source request error belongs to its original model, not the host.
    module = out / 'integrity@1.0.0.yh'
    module.write_text('statutory-module integrity version 1.0.0 { '
        'export model FictionalRestrictedAreaEntry-v0.1; source-model "bad-request.yh"; }')
    host = out / 'request-host.yh'
    host.write_text('modular-model Host { module-root "."; import integrity version 1.0.0 as m; '
                    'use model m::FictionalRestrictedAreaEntry-v0.1; }')
    d = json.loads(call([binary, 'check', host, '--scenario', scenario], 1).stderr)
    check('imported request owner retained', Path(d['path']).resolve() == req.resolve()
          and req.read_bytes().splitlines()[d['line']-1][d['column']-1:].startswith(b'ReviewA'))

    # Finite counting oracle: enumerate independent T/F/U cases before invoking Yuho.
    model = ('typed-rules-model M { limit 2048; entity-type t; entity a as t; '
             'predicate p(t) kind conduct; predicate q(t) kind conduct; proposition p:x; '
             'requirement q:x = %s %s (p(a),q(a)); '
             'rule r:x establishes proposition p:x when q:x; limitation "fictional"; }')
    m, s = out / 'finite.yh', out / 'finite.yhs'
    kernel = subprocess.check_output(['cabal', 'list-bin', 'exe:yuho-kernel', '--offline'], cwd=ROOT, text=True).strip()
    oracle_rows = []
    for op, n, values in itertools.product(['at-least', 'at-most', 'exactly'], [0, 1, 2, 3, 2048], itertools.product([0, 1, None], repeat=2)):
        low = sum(v == 1 for v in values)
        high = low + values.count(None)
        possible = [int({'at-least': count >= n, 'at-most': count <= n, 'exactly': count == n}[op])
                    for count in range(low, high+1)]
        expected = 'satisfied' if all(possible) else 'not_satisfied' if not any(possible) else 'unresolved'
        m.write_text(model % (op, n))
        status = {0: 'not_proved', 1: 'proved', None: 'unresolved'}
        s.write_text('typed-rules-scenario S for M { ' + ' '.join(
            f'classify {pred}(a) as {status[v]} reason "synthetic";' for pred, v in zip(['p', 'q'], values)) + ' }')
        p = call([binary, 'run', m, '--scenario', s])
        actual = json.loads(p.stdout)
        check('finite oracle', actual['expressions'][0]['status'] == expected)
        oracle_rows.append(dict(operation=op, threshold=n, inputs=values, expected=expected))
    # An independently assembled public wire request, not the source encoder's request.
    reference = dict(protocol='yuho.kernel-protocol/v1', input_schema='yuho.kernel-input/v1',
        operation='evaluate', fragment='TypedFiniteRules-v1', request_id='M-request', policy={'max_nodes': 2048},
        program=dict(id='M', entity_types=['t'], entities=[{'id':'a','type':'t'}],
          predicates=[{'id':x,'arguments':['t'],'kind':'conduct'} for x in ['p','q']],
          scalars=[], propositions=['p:x'], requirements=[{'id':'q:x','expression':{'kind':'at-least','threshold':1,
             'members':[{'kind':'predicate','predicate':x,'arguments':[{'kind':'entity','id':'a'}]} for x in ['p','q']]}}],
          rules=[{'id':'r:x','parameters':[],'polarity':'establish','conclusion':'p:x','body':{'kind':'reference','id':'q:x'}}],
          priorities=[], facts=[{'predicate':x,'arguments':['a'],'status':'satisfied','reason':'synthetic'} for x in ['p','q']],
          values=[], limitations=['fictional']))
    m.write_text(model % ('at-least', 1))
    s.write_text('typed-rules-scenario S for M { classify p(a) as proved reason "synthetic"; classify q(a) as proved reason "synthetic"; }')
    compiled = call([binary, 'compile', m, '--scenario', s]).stdout
    check('independently assembled request equals lowered request', json.loads(compiled) == reference)
    expected_response = call([kernel], data=json.dumps(reference).encode()+b'\n').stdout
    check('independent kernel request and source execution byte parity', call([binary, 'run', m, '--scenario', s]).stdout == expected_response)
    (out / 'independent-request.json').write_text(json.dumps(reference, indent=2)+'\n')
    (out / 'independent-response.json').write_bytes(expected_response)
    # Unrelated declaration order and consistent renaming preserve observed semantics.
    m.write_text((model % ('at-least', 1)).replace('predicate p(t) kind conduct; predicate q(t) kind conduct;',
        'predicate q(t) kind conduct; predicate p(t) kind conduct;'))
    reordered = json.loads(call([binary, 'run', m, '--scenario', s]).stdout)
    check('unrelated declaration reordering', reordered['expressions'] == json.loads(expected_response)['expressions'])
    m.write_text((model % ('at-least', 1)).replace('q:x', 'q:renamed'))
    renamed = json.loads(call([binary, 'run', m, '--scenario', s]).stdout)
    check('consistent identifier rename', renamed['expressions'][0]['id'] == 'q:renamed' and renamed['expressions'][0]['status'] == 'satisfied')
    for n in [-1, 2049, 2**63, 2**64, -(2**64), 10**100]:
        m.write_text(model % ('at-least', n))
        for op in ['check', 'compile', 'run']:
            d = json.loads(call([binary, op, m, '--scenario', s], 1).stderr)
            check('threshold refusal at exact authored number', d['code'] == 'SFT009' and d['path'] == str(m)
                  and m.read_text().splitlines()[d['line']-1][d['column']-1:].startswith(str(n)))
    # XML/SVG escaping and semantic identity, category and endpoint equivalence.
    m.write_bytes(typed.replace(b'when q:ada;', 'when q:ada citation "<&\'中文😀>";'.encode()))
    ts = ROOT / 'test/fixtures/typed-authoring/permission.yhs'
    artifacts = {}
    for fmt in ['json', 'xml', 'svg']:
        dest = out / ('equivalence.'+fmt)
        call([binary, 'diagram', m, '--scenario', ts, '--view', 'trace', '--format', fmt, '--output', dest])
        repeat = out / ('equivalence-repeat.'+fmt)
        call([binary, 'diagram', m, '--scenario', ts, '--view', 'trace', '--format', fmt, '--output', repeat])
        check('deterministic export '+fmt, dest.read_bytes() == repeat.read_bytes())
        artifacts[fmt] = dest
    graph = json.loads(artifacts['json'].read_bytes())
    xml, svg = ET.parse(artifacts['xml']), ET.parse(artifacts['svg'])
    xn = xml.findall('.//{urn:yuho:semantic-graph:v0.2}node')
    check('XML node identities', {n.attrib['id'] for n in xn} == {n['id'] for n in graph['nodes']})
    for n in xn:
        j = next(j for j in graph['nodes'] if j['id'] == n.attrib['id'])
        for key in ['kind','label','citation','status','boundary']:
            check('XML node value '+key, n.attrib.get(key) == j.get(key))
        obs = j.get('observation', {})
        for key in ['evaluation','technical_value','branch_reason','skip_reason']:
            check('XML observation '+key, n.attrib.get(key.replace('_','-')) == obs.get(key))
    edge_keys = lambda rows: collections.Counter(tuple(r[k] for k in ['from','to','kind','label']) for r in rows)
    check('XML full edge multiset', edge_keys([e.attrib for e in xml.findall('.//{urn:yuho:semantic-graph:v0.2}edge')]) == edge_keys(graph['edges']))
    sn = [x for x in svg.iter() if 'data-semantic-id' in x.attrib]
    check('SVG semantic node identities', {n.attrib['data-semantic-id'] for n in sn} == {n['id'] for n in graph['nodes']})
    ids = [x.attrib['id'] for x in svg.iter() if 'id' in x.attrib]
    check('injective DOM IDs', len(ids) == len(set(ids)))
    se = [x.attrib for x in svg.iter() if 'data-from' in x.attrib]
    check('SVG edge endpoint/category multiset', collections.Counter((e['data-from'],e['data-to'],e['data-kind']) for e in se) ==
          collections.Counter((e['from'],e['to'],e['kind']) for e in graph['edges']))
    check('no injected or external elements', all(x.tag.split('}')[-1] not in ['script','image','foreignObject','use'] for x in svg.iter()))
    for n in sn:
        j = next(j for j in graph['nodes'] if j['id'] == n.attrib['data-semantic-id'])
        check('SVG node kind', n.attrib['data-kind'] == j['kind'])
        for key, val in j.get('observation', {}).items():
            check('SVG technical observation', n.attrib[key.replace('_','-')] == val)
    # Unsupported XML characters must refuse before publication; JSON retains them.
    m.write_bytes(typed.replace(b'when q:ada;', b'when q:ada citation "bad\x01citation";'))
    for fmt in ['svg','xml']:
        dest = out / ('forbidden.'+fmt)
        d = json.loads(call([binary, 'diagram', m, '--scenario', ts, '--view', 'trace', '--format', fmt, '--output', dest], 1).stderr)
        check('no invalid '+fmt+' publication', not dest.exists() and d['code'] == 'SFD001')
    req = dict(format='yuho.machine-request/v0.1-experimental', input_kind='native-yh', operation='diagram', path=str(m),
               scenario=str(ts), output=str(out/'machine-forbidden.svg'), view='trace', encoding='svg')
    result = json.loads(call([binary, 'machine', '-'], 1, json.dumps(req).encode()).stdout)
    check('machine does not claim failed export success', result['success'] is False and not (out/'machine-forbidden.svg').exists())
    (out/'oracles.json').write_text(json.dumps(oracle_rows, indent=2)+'\n')
    summary = dict(seed=SEED, byte_inputs=len(cases), parser_entrances=6, finite_oracles=len(oracle_rows),
                   assertions=len(checks), commands=len(calls), passed=True)
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
