"""Actual CLI regressions for no-replace exports and native graph v0.2.

All probes, source copies, fault shims and generated artifacts are external.
Linux LD_PRELOAD injection affects only test children, never production behavior.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FILES = {'artifact.json', 'report.json', 'projection.json', 'view-bindings.json',
         'view.json', 'view.xml', 'view.svg', 'source-map.json'}
NS = {'s': 'http://www.w3.org/2000/svg', 'g': 'urn:yuho:semantic-graph:v0.2'}
SHIM = r'''
#define _GNU_SOURCE
#include <dlfcn.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int mode(const char *s) {const char *m=getenv("YUHO_TEST_FAULT");return m && !strcmp(m,s);}
static void record(const char *s) {
 const char *p=getenv("YUHO_TEST_LOG");if(!p)return;
 int fd=open(p,O_CREAT|O_WRONLY|O_APPEND,0600);if(fd<0)return;
 ssize_t (*realwrite)(int,const void*,size_t)=dlsym(RTLD_NEXT,"write");
 realwrite(fd,s,strlen(s));close(fd);
}
ssize_t write(int fd,const void *buf,size_t count) {
 ssize_t (*realwrite)(int,const void*,size_t)=dlsym(RTLD_NEXT,"write");
 char proc[80],path[8192];snprintf(proc,sizeof proc,"/proc/self/fd/%d",fd);
 ssize_t n=readlink(proc,path,sizeof(path)-1);if(n>=0)path[n]=0;
 if(n>=0 && mode("stage") && strstr(path,"/.yuho-compose-") && strstr(path,"/report.json")) {
  char *last=strrchr(path,'/');strcpy(last+1,"artifact.json");struct stat st;
  if(!stat(path,&st) && st.st_size>0)record("complete artifact written before injected report failure\n");
  errno=EIO;return -1;
 }
 return realwrite(fd,buf,count);
}
char *mkdtemp(char *pattern) {
 char *(*realtemp)(char*)=dlsym(RTLD_NEXT,"mkdtemp");
 if(mode("parent") && strstr(pattern,".yuho-compose-")){record("parent access denied\n");errno=EACCES;return NULL;}
 return realtemp(pattern);
}
int renameat2(int oldfd,const char *old,int newfd,const char *new,unsigned flags) {
 int (*realrename)(int,const char*,int,const char*,unsigned)=dlsym(RTLD_NEXT,"renameat2");
 if(strstr(old,".yuho-compose-")) {
  if(mode("publish")){record("injected publication failure\n");errno=EIO;return -1;}
  if(mode("race")) {
   mkdir(new,0700);char path[8192];snprintf(path,sizeof path,"%s/sentinel",new);
   int fd=open(path,O_CREAT|O_EXCL|O_WRONLY,0600);
   if(fd>=0){ssize_t (*w)(int,const void*,size_t)=dlsym(RTLD_NEXT,"write");w(fd,"unrelated winner",16);close(fd);}
   record("competing destination created immediately before rename\n");
  }
 }
 return realrename(oldfd,old,newfd,new,flags);
}
'''


def run(binary, base, project=None):
    base.mkdir(parents=True, exist_ok=False)
    commands = []

    def call(label, args, expected=0, fault=None, limit=False, machine=False):
        env = os.environ.copy()
        if fault:
            env.update(LD_PRELOAD=str(base/'fault.so'), YUHO_TEST_FAULT=fault,
                       YUHO_TEST_LOG=str(base/'fault.log'))
        def limited():
            signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024, 1024))
        p = subprocess.run([str(binary), *map(str, args)], cwd=base, capture_output=True,
                           env=env, preexec_fn=limited if limit else None, timeout=90)
        commands.append(dict(label=label, command=[str(binary), *map(str,args)],
                             cwd=str(base), exit=p.returncode, fault=fault,
                             stdout=p.stdout.decode(), stderr=p.stderr.decode()))
        (base/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        assert p.returncode == expected, commands[-1]
        if machine:
            value = json.loads(p.stdout)
            assert value['success'] == (expected == 0) and not p.stderr, commands[-1]
            if expected:
                assert value['exports'] == [] and value['payload'] is None
                assert value['diagnostics'] and '"status":"evaluated"' not in p.stdout.decode()
        elif expected:
            assert not p.stdout and json.loads(p.stderr)['code'] == 'SFC006', commands[-1]
        return p

    (base/'fault.c').write_text(SHIM)
    subprocess.run(['cc', '-shared', '-fPIC', '-O2', str(base/'fault.c'),
                    '-o', str(base/'fault.so'), '-ldl'], check=True, capture_output=True)
    projects = base/'projects'
    shutil.copytree(ROOT/'examples/source-composition', projects)
    project = Path(project).resolve() if project else projects/'proof/true.project.yh'
    source_hashes = {p: p.read_bytes() for p in projects.rglob('*') if p.is_file()}
    outputs = base/'outputs'
    outputs.mkdir()
    unrelated = outputs/'.yuho-compose-unrelated'
    unrelated.mkdir()
    (unrelated/'sentinel').write_text('not owned by export')

    def export(label, destination, expected=0, replay=None, machine=False, **kwargs):
        if machine:
            request = dict(format='yuho.machine-request/v0.1-experimental',
                input_kind='computed-input-json' if replay else 'composition-yh',
                operation='replay' if replay else 'run', path=str(replay or project),
                output=str(destination))
            request_path = base/(label+'.request.json')
            request_path.write_text(json.dumps(request))
            args = ['machine', request_path]
        else:
            args = ['compose', 'replay' if replay else 'run', replay or project,
                    '--output', destination]
        result = call(label, args, expected, machine=machine, **kwargs)
        assert set(outputs.glob('.yuho-compose-*')) == {unrelated}, label
        assert (unrelated/'sentinel').read_text() == 'not owned by export'
        return result

    success = outputs/'success'
    export('success', success)
    assert {p.name for p in success.iterdir()} == FILES
    saved = {name: (success/name).read_bytes() for name in FILES}
    for machine in [False, True]:
        prefix = 'machine-' if machine else 'cli-'
        for label, path in [('missing-parent', outputs/'absent'/'result'),
                            ('existing-directory', success)]:
            export(prefix+label, path, 1, machine=machine)
        ordinary = outputs/(prefix+'ordinary')
        ordinary.write_text('unrelated file')
        export(prefix+'existing-file', ordinary, 1, machine=machine)
        assert ordinary.read_text() == 'unrelated file'
        link = outputs/(prefix+'link')
        link.symlink_to(outputs/'missing-target')
        export(prefix+'existing-dangling-link', link, 1, machine=machine)
        assert link.is_symlink() and not link.exists()
        existing_link = outputs/(prefix+'existing-link')
        existing_link.symlink_to(ordinary)
        export(prefix+'existing-symlink', existing_link, 1, machine=machine)
        assert existing_link.is_symlink() and ordinary.read_text() == 'unrelated file'
        unicode_output = outputs/(prefix+'export é猫')
        export(prefix+'unicode-destination', unicode_output, machine=machine)
        assert {name: (unicode_output/name).read_bytes() for name in FILES} == saved
        parentlink = base/(prefix+'parent-link')
        parentlink.symlink_to(outputs, target_is_directory=True)
        export(prefix+'unsafe-parent-link', parentlink/'new', 1, machine=machine)
        parent = outputs/(prefix+'unwritable')
        parent.mkdir()
        parent.chmod(0o500)
        try:
            export(prefix+'unwritable-parent', parent/'new', 1, machine=machine,
                   fault='parent' if os.geteuid() == 0 else None)
        finally:
            parent.chmod(0o700)
        for replay in [None, success/'artifact.json']:
            suffix = '-replay' if replay else '-run'
            for fault in ['stage', 'publish', 'parent', 'race']:
                dest = outputs/(prefix+fault+suffix)
                export(prefix+fault+suffix, dest, 1, replay=replay, machine=machine, fault=fault)
                if fault == 'race':
                    assert {p.name for p in dest.iterdir()} == {'sentinel'}
                    assert (dest/'sentinel').read_text() == 'unrelated winner'
                else:
                    assert not dest.exists()
            dest = outputs/(prefix+'file-limit'+suffix)
            export(prefix+'file-limit'+suffix, dest, 1, replay=replay, machine=machine, limit=True)
            assert not dest.exists()
            dest = outputs/(prefix+'replay' if replay else prefix+'fresh')
            export(prefix+'immutable'+suffix, dest, replay=replay, machine=machine)
            assert {name: (dest/name).read_bytes() for name in FILES} == saved
    assert 'complete artifact written before injected report failure' in (base/'fault.log').read_text()
    assert source_hashes == {p: p.read_bytes() for p in source_hashes}
    assert saved == {name: (success/name).read_bytes() for name in FILES}
    print(f'Atomic export: {len(commands)} CLI/machine calls; staged-write, final-publication and no-replace race controls passed')
    native_checks(binary, base/'native')
    return commands


def geometry(svg):
    root = ET.parse(svg).getroot()
    width, height = float(root.get('width')), float(root.get('height'))
    ids = [n.get('id') for n in root.iter() if n.get('id')]
    assert len(ids) == len(set(ids)), 'DOM identities must be injective'
    nodes = root.findall('.//s:g[@data-semantic-id]', NS)
    for n in nodes:
        x,y,w,h = [float(n.get('data-'+a)) for a in ('x','y','width','height')]
        assert 0 <= x and 0 <= y and x+w <= width and y+h <= height
        for text in n.findall('s:text', NS):
            value = ''.join(text.itertext())
            cells = sum(2 if ord(c) >= 0x1100 else 1 for c in value)
            tx,ty = float(text.get('x')),float(text.get('y'))
            assert tx >= x+10 and tx+8*cells <= x+w-10, (n.get('data-semantic-id'),value)
            assert y+12 <= ty <= y+h-10
    return dict(width=width,height=height,nodes=len(nodes))


def native_checks(binary, base):
    """Compare graph observations with hand cases and raw backend report rows."""
    base.mkdir()
    work = base/'workbench'
    shutil.copytree(ROOT/'examples/language-workbench', work)
    records = []
    def command(label, args):
        cmd = [str(binary), *map(str, args)]
        p = subprocess.run(cmd, cwd=base, capture_output=True, timeout=60)
        records.append(dict(label=label,command=cmd,exit=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode()))
        (base/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
        assert p.returncode == 0, records[-1]
        return p.stdout
    def diagram(label, path, scenario=None, view='trace'):
        args = [path] + (['--scenario',scenario] if scenario else [])
        raw = json.loads(command(label+'-run',['run',*args]))
        (base/(label+'-run.json')).write_text(json.dumps(raw,indent=2)+'\n')
        files = {}
        for fmt in ['json','xml','svg']:
            out = base/(label+'.'+fmt)
            command(label+'-'+fmt,['diagram',*args,'--view',view,'--format',fmt,'--output',out])
            files[fmt] = out
        graph = json.loads(files['json'].read_bytes())
        assert graph['format'] == 'yuho.semantic-graph/v0.2'
        ids = [n['id'] for n in graph['nodes']]
        assert len(ids) == len(set(ids))
        assert all(e['from'] in ids and e['to'] in ids for e in graph['edges'])
        xml = ET.parse(files['xml']).getroot()
        svg = ET.parse(files['svg']).getroot()
        xml_nodes = {n.get('id'):n for n in xml.findall('g:nodes/g:node',NS)}
        svg_nodes = {n.get('data-semantic-id'):n for n in svg.findall('.//s:g[@data-semantic-id]',NS)}
        assert set(xml_nodes) == set(svg_nodes) == set(ids)
        for n in graph['nodes']:
            x = xml_nodes[n['id']]
            assert x.get('label') == n['label'] and x.get('status') == n.get('status')
            for key, value in n.get('observation',{}).items():
                assert x.get(key.replace('_','-')) == value
                assert svg_nodes[n['id']].get(key.replace('_','-')) == value
        xml_edges = [(e.get('from'),e.get('to'),e.get('kind'),e.get('label')) for e in xml.findall('g:edges/g:edge',NS)]
        assert xml_edges == [(e['from'],e['to'],e['kind'],e['label']) for e in graph['edges']]
        geometry(files['svg'])
        repeated = base/(label+'-repeat.svg')
        command(label+'-repeat',['diagram',*args,'--view',view,'--format','svg','--output',repeated])
        assert files['svg'].read_bytes() == repeated.read_bytes()
        return raw, graph
    matrix = [
        ('ordinary-satisfied','proved','not_proved','not_proved','satisfied', 'not_satisfied'),
        ('ordinary-negative','not_proved','proved','proved','not_satisfied',None),
        ('ordinary-unresolved','unresolved(not_determined)','proved','proved','unresolved',None),
        ('guard-defeats','proved','proved','proved','not_satisfied','satisfied'),
        ('guard-negative','proved','not_proved','proved','satisfied','not_satisfied'),
        ('guard-unresolved','proved','unresolved(not_determined)','proved','unresolved','unresolved')]
    proof = work/'01-requirements/law.yh'
    for label, main, danger, rescue, final, guard_value in matrix:
        scenario = base/(label+'.yhs')
        scenario.write_text('scenario S00 for FictionalRestrictedAreaEntry-v0.1 {\n'
            +f'f:entry = {main};\nf:no-authorization = proved;\nf:knowledge = proved;\n'
            +f'f:immediate-danger = {danger};\nf:rescue-purpose = {rescue};\n'+'}\n')
        raw,g = diagram(label,proof,scenario)
        assert raw['status'] == final
        rules = {r['id']:r for r in raw['rules']}
        nodes = {n['id']:n for n in g['nodes']}
        assert nodes['rule:o:entry']['observation']['technical_value'] == rules['r:entry']['status']
        exception = nodes['rule:x:emergency-rescue']
        guard = next(n for n in g['nodes'] if n['kind']=='guard')
        if guard_value is None:
            assert 'r:rescue' not in rules
            assert exception.get('status') is None and guard.get('status') is None
            assert guard['observation']['evaluation'] == exception['observation']['evaluation'] == 'not_evaluated'
            assert 'technical_value' not in guard['observation']
            assert raw['rules'][0]['branches'][0]['reason'] in guard['observation']['skip_reason']
        else:
            entry = rules['r:entry']['branches'][0]['exceptions'][0]
            assert entry['guard_status'] == guard_value == guard['observation']['technical_value']
            assert guard['observation']['evaluation'] == 'evaluated'
    pdir = work/'04-presumptions'
    (pdir/'skip-input.yh').write_text((pdir/'input-active.yh').read_text().replace('f:entry = proved;', 'f:entry = unresolved(not_determined);'))
    (pdir/'skip.yh').write_text((pdir/'active.yh').read_text().replace('input-active.yh','skip-input.yh'))
    for label in ['active','rebutted','dominance','skip']:
        raw,g = diagram('presumption-'+label,pdir/(label+'.yh'))
        for derivation in raw['presumption_derivations']:
            target=derivation['target_leaf_id']
            nodes={n['id']:n for n in g['nodes']}
            assert nodes['direct-input:'+target]['status'] == derivation['target_direct_satisfaction']
            assert nodes['effective-input:'+target]['status'] == derivation['target_effective_satisfaction']
            assert nodes['presumption:'+derivation['presumption_id']]['status'] == derivation['state']
            if label=='skip':
                assert derivation['state']=='active'
                guards=[n for n in g['nodes'] if n['kind']=='guard']
                assert guards and all(n['observation']['evaluation']=='not_evaluated' and 'status' not in n for n in guards)
    (pdir/'unicode.yh').write_text((pdir/'active.yh').read_text().replace('note \"', 'note \"é猫🙂 ' + 'UnbrokenLongLabel'*12 + ' '))
    _,unicode_graph=diagram('unicode-long-context',pdir/'unicode.yh')
    assert any('é猫🙂' in n['label'] for n in unicode_graph['nodes'])
    for value,expected in [(35,'not_satisfied'),(36,'satisfied')]:
        raw,g=diagram('numeric-'+str(value),work/'03-typed/law.yh',work/f'03-typed/{value}.yhs')
        scalars=[n for n in g['nodes'] if n['kind']=='scalar']
        assert any('supplied value: '+str(value) in n['label'] for n in scalars)
        assert raw['propositions'][0]['status']==expected
        assert any(e['kind']=='operand' for e in g['edges'])
    typed_dir=work/'03-typed'
    collision=(typed_dir/'law.yh').read_text().replace('q:permission','q:a-b').replace('q:threshold','q:a:b')
    (typed_dir/'collision.yh').write_text(collision)
    _,identity_graph=diagram('identity-collision',typed_dir/'collision.yh',typed_dir/'36.yhs')
    assert {'finite-requirement:q:a-b','finite-requirement:q:a:b'} <= {n['id'] for n in identity_graph['nodes']}
    lines=collision.splitlines()
    a=next(i for i,line in enumerate(lines) if 'requirement q:a-b =' in line)
    b=next(i for i,line in enumerate(lines) if 'requirement q:a:b =' in line)
    lines[a],lines[b]=lines[b],lines[a]
    (typed_dir/'reordered.yh').write_text('\n'.join(lines)+'\n')
    diagram('identity-reordered',typed_dir/'reordered.yh',typed_dir/'36.yhs')
    assert (base/'identity-collision.svg').read_bytes()==(base/'identity-reordered.svg').read_bytes()
    raw,g=diagram('two-scopes',work/'02-definitions/case.yh',view='case')
    for allegation in raw['allegations']:
        for result in allegation['result']['propositions']:
            node=next(n for n in g['nodes'] if n.get('boundary')==allegation['id'] and n['label'].startswith(result['id']+'\n'))
            assert node['status']==result['status']
    (base/'summary.json').write_text(json.dumps(dict(cases=16,calls=len(records),graph_version='v0.2',reports_match=True),indent=2)+'\n')
    print(f'Native diagrams: {len(records)} actual CLI calls; evaluated/skipped matrix, global routes, scalar operands, scope and JSON/XML/SVG parity passed')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--project', type=Path, help='optional external independent reviewer project')
    a = p.parse_args()
    if a.output:
        run(a.binary.resolve(), a.output, a.project)
    else:
        with tempfile.TemporaryDirectory(prefix='yuho-tranche04-') as parent:
            run(a.binary.resolve(), Path(parent)/'probes', a.project)
