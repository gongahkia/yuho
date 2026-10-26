"""Independent source/read/edge oracles for opt-in typed provenance.
Generated evidence stays outside the checkout; literal expectations precede runs.
"""
import argparse, copy, hashlib, json, subprocess, tempfile
import jsonschema
from pathlib import Path
import xml.etree.ElementTree as E
from quantitative import fixture, val, project, scope, component, candidate, HEADER, PREFIX, SUFFIX
ROOT=Path(__file__).resolve().parents[1]

def main():
 a=argparse.ArgumentParser();a.add_argument('binary',type=Path);a.add_argument('--output',type=Path);args=a.parse_args()
 y=args.binary.resolve();o=(args.output or Path(tempfile.mkdtemp(prefix='yuho-provenance-'))).resolve();o.mkdir(exist_ok=True,parents=True)
 checks=[];calls=[]
 def ck(n,b):
  checks.append({'name':n,'passed':bool(b)});(o/'checks.json').write_text(json.dumps(checks,indent=2));assert b,n
 def run(n,cmd,code=0,data=None):
  p=subprocess.run(list(map(str,cmd)),input=data,capture_output=True,cwd=o)
  calls.append(dict(name=n,command=list(map(str,cmd)),exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode()));(o/'commands.json').write_text(json.dumps(calls,indent=2));ck(n+' exit',p.returncode==code)
  v=json.loads(p.stdout or p.stderr) if p.stdout or p.stderr else {}
  if v.get('format')=='yuho.machine-response/v0.3-experimental':
   import jsonschema
   jsonschema.validate(v,json.loads((ROOT/'schema/machine-response-v0.3-experimental.schema.json').read_text()))
  return v
 def write(n,files):
  d=o/n;d.mkdir()
  for f,t in files.items():p=d/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
  return d
 def graph_check(n,out):
  p=json.loads((out/'provenance.json').read_text());f=json.loads((out/'focus.json').read_text());g=json.loads((out/'view.json').read_text())
  jsonschema.validate(p,json.loads((ROOT/'schema/typed-provenance-v0.1-experimental.schema.json').read_text()))
  jsonschema.validate(f,json.loads((ROOT/'schema/typed-provenance-focus-v0.1-experimental.schema.json').read_text()))
  ck(n+' versioned schemas',True)
  ns={n['identity']:n for n in p['nodes']};es={e['edgeIdentity']:e for e in p['edges']}
  ck(n+' unique structural nodes',len(ns)==len(p['nodes'])==len({tuple(n['structuralIdentity']) for n in p['nodes']}))
  ck(n+' unique edges',len(es)==len(p['edges']))
  ck(n+' all endpoints',all(e['from'] in ns and e['to'] in ns for e in es.values()))
  ck(n+' node partition',set(f['included_nodes']).isdisjoint(f['omitted_nodes']) and set(f['included_nodes'])|set(f['omitted_nodes'])==set(ns))
  ck(n+' edge partition',set(f['included_edges']).isdisjoint(f['omitted_edges']) and set(f['included_edges'])|set(f['omitted_edges'])==set(es))
  ck(n+' focus authority',f['projection']==p['identity'])
  ck(n+' graph subset',set(f['included_nodes'])=={n['id'] for n in g['nodes']})
  expect={(e['from'],e['to'],e['relationship']) for e in es.values() if e['edgeIdentity'] in f['included_edges']}
  ck(n+' graph edges',expect=={(e['from'],e['to'],e['kind']) for e in g['edges']})
  xml=E.parse(out/'view.xml');svg=E.parse(out/'view.svg')
  xn={n.attrib['id']:n.attrib for n in xml.iter() if n.tag.endswith('}node')}
  sn={n.attrib['data-semantic-id']:n.attrib for n in svg.iter() if 'data-semantic-id' in n.attrib}
  ck(n+' XML nodes',set(xn)==set(f['included_nodes']));ck(n+' SVG nodes',set(sn)==set(xn))
  ck(n+' XML edges',expect=={(e.attrib['from'],e.attrib['to'],e.attrib['kind']) for e in xml.iter() if e.tag.endswith('}edge')})
  ck(n+' SVG edges',expect=={(e.attrib['data-from'],e.attrib['data-to'],e.attrib['data-kind']) for e in svg.iter() if 'data-from' in e.attrib})
  ck(n+' DOM injective',len({v['id'] for v in sn.values()})==len(sn))
  boxes=[tuple(float(v[k]) for k in ['data-x','data-y','data-width','data-height']) for v in sn.values()]
  ck(n+' no overlapping cards',all(x+w<=a or a+c<=x or y+h<=b or b+d<=y for i,(x,y,w,h) in enumerate(boxes) for a,b,c,d in boxes[i+1:]))
  for gnode in svg.iter():
   if 'data-semantic-id' in gnode.attrib:
    v=gnode.attrib;x,y,w,h=[float(v[k]) for k in ['data-x','data-y','data-width','data-height']]
    ck(n+' text baselines contained',all(x<=float(t.attrib['x'])<=x+w and y<=float(t.attrib['y'])<=y+h for t in gnode if t.tag.endswith('}text')))
  ck(n+' DOM bindings',all(sn[b['semantic_id']]['id']==b['svg_id'] for b in f['rendered_nodes']))
  for row in g['nodes']:
   ck(n+' XML state '+row['id'][:45],xn[row['id']].get('status')==row.get('status') and xn[row['id']].get('evaluation')==row['observation']['evaluation'])
  source={n['record']['path']:n['record'] for n in ns.values() if n['category']=='source_document'}
  for e in es.values():
   site=e['evidence']
   if isinstance(site,dict) and 'qSource' in site:
    b=source[site['qSource']]['utf8'].encode();start,end=site['qStart'],site['qEnd'];line,col=site['qLine'],site['qColumn']
    ck(n+' owned span '+site['qToken'],b[start:end]==site['qToken'].encode() and sum(len(x)+1 for x in b.split(b'\n')[:line-1])+col-1==start)
  for c in p['retained']['report']['components']:
   reads=[n for n in ns.values() if n['category']=='evaluation_read' and n['authority']['component']==c['executionComponent'] and 'filter_read' not in n['structuralIdentity']]
   ck(n+' every actual read '+c['executionComponent'],len(reads)==len(c['executionReads']) and {r['record']['identity'] for r in reads}=={r['identity'] for r in c['executionReads']})
   for r in reads:
    inputs=r['record']['input_records'];actual=[e for e in es.values() if e['to']==r['identity'] and e['relationship'] in ['reads_classification','reads_scalar','expands_reference']]
    ck(n+' every actual typed input',len(actual)==len(inputs))
    for e in actual:
     if e['relationship']=='reads_classification':
      fact=ns[e['from']]['record']['actual'];inp=e['evidence']
      ck(n+' structural tuple and exact classification',fact['predicate']==inp['predicate'] and fact['arguments']==inp['arguments'] and fact['status']==inp['classification']['status'] and fact['reason']==inp['classification']['reason'])
  return p,ns,es
 def execute(n,files):
  d=write(n,files);static=run(n+' static',[y,'provenance','inspect',d/'project.yh'])
  ck(n+' no hidden static evaluation',static['mode']=='checked_not_evaluated' and not any(x['evaluation']=='evaluated' for x in static['nodes']))
  (d/'static.json').write_text(json.dumps(static,indent=2));out=o/(n+'-export');run(n+' execution',[y,'provenance','run',d/'project.yh','--output',out])
  p,ns,es=graph_check(n,out)
  for row in ns.values():
   if row['category']=='source_document':
    r=row['record'];ck(n+' original independent source bytes '+r['path'],r['path'] in files and r['utf8']==files[r['path']] and r['sha256']==hashlib.sha256(files[r['path']].encode()).hexdigest())
  return d,out,p,ns,es

 expected={'ordinary':{'q:first':'not_satisfied','q:unknown':'unresolved','q:result':'not_satisfied'},'quantified':{'actor':'satisfied','other':'not_satisfied','q:result':'not_satisfied'},'quantity':{'subtotal':30,'total':60,'q:result':'satisfied'},'scoped':{'A':'satisfied','B':'not_satisfied','C':'unresolved'}}
 (o/'expected-before-execution.json').write_text(json.dumps(expected,indent=2))
 # Held-out ordinary conditions, all(F,U)=F and a genuine reference chain.
 body='''predicate condition(person,event) kind circumstance; predicate uncertain(person,event) kind circumstance;
 requirement q:first = condition(actor,incident); requirement q:unknown = uncertain(actor,incident);
 requirement q:chain = q:unknown; requirement q:result = all(q:first,q:chain);'''
 values='classify condition(actor,incident) as not_proved reason "independent negative"; classify uncertain(actor,incident) as unresolved reason "explicit unresolved authority";'
 files=fixture(body,values);files['model.yh']=files['model.yh'].replace('quantitative version "yuho.quantitative/v0.1-experimental";','')
 d,out,p,ns,es=execute('ordinary',files)
 observations={n['record']['id']:n['state'] for n in ns.values() if n['category']=='expression_observation'}
 ck('literal all F U is F',all(observations[k]==v for k,v in expected['ordinary'].items()))
 selected=[n for n in ns.values() if n['category']=='selected_classification'];ck('two supplied tuples with different authority',len(selected)==2 and {n['state'] for n in selected}=={'not_satisfied','unresolved'})
 result=next(n['identity'] for n in ns.values() if n['category']=='expression_observation' and n['record']['id']=='q:first')
 focused=o/'ordinary-focus';run('focus actual result',[y,'provenance','replay',out/'artifact.json','--focus',result,'--output',focused]);fp,_,_=graph_check('focused',focused)
 ck('complete evidence unchanged by focus',fp==p)
 ff=json.loads((focused/'focus.json').read_text());ck('actual omissions',bool(ff['omitted_nodes']) and bool(ff['omitted_edges']))
 replay=o/'ordinary-replay';run('unchanged replay',[y,'provenance','replay',out/'artifact.json','--output',replay]);ck('six deterministic replay bytes',all(f.read_bytes()==(replay/f.name).read_bytes() for f in out.iterdir()))
 run('invalid focus',[y,'provenance','replay',out/'artifact.json','--focus','wrong-but-existing-source','--output',o/'bad-focus'],1);ck('invalid focus no publication',not (o/'bad-focus').exists())
 run('existing destination',[y,'provenance','replay',out/'artifact.json','--output',out],1)
 (d/'scenario.yh').write_text((d/'scenario.yh').read_text().replace('independent negative','same technical value revised source'))
 revised=o/'revised';run('same status source revision',[y,'provenance','run',d/'project.yh','--output',revised]);rp=json.loads((revised/'provenance.json').read_text());ck('same status different authority',rp['authority']!=p['authority'])
 old=o/'old-after-revision';run('old saved authority',[y,'provenance','replay',out/'artifact.json','--output',old]);ck('old projection immutable',(old/'provenance.json').read_bytes()==(out/'provenance.json').read_bytes())
 # Groundings are actual eager occurrences; declaration order is not an input source.
 quantified=copy.deepcopy(files);quantified['model.yh']=quantified['model.yh'].replace('predicate condition','entity other as person; predicate condition').replace('requirement q:result = all(q:first,q:chain);','requirement q:result = forall var:x as person (condition(var:x,incident));')
 quantified['scenario.yh']=quantified['scenario.yh'].replace('condition(actor,incident) as not_proved','condition(actor,incident) as proved').replace('}', 'classify condition(other,incident) as not_proved reason "other independent scope"; }')
 quantified['project.yh']=quantified['project.yh'].replace('identity target:actor nominal person;','identity target:actor nominal person; identity target:other nominal person;').replace('entity actor as target:actor;','entity actor as target:actor; entity other as target:other;')
 _,_,qp,qn,qe=execute('quantified',quantified)
 qr=[n for n in qn.values() if n['category']=='evaluation_read' and n['record']['root']==['expression','q:result']]
 ck('forall exact three rows',len(qr)==3)
 ck('forall exact bindings', {tuple(map(tuple,n['record']['bindings'])):n['state'] for n in qr if n['record']['operator']=='predicate'}=={(('var:x','actor'),):'satisfied',(('var:x','other'),):'not_satisfied'})
 # Money, inclusion and multi-stage arithmetic. Expected totals are manual ints.
 qbody='''predicate member(person,event) kind circumstance;
 requirement q:include = member(actor,incident);
 scalar v:a type money SGD; scalar v:b type money SGD; scalar v:threshold type money SGD;
 derive v:subtotal type money SGD = sum(item a value ref(v:a),item b value ref(v:b) when q:include);
 derive v:total type money SGD = scale(2,ref(v:subtotal));
 requirement q:result = compare(v:total,eq,v:threshold);'''
 qvalues=val('v:a',10,'money SGD')+val('v:b',20,'money SGD')+val('v:threshold',60,'money SGD')+'classify member(actor,incident) as proved reason "membership supplied";'
 qfiles=fixture(qbody,qvalues);qd,qo,qproj,qnodes,qedges=execute('quantity',qfiles)
 roots=[n for n in qnodes.values() if n['category']=='exact_calculation' and n['record']['record']['path']==[]]
 ck('exact intermediate scalar values',{n['record']['record']['output']:n['record']['record']['result']['integer'] for n in roots}=={'v:subtotal':'30','v:total':'60'})
 ck('filter ledgers projected',any('filter_read' in n['structuralIdentity'] for n in qnodes.values()))
 ck('filter decision linked',any(e['relationship']=='filter_decision' for e in qedges.values()))
 for name,status,total in [('excluded','not_proved','10'),('unknown','unresolved',None)]:
  f=copy.deepcopy(qfiles);f['scenario.yh']=f['scenario.yh'].replace('as proved','as '+status)
  _,_,pp,nn,ee=execute(name,f)
  root=next(n for n in nn.values() if n['category']=='exact_calculation' and n['record']['record']['output']=='v:subtotal' and n['record']['record']['path']==[])
  ck(name+' exact state',root['record']['record']['result'].get('integer')==total)
  if name=='excluded':ck('excluded operand distinguished',any(e['relationship']=='excluded_evaluated_item' for e in ee.values()))
 # Cross-interface closed authority and machine transports.
 for kind,path,op in [('dependency-yh',qd/'project.yh','inspect'),('dependency-artifact-json',qo/'artifact.json','inspect'),('dependency-yh',qd/'project.yh','provenance'),('dependency-artifact-json',qo/'artifact.json','provenance')]:
  req={'format':'yuho.machine-request/v0.3-experimental','input_kind':kind,'operation':op,'path':str(path)}
  if op=='provenance':req['output']=str(o/(kind+'-'+op))
  rf=o/(kind+'-'+op+'.request.json');rf.write_text(json.dumps(req))
  v=run(kind+op,[y,'machine',rf]);ck('machine success '+kind+op,v['success'] and v['effects']['source_authority']==('current_sources' if kind=='dependency-yh' else 'embedded_artifact'))
  if op=='inspect':ck('machine static no evaluation',v['effects']['evaluation']=='none' and not v['exports'])
  if op=='provenance':req['output']=str(o/(kind+'-stdin'))
  v=run(kind+op+' stdin',[y,'machine','-'],data=json.dumps(req).encode());ck('stdin success',v['success'])
 for kind,path in [('dependency-yh',qo/'artifact.json'),('dependency-artifact-json',qd/'project.yh')]:
  req={'format':'yuho.machine-request/v0.3-experimental','input_kind':kind,'operation':'inspect','path':str(path)}
  v=run('wrong machine authority '+kind,[y,'machine','-'],1,json.dumps(req).encode());ck('failed authority truthful',not v['success'] and not v['exports'] and v['effects']['source_authority']=='not_validated')
 # Shared authored relationship, three independent actor/context selections.
 module='''typed-rules-module reuse.permission version 1.0.0 {
 export requirement-template q:permission; entity-type person; entity-type event;
 predicate permitted(person,event) kind relationship;
 requirement-template q:permission(var:actor as person,var:incident as event) = permitted(var:actor,var:incident);
 }'''
 shared={'modules/reuse.permission@1.0.0.yh':module};parts=[]
 for n,st in [('A','proved'),('B','not_proved'),('C','unresolved')]:
  shared[n+'.yh']='''typed-rules-model Reuse { module-root "modules"; import reuse.permission version 1.0.0 as law;
 entity-type person; entity-type event; entity actor as person; entity incident as event;
 predicate permitted(person,event) kind relationship;
 requirement-use q:first from law::q:permission(actor,incident) assessments scenario;
 requirement-use q:second from law::q:permission(actor,incident) assessments scenario;
 requirement q:result = all(q:first,q:second);
 proposition p:result; rule r:result establishes proposition p:result when q:result;
 limitation "Fictional independent supplied classifications"; }'''
  shared[n+'.scenario.yh']=f'typed-rules-scenario Selected for Reuse {{ classify permitted(actor,incident) as {st} reason "{n} independent selected reason"; }}'
  parts += [scope(n),component(n,n+'.yh',n+'.scenario.yh'),candidate('candidate-'+n,n)]
 shared['project.yh']=project(parts)
 sd,so,sp,sn,se=execute('scoped',shared)
 ck('one shared authored body',len([n for n in sn.values() if n['category']=='shared_definition'])==1)
 ck('six distinct authored uses',len([n for n in sn.values() if n['category']=='definition_use'])==6)
 for c,st in expected['scoped'].items():ck('scoped independent result '+c,{n['state'] for n in sn.values() if n['category']=='expression_observation' and n['authority']['component']==c}=={st})
 eq=copy.deepcopy(shared);eq['B.scenario.yh']=eq['B.scenario.yh'].replace('not_proved','proved')
 _,_,ep,en,ee=execute('equal-authority',eq)
 ck('equal results distinct selections',len({n['identity'] for n in en.values() if n['category']=='selected_classification'})==3)
 # Independent negative readiness and type controls never publish.
 for name,ff in [('missing',copy.deepcopy(qfiles)),('currency',copy.deepcopy(qfiles))]:
  if name=='missing':ff['scenario.yh']=ff['scenario.yh'].replace(val('v:a',10,'money SGD'),'')
  else:ff['scenario.yh']=ff['scenario.yh'].replace('money SGD 10','money USD 10')
  w=write(name,ff);dest=o/(name+'-refused');run(name,[y,'provenance','run',w/'project.yh','--output',dest],1);ck(name+' no export',not dest.exists())

 # Repeated membership references are two actual item evaluations, not one.
 repeat=fixture(qbody.replace('derive v:subtotal type money SGD = sum(item a value ref(v:a),item b value ref(v:b) when q:include);','derive v:subtotal type money SGD = sum(item a value ref(v:a) when q:include,item b value ref(v:b) when q:include);'),qvalues)
 _,_,_,rn,re=execute('repeated-filter',repeat)
 rr=[n for n in rn.values() if n['category']=='evaluation_read' and 'filter_read' in n['structuralIdentity'] and n['record']['path']==[]]
 ck('distinct actual filter item occurrences',len(rr)==2 and len({n['identity'] for n in rr})==2 and {n['structuralIdentity'][-5] for n in rr}=={'a','b'})
 countfiles=fixture('predicate member(person,event) kind circumstance; requirement q:include = member(actor,incident); derive v:total type count events = count(item first when q:include,item second when q:include); scalar v:threshold type count events; requirement q:result = compare(v:total,eq,v:threshold);',val('v:threshold',2,'count events')+'classify member(actor,incident) as proved reason "two explicitly identified hypothetical members";')
 _,_,_,cn,ce=execute('count',countfiles)
 ck('count retains nominal exact two',any(n['category']=='exact_calculation' and n['record']['record']['result'].get('integer')=='2' for n in cn.values()))
 # Actual quantitative observation -> checked slot -> candidate.
 chain=copy.deepcopy(qfiles)
 chain['receiver.yh']='typed-rules-model Receipt { entity-type person; entity-type event; entity actor as person; entity incident as event; dependency-condition in:gate type technical-condition; requirement q:result = condition(in:gate); proposition p:result; rule r:result establishes proposition p:result when q:result; limitation "Fictional receiver"; }'
 chain['receiver.yhs']='typed-rules-scenario ReceiptInputs for Receipt {}'
 chain['project.yh']=project([scope(),component(),component('receiver','receiver.yh','receiver.yhs',sc='target'),'bind transfer from target . expression q:result to receiver . condition in:gate mapping "yuho.condition-identity/v1" rationale "Explicit calculated comparison input" refs src;',candidate('candidate','receiver',sc='target')])
 chd,cho,chp,chn,che=execute('chain',chain)
 gen=[n for n in chn.values() if n['category']=='generated_condition_input'];ck('one exact generated input',len(gen)==1 and gen[0]['state']=='satisfied' and gen[0]['record']['generated_by']==['transfer'])
 ck('generated input conversion edge',any(e['to']==gen[0]['identity'] and e['relationship']=='generated_by_binding' for e in che.values()))
 ck('actual generated primitive read',any(e['from']==gen[0]['identity'] and e['relationship']=='reads_classification' for e in che.values()))
 # Known SDK v0.3 source selection; explicit assessments stay distinguishable.
 sdkfiles={p.name:p.read_text() for p in (ROOT/'test/fixtures/dependency/SDK').iterdir() if p.suffix in ['.json','.yh']}
 sdkfiles['project.yh']=sdkfiles.pop('project.proposed.yh',sdkfiles.get('project.yh',''))
 _,_,_,sdkn,sdke=execute('sdk-producer',sdkfiles)
 selected_sdk=[n for n in sdkn.values() if n['category']=='selected_classification']
 ck('SDK exact original application assessment links',all(sdkn[e['to']]['record']['object']['assessedApplication']==sdkn[e['from']]['record']['metadata']['typedId'] and sdkn[e['to']]['record']['object']['assessedTuple']==e['evidence'] for e in sdke.values() if e['relationship']=='assesses_application'))
 ck('SDK selected assessment records retained',bool(selected_sdk) and all(n['record']['selected_sdk'] for n in selected_sdk))
 # Public SDK consumer and semantic-tamper rejection, with identical exports.
 build=o/'sdk-build';build.mkdir();client=o/'provenance-client'
 proc=subprocess.run(['cabal','exec','--offline','--','ghc-9.8.4','-package=yuho','-outputdir',str(build),'-o',str(client),str(ROOT/'test/ProvenanceClient.hs')],cwd=ROOT,capture_output=True)
 (o/'sdk-build.log').write_bytes(proc.stdout+proc.stderr);ck('public provenance SDK compiles',proc.returncode==0)
 proc=subprocess.run([client,qd/'project.yh',o/'sdk-output'],capture_output=True);(o/'sdk-client.log').write_bytes(proc.stdout+proc.stderr);ck('public SDK operations and tamper controls',proc.returncode==0)
 for name,signature,update in [('Projection','Projection -> Projection','p { nodes = [] }'),('Node','Node -> Node','p { state = Nothing }'),('Edge','Edge -> Edge','p { from = "wrong" }'),('Focus','Focus -> Focus','p { focusOmittedNodes = [] }')]:
  attempt=o/('Opaque'+name+'.hs');attempt.write_text('{-# LANGUAGE OverloadedStrings #-}\nmodule Opaque'+name+' where\nimport Yuho.Authoring.Provenance\nalter :: '+signature+'\nalter p = '+update+'\n')
  refusal=subprocess.run(['cabal','exec','--offline','--','ghc-9.8.4','-package=yuho','-fno-code','-outputdir',str(build),str(attempt)],cwd=ROOT,capture_output=True)
  (o/('opaque-'+name+'.log')).write_bytes(refusal.stdout+refusal.stderr);ck('public '+name+' cannot be mutated',refusal.returncode!=0 and (b'record field' in refusal.stderr or b'record selector' in refusal.stderr))
 ck('public SDK complete projection identical',(o/'sdk-output/provenance.json').read_bytes()==(qo/'provenance.json').read_bytes())
 validator=jsonschema.Draft202012Validator(json.loads((ROOT/'schema/typed-provenance-v0.1-experimental.schema.json').read_text()))
 for value in [p,qproj,sp,chp]:ck('new schema validates actual record',not list(validator.iter_errors(value)))
 trace=run('full structured trace',[y,'provenance','trace-artifact',qo/'artifact.json']);ck('trace complete without render',trace==qproj)
 target=next(n['identity'] for n in qnodes.values() if n['category']=='expression_observation' and n['record']['id']=='q:result')
 explanation=run('structured explanation',[y,'provenance','explain',qo/'artifact.json','--focus',target]);ck('explanation exact result and authority',explanation['target']==target and explanation['projection']==qproj['identity'])
 # SDK original quotation ownership, including the exact multibyte source.
 references=[e for e in sdke.values() if e['relationship']=='sdk_source_reference']
 ck('SDK original source reference edge',len(references)==1)
 ref=references[0];anchor=sdkn[ref['from']];src=sdkn[anchor['authority']]['record'];span=anchor['record']['referenceSpan']
 ck('SDK exact Unicode original bytes',src['sourceText'].encode()[span['start']:span['end']]=='猫'.encode() and span['startColumn']==3)
 # Multiple anchors in one source and equal quotations in distinct source records.
 anchors=copy.deepcopy(sdkfiles);adoc=json.loads(anchors['source.json']);source2=copy.deepcopy(adoc['typedOriginalSources'][0]);source2['sourceId']='distinct-original';adoc['typedOriginalSources'].append(source2)
 meta=adoc['typedExpressions'][0]['expressionMeta'];meta['typedSources'] += [{'referenceSource':'original','referenceSpan':{'start':0,'end':2,'startLine':1,'startColumn':1,'endLine':1,'endColumn':3}}, {'referenceSource':'distinct-original','referenceSpan':copy.deepcopy(meta['typedSources'][0]['referenceSpan'])}]
 anchors['source.json']=json.dumps(adoc);_,_,_,acn,ace=execute('original-anchors',anchors)
 ck('three distinct authoritative anchors',len([n for n in acn.values() if n['category']=='source_reference'])==3 and len([e for e in ace.values() if e['relationship']=='sdk_source_reference'])==3)
 # An added unselected assessment remains authored, never an execution input.
 unused=copy.deepcopy(sdkfiles);doc=json.loads(unused['source.json']);a=copy.deepcopy(doc['typedAssessments'][0]);a['typedAssessmentMeta']['typedId']='unused';a['typedAssessmentMeta']['typedLabel']='unused';a['typedAssessmentReason']='not selected';doc['typedAssessments'].append(a);unused['source.json']=json.dumps(doc)
 _,_,_,un,ue=execute('unselected',unused)
 ck('unselected assessment remains authored',any(n['category']=='sdk_authored_object' and n['record']['metadata']['typedId']=='unused' for n in un.values()))
 ck('unselected assessment never selected',all(v['typedAssessmentMeta']['typedId']!='unused' for n in un.values() if n['category']=='selected_classification' for v in n['record']['selected_sdk']))
 # In-memory technical template: exact accepted false-ancestry reproduction.
 doc=json.loads((ROOT/'test/fixtures/dependency-integrity/false-conflict.json').read_text())
 t=doc['dependencyPlan']['planComponents'][1]['componentTemplate']
 t['templateRequirements'].append(['q:strong',{'tag':'TemplateAll','contents':[{'tag':'TemplateAtom','contents':['own',['person:a','event:i']]},{'tag':'TemplateReference','contents':'q:uses-slot'}]}])
 cand=doc['dependencyPlan']['planCandidates'][0];extra_c=copy.deepcopy(cand);extra_c['candidateIdentity']='actual-transitive';extra_c['candidateGuard']['portObject']='q:strong';doc['dependencyPlan']['planCandidates'].append(extra_c)
 def unicode_names(v):
  if isinstance(v,str):return '規則(α,β' if v=='own' else v
  if isinstance(v,list):return [unicode_names(x) for x in v]
  if isinstance(v,dict):return {k:unicode_names(x) for k,x in v.items()}
  return v
 doc=unicode_names(doc)
 source=o/'in-memory-conflict.json';source.write_text(json.dumps(doc));dest=o/'in-memory-conflict-export'
 proc=subprocess.run([client,source,dest],capture_output=True);(o/'conflict-sdk.log').write_bytes(proc.stdout+proc.stderr);ck('in-memory projection accepted',proc.returncode==0)
 cp,cn,ce=graph_check('conflict',dest);cs=cp['retained']['report']['candidates']
 independent=next(c for c in cs if c['availabilityCandidate']['candidateIdentity']!= 'actual-transitive');dependent=next(c for c in cs if c['availabilityCandidate']['candidateIdentity']=='actual-transitive')
 ck('unrelated ancestry absent',independent['availabilityGuard']['conversionCauses']==[] and independent['availabilityState']['tag']=='Ineligible')
 ck('genuine conflict retained despite definitive F',dependent['availabilityState']['tag']=='Ineligible' and any(x.startswith('conflict:') for x in dependent['availabilityGuard']['conversionCauses']))
 def ancestors(target):
  seen={target}
  while True:
   nxt=seen|{e['from'] for e in ce.values() if e['to'] in seen}
   if nxt==seen:return seen
   seen=nxt
 for q,expected in [('q:independent',False),('q:strong',True)]:
  target=next(n['identity'] for n in cn.values() if n['category']=='expression_observation' and n['authority']['component']=='d' and n['record']['id']==q)
  ck('actual generated ancestor '+q,any(cn[i]['category']=='generated_condition_input' for i in ancestors(target))==expected)
 # Multiple allegations plus actual imported author ownership use accepted source fixtures.
 fix=ROOT/'test/fixtures/dependency/C';ff={f.name:f.read_text() for f in fix.iterdir() if f.suffix in ['.yh','.yhs']};ff['project.yh']=ff.pop('project.proposed.yh')
 _,_,_,an,ae=execute('allegations',ff)
 ck('allegations remain distinct', {n['authority']['scope']['scopeAllegation'] for n in an.values() if n['category']=='expression_observation'}=={'allegation:a','allegation:b'})
 # Authored norms/routes have explicit lowering edges, never fabricated rules.
 normative=copy.deepcopy(files);normative['model.yh']=normative['model.yh'].replace('proposition p:result;', 'proposition p:result; proposition p:action; norm n:duty subject actor modality required action proposition p:action when q:first; responsibility-route route:aid subject actor kind intentional-aid target proposition p:action when q:chain;')
 _,_,_,nn,ne=execute('normative',normative)
 ck('norm and route explicit checked lowering', {e['evidence'] for e in ne.values() if e['relationship']=='lowered_as'}=={'norm','responsibility-route'})
 # UTF-8 and punctuation-bearing authored names preserve structural tuples.
 unicode=copy.deepcopy(files)
 for name in ['model.yh','scenario.yh']:unicode[name]=unicode[name].replace('condition','condition:alpha').replace('uncertain','condition:beta').replace('independent negative','分類 猫 independent negative').replace('predicate condition:alpha','// 多字節 source ownership\npredicate condition:alpha')
 _,_,_,un,ue=execute('unicode',unicode)
 ck('Unicode exact structural identities',{n['record']['actual']['predicate'] for n in un.values() if n['category']=='selected_classification'}=={'condition:alpha','condition:beta'})
 # Source order changes authority but preserves values and actual read records.
 reordered=copy.deepcopy(files);reordered['model.yh']=reordered['model.yh'].replace('requirement q:first = condition(actor,incident); requirement q:unknown = uncertain(actor,incident);','requirement q:unknown = uncertain(actor,incident); requirement q:first = condition(actor,incident);')
 _,_,_,on,oe=execute('reordered',reordered)
 ck('declaration order semantic independence',{n['record']['id']:n['state'] for n in on.values() if n['category']=='expression_observation'}==observations)
 ck('A and C unchanged when B revised',next(n['state'] for n in en.values() if n['category']=='expression_observation' and n['authority']['component']=='A')=='satisfied' and next(n['state'] for n in en.values() if n['category']=='expression_observation' and n['authority']['component']=='C')=='unresolved')
 # One authored quantitative expression, two independently selected scopes.
 qm='typed-rules-module quantitative.shared version 1.0.0 {'+HEADER+' export scalar v:a; export scalar v:b; export scalar v:total; scalar v:a type integer; scalar v:b type integer; derive v:total type integer = sum(item first value ref(v:a),item second value ref(v:b)); }'
 host=PREFIX+'module-root "modules"; import quantitative.shared version 1.0.0 as shared; use scalar shared::v:a; use scalar shared::v:b; use scalar shared::v:total; scalar v:threshold type integer; requirement q:result = compare(v:total,gte,v:threshold);'+SUFFIX
 qsc={'a.yh':host,'b.yh':host,'modules/quantitative.shared@1.0.0.yh':qm,'a.scenario.yh':'typed-rules-scenario A for Quantities {'+val('v:a',4,reason='A independent')+val('v:b',6)+val('v:threshold',10)+'}','b.scenario.yh':'typed-rules-scenario B for Quantities {'+val('v:a',1,reason='B independent')+val('v:b',2)+val('v:threshold',10)+'}','project.yh':project([scope('a'),scope('b'),component('a','a.yh','a.scenario.yh'),component('b','b.yh','b.scenario.yh'),candidate('A','a'),candidate('B','b')])}
 _,_,_,qsn,qse=execute('shared-quantity',qsc)
 ck('one quantitative authorship two uses',sum(n['category']=='quantitative_definition' for n in qsn.values())==1 and sum(n['category']=='quantitative_use' for n in qsn.values())==2)
 def numeric_roots(ns):return {n['record']['scope']['scopeIdentity']:n['record']['record']['result']['integer'] for n in ns.values() if n['category']=='exact_calculation' and n['record']['record']['path']==[]}
 ck('independent exact numeric roots',numeric_roots(qsn)=={'a':'10','b':'3'})
 equal=copy.deepcopy(qsc);equal['b.scenario.yh']=equal['b.scenario.yh'].replace('integer 1 reason','integer 8 reason');_,_,_,eqn,eqe=execute('equal-quantities',equal)
 ck('equal numeric values remain distinct',numeric_roots(eqn)=={'a':'10','b':'10'} and len({n['identity'] for n in eqn.values() if n['category']=='exact_calculation' and n['record']['record']['path']==[]})==2)
 changed=copy.deepcopy(qsc);changed['a.scenario.yh']=changed['a.scenario.yh'].replace('integer 4 reason','integer 40 reason');_,_,_,chn,che=execute('quantitative-isolation',changed)
 ck('independent B retains value',numeric_roots(chn)=={'a':'46','b':'3'})
 b_before=[n['record'] for n in qsn.values() if n['category'] in ['supplied_quantity','exact_calculation'] and n['record']['scope']['scopeIdentity']=='b']
 b_after=[n['record'] for n in chn.values() if n['category'] in ['supplied_quantity','exact_calculation'] and n['record']['scope']['scopeIdentity']=='b']
 ck('B retains independent inputs, scope and calculations', [{k:v for k,v in r.items() if k!='snapshot'} for r in b_before]==[{k:v for k,v in r.items() if k!='snapshot'} for r in b_after])
 ck('revised execution snapshot is distinct',b_before[0]['snapshot']!=b_after[0]['snapshot'])
 # Invalid focuses/publication and tampered artifacts cannot claim exports.
 for name,focus,destination in [('bad-focus','absent',o/'machine-bad-focus'),('existing',None,qo)]:
  req={'format':'yuho.machine-request/v0.3-experimental','input_kind':'dependency-artifact-json','operation':'provenance','path':str(qo/'artifact.json'),'output':str(destination)}
  if focus:req['focus']=focus
  response=run('machine failure '+name,[y,'machine','-'],1,json.dumps(req).encode());ck('machine no successful export '+name,not response['success'] and response['exports']==[] and response['effects']['source_authority']=='not_validated')
 artifact=json.loads((qo/'artifact.json').read_text())
 # A digest field is altered independently of the implementation encoder.
 def corrupt(v):
  if isinstance(v,dict):
   for k,x in v.items():
    if 'digest' in k.lower() and isinstance(x,str) and len(x)==64:v[k]='0'*64;return True
    if corrupt(x):return True
  if isinstance(v,list):return any(corrupt(x) for x in v)
  return False
 ck('artifact digest field found',corrupt(artifact));tampered=o/'tampered-artifact.json';tampered.write_text(json.dumps(artifact));run('tampered artifact replay',[y,'provenance','replay',tampered,'--output',o/'tampered-export'],1);ck('tampered artifact no publication',not (o/'tampered-export').exists())
 # Same export label from two exact module versions retains two authorities.
 versions=copy.deepcopy(shared);versions['modules/reuse.permission@2.0.0.yh']=module.replace('version 1.0.0','version 2.0.0')
 for name in ['A.yh','B.yh','C.yh']:
  versions[name]=versions[name].replace('as law;','as law; import reuse.permission version 2.0.0 as law2;').replace('q:second from law::','q:second from law2::')
 _,_,_,vn,ve=execute('module-versions',versions)
 definitions=[n for n in vn.values() if n['category']=='shared_definition']
 ck('exact original module/version owner paths',all(n['record']['definitionSource']=='modules/reuse.permission@'+n['record']['definitionKey'][1]+'.yh' for n in definitions))
 ck('two exact original module identities',len(definitions)==2 and {n['record']['definitionKey'][1] for n in definitions}=={'1.0.0','2.0.0'})
 for e in ve.values():
  if e['relationship']=='authored_in' and vn[e['to']]['category']=='shared_definition':
   ck('version-resolved owner',vn[e['from']]['record']['path']==vn[e['to']]['record']['definitionSource'])
 # Structured evidence stays available when full diagram reaches its explicit bound.
 dense=copy.deepcopy(files);dense['model.yh']=dense['model.yh'].replace('proposition p:result;',''.join('requirement q:extra'+str(i)+' = condition(actor,incident);' for i in range(125))+'proposition p:result;')
 dd=write('dense-refusal',dense);dp=run('dense structured trace',[y,'provenance','trace',dd/'project.yh']);ck('dense complete over render bound',len(dp['nodes'])>512)
 (dd/'trace.json').write_text(json.dumps(dp));failure=run('dense no truncation',[y,'provenance','run',dd/'project.yh','--output',o/'dense-full'],1);ck('dense explicit bounded refusal',failure['dependencyCode']=='PVLIMIT' and not (o/'dense-full').exists())
 target=next(n['identity'] for n in dp['nodes'] if n['category']=='expression_observation' and n['record']['id']=='q:extra0')
 dest=o/'dense-focused';run('dense focused publication',[y,'provenance','run',dd/'project.yh','--focus',target,'--output',dest]);graph_check('dense-focused',dest)
 (o/'summary.json').write_text(json.dumps({'assertions':len(checks),'commands':len(calls)},indent=2));print(json.dumps({'assertions':len(checks),'commands':len(calls),'output':str(o)}))
if __name__=='__main__':main()
