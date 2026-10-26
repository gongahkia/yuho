"""Imported diagnostics: independent UTF-8 byte-span oracles and exact reviewer F01.
All fixtures/exports are external. Expected sites come from authored declarations,
not the production source mapper or diagnostic message text.
"""
import argparse, copy, json, subprocess, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = {'a.scenario.yh': 'typed-rules-scenario Inputs for HeldOut {\n classify authorises(actor,object,event) as proved reason "a independent reason source";\n classify bars(actor,event) as not_proved reason "bar a independent reason source";\n classify owns(owner,object) as not_proved reason "owner a independent reason source";\n classify delegates(owner,actor,object) as proved reason "delegation a independent reason source";\n}', 'a.yh': 'typed-rules-model HeldOut {\n module-root "modules"; import heldout.authority version 1.0.0 as law;\n entity-type person; entity-type asset; entity-type event;\n entity actor as person; entity owner as person; entity object as asset; entity event as event;\n predicate authorises(person,event,asset) kind relationship;\n predicate bars(person,event) kind circumstance;\n predicate owns(person,asset) kind relationship;\n predicate delegates(person,person,asset) kind relationship;\n requirement-use q:grant from law::q:authority(actor,owner,object,event) assessments scenario;\n requirement-use q:repeat from law::q:authority(actor,owner,object,event) assessments scenario;\n requirement q:outside = all(q:grant,not(not(q:repeat)));\n proposition p:allowed; rule r:allow establishes proposition p:allowed when q:outside;\n limitation "Fictional independent multi-role, multi-input review control; no legal conclusion";\n}', 'modules/heldout.authority@1.0.0.yh': 'typed-rules-module heldout.authority version 1.0.0 {\n export requirement-template q:authority;\n entity-type person; entity-type asset; entity-type event;\n predicate authorises(person,asset,event) kind relationship;\n predicate bars(person,event) kind circumstance;\n predicate owns(person,asset) kind relationship;\n predicate delegates(person,person,asset) kind relationship;\n requirement-template q:authority(var:a as person,var:o as person,var:x as asset,var:e as event)\n   = all(authorises(var:a,var:x,var:e),not(bars(var:a,var:e)),any(owns(var:o,var:x),delegates(var:o,var:a,var:x)));\n}', 'project.yh': 'checked-project heldout version "yuho.dependency-plan/v0.1-experimental" { source src locator "urn:independent:fictional";\nscope a actor real:a context event:a  { identity real:a nominal person; identity event:a nominal event; identity owner:a nominal person; identity asset:a nominal asset; }\ncomponent a profile native-typed model "a.yh" scenario "a.scenario.yh" scope a { nominal person as person; nominal event as event; nominal asset as asset; entity actor as real:a; entity owner as owner:a; entity object as asset:a; entity event as event:a; } rationale "Explicit independent source selection for a";\ncandidate a-candidate scope a guard a . expression q:grant mapping "yuho.condition-identity/v1" modality unspecified rationale "Fictional technical control" refs src { life-imprisonment term:a-candidate; }\n}'}
MODULE = 'modules/heldout.authority@1.0.0.yh'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('binary',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
 O=(a.output or Path(tempfile.mkdtemp(prefix='yuho-import-diagnostics-'))).resolve();O.mkdir(parents=True,exist_ok=True)
 Y=a.binary.resolve();calls=[];checks=[];oracles=[]
 def check(n,b):
  checks.append({'name':n,'passed':bool(b)});(O/'checks.json').write_text(json.dumps(checks,indent=2));assert b,n
 def call(n,argv,code=1,data=None,cwd=None):
  p=subprocess.run(list(map(str,argv)),cwd=cwd or O,input=data,capture_output=True)
  r=dict(name=n,args=list(map(str,argv)),exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode());calls.append(r);(O/'commands.json').write_text(json.dumps(calls,indent=2));check(n+' exit',p.returncode==code);return json.loads(p.stdout or p.stderr)
 def write(n,files):
  w=O/n;w.mkdir()
  for f,t in files.items():
   p=w/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
  return w
 def site(files,f,marker,token):
  b=files[f].encode();i=b.index(marker.encode())+marker.encode().index(token.encode());prefix=b[:i]
  return dict(path=f,line=prefix.count(b'\n')+1,column=len(prefix.rsplit(b'\n',1)[-1])+1,start=i,end=i+len(token.encode()),token=token)
 def located(n,w,l,s,native=False):
  path=Path(l['path'] if native else l['locationPath']);expected=w/s['path']
  check(n+' source',path==expected if path.is_absolute() else path==Path(s['path']))
  check(n+' line/byte-column',(l['line'],l['column'])==(s['line'],s['column']) if native else (l['locationLine'],l['locationColumn'])==(s['line'],s['column']))
  b=expected.read_bytes();start=sum(len(x)+1 for x in b.split(b'\n')[:s['line']-1])+s['column']-1
  check(n+' original bytes',b[start:start+len(s['token'].encode())]==s['token'].encode() and s['token']!='erson,perso')
  if not native:check(n+' exact half-open range',(l['locationStart'],l['locationEnd'])==(s['start'],s['end']) and b[l['locationStart']:l['locationEnd']]==s['token'].encode())
 def validate(n,w,d,code,primary,related,native=False):
  check(n+' code',d['code' if native else 'dependencyCode']==code)
  located(n+' primary',w,d if native else d['dependencyLocation'],primary,native)
  if related:
   r=d.get('related') if native else (d['dependencyRelated'][0] if d['dependencyRelated'] else None)
   check(n+' related exists',r is not None);located(n+' related',w,r,related,native)
 def negative(n,files,code,primary,related,all_routes=True):
  w=write(n,files);oracles.append(dict(case=n,code=code,primary=primary,related=related));(O/'expected-spans-before-execution.json').write_text(json.dumps(oracles,indent=2))
  d=call(n+'-compose',[Y,'compose','check',w/'project.yh']);validate(n,w,d,code,primary,related)
  d=call(n+'-native',[Y,'check',w/'a.yh','--scenario',w/'a.scenario.yh']);validate(n+' native',w,d,code,primary,related,True)
  for op in (['check','run'] if all_routes else ['check']):
   output=O/(n+'-refused-'+op);request=dict(format='yuho.machine-request/v0.2-experimental',input_kind='dependency-yh',operation=op,path=str(w/'project.yh'))
   if op=='run':request['output']=str(output)
   req=O/(n+'-'+op+'.request.json');req.write_text(json.dumps(request))
   v=call(n+'-machine-'+op,[Y,'machine','-' if op=='check' else req],data=req.read_bytes() if op=='check' else None)
   check(n+' no evaluation/publication '+op,v['success'] is False and v['exports']==[] and v['payload'] is None and v['effects']['evaluation'] in ('none','not_reported') and v['effects']['source_authority']=='not_validated' and not output.exists())
   validate(n+' machine '+op,w,v['diagnostics'][0],code,primary,related)
  return w
 def sig(f=ORIGINAL):return (site(f,'a.yh','predicate authorises(','authorises'),site(f,MODULE,'predicate authorises(','authorises'))
 primary,related=sig();negative('original-F01',ORIGINAL,'SFSIGNATURE',primary,related)
 # Shift layouts and put multibyte source before each declaration on its line.
 f=copy.deepcopy(ORIGINAL);f['a.yh']='\n\n'+f['a.yh'].replace('predicate authorises','limitation "é漢🙂 host"; predicate authorises');f[MODULE]='\n\n\n'+f[MODULE].replace('predicate authorises','limitation "é漢🙂 module"; predicate authorises');negative('utf8-shifted',f,'SFSIGNATURE',*sig(f))
 # Valid original signature for all subsequent controls.
 valid=copy.deepcopy(ORIGINAL);valid['a.yh']=valid['a.yh'].replace('authorises(person,event,asset)','authorises(person,asset,event)')
 # Two exact versions with the same exported definition name. Only v2 differs.
 f=copy.deepcopy(valid);second='modules/heldout.authority@2.0.0.yh';f[second]=f[MODULE].replace('version 1.0.0','version 2.0.0').replace('authorises(person,asset,event)','authorises(person,event,asset)').replace('authorises(var:a,var:x,var:e)','authorises(var:a,var:e,var:x)')
 f['a.yh']=f['a.yh'].replace('as law;','as law; import heldout.authority version 2.0.0 as other;').replace('q:repeat from law::','q:repeat from other::');negative('two-exact-versions',f,'SFSIGNATURE',site(f,'a.yh','predicate authorises(','authorises'),site(f,second,'predicate authorises(','authorises'))
 # Same textual template in another module and alias must select its own file.
 f=copy.deepcopy(valid);second='modules/heldout.other@1.0.0.yh';f[second]=f[MODULE].replace('heldout.authority','heldout.other').replace('authorises','warrants');f['a.yh']=f['a.yh'].replace('as law;','as law; import heldout.other version 1.0.0 as other;').replace('predicate authorises','predicate warrants(asset,person,event) kind relationship; predicate authorises').replace('q:repeat from law::','q:repeat from other::');negative('two-modules',f,'SFSIGNATURE',site(f,'a.yh','predicate warrants','warrants'),site(f,second,'predicate warrants','warrants'))
 # A signature selected from another real module is primary there, not in the host.
 f=copy.deepcopy(valid);second='modules/heldout.predicates@1.0.0.yh';f[second]='typed-rules-module heldout.predicates version 1.0.0 {\n export predicate authorises;\n predicate authorises(person,event,asset) kind relationship;\n}'
 f['a.yh']=f['a.yh'].replace('as law;','as law; import heldout.predicates version 1.0.0 as pred;').replace('predicate authorises(person,asset,event) kind relationship;','use predicate pred::authorises;');negative('selected-signature-origin',f,'SFSIGNATURE',site(f,second,'predicate authorises(','authorises'),site(f,MODULE,'predicate authorises(','authorises'))
 f=copy.deepcopy(valid);f['a.yh']=f['a.yh'].replace('q:grant from law::q:authority(actor,','q:grant from law::q:authority(object,');negative('host-nominal-use',f,'SFT005',site(f,'a.yh','q:authority(object,','object'),site(f,MODULE,'requirement-template q:authority(','q:authority'))
 f=copy.deepcopy(valid);f['a.yh']=f['a.yh'].replace('entity object as asset;','use entity law::object;').replace('q:grant from law::q:authority(actor,','q:grant from law::q:authority(object,');f[MODULE]=f[MODULE].replace('export requirement-template q:authority;','export requirement-template q:authority; export entity object; entity object as asset;');negative('host-imported-role-fallback',f,'SFT005',site(f,'a.yh','q:authority(object,','object'),site(f,MODULE,'requirement-template q:authority(','q:authority'))
 f=copy.deepcopy(valid);f['a.yh']=f['a.yh'].replace('q:authority(actor,owner,object,event)','q:authority(actor,owner,object)');negative('host-arity',f,'SFARITY',site(f,'a.yh','requirement-use q:grant','q:grant'),site(f,MODULE,'requirement-template q:authority(','q:authority'))
 f=copy.deepcopy(valid);f[MODULE]=f[MODULE].replace('authorises(var:a,','authorises(var:free,');negative('module-invalid-body',f,'SFT006',site(f,MODULE,'requirement-template q:authority(','q:authority'),site(f,'a.yh','from law::q:authority','law::q:authority'))
 f=copy.deepcopy(valid);f[MODULE]=f[MODULE].replace('var:x as asset','var:x as missing');negative('module-invalid-formal',f,'SFT003',site(f,MODULE,'var:x as missing','missing'),site(f,'a.yh','from law::q:authority','law::q:authority'))
 f=copy.deepcopy(valid);f['a.yh']=f['a.yh'].replace('q:repeat from law::q:authority(actor,','q:repeat from law::q:authority(object,');negative('second-use-nominal',f,'SFT005',site(f,'a.yh','q:repeat from law::q:authority(object,','object'),site(f,MODULE,'requirement-template q:authority(','q:authority'))
 # The predicates selected through ordinary use declarations retain file origin.
 def ordinary(signature='person,event',body='actor,event'):
  return {'a.yh':f'''typed-rules-model HeldOut {{ module-root "modules"; import heldout.authority version 1.0.0 as law;
 entity-type person; entity-type event; entity actor as person; entity event as event;
 use predicate law::authorises;
 requirement q:grant = authorises({body}); proposition p:r; rule r establishes proposition p:r when q:grant;
 limitation "Fictional imported predicate control"; }}''',MODULE:f'''typed-rules-module heldout.authority version 1.0.0 {{
 export predicate authorises;
 predicate authorises({signature}) kind relationship;
 }}''','a.scenario.yh':'typed-rules-scenario Inputs for HeldOut { classify authorises(actor,event) as proved reason "fictional"; }','project.yh':ORIGINAL['project.yh'].replace('identity owner:a nominal person; identity asset:a nominal asset;','').replace('nominal asset as asset;','').replace('entity owner as owner:a; entity object as asset:a;','')}
 f=ordinary('person,missing');negative('invalid-imported-predicate',f,'SFT003',site(f,MODULE,'predicate authorises(person,missing)','missing'),site(f,'a.yh','use predicate law::authorises','law::authorises'))
 f=ordinary();f[MODULE]=f[MODULE].replace('export predicate authorises;','export predicate authorises; export requirement q:bad; requirement q:bad = unknown(actor,event);');f['a.yh']=f['a.yh'].replace('requirement q:grant = authorises(actor,event);','use requirement law::q:bad; requirement q:grant = q:bad;');negative('imported-requirement',f,'SFT003',site(f,MODULE,'requirement q:bad =','q:bad'),site(f,'a.yh','use requirement law::q:bad','law::q:bad'))
 f=ordinary();f[MODULE]=f[MODULE].replace('export predicate authorises;','export predicate authorises; export rule r:bad; rule r:bad establishes proposition p:missing when authorises(actor,event);');f['a.yh']=f['a.yh'].replace('use predicate law::authorises;','use predicate law::authorises; use rule law::r:bad;');negative('imported-rule',f,'SFT003',site(f,MODULE,'proposition p:missing','p:missing'),site(f,'a.yh','use rule law::r:bad','law::r:bad'))
 f=ordinary();f[MODULE]=f[MODULE].replace('export predicate authorises;','export predicate authorises; export entity alien; entity alien as missing;');f['a.yh']=f['a.yh'].replace('use predicate law::authorises;','use predicate law::authorises; use entity law::alien;');negative('imported-entity',f,'SFT003',site(f,MODULE,'entity alien as missing','missing'),site(f,'a.yh','use entity law::alien','law::alien'))
 f=ordinary(body='event,actor');negative('host-imported-predicate-use',f,'SFT005',site(f,'a.yh','requirement q:grant','q:grant'),site(f,MODULE,'predicate authorises(','authorises'))
 f=ordinary(body='event,actor');f['a.yh']=f['a.yh'].replace('use predicate law::authorises;','predicate authorises(person,event) kind relationship;').replace('module-root "modules"; import heldout.authority version 1.0.0 as law;','');negative('local-no-import-use',f,'SFT005',site(f,'a.yh','requirement q:grant','q:grant'),site(f,'a.yh','predicate authorises(','authorises'))
 # Export-kind/privacy/version resolution errors belong to the actual host target.
 for n,change,code in [('private',lambda f:f[MODULE].replace('export requirement-template q:authority;',''),'SFNAME'),('wrong-export-kind',lambda f:f[MODULE].replace('export requirement-template','export requirement'),'SFNAME')]:
  f=copy.deepcopy(valid);f[MODULE]=change(f);negative(n,f,code,site(f,'a.yh','from law::q:authority','law::q:authority'),None,False)
 # Valid program, replay and complete exports. Also feeds a public source-backed SDK check.
 w=write('valid',valid);v=call('valid-native',[Y,'run',w/'a.yh','--scenario',w/'a.scenario.yh'],0);check('hand specified satisfied',next(x for x in v['expressions'] if x['id']=='q:grant')['status']=='satisfied')
 check('valid static non-evaluation',call('valid-check',[Y,'compose','check',w/'project.yh'],0)['evaluated'] is False)
 export=O/'valid-export';call('valid-run',[Y,'compose','run',w/'project.yh','--output',export],0);replay=O/'valid-replay';call('valid-replay',[Y,'compose','replay',export/'artifact.json','--output',replay],0)
 check('eight deterministic replay files',len(list(export.iterdir()))==8 and all(p.read_bytes()==(replay/p.name).read_bytes() for p in export.iterdir()))
 document=json.loads((export/'projection.json').read_text())['document'];document['dependencySources'].update(ORIGINAL);(O/'sdk-invalid.json').write_text(json.dumps(document))
 # Public SDK consumer: no private parser, source-map or compiler imports.
 p=subprocess.run(['cabal','exec','--offline','--','ghc-9.8.4','-package=yuho','-outputdir',str(O/'sdk-build'),'-o',str(O/'sdk'),str(ROOT/'test/ImportDiagnosticClient.hs')],cwd=ROOT,capture_output=True)
 (O/'sdk-build.log').write_bytes(p.stdout+p.stderr);check('public SDK compiles',p.returncode==0)
 d=call('sdk-source-check',[O/'sdk',O/'sdk-invalid.json']);validate('sdk',O/'original-F01',d,'SFSIGNATURE',primary,related)
 check('invalid artifacts absent',not any(p.name.startswith('refused-') for p in O.iterdir()))
 (O/'summary.json').write_text(json.dumps({'assertions':len(checks),'invocations':len(calls),'output':str(O)},indent=2));print((O/'summary.json').read_text())
if __name__=='__main__':main()
