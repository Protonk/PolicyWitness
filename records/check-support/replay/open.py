"""B1 open replay: read historical git trees; write compact facts only here."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
COMMANDS = []


def git(*args, optional=False):
    COMMANDS.append(['git', *args])
    r = subprocess.run(['git', *args], cwd=ROOT, capture_output=True)
    if r.returncode:
        if optional:
            return None
        raise RuntimeError(r.stderr.decode())
    return r.stdout


def show(rev, path, optional=False):
    return git('show', f'{rev}:{path}', optional=optional)


def identity(rev):
    text = show(rev, 'controller/tools/pw_probe_runner/pw_probe_runner_abi.h').decode()
    return re.search(r'PW_WORKER_ABI_IDENTITY_HEX "([0-9a-f]{64})"', text)[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def observation(rev):
    raw = show(rev, 'docs/worker-launch-observation.json', optional=True)
    if raw is None:
        return dict(revision=rev, result='evidence-missing', reason='registered observation receipt absent',
                    current_worker_identity=identity(rev))
    receipt = json.loads(raw)
    compared = {p:dict(receipt=h, current=digest(show(rev, p))) for p,h in receipt['source_files'].items()}
    changed = [p for p,h in compared.items() if h['receipt'] != h['current']]
    worker = identity(rev)
    stale = worker != receipt['worker_source_identity']
    return dict(revision=rev, result='review-required' if changed or stale else 'represented-inputs-current',
                reason='changed represented inputs' if changed or stale else 'equal represented inputs; supplied adoption review',
                source_files=compared, changed=changed, worker_identity_changed=stale,
                receipt_worker_identity=receipt['worker_source_identity'], current_worker_identity=worker,
                receipt_sha256=digest(raw))


def graph_items(rev):
    manifest = json.loads(show(rev, 'docs/architecture.json'))
    graph = next(g for g in manifest['graphs'] if g['id'] == 'worker_capabilities')
    return {r['id']:r for r in graph['nodes'] + graph['edges']}


def sources(rev, row):
    return [dict(**r, symbol_present=r['symbol'] in show(rev, r['path']).decode()) for r in row['sources']]


def main():
    result = dict(design='B1', prediction_commit='689cb49', historical_facts_only=True,
                  supplied_annotations='replays.md; explicit hypothetical adoption review at69c7dfe', cases=[], churn=[])
    result['cases'] += [dict(id='A', **observation(r)) for r in ('51487f7','69c7dfe','f468200')]
    base = show('69c7dfe','docs/WORKER.md')
    for rev in ('69c7dfe','11fddc4'):
        text = show(rev, 'docs/WORKER.md')
        result['cases'].append(dict(id='P-change', revision=rev, baseline_claim_hash=digest(base), claim_hash=digest(text),
            result='represented-inputs-current' if text == base else 'review-required',
            reason='registered whole claim-document bytes unchanged' if text == base else 'registered whole claim-document bytes changed'))
    for rev in ('46fe43e','b410ac3','d46ccd6','99cf137'):
        excerpts = {}
        for p in ('Makefile','docs/BUILD.md','tests/lib/checkout_lock.py','tests/lib/checkout_lock.sh'):
            data = show(rev,p,optional=True)
            if data is not None:
                lines=data.decode().splitlines()
                chosen={i for i,line in enumerate(lines) if '/usr/bin/python3' in line or ('shim' in line and 'Python' in line)}
                excerpts[p]=[dict(line=i+1,text=lines[i]) for j in sorted(chosen) for i in range(max(0,j-1),min(len(lines),j+2))]
        result['cases'].append(dict(id='B', revision=rev, result='excluded', reason='no registered subject relationship; unconnected prose semantics',excerpts=excerpts))
    for rev in ('51487f7','69c7dfe'):
        rows=graph_items(rev)
        for ident in ('W24','W30'):
            result['cases'].append(dict(id='S9-'+ident, revision=rev, row=rows[ident], sources=sources(rev,rows[ident]),
                result='excluded',reason='wrong versus repaired attribution is semantic; existing pointer does not adjudicate it'))
        result['cases'].append(dict(id='S2',revision=rev,row=rows['s2'], result='unreviewed',
            reason='a located definition does not establish assertion support; classification needs review'))
        result['cases'].append(dict(id='S6',revision=rev,rows=[rows[i] for i in ('s9','s29','s31a','s32','s36b')],
            result='excluded',reason='truth of generated source data is outside identity checking'))
    for rev in ('51487f7','f699758'):
        evidence={}
        for p in ('docs/WORKER.md','docs/limits.json','controller/tools/pw_probe_runner/pw_probe_runner.c'):
            lines=show(rev,p).decode().splitlines()
            selected={i for i,l in enumerate(lines) if 'sysctl' in l or '4096' in l}
            evidence[p]=[dict(line=i+1,text=lines[i]) for j in sorted(selected) for i in range(max(0,j-1),min(len(lines),j+3))]
        result['cases'].append(dict(id='S11',revision=rev,result='excluded',reason='omitted or newly described fact has no supplied registration',excerpts=evidence))
    for rev in ('e04ec96','2b0be8e','16e2f83','146e7d2','cb8a110'):
        before,after=identity(rev+'^'),identity(rev)
        paths=git('diff','--name-only',rev+'^',rev).decode().splitlines()
        result['churn'].append(dict(revision=rev,before=before,after=after,review_required=before!=after,changed_paths=paths))
    result['revision_objects']={r:git('rev-parse',r).decode().strip() for r in sorted({c['revision'] for c in result['cases']+result['churn']})}
    result['commands']=COMMANDS
    (OUT/'open-results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(cases=len(result['cases']), review_events=sum(c['review_required'] for c in result['churn']),
                         A=[(r['revision'],r['result'],len(r.get('changed',[]))) for r in result['cases'] if r['id']=='A'])))


if __name__ == '__main__':
    main()
