"""F04: independently specified authored identities versus actual lowering ownership.
All mutable programs, SDK build products, exports and transcripts are external.
"""
import argparse, copy, hashlib, json, shutil, subprocess, tempfile
import xml.etree.ElementTree as E
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXACT = ROOT / 'test/fixtures/dependency-generated-identity/exact'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary', type=Path)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--builddir', type=Path)
    a = ap.parse_args()
    out = a.output or Path(tempfile.mkdtemp(prefix='yuho-f04-'))
    out.mkdir(parents=True, exist_ok=True)
    y = a.binary.resolve()
    checks, calls = [], []
    (out/'expectations-before-execution.json').write_text(json.dumps({
        'no_holes': 'All ordinary/entity/type/both authored variants admit. Exact own tuple supplied T gives q satisfied and candidate Eligible; no incoming/generated hole input.',
        'holes': 'Actual private type/entity/predicate and direct classification collisions reject DEPWRITER. Two valid holes retain two exact generated facts.',
        'authority': 'Same-status source revision changes snapshot; old embedded replay stays identical; live attachment refuses.',
        'scope': 'Wrong nominal correspondence, noninjective entity maps and cross-scope writers reject.'}, indent=2))
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
        (out/'checks.json').write_text(json.dumps(checks, indent=2))
        assert value, name
    def call(name, args, code=0, data=None, cwd=None):
        p = subprocess.run(list(map(str,args)), input=data, cwd=cwd or out, capture_output=True)
        row = dict(name=name,args=list(map(str,args)),cwd=str(cwd or out),exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode())
        calls.append(row); (out/'commands.json').write_text(json.dumps(calls,indent=2,ensure_ascii=False))
        assert p.returncode == code, row
        return p
    def cli(name,args,code=0):
        p=call(name,[y,*args],code)
        return json.loads(p.stdout or p.stderr)
    flags=['--builddir='+str(a.builddir)] if a.builddir else []
    for source, client in [('DependencyGeneratedIdentityClient.hs','builder'),('DependencyIntegrityClient.hs','sdk')]:
        call('compile-'+client,['cabal','exec','--offline',*flags,'--','ghc-9.8.4','-package=yuho','-outputdir',out/(client+'-build'),'-o',out/client,ROOT/'test'/source],cwd=ROOT)
    call('construct-public-SDK-records',[out/'builder',out])
    def sdk(name,doc,code=0):
        f=out/(name+'.json');f.write_text(json.dumps(doc,ensure_ascii=False))
        dest=out/(name+'-export');p=call(name,[out/'sdk','run',f,dest],code)
        if code: check(name+' no publication',not dest.exists())
        return json.loads(p.stdout), dest
    def parity(dest):
        names={'artifact.json','report.json','projection.json','view-bindings.json','view.json','view.xml','view.svg','source-map.json'}
        check('complete eight-file publication',set(p.name for p in dest.iterdir())==names)
        r=json.loads((dest/'report.json').read_text());p=json.loads((dest/'projection.json').read_text())
        check('report/projection parity',r==p['report'])
        check('source map parity',json.loads((dest/'source-map.json').read_text())==p['source_map'])
        g=json.loads((dest/'view.json').read_text());ids={n['id'] for n in g['nodes']}
        check('unique graph and valid endpoints',len(ids)==len(g['nodes']) and all(e['from'] in ids and e['to'] in ids for e in g['edges']))
        x=E.parse(dest/'view.xml').getroot();check('XML exact graph identities',ids=={n.attrib['id'] for n in x.iter() if n.tag.endswith('node')})
        s=E.parse(dest/'view.svg').getroot();dom=[n.attrib['id'] for n in s.iter() if 'id' in n.attrib]
        check('SVG unique DOM and semantic associations',len(dom)==len(set(dom)) and ids<={n.attrib['data-semantic-id'] for n in s.iter() if 'data-semantic-id' in n.attrib})
        bindings=json.loads((dest/'view-bindings.json').read_text())
        check('view binding coverage',{b['semantic_id'] for b in bindings['included']}==ids)
        return r,p
    def observation(r,actor,ty,event,sdk_profile=False):
        c=r['components'][0];p=c['executionRequest']['program']
        check('actual authored entity/type retained',ty in p['entity_types'] and {'id':actor,'type':ty} in p['entities'])
        check('no generated hole objects or inputs',not r['bindings'] and not c['executionIncoming'] and len(p['entity_types'])==2 and len(p['entities'])==2)
        reads=[i for row in c['executionReads'] if row['root']==['expression','q'] for i in row['input_records']]
        check('actual structural read retains supplied identity',len(reads)==1 and reads[0]['kind']=='ground_predicate' and reads[0]['predicate']=='own' and reads[0]['arguments']==[actor,event] and reads[0]['classification']['status']=='satisfied')
        check('classification reason provenance',reads[0]['classification']['reason'].startswith('generated SDK assessment ') if sdk_profile else reads[0]['classification']['reason']=='supplied')
        guard=r['candidates'][0]['availabilityGuard'];o=guard['conversionSource']
        check('candidate exact scoped observation',r['candidates'][0]['availabilityState']['tag']=='Eligible' and o['observationSnapshot']==c['executionSnapshot'] and o['observationScope']==c['executionScope'] and o['observationPort']['portObject']=='q' and guard['conversionPolicy']=='yuho.condition-identity/v1' and guard['conversionCauses']==[])
    # Exact independent reproduction, unchanged source bytes.
    exact=out/'exact';shutil.copytree(EXACT,exact)
    ordinary=cli('exact-ordinary-run',['run',exact/'m.yh','--scenario',exact/'s.yh'])
    cli('exact-ordinary-check',['check',exact/'m.yh','--scenario',exact/'s.yh'])
    cli('exact-project-check',['compose','check',exact/'project.yh'])
    dest=out/'exact-export';cli('exact-project-run',['compose','run',exact/'project.yh','--output',dest])
    r,p=parity(dest);observation(r,'dep_template_entity','person','e')
    check('ordinary native backend parity',all(r['components'][0]['executionBackend'][f]==ordinary[f] for f in ('expressions','rules','propositions')))
    check('original source recovery',p['document']['dependencySources']['m.yh']==(EXACT/'m.yh').read_text())
    _, sdk_native=sdk('exact-native-SDK',p['document']);parity(sdk_native)
    check('exact source/public SDK eight-file parity',all(f.read_bytes()==(sdk_native/f.name).read_bytes() for f in dest.iterdir()))
    for label,actor,ty in [('ordinary','actor','person'),('type','actor','dep_template_type'),('both','dep_template_entity','dep_template_type')]:
        w=out/('native-'+label);w.mkdir()
        for name in ['m.yh','s.yh','project.yh']:
            text=(EXACT/name).read_text().replace('dep_template_entity',actor).replace('person',ty)
            (w/name).write_text(text)
        cli('native-'+label+'-check',['compose','check',w/'project.yh'])
        target=out/('native-'+label+'-export');cli('native-'+label+'-run',['compose','run',w/'project.yh','--output',target])
        rr,_=parity(target);observation(rr,actor,ty,'e')
    no_candidate=out/'source-no-candidate.yh'
    no_candidate.write_text((EXACT/'project.yh').read_text().split(' candidate candidate ')[0]+' }')
    # Keep relative model/scenario resolution beside this alternative project.
    for name in ['m.yh','s.yh']:(out/name).write_bytes((EXACT/name).read_bytes())
    cli('native-without-candidate',['compose','check',no_candidate])
    # Public SDK in-memory templates and actual selected typed-v0.3 analyses.
    docs={}
    for label,ty,actor in [('ordinary','person','actor'),('entity','person','dep_template_entity'),('type','dep_template_type','actor'),('both','dep_template_type','dep_template_entity')]:
        for profile in ('template','typed'):
            name=label+'-'+profile;d=json.loads((out/(name+'.json')).read_text());docs[name]=d
            r,export=sdk('run-'+name,d);_,p=parity(export);observation(r,actor,ty,'event:one',profile=='typed')
            checked=p['checked_components'][0]
            check('no slots means no private identities',checked['slots']==[])
            if profile=='typed':
                f=out/(name+'-source.json');f.write_text(d['dependencySources']['typed.json'])
                response=out/(name+'-standalone.json');call('standalone-'+name,[out/'builder','typed',f,response])
                backend=json.loads(response.read_text())
                request=json.loads(Path(str(response)+'.request.json').read_text())
                check('SDK standalone actual inputs parity',request['program']==r['components'][0]['executionRequest']['program'])
                check('original SDK assessment not relabelled',json.loads(d['dependencySources']['typed.json'])['typedAssessments'][0]['typedAssessmentReason']=='supplied')
                check('selected SDK standalone response parity',all(r['components'][0]['executionBackend'][k]==backend[k] for k in ('expressions','rules','propositions')))
                check('actual selected SDK scope retained',r['components'][0]['executionLocalScope']['scopeActor']==actor)
            # Admission must not depend on whether a candidate consumes the result.
            d2=copy.deepcopy(d);d2['dependencyPlan']['planCandidates']=[]
            rr,_=sdk('no-candidate-'+name,d2);check('no-candidate admission',rr['components'][0]['executionState']=='evaluated' and rr['candidates']==[])
    # New external source control: both spellings, additional nominal/entity,
    # a named requirement and a real rule/proposition; three independent outcomes.
    new=out/'independent';new.mkdir()
    model='''typed-rules-model Owned {
 entity-type dep_template_type; entity-type event; entity-type property;
 entity dep_template_entity as dep_template_type; entity event:one as event;
 entity item:two as property;
 predicate own(dep_template_type,event) kind relationship;
 predicate inspect(dep_template_type,property) kind relationship;
 requirement q = own(dep_template_entity,event:one);
 requirement local = inspect(dep_template_entity,item:two);
 proposition p; rule r establishes proposition p when own(dep_template_entity,event:one);
 limitation "Fictional control; authored names are not lowering ownership";
}'''
    scenario='''typed-rules-scenario S for Owned {
 classify own(dep_template_entity,event:one) as proved reason "supplied";
 classify inspect(dep_template_entity,item:two) as not_proved reason "Independent false";
}'''
    project=(EXACT/'project.yh').read_text().replace('nominal person as role:p','nominal dep_template_type as role:p').replace('entity e as i','entity event:one as i')
    project=project.replace('nominal event as role:e;','nominal event as role:e; nominal property as role:property;').replace('identity i nominal role:e;','identity i nominal role:e; identity object:two nominal role:property;')
    project=project.replace('entity event:one as i;','entity event:one as i; entity item:two as object:two;')
    (new/'m.yh').write_text(model);(new/'s.yh').write_text(scenario);(new/'project.yh').write_text(project)
    cli('independent-native-check',['check',new/'m.yh','--scenario',new/'s.yh'])
    ordinary=cli('independent-native-run',['run',new/'m.yh','--scenario',new/'s.yh'])
    cli('independent-project-check',['compose','check',new/'project.yh'])
    export=out/'independent-export';cli('independent-project-run',['compose','run',new/'project.yh','--output',export]);r,p=parity(export)
    check('independent hand-specified observations',{x['id']:x['status'] for x in r['components'][0]['executionBackend']['expressions']}=={'q':'satisfied','local':'not_satisfied'})
    check('independent ordinary parity',all(r['components'][0]['executionBackend'][f]==ordinary[f] for f in ('expressions','rules','propositions')))
    maps=p['checked_components'][0]['identity_maps'];check('authored project identity maps retained',['dep_template_entity','a'] in maps[1] and ['dep_template_type','role:p'] in maps[0])
    for row in p['source_map']['sources']:
        check('exact retained UTF-8 source digest',hashlib.sha256(row['utf8'].encode()).hexdigest()==row['sha256'])
    # Scope and nominal correctness remain checked even for familiar spellings.
    for name,mutate in [('wrong-nominal',lambda d:d['dependencyPlan']['planComponents'][0]['componentNominals'].__setitem__(0,['dep_template_type','role:event'])),('noninjective',lambda d:d['dependencyPlan']['planComponents'][0]['componentEntities'].__setitem__(1,['event:one','project:actor'])),('wrong-existing-actor',lambda d:d['dependencyPlan']['planComponents'][0].update(componentEntities=[['dep_template_entity','project:event'],['event:one','project:actor']]))]:
        d=copy.deepcopy(docs['both-template']);mutate(d);v,_=sdk(name,d,1);check(name+' rejected',v['dependencyCode']==('DEPNAME' if name=='noninjective' else 'DEPSCOPE'))
    # SDK generated names are reserved only when the compiler creates them.
    for name,doc in [('entity',docs['entity-template']),('type',docs['type-template']),('both',docs['both-template'])]:
        d=copy.deepcopy(doc);d['dependencyPlan']['planComponents'][0]['componentTemplate']['templateConditions']=['gate']
        v,_=sdk('hole-'+name,d,1);check('actual helper collision '+name,v['dependencyCode']=='DEPWRITER')
    generated='dep_'+hashlib.sha256(b'gate').hexdigest()
    d=copy.deepcopy(docs['ordinary-template']);t=d['dependencyPlan']['planComponents'][0]['componentTemplate']
    t['templatePredicates'].append([generated,['person']]);t['templateFacts'].append([generated,['actor'],'Satisfied','Authored, no holes'])
    t['templateRequirements']=[['q',dict(tag='TemplateAtom',contents=[generated,['actor']])]]
    rr,_=sdk('no-hole-authored-slot-looking-predicate',d)
    check('unclaimed generated-looking predicate remains authored',rr['candidates'][0]['availabilityState']['tag']=='Eligible' and not rr['bindings'] and not rr['components'][0]['executionIncoming'])
    d=copy.deepcopy(docs['ordinary-template']);t=d['dependencyPlan']['planComponents'][0]['componentTemplate'];t['templateConditions']=['gate'];t['templatePredicates'].append([generated,['person']])
    v,_=sdk('hole-generated-predicate',d,1);check('actual generated predicate collision',v['dependencyCode']=='DEPWRITER')
    d=copy.deepcopy(docs['ordinary-template']);t=d['dependencyPlan']['planComponents'][0]['componentTemplate'];t['templateConditions']=['gate'];t['templateFacts'].append(['gate',['actor'],'Satisfied','forged'])
    v,_=sdk('hole-direct-fact',d,1);check('direct SDK hole fact rejected',v['dependencyCode']=='DEPWRITER')
    # Source path collision controls: no output can precede a successful check.
    for name,text in [('entity',(EXACT/'m.yh').read_text()),('type',(EXACT/'m.yh').read_text().replace('person','dep_template_type').replace('dep_template_entity','actor')),('predicate',(EXACT/'m.yh').read_text().replace('dep_template_entity','actor').replace('requirement q =',f'predicate {generated}(person) kind relationship; requirement q ='))]:
        w=out/('source-hole-'+name);shutil.copytree(EXACT,w);(w/'m.yh').write_text(text.replace('requirement q =','dependency-condition gate type technical-condition; requirement q ='))
        v=cli('source-hole-'+name,['compose','check',w/'project.yh'],1);check('source exact generated collision '+name,v['dependencyCode']=='DEPWRITER')
    # Valid native two-hole recipient, with a similar but distinct authored name.
    w=out/'valid-holes';w.mkdir()
    base=(EXACT/'m.yh').read_text().replace('dep_template_entity','actor')
    (w/'m.yh').write_text(base);(w/'s.yh').write_text((EXACT/'s.yh').read_text().replace('dep_template_entity','actor'))
    (w/'recipient.yh').write_text(base.replace('requirement q =','entity dep_template_entity:authored as person; dependency-condition gate type technical-condition; dependency-condition gate:two type technical-condition; requirement extra = condition(gate:two); requirement q = all(condition(gate),').replace('own(actor,e);','own(actor,e));'))
    recipient='component recipient profile native-typed model "recipient.yh" scenario "s.yh" scope sc { nominal person as role:p; nominal event as role:e; entity actor as a; entity e as i; } rationale "Explicit independent recipient";'
    binding='bind link from c . expression q to recipient . condition gate mapping "yuho.condition-identity/v1" rationale "Technical only" refs origin;'
    binding2=binding.replace('bind link','bind second').replace('condition gate ','condition gate:two ')
    proj=(EXACT/'project.yh').read_text().replace('dep_template_entity','actor').replace(' candidate candidate ', ' '+recipient+' '+binding+' '+binding2+' candidate candidate ').replace('guard c . expression q','guard recipient . expression q')
    (w/'project.yh').write_text(proj)
    cli('valid-holes-check',['compose','check',w/'project.yh']);dest=out/'valid-holes-export';cli('valid-holes-run',['compose','run',w/'project.yh','--output',dest]);rr,pp=parity(dest)
    recipient_record=next(x for x in rr['components'] if x['executionComponent']=='recipient')
    check('two exact generated runtime inputs',len(recipient_record['executionIncoming'])==2 and len(rr['bindings'])==2 and len({x['conversionGeneratedInput']['predicate'] for x in rr['bindings']})==2)
    check('similar authored name remains authored',{'id':'dep_template_entity:authored','type':'person'} in recipient_record['executionRequest']['program']['entities'])
    wrong_scope=proj.replace(recipient,recipient.replace('scope sc','scope other'))
    wrong_scope=wrong_scope.replace(' '+recipient.replace('scope sc','scope other'),
        ' scope other actor a context i { identity a nominal role:p; identity i nominal role:e; } '+recipient.replace('scope sc','scope other'))
    duplicate=proj.replace(binding2,binding2+' '+binding.replace('bind link','bind duplicate'))
    for name,text,code in [('duplicate-writer',duplicate,'DEPWRITER'),('wrong-scope',wrong_scope,'DEPSCOPE')]:
        f=w/(name+'.yh');f.write_text(text);v=cli(name,['compose','check',f],1);check(name,v['dependencyCode']==code)
    bad=w/'direct-hole.yh';(w/'bad-s.yh').write_text((w/'s.yh').read_text().replace(' }',' classify condition(gate) as proved reason "forged"; }'))
    bad.write_text(proj.replace('model "recipient.yh" scenario "s.yh"','model "recipient.yh" scenario "bad-s.yh"'));v=cli('source-direct-hole',['compose','check',bad],1);check('source direct hole fact refused',v['dependencyCode']=='DEPWRITER')
    for name,dest in [('exact',out/'exact-export'),('independent',export),('holes',out/'valid-holes-export')]:
        replay=out/(name+'-replay');cli(name+'-replay',['compose','replay',dest/'artifact.json','--output',replay])
        check('eight immutable replay bytes '+name,all(f.read_bytes()==(replay/f.name).read_bytes() for f in dest.iterdir()))
    # Fresh source authority changes on a same-status reason edit; saved bytes do not.
    (new/'s.yh').write_text(scenario.replace('supplied','same-status revision'))
    v=cli('same-status-attachment',['compose','check',new/'project.yh','--against',export/'artifact.json'],1);check('changed attachment refused',v['dependencyCode']=='DEPSTALE')
    changed=out/'independent-changed';cli('same-status-fresh',['compose','run',new/'project.yh','--output',changed]);fresh=json.loads((changed/'report.json').read_text())
    check('fresh revision changes authority not truth',fresh['components'][0]['executionSnapshot']!=r['components'][0]['executionSnapshot'] and fresh['candidates'][0]['availabilityState']==r['candidates'][0]['availabilityState'])
    def machine(name,kind,op,path,code=0,destination=None,file=False):
        req=dict(format='yuho.machine-request/v0.2-experimental',input_kind=kind,operation=op,path=str(path))
        if destination:req['output']=str(destination)
        raw=json.dumps(req).encode();f=out/(name+'-request.json');f.write_bytes(raw)
        p=call(name,[y,'machine',f if file else '-'],code,None if file else raw)
        v=json.loads(p.stdout);check('machine one response and truthful exit',len(p.stdout.splitlines())==1 and v['success']==(code==0))
        if code:check('machine wrong-kind authority/no exports',v['effects']['source_authority']=='not_validated' and v['payload'] is None and v['exports']==[])
        return v
    for mode in ['check','run']:
        target=out/('machine-'+mode+'-export') if mode=='run' else None
        v=machine('machine-source-'+mode,'dependency-yh',mode,exact/'project.yh',destination=target,file=(mode=='check'))
        check('machine current authority',v['effects']['source_authority']=='current_sources')
        if target:check('machine/direct export parity',all(f.read_bytes()==(target/f.name).read_bytes() for f in (out/'exact-export').iterdir()))
    v=machine('machine-artifact-check','dependency-artifact-json','check',export/'artifact.json');check('saved authority/static check',v['effects']['source_authority']=='embedded_artifact' and v['payload']['evaluated'] is False)
    target=out/'machine-artifact-replay';machine('machine-artifact-replay','dependency-artifact-json','replay',export/'artifact.json',destination=target,file=True)
    check('saved replay ignores changed live bytes',all(f.read_bytes()==(target/f.name).read_bytes() for f in export.iterdir()))
    machine('machine-live-as-artifact','dependency-artifact-json','check',exact/'project.yh',1)
    machine('machine-artifact-as-live','dependency-yh','check',export/'artifact.json',1)
    check('original source files unmodified',all((exact/n).read_bytes()==(EXACT/n).read_bytes() for n in ['m.yh','s.yh','project.yh']))
    result=dict(checks=len(checks),calls=len(calls),output=str(out));(out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
