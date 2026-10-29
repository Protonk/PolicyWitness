"""Historical tree extraction and frozen B1 paper evaluation; no live tests."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
COMMANDS = []


def read(rev, path):
    args = ['git', 'show', f'{rev}:{path}']
    COMMANDS.append(args)
    return subprocess.check_output(args, cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def definitions(text):
    return {n.name for n in ast.walk(ast.parse(text)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def worker_graph(rev):
    data = json.loads(read(rev, 'docs/architecture.json'))
    return next(g for g in data['graphs'] if g['id'] == 'worker_capabilities')


def main():
    dataset = (OUT / 'heldback-cases.json').read_bytes()
    assert digest(dataset) == '6c68e4618806d0d47000a10c0ea5be39ac564d1159c4497190153425a78c2cb4'
    cases = json.loads(dataset)['cases']
    result = dict(design='B1', equipment_revision=2, initial_equipment_commit='3e08737',
                  freeze_commit='db75edf', prediction_commit='152f984',
                  dataset_sha256=digest(dataset), live_execution=False, file_hashes_verified=0, cases=[])
    for case in cases:
        ident = case['id']
        records = []
        for snap in case['snapshots']:
            rev = snap['revision']
            file_records = []
            for key in ('files', 'sources', 'check_file', 'source', 'file', 'worker_doc'):
                val = snap.get(key, [])
                file_records.extend(val if isinstance(val, list) else [val])
            hashes = {}
            for file in file_records:
                data = read(rev, file['path'])
                hashes[file['path']] = digest(data)
                assert digest(data) == file['sha256'] and len(data) == file['bytes'], (ident,rev,file['path'])
                result['file_hashes_verified'] += 1
            record = dict(revision=rev, verified_hashes=hashes)
            if ident == 'H01':
                manifest = json.loads(read(rev,'docs/build.json'))
                refs=[]
                def visit(node):
                    if isinstance(node,dict):
                        if node.get('symbol') == 'test_records_are_bounded_redacted_and_complete':
                            refs.append(node)
                        for value in node.values(): visit(value)
                    elif isinstance(node,list):
                        for value in node: visit(value)
                visit(manifest)
                assert refs and snap['citation'][0] in refs
                text=read(rev,snap['check_file']['path']).decode()
                present=refs[0]['symbol'] in definitions(text)
                assert present == snap['definition_present']
                record.update(definition_present=present,result='referent-present' if present else 'referent-missing',
                              reason='Python definition for existing manifest check citation')
            elif ident == 'H02':
                baseline={p['path']:p['sha256'] for p in case['snapshots'][0]['files']}
                changed=[p for p,h in hashes.items() if h != baseline[p]]
                worker=read(rev,'controller/tools/pw_probe_runner/pw_probe_runner.c').decode()
                record.update(changed=changed,same_named_referent='wait_for_proceed' in worker,
                              result='review-required' if changed else 'represented-inputs-current',
                              reason='changed represented input' if changed else 'equal represented inputs; hypothetical baseline review',
                              historical_only_disposition_supplied=False)
            elif ident == 'H03':
                text=read(rev,'docs/ARCHITECTURE.md').decode()
                start=text.index('Known gap. The observer receiver,')
                prose=text[start:text.index('\n\n',start)]
                assert digest(prose.encode()) == snap['prose_sha256']
                # The paragraph verifies the curator's evidence excerpt. B1's
                # actual selected claim input is the whole file, not this parser.
                baseline=read(case['snapshots'][0]['revision'],'docs/ARCHITECTURE.md')
                changed=digest(text.encode()) != digest(baseline)
                record.update(prose_sha256=digest(prose.encode()),claim_selector='whole file docs/ARCHITECTURE.md',
                              claim_sha256=digest(text.encode()),baseline_claim_sha256=digest(baseline),
                              code_inputs_changed=hashes != records[0]['verified_hashes'] if records else False,
                              result='review-required' if changed else 'unreviewed', support='unresolved in both trees',
                              reason='registered prose changed; no support approval' if changed else 'baseline unchanged; no support approval')
            elif ident == 'H04':
                rows={e['id']:e for e in worker_graph(rev)['edges']}
                contrast_ids=sorted(set(rows) & {'W50','W53'})
                assert contrast_ids == sorted(e['id'] for e in snap['edges'])
                observed=[]
                for e in snap['edges']:
                    assert rows[e['id']] == e
                    present=all(r['symbol'] in read(rev,r['path']).decode() for r in e['sources']+e['checks'])
                    assert present
                    observed.append(dict(id=e['id'],label=e['label'],pointer_presence=True))
                record.update(edges=observed,contrast_ids=contrast_ids,w50_present='W50' in rows,
                              result='semantic-support-excluded',reason='same existing places do not establish object relation')
            elif ident == 'H05':
                text=read(rev,snap['file']['path']).decode()
                assert 'test_records_are_bounded_redacted_and_complete' in definitions(text)
                assert snap['comment_and_assertion'] in text
                record.update(definition_present=True,excerpt=snap['comment_and_assertion'],
                              result='semantic-support-excluded',reason='assertion adequacy requires review; definition presence is insufficient')
            elif ident == 'H06':
                worker=read(rev,'docs/WORKER.md').decode()
                lines=[line for line in worker.splitlines() if 'privacy consent' in line]
                assert lines == snap['worker_privacy_lines']
                record.update(privacy_lines=lines,result='unregistered',reason='no registered completeness relationship')
            records.append(record)
        result['cases'].append(dict(id=ident,observations=records))
    result['commands']=COMMANDS
    (OUT/'heldback-results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(cases=len(result['cases']),files_verified=result['file_hashes_verified'],
                         evaluations=sum(len(c['observations']) for c in result['cases']))))


if __name__ == '__main__':
    main()
