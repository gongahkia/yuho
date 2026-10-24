"""Independent finite plan/conversion conformance; no generated expectations.

The Haskell internal model tests unavailable coordination without exposing an
invented public typed-skip producer. CLI fixtures separately exercise actual ports.
Run after a Cabal build. Every probe/output uses a disposable external directory.
"""
import argparse,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=[{'id':i,'value':v,'conflict':c,'availability':a} for i,v,c,a in [
 ('T','satisfied',False,'eligible'),('F','not_satisfied',False,'ineligible'),('U','unresolved',False,'unresolved'),
 ('P-established','satisfied',False,'eligible'),('P-defeated','not_satisfied',False,'ineligible'),
 ('P-not-established','not_satisfied',False,'ineligible'),('P-unresolved','unresolved',False,'unresolved'),
 ('P-conflict','unresolved',True,'unresolved'),('unavailable','not_evaluated',False,'not_evaluated')]]
def main():
 p=argparse.ArgumentParser();p.add_argument('--builddir',type=Path);p.add_argument('--lean-root',type=Path,default=ROOT/'mechanisation');p.add_argument('--output',type=Path);a=p.parse_args()
 out=a.output or Path(tempfile.mkdtemp(prefix='yuho-dependency-conformance-'));out.mkdir(parents=True,exist_ok=True)
 calls=[]
 def run(args,cwd):
  r=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
  calls.append({'args':list(map(str,args)),'cwd':str(cwd),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
  (out/'commands.json').write_text(json.dumps(calls,indent=2)+'\n');assert r.returncode==0,calls[-1];return r.stdout
 buildflags=['--builddir='+str(a.builddir)] if a.builddir else []
 haskell=run(['cabal','exec','--offline',*buildflags,'--','runghc-9.8.4','-isrc',ROOT/'test/DependencyModelChecks.hs',ROOT/'test/fixtures/dependency/C/project.proposed.yh'],ROOT)
 run(['lake','build','dependency_conformance'],a.lean_root)
 lean=run([a.lean_root/'.lake/build/bin/dependency_conformance'],a.lean_root)
 h=json.loads(haskell);l=json.loads(lean)
 assert h==EXPECTED,('Haskell differs from independent oracle',h)
 assert l==EXPECTED,('Lean differs from independent oracle',l)
 (out/'results.json').write_text(json.dumps({'expected':EXPECTED,'haskell':h,'lean':l,'sealed_unavailable_chain':'passed'},indent=2)+'\n')
 print(json.dumps({'vectors':len(EXPECTED),'Haskell_Lean_oracle':'equal','unavailable_chain':'passed','output':str(out)}))
if __name__=='__main__':main()
