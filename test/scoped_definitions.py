"""Scoped templates: independent literal oracles; public subprocesses, external data.
The compiler/evaluator is shared by CLI/SDK comparisons; literal expectations,
read tuples, source keys and mutation/metamorphic controls are separate oracles.
"""
import argparse,copy,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('binary',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
 O=a.output or Path(tempfile.mkdtemp(prefix='yuho-scoped-definitions-'));O=O.resolve();O.mkdir(exist_ok=True,parents=True);y=a.binary.resolve();calls=[];checks=[]
 def check(n,b):
  checks.append({'name':n,'passed':bool(b)});(O/'checks.json').write_text(json.dumps(checks,indent=2));assert b,n
 def call(n,args,code=0,data=None,cwd=None):
  p=subprocess.run(list(map(str,args)),cwd=cwd or O,input=data,capture_output=True);r={'name':n,'args':list(map(str,args)),'cwd':str(cwd or O),'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()};calls.append(r);(O/'commands.json').write_text(json.dumps(calls,indent=2));assert p.returncode==code,r;return p
 def cli(n,args,code=0):
  p=call(n,[y,*args],code);return json.loads(p.stdout or p.stderr)
 def execute(n,w):
  c=cli(n+'-check',['compose','check',w/'project.yh']);check(n+' static',c['evaluated'] is False)
  dest=O/(n+'-export');cli(n+'-run',['compose','run',w/'project.yh','--output',dest]);r=json.loads((dest/'report.json').read_text());g=json.loads((dest/'view.json').read_text());p=json.loads((dest/'projection.json').read_text())
  check(n+' eight files',len(list(dest.iterdir()))==8);check(n+' projected report',r==p['report']);sd=r['scoped_definitions']
  check(n+' distinct use handles',len({u['identity'] for u in sd['uses']})==len(sd['uses']))
  ids={n['id'] for n in g['nodes']};check(n+' unique graph and endpoints',len(ids)==len(g['nodes']) and all(x['from'] in ids and x['to'] in ids for x in g['edges']))
  x=E.parse(dest/'view.xml').getroot();check(n+' XML identity parity',ids=={n.attrib['id'] for n in x.iter() if n.tag.endswith('node')})
  s=E.parse(dest/'view.svg').getroot();dom=[n.attrib['id'] for n in s.iter() if 'id' in n.attrib];check(n+' SVG identity parity',len(dom)==len(set(dom)) and ids<={n.attrib['data-semantic-id'] for n in s.iter() if 'data-semantic-id' in n.attrib})
  b=json.loads((dest/'view-bindings.json').read_text());check(n+' view bindings complete',ids=={v['semantic_id'] for v in b['included']} and all(v['record'] is not None for v in b['included']))
  for u in sd['uses']:
   c=next(c for c in r['components'] if c['executionComponent']==u['component']);check(n+' selected component/scope/snapshot',u['scope']==c['executionScope'] and u['snapshot']==c['executionSnapshot'])
   for o in u['occurrences']:
    check(n+' actual ledger occurrence',o['read'] in c['executionReads'])
    check(n+' exact selected authored assessment',len(o['selected_inputs'])==len(o['selected_assessments']) and all(a['declaration']['selectedPredicate']==i['predicate'] and a['declaration']['selectedArguments']==i['arguments'] and a['declaration']['selectedClassification']==i['classification'] for i,a in zip(o['selected_inputs'],o['selected_assessments'])))
    for a in o['selected_assessments']:
     source=next(v for v in p['source_map']['sources'] if v['path']==a['declaration']['selectedSource']);check(n+' assessment source digest',a['source_snapshot']==hashlib.sha256(source['utf8'].encode()).hexdigest())
   source=next(v for v in p['source_map']['sources'] if v['path']==u['selection']['source']);check(n+' scenario selection exact bytes',hashlib.sha256(source['utf8'].encode()).hexdigest()==u['selection']['sha256'])
  for edge in g['edges']:
   if edge['kind']=='produces_port':
    source=next(o for u in sd['uses'] for o in u['occurrences'] if o['identity']==edge['from']);target=next(n for n in g['nodes'] if n['id']==edge['to']);check(n+' exact occurrence port',source['read']['root'][0]=='expression' and source['read']['path']==[] and source['read']['status']==target['status'])
  return dest,r,p,g
 def write(w,n,t):p=w/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
 # C11-inspired authorisation relationship, explicitly selected structural control.
 # No new statutory interpretation: primitive classifications are fictional.
 module='''typed-rules-module reuse.permission version 1.0.0 {
 export requirement-template q:permission;
 entity-type person; entity-type event;
 predicate permitted(person,event) kind relationship;
 requirement-template q:permission(var:actor as person,var:incident as event) = permitted(var:actor,var:incident);
 }'''
 def model(actor='actor:a',event='event:a',uses=1):
  return f'''typed-rules-model Reuse {{
 module-root "modules"; import reuse.permission version 1.0.0 as law;
 entity-type person; entity-type event; entity {actor} as person; entity {event} as event;
 predicate permitted(person,event) kind relationship;
 requirement-use q:first from law::q:permission({actor},{event}) assessments scenario;
 '''+(f'requirement-use q:second from law::q:permission({actor},{event}) assessments scenario;\n' if uses==2 else '')+'''
 requirement q:combined = '''+('all(q:first,q:second)' if uses==2 else 'q:first')+''';
 proposition p:result; rule r establishes proposition p:result when q:combined;
 limitation "Fictional classified inputs, selected recurring authorisation structure; no complete offence or legal finding";
 }'''
 def scenario(state='proved',actor='actor:a',event='event:a',reason='explicit selected classification'):
  return f'typed-rules-scenario Selected for Reuse {{ classify permitted({actor},{event}) as {state} reason "{reason}"; }}'
 def scope(i,actor,context,case=None,allegation=None):
  return f'scope {i} actor {actor} context {context} '+(f'case {case} allegation {allegation} ' if case else '')+f'{{ identity {actor} nominal person; identity {context} nominal event; }}'
 def component(i,m,s,sc,actor,event,entry=''):
  return f'component {i} profile native-typed model "{m}" '+(f'entry allegation {entry} ' if entry else f'scenario "{s}" ')+f'scope {sc} {{ nominal person as person; nominal event as event; entity {actor} as {i}:actor; entity {event} as {i}:event; }} rationale "Explicit scoped assessment selection";'
 def candidate(i,c,sc,q='q:first'):
  return f'candidate {i} scope {sc} guard {c} . expression {q} mapping "yuho.condition-identity/v1" modality unspecified rationale "Fictional candidate; not sentence" refs src {{ life-imprisonment term:{i}; }}'
 def project(parts):return 'checked-project reuse version "yuho.dependency-plan/v0.1-experimental" { source src locator "urn:synthetic:scoped-reuse"; '+'\n'.join(parts)+' }'
 w=O/'actors';w.mkdir();write(w,'modules/reuse.permission@1.0.0.yh',module)
 parts=[]
 for i,state in [('alpha','proved'),('beta','not_proved'),('gamma','unresolved')]:
  write(w,i+'.yh',model('actor:'+i,'event:'+i,2));write(w,i+'.scenario.yh',scenario(state,'actor:'+i,'event:'+i))
  parts += [scope(i,i+':actor',i+':event'),component(i,i+'.yh',i+'.scenario.yh',i,'actor:'+i,'event:'+i),candidate(i+'-candidate',i,i)]
 write(w,'project.yh',project(parts))
 (O/'expectations-before-execution.json').write_text(json.dumps({'actors':{'alpha':'satisfied','beta':'not_satisfied','gamma':'unresolved'},'candidates':{'alpha-candidate':'Eligible','beta-candidate':'Ineligible','gamma-candidate':'EligibilityUnresolved'},'definition_count':1,'explicit_uses':6,'selection':'separate exact scenarios; repeated same-scope use explicitly shares selected tuple; actual evaluations remain distinct'},indent=2))
 dest,r,p,g=execute('actors',w);sd=r['scoped_definitions']
 check('one authoritative definition',len(sd['definitions'])==1 and sd['definitions'][0]['definitionName']=='q:permission')
 check('six separately named/scoped uses',len(sd['uses'])==6)
 for component_name in ['alpha','beta','gamma']:
  group=[u for u in sd['uses'] if u['component']==component_name];check('shared structure distinct uses '+component_name,len({u['instantiation'] for u in group})==1 and len({u['identity'] for u in group})==2)
 check('candidate literal outcomes',{c['availabilityCandidate']['candidateIdentity']:c['availabilityState']['tag'] for c in r['candidates']}=={'alpha-candidate':'Eligible','beta-candidate':'Ineligible','gamma-candidate':'EligibilityUnresolved'})
 for i,status in [('alpha','satisfied'),('beta','not_satisfied'),('gamma','unresolved')]:
  c=next(c for c in r['components'] if c['executionComponent']==i);ordinary=cli(i+'-ordinary',['run',w/(i+'.yh'),'--scenario',w/(i+'.scenario.yh')]);check('ordinary checked parity '+i,all(ordinary[k]==c['executionBackend'][k] for k in ['expressions','rules','propositions']))
  check('independent value '+i,{v['status'] for v in c['executionBackend']['expressions']}=={status})
  uses=[u for u in sd['uses'] if u['component']==i]
  check('distinct repeated evaluations '+i,len({o['identity'] for u in uses for o in u['occurrences']})==sum(len(u['occurrences']) for u in uses) and all(u['occurrences'] for u in uses))
  for u in uses:
   for o in u['occurrences']:
    check('exact selected primitive '+i,all(x['predicate']=='permitted' and x['arguments']==['actor:'+i,'event:'+i] and x['classification']['status']==status for x in o['selected_inputs']) and bool(o['selected_inputs']))
 # Pure repeated generation and saved source authority, through the public CLI.
 duplicate,_,_,_=execute('determinism',w);check('eight byte-identical exports',all(f.read_bytes()==(duplicate/f.name).read_bytes() for f in dest.iterdir()))
 replay=O/'replay';cli('replay',['compose','replay',dest/'artifact.json','--output',replay]);check('immutable replay bytes',all(f.read_bytes()==(replay/f.name).read_bytes() for f in dest.iterdir()))
 write(w,'alpha.scenario.yh',scenario('not_proved','actor:alpha','event:alpha','actor A revised'))
 _,rr,_,_=execute('actor-isolation',w);check('actor isolation',{c['availabilityCandidate']['candidateIdentity']:c['availabilityState']['tag'] for c in rr['candidates']}=={'alpha-candidate':'Ineligible','beta-candidate':'Ineligible','gamma-candidate':'EligibilityUnresolved'})
 for i in ['beta','gamma']:check('unchanged independent occurrence '+i,next(c for c in r['components'] if c['executionComponent']==i)['executionBackend']==next(c for c in rr['components'] if c['executionComponent']==i)['executionBackend'])
 for component_name in ['beta','gamma']:
  old=[u for u in sd['uses'] if u['component']==component_name];new=[u for u in rr['scoped_definitions']['uses'] if u['component']==component_name]
  def causal(u):
   return dict(identity=u['identity'],instantiation=u['instantiation'],declaration=u['declaration'],scope=u['scope'],selection=u['selection'],definition_snapshot=u['definition_snapshot'],occurrences=[dict(read={k:v for k,v in o['read'].items() if k!='identity'},selected_inputs=o['selected_inputs'],selected_assessments=o['selected_assessments']) for o in u['occurrences']])
  check('unrelated actor causal selections remain identical '+component_name,[causal(u) for u in old]==[causal(u) for u in new])
 # Exact execution handles seal the complete plan, so a retained-source revision
 # can change those handles while actual causal selections above remain stable.

 refused=cli('stale-source-attachment',['compose','check',w/'project.yh','--against',dest/'artifact.json'],1);check('stale same plan authority',refused['dependencyCode']=='DEPSTALE')
 # Machine v0.2 dispatch, file and stdin, exact input-kind authority.
 def machine(name,op,kind,path,out=None,code=0,stdin=False):
  request={'format':'yuho.machine-request/v0.2-experimental','operation':op,'input_kind':kind,'path':str(path)}
  if out:request['output']=str(out)
  f=O/(name+'.request.json');f.write_text(json.dumps(request));p=call(name,[y,'machine','-' if stdin else f],code,data=f.read_bytes() if stdin else None);v=json.loads(p.stdout);check(name+' one response',v['success']==(code==0));return v
 machine('machine-live-check','check','dependency-yh',w/'project.yh')
 machine('machine-live-run','run','dependency-yh',w/'project.yh',O/'machine-run',stdin=True)
 machine('machine-artifact-check','check','dependency-artifact-json',dest/'artifact.json')
 machine('machine-artifact-replay','replay','dependency-artifact-json',dest/'artifact.json',O/'machine-replay')
 check('machine replay keeps embedded original despite live edit',all(f.read_bytes()==(O/'machine-replay'/f.name).read_bytes() for f in dest.iterdir()))
 check('machine live current-source parity',all(f.read_bytes()==(O/'machine-run'/f.name).read_bytes() for f in (O/'actor-isolation-export').iterdir()))
 machine('machine-source-kind-artifact','check','dependency-yh',dest/'artifact.json',code=1)
 machine('machine-replay-kind-live','replay','dependency-artifact-json',w/'project.yh',O/'refused-output',code=1)
 check('wrong kind never publishes',not (O/'refused-output').exists())
 v=machine('machine-wrong-kind','check','dependency-artifact-json',w/'project.yh',code=1);check('wrong input authority fails',v['effects']['source_authority']=='not_validated')
 # The same actual actor in different contexts still selects independent facts.
 contexts=O/'same-actor-contexts';shutil.copytree(w,contexts);text=(contexts/'project.yh').read_text()
 for key in ['alpha','beta','gamma']:text=text.replace(key+':actor','one:actor')
 write(contexts,'project.yh',text);_,context_report,_,_=execute('same-actor-contexts',contexts)
 check('same actor different contexts remain independent',{u['scope']['scopeActor'] for u in context_report['scoped_definitions']['uses']}=={'one:actor'} and len({u['scope']['scopeContext'] for u in context_report['scoped_definitions']['uses']})==3 and [c['availabilityState']['tag'] for c in context_report['candidates']]==['Ineligible','Ineligible','EligibilityUnresolved'])
 # Fixed source revision with unchanged truth changes authority, not definition key.
 write(w,'alpha.scenario.yh',scenario('proved','actor:alpha','event:alpha'))
 write(w,'modules/reuse.permission@1.0.0.yh',module+'\n// same-status source revision\n')
 _,revision,_,_=execute('source-revision',w);check('source key stable snapshot changed',revision['scoped_definitions']['definitions'][0]['definitionKey']==sd['definitions'][0]['definitionKey'] and revision['scoped_definitions']['definitions'][0]['definitionSnapshot']!=sd['definitions'][0]['definitionSnapshot'])
 check('changed definition attachment refused',cli('stale-definition',['compose','check',w/'project.yh','--against',dest/'artifact.json'],1)['dependencyCode']=='DEPSTALE')
 # Static adversarial controls. Literal codes specify the failing layer.
 negative=[('unknown','alpha.yh','law::q:permission','law::q:missing','SFNAME'),('wrong-role','alpha.yh','(actor:alpha,event:alpha)','(event:alpha,actor:alpha)','SFT005'),('missing-argument','alpha.yh','(actor:alpha,event:alpha)','(actor:alpha)','SFARITY'),('duplicate-use','alpha.yh','requirement-use q:second','requirement-use q:first','SFDUPLICATE'),('private','modules/reuse.permission@1.0.0.yh','export requirement-template q:permission;','','SFNAME'),('wrong-kind','modules/reuse.permission@1.0.0.yh','export requirement-template','export requirement','SFNAME'),('wrong-version','alpha.yh','version 1.0.0','version 2.0.0','DEPFORMAT'),('free-variable','modules/reuse.permission@1.0.0.yh','= permitted(var:actor,var:incident)','= permitted(var:free,var:incident)','SFT006'),('capture','modules/reuse.permission@1.0.0.yh','= permitted(var:actor,var:incident)','= permitted(actor:alpha,var:incident)','SFCAPTURE'),('recursive-template','modules/reuse.permission@1.0.0.yh','= permitted(var:actor,var:incident)','= q:permission','SFCAPTURE'),('wrong-signature','alpha.yh','predicate permitted(person,event)','predicate permitted(event,person)','SFSIGNATURE'),('missing-input','alpha.scenario.yh',scenario('proved','actor:alpha','event:alpha'),'typed-rules-scenario Selected for Reuse {}','SFT011'),('conflicting-selection','alpha.scenario.yh',' }',' classify permitted(actor:alpha,event:alpha) as not_proved reason "second writer"; }','SFT002'),('ordinary-reference-cycle','alpha.yh','requirement q:combined = all(q:first,q:second);','requirement q:combined = q:cycle; requirement q:cycle = q:combined;','SFT010')]
 for n,file,old,new,code in negative:
  f=O/('negative-'+n);shutil.copytree(w,f);text=(f/file).read_text();check(n+' mutation applies',old in text);write(f,file,text.replace(old,new));v=cli(n,['compose','check',f/'project.yh'],1);check(n+' static refusal',v['dependencyCode']==code)
 # C06-inspired distinct guardian/beneficiary roles, synthetic classified inputs.
 f=O/'guardian';f.mkdir();write(f,'modules/reuse.permission@1.0.0.yh',module)
 guardian='''typed-rules-model Guardian {
 entity-type person; entity-type guardian; entity-type event;
 entity doctor as person; entity beneficiary as person; entity adult as guardian; entity treatment as event;
 predicate consents(guardian,event) kind relationship; predicate deceived(guardian,event) kind circumstance;
 predicate protects(person,event) kind relationship;
 requirement-template q:consent(var:g as guardian,var:e as event) = all(consents(var:g,var:e),not(deceived(var:g,var:e)));
 requirement-use q:benefit from q:consent(adult,treatment) assessments scenario;
 requirement-use q:protection from q:consent(adult,treatment) assessments scenario;
 requirement q:route = all(q:protection,protects(beneficiary,treatment));
 proposition p:benefit; proposition p:protection;
 rule rb establishes proposition p:benefit when q:benefit;
 rule rp establishes proposition p:protection when q:route;
 limitation "Fictional technical consent roles inspired by C06; no complete statutory exception";
 }'''
 write(f,'m.yh',guardian);write(f,'s.yh','typed-rules-scenario Selected for Guardian { classify consents(adult,treatment) as proved reason "guardian selection"; classify deceived(adult,treatment) as not_proved reason "independent selection"; classify protects(beneficiary,treatment) as not_proved reason "different contextual route"; }')
 gscope='scope sc actor real:doctor context real:treatment { identity real:doctor nominal person; identity real:treatment nominal event; identity real:adult nominal guardian; }'
 gc='component consent profile native-typed model "m.yh" scenario "s.yh" scope sc { nominal person as person; nominal guardian as guardian; nominal event as event; entity doctor as real:doctor; entity treatment as real:treatment; entity adult as real:adult; } rationale "Distinct consenting adult, doctor and beneficiary roles";'
 write(f,'project.yh',project([gscope,gc,candidate('benefit','consent','sc','q:benefit'),candidate('protection','consent','sc','q:route')]))
 _,gr,_,_=execute('guardian',f);check('same body different contextual routes',{c['availabilityCandidate']['candidateIdentity']:c['availabilityState']['tag'] for c in gr['candidates']}=={'benefit':'Eligible','protection':'Ineligible'} and len(gr['scoped_definitions']['definitions'])==1)
 inspected=cli('parsed-template',['inspect',f/'m.yh','--stage','parsed']);parsed=inspected['stages'][0]['data'];check('honest parsed template structure',parsed['scoped_templates'][0]['body']['kind']=='all' and len(parsed['scoped_uses'])==2)
 check('honest unsupported checked stage',cli('unsupported-checked-template',['inspect',f/'m.yh','--scenario',f/'s.yh','--stage','checked'],1)['code']=='SFI002')
 # Same local tuple in independently selected allegations: T and F remain distinct.
 f=O/'allegations';f.mkdir();write(f,'modules/reuse.permission@1.0.0.yh',module);write(f,'m.yh',model());write(f,'yes.yh',scenario());write(f,'no.yh',scenario('not_proved'))
 write(f,'case.yh','typed-rules-case case:trial model "m.yh" { allegation a--one scenario "yes.yh"; allegation a--two scenario "no.yh"; }')
 parts=[]
 for i,al in [('first','a--one'),('second','a--two')]:parts += [scope(i,'case:actor','case:event','case:trial',al),component(i,'case.yh','',i,'actor:a','event:a',al).replace(i+':actor','case:actor').replace(i+':event','case:event'),candidate(i,i,i)]
 write(f,'project.yh',project(parts));_,cr,_,_=execute('allegations',f)
 check('case results isolated',[c['availabilityState']['tag'] for c in cr['candidates']]==['Eligible','Ineligible'] and {u['scope']['scopeAllegation'] for u in cr['scoped_definitions']['uses']}=={'a--one','a--two'})
 # An actual case-selected shared classification retains its original case source.
 shared=O/'shared-allegation';shutil.copytree(f,shared);write(shared,'yes.yh','typed-rules-scenario Selected for Reuse {}')
 write(shared,'case.yh','typed-rules-case case:trial model "m.yh" { shared-classification shared:fact permitted(actor:a,event:a) as proved reason "case authored classification"; allegation a--one scenario "yes.yh" use shared:fact; allegation a--two scenario "no.yh"; }')
 _,sr,_,_=execute('shared-allegation',shared);check('shared case assessment authority',all(a['declaration']['selectedSource']=='case.yh' for u in sr['scoped_definitions']['uses'] if u['component']=='first' for o in u['occurrences'] for a in o['selected_assessments']))
 # Existing explicit DAG binding consumes the correct scoped occurrence.
 f=O/'dependency';shutil.copytree(w,f);write(f,'modules/reuse.permission@1.0.0.yh',module);write(f,'alpha.scenario.yh',scenario('proved','actor:alpha','event:alpha'))
 recipient='''typed-rules-model Recipient { entity-type person; entity-type event; entity actor:alpha as person; entity event:alpha as event;
 dependency-condition in:permission type technical-condition; requirement q:downstream = condition(in:permission);
 proposition p:downstream; rule r establishes proposition p:downstream when q:downstream; limitation "Explicit technical dependency"; }'''
 write(f,'recipient.yh',recipient);write(f,'recipient.scenario.yh','typed-rules-scenario Selected for Recipient {}')
 extra='component receiver profile native-typed model "recipient.yh" scenario "recipient.scenario.yh" scope alpha { nominal person as person; nominal event as event; entity actor:alpha as alpha:actor; entity event:alpha as alpha:event; } rationale "Same actual actor/context"; bind supplied from alpha . expression q:first to receiver . condition in:permission mapping "yuho.condition-identity/v1" rationale "Actual scoped use observation supplies technical condition" refs src;'
 write(f,'project.yh',(f/'project.yh').read_text().rsplit('}',1)[0]+extra+candidate('receiver-candidate','receiver','alpha','q:downstream')+'}')
 dd,dr,_,_=execute('dependency',f);converted=dr['bindings'][0];check('dependency selects real scoped use',converted['conversionSource']['observationPort']==dict(portComponent='alpha',portCategory='typed.expression.truth',portObject='q:first') and converted['conversionSource']['observationScope']['scopeActor']=='alpha:actor' and next(c for c in dr['candidates'] if c['availabilityCandidate']['candidateIdentity']=='receiver-candidate')['availabilityState']['tag']=='Eligible')
 # Genuine conflict remains on its actual generated condition, not a shared use.
 f=O/'conflict-cone';shutil.copytree(O/'dependency',f)
 source='''typed-rules-model Conflict { entity-type person; entity-type event; entity actor:alpha as person; entity event:alpha as event;
 predicate supports(person,event) kind relationship; requirement q:positive = supports(actor:alpha,event:alpha);
 proposition p:conflicted; rule ra establishes proposition p:conflicted when q:positive; rule rb defeats proposition p:conflicted when q:positive;
 limitation "Synthetic contradictory technical support"; }'''
 write(f,'conflict.yh',source);write(f,'conflict.scenario.yh','typed-rules-scenario S for Conflict { classify supports(actor:alpha,event:alpha) as proved reason "actual equal priority contradiction"; }')
 m=(f/'alpha.yh').read_text().replace('requirement q:combined = all(q:first,q:second);','dependency-condition in:conflict type technical-condition; requirement q:combined = all(q:first,condition(in:conflict));');write(f,'alpha.yh',m)
 comp='component upstream profile native-typed model "conflict.yh" scenario "conflict.scenario.yh" scope alpha { nominal person as person; nominal event as event; entity actor:alpha as alpha:actor; entity event:alpha as alpha:event; } rationale "Same exact technical context"; bind conflict-input from upstream . proposition p:conflicted to alpha . condition in:conflict mapping "yuho.proposition-support/v1" rationale "Explicit conflict-preserving technical support mapping" refs src;'
 write(f,'project.yh',(f/'project.yh').read_text().rsplit('}',1)[0]+comp+candidate('joined-conflict','alpha','alpha','q:combined')+'}')
 _,fr,_,_=execute('conflict-cone',f);independent=next(c for c in fr['candidates'] if c['availabilityCandidate']['candidateIdentity']=='alpha-candidate');dependent=next(c for c in fr['candidates'] if c['availabilityCandidate']['candidateIdentity']=='joined-conflict')
 check('actual conflict cone only',independent['availabilityState']['tag']=='Eligible' and not independent['availabilityGuard']['conversionCauses'] and dependent['availabilityState']['tag']=='EligibilityUnresolved' and any(x.startswith('conflict:') for x in dependent['availabilityGuard']['conversionCauses']))
 check('scoped use is independently evaluated T',all(o['read']['status']=='satisfied' and all(i['predicate']=='permitted' for i in o['selected_inputs']) for u in fr['scoped_definitions']['uses'] if u['component']=='alpha' for o in u['occurrences']))
 # Held-out 1: finite quantified body; new variable cannot capture formal.
 f=O/'quantified';shutil.copytree(w,f);quant=module.replace('= permitted(var:actor,var:incident);','= forall var:other as event(permitted(var:actor,var:other));')
 write(f,'modules/reuse.permission@1.0.0.yh',quant);_,qr,_,_=execute('quantified',f);check('quantified independent result',[c['availabilityState']['tag'] for c in qr['candidates']]==['Eligible','Ineligible','EligibilityUnresolved'])
 # Held-out 2: inverted body in a second exact module with same declaration label.
 f=O/'two-modules';shutil.copytree(w,f);other=module.replace('reuse.permission','other.permission').replace('= permitted(var:actor,var:incident);','= not(permitted(var:actor,var:incident));')
 write(f,'modules/other.permission@1.0.0.yh',other);m=(f/'alpha.yh').read_text().replace('import reuse.permission version 1.0.0 as law;','import reuse.permission version 1.0.0 as law; import other.permission version 1.0.0 as second;').replace('requirement-use q:second from law::','requirement-use q:second from second::')
 write(f,'alpha.yh',m);_,tr,_,_=execute('two-modules',f);ac=next(c for c in tr['components'] if c['executionComponent']=='alpha');check('same label different original definitions',{x['id']:x['status'] for x in ac['executionBackend']['expressions']}=={'q:first':'satisfied','q:second':'not_satisfied','q:combined':'not_satisfied'} and len(tr['scoped_definitions']['definitions'])==2)
 # Held-out 3: Unicode and delimiter-looking IDs, plus alpha-renamed formals.
 f=O/'unicode';shutil.copytree(w,f)
 for file in list(f.glob('*.yh'))+[f/'modules/reuse.permission@1.0.0.yh']:
  text=file.read_text().replace('q:first','q:use--a').replace('q:second','q:use--a--b').replace('var:actor','var:renamed').replace('var:incident','var:other').replace('explicit selected classification','授權 — independent Unicode reason').replace('Fictional classified inputs','Unicode explanation 授權; fictional classified inputs')
  file.write_text(text)
 _,ur,_,_=execute('unicode',f);check('Unicode literal outcomes',[c['availabilityState']['tag'] for c in ur['candidates']]==['Eligible','Ineligible','EligibilityUnresolved'])
 # Declaration order and unrelated declarations may alter source hashes, not meaning.
 f=O/'order';shutil.copytree(w,f);text=(f/'alpha.yh').read_text();text=text.replace('entity-type person; entity-type event;','entity-type event; entity-type person;').replace('requirement q:combined','requirement q:unrelated = permitted(actor:alpha,event:alpha); requirement q:combined');write(f,'alpha.yh',text)
 _,mr,_,_=execute('declaration-order',f);check('unrelated order/value invariance',[c['availabilityState']['tag'] for c in mr['candidates']]==['Eligible','Ineligible','EligibilityUnresolved'])
 # Accepted F04/F05 ownership also holds inside the new scoped template body.
 f=O/'ordinary-condition-helpers';shutil.copytree(w,f)
 for file in list(f.glob('*.yh'))+[f/'modules/reuse.permission@1.0.0.yh']:
  text=file.read_text().replace('permitted','condition').replace('person','dep_template_type').replace('actor:alpha','dep_template_entity');file.write_text(text)
 _,ownership,_,_=execute('ordinary-condition-helpers',f);check('scoped F04 F05 remain ordinary authored identities',[c['availabilityState']['tag'] for c in ownership['candidates']]==['Eligible','Ineligible','EligibilityUnresolved'] and all(not c['executionIncoming'] for c in ownership['components']))
 # Additional static controls around the admitted template boundary.
 for n,old,new,code in [('shadowing','= permitted(var:actor,var:incident)','= forall var:actor as person(permitted(var:actor,var:incident))','SFT006'),('wrong-template-type','var:actor as person','var:actor as absent','SFT003'),('nested-import','export requirement-template','import other.permission version 1.0.0 as nested; export requirement-template','SFT013')]:
  f=O/('negative-'+n);shutil.copytree(w,f);file='modules/reuse.permission@1.0.0.yh';write(f,file,(f/file).read_text().replace(old,new));v=cli(n,['compose','check',f/'project.yh'],1);check(n+' rejected',v['dependencyCode']==code)
 f=O/'negative-use-budget';shutil.copytree(w,f);text=(f/'alpha.yh').read_text();text=text.rsplit('}',1)[0]+''.join('requirement-use q:extra'+str(i)+' from law::q:permission(actor:alpha,event:alpha) assessments scenario;' for i in range(129))+'}';write(f,'alpha.yh',text);check('finite use budget',cli('use-budget',['compose','check',f/'project.yh'],1)['dependencyCode']=='SFLIMIT')
 # Research-grounded selected C11 body: authorisation (not full CMA offence).
 f=O/'C11-authorisation';f.mkdir();(f/'modules').mkdir()
 law='''typed-rules-module c11.authorisation version 1.0.0 {
 export requirement-template q:unauthorised;
 entity-type person; entity-type authoriser; entity-type data; entity-type event;
 predicate entitled(person,data) kind relationship; predicate entitledAuthoriser(authoriser,data) kind relationship; predicate consent(authoriser,person,data,event) kind relationship;
 requirement-template q:unauthorised(var:a as person,var:o as authoriser,var:d as data,var:i as event) = all(not(entitled(var:a,var:d)),not(all(entitledAuthoriser(var:o,var:d),consent(var:o,var:a,var:d,var:i))));
 }'''
 write(f,'modules/c11.authorisation@1.0.0.yh',law)
 base='''typed-rules-model Authorisation {
 module-root "modules"; import c11.authorisation version 1.0.0 as cma;
 entity-type person; entity-type authoriser; entity-type data; entity-type event;
 entity subject as person; entity owner as authoriser; entity resource as data; entity access as event;
 predicate entitled(person,data) kind relationship; predicate entitledAuthoriser(authoriser,data) kind relationship; predicate consent(authoriser,person,data,event) kind relationship;
 requirement-use q:base from cma::q:unauthorised(subject,owner,resource,access) assessments scenario;
 requirement-use q:protected from cma::q:unauthorised(subject,owner,resource,access) assessments scenario;
 requirement-use q:damage from cma::q:unauthorised(subject,owner,resource,access) assessments scenario;
 proposition p:base; rule r establishes proposition p:base when q:base;
 limitation "Selected C11 unauthorised-access definition structure retained from Phase1B; fictional independent assessments; not complete CMA3/11";
 }'''
 write(f,'m.yh',base);pieces=[]
 for i,state,expected in [('cmaA','not_proved','Eligible'),('cmaB','proved','Ineligible')]:
  write(f,i+'.yh','typed-rules-scenario Selected for Authorisation { classify entitled(subject,resource) as not_proved reason "actor-specific entitlement"; classify entitledAuthoriser(owner,resource) as proved reason "owner selection"; classify consent(owner,subject,resource,access) as '+state+' reason "independent actor/data/event consent selection"; }')
  sc=scope(i,i+':actor',i+':event').rsplit('}',1)[0]+f'identity {i}:owner nominal authoriser; identity {i}:resource nominal data; }}'
  comp=f'component {i} profile native-typed model "m.yh" scenario "{i}.yh" scope {i} {{ nominal person as person; nominal event as event; nominal authoriser as authoriser; nominal data as data; entity subject as {i}:actor; entity access as {i}:event; entity owner as {i}:owner; entity resource as {i}:resource; }} rationale "Independently selected actor owner resource incident";'
  pieces.extend([sc,comp,candidate(i,i,i,'q:base')])
 write(f,'project.yh',project(pieces));_,cma,_,_=execute('C11-authorisation',f);check('C11 original body independent outcomes',[c['availabilityState']['tag'] for c in cma['candidates']]==['Eligible','Ineligible'] and len(cma['scoped_definitions']['definitions'])==1 and len(cma['scoped_definitions']['uses'])==6)
 # Independent executable production vectors for the Lean model, no shared oracle.
 vectors=[];expected=['not_satisfied','satisfied','unresolved','not_satisfied','not_satisfied','not_satisfied','not_satisfied','unresolved','unresolved']
 for index,(a1,a2) in enumerate((x,y) for x in ['proved','not_proved','unresolved'] for y in ['proved','not_proved','unresolved']):
  f=O/('conformance-'+str(index));f.mkdir();m='''typed-rules-model Vector { entity-type person; entity actor as person;
 predicate first(person) kind circumstance; predicate second(person) kind circumstance;
 requirement-template q:shared(var:a as person) = all(first(var:a),not(second(var:a)));
 requirement-use q:selected from q:shared(actor) assessments scenario;
 proposition p; rule r establishes proposition p when q:selected; limitation "Fictional fixed conformance vector"; }'''
  write(f,'m.yh',m);write(f,'s.yh',f'typed-rules-scenario V for Vector {{ classify first(actor) as {a1} reason "first"; classify second(actor) as {a2} reason "second"; }}')
  v=cli('conformance-'+str(index),['run',f/'m.yh','--scenario',f/'s.yh']);value=next(x['status'] for x in v['expressions'] if x['id']=='q:selected');check('manual conformance vector '+str(index),value==expected[index]);vectors.append(value)
 (O/'conformance-production.json').write_text(json.dumps(vectors))
 # Long supported source IDs preserve typed observation paths and layout.
 f=O/'long-identifiers';shutil.copytree(w,f);long='q:'+('long' * 24)
 for file in list(f.glob('*.yh'))+[f/'modules/reuse.permission@1.0.0.yh']:file.write_text(file.read_text().replace('q:first',long))
 _,lr,_,_=execute('long-identifiers',f);check('long source use retained',all(any(x['id']==long for x in c['executionBackend']['expressions']) for c in lr['components']))
 # Public SDK builders and existing plan facade, independently authored Haskell.
 call('compile-public-SDK',['cabal','exec','--offline','--','ghc-9.8.4','-package=yuho','-outputdir',O/'sdk-build','-o',O/'sdk',ROOT/'test/ScopedDefinitionClient.hs'],cwd=ROOT)
 call('public-builders',[O/'sdk','builders',O]);check('SDK template readable source', (O/'template.yh').read_text()=='requirement-template q:permission(var:actor as person,var:incident as event) = permitted(var:actor,var:incident);');check('SDK explicit selection source',(O/'use.yh').read_text()=='requirement-use q:first from law::q:permission(actor:alpha,event:alpha) assessments scenario;')
 document=O/'sdk-document.json';document.write_text(json.dumps(p['document']));sdk=call('public-SDK-execute',[O/'sdk','run',document,O/'sdk-export']);check('SDK scoped inspection parity',json.loads(sdk.stdout)==sd);check('SDK full eight-file parity',all(f.read_bytes()==(O/'sdk-export'/f.name).read_bytes() for f in dest.iterdir()))
 unicode_doc=copy.deepcopy(p['document']);unicode_doc['dependencyProjectSource']=None
 plan=unicode_doc['dependencyPlan']
 def rename_entity(text):return {'alpha:actor':'甲--主體','alpha:event':'事:甲','beta:actor':'乙--主體','beta:event':'事:乙'}.get(text,text)
 for sc in plan['planScopes']:
  sc['scopeActor']=rename_entity(sc['scopeActor']);sc['scopeContext']=rename_entity(sc['scopeContext']);sc['scopeEntities']=[[rename_entity(x),t] for x,t in sc['scopeEntities']]
 for c in plan['planComponents']:c['componentEntities']=[[x,rename_entity(t)] for x,t in c['componentEntities']]
 uf=O/'unicode-sdk-document.json';uf.write_text(json.dumps(unicode_doc,ensure_ascii=False));call('SDK-Unicode-scopes',[O/'sdk','run',uf,O/'unicode-sdk-export'])
 ur=json.loads((O/'unicode-sdk-export/report.json').read_text());check('SDK admitted Unicode scope isolation',{u['scope']['scopeActor'] for u in ur['scoped_definitions']['uses']}=={'甲--主體','乙--主體','gamma:actor'})
 g=json.loads((O/'unicode-sdk-export/view.json').read_text());ids=[n['id'] for n in g['nodes']];svg=E.parse(O/'unicode-sdk-export/view.svg').getroot();check('Unicode SDK injective SVG associations',len(ids)==len(set(ids)) and set(ids)<={n.attrib['data-semantic-id'] for n in svg.iter() if 'data-semantic-id' in n.attrib})
 (O/'summary.json').write_text(json.dumps({'checks':len(checks),'calls':len(calls),'output':str(O)},indent=2));print((O/'summary.json').read_text())

if __name__=='__main__':main()
