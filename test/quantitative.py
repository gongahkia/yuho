"""Independent exact-number, authority, scope and public-interface regressions.
All generated projects/exports are external. Expected integers use Python ints
and literal preregistered outcomes, never the production reduction helper.
"""
import argparse, copy, hashlib, json, subprocess, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
HEADER='quantitative version "yuho.quantitative/v0.1-experimental";'
PREFIX='''typed-rules-model Quantities {
 entity-type person; entity-type event; entity actor as person; entity incident as event;
'''+HEADER+'\n'
SUFFIX='''
 proposition p:result; rule r:result establishes proposition p:result when q:result;
 limitation "Fictional finite quantitative control; no legal finding or imposed sentence";
}'''

def scope(n='target',actor=None,event=None,case=''):
    actor=actor or n+':actor';event=event or n+':event'
    return f'scope {n} actor {actor} context {event} {case} {{ identity {actor} nominal person; identity {event} nominal event; }}'
def component(n='target',model='model.yh',scenario='scenario.yh',sc=None,entry=None):
    selector=f'entry allegation {entry}' if entry else f'scenario "{scenario}"'
    return f'component {n} profile native-typed model "{model}" {selector} scope {sc or n} {{ nominal person as person; nominal event as event; entity actor as {(sc or n)}:actor; entity incident as {(sc or n)}:event; }} rationale "Explicit independently selected quantitative source and scenario";'
def candidate(n='candidate',c='target',sc=None):
    return f'candidate {n} scope {sc or c} guard {c} . expression q:result mapping "yuho.condition-identity/v1" modality unspecified rationale "Authored technical candidate only" refs src {{ life-imprisonment term:{n}; }}'
def project(parts=None):
    return 'checked-project quantities version "yuho.dependency-plan/v0.1-experimental" { source src locator "urn:fictional:independent-quantities";\n'+'\n'.join(parts or [scope(),component(),candidate()])+'\n}'
def fixture(body,values,extra=''):
    return {'model.yh':PREFIX+body+extra+SUFFIX,
            'scenario.yh':'typed-rules-scenario Selected for Quantities {\n'+values+'\n}',
            'project.yh':project()}
def val(name,n,ty='integer',reason=None):
    return f'value {name} = {ty} {n} reason "{reason or name+" independent source"}";\n'
