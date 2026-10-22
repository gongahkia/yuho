"""Standard-library only client. Run outside the checkout; never invokes a shell.
Usage: python3 client.py /absolute/yuho /path/to/language-workbench NEW_OUTPUT
The output directory must not exist. Copied sources and both executions are kept.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

VERSION = 'yuho.machine-request/v0.1-experimental'


def call(binary, cwd, kind, operation, path, **fields):
    request = dict(format=VERSION, input_kind=kind, operation=operation, path=str(path), **fields)
    proc = subprocess.run([str(binary), 'machine', '-'], input=json.dumps(request).encode(),
                          cwd=cwd, capture_output=True, timeout=90)
    response = json.loads(proc.stdout)
    assert response['success'] == (proc.returncode == 0), response
    assert not proc.stderr, proc.stderr.decode()
    with (cwd / 'commands.jsonl').open('a') as log:
        log.write(json.dumps(dict(command=[str(binary), 'machine', '-'], request=request,
                                  cwd=str(cwd), exit=proc.returncode, response=response)) + '\n')
    return response


def main(binary, source, out):
    binary, source, out = binary.resolve(), source.resolve(), out.resolve()
    out.mkdir(exist_ok=False)
    project = out / 'project'
    shutil.copytree(source / '06-composition', project)
    check = call(binary, out, 'composition-yh', 'check', project / 'true.project.yh')
    assert check['success'] and check['effects']['evaluation'] == 'none'
    inspection = call(binary, out, 'native-yh', 'inspect', project / 'relationship.yh',
                      scenario=str(project / 'true.yh'))
    assert inspection['success'] and not inspection['payload']['evaluated']
    runs = []
    for name in ['initial', 'revised']:
        run = call(binary, out, 'composition-yh', 'run', project / 'true.project.yh', output=str(out / name))
        assert run['success'], run
        folder = out / name
        report = json.loads((folder / 'report.json').read_text())
        projection = json.loads((folder / 'projection.json').read_text())
        artifact = json.loads((folder / 'artifact.json').read_text())
        binding = artifact['computedBinding']
        # Machine-readable navigation is qualified by component; never join origins by equal strings.
        navigation = projection['computedNavigation']
        assert navigation and binding['computedRationale']
        assert report['computedGeneratedOrigin'] == 'generated_computed_input_bridge'
        source_map = json.loads((folder / 'source-map.json').read_text())
        refs = [a for obj in source_map['source']['objects'] for a in obj['original_line_anchors']]
        assert refs and (folder / 'view.svg').read_text().startswith('<svg')
        # Recover exact retained source text through SourceRef, using UTF-8 byte spans.
        sources = {x['sourceId']: x for x in artifact['computedTypedSource']['typedOriginalSources']}
        excerpts = []
        for ref in refs:
            anchor = ref.get('referenceSpan')
            if anchor:
                text = sources[ref['referenceSource']]['sourceText'].encode()
                excerpts.append(text[anchor['start']:anchor['end']].decode())
        assert excerpts
        runs.append(dict(execution=report['computedExecutionId'], snapshot=binding['computedSourceSnapshot'],
                         observation=report['computedOriginalObservation'], mapping=report['computedMappedClassification'],
                         navigation=navigation, excerpts=excerpts, projection=str(folder / 'projection.json')))
        if name == 'initial':
            text = (project / 'true.yh').read_text()
            (project / 'true.yh').write_text(text.replace('as proved', 'as not_proved'))
            stale = call(binary, out, 'composition-yh', 'check', project / 'true.project.yh',
                         against=str(folder / 'artifact.json'))
            assert not stale['success'] and stale['diagnostics'][0]['code'] == 'SFCSTALE'
    assert runs[0]['snapshot'] != runs[1]['snapshot']
    assert runs[0]['observation']['typedObservedStatus'] == 'satisfied'
    assert runs[1]['observation']['typedObservedStatus'] == 'not_satisfied'
    replay = call(binary, out, 'computed-input-json', 'replay', out / 'initial/artifact.json', output=str(out / 'replay'))
    assert replay['success'] and replay['effects']['source_authority'] == 'embedded_artifact'
    for filename in ['artifact.json','report.json','projection.json','view-bindings.json','view.svg','source-map.json']:
        assert (out / 'initial' / filename).read_bytes() == (out / 'replay' / filename).read_bytes(), filename
    bad = call(binary, out, 'composition-yh', 'check', project / 'unsupported.project.yh')
    assert not bad['success']
    (out / 'inspection.json').write_text(json.dumps(inspection, indent=2))
    (out / 'inspection-records.json').write_text(json.dumps(runs, indent=2))
    (out / 'RESULT.json').write_text(json.dumps(dict(status='passed', runs=2, replay='byte-identical',
        source_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in project.iterdir()}), indent=2))
    print('client: check, inspection, two fresh executions, stale refusal, original source recovery, complete navigation, SVG, frozen replay passed')


if __name__ == '__main__':
    main(*map(Path, sys.argv[1:]))
