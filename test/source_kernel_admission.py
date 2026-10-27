"""C01–C03: independent boundary/cost oracles and actual closed-kernel admission.
All generated inputs, expectations, outputs and transcripts stay outside the repo.
"""
import argparse, copy, hashlib, json, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODEL='''// source-owner padding é🙂
typed-rules-model M {
 entity-type t; entity a as t; predicate p(t) kind conduct;
 requirement q:x = p(a); proposition p:x;
 rule r:x establishes proposition p:x when q:x;
 limitation "fictional";
}
'''
SCENARIO='''// original scenario é🙂
typed-rules-scenario S for M {
 classify p(a) as proved reason "reason";
}
'''
CASE='''// original case é🙂
typed-rules-case C model "model.yh" {
 allegation al scenario "scenario.yhs";
}
'''

def independent_cost(p):
    """Literal published recurrence; no production estimator/helper imports."""
    req={q['id']:q['expression'] for q in p['requirements']}
    domain={t:sum(e['type']==t for e in p['entities']) for t in p['entity_types']}
    def expr(e):
        k=e['kind']
        if k=='reference':return 1+expr(req[e['id']])
        if k in ['all','any','at-least','at-most','exactly']:return 1+sum(map(expr,e['members']))
        if k in ['forall','exists']:return 1+domain[e['entity_type']]*expr(e['member'])
        if k=='not':return 1+expr(e['member'])
        return 1
    def rule(r):
        instances=1
        for v in r['parameters']:instances*=domain[v['entity_type']]
        return 1+instances*expr(r['body'])
    return sum(len(p[k]) for k in ['entity_types','entities','predicates','scalars','propositions','priorities','facts','values'])+sum(expr(q['expression']) for q in p['requirements'])+sum(map(rule,p['rules']))

def expanded_source(scalars=0,extra_rules=0,edges=0,context=False):
    declarations=''.join(f' scalar v:{i} type integer;\n' for i in range(scalars))
    requirements=' requirement q:0 = p(a);\n'+''.join(f' requirement q:{i} = all(q:{i-1},q:{i-1});\n' for i in range(1,8))
    rules=''.join(f' rule r:{i} establishes proposition p:x when q:{7 if i<2 else 0};\n' for i in range(2+extra_rules))
    pairs=[(i,j) for i in range(2+extra_rules) for j in range(i+1,2+extra_rules)][:edges]
    assert len(pairs)==edges
    priorities=''.join(f' priority r:{i} over r:{j};\n' for i,j in pairs)
    m='// cost owner é🙂\ntyped-rules-model M {\n entity-type t; entity a as t; '+('entity e as t; ' if context else '')+'predicate p(t) kind conduct; proposition p:x;\n'+declarations+requirements+rules+priorities+' limitation "fictional";\n}'
    s=SCENARIO.replace('\n}', '\n'+''.join(f' value v:{i} = integer 0;\n' for i in range(scalars))+'}')
    # E0=1; Ei=2Ei-1+3; sum(E0..E7)=996. Two deep rules cost 2*511.
    cost=2023+2*scalars+3*extra_rules+edges+int(context)
    return m,s,cost

