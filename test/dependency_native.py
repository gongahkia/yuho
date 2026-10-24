"""Full admitted native component domain through checked dependencies.

Ordinary native execution is an independent adapter/path comparison sharing the
accepted finite backend. Fixed scalar/count expectations supplement that parity.
"""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 a=argparse.ArgumentParser();a.add_argument('binary',type=Path);a.add_argument('--output',type=Path);args=a.parse_args()
 out=args.output or Path(tempfile.mkdtemp(prefix='yuho-dependency-native-'));out.mkdir(parents=True,exist_ok=True)
 shutil.copytree(ROOT/'examples/typed-finite',out/'typed');shutil.copytree(ROOT/'examples/typed-finite-v0.3',out/'normative')
 calls=[];checks=[];binary=args.binary.resolve()
 def call(argv,code=0):
  p=subprocess.run([str(binary),*map(str,argv)],cwd=out,capture_output=True,text=True)
  calls.append(dict(args=list(map(str,argv)),exit=p.returncode,stdout=p.stdout,stderr=p.stderr));(out/'commands.json').write_text(json.dumps(calls,indent=2)+'\n')
  assert p.returncode==code,calls[-1];return json.loads(p.stdout if code==0 else p.stderr)
 def project(name,model,scenario,actor,context,types,allegation=None,port='q:cardinality',category='expression'):
  ci,ai=(('case:multi-person-property',allegation) if allegation else (None,None))
  case=f'case {ci} allegation {ai}' if allegation else ''
  entry=f'entry allegation {ai}' if allegation else ''
  scenario=f'scenario "{scenario}"' if scenario else ''
  type_decls=' '.join(f'nominal {t} as role:{t};' for t in sorted(set(types)))
  text=f'''checked-project plan:{name} version "yuho.dependency-plan/v0.1-experimental" {{
 source origin locator "urn:fictional:full-native-domain";
 scope selected actor project:actor context project:context {case} {{
 identity project:actor nominal role:{types[0]}; identity project:context nominal role:{types[1]}; }}
 component native profile native-typed model "{model}" {scenario} {entry} scope selected {{
 {type_decls} entity {actor} as project:actor; entity {context} as project:context;
 }} rationale "Explicitly selected actual finite source identities and occurrence";
 candidate fixture scope selected guard native . {category} {port}
 mapping "{'yuho.condition-identity/v1' if category=='expression' else 'yuho.proposition-support/v1'}" modality unspecified
 rationale "Fictional candidate only, full native adapter control" refs origin {{life-imprisonment term:fictional;}}
}}'''
  path=out/(name+'.yh');path.write_text(text);return path
 cases=[('full','typed/fictional-typed-rules.yh','typed/fictional-typed-rules-satisfied.yh','actor:alex','item:laptop',('person','property'),None,'q:cardinality'),('modules','typed/modular-typed-rules.yh','typed/modular-typed-rules-scenario.yh','actor:modular-person','item:modular-item',('person','property'),None,'q:modular-possession'),('norms','normative/normative-responsibility.yh','normative/normative-responsibility-satisfied.yh','actor:blair','actor:alex',('person','person'),None,'q:aid'),('case','typed/multi-person-property-case.yh',None,'actor:one','item:camera',('person','property'),'a:actor-one','q:one')]
 for spec in cases:
  path=project(*spec);check=call(['compose','check',path]);assert check['evaluated'] is False
  export=out/('export-'+spec[0]);call(['compose','run',path,'--output',export]);record=json.loads((export/'report.json').read_text())['components'][0]
  ordinary=call(['run',out/spec[1],*(['--scenario',out/spec[2]] if spec[2] else [])])
  if spec[6]:ordinary=next(a['result'] for a in ordinary['allegations'] if a['id']==spec[6])
  for field in ('expressions','rules','propositions'):assert record['executionBackend'][field]==ordinary[field],(spec[0],field)
  checks.append(spec[0]+' full authoritative rows agree with ordinary native run')
  if spec[0]=='full':
   statuses={r['id']:r['status'] for r in ordinary['expressions']}
   assert all(statuses[q]=='satisfied' for q in ('q:date-applicable','q:money-within','q:risk-high','q:cardinality','q:exactly'))
   assert statuses['q:minor']=='satisfied' and statuses['q:not-minor']=='not_satisfied'
   reads=record['executionReads'];assert {'forall','exists','at-least','at-most','exactly','in-half-open','lte','eq'}<={r['operator'] for r in reads}
   assert any(r['bindings'] for r in reads);checks.append('hand-specified scalar/cardinality values and actual grounded reads')
  if spec[0]=='modules':
   projection=json.loads((export/'projection.json').read_text());assert any('@1.0.0.yh' in p for p in projection['document']['dependencySources'])
   checks.append('exact version imported bytes retained')
  if spec[0]=='case':
   saved=path.read_text();path.write_text(saved.replace('case case:multi-person-property allegation a:actor-one','case case:multi-person-property allegation a:actor-two'))
   assert call(['compose','check',path],1)['dependencyCode']=='DEPSCOPE';path.write_text(saved)
   checks.append('wrong actual allegation rejected')
 # The same legal program is still admitted standalone; only a globally
 # aggregated proposition is refused as an actor-local dependency source.
 path=project('aggregate','typed/fictional-typed-rules.yh','typed/fictional-typed-rules-satisfied.yh','actor:alex','item:laptop',('person','property'),None,'p:any-property','proposition')
 assert call(['compose','check',path],1)['dependencyCode']=='DEPSCOPE';checks.append('aggregate proposition actor-local cast refused')
 # Missing a quantified grounding is a non-evaluating readiness failure.
 path=out/'full.yh';scenario=out/'typed/fictional-typed-rules-satisfied.yh';saved=scenario.read_text();scenario.write_text(saved.replace('  classify takes(actor:alex,item:phone) as not_proved reason "synthetic supplied classification";',''))
 result=call(['compose','check',path],1);assert result['dependencyCode']=='SFT011';assert result['dependencyLocation']['locationPath'].endswith('fictional-typed-rules-satisfied.yh');scenario.write_text(saved)
 checks.append('full-domain readiness diagnostic has real original coordinates')
 (out/'summary.json').write_text(json.dumps(dict(checks=checks,cli_calls=len(calls)),indent=2)+'\n');print(json.dumps(dict(checks=len(checks),cli_calls=len(calls),output=str(out))))
if __name__=='__main__':main()
