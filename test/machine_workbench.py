"""Execute the documented machine/workbench contract from a copied external tree.
Independent hand-specified expectations live in cases.json. --sdk-evidence consumes
SourceCompositionChecks output (independently authored Haskell references).
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'yuho.machine-request/v0.1-experimental'


def pointer(value, path):
    for key in path.split('/')[1:]:
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def proof_semantic(r):
    return [r['reportConclusion'], sorted([[x['observationNode'],x['observationComputed'],x['observationEvaluation'],x['observationSkipReason']] for x in r['reportRequirements']]),
            sorted([[x['ruleAuthoredId'],x['ruleComputed'],x['ruleEvaluation'],x['ruleBranchReason']] for x in r['reportRules']]),
            [[x['exceptionComputed'],x['exceptionEvaluation'],x['exceptionFired'],x['exceptionSkipReason']] for x in r['reportExceptions']]]


def derivations(r):
    if r is None:
        return None
    return [[[x['registrationAuthored']['registeredId'],x['registrationRouteState'],x['registrationEvaluation'],x['registrationTriggerResult']['resolvedConditionValue'],x['registrationRebuttalResult']['resolvedConditionValue']] for x in r['presumptionReportDerivations']],
            sorted([[x['effectiveInput'],x['effectiveDirectValue'],x['effectiveValue'],x['effectiveRoutes']] for x in r['presumptionReportLeaves']])]


def run(binary, base, sdk_evidence):
    from jsonschema import Draft202012Validator
    request_schema = Draft202012Validator(json.loads((ROOT/'schema/machine-request-v0.1-experimental.schema.json').read_text()))
    response_schema = Draft202012Validator(json.loads((ROOT/'schema/machine-response-v0.1-experimental.schema.json').read_text()))
    work = base/'workbench'
    shutil.copytree(ROOT/'examples/language-workbench', work)
    commands, results = [], []
    witnessed_pairs = set()

    def invoke(req, expected=0, raw=None):
        if expected==0:
            request_schema.validate(req)
            witnessed_pairs.add((req["input_kind"],req["operation"]))
        encoded = raw if raw is not None else json.dumps(req).encode()
        p = subprocess.run([str(binary),'machine','-'],input=encoded,cwd=base,capture_output=True,timeout=90)
        commands.append(dict(command=[str(binary),'machine','-'],stdin=encoded.decode(),cwd=str(base),exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode()))
        (base/'commands.json').write_text(json.dumps(commands,indent=2))
        assert p.returncode==expected,(req,p.stdout,p.stderr)
        assert not p.stderr,p.stderr
        response = json.loads(p.stdout)
        response_schema.validate(response)
        assert response['success']==(expected==0)
        if expected:assert response['diagnostics']
        return response

    def request(kind,op,path,**fields):
        return dict(format=VERSION,input_kind=kind,operation=op,path=str(path),**fields)

    for c in json.loads((work/'cases.json').read_text()):
        folder=base/c['id'];folder.mkdir()
        kind,path=c['input_kind'],work/c['path']
        fields={'scenario':str(work/c['scenario'])} if c['scenario'] else {}
        req=request(kind,'check',path,**fields)
        checked=invoke(req)
        assert invoke(req)==checked
        if kind=='native-yh':
            runreq=request(kind,'run',path,**fields)
            result=invoke(runreq)['payload']
            native=[str(binary),'run',str(path)]+(['--scenario',fields['scenario']] if fields else [])
            direct=subprocess.run(native,cwd=base,capture_output=True,timeout=60)
            commands.append(dict(command=native,cwd=str(base),exit=direct.returncode,stdout=direct.stdout.decode(),stderr=direct.stderr.decode()))
            assert direct.returncode==0 and json.loads(direct.stdout)==result
            compiled=invoke(request(kind,'compile',path,**fields))['payload']
            assert invoke(request(kind,'compile',path,**fields))['payload']==compiled
            (folder/'compiled.json').write_text(json.dumps(compiled,indent=2))
            inspection=request(kind,'inspect',path,**fields)
            inspected=invoke(inspection,0 if c['inspection'] else 1)
            if c['inspection']:
                assert not inspected['payload']['evaluated']
                assert invoke(inspection)==inspected
                stages=inspected['payload']['stages']
                lowered=next(x for x in stages if x['stage']=='lowered')
                assert lowered['data']['request']==compiled
                (folder/'inspection.json').write_text(json.dumps(inspected,indent=2))
            else:
                assert inspected['diagnostics'][0]['code']=='SFI002'
            for encoding in ['json','xml','svg']:
                dest=folder/('diagram.'+encoding)
                invoke(request(kind,'diagram',path,output=str(dest),view=c['view'],encoding=encoding,**fields))
                if encoding!='json':ET.parse(dest)
                original=dest.read_bytes()
                refused=invoke(request(kind,'diagram',path,output=str(dest),view=c['view'],encoding=encoding,**fields),1)
                assert refused['diagnostics'][0]['code']=='SFE015' and dest.read_bytes()==original
        else:
            invoke(request(kind,'run',path,output=str(folder/'execution')))
            result=json.loads((folder/'execution/report.json').read_text())
            native=[str(binary),'compose','run',str(path),'--output',str(folder/'native')]
            direct=subprocess.run(native,cwd=base,capture_output=True,timeout=90)
            commands.append(dict(command=native,cwd=str(base),exit=direct.returncode,stdout=direct.stdout.decode(),stderr=direct.stderr.decode()))
            assert direct.returncode==0 and not direct.stderr
            for f in (folder/'execution').iterdir():assert f.read_bytes()==(folder/'native'/f.name).read_bytes(),f.name
            artifact=folder/'execution/artifact.json'
            invoke(request('computed-input-json','check',artifact))
            invoke(request('computed-input-json','replay',artifact,output=str(folder/'replay')))
            for f in (folder/'execution').iterdir():assert f.read_bytes()==(folder/'replay'/f.name).read_bytes()
            invoke(request(kind,'run',path,output=str(folder/'execution')),1)
        for ptr,expected in c['expected'].items():assert pointer(result,ptr)==expected,(c['id'],ptr,result)
        (folder/'result.json').write_text(json.dumps(result,indent=2))
        results.append(dict(id=c['id'],expected=c['expected'],status='passed'))

    # Companion law graph: the case summary intentionally does not expose definition bodies.
    law=work/'02-definitions/law.yh';scenario=work/'02-definitions/law-input.yhs'
    inspected=invoke(request('native-yh','inspect',law,scenario=str(scenario)))
    (base/'shared-definitions/law-inspection.json').write_text(json.dumps(inspected,indent=2))
    for encoding in ['json','xml','svg']:
        invoke(request('native-yh','diagram',law,scenario=str(scenario),view='trace',encoding=encoding,
                       output=str(base/'shared-definitions'/('law-diagram.'+encoding))))
    standard=request('native-yh','run',work/'03-typed/law.yh',scenario=str(work/'03-typed/36.yhs'))
    for key,value in [('format','yuho.machine-request/v99'),('misspelt',True),('operation','serve'),('input_kind','typed-authoring-json'),('stage','lowered')]:
        invalid={**standard,key:value}
        assert not request_schema.is_valid(invalid)
        assert invoke(invalid,1)['diagnostics'][0]['code']=='SMREQUEST'
    invoke({},1,raw=b'{')
    invoke({},1,raw=b'{"format":"x","format":"y"}')
    invoke(request('native-yh','inspect',work/'03-typed/law.yh',scenario=str(work/'03-typed/36.yhs'),stage='normalized'),1)
    invoke(request('composition-yh','check',work/'06-composition/unsupported.project.yh'),1)
    malformed=base/'malformed.yh';malformed.write_text('typed-rules-model Broken { nonsense }')
    d=invoke(request('native-yh','check',malformed),1)['diagnostics'][0]
    assert d['path']==str(malformed) and d['line']==1 and d['column']>1
    # Request file mode and regular/symlink rejection; no shell expansion, including paths with spaces.
    reqfile=base/'request with spaces.json';reqfile.write_text(json.dumps(standard))
    p=subprocess.run([str(binary),'machine',str(reqfile)],cwd=base,capture_output=True,timeout=60)
    assert p.returncode==0 and not p.stderr
    link=base/'link.json';link.symlink_to(reqfile)
    p=subprocess.run([str(binary),'machine',str(link)],cwd=base,capture_output=True,timeout=60)
    assert p.returncode==1 and json.loads(p.stdout)['diagnostics'][0]['code']=='SMIO'
    # Wrong authored format and unknown fields use the existing public decoder.
    saved=base/'composition-true/execution/artifact.json';artifact=json.loads(saved.read_text())
    for key,val in [('computedDocumentFormat','bad-version'),('unknown',True)]:
        bad=base/(key+'.json');bad.write_text(json.dumps({**artifact,key:val}))
        invoke(request('computed-input-json','check',bad),1)
    # Metamorphic semantic fields: provenance/digests deliberately excluded after edits.
    original=invoke(standard)['payload']
    text=(work/'03-typed/law.yh').read_text()
    (work/'03-typed/law.yh').write_text(text.replace(' predicate permitted',' entity actor:unused as actor;\n predicate permitted'))
    revised=invoke(standard)['payload']
    for field in ['rules','expressions','propositions']:assert revised[field]==original[field],field
    (work/'03-typed/law.yh').write_text(text.replace('q:permission = permitted(actor:one','q:permission = permitted(actor:two'))
    isolated=invoke(standard)['payload'];assert isolated['rules'][0]['status']=='not_satisfied'
    (work/'03-typed/law.yh').write_text(text)
    supplied=(work/'03-typed/36.yhs').read_text()
    (work/'03-typed/36.yhs').write_text('\n'.join(x for x in supplied.splitlines() if 'classify permitted(actor:one' not in x))
    invoke(standard,1)
    (work/'03-typed/36.yhs').write_text(supplied.replace('as proved','as unresolved'))
    assert invoke(standard)['payload']['rules'][0]['status']=='unresolved'
    (work/'03-typed/36.yhs').write_text(supplied)
    # Public SDK parity: source fixtures are independent of reference constructors in native tests.
    parity=[]
    if sdk_evidence:
        rows=[json.loads(line.split('source-composition-parity ',1)[1]) for line in sdk_evidence.read_text().splitlines() if line.startswith('source-composition-parity ')]
        assert len(rows)>=11
        shutil.copytree(ROOT/'examples/source-composition',base/'source-parity')
        for row in rows:
            name=row['project'];out=base/('parity-'+name.replace('/','-'))
            invoke(request('composition-yh','run',base/'source-parity'/(name+'.project.yh'),output=str(out)))
            r=json.loads((out/'report.json').read_text())
            assert proof_semantic(r['computedDownstreamReport'])==row['reference_proof']==row['actual_proof'],name
            assert derivations(r['computedDerivationReport'])==row.get('reference_derivations')==row.get('actual_derivations'),name
            parity.append(dict(project=name,proof=True,derivations=True,shared_backend=True))
    spec=importlib.util.spec_from_file_location('workbench_client',work/'client.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.main(binary,work,base/'python-client')
    (base/'commands.json').write_text(json.dumps(commands,indent=2))
    capabilities=json.loads((ROOT/'test/machine_capabilities.json').read_text())
    assert {(r['input_kind'],r['operation']) for r in capabilities['pairs']} == witnessed_pairs
    (base/'RESULTS.json').write_text(json.dumps(dict(cases=results,commands=len(commands),parity=parity,
       metamorphic=['irrelevant entity','actor isolation','deterministic compilation','missing vs unresolved','34/35/36 exact thresholds']),indent=2))
    print(f'machine/workbench: {len(results)} scenarios; {len(commands)} calls; {len(parity)} SDK parity rows; client and refusals passed')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('--output',type=Path);p.add_argument('--sdk-evidence',type=Path);a=p.parse_args()
    if a.output:
        a.output.mkdir(exist_ok=False);run(a.executable.resolve(),a.output.resolve(),a.sdk_evidence)
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-workbench-') as temp:run(a.executable.resolve(),Path(temp),a.sdk_evidence)
