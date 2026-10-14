"""Extra queries observe the actual PW worker without changing planner output."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from check_path_queries import ROOT, CONTENTS, path_state, save
sys.path.insert(0, str(ROOT / 'tests/lib'))
import consumer


def probe(step, target, action='open_read', operation='file-read-data'):
    return dict(step_id=step, sandbox_check=dict(operation=operation, filter=dict(kind='path', value=str(target))),
                attempt=dict(kind='file', action=action, target=str(target)))


def main():
    pw, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    workspace = Path(tempfile.mkdtemp(prefix='pw-path-integrated-', dir='/private/tmp'))
    owner = dict(path=str(workspace), creator_pid=os.getpid(), cleanup_retained=True, children_confirmed=True)
    save(workspace / 'owner.json', owner); save(out / 'workspace-owner.json', owner)
    validator_source = pw.parent.parent / 'XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator'
    validator = workspace / 'native-validator'
    shutil.copy2(validator_source, validator)
    wrapper = workspace / 'validator_observer.py'
    shutil.copy2(ROOT / 'tests/fixtures/path_query/validator_observer.py', wrapper); wrapper.chmod(0o755)
    save(out / 'equipment.json', dict(source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        validator_source=str(validator_source), validator_sha256=hashlib.sha256(validator.read_bytes()).hexdigest(),
        copied_validator_equal=validator.read_bytes()==validator_source.read_bytes()))
    observations = []
    try:
        for kind in ('transition', 'create', 'dangling_unlink'):
            case = out / kind; case.mkdir()
            targets = workspace / kind; targets.mkdir()
            receipt_dir = targets / 'receipts'; receipt_dir.mkdir()
            blocked, sibling, anchor = [targets / n for n in ('blocked','sibling','anchor')]
            anchor.write_bytes(CONTENTS)
            if kind == 'transition':
                blocked.write_bytes(CONTENTS); sibling.write_bytes(CONTENTS)
                phases = [
                    [probe('b0',blocked),probe('s0',sibling),probe('ub',blocked,'unlink','file-write-unlink'),probe('us',sibling,'unlink','file-write-unlink')],
                    [probe('b1',blocked),probe('s1',sibling),probe('a1',anchor)],
                    [probe('cb',blocked,'create','file-write-create'),probe('cs',sibling,'create','file-write-create'),probe('a2',anchor)],
                    [probe('b3',blocked),probe('s3',sibling),probe('a3',anchor)]]
                denied_op = 'file-read-data'
            elif kind == 'create':
                phases = [[probe('cb',blocked,'create','file-write-create'),probe('cs',sibling,'create','file-write-create'),probe('a0',anchor)]]
                denied_op = 'file-write-create'
            else:
                blocked.symlink_to(targets / 'missing_b'); sibling.symlink_to(targets / 'missing_s')
                phases = [[probe('ub',blocked,'unlink','file-write-unlink'),probe('us',sibling,'unlink','file-write-unlink'),probe('a0',anchor)]]
                denied_op = 'file-write-unlink'
            queries = [dict(step_id='extra_' + n + '_' + op, operation=operation, filter_type='PATH', filter_value=str(path))
                       for n,path in [('b',blocked),('s',sibling)] for op,operation in [('read','file-read-data'),('create','file-write-create'),('unlink','file-write-unlink')]]
            config = dict(validator=str(validator), receipts=str(receipt_dir), queries=queries)
            save(wrapper.with_suffix('.json'), config); save(case/'observer-config.json', config)
            before = {n:path_state(p) for n,p in [('blocked',blocked),('sibling',sibling)]}
            spec = dict(schema_version=4, specimen_id='path_query_' + kind,
                        policy=dict(format='sbpl',sbpl_source='(version 1) (allow default) (deny ' + denied_op + ' (literal ' + json.dumps(str(blocked)) + '))'),
                        phases=[dict(phase_id='p'+str(i),actions=actions) for i,actions in enumerate(phases)],
                        _test_overrides=dict(validator_executable_path=str(wrapper)))
            request = targets / 'request.json'; save(request,spec); save(case/'specimen.json',spec)
            owner['children_confirmed'] = False
            save(workspace/'owner.json',owner); save(out/'workspace-owner.json',owner)
            command = [str(pw),'run',str(request),'--no-log-capture']
            result = subprocess.run(command,capture_output=True,timeout=40)
            (case/'stdout.json').write_bytes(result.stdout); (case/'stderr.txt').write_bytes(result.stderr)
            save(case/'capture.json',dict(argv=command,returncode=result.returncode))
            envelope = json.loads(result.stdout)
            reply = envelope['data']['runner_result']
            process = reply.get('runner_subprocess') or {}
            owner['children_confirmed'] = process.get('reaped') is True and all(
                (p.get('validator_subprocess') or {}).get('reaped') is True for p in reply['phases'])
            assert owner['children_confirmed'], 'owned PW cleanup uncertain; preserve workspace'
            assert result.returncode == 0 and reply['normalized_outcome']=='ok', reply
            assert consumer.validate(envelope)==[], consumer.validate(envelope)
            receipts = [json.loads(p.read_text()) for p in receipt_dir.glob('*.json')]
            assert len(receipts)==len(phases)
            assert {r['target_pid'] for r in receipts}=={process['pid']}
            assert {r['pid'] for r in receipts}=={p['validator_subprocess']['pid'] for p in reply['phases']}
            shutil.copytree(receipt_dir,case/'observer-receipts')
            row = dict(case=kind, before=before, after={n:path_state(p) for n,p in [('blocked',blocked),('sibling',sibling)]},
                       worker=process, phase_validator_pids=[p['validator_subprocess']['pid'] for p in reply['phases']],
                       steps=reply['steps'])
            if kind=='transition':
                assert blocked.read_bytes()==b'' and sibling.read_bytes()==b''
            elif kind=='create':
                assert not blocked.exists() and sibling.read_bytes()==b''
            else:
                assert blocked.is_symlink() and not os.path.lexists(sibling)
            save(case/'observations.json',row); observations.append(row)
        save(out/'observations.json',observations)
    finally:
        if owner['children_confirmed']:
            shutil.rmtree(workspace)
            owner.update(cleanup_retained=False,absent=not workspace.exists())
        save(out/'workspace-owner.json',owner)
    print('Three actual-worker experiments passed with six separately observed validator collections.')


if __name__=='__main__':
    main()
