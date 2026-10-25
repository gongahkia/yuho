"""Tranche 02.1 independent structural-tuple / causal-read / authority oracles.
All source mutations, builds and exports are external. No expected-value generator.
"""
import argparse,copy,json,os,shutil,subprocess,tempfile,xml.etree.ElementTree as E
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'test/fixtures/dependency-integrity'

def main():
 p=argparse.ArgumentParser();p.add_argument('binary',type=Path);p.add_argument('--builddir',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
 out=a.output or Path(tempfile.mkdtemp(prefix='yuho-integrity-'));out.mkdir(parents=True,exist_ok=True)
 input_validator=jsonschema.Draft202012Validator(json.loads((ROOT/'schema/typed-read-input-v1.schema.json').read_text()))
 machine_validator=jsonschema.Draft202012Validator(json.loads((ROOT/'schema/machine-response-v0.2-experimental.schema.json').read_text()))
 binary=a.binary.resolve();kernel=binary.parents[3]/'yuho-kernel/build/yuho-kernel/yuho-kernel';calls=[];checks=[]
 def call(name,args,exit=0,data=None):
  r=subprocess.run(list(map(str,args)),input=data,cwd=ROOT,capture_output=True)
  row=dict(name=name,args=list(map(str,args)),cwd=str(ROOT),exit=r.returncode,stdout=r.stdout.decode(),stderr=r.stderr.decode());calls.append(row)
  (out/'commands.json').write_text(json.dumps(calls,indent=2,ensure_ascii=False)+'\n');assert r.returncode==exit,row
  return r
 def check(name,condition):assert condition,name;checks.append(name)
 client=out/'sdk-client'
 call('public-client-compile',['cabal','exec','--offline',*(['--builddir='+str(a.builddir)] if a.builddir else []),'--','ghc-9.8.4','-package=yuho','-outputdir',out/'client-build','-o',client,ROOT/'test/DependencyIntegrityClient.hs'])
 def sdk(name,doc,code=0):
  file=out/(name+'.json');file.write_text(json.dumps(doc,ensure_ascii=False));destination=out/(name+'-export')
  r=call(name,[client,'run',file,destination],code);v=json.loads(r.stdout)
  if code:check(name+' no partial export',not destination.exists())
  return v,destination
 def candidate(template,owner,obj,identity):
  c=copy.deepcopy(template);c.update(candidateIdentity=identity);c['candidateGuard'].update(portComponent=owner,portObject=obj);return c
 def backend(report,owner):return next(c for c in report['components'] if c['executionComponent']==owner)
 def parity(directory):
  graph=json.loads((directory/'view.json').read_text());ids={n['id'] for n in graph['nodes']};check('unique semantic graph nodes',len(ids)==len(graph['nodes']))
  check('valid graph endpoints',all(e['from'] in ids and e['to'] in ids for e in graph['edges']))
  xml=E.parse(directory/'view.xml').getroot();check('JSON XML identity parity',ids=={n.attrib['id'] for n in xml.iter() if n.tag.endswith('node')})
  svg=E.parse(directory/'view.svg').getroot();dom=[n.attrib['id'] for n in svg.iter() if 'id' in n.attrib];check('injective SVG DOM identities',len(dom)==len(set(dom)))
  check('SVG graph associations',ids<={n.attrib['data-semantic-id'] for n in svg.iter() if 'data-semantic-id' in n.attrib})
  report=json.loads((directory/'report.json').read_text())
  for component in report['components']:
   for read in component['executionReads']:
    for item in read['input_records']:input_validator.validate(item)
  projection=json.loads((directory/'projection.json').read_text());check('complete report/projection correspondence',projection['report']==report)
  bindings=json.loads((directory/'view-bindings.json').read_text());included={r['semantic_id']:r for r in bindings['included']};check('view record coverage',set(included)==ids)
  check('exact source map',json.loads((directory/'source-map.json').read_text())==projection['source_map'])
  return graph
 # R1 exact original primitive collision: target p(a(b) is genuinely missing.
 original=json.loads((FIX/'ground-alias.json').read_text());r,_=sdk('original-ground-alias',original,1)
 check('original false eligibility refused statically',r['dependencyCode']=='DEPMISSING' and 'missing ground classification' in r['dependencyMessage'])
 # Structural tuple dictionary is the oracle, not any production key helper.
 tuples=[('p',['a(b'],'Satisfied'),('p(a',['b'],'NotSatisfied'),('pair',['x,y','z'],'Satisfied'),('pair',['x','y,z'],'NotSatisfied'),('ordered',['x','y'],'Satisfied'),('ordered',['y','x'],'Unresolved'),('r',['a(b,c'],'Satisfied'),('r(a',['b','c'],'NotSatisfied'),('規則',['α(β,γ'],'Satisfied'),('規則(α',['β,γ'],'NotSatisfied'),('long:'+('λ'*100),['x'],'Unresolved')]
 d=copy.deepcopy(original);plan=d['dependencyPlan'];t=plan['planComponents'][0]['componentTemplate'];t['templateEntities']=[['person:a','person'],['event:i','event']]+[[x,'person'] for x in sorted({x for _,args,_ in tuples for x in args})]
 signatures={n:len(args) for n,args,_ in tuples};t['templatePredicates']=[[n,['person']*arity] for n,arity in signatures.items()]
 t['templateRequirements']=[['q:'+str(i),{'tag':'TemplateAtom','contents':[n,args]}] for i,(n,args,_) in enumerate(tuples)]
 t['templateFacts']=[[n,args,v,'Independent exact tuple '+str(i)] for i,(n,args,v) in enumerate(tuples)]
 c=plan['planCandidates'][0];plan['planCandidates']=[candidate(c,'s','q:'+str(i),'candidate:'+str(i)) for i in range(len(tuples))]
 report,directory=sdk('structural-tuples',d);parity(directory);component=backend(report,'s')
 expected={(n,tuple(args)):(v,'Independent exact tuple '+str(i)) for i,(n,args,v) in enumerate(tuples)}
 status={'Satisfied':'satisfied','NotSatisfied':'not_satisfied','Unresolved':'unresolved'};avail={'Satisfied':'Eligible','NotSatisfied':'Ineligible','Unresolved':'EligibilityUnresolved'}
 for i,(n,args,value) in enumerate(tuples):
  q='q:'+str(i);rows=[r for r in component['executionReads'] if r['root']==['expression',q]]
  inputs=[x for r in rows for x in r['input_records']];check('exact tuple input '+q,len(inputs)==1 and (inputs[0]['predicate'],tuple(inputs[0]['arguments']))==(n,tuple(args)))
  check('classification is exact supplied record '+q,inputs[0]['classification']==dict(status=status[value],reason=expected[(n,tuple(args))][1]))
  cand=next(c for c in report['candidates'] if c['availabilityCandidate']['candidateIdentity']=='candidate:'+str(i))
  check('candidate exact tuple value '+q,cand['availabilityState']['tag']==avail[value] and cand['availabilityGuard']['conversionSource']['observationRecord']['status']==status[value])
 # Same display / distinct tuples are allowed; only exact duplicates fail.
 missing=copy.deepcopy(d);missing['dependencyPlan']['planComponents'][0]['componentTemplate']['templateFacts'].pop(1)
 r,_=sdk('missing-exact-tuple-with-alias',missing,1);check('missing alias does not become T/F/U',r['dependencyCode']=='DEPMISSING')
 duplicate=copy.deepcopy(d);duplicate['dependencyPlan']['planComponents'][0]['componentTemplate']['templateFacts'].append(copy.deepcopy(t['templateFacts'][0]))
 r,_=sdk('duplicate-identical-tuple',duplicate,1);check('identical tuple duplicate refused',r['dependencyCode']=='DEPFORMAT')
 request=component['executionRequest'];kernel_result=json.loads(call('standalone-distinct-tuples',[kernel],data=json.dumps(request).encode()+b'\n').stdout)
 check('standalone exact values',[r['status'] for r in kernel_result['expressions']]==[status[v] for _,_,v in tuples])
 # The exact old unchecked kernel request must now refuse the missing tuple.
 request=json.loads((FIX/'ground-alias-request.json').read_text());r=json.loads(call('standalone-original-collision',[kernel],data=json.dumps(request).encode()+b'\n').stdout)
 check('standalone unsupplied tuple refused',r['status']=='rejected' and 'missing ground classification' in json.dumps(r))
 bad=copy.deepcopy(component['executionRequest']);bad['program']['facts'].append(copy.deepcopy(bad['program']['facts'][0]));r=json.loads(call('standalone-duplicate',[kernel],data=json.dumps(bad).encode()+b'\n').stdout);check('standalone duplicate refused',r['status']=='rejected')
 bad=copy.deepcopy(component['executionRequest']);bad['program']['facts'][0]['arguments']=[];r=json.loads(call('standalone-wrong-arity',[kernel],data=json.dumps(bad).encode()+b'\n').stdout);check('arity is checked',r['status']=='rejected')
 # R2 exact reviewer reference collision, then genuine reference chains.
 original2=json.loads((FIX/'false-conflict.json').read_text());report,directory=sdk('original-false-conflict',original2)
 check('original false conflict removed',report['candidates'][0]['availabilityGuard']['conversionCauses']==[] and report['candidates'][0]['availabilityState']['tag']=='Ineligible');parity(directory)
 d=copy.deepcopy(original2);plan=d['dependencyPlan'];t=plan['planComponents'][1]['componentTemplate'];fake=t['templateRequirements'][0][0]
 t['templatePredicates'].append(['local:unknown',['person','event']]);t['templateFacts'].append(['local:unknown',['person:a','event:i'],'Unresolved','Independent unknown has no conflict origin'])
 ref=lambda key:dict(tag='TemplateReference',contents=key)
 t['templateRequirements'] += [['q:chain:規則',ref('q:uses-slot')],['q:chain:deep',ref('q:chain:規則')],['q:strong',dict(tag='TemplateAll',contents=[dict(tag='TemplateAtom',contents=['own',['person:a','event:i']]),ref('q:chain:deep')])],['q:local',dict(tag='TemplateAtom',contents=['own',['person:a','event:i']])],['q:unknown',dict(tag='TemplateAtom',contents=['local:unknown',['person:a','event:i']])]]
 cases=[('q:independent','Ineligible',False),('q:uses-slot','EligibilityUnresolved',True),('q:chain:deep','EligibilityUnresolved',True),('q:strong','Ineligible',True),('q:local','Ineligible',False),('q:unknown','EligibilityUnresolved',False)]
 plan['planCandidates']=[candidate(plan['planCandidates'][0],'d',q,'candidate:'+q) for q,_,_ in cases]
 report,directory=sdk('causal-reference-chains',d);graph=parity(directory);comp=backend(report,'d');binding=report['bindings'][0];g=binding['conversionGeneratedInput'];source=binding['conversionSource']
 for q,state,conflicted in cases:
  c=next(c for c in report['candidates'] if c['availabilityCandidate']['candidateGuard']['portObject']==q);guard=c['availabilityGuard'];causes=guard['conversionCauses']
  check('actual value '+q,c['availabilityState']['tag']==state)
  check('exact original conflict origin '+q,any(x=='conflict:'+source['observationIdentity'] for x in causes)==conflicted)
  rows=[r for r in comp['executionReads'] if r['root']==['expression',q]];inputs=[x for r in rows for x in r['input_records']]
  used=any(x['kind']=='ground_predicate' and x['predicate']==g['predicate'] and x['arguments']==g['arguments'] for x in inputs)
  check('real causal input '+q,used==conflicted)
  convert=next(n for n in graph['nodes'] if n['kind']=='conversion' and n['label'].startswith(c['availabilityCandidate']['candidateIdentity']+' |'))
  check('diagram conflict matches actual cause '+q,('conflict origin retained' in convert['label'])==conflicted)
 rows=[r for r in comp['executionReads'] if r['root']==['expression','q:independent']]
 check('same text remains separate semantic category',any(x.get('requirement')==fake for r in rows for x in r['input_records']) and all(x['kind']!='ground_predicate' or x['predicate']!=g['predicate'] for r in rows for x in r['input_records']))
 strong=[r for r in comp['executionReads'] if r['root']==['expression','q:strong']]
 check('eager decisive F retains F and U operands',{r['status'] for r in strong}>={'not_satisfied','unresolved'} and len({tuple(r['path']) for r in strong})==len(strong))
 # Duplicate occurrence identities in a second actor/allegation never join.
 two=copy.deepcopy(d);p2=two['dependencyPlan'];scope_a=p2['planScopes'][0];scope_a.update(scopeCase='case:integrity',scopeAllegation='allegation:a')
 scope_b=copy.deepcopy(scope_a);scope_b.update(scopeIdentity='scope:b',scopeActor='project:b',scopeContext='project:j',scopeAllegation='allegation:b',scopeEntities=[['project:b','role:person'],['project:j','role:event']]);p2['planScopes'].append(scope_b)
 for c in copy.deepcopy(p2['planComponents']):
  c['componentIdentity']+=':b';c['componentScope']='scope:b';c['componentEntities']=[['person:a','project:b'],['event:i','project:j']]
  if c['componentTemplate']:c['componentTemplate']['templateFacts'][0][2]='Satisfied'
  else:c['componentScenario']='facts-b.yh'
  p2['planComponents'].append(c)
 two['dependencySources']['facts-b.yh']=two['dependencySources']['facts.yh'].replace('support(person:a,event:i) as proved','support(person:a,event:i) as not_proved')
 b=copy.deepcopy(p2['planBindings'][0]);b.update(bindingIdentity='conflict:b',bindingComponent='d:b');b['bindingPort']['portComponent']='s:b';p2['planBindings'].append(b)
 for c in copy.deepcopy(p2['planCandidates']):c['candidateIdentity']+=':b';c['candidateScope']='scope:b';c['candidateGuard']['portComponent']='d:b';p2['planCandidates'].append(c)
 report,directory=sdk('two-scopes',two);parity(directory)
 for c in report['candidates']:
  b=c['availabilityCandidate']['candidateScope']=='scope:b';obs=c['availabilityGuard']['conversionSource'];causes=c['availabilityGuard']['conversionCauses']
  check('actor and allegation isolation',obs['observationScope']['scopeActor']==('project:b' if b else 'project:a') and obs['observationScope']['scopeAllegation']==('allegation:b' if b else 'allegation:a'))
  check('no cross-actor conflict',not any(x.startswith('conflict:') for x in causes) if b else True)
  producer=backend(report,obs['observationPort']['portComponent']);check('actual occurrence snapshot retained',obs['observationSnapshot']==producer['executionSnapshot'])
 expected_b={'q:independent':'Eligible','q:uses-slot':'Ineligible','q:chain:deep':'Ineligible','q:strong':'Ineligible','q:local':'Eligible','q:unknown':'EligibilityUnresolved'}
 for c in report['candidates']:
  if c['availabilityCandidate']['candidateScope']=='scope:b':check('scope B independent exact guard outcome',c['availabilityState']['tag']==expected_b[c['availabilityCandidate']['candidateGuard']['portObject']])
 for binding in report['bindings']:
  is_b=binding['conversionIdentity']=='conflict:b';source=binding['conversionSource'];owner='d:b' if is_b else 'd';actual=backend(report,owner)
  check('scope-specific converted value',binding['conversionValue']==('NotSatisfied' if is_b else 'Unresolved'))
  check('conversion pins actual source component',source['observationPort']['portComponent']==('s:b' if is_b else 's') and source['observationSnapshot']==backend(report,source['observationPort']['portComponent'])['executionSnapshot'])
  generated=binding['conversionGeneratedInput'];reads=[x for r in actual['executionReads'] if r['root']==['expression','q:uses-slot'] for x in r['input_records']]
  check('scope-specific actual generated classification',len(reads)==1 and reads[0]['predicate']==generated['predicate'] and reads[0]['arguments']==generated['arguments'] and reads[0]['classification']['status']==('not_satisfied' if is_b else 'unresolved') and reads[0]['classification']['reason']==generated['reason'])
 check('scope B independent positive',{c['availabilityState']['tag'] for c in report['candidates'] if c['availabilityCandidate']['candidateIdentity']=='candidate:q:independent:b'}=={'Eligible'})
 # R3 exact authority operations, one JSON response, no implicit kind casts.
 authority=out/'authority';shutil.copytree(FIX/'authority',authority);project=authority/'project.yh'
 def machine(name,kind,op,path,code=0,output=None,file=False):
  req=dict(format='yuho.machine-request/v0.2-experimental',input_kind=kind,operation=op,path=str(path))
  if output is not None:req['output']=str(output)
  argv=[binary,'machine','-'];data=json.dumps(req).encode()
  if file:
   request=out/(name+'-request.json');request.write_bytes(data);argv=[binary,'machine',request];data=None
  r=call(name,argv,code,data);check('exactly one machine JSON line',len(r.stdout.splitlines())==1);v=json.loads(r.stdout);machine_validator.validate(v);check('machine exit and success agree',v['success']==(code==0))
  if code:check('failed kind/operation has no authority/payload/exports',v['payload'] is None and not v['exports'] and v['effects']['source_authority']=='not_validated' and bool(v['diagnostics']))
  return v
 first=machine('live-check','dependency-yh','check',project);check('source check does not evaluate',first['payload']['evaluated'] is False and first['effects']['source_authority']=='current_sources')
 exports=out/'live-export';machine('live-run','dependency-yh','run',project,output=exports,file=True);saved=exports/'artifact.json'
 frozen=machine('artifact-check','dependency-artifact-json','check',saved,file=True);check('real artifact authority',frozen['effects']['source_authority']=='embedded_artifact' and frozen['payload']['evaluated'] is False)
 machine('artifact-replay','dependency-artifact-json','replay',saved,output=out/'artifact-replay')
 for kind,path in [('dependency-artifact-json',project),('dependency-yh',saved)]:
  for op in (['check','replay'] if kind=='dependency-artifact-json' else ['check','run']):
   target=out/('wrong-kind-'+kind+'-'+op);v=machine('wrong-kind-'+kind+'-'+op,kind,op,path,1,output=target if op!='check' else None,file=op=='check');check('no wrong-kind output',not target.exists())
 for name,content in [('truncated','{"artifactFormatVersion":'),('lookalike',json.dumps({'artifactFormatVersion':'yuho.dependency-artifact/v0.1-experimental'}))]:
  path=out/(name+'.json');path.write_text(content);machine(name,'dependency-artifact-json','check',path,1)
 artifact=json.loads(saved.read_text())
 for name,field,value in [('unknown-format','artifactFormatVersion','yuho.dependency-artifact/v999'),('tampered-source','artifactSourceDigest','0'*64),('tampered-execution','artifactExecutionDigest','0'*64)]:
  altered=copy.deepcopy(artifact);altered[field]=value;path=out/(name+'.json');path.write_text(json.dumps(altered));machine(name+'-check','dependency-artifact-json','check',path,0 if name=='tampered-execution' else 1)
  machine(name+'-replay','dependency-artifact-json','replay',path,1,output=out/(name+'-output'))
 source=authority/'source.yh';previous=source.read_bytes();source.write_bytes(previous+b'\n// Same result, different current-source authority\n')
 second=machine('changed-live-check','dependency-yh','check',project);check('fresh check pins live edit',first['payload']['snapshot']!=second['payload']['snapshot'])
 retained=machine('saved-after-live-edit','dependency-artifact-json','check',saved);check('artifact check pins original bytes',retained['payload']['snapshot']==frozen['payload']['snapshot'])
 machine('replay-after-live-edit','dependency-artifact-json','replay',saved,output=out/'frozen-after-edit',file=True)
 check('unchanged immutable replay bytes',all((exports/n).read_bytes()==(out/'frozen-after-edit'/n).read_bytes() for n in ['artifact.json','report.json','projection.json','view-bindings.json','view.json','view.xml','view.svg','source-map.json']))
 source.rename(authority/'source.unavailable')
 machine('artifact-without-live-source','dependency-artifact-json','check',saved)
 machine('wrong-kind-never-loads-live-closure','dependency-artifact-json','check',project,1)
 for name,path in [('missing',out/'no-such-file'),('directory',authority)]:machine(name,'dependency-artifact-json','check',path,1)
 unreadable=out/'unreadable-artifact.json';unreadable.write_bytes(saved.read_bytes());unreadable.chmod(0)
 try:
  if not os.access(unreadable,os.R_OK):machine('unreadable-artifact','dependency-artifact-json','check',unreadable,1)
 finally:unreadable.chmod(0o600)
 machine('existing-output','dependency-artifact-json','replay',saved,1,output=exports)
 # Genuine unaffected saved v0.1 execution identity is preserved; unsafe old
 # snapshots cannot be replayed as though their false observations were valid.
 old=FIX/'normal-v01-artifact.json';old_artifact=json.loads(old.read_text());destination=out/'old-v01-replay'
 machine('unaffected-v01-artifact-replay','dependency-artifact-json','replay',old,output=destination)
 check('unaffected v0.1 execution identity preserved',json.loads((destination/'artifact.json').read_text())==old_artifact)
 for name in ['ground-alias','false-conflict']:
  machine('unsafe-old-'+name,'dependency-artifact-json','replay',FIX/(name+'-old-artifact.json'),1,output=out/('unsafe-'+name))
 # Representative v0.1 operation remains explicit and byte-equivalent.
 model=ROOT/'examples/typed-finite/fictional-typed-rules.yh';scenario=ROOT/'examples/typed-finite/fictional-typed-rules-satisfied.yh'
 req=dict(format='yuho.machine-request/v0.1-experimental',input_kind='native-yh',operation='run',path=str(model),scenario=str(scenario));r=call('legacy-v1-native',[binary,'machine','-'],data=json.dumps(req).encode());v=json.loads(r.stdout);direct=call('legacy-native-direct',[binary,'run',model,'--scenario',scenario]);check('v0.1 native parity',v['format']=='yuho.machine-response/v0.1-experimental' and v['payload']==json.loads(direct.stdout))
 (out/'summary.json').write_text(json.dumps(dict(assertions=checks,calls=len(calls)),indent=2,ensure_ascii=False)+'\n');print(json.dumps(dict(assertions=len(checks),calls=len(calls),output=str(out))))
if __name__=='__main__':main()