def main():
    ap=argparse.ArgumentParser();ap.add_argument('binary',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
    O=(a.output or Path(tempfile.mkdtemp(prefix='yuho-admission-'))).resolve();O.mkdir(parents=True,exist_ok=True)
    Y=str(a.binary.resolve());K=subprocess.check_output(['cabal','list-bin','exe:yuho-kernel','--offline'],cwd=ROOT,text=True).strip()
    records=[];checks=[];expected=[];requests=[]
    def ck(n,b):
        checks.append(dict(name=n,passed=bool(b)));(O/'checks.json').write_text(json.dumps(checks,indent=2));assert b,n
    def call(argv,code=0,data=None):
        p=subprocess.run(list(map(str,argv)),input=data,capture_output=True,cwd=ROOT,timeout=20)
        records.append(dict(argv=list(map(str,argv)),exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode()));(O/'commands.json').write_text(json.dumps(records,indent=2))
        ck('exit '+str(argv[1:3]),p.returncode==code);return p
    def write(name,m=MODEL,s=SCENARIO,c=None):
        d=O/name;d.mkdir();(d/'model.yh').write_text(m);(d/'scenario.yhs').write_text(s)
        if c is not None:(d/'case.yh').write_text(c)
        return d
    def site(diag,path,token,offset=None):
        raw=path.read_bytes();word=token.encode();at=raw.index(word) if offset is None else offset;prefix=raw[:at]
        ck('original source owner',Path(diag['path'])==path)
        ck('original token bytes',raw[at:at+len(word)]==word)
        ck('byte line/column',(diag['line'],diag['column'])==(prefix.count(b'\n')+1,len(prefix.rsplit(b'\n',1)[-1])+1))
    def machine(op,path,scenario=None,code=0):
        r=dict(format='yuho.machine-request/v0.1-experimental',input_kind='native-yh',operation=op,path=str(path))
        if scenario:r['scenario']=str(scenario)
        v=json.loads(call([Y,'machine','-'],code,json.dumps(r).encode()).stdout)
        ck('machine success truthful',v['success']==(code==0))
        if code:ck('machine no failed exports',not v['exports'])
        return v
    def exercise(d,cost=None,invalid=None,case=False):
        # Expectations are persisted before running the source compiler.
        expectation=dict(case=d.name,cost=cost,invalid=invalid is not None)
        if invalid:
            code,file,token=invalid;raw=(d/file).read_bytes();offset=raw.index(token.encode());prefix=raw[:offset]
            expectation['diagnostic']=dict(code=code,path=str(d/file),token=token,
                line=prefix.count(b'\n')+1,column=len(prefix.rsplit(b'\n',1)[-1])+1,byte_offset=offset)
        expected.append(expectation);(O/'expected-before.json').write_text(json.dumps(expected,indent=2))
        path=d/('case.yh' if case else 'model.yh');args=[path]+([] if case else ['--scenario',d/'scenario.yhs'])
        for op in ['check','compile','run','explain']:
            p=call([Y,op,*args],int(invalid is not None))
            if invalid:
                code,file,token=invalid;v=json.loads(p.stderr);ck('source refusal '+code,v['code']==code and not p.stdout);site(v,d/file,token)
                if cost is not None:ck('effective resource cost reported',str(cost) in v['message'])
            elif op=='compile':
                v=json.loads(p.stdout);rs=[x['request'] for x in v['allegations']] if case else [v]
                for i,r in enumerate(rs):
                    computed=independent_cost(r['program']);ck('independent exact cost',computed<=2048 and (cost is None or computed==cost))
                    raw=json.dumps(r,ensure_ascii=False).encode();(d/f'request-{i}.json').write_bytes(raw);response=call([K],data=raw+b'\n').stdout;(d/f'kernel-{i}.json').write_bytes(response)
                    ck('successful compile is kernel admitted',json.loads(response)['status']=='evaluated');requests.append((r,computed))
                ck('distinct allegation request identities',len({r['request_id'] for r in rs})==len(rs))
        result=machine('compile',path,None if case else d/'scenario.yhs',int(invalid is not None))
        if invalid:
            code,file,token=invalid;diag=result['diagnostics'][0]
            ck('machine diagnostic code',diag['code']==code);site(diag,d/file,token)
        return result

    # C01: short wire bytes preserved; all 128 authored characters retained.
    for length in [1,119,120,121,127,128,129]:
        ident='m'*length;d=write('model-'+str(length),MODEL.replace('model M','model '+ident),SCENARIO.replace('for M','for '+ident))
        exercise(d,invalid=('SFT010','model.yh',ident) if length>128 else None)
        if length<=128:
            r=json.loads((d/'request-0.json').read_text());wanted=ident+'-request' if length<=120 else '~yh-request:'+hashlib.sha256(ident.encode()).hexdigest()
            ck('generated ID exact policy',r['request_id']==wanted and len(wanted)<=128 and r['program']['id']==ident)
    for length in [120,121,128,129]:
        ident='a'*length;d=write('allegation-'+str(length),c=CASE.replace('allegation al','allegation '+ident));exercise(d,case=True,invalid=('SFT010','case.yh',ident) if length>128 else None)
    ids=['x'*120,'x'*120+'-request','x'*127+'a','x'*127+'b','a:b.c/d_e-'*12+'z']
    d=write('long-distinct',c=CASE.replace(' allegation al scenario "scenario.yhs";', ''.join(' allegation '+i+' scenario "scenario.yhs";\n' for i in ids)));exercise(d,case=True)
    d=write('case-identity-over',c=CASE.replace('case C','case '+'c'*129));exercise(d,case=True,invalid=('SFT010','case.yh','c'*129))
    for length in [128,129]:
        ident='m'*length;d=write('case-model-'+str(length),MODEL.replace('model M','model '+ident),SCENARIO.replace('for M','for '+ident),CASE)
        exercise(d,case=True,invalid=('SFT010','model.yh',ident) if length>128 else None)

    # Imported declarations keep their defining file even for new bounds checks.
    for length in [128,129]:
        ident='p'*length
        m=MODEL.replace('entity-type t;', 'module-root "modules"; import bounds.types version 1.0.0 as b; entity-type t;').replace('predicate p(t) kind conduct;', 'use predicate b::'+ident+';').replace('p(a)',ident+'(a)')
        d=write('imported-'+str(length),m,SCENARIO.replace('p(a)',ident+'(a)'))
        (d/'modules').mkdir();(d/'modules/bounds.types@1.0.0.yh').write_text('// imported owner é🙂\ntyped-rules-module bounds.types version 1.0.0 {\n predicate '+ident+'(t) kind conduct;\n export predicate '+ident+';\n}')
        exercise(d,invalid=('SFT010','modules/bounds.types@1.0.0.yh',ident) if length>128 else None)

    # C02: code points, not bytes; whitespace is preserved and permitted.
    for n in [0,1,127,128,129]:
        for alphabet in ['r','🙂']:
            reason=alphabet*n;d=write('reason-'+str(n)+'-'+('ascii' if alphabet=='r' else 'unicode'),s=SCENARIO.replace('"reason"','"'+reason+'"').replace('as proved','as unresolved'))
            exercise(d,invalid=('SFT008','scenario.yhs','"'+reason+'"') if n not in range(1,129) else None)
            if 1<=n<=128:ck('reason unchanged',json.loads((d/'request-0.json').read_text())['program']['facts'][0]['reason']==reason)
    d=write('reason-space',s=SCENARIO.replace('"reason"','" \t "'));exercise(d)
    for n in [0,1,127,128,129]:
        reason='漢'*n;c=CASE.replace(' allegation',' shared-classification shared p(a) as unresolved reason "'+reason+'";\n allegation').replace('scenario "scenario.yhs";','scenario "scenario.yhs" use shared;')
        d=write('shared-'+str(n),s='typed-rules-scenario S for M {}',c=c);exercise(d,case=True,invalid=('SFT008','case.yh','"'+reason+'"') if n not in range(1,129) else None)

    # C03: explicit independent boundary literals, including exact reviewer shape.
    for name,scalars,extra,edges,target in [('cost-2036',6,0,1,2036),('cost-2047',12,0,0,2047),('cost-2048',12,0,1,2048),('reviewer-cost-2049',13,0,0,2049),('cost-2051',14,0,0,2051),('priority-2048',0,8,1,2048),('priority-2049',0,8,2,2049)]:
        m,s,cost=expanded_source(scalars,extra,edges);ck('precomputed cost literal',cost==target);d=write(name,m,s);exercise(d,cost,('SFT010','model.yh','M') if cost>2048 else None)
        if target in [2047,2048,2049]:
            (d/'case.yh').write_text(CASE);exercise(d,cost,('SFT010','model.yh','M') if cost>2048 else None,case=True)
    d=write('minimum','// padding\ntyped-rules-model M { limitation "x"; }','typed-rules-scenario S for M {}');exercise(d,0)
    d=write('one-node','typed-rules-model M { entity-type t; limitation "x"; }','typed-rules-scenario S for M {}');exercise(d,1)
    for limit in [8,9]:
        d=write('explicit-limit-'+str(limit),MODEL.replace(' limitation',f' limit {limit};\n limitation'))
        exercise(d,9,('SFT010','model.yh',str(limit)) if limit==8 else None)
    for scalar_count,edge_count in [(0,200),(200,0),(200,200)]:
        rules=''.join(f' rule r:{i} establishes proposition p:x when q:x;' for i in range(32));pairs=[(i,j) for i in range(32) for j in range(i+1,32)][:edge_count]
        m=MODEL.replace(' rule r:x establishes proposition p:x when q:x;',rules+''.join(f' priority r:{i} over r:{j};' for i,j in pairs)+''.join(f' scalar v:{i} type integer;' for i in range(scalar_count)))
        s=SCENARIO.replace('\n}', ''.join(f' value v:{i} = integer 0;' for i in range(scalar_count))+'\n}')
        exercise(write(f'categories-{scalar_count}-{edge_count}',m,s),102+2*scalar_count+edge_count)
    m=MODEL.replace('entity a as t;','entity a as t; entity e as t;').replace('q:x = p(a)','q:x = forall var:x as t(p(var:x))').replace('rule r:x establishes','rule r:x(var:r as t) establishes')
    s=SCENARIO.replace('\n}', '\n classify p(e) as proved reason "other";\n}');exercise(write('quantifier-parameters',m,s),19)
    for name,text in [('norm','norm n:x subject a modality required action proposition p:x when q:x;'),('route','responsibility-route route:x subject a kind principal-conduct target proposition p:x when q:x;')]:
        exercise(write('elaborated-'+name,MODEL.replace(' limitation',' '+text+'\n limitation')),12)
    m=MODEL.replace('entity-type t;', 'module-root "modules"; import bounds.types version 1.0.0 as b; entity-type t;').replace('requirement q:x = p(a);','requirement-use q:use from b::q:template(a) assessments scenario; requirement q:x = q:use;')
    d=write('scoped-use',m);(d/'modules').mkdir();(d/'modules/bounds.types@1.0.0.yh').write_text('typed-rules-module bounds.types version 1.0.0 { export requirement-template q:template; entity-type t; predicate p(t) kind conduct; requirement-template q:template(var:x as t) = p(var:x); }')
    exercise(d,12)

    # Selected case/checked-project costs and shared reason owners are static.
    def project(d,case=False):
        text='''checked-project P version "yuho.dependency-plan/v0.1-experimental" {
 source origin locator "urn:synthetic:admission";
 scope s actor project:a context project:e CASE { identity project:a nominal role:t; identity project:e nominal role:t; }
 component c profile native-typed model "MODEL" ENTRY scope s {
 nominal t as role:t; entity a as project:a; entity e as project:e;
 } rationale "fictional";
}'''.replace('CASE','case C allegation al' if case else '').replace('MODEL','case.yh' if case else 'model.yh').replace('ENTRY','entry allegation al' if case else 'scenario "scenario.yhs"')
        (d/'project.yh').write_text(text)
    for case in [False,True]:
        for edges in [0,1]:
            m,s,cost=expanded_source(12,0,edges,True);d=write(f'component-{case}-{edges}',m,s,CASE if case else None);project(d,case)
            p=call([Y,'compose','check',d/'project.yh'],int(edges==1));v=json.loads(p.stderr or p.stdout)
            if edges:ck('component rejects true cost',v['dependencyCode']=='SFT010' and '2049' in v['dependencyMessage'] and v['dependencyLocation']['locationPath']=='model.yh')
            else:
                ck('component exact limit static',v['evaluated'] is False and v['expanded_cost']==2048)
                call([Y,'compose','run',d/'project.yh','--output',d/'export'])
    d=write('component-shared',MODEL.replace('entity a as t;','entity a as t; entity e as t;'), 'typed-rules-scenario S for M {}',CASE.replace(' allegation',' shared-classification shared p(a) as proved reason "";\n allegation').replace('scenario "scenario.yhs";','scenario "scenario.yhs" use shared;'));project(d,True)
    v=json.loads(call([Y,'compose','check',d/'project.yh'],1).stderr);loc=v['dependencyLocation'];ck('component shared owner',v['dependencyCode']=='SFT008' and loc['locationPath']=='case.yh' and (d/'case.yh').read_bytes()[loc['locationStart']:loc['locationEnd']]==b'""')

    # Proven adjacent gaps: depth, enum member/uniqueness, parameter and elaboration.
    m=MODEL.replace('requirement q:x = p(a);','requirement q:inner = forall var:x as t(p(var:x)); requirement q:x = forall var:x as t(q:inner);')
    exercise(write('reference-shadow',m),invalid=('SFT006','model.yh','q:inner'))
    exercise(write('reference-no-shadow',m.replace('q:x = forall var:x as t(q:inner)','q:x = forall var:y as t(q:inner)')))
    for depth in [4,5]:
        d=write('depth-'+str(depth),MODEL.replace('q:x = p(a)','q:x = '+'not('*depth+'p(a)'+')'*depth));exercise(d,invalid=('SFT010','model.yh','q:x') if depth==5 else None)
    for length in [128,129]:
        param='var:'+'z'*(length-4);d=write('parameter-'+str(length),MODEL.replace('rule r:x establishes','rule r:x('+param+' as t) establishes'));exercise(d,invalid=('SFT010','model.yh',param) if length==129 else None)
        member='v'*length;m=MODEL.replace(' requirement',' enum-type en values '+member+'; scalar v:e type enum en;\n requirement');s=SCENARIO.replace('\n}', '\n value v:e = enum en '+member+';\n}');exercise(write('enum-'+str(length),m,s),invalid=('SFT010','model.yh',member) if length==129 else None)
    d=write('duplicate-enum',MODEL.replace(' requirement',' enum-type en values x,x; scalar v:e type enum en;\n requirement'),SCENARIO.replace('\n}','\n value v:e = enum en x;\n}'))
    v=json.loads(call([Y,'check',d/'model.yh','--scenario',d/'scenario.yhs'],1).stderr);ck('duplicate enum source token',v['code']=='SFT002');site(v,d/'model.yh','x', (d/'model.yh').read_bytes().index(b'x,x')+2)
    for label,prefix,keyword,tail,maximum in [('norm','n:','norm','subject a modality required action proposition p:x when q:x;',121),('route','route:','responsibility-route','subject a kind principal-conduct target proposition p:x when q:x;',120)]:
        for size in [maximum,maximum+1]:
            ident=prefix+'x'*(size-len(prefix));d=write(f'generated-{label}-{size}',MODEL.replace(' limitation',f' {keyword} {ident} {tail}\n limitation'));exercise(d,invalid=('SFT010','model.yh',ident) if size>maximum else None)
    d=write('elaborated-count',MODEL.replace(' rule r:x establishes proposition p:x when q:x;', ''.join(f' rule r:{i} establishes proposition p:x when q:x;' for i in range(65))+''.join(f' norm n:{i} subject a modality required action proposition p:x when q:x;' for i in range(64))))
    exercise(d,invalid=('SFT010','model.yh','n:63'))
    d=write('elaborated-collision',MODEL.replace('rule r:x','rule r:norm:n:x').replace(' limitation',' norm n:x subject a modality required action proposition p:x when q:x;\n limitation'))
    v=json.loads(call([Y,'compile',d/'model.yh','--scenario',d/'scenario.yhs'],1).stderr);ck('collision source refusal',v['code']=='SFT002');site(v,d/'model.yh','n:x',(d/'model.yh').read_bytes().index(b'norm n:x')+5)

    # SDK public decoder and estimator must agree with independently counted wire.
    probe=O/'sdk-probe';p=subprocess.run(['cabal','exec','--offline','--','ghc-9.8.4','-Wall','-Werror','-package=yuho','-outputdir',str(O/'sdk-build'),'-o',str(probe),str(ROOT/'test/AdmissionClient.hs')],cwd=ROOT,capture_output=True,timeout=120)
    records.append(dict(argv=p.args,exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode()));(O/'commands.json').write_text(json.dumps(records,indent=2));ck('SDK probe build',p.returncode==0)
    wire=b''.join(json.dumps(r,ensure_ascii=False).encode()+b'\n' for r,_ in requests);values=[json.loads(x) for x in call([probe],data=wire).stdout.splitlines()];ck('SDK count',len(values)==len(requests))
    for v,(_,cost) in zip(values,requests):ck('public SDK closed admission and shared exact cost',v==dict(admitted=True,source_cost=cost,kernel_cost=cost))
    (O/'cost-parity.json').write_text(json.dumps([dict(request=r,independent_cost=cost,sdk=v)
        for (r,cost),v in zip(requests,values)],indent=2))
    # Deterministic mutations at frozen wire boundaries exercise the actual SDK guard.
    r=copy.deepcopy(requests[0][0]);r['request_id']='r'*129
    ck('SDK refuses oversized caller-chosen request ID',json.loads(call([probe],data=json.dumps(r).encode()+b'\n').stdout)['admitted'] is False)
    summary=dict(assertions=len(checks),commands=len(records),admitted_requests=len(requests),passed=True)
    (O/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