def number(v):
    assert v['state']=='known_exact',v
    return int(v['integer'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('binary',type=Path);ap.add_argument('--output',type=Path);args=ap.parse_args()
    Y=args.binary.resolve();O=(args.output or Path(tempfile.mkdtemp(prefix='yuho-quantitative-'))).resolve();O.mkdir(parents=True,exist_ok=True)
    checks=[];calls=[];expectations=[]
    def ck(name,b):
        checks.append(dict(name=name,passed=bool(b)));(O/'checks.json').write_text(json.dumps(checks,indent=2));assert b,name
    def run(name,argv,expected=0,data=None):
        p=subprocess.run(list(map(str,argv)),input=data,cwd=O,capture_output=True)
        row=dict(name=name,argv=list(map(str,argv)),exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode());calls.append(row);(O/'commands.json').write_text(json.dumps(calls,indent=2));ck(name+' exit',p.returncode==expected)
        return json.loads(p.stdout or p.stderr) if p.stdout or p.stderr else {}
    def write(name,files):
        d=O/name;d.mkdir()
        for n,text in files.items():
            p=d/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
        return d
    def execute(name,files,expected_values,status='satisfied',native=True):
        expectations.append(dict(case=name,values=expected_values,status=status));(O/'expected-before-execution.json').write_text(json.dumps(expectations,indent=2))
        d=write(name,files)
        checked=run(name+'-check',[Y,'compose','check',d/'project.yh'])
        ck(name+' no check evaluation',checked['evaluated'] is False and checked['quantitative_plans'][0]['evaluated'] is False)
        export=O/(name+'-export');run(name+'-run',[Y,'compose','run',d/'project.yh','--output',export])
        report=json.loads((export/'report.json').read_text());component_record=next(c for c in report['components'] if c.get('quantitative'))
        q=component_record['quantitative'];actual=q['values']
        for k,v in expected_values.items():
            ck(name+' exact '+k,number(actual[k])==v if v is not None else actual[k]['state']=='explicitly_unresolved')
        backend=component_record['executionBackend'];obs=next(x for x in backend['expressions'] if x['id']=='q:result')
        ck(name+' backend technical outcome',obs['status']==status)
        state=report['candidates'][0]['availabilityState'];tag=state if isinstance(state,str) else state['tag']
        ck(name+' candidate availability',tag=={'satisfied':'Eligible','not_satisfied':'Ineligible','unresolved':'EligibilityUnresolved'}[status])
        ck(name+' supplied and derived separated',not set(q['plan']['qOrder']) & {x['name'] for x in q['plan']['qInputs']})
        ck(name+' new immutable artifact',json.loads((export/'artifact.json').read_text())['artifactFormatVersion']=='yuho.dependency-artifact/v0.2-quantitative-experimental')
        graph=json.loads((export/'view.json').read_text());nodes=graph['nodes'];ids=[x['id'] for x in nodes]
        ck(name+' unique graph IDs',len(ids)==len(set(ids)))
        ck(name+' endpoints',all(x['from'] in ids and x['to'] in ids for x in graph['edges']))
        bindings=json.loads((export/'view-bindings.json').read_text())
        ck(name+' complete binding records',set(ids)=={x['semantic_id'] for x in bindings['included']} and all(x['record'] is not None for x in bindings['included']))
        xml=ET.parse(export/'view.xml');svg=ET.parse(export/'view.svg')
        ck(name+' XML parity',len([x for x in xml.iter() if x.tag.rsplit('}',1)[-1]=='node'])==len(nodes))
        ck(name+' XML identities',set(ids)=={x.attrib['id'] for x in xml.iter() if x.tag.rsplit('}',1)[-1]=='node'})
        svg_ids=[x.attrib['id'] for x in svg.iter() if 'id' in x.attrib]
        ck(name+' unique SVG elements',len(svg_ids)==len(set(svg_ids)))
        ck(name+' SVG correspondence',set(ids)<={x.attrib['data-semantic-id'] for x in svg.iter() if 'data-semantic-id' in x.attrib})
        for i in q['plan']['qInputs']:
            for site in [i['source'],i['declaration']]:
                b=files[site['qSource']].encode()
                ck(name+' actual source bytes '+i['name'],b[site['qStart']:site['qEnd']]==site['qToken'].encode())
            ck(name+' actual scenario authority',hashlib.sha256(files[i['source']['qSource']].encode()).hexdigest()==i['snapshot'])
        if native:
            v=run(name+'-native',[Y,'run',d/'model.yh','--scenario',d/'scenario.yh'])
            ck(name+' native parity',v['quantitative']['values']==actual and v['backend']['expressions']==backend['expressions'])
            static=run(name+'-native-check',[Y,'check',d/'model.yh','--scenario',d/'scenario.yh'])
            ck(name+' native static',static['evaluated'] is False)
        return d,export,report,q
    def reject(name,files,codes,operation='check'):
        d=write(name,files);dest=O/(name+'-must-not-publish')
        argv=[Y,'compose',operation,d/'project.yh']+(['--output',dest] if operation=='run' else [])
        v=run(name,argv,1);ck(name+' structured refusal',v['dependencyCode'] in codes and not dest.exists());return d,v

    # C18-inspired dated finite losses. The legal inclusion interpretation is
    # explicitly authored; dates and separate amounts are original inputs.
    body='''scalar v:first type money SGD; scalar v:second type money SGD;
 scalar v:threshold type money SGD;
 scalar v:start type date; scalar v:end type date; scalar v:day-one type date; scalar v:day-two type date;
 requirement q:one = compare(v:day-one,in-half-open,v:start,v:end);
 requirement q:two = compare(v:day-two,in-half-open,v:start,v:end);
 derive v:total type money SGD = sum(item loss-one value ref(v:first) when q:one,item loss-two value ref(v:second) when q:two);
 requirement q:result = compare(v:total,gte,v:threshold);
 requirement q:strict = compare(v:total,gt,v:threshold);
'''
    dates=val('v:start','2026-01-01','date')+val('v:end','2026-02-01','date')+val('v:day-one','2026-01-01','date')+val('v:day-two','2026-01-31','date')
    base=val('v:first',400000,'money SGD')+val('v:second',600000,'money SGD')+val('v:threshold',1000000,'money SGD')+dates
    original=fixture(body,base)
    d,e,r,q=execute('C18-boundary',original,{'v:total':1000000})
    ck('C18 old strict boundary independently false',next(x for x in r['components'][0]['executionBackend']['expressions'] if x['id']=='q:strict')['status']=='not_satisfied')
    for fmt in ['json','xml','svg']:
        run('native-quantity-diagram-'+fmt,[Y,'diagram',d/'model.yh','--scenario',d/'scenario.yh','--view','trace','--format',fmt,'--output',O/('native-quantity.'+fmt)])
    ng=json.loads((O/'native-quantity.json').read_text());nids={n['id'] for n in ng['nodes']}
    ck('native quantity graph endpoints',len(nids)==len(ng['nodes']) and all(x['from'] in nids and x['to'] in nids for x in ng['edges']))
    ck('native numeric derived card',any(n['kind']=='scalar' and 'derived' in n['label'] and '1000000' in n['label'] for n in ng['nodes']))
    ck('native XML graph IDs',nids=={n.attrib['id'] for n in ET.parse(O/'native-quantity.xml').iter() if n.tag.rsplit('}',1)[-1]=='node'})
    ck('native SVG graph IDs',nids<={n.attrib['data-semantic-id'] for n in ET.parse(O/'native-quantity.svg').iter() if 'data-semantic-id' in n.attrib})
    unsupported=run('frozen-compile-refuses-quantity',[Y,'compile',d/'model.yh','--scenario',d/'scenario.yh'],1)
    ck('no lossy frozen quantitative compilation',unsupported['code']=='QWORKFLOW')
    for name,amount,total,status in [('below',599999,999999,'not_satisfied'),('above',600001,1000001,'satisfied')]:
        execute('C18-'+name,fixture(body,base.replace('SGD 600000','SGD '+str(amount))),{'v:total':total},status)
    unknown=fixture(body,base.replace('money SGD 600000 reason "v:second independent source"','unresolved reason "second loss genuinely unknown"'))
    _,_,_,uq=execute('C18-unknown',unknown,{'v:total':None},'unresolved')
    ck('unknown original reason retained',any('second loss genuinely unknown' in x for x in uq['values']['v:total']['reasons']))
    reject('missing-required-amount',fixture(body,base.replace(val('v:second',600000,'money SGD'),'')),['SFT011','QMISSING'])
    # End is excluded under the existing half-open comparison, not inferred law.
    execute('C18-excluded-end',fixture(body,base.replace('date 2026-01-31','date 2026-02-01')),{'v:total':400000},'not_satisfied')
    excluded_unknown=copy.deepcopy(unknown);excluded_unknown['scenario.yh']=excluded_unknown['scenario.yh'].replace('date 2026-01-31','date 2026-02-01')
    execute('excluded-unknown-amount',excluded_unknown,{'v:total':400000},'not_satisfied')
    unknown_filter=fixture(body,base.replace('date 2026-01-31 reason "v:day-two independent source"','unresolved reason "date not resolved"'))
    execute('unknown-inclusion',unknown_filter,{'v:total':None},'unresolved')

    # Supplementary GST motivates exact factors; these amounts/factor are
    # fictional and do not purport to encode a statutory sentence formula.
    multistage='''scalar v:a type money SGD; scalar v:b type money SGD; scalar v:adjustment type money SGD;
 derive v:final type money SGD = sum(item base value ref(v:scaled),item adjustment value ref(v:adjustment));
 derive v:scaled type money SGD = scale(3,ref(v:subtotal));
 derive v:subtotal type money SGD = sum(item a value ref(v:a),item b value ref(v:b));
 scalar v:threshold type money SGD; requirement q:result = compare(v:final,eq,v:threshold);'''
    multi_values=val('v:a',125,'money SGD')+val('v:b',275,'money SGD')+val('v:adjustment',50,'money SGD')+val('v:threshold',1250,'money SGD')
    md,me,mr,mq=execute('factor-multistage',fixture(multistage,multi_values),{'v:subtotal':400,'v:scaled':1200,'v:final':1250})
    ck('forward references ordered by dependencies',mq['plan']['qOrder']==['v:subtotal','v:scaled','v:final'])
    scalar_body='''scalar v:a type integer; scalar v:b type integer;
 derive v:total type integer = sum(item first value ref(v:a),item second value ref(v:b));
 scalar v:threshold type integer; requirement q:result = compare(v:total,eq,v:threshold);'''
    for name,a,b in [('zero',0,0),('signed',9,-12),('equal',7,7),('precision',9007199254740993,2),('very-large',2**1024,-2**1023),('wide-partial',2**4095,-2**4095)]:
        execute(name,fixture(scalar_body,val('v:a',a)+val('v:b',b)+val('v:threshold',a+b)),{'v:total':a+b})
    grouped=scalar_body.replace('sum(item first value ref(v:a),item second value ref(v:b))','sum(item outer value sum(item first value ref(v:b),item second value ref(v:a)))')
    execute('grouping-permutation',fixture(grouped,val('v:a',11)+val('v:b',-4)+val('v:threshold',7)),{'v:total':7})
    zero_unknown=scalar_body.replace('sum(item first value ref(v:a),item second value ref(v:b))','scale(0,ref(v:a))')
    execute('zero-factor-unknown',fixture(zero_unknown,'value v:a = unresolved reason "unknown operand remains unknown";\n'+val('v:b',2)+val('v:threshold',0)),{'v:total':None},'unresolved')

    count_body='''predicate condition(person,event) kind circumstance;
 predicate other(person,event) kind circumstance;
 requirement q:first = condition(actor,incident); requirement q:second = other(actor,incident);
 derive v:number type count occasions = count(item one when q:first,item two when q:second);
 scalar v:threshold type count occasions; requirement q:result = compare(v:number,gte,v:threshold);'''
    count_values='classify condition(actor,incident) as proved reason "independent first occasion"; classify other(actor,incident) as not_proved reason "independent second occasion";\n'+val('v:threshold',1,'count occasions')
    execute('finite-count',fixture(count_body,count_values),{'v:number':1})
    execute('finite-count-unknown',fixture(count_body,count_values.replace('not_proved','unresolved')),{'v:number':None},'unresolved')
    execute('finite-count-empty',fixture(count_body.replace('count(item one when q:first,item two when q:second)','count()'),count_values.replace('count occasions 1','count occasions 0')),{'v:number':0})
    execute('empty-sum',fixture(scalar_body.replace('sum(item first value ref(v:a),item second value ref(v:b))','sum()'),val('v:a',0)+val('v:b',0)+val('v:threshold',0)),{'v:total':0})

    # Static refusals: independently chosen invalid programs, never expected
    # output generated from the implementation's type checker.
    invalid=[
      ('derived-input',scalar_body,val('v:a',1)+val('v:b',2)+val('v:threshold',3)+val('v:total',3),['QWRITER']),
      ('unknown-reference',scalar_body.replace('ref(v:a)','ref(v:missing)'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QTYPE']),
      ('self-cycle',scalar_body.replace('ref(v:a)','ref(v:total)'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QCYCLE']),
      ('two-cycle',scalar_body.replace('derive v:total','derive v:other type integer = ref(v:total); derive v:total').replace('ref(v:a)','ref(v:other)'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QCYCLE']),
      ('duplicate-writer',scalar_body.replace('scalar v:threshold','derive v:total type integer = integer(3); scalar v:threshold'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['SFT002','QWRITER']),
      ('duplicate-items',scalar_body.replace('item second','item first'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QWRITER']),
      ('duplicate-count-items',count_body.replace('item two','item one'),count_values,['QWRITER']),
      ('count-domain',count_body.replace('scalar v:threshold type count occasions','scalar v:threshold type count persons'),count_values.replace('count occasions','count persons'),['QTYPE']),
      ('count-integer-coercion',count_body.replace('scalar v:threshold type count occasions','scalar v:threshold type integer'),count_values.replace('count occasions','integer'),['QTYPE']),
      ('money-factor-negative',multistage.replace('scale(3','scale(-1'),multi_values,['QTYPE']),
      ('cross-currency',multistage.replace('scalar v:a type money SGD','scalar v:a type money USD'),multi_values.replace('money SGD 125 reason','money USD 125 reason'),['QTYPE']),
      ('money-integer',multistage.replace('scalar v:a type money SGD','scalar v:a type integer'),multi_values.replace('money SGD 125 reason','integer 125 reason'),['QTYPE']),
      ('unsupported-division',scalar_body.replace('sum(item first value ref(v:a),item second value ref(v:b))','divide(ref(v:a),integer(0))'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QOPERATION']),
      ('oversized-literal',scalar_body.replace('ref(v:a)','integer('+str(2**4096)+')'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QLIMIT']),
      ('oversized-input-literal',scalar_body,val('v:a','1'*1300)+val('v:b',2)+val('v:threshold',3),['QLIMIT']),
      ('missing-reason',scalar_body,val('v:a',1).replace(' reason "v:a independent source"','')+val('v:b',2)+val('v:threshold',3),['QREASON']),
      ('unknown-filter',scalar_body.replace('item first value ref(v:a)','item first value ref(v:a) when q:missing'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QNAME']),
      ('fractional-literal',scalar_body.replace('ref(v:a)','integer(0.1)'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['SFT008']),
      ('unsupported-measure',scalar_body.replace('v:a type integer','v:a type measure gram'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['SFT008']),
      ('date-arithmetic',scalar_body.replace('v:a type integer','v:a type date'),val('v:a','2026-01-01','date')+val('v:b',2)+val('v:threshold',3),['QTYPE']),
      ('output-declaration-limit',scalar_body+'\n'+''.join(f'derive v:extra-{i} type integer = integer(0);\n' for i in range(64)),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QLIMIT']),
      ('item-limit',scalar_body.replace('sum(item first value ref(v:a),item second value ref(v:b))','sum('+','.join(f'item i-{i} value ref(v:a)' for i in range(257))+')'),val('v:a',1)+val('v:b',2)+val('v:threshold',3),['QLIMIT']),
    ]
    for name,b,v,codes in invalid:reject(name,fixture(b,v),codes)
    # A scalar cycle can cross an inclusion requirement.
    cyc=scalar_body.replace('item first value ref(v:a)','item first value ref(v:a) when q:result')
    reject('scalar-condition-cycle',fixture(cyc,val('v:a',1)+val('v:b',2)+val('v:threshold',3)),['QCYCLE'])
    overflow=scalar_body.replace('sum(item first value ref(v:a),item second value ref(v:b))','scale(2,ref(v:a))')
    reject('runtime-intermediate-budget',fixture(overflow,val('v:a',2**4095)+val('v:b',0)+val('v:threshold',0)),['QLIMIT'],'run')

    # One original module derivation, explicit selected inputs, two scenarios.
    module='''typed-rules-module quantitative.shared version 1.0.0 {
'''+HEADER+'''
 export scalar v:a; export scalar v:b; export scalar v:total;
 scalar v:a type integer; scalar v:b type integer;
 derive v:total type integer = sum(item first value ref(v:a),item second value ref(v:b));
}'''
    host=PREFIX+'''module-root "modules"; import quantitative.shared version 1.0.0 as shared;
 use scalar shared::v:a; use scalar shared::v:b; use scalar shared::v:total;
 scalar v:threshold type integer; requirement q:result = compare(v:total,gte,v:threshold);'''+SUFFIX
    files={'a.yh':host,'b.yh':host,'a.scenario.yh':'typed-rules-scenario A for Quantities {'+val('v:a',4,reason='actor A original')+val('v:b',6)+val('v:threshold',10)+'}',
           'b.scenario.yh':'typed-rules-scenario B for Quantities {'+val('v:a',1,reason='actor B original')+val('v:b',2)+val('v:threshold',10)+'}',
           'modules/quantitative.shared@1.0.0.yh':module,
           'project.yh':project([scope('a'),scope('b'),component('a','a.yh','a.scenario.yh'),component('b','b.yh','b.scenario.yh'),candidate('A','a'),candidate('B','b')])}
    sd=write('scoped-shared',files);se=O/'scoped-shared-export';run('scoped-shared',[Y,'compose','run',sd/'project.yh','--output',se]);sr=json.loads((se/'report.json').read_text())
    components={c['executionComponent']:c for c in sr['components']}
    ck('actor A exact total',number(components['a']['quantitative']['values']['v:total'])==10)
    ck('actor B exact total',number(components['b']['quantitative']['values']['v:total'])==3)
    graph=json.loads((se/'view.json').read_text())
    ck('one authored quantitative definition',len([n for n in graph['nodes'] if n['kind']=='quantitative_definition'])==1)
    ck('two distinct scoped uses',len([n for n in graph['nodes'] if n['kind']=='quantitative_use'])==2)
    combined=copy.deepcopy(files)
    for name in ['a','b']:
        combined[name+'.yh']=combined[name+'.yh'].replace('scalar v:threshold type integer;',
          'predicate allowed(person,event) kind relationship; requirement-template q:permission(var:a as person,var:e as event) = allowed(var:a,var:e); requirement-use q:scoped from q:permission(actor,incident) assessments scenario; scalar v:threshold type integer;').replace('requirement q:result = compare(v:total,gte,v:threshold);','requirement q:result = all(q:scoped,compare(v:total,gte,v:threshold));')
        combined[name+'.scenario.yh']=combined[name+'.scenario.yh'].rsplit('}',1)[0]+'classify allowed(actor,incident) as proved reason "independent permission for this occurrence"; }'
    scd=write('scoped-template-and-quantity',combined);sce=O/'scoped-template-and-quantity-export';run('scoped-template-and-quantity',[Y,'compose','run',scd/'project.yh','--output',sce]);scr=json.loads((sce/'report.json').read_text())
    ck('scoped template and numeric comparison coexist',len(scr['scoped_definitions']['uses'])==2 and [c['availabilityState']['tag'] for c in scr['candidates']]==['Eligible','Ineligible'])
    changed=copy.deepcopy(files);changed['a.scenario.yh']=changed['a.scenario.yh'].replace('integer 4','integer 40')
    cd=write('scope-isolation-change-A',changed);ce=O/'scope-isolation-export';run('scope-isolation',[Y,'compose','run',cd/'project.yh','--output',ce]);cr=json.loads((ce/'report.json').read_text())
    ck('B independent of A values and authority',next(c for c in cr['components'] if c['executionComponent']=='b')['quantitative']==components['b']['quantitative'])
    wrong=copy.deepcopy(files);wrong['a.yh']=wrong['a.yh'].replace('use scalar shared::v:a;','scalar v:a type integer;')
    reject('wrong-but-existing-module-input',wrong,['QAUTHORITY'])

    # Actual quantitative comparison -> accepted dependency -> technical slot.
    recipient='''typed-rules-model Receiver { entity-type person; entity-type event; entity actor as person; entity incident as event;
 dependency-condition in:quant type technical-condition; requirement q:result = condition(in:quant);
 proposition p; rule r establishes proposition p when q:result; limitation "Technical condition only"; }'''
    integration=copy.deepcopy(original);integration['receiver.yh']=recipient;integration['receiver.scenario.yh']='typed-rules-scenario R for Receiver {}'
    integration['project.yh']=project([scope(),component(),component('receiver','receiver.yh','receiver.scenario.yh','target'),
      'bind exact-result from target . expression q:result to receiver . condition in:quant mapping "yuho.condition-identity/v1" rationale "Actual evaluated derived comparison" refs src;',candidate('receiver-candidate','receiver','target')])
    id=write('dependency-integration',integration);ie=O/'integration-export';run('dependency-integration',[Y,'compose','run',id/'project.yh','--output',ie]);ir=json.loads((ie/'report.json').read_text())
    ck('actual derived comparison port',ir['bindings'][0]['conversionSource']['observationPort']==dict(portComponent='target',portCategory='typed.expression.truth',portObject='q:result') and ir['bindings'][0]['conversionValue']=='Satisfied')
    ck('downstream actual satisfied',next(c for c in ir['components'] if c['executionComponent']=='receiver')['executionBackend']['expressions'][0]['status']=='satisfied')

    # Actual generated condition -> quantitative filter -> comparison ancestry.
    conflict_source='''typed-rules-model Contradiction {
 entity-type person; entity-type event; entity actor as person; entity incident as event;
 predicate supports(person,event) kind relationship; requirement q:positive = supports(actor,incident);
 proposition p:conflict; rule r:yes establishes proposition p:conflict when q:positive;
 rule r:no defeats proposition p:conflict when q:positive; limitation "Fictional equal-priority conflict"; }'''
    conflict_body='''dependency-condition in:conflict type technical-condition;
 predicate local(person,event) kind circumstance;
 requirement q:local = local(actor,incident); requirement q:gate = condition(in:conflict);
 scalar v:a type integer; scalar v:threshold type integer;
 derive v:total type integer = sum(item selected value ref(v:a) when q:gate);
 requirement q:result = compare(v:total,gte,v:threshold);
 requirement q:independent = q:local;
 requirement q:strong = all(q:local,q:gate);'''
    cf=fixture(conflict_body,val('v:a',10)+val('v:threshold',1)+'classify local(actor,incident) as not_proved reason "independent false";')
    cf.update({'upstream.yh':conflict_source,'upstream.scenario.yh':'typed-rules-scenario C for Contradiction { classify supports(actor,incident) as proved reason "contradictory support"; }'})
    cf['project.yh']=project([scope(),component(),component('upstream','upstream.yh','upstream.scenario.yh','target'),
      'bind conflict-input from upstream . proposition p:conflict to target . condition in:conflict mapping "yuho.proposition-support/v1" rationale "Actual typed conflict through numeric inclusion" refs src;',
      candidate('dependent'),candidate('independent').replace('expression q:result','expression q:independent'),candidate('strong').replace('expression q:result','expression q:strong')])
    fd=write('conflict-through-quantity',cf);fe=O/'conflict-through-quantity-export';run('conflict-through-quantity',[Y,'compose','run',fd/'project.yh','--output',fe]);fr=json.loads((fe/'report.json').read_text())
    cs={c['availabilityCandidate']['candidateIdentity']:c for c in fr['candidates']}
    for name,state,ancestry in [('dependent','EligibilityUnresolved',True),('independent','Ineligible',False),('strong','Ineligible',True)]:
        ck('actual conflict ancestry '+name,cs[name]['availabilityState']['tag']==state and any(x.startswith('conflict:') for x in cs[name]['availabilityGuard']['conversionCauses'])==ancestry)
    fq=next(c for c in fr['components'] if c['executionComponent']=='target')['quantitative']
    ck('conflict actual generated ground read',any(i['kind']=='ground_application' and i['arguments']==['dep_template_entity'] for s in fq['steps'] for i in s['contributing_inputs']))
    ck('conflict does not fabricate known total',fq['values']['v:total']['state']=='explicitly_unresolved')

    # Same shared quantitative body, separate allegation-specific scenarios.
    af=copy.deepcopy(files);af['case.yh']='typed-rules-case case:trial model "a.yh" { allegation a--one scenario "a.scenario.yh"; allegation a--two scenario "b.scenario.yh"; }'
    af['project.yh']=project([scope('a','a:actor','a:event','case case:trial allegation a--one'),scope('b','b:actor','b:event','case case:trial allegation a--two'),component('a','case.yh',entry='a--one'),component('b','case.yh',entry='a--two'),candidate('A','a'),candidate('B','b')])
    ad=write('quantitative-allegations',af);ae=O/'quantitative-allegations-export';run('quantitative-allegations',[Y,'compose','run',ad/'project.yh','--output',ae]);ar=json.loads((ae/'report.json').read_text())
    ck('distinct allegation values and scopes',[(c['executionScope']['scopeAllegation'],number(c['quantitative']['values']['v:total'])) for c in ar['components']]==[('a--one',10),('a--two',3)])
    equal=copy.deepcopy(files);equal['b.scenario.yh']=equal['b.scenario.yh'].replace('integer 1 reason','integer 8 reason')
    eqd=write('equal-value-distinct-authority',equal);eqe=O/'equal-value-export';run('equal-value',[Y,'compose','run',eqd/'project.yh','--output',eqe]);eqr=json.loads((eqe/'report.json').read_text())
    qa,qb=[c['quantitative'] for c in eqr['components']]
    ck('equal values retain different assessment authority',number(qa['values']['v:total'])==number(qb['values']['v:total'])==10 and qa['plan']['qInputs']!=qb['plan']['qInputs'])

    # Independent declaration order and UTF-8 identity controls.
    ordered=fixture(multistage.replace('derive v:final','derive v:unrelated type money SGD = money(SGD,0); derive v:final'),multi_values)
    _,_,_,oq=execute('unrelated-derivation',ordered,{'v:subtotal':400,'v:scaled':1200,'v:final':1250,'v:unrelated':0})
    unicode_files=fixture(scalar_body.replace('v:a','v:a--b').replace('v:b','v:b--c'),val('v:a--b',11,reason='數量 — supplied A')+val('v:b--c',2,reason='數量 — supplied B')+val('v:threshold',13))
    execute('unicode-delimiter',unicode_files,{'v:total':13})
    reject('missing-even-excluded',fixture(body,base.replace(val('v:second',600000,'money SGD'),'').replace('date 2026-01-31','date 2026-02-01')),['SFT011','QMISSING'])
    deep='ref(v:a)'
    for _ in range(18):deep='scale(1,'+deep+')'
    reject('expression-depth',fixture(scalar_body.replace('sum(item first value ref(v:a),item second value ref(v:b))',deep),val('v:a',1)+val('v:b',2)+val('v:threshold',3)),['QLIMIT'])

    # Public SDK construction, actual source-backed execution and source recovery.
    sdk=O/'sdk-client';build=O/'sdk-build'
    p=subprocess.run(['cabal','exec','--offline','--','ghc-9.8.4','-package=yuho','-outputdir',str(build),'-o',str(sdk),str(ROOT/'test/QuantitativeClient.hs')],cwd=ROOT,capture_output=True)
    (O/'sdk-build.log').write_bytes(p.stdout+p.stderr);ck('public SDK compiles',p.returncode==0)
    builder=O/'sdk-builders';p=subprocess.run([sdk,'builders',builder],capture_output=True);ck('SDK source builders',p.returncode==0)
    (builder/'project.yh').write_text(project());be=O/'sdk-builders-cli-export';run('SDK-builder-source',[Y,'compose','run',builder/'project.yh','--output',be])
    br=json.loads((be/'report.json').read_text());ck('SDK builder independent 400 oracle',number(br['components'][0]['quantitative']['values']['v:total'])==400)
    doc=O/'sdk-document.json';doc.write_text(json.dumps(json.loads((be/'artifact.json').read_text())['artifactDocument']))
    se2=O/'sdk-public-export';sdk_result=run('SDK-source-recovery-replay',[sdk,'run',doc,se2]);ck('SDK actual quantitative parity',sdk_result==br['quantitative'])
    ck('SDK complete export parity',all(p.read_bytes()==(se2/p.name).read_bytes() for p in be.iterdir()))

    # Validate the new exact string-valued contracts, not only JSON parseability.
    import jsonschema
    from referencing import Registry,Resource
    registry=Registry().with_resources((p.as_uri(),Resource.from_contents(json.loads(p.read_text()))) for p in (ROOT/'schema').glob('*.schema.json'))
    for name in ['report','artifact']:
        schema_name='dependency-report-v0.1-experimental' if name=='report' else 'dependency-artifact-v0.2-quantitative-experimental'
        path=ROOT/'schema'/(schema_name+'.schema.json');schema=json.loads(path.read_text());schema['$id']=path.as_uri()
        jsonschema.Draft202012Validator(schema,registry=registry).validate(json.loads((be/(name+'.json')).read_text()))
        ck('new '+name+' schema',True)

    # Replay exact source authority, deterministic output, tampering and no replace.
    replay=O/'replay';run('immutable-replay',[Y,'compose','replay',e/'artifact.json','--output',replay])
    ck('all eight replay bytes deterministic',len(list(e.iterdir()))==8 and all(p.read_bytes()==(replay/p.name).read_bytes() for p in e.iterdir()))
    run('existing-destination',[Y,'compose','replay',e/'artifact.json','--output',replay],1)
    original_source=(d/'scenario.yh').read_bytes();(d/'scenario.yh').write_bytes(original_source.replace(b'independent source',b'changed authority'))
    run('same-status-stale-attachment',[Y,'compose','check',d/'project.yh','--against',e/'artifact.json'],1)
    run('artifact-static-check',[Y,'compose','check',e/'artifact.json'])
    for name,change in [
      ('missing-quantitative-record',lambda r:r.update(quantitative=None)),
      ('wrong-quantitative-version',lambda r:r['quantitative'].update(format='yuho.quantitative/unknown')),
      ('missing-actual-values',lambda r:r['quantitative']['occurrences'][0]['actual'].pop('values')),
      ('duplicate-saved-occurrence',lambda r:r['quantitative']['occurrences'].append(r['quantitative']['occurrences'][0]))]:
        malformed=json.loads((e/'artifact.json').read_text());change(malformed['artifactQuantitativeReport']);mp=O/(name+'.json');mp.write_text(json.dumps(malformed))
        run(name,[Y,'compose','check',mp],1)
    unchanged=O/'unchanged-frozen';run('old-artifact-live-change',[Y,'compose','replay',e/'artifact.json','--output',unchanged])
    ck('frozen result unaffected by live source',all(p.read_bytes()==(unchanged/p.name).read_bytes() for p in e.iterdir()))
    bad=json.loads((e/'artifact.json').read_text());bad['artifactQuantitativeReport']['components'][0]['quantitative']['values']['v:total']['integer']='0';(O/'tampered.json').write_text(json.dumps(bad))
    run('tampered-saved-result',[Y,'compose','replay',O/'tampered.json','--output',O/'tamper-output'],1);ck('tamper no publication',not (O/'tamper-output').exists())
    for op,kind,path in [('check','dependency-yh',md/'project.yh'),('run','dependency-yh',md/'project.yh'),('check','dependency-artifact-json',e/'artifact.json'),('replay','dependency-artifact-json',e/'artifact.json')]:
        for transport in ['file','stdin']:
            request=dict(format='yuho.machine-request/v0.2-experimental',input_kind=kind,operation=op,path=str(path))
            if op in ['run','replay']:request['output']=str(O/('machine-'+op+'-'+transport))
            req=O/(op+'-'+kind+'-'+transport+'.json');req.write_text(json.dumps(request))
            result=run('machine-'+op+'-'+transport,[Y,'machine','-' if transport=='stdin' else req],data=req.read_bytes() if transport=='stdin' else None)
            ck('machine quantitative profile '+op+transport,result['success'] and 'ExactQuantities-v1' in result['semantic_profiles'])
    request=dict(format='yuho.machine-request/v0.2-experimental',input_kind='dependency-artifact-json',operation='check',path=str(md/'project.yh'))
    failure=run('wrong-machine-authority',[Y,'machine','-'],1,json.dumps(request).encode())
    ck('wrong kind structured unvalidated',failure['success'] is False and not failure['exports'] and failure['effects']['source_authority']=='not_validated')
    request=dict(format='yuho.machine-request/v0.2-experimental',input_kind='dependency-yh',operation='run',path=str(md/'project.yh'),output=str(me))
    failure=run('machine-existing-destination',[Y,'machine','-'],1,json.dumps(request).encode())
    ck('machine publication failure advertises no exports',failure['success'] is False and not failure['exports'])
    (O/'summary.json').write_text(json.dumps(dict(assertions=len(checks),calls=len(calls),positive_cases=len(expectations),output=str(O)),indent=2));print((O/'summary.json').read_text())

if __name__=='__main__':main()
