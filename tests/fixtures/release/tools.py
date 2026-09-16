"""Independent command stand-ins: no Apple requests, signing, or PW execution."""
import json
from pathlib import Path
import zipfile

ID = '11111111-2222-3333-4444-555555555555'


class Tools:
    def __init__(self, mode, receipts):
        self.mode, self.receipts = mode, receipts
        self.calls = []

    def __call__(self, out, argv, *, timeout, env=None, cwd=None):
        argv = list(map(str, argv))
        self.calls.append(argv)
        with self.receipts.open('a') as stream:
            stream.write(json.dumps(dict(argv=argv, timeout=timeout, app=(env or {}).get('PW_APP_DIR'))) + '\n')
        out.mkdir(parents=True)
        stdout, stderr = out / 'stdout', out / 'stderr'
        stdout.write_bytes(b'')
        stderr.write_bytes(b'')
        if argv[1:3] == ['notarytool', 'submit']:
            stdout.write_text(json.dumps(dict(id=ID, message='Uploaded', extra='unfamiliar but harmless')))
            if self.mode == 'agreement':
                stderr.write_bytes(b'An agreement must be signed.\n')
                raise RuntimeError('controlled nonzero submit exit')
            if self.mode == 'unknown_submit':
                stdout.write_bytes(b'<html>service response changed</html>')
            return
        if argv[1:3] == ['notarytool', 'wait']:
            value = dict(id=ID, status='Accepted', extra={'new': True})
            if self.mode == 'pending':
                value['status'] = 'In Progress'
            elif self.mode == 'rejected':
                value['status'] = 'Invalid'
            elif self.mode == 'unknown_status':
                value['status'] = 'Maybe'
            elif self.mode == 'wrong_id':
                value['id'] = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
            stdout.write_text(json.dumps(value))
            if self.mode == 'ambiguous_response':
                stdout.write_text('{"id":"' + ID + '","status":"Invalid","status":"Accepted"}')
            if self.mode == 'wait_timeout':
                stderr.write_bytes(b'waiting did not complete\n')
                raise RuntimeError('controlled local timeout')
            if self.mode == 'changed_archive':
                # The only original fixture ZIP; retained submitted.zip stays intact.
                (self.receipts.parent / 'original.zip').write_bytes(b'changed')
            return
        if argv[0] == '/usr/bin/ditto':
            with zipfile.ZipFile(argv[3]) as archive:
                archive.extractall(argv[4])
            # zipfile doesn't restore executable mode; this is fake extraction
            # equipment, independent of the production ditto invocation.
            for binary in Path(argv[4]).glob('PolicyWitness.app/**/MacOS/*'):
                binary.chmod(0o755)
            return
        if argv[1:3] == ['stapler', 'validate']:
            if self.mode == 'missing_staple':
                raise RuntimeError('controlled absent ticket')
            return
        if argv[0] == '/usr/sbin/spctl':
            return
        if argv[0] != 'bash':
            raise AssertionError(f'unexpected release command: {argv}')
        app = Path(env['PW_APP_DIR'])
        if not str(app).startswith('/private/tmp/pw-release-'):
            raise AssertionError('execution used a local fallback app')
        if 'PW_BIN' in env or 'PW_TEST_RUNNER_MODE' in env:
            raise AssertionError('inherited configuration reached the test command')
        if self.mode == 'xpc_failure':
            stderr.write_text('controlled XPC failure')
            raise RuntimeError('controlled case failure')
        output = Path(env['PW_TEST_OUT_DIR'])
        output.mkdir()
        cases = ['smoke/specimen_file_read_deny', 'witness_contract/happy_path_baseline']
        summary = dict(ok=True, configuration={'app_dir': str(app)},
            completion=dict(selected=2, completed=2, skipped=0, unrun=0),
            case_results=[dict(id=case, status='pass') for case in cases])
        if self.mode == 'skipped':
            summary['completion'].update(completed=1, skipped=1)
        (output / 'run.json').write_text(json.dumps(summary))
        for case, leaf in zip(cases, ('policy_witness.run.stdout.json', 'run.json')):
            path = output / 'suites' / case / 'artifacts' / leaf
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'data': {'runner_provenance': {
                'runner_kind': 'byoxpc' if self.mode == 'wrong_runner' else 'standard'}}}))
        if self.mode == 'mutated_app':
            (app / 'Contents/Info.plist').write_bytes(b'modified during testing')
