"""Independent abstract Lean/production compiler conformance over fixed vectors.
This is not a compiler proof: scope/source/projection refinement is tested by the
separate CLI adversarial suite. All generated models/results are external.
"""
from pathlib import Path
import json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=['not_satisfied','satisfied','unresolved','not_satisfied','not_satisfied','not_satisfied','not_satisfied','unresolved','unresolved']
def main():
 out=Path(tempfile.mkdtemp(prefix='yuho-scoped-conformance-'));commands=[]
 def run(args,cwd=ROOT):
  p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
  commands.append(dict(args=list(map(str,args)),cwd=str(cwd),exit=p.returncode,stdout=p.stdout,stderr=p.stderr));(out/'commands.json').write_text(json.dumps(commands,indent=2));assert p.returncode==0,commands[-1];return p.stdout
 y=run(['cabal','list-bin','exe:yuho','--offline','--with-compiler=ghc-9.8.4']).strip()
 run(['lake','build','Yuho.CoreYuho.ScopedDefinitions'],ROOT/'mechanisation')
 lean=run(['lake','env','lean','--run','scripts/ScopedDefinitionConformance.lean'],ROOT/'mechanisation').splitlines()
 model='''typed-rules-model Conformance {
 entity-type person; entity actor as person;
 predicate first(person) kind circumstance; predicate second(person) kind circumstance;
 requirement-template q:body(var:a as person) = all(first(var:a),not(second(var:a)));
 requirement-use q:result from q:body(actor) assessments scenario;
 proposition p; rule r establishes proposition p when q:result;
 limitation "Synthetic manually specified independent conformance vectors";
 }'''
 (out/'m.yh').write_text(model);actual=[]
 for index,(a,b) in enumerate((a,b) for a in ['proved','not_proved','unresolved'] for b in ['proved','not_proved','unresolved']):
  s=out/(str(index)+'.yh');s.write_text(f'typed-rules-scenario V for Conformance {{ classify first(actor) as {a} reason "first"; classify second(actor) as {b} reason "second"; }}')
  response=run([y,'run',out/'m.yh','--scenario',s]);(out/(str(index)+'.json')).write_text(response)
  actual.append(next(r['status'] for r in json.loads(response)['expressions'] if r['id']=='q:result'))
 assert actual==EXPECTED==lean,(actual,EXPECTED,lean)
 (out/'results.json').write_text(json.dumps(dict(expected=EXPECTED,lean=lean,production=actual),indent=2))
 print(json.dumps(dict(cases=len(EXPECTED),status='passed',output=str(out))))
if __name__=='__main__':main()
