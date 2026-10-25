"""F05: ordinary predicate admission versus the actual active hole construct.
Literal tuple/status/scope expectations are independent of production helpers.
All programs, SDK builds, mutable scenarios and exports are external.
"""
import argparse, copy, hashlib, json, shutil, subprocess, tempfile
import xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'test/fixtures/dependency-condition-admission/exact'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('binary',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--builddir',type=Path);a=ap.parse_args()
    out=a.output or Path(tempfile.mkdtemp(prefix='yuho-condition-admission-'));out.mkdir(parents=True,exist_ok=True)
    y=a.binary.resolve();calls=[];checks=[]
    (out/'expectations-before-execution.json').write_text(json.dumps({
        'ordinary':'No holes: authored condition has ordinary nominal/arity/completeness and structural tuple semantics. T/F/U give Eligible/Ineligible/EligibilityUnresolved; no incoming generated inputs.',
        'names':'Without holes: helper-looking type/entity/slot predicate names remain authored. With holes: actual helper, slot and condition source-form identities remain protected.',
        'scope':'Equal local tuples in distinct scopes have distinct observations and classifications. Named references retain actual requirement and ground read categories.',
        'sources':'Exact reviewer source, modules and selected allegation with shared classification retain actual source authority.',
        'holes':'Unknown slots, wrong special arity, authored collisions/direct inputs, duplicate writers and cross-scope bindings reject before execution.',
        'authority':'Fresh source revisions change snapshot; saved replay uses old embedded bytes; wrong machine input kinds fail truthfully.'},indent=2))
    def check(name,b):
        checks.append(dict(name=name,pass_=bool(b)));(out/'checks.json').write_text(json.dumps(checks,indent=2));assert b,name
    def call(name,args,code=0,data=None,cwd=None):
        p=subprocess.run(list(map(str,args)),input=data,cwd=cwd or out,capture_output=True)
        row=dict(name=name,args=list(map(str,args)),cwd=str(cwd or out),exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode())
        calls.append(row);(out/'commands.json').write_text(json.dumps(calls,indent=2,ensure_ascii=False));assert p.returncode==code,row
        return p
    def cli(name,args,code=0):
        p=call(name,[y,*args],code);return json.loads(p.stdout or p.stderr)
    def sdk(name,doc,code=0):
        f=out/(name+'.json');f.write_text(json.dumps(doc,ensure_ascii=False));dest=out/(name+'-export')
        p=call(name,[out/'sdk','run',f,dest],code)
        if code:check(name+' no publication',not dest.exists())
        return json.loads(p.stdout),dest
    flags=['--builddir='+str(a.builddir)] if a.builddir else []
    for source,target in [('DependencyConditionClient.hs','builder'),('DependencyIntegrityClient.hs','sdk')]:
        call('compile-'+target,['cabal','exec','--offline',*flags,'--','ghc-9.8.4','-package=yuho','-outputdir',out/(target+'-build'),'-o',out/target,ROOT/'test'/source],cwd=ROOT)
    call('public-SDK-construction',[out/'builder',out])
    def parity(dest):
        expected={'artifact.json','report.json','projection.json','view-bindings.json','view.json','view.xml','view.svg','source-map.json'}
        check('complete publication',set(p.name for p in dest.iterdir())==expected)
        r=json.loads((dest/'report.json').read_text());p=json.loads((dest/'projection.json').read_text());g=json.loads((dest/'view.json').read_text())
        check('complete report/projection equality',p['report']==r)
        check('exact source map',json.loads((dest/'source-map.json').read_text())==p['source_map'])
        for s in p['source_map']['sources']:check('original source bytes and digest',hashlib.sha256(s['utf8'].encode()).hexdigest()==s['sha256'])
        ids={n['id'] for n in g['nodes']};check('unique graph and endpoints',len(ids)==len(g['nodes']) and all(e['from'] in ids and e['to'] in ids for e in g['edges']))
        xml=E.parse(dest/'view.xml').getroot();check('XML IDs',ids=={n.attrib['id'] for n in xml.iter() if n.tag.endswith('node')})
        check('XML exact edge relationships',sorted((e['from'],e['to'],e['kind']) for e in g['edges'])==sorted((e.attrib['from'],e.attrib['to'],e.attrib['kind']) for e in xml.iter() if e.tag.endswith('edge')))
        svg=E.parse(dest/'view.svg').getroot();dom=[n.attrib['id'] for n in svg.iter() if 'id' in n.attrib]
        check('SVG injective DOM/semantic associations',len(dom)==len(set(dom)) and ids<={n.attrib['data-semantic-id'] for n in svg.iter() if 'data-semantic-id' in n.attrib})
        bindings=json.loads((dest/'view-bindings.json').read_text())
        check('view binding coverage',{b['semantic_id'] for b in bindings['included']}==ids)
        for cand in r['candidates']:
            guard=cand['availabilityGuard'];obs=guard['conversionSource'];owner=next(c for c in r['components'] if c['executionComponent']==obs['observationPort']['portComponent'])
            check('guard exact occurrence/snapshot',obs['observationScope']==owner['executionScope'] and obs['observationSnapshot']==owner['executionSnapshot'])
            conversion=next(n['id'] for n in g['nodes'] if n['kind']=='conversion' and n['label'].startswith(cand['availabilityCandidate']['candidateIdentity']+' |'))
            check('actual observation conversion edge',any(e['from']==obs['observationIdentity'] and e['to']==conversion and e['kind']=='converts' for e in g['edges']))
            check('actual conversion candidate edge',any(e['from']==conversion and e['to']==guard['conversionDestination'] and e['kind']=='guards' for e in g['edges']))
        return r,p
    def ground(component,q):return [i for r in component['executionReads'] if r['root']==['expression',q] for i in r['input_records'] if i['kind']=='ground_predicate']
    states={'proved':('satisfied','Eligible'),'not_proved':('not_satisfied','Ineligible'),'unresolved':('unresolved','EligibilityUnresolved')}
    def native(name,folder,expected='proved'):
        cli(name+'-standalone-check',['check',folder/'m.yh','--scenario',folder/'s.yh'])
        ordinary=cli(name+'-standalone-run',['run',folder/'m.yh','--scenario',folder/'s.yh'])
        checked=cli(name+'-check',['compose','check',folder/'project.yh']);check('check does not evaluate',checked['evaluated'] is False)
        dest=out/(name+'-export');cli(name+'-run',['compose','run',folder/'project.yh','--output',dest]);r,p=parity(dest);c=r['components'][0]
        check(name+' actual native backend parity',all(c['executionBackend'][k]==ordinary[k] for k in ('expressions','rules','propositions')))
        status,availability=states[expected];q=r['candidates'][0]['availabilityCandidate']['candidateGuard']['portObject']
        check(name+' independent value',next(x for x in c['executionBackend']['expressions'] if x['id']==q)['status']==status and r['candidates'][0]['availabilityState']['tag']==availability)
        check(name+' no generated hole attribution',not c['executionIncoming'] and not r['bindings'] and not p['checked_components'][0]['slots'])
        return r,p,dest
    # Exact independent-reviewer reproduction, without byte changes.
    exact=out/'exact';shutil.copytree(FIX,exact);r,p,original=native('original',exact)
    read=ground(r['components'][0],'q');check('exact authored ordinary primitive',len(read)==1 and read[0]['predicate']=='condition' and read[0]['arguments']==['actor','e'] and read[0]['classification']==dict(status='satisfied',reason='authored ordinary binary predicate'))
    _,sdk_original=sdk('original-SDK-native',p['document']);check('SDK-native eight-file exact parity',all(f.read_bytes()==(sdk_original/f.name).read_bytes() for f in original.iterdir()))
    # Independent source with F04 names, two tuples, a reference chain and local F.
    w=out/'independent';w.mkdir()
    model='''typed-rules-model Matrix {
 entity-type dep_template_type; entity-type event;
 entity dep_template_entity as dep_template_type; entity e as event; entity e:other as event;
 predicate condition(dep_template_type,event) kind relationship;
 predicate unrelated(dep_template_type,event) kind relationship;
 requirement q:first = condition(dep_template_entity,e);
 requirement q:second = condition(dep_template_entity,e:other);
 requirement q:chain = q:first;
 requirement q:local = unrelated(dep_template_entity,e);
 proposition p; rule r establishes proposition p when q:chain;
 limitation "Independent fictional ordinary condition, no dependency holes";
}'''
    scenario='''typed-rules-scenario Input for Matrix {
 classify condition(dep_template_entity,e) as proved reason "exact first";
 classify condition(dep_template_entity,e:other) as not_proved reason "exact second";
 classify unrelated(dep_template_entity,e) as unresolved reason "independent unknown";
}'''
    project=(FIX/'project.yh').read_text().replace('nominal person','nominal dep_template_type').replace('entity actor as','entity dep_template_entity as').replace('expression q ','expression q:chain ')
    for n,t in [('m.yh',model),('s.yh',scenario),('project.yh',project)]:(w/n).write_text(t)
    rr,pp,independent=native('independent',w)
    c=rr['components'][0];backend=c['executionBackend'];values={x['id']:x['status'] for x in backend['expressions']}
    check('independent literal T/F/U/reference results',values=={'q:first':'satisfied','q:second':'not_satisfied','q:chain':'satisfied','q:local':'unresolved'})
    check('independent rule/proposition',backend['rules'][0]['status']=='satisfied' and backend['propositions'][0]['state']=='established')
    check('F04 actual nominal/entity retained',{'id':'dep_template_entity','type':'dep_template_type'} in c['executionRequest']['program']['entities'] and 'dep_template_type' in c['executionRequest']['program']['entity_types'])
    for q,args,status,reason in [('q:first',['dep_template_entity','e'],'satisfied','exact first'),('q:second',['dep_template_entity','e:other'],'not_satisfied','exact second')]:
        inputs=ground(c,q);check('independent structural tuple '+q,len(inputs)==1 and inputs[0]['predicate']=='condition' and inputs[0]['arguments']==args and inputs[0]['classification']==dict(status=status,reason=reason))
    chain=[i for row in c['executionReads'] if row['root']==['expression','q:chain'] for i in row['input_records']]
    check('typed requirement reference distinct from primitive',any(i.get('requirement')=='q:first' and i['kind']=='requirement_reference' for i in chain) and any(i.get('predicate')=='condition' and i['arguments']==['dep_template_entity','e'] for i in chain))
    # T/F/U across native, public template and real selected SDK producer.
    for state,(status,availability) in states.items():
        f=out/('native-'+state);shutil.copytree(exact,f);s=(f/'s.yh');s.write_text(s.read_text().replace(' as proved ',' as '+state+' '));nr,_,_=native('native-'+state,f,state)
        for profile in ['template','typed']:
            doc=json.loads((out/('ordinary-'+profile+'.json')).read_text());comp=doc['dependencyPlan']['planComponents'][0]
            if profile=='template':comp['componentTemplate']['templateFacts'][0][2]={'proved':'Satisfied','not_proved':'NotSatisfied','unresolved':'Unresolved'}[state]
            else:
                typed=json.loads(doc['dependencySources']['typed.json']);typed['typedAssessments'][0]['typedClassification']={'tag':{'proved':'TechnicalTrue','not_proved':'TechnicalFalse','unresolved':'TechnicalUnresolved'}[state]}
                if state=='unresolved':typed['typedAssessments'][0]['typedClassification']['contents']='explicit unknown'
                doc['dependencySources']['typed.json']=json.dumps(typed)
            sr,dest=sdk(profile+'-'+state,doc);parity(dest);sc=sr['components'][0];reads=ground(sc,'q')
            check('SDK actual authored condition '+profile+state,len(reads)==1 and reads[0]['predicate']=='condition' and reads[0]['arguments']==['actor','e'] and reads[0]['classification']['status']==status)
            check('source/SDK independent outcome '+profile+state,sr['candidates'][0]['availabilityState']['tag']==availability and not sc['executionIncoming'])
            if profile=='typed':
                source=out/(profile+'-'+state+'-source.json');source.write_text(doc['dependencySources']['typed.json']);response=out/(profile+'-'+state+'-standalone.json')
                call('standalone-SDK-'+state,[out/'builder','typed',source,response]);actual=json.loads(response.read_text());request=json.loads(Path(str(response)+'.request.json').read_text())
                check('actual SDK standalone program/results parity',request['program']==sc['executionRequest']['program'] and all(actual[k]==sc['executionBackend'][k] for k in ['expressions','rules','propositions']))
    # The ordinary predicate also coexists with both accepted F04 names in SDKs.
    for label,actor,ty in [('entity','dep_template_entity','person'),('type','actor','dep_template_type'),('both','dep_template_entity','dep_template_type')]:
        for profile in ['template','typed']:
            doc=json.loads((out/(label+'-'+profile+'.json')).read_text());sr,dest=sdk(label+'-'+profile+'-ordinary-condition',doc);parity(dest);sc=sr['components'][0]
            check('SDK F04/F05 coexist '+label+profile,{'id':actor,'type':ty} in sc['executionRequest']['program']['entities'] and ground(sc,'q')[0]['arguments']==[actor,'e'] and sr['candidates'][0]['availabilityState']['tag']=='Eligible' and not sc['executionIncoming'])
    # SDK's tagged constructors disambiguate atoms from holes; no source-form ban
    # is imposed on an otherwise valid TemplateAtom merely by its display text.
    doc=json.loads((out/'ordinary-template.json').read_text());plan=doc['dependencyPlan'];supplier=plan['planComponents'][0]
    recipient=copy.deepcopy(supplier);recipient['componentIdentity']='recipient';t=recipient['componentTemplate'];t['templateConditions']=['in:tagged'];t['templateFacts'][0][2]='NotSatisfied'
    t['templateRequirements']=[['q',dict(tag='TemplateAll',contents=[dict(tag='TemplateAtom',contents=['condition',['actor','e']]),dict(tag='TemplateCondition',contents='in:tagged')])]]
    plan['planComponents'].append(recipient);plan['planCandidates'][0]['candidateGuard']['portComponent']='recipient'
    plan['planBindings']=[dict(bindingIdentity='tagged-binding',bindingPort=dict(portComponent='producer',portCategory='typed.expression.truth',portObject='q'),bindingComponent='recipient',bindingSlot='in:tagged',bindingPolicy='yuho.condition-identity/v1',bindingRationale='Explicit tagged constructor only',bindingReferences=['origin'],bindingLocation=None)]
    sr,dest=sdk('SDK-tagged-atom-and-hole',doc);parity(dest);sc=next(c for c in sr['components'] if c['executionComponent']=='recipient');reads=ground(sc,'q')
    check('tagged ordinary F distinct from generated T',sr['candidates'][0]['availabilityState']['tag']=='Ineligible' and any(i['predicate']=='condition' and i['arguments']==['actor','e'] and i['classification']['status']=='not_satisfied' for i in reads) and any(i['predicate']==sr['bindings'][0]['conversionGeneratedInput']['predicate'] and i['arguments']==['dep_template_entity'] and i['classification']['status']=='satisfied' for i in reads))
    # Normal missing-input and nominal/arity contracts still reject.
    for name,m,s,code in [('missing',(FIX/'m.yh').read_text(),'typed-rules-scenario Input for Plain {}','SFT011'),('wrong-arity',(FIX/'m.yh').read_text().replace('condition(actor,e)','condition(actor)'),(FIX/'s.yh').read_text(),'SFT004'),('wrong-type',(FIX/'m.yh').read_text().replace('condition(actor,e)','condition(e,actor)'),(FIX/'s.yh').read_text(),'SFT005')]:
        f=out/name;shutil.copytree(exact,f);(f/'m.yh').write_text(m);(f/'s.yh').write_text(s);v=cli(name,['compose','check',f/'project.yh'],1);check(name+' normal diagnostic',v['dependencyCode']==code)
    n=out/'undeclared-ordinary';shutil.copytree(exact,n);(n/'m.yh').write_text((FIX/'m.yh').read_text().replace('predicate condition(', 'predicate unrelated('))
    check('no implicit condition declaration without holes',cli('undeclared-ordinary',['compose','check',n/'project.yh'],1)['dependencyCode']=='SFT003')
    doc=json.loads((out/'ordinary-template.json').read_text());doc['dependencyPlan']['planComponents'][0]['componentTemplate']['templateRequirements']=[['q',dict(tag='TemplateCondition',contents='absent')]]
    refusal,_=sdk('SDK-undeclared-tagged-condition',doc,1);check('explicit SDK constructor still requires actual slot',refusal['dependencyCode']=='DEPNAME')
    # Exhaustive actual private-identity categories without holes.
    generated='dep_'+hashlib.sha256(b'in:gate').hexdigest()
    for i,name in enumerate(['dep_template_type','dep_template_entity',generated,'in:gate','condition:authored']):
        f=out/('unclaimed-name-'+str(i));shutil.copytree(exact,f)
        for n in ['m.yh','s.yh']:(f/n).write_text((f/n).read_text().replace('condition(',name+'('))
        native('unclaimed-name-'+str(i),f)
    for arity,args,signature in [('unary','actor','person'),('ternary','actor,e,e','person,event,event')]:
        f=out/arity;shutil.copytree(exact,f)
        (f/'m.yh').write_text((f/'m.yh').read_text().replace('condition(person,event)','condition('+signature+')').replace('condition(actor,e)','condition('+args+')'))
        (f/'s.yh').write_text((f/'s.yh').read_text().replace('condition(actor,e)','condition('+args+')'));native(arity,f)
    # Same local fact, different exact component scope and classification.
    f=out/'two-scopes';shutil.copytree(exact,f);(f/'false.yh').write_text((FIX/'s.yh').read_text().replace(' as proved ',' as not_proved '))
    source_project=(FIX/'project.yh').read_text();component=source_project[source_project.index(' component c '):source_project.index(' candidate candidate ')]
    second=component.replace('component c ','component c2 ').replace('"s.yh"','"false.yh"').replace('scope sc ','scope sc2 ').replace('as global:actor','as second:actor').replace('as global:context','as second:context')
    cand=source_project[source_project.index(' candidate candidate '):source_project.rfind('}')]
    cand2=cand.replace('candidate candidate ','candidate candidate2 ').replace('scope sc ','scope sc2 ').replace('guard c .','guard c2 .')
    scope='scope sc2 actor second:actor context second:context { identity second:actor nominal role:actor; identity second:context nominal role:event; }'
    (f/'project.yh').write_text(source_project[:source_project.rfind('}')]+scope+second+cand2+'}')
    dest=out/'two-scopes-export';cli('two-scopes',['compose','run',f/'project.yh','--output',dest]);sr,sp=parity(dest)
    check('independent scoped values',[c['availabilityState']['tag'] for c in sr['candidates']]==['Eligible','Ineligible'])
    observations=[c['availabilityGuard']['conversionSource'] for c in sr['candidates']];check('no shared scoped observation or snapshot',len({o['observationIdentity'] for o in observations})==2 and len({o['observationSnapshot'] for o in observations})==2)
    for owner,status in [('c','satisfied'),('c2','not_satisfied')]:
        c=next(c for c in sr['components'] if c['executionComponent']==owner);check('scope-local exact fact '+owner,ground(c,'q')[0]['classification']['status']==status)
    # Existing exact-version module and selected-allegation forms use same guard.
    f=out/'module';f.mkdir();(f/'modules').mkdir()
    module='''typed-rules-module f05.logic version 1.0.0 {
 export entity-type person; export entity-type event; export entity actor; export entity e;
 export predicate condition; export requirement q:module;
 entity-type person; entity-type event; entity actor as person; entity e as event;
 predicate condition(person,event) kind relationship; requirement q:module = condition(actor,e);
}'''
    (f/'modules/f05.logic@1.0.0.yh').write_text(module)
    (f/'m.yh').write_text('''typed-rules-model Plain { module-root "modules"; import f05.logic version 1.0.0 as lib;
 use entity-type lib::person; use entity-type lib::event; use entity lib::actor; use entity lib::e;
 use predicate lib::condition; use requirement lib::q:module; limitation "fictional imported ordinary predicate";}''')
    (f/'s.yh').write_bytes((FIX/'s.yh').read_bytes());(f/'project.yh').write_text(source_project.replace('expression q ','expression q:module '));native('imported-module',f)
    f=out/'selected-case';shutil.copytree(exact,f)
    (f/'s.yh').write_text('typed-rules-scenario Input for Plain {}')
    (f/'case.yh').write_text('''typed-rules-case case:ordinary model "m.yh" {
 shared-classification shared:ordinary condition(actor,e) as proved reason "authored shared tuple";
 allegation a:one scenario "s.yh" use shared:ordinary;
}''')
    cp=source_project.replace('model "m.yh" scenario "s.yh"','model "case.yh" entry allegation a:one').replace('context global:context {','context global:context case case:ordinary allegation a:one {')
    (f/'project.yh').write_text(cp);dest=out/'selected-case-export';cli('selected-case-check',['compose','check',f/'project.yh']);cli('selected-case-run',['compose','run',f/'project.yh','--output',dest]);sr,sp=parity(dest)
    ordinary=cli('selected-case-standalone',['run',f/'case.yh'])['allegations'][0]['result'];check('selected case parity',all(ordinary[k]==sr['components'][0]['executionBackend'][k] for k in ['expressions','rules','propositions']))
    check('shared authored tuple not generated',ground(sr['components'][0],'q')[0]['classification']==dict(status='satisfied',reason='authored shared tuple') and not sr['components'][0]['executionIncoming'])
    # Real dependency holes remain separate from the supplier's ordinary condition.
    f=out/'holes';shutil.copytree(exact,f)
    recipient='''typed-rules-model Recipient {
 entity-type person; entity-type event; entity actor as person; entity e as event;
 predicate ready(person,event) kind relationship;
 dependency-condition in:gate type technical-condition;
 dependency-condition in:other type technical-condition;
 requirement q:recipient = all(ready(actor,e),condition(in:gate),condition(in:other));
 limitation "fictional bound recipient";}'''
    recipient_scenario='typed-rules-scenario Input for Recipient { classify ready(actor,e) as proved reason "authored local"; }'
    (f/'recipient.yh').write_text(recipient);(f/'recipient-s.yh').write_text(recipient_scenario)
    rc=component.replace('component c ','component r ').replace('"m.yh"','"recipient.yh"').replace('"s.yh"','"recipient-s.yh"')
    bind='bind link from c . expression q to r . condition in:gate mapping "yuho.condition-identity/v1" rationale "Technical only" refs ref;'
    bind2=bind.replace('bind link','bind second').replace('condition in:gate ','condition in:other ')
    hp=source_project.replace(' candidate candidate ',' '+rc+bind+bind2+' candidate candidate ').replace('guard c . expression q','guard r . expression q:recipient')
    (f/'project.yh').write_text(hp);dest=out/'holes-export';cli('holes-check',['compose','check',f/'project.yh']);cli('holes-run',['compose','run',f/'project.yh','--output',dest]);hr,hp_projection=parity(dest)
    supplier=next(c for c in hr['components'] if c['executionComponent']=='c');recipient_record=next(c for c in hr['components'] if c['executionComponent']=='r')
    check('ordinary supplier never replaced',ground(supplier,'q')[0]['predicate']=='condition' and not supplier['executionIncoming'])
    check('two exact generated hole inputs',len(recipient_record['executionIncoming'])==2 and len({b['conversionGeneratedInput']['predicate'] for b in hr['bindings']})==2 and all(b['conversionGeneratedInput']['arguments']==['dep_template_entity'] for b in hr['bindings']))
    # Special syntax reserves a predicate position, not unrelated entity/type names.
    for name,m,scenario_text,component_text in [
        ('condition-entity-with-holes',recipient.replace('entity actor as','entity condition as').replace('ready(actor,e)','ready(condition,e)'),recipient_scenario.replace('ready(actor,e)','ready(condition,e)'),rc.replace('entity actor as','entity condition as')),
        ('condition-type-with-holes',recipient.replace('entity-type person','entity-type condition').replace('as person','as condition').replace('ready(person,event)','ready(condition,event)'),recipient_scenario,rc.replace('nominal person as','nominal condition as'))]:
        n=out/name;shutil.copytree(f,n);(n/'recipient.yh').write_text(m);(n/'recipient-s.yh').write_text(scenario_text);(n/'project.yh').write_text(hp.replace(rc,component_text));nd=out/(name+'-export')
        cli(name,['compose','run',n/'project.yh','--output',nd]);nr,_=parity(nd)
        check(name+' category-specific ownership',nr['candidates'][0]['availabilityState']['tag']=='Eligible')
    negatives=[('unknown-slot',recipient.replace('condition(in:gate)','condition(absent:slot)'),recipient_scenario,'DEPNAME'),('wrong-special-arity',recipient.replace('condition(in:gate)','condition(in:gate,actor)'),recipient_scenario,'DEPCATEGORY'),('empty-special-arity',recipient.replace('condition(in:gate)','condition()'),recipient_scenario,'DEPCATEGORY'),('authored-condition-predicate',recipient.replace('predicate ready','predicate condition(person,event) kind relationship; predicate ready'),recipient_scenario,'DEPWRITER'),('generated-predicate',recipient.replace('predicate ready','predicate '+generated+'(person) kind relationship; predicate ready'),recipient_scenario,'DEPWRITER'),('generated-type',recipient.replace('predicate ready','entity-type dep_template_type; predicate ready'),recipient_scenario,'DEPWRITER'),('generated-entity',recipient.replace('predicate ready','entity dep_template_entity as person; predicate ready'),recipient_scenario,'DEPWRITER')]
    for name,classification in [('direct-special','condition(in:gate)'),('direct-slot-id','in:gate(actor)'),('direct-generated',generated+'(dep_template_entity)')]:
        negatives.append((name,recipient,recipient_scenario.replace(' }',' classify '+classification+' as proved reason "forged direct input"; }'),'DEPWRITER'))
    for name,m,s,code in negatives:
        n=out/name;shutil.copytree(f,n);(n/'recipient.yh').write_text(m);(n/'recipient-s.yh').write_text(s);v=cli(name,['compose','check',n/'project.yh'],1);check(name+' required refusal',v['dependencyCode']==code)
    n=out/'duplicate-writer';shutil.copytree(f,n);(n/'project.yh').write_text(hp.replace(bind,bind+' '+bind.replace('bind link','bind duplicate')));check('duplicate writer stays refused',cli('duplicate-writer',['compose','check',n/'project.yh'],1)['dependencyCode']=='DEPWRITER')
    n=out/'wrong-scope';shutil.copytree(f,n);scope2='scope other actor other:a context other:e {identity other:a nominal role:actor; identity other:e nominal role:event;}'
    rc2=rc.replace('scope sc ','scope other ').replace('as global:actor','as other:a').replace('as global:context','as other:e')
    (n/'project.yh').write_text(hp.replace(rc,scope2+rc2));check('incompatible actual scope stays refused',cli('wrong-scope',['compose','check',n/'project.yh'],1)['dependencyCode']=='DEPSCOPE')
    # Genuine unresolved upstream classification stays U through active slots.
    n=out/'unresolved-holes';shutil.copytree(f,n);(n/'s.yh').write_text((n/'s.yh').read_text().replace(' as proved ',' as unresolved '));udest=out/'unresolved-holes-export'
    cli('unresolved-holes',['compose','run',n/'project.yh','--output',udest]);ur,_=parity(udest)
    check('unresolved source never becomes false',ur['candidates'][0]['availabilityState']['tag']=='EligibilityUnresolved' and all(b['conversionValue']=='Unresolved' for b in ur['bindings']))
    # Replay, source changes and exact machine authority.
    for name,d in [('original',original),('independent',independent),('holes',dest)]:
        target=out/(name+'-replay');cli(name+'-replay',['compose','replay',d/'artifact.json','--output',target]);check(name+' immutable eight-file bytes',all(p.read_bytes()==(target/p.name).read_bytes() for p in d.iterdir()))
    old_snapshot=r['components'][0]['executionSnapshot'];(exact/'s.yh').write_text((exact/'s.yh').read_text().replace('authored ordinary binary predicate','same-status revision'))
    check('stale live attachment refused',cli('stale-source',['compose','check',exact/'project.yh','--against',original/'artifact.json'],1)['dependencyCode']=='DEPSTALE')
    fresh=out/'fresh-export';cli('fresh-revision',['compose','run',exact/'project.yh','--output',fresh]);fresh_report=json.loads((fresh/'report.json').read_text())
    check('same-status fresh source distinct authority',fresh_report['components'][0]['executionSnapshot']!=old_snapshot and fresh_report['candidates'][0]['availabilityState']['tag']=='Eligible')
    def machine(name,kind,op,path,code=0,output=None,file=False):
        request=dict(format='yuho.machine-request/v0.2-experimental',input_kind=kind,operation=op,path=str(path))
        if output:request['output']=str(output)
        raw=json.dumps(request).encode();req=out/(name+'-request.json');req.write_bytes(raw)
        p=call(name,[y,'machine',req if file else '-'],code,None if file else raw);v=json.loads(p.stdout)
        check('single machine JSON and truthful exit',len(p.stdout.splitlines())==1 and v['success']==(code==0))
        if code:check('failed machine has no authority/payload/export',v['effects']['source_authority']=='not_validated' and v['payload'] is None and not v['exports'])
        return v
    for op in ['check','run']:
        target=out/('machine-source-'+op) if op=='run' else None
        v=machine('machine-source-'+op,'dependency-yh',op,exact/'project.yh',output=target,file=(op=='check'));check('current-source authority',v['effects']['source_authority']=='current_sources')
        if target:check('live CLI/machine eight-file bytes',all(p.read_bytes()==(target/p.name).read_bytes() for p in fresh.iterdir()))
    v=machine('machine-saved-check','dependency-artifact-json','check',original/'artifact.json',file=True);check('saved check static authority',v['effects']['source_authority']=='embedded_artifact' and v['payload']['evaluated'] is False)
    target=out/'machine-saved-replay';v=machine('machine-saved-replay','dependency-artifact-json','replay',original/'artifact.json',output=target);check('replay embedded authority',v['effects']['source_authority']=='embedded_artifact')
    check('saved machine ignores live revision',all(p.read_bytes()==(target/p.name).read_bytes() for p in original.iterdir()))
    machine('source-as-artifact','dependency-artifact-json','check',exact/'project.yh',1);machine('artifact-as-source','dependency-yh','check',original/'artifact.json',1)
    # The same public machine source workflow may select a real SDK analysis.
    selected=out/'SDK-selected-source';selected.mkdir();doc=json.loads((out/'ordinary-typed.json').read_text());(selected/'typed.json').write_text(doc['dependencySources']['typed.json'])
    text=(FIX/'project.yh').read_text().replace('profile native-typed model "m.yh" scenario "s.yh"','profile sdk-typed-v0.3 model "typed.json" entry analysis analysis')
    (selected/'project.yh').write_text(text);cli('SDK-selected-check',['compose','check',selected/'project.yh']);target=out/'SDK-selected-direct'
    cli('SDK-selected-run',['compose','run',selected/'project.yh','--output',target]);sr,_=parity(target)
    check('SDK selected actual condition',ground(sr['components'][0],'q')[0]['predicate']=='condition' and sr['components'][0]['executionLocalScope']['scopeActor']=='actor')
    machine('machine-SDK-source-check','dependency-yh','check',selected/'project.yh',file=True);mt=out/'SDK-selected-machine'
    machine('machine-SDK-source-run','dependency-yh','run',selected/'project.yh',output=mt)
    check('SDK selected CLI/machine eight files',all(p.read_bytes()==(mt/p.name).read_bytes() for p in target.iterdir()))
    result=dict(checks=len(checks),calls=len(calls),output=str(out));(out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
