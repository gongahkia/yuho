"""Regression oracles for case authority and bounded graph validation.

Seeded source programs and independent kernel requests are constructed here.
All inputs, expected outcomes, actual outputs and transcripts are retained outside
this checkout. No production lowering helper constructs the reference requests.
"""
import argparse
import copy
import json
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SEED = 0x59483236
MODEL = 'typed-rules-model M {\n entity-type t; entity a as t; predicate p(t) kind conduct;\n requirement q:x = p(a); proposition p:x;\n rule r:x establishes proposition p:x when q:x;\n limitation "fictional";\n}\n'
SCENARIO = 'typed-rules-scenario S for M {\n classify p(a) as proved reason "synthetic";\n}\n'
CASE = 'typed-rules-case C model "model.yh" {\n allegation a scenario "scenario.yhs";\n}\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    out = args.output or Path(tempfile.mkdtemp(prefix='yuho-hardening-'))
    out.mkdir(parents=True, exist_ok=True)
    y = str(args.binary.resolve())
    kernel = subprocess.check_output(['cabal', 'list-bin', 'exe:yuho-kernel', '--offline'], cwd=ROOT, text=True).strip()
    records, checks = [], []
    (out/'expected.json').write_text(json.dumps(dict(seed=SEED, trailing='SFT001', quantity='QWORKFLOW',
        duplicate='SFT002', priority_cycle='SFT007', reference_limit='SFT010',
        shared_owner='case.yh', supplied_derived_override='refused',
        priority_dag='established', kernel_reference_limit='rejected'), indent=2))

    def ck(label, condition):
        assert condition, label
        checks.append(label)

    def call(argv, expected=0, data=None):
        p = subprocess.run(list(map(str, argv)), input=data, capture_output=True, cwd=out, timeout=10)
        records.append(dict(argv=list(map(str, argv)), exit=p.returncode,
                            stdout=p.stdout.decode(), stderr=p.stderr.decode()))
        (out/'commands.json').write_text(json.dumps(records, indent=2))
        ck('exit '+str(argv[1:3]), p.returncode == expected)
        return p

    def write(name, model=MODEL, scenario=SCENARIO, case=CASE):
        d = out/name
        d.mkdir()
        for n, text in [('model.yh',model),('scenario.yhs',scenario),('case.yh',case)]:
            (d/n).write_bytes(text.encode())
        return d

    def site(diagnostic, path, token, start=0):
        raw = path.read_bytes()
        offset = raw.index(token.encode(), start)
        prefix = raw[:offset]
        ck('source owner '+token, Path(diagnostic['path']) == path)
        ck('original UTF-8 token start '+token, (diagnostic['line'],diagnostic['column']) ==
           (prefix.count(b'\n')+1,len(prefix.rsplit(b'\n',1)[-1])+1))

    d = write('trailing')
    # Every proper token prefix before the final brace must refuse. Comments after
    # a complete case are valid; any following non-comment token must refuse.
    rng = random.Random(SEED)
    tails = ['ignored','}', ';', '""', CASE, 'allegation truncated']
    for i, tail in enumerate(tails):
        (d/'case.yh').write_text(CASE+'// é漢🙂\n'+tail)
        for op in ['check','compile','run','explain']:
            r = call([y,op,d/'case.yh'],1)
            diag = json.loads(r.stderr)
            ck('trailing refusal',diag['code']=='SFT001' and not r.stdout)
            site(diag,d/'case.yh',tail, len((CASE+'// é漢🙂\n').encode()))
    for i, cut in enumerate(sorted({0,1,len(CASE.rstrip())-1,*[rng.randrange(len(CASE.rstrip())) for _ in range(32)]})):
        (d/'case.yh').write_text(CASE[:cut])
        call([y,'check',d/'case.yh'],1)
    for i in range(36):
        status = ['proved','not_proved','unresolved'][i%3]
        model_name, actor = 'Model'+str(i), 'actor'+str(i)
        m = MODEL.replace(' M ', ' '+model_name+' ').replace('entity a ', 'entity '+actor+' ').replace('p(a)', 'p('+actor+')')
        s = SCENARIO.replace('for M ', 'for '+model_name+' ').replace('p(a)', 'p('+actor+')').replace('as proved', 'as '+status)
        prefix = rng.choice(['','\n','// é漢🙂\n','\t'])
        g = write('generated-'+str(i),prefix+m,s,prefix+CASE+'// trailing comment')
        first = call([y,'run',g/'case.yh']).stdout
        ck('deterministic case',first==call([y,'run',g/'case.yh']).stdout)
        result=json.loads(first)['allegations'][0]
        ck('literal generated outcome',result['id']=='a' and result['result']['expressions'][0]['status']==
           {'proved':'satisfied','not_proved':'not_satisfied','unresolved':'unresolved'}[status])

    d = write('model-owner',MODEL.replace('as t;', 'as missing;'))
    diag=json.loads(call([y,'check',d/'case.yh'],1).stderr);site(diag,d/'model.yh','missing')
    d = write('scenario-owner',scenario=SCENARIO.replace('for M','for Wrong'))
    diag=json.loads(call([y,'check',d/'case.yh'],1).stderr);site(diag,d/'scenario.yhs','Wrong')
    d = write('shared-owner',scenario='typed-rules-scenario S for M {}',case=CASE.replace(' allegation',
        ' shared-classification shared p(missing) as proved reason "synthetic";\n allegation').replace(
        'scenario "scenario.yhs";', 'scenario "scenario.yhs" use shared;'))
    diag=json.loads(call([y,'check',d/'case.yh'],1).stderr);site(diag,d/'case.yh','missing')
    # The selected-allegation dependency path must retain the same case owner.
    (d/'model.yh').write_text(MODEL.replace('entity a as t;', 'entity a as t; entity e as t;'))
    (d/'project.yh').write_text('''checked-project P version "yuho.dependency-plan/v0.1-experimental" {
 source origin locator "urn:synthetic:owner";
 scope s actor project:a context project:e case C allegation a {
 identity project:a nominal role:t; identity project:e nominal role:t; }
 component c profile native-typed model "case.yh" entry allegation a scope s {
 nominal t as role:t; entity a as project:a; entity e as project:e;
 } rationale "fictional";
}''')
    diag=json.loads(call([y,'compose','check',d/'project.yh'],1).stderr)
    loc=diag['dependencyLocation']
    ck('dependency shared owner',loc['locationPath']=='case.yh' and
       (d/'case.yh').read_bytes()[loc['locationStart']:loc['locationEnd']]==b'missing')
    (d/'case.yh').write_text((d/'case.yh').read_text().replace('p(missing)', 'p(a)'))
    ck('selected shared case remains admitted',json.loads(call([y,'compose','check',d/'project.yh']).stdout)['evaluated'] is False)
    (d/'scenario.yhs').write_text(SCENARIO)
    diag=json.loads(call([y,'check',d/'case.yh'],1).stderr)
    ck('mixed-source duplicate code',diag['code']=='SFT002')
    site(diag,d/'case.yh','p(a)');site(diag['related'],d/'scenario.yhs','p(a)')
    diag=json.loads(call([y,'compose','check',d/'project.yh'],1).stderr)
    loc=diag['dependencyLocation']
    ck('dependency duplicate case owner',diag['dependencyCode']=='SFT002' and loc['locationPath']=='case.yh' and
       (d/'case.yh').read_bytes()[loc['locationStart']:loc['locationEnd']]==b'p')
    duplicate=SCENARIO.replace('\n}', '\n // é漢🙂\n classify p(a) as not_proved reason "duplicate";\n}')
    d=write('duplicate',scenario=duplicate)
    for argv in [[y,'check',d/'case.yh'],[y,'check',d/'model.yh','--scenario',d/'scenario.yhs']]:
        diag=json.loads(call(argv,1).stderr)
        ck('duplicate code',diag['code']=='SFT002')
        site(diag,d/'scenario.yhs','p(a)',duplicate.index('//'))
        site(diag['related'],d/'scenario.yhs','p(a)')
    d=write('priority-cycle',MODEL.replace(' limitation', ' rule r:y defeats proposition p:x when q:x;\n priority r:x over r:y;\n priority r:y over r:x;\n limitation'))
    diag=json.loads(call([y,'check',d/'model.yh','--scenario',d/'scenario.yhs'],1).stderr)
    ck('priority cycle',diag['code']=='SFT007')
    site(diag,d/'model.yh','r:x;',d.joinpath('model.yh').read_bytes().index(b'priority r:y'))
    quantity=MODEL.replace(' requirement',' quantitative version "yuho.quantitative/v0.1-experimental";\n derive v:lost type integer = integer(7);\n requirement')
    d=write('derived-authority',quantity,SCENARIO.replace('\n}', '\n value v:lost = integer 99;\n}'))
    for op in ['check','compile','run','explain']:
        r=call([y,op,d/'case.yh'],1);diag=json.loads(r.stderr)
        ck('no silently coerced quantity',diag['code']=='QWORKFLOW' and not r.stdout)
        site(diag,d/'model.yh','M')
    request=dict(format='yuho.machine-request/v0.1-experimental', input_kind='native-yh',operation='run',path=str(d/'case.yh'))
    response=json.loads(call([y,'machine','-'],1,json.dumps(request).encode()).stdout)
    ck('machine no derived spoof success',response['success'] is False and not response['exports'])

    n=40
    rules=''.join(f' rule r:{i} establishes proposition p:x when q:x;\n' for i in range(n))
    edges=''.join(f' priority r:{i} over r:{j};\n' for i in range(n) for j in [i+1,i+2] if j<n)
    d=write('priority-dag',MODEL.replace(' rule r:x establishes proposition p:x when q:x;\n',rules+edges))
    ck('DAG source literal outcome',json.loads(call([y,'run',d/'model.yh','--scenario',d/'scenario.yhs']).stdout)['propositions'][0]['state']=='established')
    reqs=''.join(f' requirement q:{i} = all(q:{i-1},q:{i-1});\n' for i in range(1,30))
    d=write('expansion',MODEL.replace('requirement q:x = p(a);','requirement q:0 = p(a);\n'+reqs).replace('when q:x','when q:29'))
    diag=json.loads(call([y,'check',d/'model.yh','--scenario',d/'scenario.yhs'],1).stderr)
    ck('bounded reference expansion',diag['code']=='SFT010')

    reference=dict(protocol='yuho.kernel-protocol/v1',input_schema='yuho.kernel-input/v1',operation='evaluate',fragment='TypedFiniteRules-v1',request_id='R',policy={'max_nodes':2048},program=dict(id='M',entity_types=['t'],entities=[{'id':'a','type':'t'}],predicates=[{'id':'p','arguments':['t'],'kind':'conduct'}],scalars=[],values=[],propositions=['p:x'],requirements=[{'id':'q:0','expression':{'kind':'predicate','predicate':'p','arguments':[{'kind':'entity','id':'a'}]}}],facts=[{'predicate':'p','arguments':['a'],'status':'satisfied','reason':'synthetic'}],rules=[],priorities=[],limitations=['fictional']))
    for name in ['priorities','references','reference-cycle','scope-cache']:
        req=copy.deepcopy(reference);p=req['program']
        if name=='priorities':
            p['rules']=[dict(id=f'r:{i}',parameters=[],polarity='establish',conclusion='p:x',body={'kind':'reference','id':'q:0'}) for i in range(40)]
            p['priorities']=[dict(higher=f'r:{i}',lower=f'r:{j}') for i in range(40) for j in [i+1,i+2] if j<40]
        elif name=='references':
            p['requirements'] += [dict(id=f'q:{i}',expression={'kind':'all','members':[{'kind':'reference','id':f'q:{i-1}'}]*2}) for i in range(1,30)]
            p['rules']=[dict(id='r:x',parameters=[],polarity='establish',conclusion='p:x',body={'kind':'reference','id':'q:29'})]
        elif name=='scope-cache':
            # A cached reference is not valid in a different lexical scope if it
            # shadows that scope's variable. The wire uses the actual encoder's
            # published field names, but the values/expected refusal are authored here.
            body=dict(kind='forall',variable='var:x',entity_type='t',member=dict(
                kind='predicate',predicate='p',arguments=[dict(kind='variable',id='var:x')]))
            ref=dict(kind='reference',id='q:body')
            p['requirements'] += [dict(id='q:body',expression=body),dict(id='q:combined',
                expression=dict(kind='all',members=[ref,dict(kind='forall',variable='var:x',entity_type='t',member=ref)]))]
        else:
            p['requirements'] += [dict(id='q:cycle',expression={'kind':'reference','id':'q:cycle'})]
        raw=json.dumps(req).encode()+b'\n';(out/(name+'.request.json')).write_bytes(raw)
        answer=call([kernel],data=raw).stdout
        ck('kernel deterministic '+name,answer==call([kernel],data=raw).stdout)
        v=json.loads(answer)
        ck('independent kernel result '+name,v['status']==('evaluated' if name=='priorities' else 'rejected'))
        if name=='scope-cache':ck('lexical scope is not bypassed by cache','shadows' in v['diagnostics'][0]['parameters']['reason'])
        if name=='priorities':ck('independent DAG state',v['propositions'][0]['state']=='established')
        (out/(name+'.response.json')).write_bytes(answer)
    summary=dict(seed=SEED,assertions=len(checks),commands=len(records),passed=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))

if __name__ == '__main__':
    main()
