"""Independent public-CLI acceptance and adversarial checks for dependency v0.1.
All mutations and outputs are external; no production expected-value generator.
"""
import argparse, json, os, shutil, subprocess, tempfile, sys, importlib.util
sys.dont_write_bytecode=True
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
FILES={'artifact.json','report.json','projection.json','view-bindings.json','view.json','view.xml','view.svg','source-map.json'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('binary',type=Path);ap.add_argument('--output',type=Path);args=ap.parse_args()
 output=args.output or Path(tempfile.mkdtemp(prefix='yuho-dependency-'))
 output.mkdir(parents=True,exist_ok=True)
 work=output/'sources';shutil.copytree(ROOT/'test/fixtures/dependency',work)
 binary=args.binary.resolve();commands=[];checks=[];counter=0
 def call(argv,expected=0,stdin=None,env=None):
  nonlocal counter
  counter+=1;r=subprocess.run([str(binary),*map(str,argv)],input=stdin,capture_output=True,cwd=output,env=env)
  record={'args':list(map(str,argv)),'exit':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode()};commands.append(record)
  (output/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  assert r.returncode==expected,record
  stream=r.stdout if expected==0 or str(argv[0])=='machine' else r.stderr
  return json.loads(stream) if stream.strip() else None
 def check(name,value=True):
  assert value,name;checks.append(name)
 def project(case):return work/case/'project.proposed.yh'
 def run(case,label=None):
  out=output/('export-'+str(counter)+'-'+(label or case));call(['compose','check',project(case)])
  call(['compose','run',project(case),'--output',out]);check('eight coherent files',set(p.name for p in out.iterdir())==FILES)
  return out,json.loads((out/'report.json').read_text())
 def status(report,component,obj,category='expressions'):
  c=next(c for c in report['components'] if c['executionComponent']==component)
  rows=c['executionBackend'][category]
  return next(r for r in rows if r['id']==obj)['status']
 def candidates(report):return {r['availabilityCandidate']['candidateIdentity']:r['availabilityState'] for r in report['candidates']}
 def parity(out,report):
  graph=json.loads((out/'view.json').read_text());xml=ET.parse(out/'view.xml').getroot();svg=ET.parse(out/'view.svg').getroot()
  nodes={n['id']:n for n in graph['nodes']};check('unique graph identities',len(nodes)==len(graph['nodes']))
  xml_nodes={n.attrib['id'] for n in xml.iter() if n.tag.endswith('node')}
  check('JSON XML identity parity',set(nodes)==xml_nodes)
  dom=[e.attrib['id'] for e in svg.iter() if 'id' in e.attrib];check('injective SVG ids',len(dom)==len(set(dom)))
  semantic={e.attrib['data-semantic-id'] for e in svg.iter() if 'data-semantic-id' in e.attrib}
  check('SVG semantic association',set(nodes)<=semantic)
  for edge in graph['edges']:check('valid edge endpoints',edge['from'] in nodes and edge['to'] in nodes)
  bindings=json.loads((out/'view-bindings.json').read_text());included={x['semantic_id']:x for x in bindings['included']}
  check('view binding coverage',set(included)==set(nodes) and all(x['record'] for x in included.values()))
  for conversion in report['bindings']+[c['availabilityGuard'] for c in report['candidates']]:
   obs=conversion['conversionSource']; node=nodes[obs['observationIdentity']]
   check('actual scoped observation endpoint',obs['observationPort']['portObject'] in node['label'])
   check('scope retained',obs['observationScope']['scopeActor'] in node['boundary'])
  check('read identities unique',len({x['identity'] for c in report['components'] for x in c['executionReads']})==sum(len(c['executionReads']) for c in report['components']))
 # A: original quantifier model, with independent fixed technical expectations.
 original=project('A').read_text()
 both=(work/'A/impairment.yh').read_text().replace('prosecutorCertificate(actor:a,event:i) as not_proved','prosecutorCertificate(actor:a,event:i) as proved')
 (work/'A/both.yh').write_text(both)

 for scenario,values in [('both',('Eligible','Eligible')),('certificate',('Eligible','Ineligible')),('impairment',('Ineligible','Eligible')),('unknown',('Ineligible','EligibilityUnresolved')),('sale',('Ineligible','Ineligible')),('no-conviction',('Ineligible','Ineligible'))]:
  project('A').write_text(original.replace('certificate.yh',scenario+'.yh'))
  out,report=run('A',scenario);actual=candidates(report)
  for key,expected in zip(['cand:discretionary','cand:mandatory'],values):
   value=actual[key];check('A '+scenario+' '+key,(value if isinstance(value,str) else value['tag'])==expected)
  parity(out,report)
 project('A').write_text(original)
 # B: actual resolved proposition, including body-vs-priority contrast.
 original_b=project('B').read_text()
 expected_b=[('established','supplier.yh','established','satisfied','not_satisfied'),('defeated','defeat-first.yh','defeated','not_satisfied','satisfied'),('not-established','supplier.yh','not_established','not_satisfied','satisfied'),('unresolved','supplier.yh','unresolved','unresolved','unresolved'),('conflict','supplier.yh','conflict','unresolved','unresolved')]
 for scenario,model,state,value,dest in expected_b:
  project('B').write_text(original_b.replace('defeat-first.yh',model).replace('defeated.yhs',scenario+'.yhs'))
  out,report=run('B',scenario)
  conversion=report['bindings'][0];obs=conversion['conversionSource']
  check('B actual resolved state '+state,obs['observationState']==state)
  check('B authoritative value',status(report,'supplier','p:qualified','propositions')==value)
  check('B recipient independently expected result',status(report,'recipient','q:recipient')==dest)
  if state=='defeated':check('resolved result differs from establishing body',status(report,'supplier','q:support')=='satisfied')
  if state=='conflict':check('conflict retained',any(x.startswith('conflict:') for x in conversion['conversionCauses']))
  parity(out,report)
 project('B').write_text(original_b)
 # Conflict ancestry is attached to the actual read cone, including a
 # definitive F consumer; an unrelated named condition must not inherit it.
 recipient=work/'B/recipient.proposed.yh';saved_recipient=recipient.read_text()
 own=work/'B/recipient.yhs';saved_own=own.read_text()
 own.write_text(saved_own.replace('as proved','as not_proved'))
 recipient.write_text(saved_recipient.replace('proposition p:recipient;','proposition p:recipient;\n requirement q:independent = ownCriterion(person:benefactor,event:benefit);'))
 text=original_b.replace('defeat-first.yh','supplier.yh').replace('defeated.yhs','conflict.yhs')
 extras=''
 for key,q in [('dependent','q:recipient'),('independent','q:independent')]:
  extras+=f'candidate cand:{key} scope sc:a guard recipient . expression {q} mapping "yuho.condition-identity/v1" modality unspecified rationale "Fictional conflict ancestry control" refs src:fiction {{ life-imprisonment term:{key}; }}\n'
 project('B').write_text(text.rsplit('}',1)[0]+extras+'}\n')
 _,contrast=run('B','conflict-false')
 for record in contrast['candidates']:
  check('strong F result retained',record['availabilityState']=={'tag':'Ineligible'})
  conflict=any(x.startswith('conflict:') for x in record['availabilityGuard']['conversionCauses'])
  check('actual dependency cone ancestry',conflict==(record['availabilityCandidate']['candidateIdentity']=='cand:dependent'))
 recipient.write_text(saved_recipient);own.write_text(saved_own);project('B').write_text(original_b)
 # A real two-node cycle is rejected before either component executes.
 supplier=work/'B/defeat-first.yh';saved_supplier=supplier.read_text()
 supplier.write_text(saved_supplier.replace('proposition p:qualified;','dependency-condition in:reverse type technical-condition;\n proposition p:qualified;'))
 reverse='bind reverse from recipient . expression q:recipient to supplier . condition in:reverse mapping "yuho.condition-identity/v1" rationale "Synthetic cyclic invalid control" refs src:fiction;\n'
 project('B').write_text(original_b.rsplit('}',1)[0]+reverse+'}\n')
 result=call(['compose','check',project('B')],1);check('two-node cycle refused',result['dependencyCode']=='DEPCYCLE')
 supplier.write_text(saved_supplier);project('B').write_text(original_b)
 # C: two scopes, two conditions each, then resolved recipient to candidate.
 out,report=run('C');parity(out,report)
 check('C independent scopes',{k:(v['tag'] if isinstance(v,dict) else v) for k,v in candidates(report).items()}=={'cand:a':'Eligible','cand:b':'Ineligible'})
 check('C deterministic topological order',report['order']==['gate:a','gate:b','receipt:a','receipt:b'])
 for b in report['bindings']:
  check('scope isolation',b['conversionSource']['observationScope']['scopeIdentity']==('sc:a' if b['conversionIdentity'].endswith(':a') else 'sc:b'))
 # Independently specified slot order and actual generated backend leaves.
 # Final all() alone would conceal a swapped T/F pair in scope B.
 for scope,expected in [('a',('satisfied','satisfied')),('b',('satisfied','not_satisfied'))]:
  component=next(c for c in report['components'] if c['executionComponent']=='receipt:'+scope)
  root=next(q['expression'] for q in component['executionRequest']['program']['requirements'] if q['id']=='q:receipt')
  for index,kind in enumerate(('attempt','general')):
   conversion=next(b for b in report['bindings'] if b['conversionIdentity']=='link:'+kind+':'+scope)
   generated=conversion['conversionGeneratedInput'];source=conversion['conversionSource']
   check('authored slot position preserved',root['members'][index]['predicate']==generated['predicate'])
   fact=next(f for f in component['executionRequest']['program']['facts'] if f['reason']==generated['reason'])
   check('actual generated slot value',fact['status']==expected[index] and fact['predicate']==generated['predicate'] and fact['arguments']==generated['arguments'])
   check('generated input applied and distinguished',generated['application_state']=='applied' and 'not an authored assessment' in generated['origin'])
   upstream=next(c for c in report['components'] if c['executionComponent']=='gate:'+scope)
   check('actual source snapshot correspondence',source['observationSnapshot']==upstream['executionSnapshot'])
 # Unknown and local false controls in the same multistage representation.
 saved_c=project('C').read_text()
 project('C').write_text(saved_c.replace('scenario "yes.yh"','scenario "unknown.yh"'))
 _,unknown=run('C','unknown');check('multistage U',status(unknown,'receipt:a','q:receipt')=='unresolved')
 project('C').write_text(saved_c)
 # Same exact bytes yield identical export bytes, including saved replay.
 out2,report2=run('C','repeat')
 check('deterministic execution',report==report2)
 check('deterministic eight files',all((out/f).read_bytes()==(out2/f).read_bytes() for f in FILES))
 replay=output/'replayed';call(['compose','replay',out/'artifact.json','--output',replay])
 check('immutable replay bytes',all((out/f).read_bytes()==(replay/f).read_bytes() for f in FILES))
 # Source revision changes authority even if the values remain equal.
 source=work/'C/source.yh';before=source.read_bytes();source.write_bytes(before+b'\n// same-status source revision\n')
 result=call(['compose','check',project('C'),'--against',out/'artifact.json'],1);check('same-status attachment refused',result['dependencyCode']=='DEPSTALE')
 frozen=output/'replay-after-live-edit';call(['compose','replay',out/'artifact.json','--output',frozen]);check('replay ignores live edit',(frozen/'report.json').read_bytes()==(out/'report.json').read_bytes());source.write_bytes(before)
 # Actual machine request-file and stdin routes; unsupported v0.1 cannot opt in.
 req={'format':'yuho.machine-request/v0.2-experimental','input_kind':'dependency-yh','operation':'check','path':str(project('C'))}
 response=call(['machine','-'],stdin=json.dumps(req).encode());check('machine v0.2',response['success'] and response['format']=='yuho.machine-response/v0.2-experimental' and response['payload']['evaluated'] is False)
 req.update(operation='run',output=str(output/'machine-export'));(output/'request.json').write_text(json.dumps(req));response=call(['machine',output/'request.json']);check('machine actual exports',response['success'] and bool(response['exports']))
 check('machine same report',json.loads((output/'machine-export/report.json').read_text())==report)
 failed=subprocess.run([str(binary),'machine','-'],input=json.dumps(req).encode(),capture_output=True,cwd=output);fail=json.loads(failed.stdout)
 check('machine failed publication has no exports',failed.returncode==1 and not fail['success'] and not fail['exports'] and fail['payload'] is None)
 # Opt-in version/kind matrix remains closed.
 v1={'format':'yuho.machine-request/v0.1-experimental','input_kind':'composition-yh','operation':'check','path':str(project('C'))}
 refusal=call(['machine','-'],1,stdin=json.dumps(v1).encode());check('v0.1 does not admit dependency source',not refusal['success'])
 invalid=dict(req,operation='unsupported');invalid.pop('output',None)
 refusal=call(['machine','-'],1,stdin=json.dumps(invalid).encode());check('v0.2 invalid request response version',refusal['format']=='yuho.machine-response/v0.2-experimental' and not refusal['success'])
 # Existing SDK documents are checked/executed through a readable project too.
 sdk_project=work/'SDK/project.yh';call(['compose','check',sdk_project]);sdk_out=output/'sdk-source-export'
 call(['compose','run',sdk_project,'--output',sdk_out]);sdk_report=json.loads((sdk_out/'report.json').read_text());parity(sdk_out,sdk_report)
 check('actual SDK local context retained',sdk_report['components'][0]['executionLocalScope']=={'scopeActor':'orin','scopeContext':'archive-morning'})
 # Static mutations of the same common plan, not three bespoke adapters.
 original_c=project('C').read_text()
 mutations=[('unknown-source',original_c.replace('from gate:a .','from absent .',1),'DEPNAME'),('unknown-destination',original_c.replace('to receipt:a .','to absent .',1),'DEPNAME'),('wrong-port-object',original_c.replace('expression q:attempt','expression p:attempt',1),'DEPNAME'),('wrong-category',original_c.replace('expression q:attempt','proposition q:attempt',1),'DEPNAME'),('wrong-scope',original_c.replace('from gate:a .','from gate:b .',1),'DEPSCOPE'),('wrong-policy',original_c.replace('yuho.condition-identity/v1','yuho.proposition-support/v1',1),'DEPPOLICY'),('empty-rationale',original_c.replace('Actual checked attempt condition, not a copied assessment','   ',1),'DEPRATIONALE'),('unknown-ref',original_c.replace('refs src:control','refs src:missing',1),'DEPRATIONALE'),('duplicate-writer',original_c.replace('condition in:general','condition in:attempt',1),'DEPWRITER'),('missing-writer',original_c.replace('bind link:general:a from gate:a . expression q:general-candidate to receipt:a . condition in:general\n mapping "yuho.condition-identity/v1" rationale "Keep the existing express-punishment precedence gate" refs src:control;',''),'DEPMISSING'),('self-cycle',original_c.replace('from gate:a . expression q:attempt','from receipt:a . expression q:receipt',1),'DEPCYCLE'),('unsupported-policy',original_c.replace('yuho.condition-identity/v1','yuho.technical-status-to-proof/v1',1),'DEPPOLICY'),('invalid-term',original_c.replace('maximum 100','maximum -1',1),'DEPUNSUPPORTED')]
 for name,text,code in mutations:
  project('C').write_text(text);result=call(['compose','check',project('C')],1);check(name,result['dependencyCode']==code)
 project('C').write_text(original_c)
 # Primitive readiness never excuses unrelated missing inputs.
 scenario=work/'C/receipt.yhs';saved=scenario.read_text();scenario.write_text(saved.replace('classify localApproval(person:subject,event:context) as satisfied reason "Independent local approval control";',''))
 if scenario.read_text()==saved:
  import re
  scenario.write_text(re.sub(r'classify localApproval[^;]+;','',saved))
 result=call(['compose','check',project('C')],1);check('unrelated missing primitive',result['dependencyCode'] in ('SFT011','DEPMISSING'));scenario.write_text(saved)
 # Duplicate direct input, unsupported port, bounds and actor/context maps.
 rec=work/'C/receipt.yhs';saved=rec.read_text();rec.write_text(saved.replace('}', ' classify in:attempt() as proved reason "Illegal authored override";\n}'))
 refused=call(['compose','check',project('C')],1);check('direct hole assessment rejected',refused['dependencyCode']=='DEPWRITER');rec.write_text(saved)
 for name,text,code in [('unsupported-port',original_c.replace('expression q:attempt','rule q:attempt',1),'DEPCATEGORY'),('wrong-actor',original_c.replace('scope sc:a actor person:a','scope sc:a actor person:absent',1),'DEPSCOPE'),('wrong-context',original_c.replace('context event:a','context event:absent',1),'DEPSCOPE')]:
  project('C').write_text(text);result=call(['compose','check',project('C')],1);check(name,result['dependencyCode']==code)
 many=''.join(f'bind extra:{i} from gate:a . expression q:attempt to receipt:a . condition missing:{i} mapping "yuho.condition-identity/v1" rationale "Resource invalid control" refs src:control;\n' for i in range(65))
 project('C').write_text(original_c.rsplit('}',1)[0]+many+'}\n');refused=call(['compose','check',project('C')],1);check('finite binding resource limit',refused['dependencyCode']=='DEPLIMIT');project('C').write_text(original_c)
 # Same display/local identifiers across sources stay distinct. New admitted
 # long component identities and Unicode text/path do not change the outcome.
 long_id='rule:0-'+'a'*120
 renamed=original_c.replace('gate:a',long_id).replace('Actual checked attempt condition, not a copied assessment','Évidence 規則: actual checked condition')
 src=work/'C/source.yh';unicode_path=work/'C/源 source.yh';unicode_path.write_bytes(src.read_bytes())
 project('C').write_text(renamed.replace('model "source.yh"','model "源 source.yh"'))
 long_out,long_report=run('C','long-unicode');parity(long_out,long_report)
 check('long Unicode case meaning retained',candidates(long_report)==candidates(report));project('C').write_text(original_c)
 # Revisions of each saved authority record fail attachment/replay rather than
 # inheriting old observations because the resulting statuses happen to agree.
 artifact=json.loads((out/'artifact.json').read_text())
 for name,change in [('reason',lambda d:d['dependencySources'].__setitem__('receipt.yhs',d['dependencySources']['receipt.yhs'].replace('Fictional local control','Revised same technical reason'))),('policy',lambda d:d['dependencyPlan']['planBindings'][0].__setitem__('bindingPolicy','unsupported-policy')),('scope',lambda d:d['dependencyPlan']['planScopes'][0].__setitem__('scopeActor','person:b')),('term',lambda d:d['dependencyPlan']['planCandidates'][0]['candidateTerm']['termValue'].__setitem__('currency','USD')),('wrong-existing-port',lambda d:d['dependencyPlan']['planBindings'][0]['bindingPort'].__setitem__('portObject','q:general-candidate'))]:
  import copy
  mutated=copy.deepcopy(artifact);change(mutated['artifactDocument']);saved_artifact=output/('tampered-'+name+'.json');saved_artifact.write_text(json.dumps(mutated))
  result=call(['compose','replay',saved_artifact,'--output',output/('unpublished-'+name)],1)
  check('stale authority '+name,result['dependencyCode'] in ('DEPSTALE','DEPPOLICY','DEPSCOPE','DEPUNSUPPORTED'))
  check('no stale export '+name,not (output/('unpublished-'+name)).exists())
 # Structural invariance and authority changes are different properties.
 saved_source=(work/'C/source.yh').read_text()
 (work/'C/source.yh').write_text(saved_source.replace('limitation "','requirement q:irrelevant = not(q:attempt);\n limitation "',1))
 _,irrelevant=run('C','irrelevant')
 check('irrelevant declaration leaves candidate outcomes unchanged',candidates(irrelevant)==candidates(report))
 check('exact authored revision still changes authority',irrelevant['execution']!=report['execution'])
 (work/'C/source.yh').write_text(saved_source)
 project('C').write_text(original_c.replace('scenario "specific.yh"','scenario "yes.yh"'))
 _,actor_revision=run('C','actor-revision');check('actor isolation A unchanged',status(actor_revision,'receipt:a','q:receipt')==status(report,'receipt:a','q:receipt'))
 check('actor B revision actually evaluated',status(actor_revision,'receipt:b','q:receipt')=='satisfied');project('C').write_text(original_c)
 # Relocation changes physical paths, not virtual sources or execution meaning.
 relocated=output/'relocated';shutil.copytree(work/'C',relocated)
 relocated_out=output/'relocated-export';call(['compose','run',relocated/'project.proposed.yh','--output',relocated_out])
 check('fresh relocated result bytes identical',(relocated_out/'report.json').read_bytes()==(out/'report.json').read_bytes())
 # `condition` is reserved as an expression form/predicate in new templates,
 # not as an unrelated entity name inside a tuple.
 saved_project=project('B').read_text();recipient=work/'B/recipient.proposed.yh';saved_recipient=recipient.read_text();facts=work/'B/recipient.yhs';saved_facts=facts.read_text()
 recipient.write_text(saved_recipient.replace('person:benefactor','condition'));facts.write_text(saved_facts.replace('person:benefactor','condition'));project('B').write_text(saved_project.replace('entity person:benefactor as','entity condition as'))
 _,entity_control=run('B','condition-entity');check('form name does not erase valid entity identity',status(entity_control,'recipient','q:recipient')=='satisfied')
 recipient.write_text(saved_recipient);facts.write_text(saved_facts);project('B').write_text(saved_project)
 # Filesystem refusal/cleanup through ordinary CLI.
 for kind in ('directory','file','symlink','missing-parent'):
  dest=output/('exists-'+kind)
  if kind=='directory':dest.mkdir()
  elif kind=='file':dest.write_text('preserve me')
  elif kind=='symlink':dest.symlink_to(output/'unrelated')
  else:dest=dest/'child'
  result=call(['compose','run',project('C'),'--output',dest],1);check('no-clobber '+kind,result['dependencyCode']=='DEPPUBLISH')
 # Deterministic external write/publication/race injection, both routes and
 # both fresh execution and immutable replay. Shared existing shim, no product
 # fault flags or second export implementation.
 spec=importlib.util.spec_from_file_location('tranche04_probe',ROOT/'test/tranche04.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 (output/'fault.c').write_text(old.SHIM);subprocess.run(['cc','-shared','-fPIC','-o',str(output/'fault.so'),str(output/'fault.c'),'-ldl'],check=True)
 for machine in (False,True):
  for replay_mode in (False,True):
   for fault in ('stage','publish','parent','race'):
    destination=output/f'fault-{machine}-{replay_mode}-{fault}'
    env=os.environ.copy();env.update(LD_PRELOAD=str(output/'fault.so'),YUHO_TEST_FAULT=fault,YUHO_TEST_LOG=str(output/'fault.log'))
    if machine:
     request={'format':'yuho.machine-request/v0.2-experimental','input_kind':'dependency-artifact-json' if replay_mode else 'dependency-yh','operation':'replay' if replay_mode else 'run','path':str(out/'artifact.json' if replay_mode else project('C')),'output':str(destination)}
     result=call(['machine','-'],1,stdin=json.dumps(request).encode(),env=env);check('failed machine exports absent',not result['success'] and not result['exports'] and result['payload'] is None)
    else:call(['compose','replay' if replay_mode else 'run',out/'artifact.json' if replay_mode else project('C'),'--output',destination],1,env=env)
    if fault=='race':check('unrelated race winner preserved',list(p.name for p in destination.iterdir())==['sentinel'] and (destination/'sentinel').read_text()=='unrelated winner')
    else:check('no partial published destination',not destination.exists())
 check('staged failure occurred after first complete file','complete artifact written before injected report failure' in (output/'fault.log').read_text())
 check('no temporary directory leak',not list(output.glob('.yuho-compose-*')))
 # Bare dependency templates must refuse standalone execution.
 result=call(['check',work/'C/receipt.proposed.yh','--scenario',work/'C/receipt.yhs'],1)
 check('standalone hole refusal',result.get('code')=='DEPMISSING')
 (output/'summary.json').write_text(json.dumps({'assertions':len(checks),'cli_calls':len(commands),'checks':checks},indent=2)+'\n')
 print(json.dumps({'assertions':len(checks),'cli_calls':len(commands),'output':str(output)}))
if __name__=='__main__':main()
