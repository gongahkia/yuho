"""Independent finite focus/partition oracle and abstract Lean comparison.
No evaluator helper generates expected sets. Temporary sources stay external.
This checks graph construction/refinement examples, not a compiler proof.
"""
from pathlib import Path
import sys, json, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'test'))
from quantitative import fixture

def main():
 o=Path(tempfile.mkdtemp(prefix='yuho-provenance-conformance-'));calls=[]
 def run(args,cwd=ROOT):
  p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
  calls.append(dict(command=list(map(str,args)),cwd=str(cwd),exit=p.returncode,stdout=p.stdout,stderr=p.stderr));(o/'commands.json').write_text(json.dumps(calls,indent=2));assert p.returncode==0,calls[-1];return p.stdout
 y=run(['cabal','list-bin','exe:yuho','--offline','--with-compiler=ghc-9.8.4']).strip()
 files=fixture('predicate a(person,event) kind circumstance; predicate b(person,event) kind circumstance; requirement q:a = a(actor,incident); requirement q:b = b(actor,incident); requirement q:result = all(q:a,q:b);','classify a(actor,incident) as not_proved reason "a"; classify b(actor,incident) as unresolved reason "b";')
 for n,b in files.items():(o/n).write_text(b)
 p=json.loads(run([y,'provenance','trace',o/'project.yh']));ids=[n['identity'] for n in p['nodes']];index={n:i for i,n in enumerate(ids)}
 edges=[(index[e['from']],index[e['to']]) for e in p['edges']];cases=[]
 for target in [n['identity'] for n in p['nodes'] if n['category'] in ['expression_observation','candidate']]:
  def closure(reverse):
   seen={index[target]}
   while True:
    more=seen|{a if reverse else b for a,b in edges if (b if reverse else a) in seen}
    if more==seen:return seen
    seen=more
  chosen=closure(True)|closure(False);inc=sorted(chosen);omit=sorted(set(range(len(ids)))-chosen)
  visible=[i for i,(a,b) in enumerate(edges) if a in chosen and b in chosen]
  request=dict(format='yuho.machine-request/v0.3-experimental',input_kind='dependency-yh',operation='explain',path=str(o/'project.yh'),focus=target)
  rf=o/'request.json';rf.write_text(json.dumps(request));response=json.loads(run([y,'machine',rf]));assert response['success'];f=response['payload']['focus']
  actual=[sorted(index[n] for n in f['included_nodes']),sorted(index[n] for n in f['omitted_nodes']),[i for i,e in enumerate(p['edges']) if e['edgeIdentity'] in f['included_edges']]]
  assert actual==[inc,omit,visible],(actual,inc,omit,visible)
  cases.append(dict(selected=inc,expected=actual))
 def leanlist(xs):return '['+','.join(map(str,xs))+']'
 code='import Yuho.CoreYuho.Provenance\nset_option maxHeartbeats 5000000\nopen Yuho.Provenance\ndef ident (n : Nat) : Id := ⟨toString n,"scope",[n],.observation⟩\n'
 code+='def ns : List Id := (List.range '+str(len(ids))+').map ident\n'
 code+='def es : List Edge := ['+','.join('⟨ident '+str(a)+',ident '+str(b)+'⟩' for a,b in edges)+']\n'
 code+='def main : IO Unit := do\n'
 for c in cases:
  code+='  let sel := fun (n : Id) => '+leanlist(c['selected'])+'.contains (n.source.toNat!)\n'
  code+='  IO.println ("VECTOR:" ++ reprStr ((included sel ns).map (fun n => n.source.toNat!), (omitted sel ns).map (fun n => n.source.toNat!), ((es.zip (List.range es.length)).filter (fun (e,_) => sel e.source && sel e.target)).map Prod.snd))\n'
 f=o/'Vectors.lean';f.write_text(code)
 run(['lake','build','Yuho.CoreYuho.Provenance'],ROOT/'mechanisation')
 output=run(['lake','env','lean','--run',f],ROOT/'mechanisation').split('VECTOR:')[1:]
 import ast
 actual=[list(ast.literal_eval(line)) for line in output];assert actual==[c['expected'] for c in cases],(actual,cases)
 (o/'results.json').write_text(json.dumps(dict(cases=cases,lean=actual),indent=2));print(json.dumps(dict(cases=len(cases),status='passed',output=str(o))))
if __name__=='__main__':main()
