"""The specimen dossier against the request that ran and facts read independently.

Every expectation here comes from the request this test wrote, from host tools
it runs itself (`sw_vers`, `uname`), from the app manifest it parses itself and
from hashes it computes itself. Nothing is derived from the envelope under test
except the values being checked. The run-level outcome of each example is
whatever the policy and the plan produce; the dossier is the subject.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
import contract
import build_context
from run_capture import RunCapture
from seam_invocation import SeamCapture

SERVICE_REL = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner'
WORKER_REL = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
VALIDATOR_REL = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator'
UNENTITLED_WORKER_REL = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner-unentitled'
SOURCE = '(version 1)\n(allow default)\n'
TEMP_REQUEST_DIR = Path(tempfile.gettempdir()) / 'policy-witness'


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


# Controller-owned runner selector fields, consumed before XPC delivery
# (`SELECTOR_FIELDS` in controller/src/runner_select.rs).
SELECTOR_FIELDS = ('runner', 'runner_id', 'runner_service', 'required_entitlements', 'runner_mode')


def held_bytes(request):
    """The controller serializes the resolved request once, after stripping the
    runner selector fields: sorted keys, two-space pretty JSON."""
    held = {key: value for key, value in request.items() if key not in SELECTOR_FIELDS}
    return len(json.dumps(held, indent=2, sort_keys=True, ensure_ascii=False).encode())


def host_facts():
    def run(argv):
        return subprocess.run(argv, capture_output=True, text=True, timeout=10, check=True).stdout.strip()
    return {'macos_version': run(['/usr/bin/sw_vers', '-productVersion']),
            'macos_build': run(['/usr/bin/sw_vers', '-buildVersion']),
            'kernel_release': run(['/usr/bin/uname', '-r']), 'arch': run(['/usr/bin/uname', '-m'])}


def manifest_for(app):
    path = app / 'Contents/Resources/Evidence/manifest.json'
    manifest = json.loads(path.read_text())
    entries = {}
    for entry in manifest['entries']:
        assert entry['rel_path'] not in entries, 'duplicate manifest path: ' + entry['rel_path']
        entries[entry['rel_path']] = entry
    return path, entries


def temp_request_files():
    return sorted(p.name for p in TEMP_REQUEST_DIR.iterdir()) if TEMP_REQUEST_DIR.is_dir() else None


class Witness:
    def __init__(self, pw, out, *, byoxpc=None):
        self.pw = Path(pw)
        self.app = self.pw.parents[2]
        self.out = out
        self.byoxpc = byoxpc
        self.manifest_path, self.entries = manifest_for(self.app)
        self.host = host_facts()
        self.records = []
        self.temp_before = temp_request_files()

    def specimen(self, name, *, policy=None, plan=None, overrides=None):
        request = {'contract': build_context.candidate_contract(), 'specimen_id': 'dossier-' + name,
                   'policy': policy if policy is not None else {'format': 'sbpl', 'sbpl_source': SOURCE},
                   'probe_plan': plan if plan is not None else []}
        if self.byoxpc:
            request['runner'] = {'mode': 'byoxpc', 'service': self.byoxpc['service_name']}
        if overrides is not None:
            request['_test_overrides'] = overrides
        return request

    def run(self, name, request, *, cli_args=(), timeout=60, raw=None, controls=None):
        directory = self.out / name
        if raw is not None:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / 'request.raw'
            path.write_bytes(raw)
            result = subprocess.run([str(self.pw), 'run', str(path), *cli_args], capture_output=True, timeout=timeout)
            (directory / 'stdout').write_bytes(result.stdout)
            (directory / 'stderr').write_bytes(result.stderr)
            return result.returncode, json.loads(result.stdout), str(path)
        with (RunCapture(self.pw, directory, request, cli_args=list(cli_args)) if controls is None else
              SeamCapture(self.pw, directory, request, controls=controls, scenario='dossier.' + name,
                          cli_args=list(cli_args))) as capture:
            rc = capture.wait(timeout=timeout)
            envelope = capture.load_json()
        return rc, envelope, str(capture.request_path) if hasattr(capture, 'request_path') else None

    def record(self, name, **facts):
        self.records.append(dict(control=name, **facts))
        (self.out / 'dossier-controls.json').write_text(json.dumps(self.records, indent=2) + '\n')
        print(f'{name}: ok', flush=True)

    # ---- shared assertions --------------------------------------------------

    def common(self, envelope, name):
        errors = consumer.validate(envelope, build_context.candidate_contract())
        assert not errors, (name, errors)
        data = envelope['data']
        specimen = data['specimen']
        assert set(specimen) == {'request_path', 'policy', 'host', 'runner_provenance', 'app_provenance', 'binaries'}, specimen.keys()
        assert specimen['host'] == self.host, (specimen['host'], self.host)
        assert data.get('runner_startup_diagnostics', 'absent') == 'absent' and 'policy_augmentation' not in data, data.keys()
        return specimen

    def app_provenance_present(self, specimen):
        provenance = specimen['app_provenance']
        assert provenance == {'evidence_manifest_path': str(self.manifest_path), 'evidence_verify': None}, provenance

    def builtin_binaries(self, specimen):
        assert specimen['binaries'] == {'service': None, 'worker': None, 'validator': None, 'unentitled_worker': None}, specimen['binaries']
        provenance = specimen['runner_provenance']
        assert provenance['runner_kind'] == 'standard', provenance
        assert provenance['runner_service_name'] == self.entries[SERVICE_REL]['bundle_id'], provenance
        assert provenance['runner_executable_path'] == str(self.app / SERVICE_REL), provenance

    def no_temp_request(self, name):
        after = temp_request_files()
        assert after == self.temp_before, (name, 'a run left files in the temp request directory', self.temp_before, after)

    def delivery(self, data, request, name):
        client = data['runner_client']
        delivery = client['request_delivery']
        assert delivery['error'] is None, (name, delivery)
        assert delivery['bytes_written'] == held_bytes(request), (name, delivery, held_bytes(request))
        assert client['argv'][-3:-1] == ['--request', '-'], (name, client['argv'])

    # ---- examples -----------------------------------------------------------

    def ordinary(self):
        request = self.specimen('ordinary')
        rc, envelope, path = self.run('ordinary', request)
        assert rc == 0 and envelope['result']['normalized_outcome'] == 'finished', envelope['result']
        specimen = self.common(envelope, 'ordinary')
        assert specimen['request_path'] == path, (specimen['request_path'], path)
        augmentation = specimen['policy']['augmentation']
        assert augmentation == {'status': 'not_requested', 'applied': [], 'original_sha256': sha256_text(SOURCE),
                                'applied_sha256': sha256_text(SOURCE), 'error': None}, augmentation
        assert envelope['data']['runner_result']['policy_sha256'] == augmentation['applied_sha256']
        assert envelope['data']['runner_result']['specimen_id'] == request['specimen_id']
        imports = specimen['policy']['imports']
        assert imports['status'] == 'complete' and imports['records'] == [] and imports['cycle'] is None, imports
        assert imports['exceeded'] is None and imports['failure'] is None and len(imports['closure_sha256']) == 64, imports
        self.app_provenance_present(specimen)
        if self.byoxpc:
            self.byoxpc_binaries(specimen)
        else:
            self.builtin_binaries(specimen)
        self.delivery(envelope['data'], request, 'ordinary')
        self.no_temp_request('ordinary')
        assert envelope['data']['policy_check'] is None
        self.record('ordinary', request_path=path, imports=imports, host=specimen['host'])
        return envelope

    def with_imports(self):
        source = '(version 1)\n(import "system.sb")\n(allow default)\n'
        request = self.specimen('imports', policy={'format': 'sbpl', 'sbpl_source': source})
        rc, envelope, _ = self.run('imports', request)
        specimen = self.common(envelope, 'imports')
        imports = specimen['policy']['imports']
        names = [r['name'] for r in imports['records']]
        assert 'system.sb' in names, imports
        system = next(r for r in imports['records'] if r['name'] == 'system.sb')
        assert system['resolved_path'] in ('/System/Library/Sandbox/Profiles/system.sb', '/usr/share/sandbox/system.sb'), system
        assert system['sha256'] == sha256_file(system['resolved_path']), system
        assert imports['status'] in ('complete', 'incomplete'), imports
        assert len(imports['closure_sha256']) == 64
        self.record('imports', status=imports['status'], records=len(imports['records']), run=envelope['result']['normalized_outcome'])

    def import_forms(self):
        """Import spellings through the dossier, beside what the worker's compiler did.

        Evaluating `marker.sb` fails compilation with a diagnostic naming that
        file, so each reply shows whether the worker's compiler evaluated it.
        That is evaluation of the file's content on this system; it does not
        show which files the compiler opened.
        """
        files = self.out / 'import_forms' / 'files'
        files.mkdir(parents=True)
        marker = files / 'marker.sb'
        marker.write_bytes(b'(allow pw-trace-marker-operation)\n')
        computed = '(import (string-append "%s" "/marker.sb"))' % files
        wrapper = files / 'wrapper.sb'
        wrapper.write_text(computed + '\n')
        # name, source after the base, status, recorded file, evaluated by the worker's compiler
        rows = [
            ('no_import', '', 'complete', None, False),
            ('literal', '(import "%s")' % marker, 'complete', marker, True),
            ('newline_between', '(import\n"%s")' % marker, 'complete', marker, True),
            ('comment_between', '(import ; note\n "%s")' % marker, 'complete', marker, True),
            ('trailing_comment', '(import "%s" ; note\n)' % marker, 'complete', marker, True),
            ('computed', computed, 'incomplete', None, True),
            ('computed_without_space', computed.replace('(import (', '(import(', 1), 'incomplete', None, True),
            ('nested_computed', '(import "%s")' % wrapper, 'incomplete', wrapper, True),
            ('unevaluated', '(if #f (import "%s"))' % marker, 'complete', marker, False),
            ('aliased', '(define pw-alias import)\n(pw-alias "%s")' % marker, 'complete', None, True),
        ]
        problems, observed = [], []
        for name, form, status, recorded, evaluated in rows:
            source = SOURCE + form + '\n'
            request = self.specimen('import-' + name, policy={'format': 'sbpl', 'sbpl_source': source})
            rc, envelope, _ = self.run('import_forms/' + name, request)
            specimen = self.common(envelope, 'import_' + name)
            imports = specimen['policy']['imports']
            reply = envelope['data']['runner_result']
            observed.append({'row': name, 'status': imports['status'], 'failure': imports['failure'],
                             'records': [(r['name'], r['sha256'], r['error']) for r in imports['records']],
                             'run': reply['normalized_outcome'], 'exit': rc})

            def expect(condition, what):
                if not condition:
                    problems.append((name, what))
            expect(specimen['policy']['augmentation']['applied_sha256'] == sha256_text(source), 'applied source digest')
            expect(imports['status'] == status, 'status')
            expect(imports['cycle'] is None and imports['exceeded'] is None, 'no cycle or bound')
            # The compiler's witness: a diagnostic naming the marker file and the
            # operation only that file contains, or a finished run.
            if evaluated:
                diagnostic = reply.get('error') or ''
                expect(rc == 1 and reply['normalized_outcome'] != 'finished' and str(marker) in diagnostic
                       and 'pw-trace-marker-operation' in diagnostic, 'worker compiler evaluated marker.sb')
            else:
                expect(rc == 0 and reply['normalized_outcome'] == 'finished', 'worker compiler did not evaluate marker.sb')
            records = imports['records']
            if recorded is None:
                expect(records == [], 'no record')
            else:
                expect(len(records) == 1 and records[0]['name'] == str(recorded)
                       and records[0]['resolved_path'] == str(recorded)
                       and records[0]['sha256'] == sha256_file(recorded)
                       and records[0]['size_bytes'] == recorded.stat().st_size, 'one hashed record')
            # A form the scan did not follow is the first problem when it is in
            # the submitted source, and an error on the record of the file that holds it.
            record_errors = [r['error'] for r in records]
            if name == 'nested_computed':
                expect(len(record_errors) == 1 and 'did not follow' in (record_errors[0] or ''), 'record error')
                expect(str(wrapper) in (imports['failure'] or '') and 'did not follow' in imports['failure'], 'failure names the file')
            elif status == 'incomplete':
                expect('did not follow' in (imports['failure'] or '') and 'source' in imports['failure'], 'failure names the source')
            else:
                expect(imports['failure'] is None and all(e is None for e in record_errors), 'no reported problem')
        self.record('import_forms', rows=observed, problems=problems)
        assert not problems, (problems, 'observed rows are in dossier-controls.json')

    def import_failures(self):
        """Report file errors individually and surface a problem in the submitted source."""
        absent = self.out / 'import_forms' / 'absent'
        first, second = str(absent / 'aa-absent.sb'), str(absent / 'zz-absent.sb')
        # The inventory still sorts the two unresolved names.
        source = SOURCE + '(import "%s")\n(import "%s")\n' % (second, first)
        request = self.specimen('import-order', policy={'format': 'sbpl', 'sbpl_source': source})
        rc, envelope, _ = self.run('import_forms/order', request)
        imports = self.common(envelope, 'import_order')['policy']['imports']
        assert imports['status'] == 'incomplete', imports
        assert [(r['name'], r['error']) for r in imports['records']] == [
            (first, 'not found in search path'), (second, 'not found in search path')], imports
        assert any(name in imports['failure'] for name in (first, second)), imports
        assert 'not found in search path' in imports['failure'], imports
        # A problem in the submitted source has no file record of its own.
        source = SOURCE + '(import "%s")\n(import (string-append "a" "b"))\n' % first
        request = self.specimen('import-order-root', policy={'format': 'sbpl', 'sbpl_source': source})
        rc, envelope, _ = self.run('import_forms/order_root', request)
        root = self.common(envelope, 'import_order_root')['policy']['imports']
        assert root['status'] == 'incomplete' and len(root['records']) == 1, root
        assert (root['records'][0]['name'], root['records'][0]['error']) == (first, 'not found in search path'), root
        assert 'source' in root['failure'] and 'did not follow' in root['failure'], root
        self.record('import_failures', failure=imports['failure'], root_failure=root['failure'])

    def applied_augments(self):
        policy = {'format': 'sbpl', 'sbpl_source': '(version 1)\n(deny default)\n', 'augments': ['exec_baseline']}
        request = self.specimen('augmented', policy=policy)
        rc, envelope, _ = self.run('augmented', request)
        assert rc == 0, envelope['result']
        specimen = self.common(envelope, 'augmented')
        augmentation = specimen['policy']['augmentation']
        assert augmentation['status'] == 'applied' and augmentation['applied'] == ['exec_baseline'], augmentation
        assert augmentation['original_sha256'] == sha256_text(policy['sbpl_source']), augmentation
        assert augmentation['applied_sha256'] != augmentation['original_sha256'] and augmentation['error'] is None
        assert envelope['data']['runner_result']['policy_sha256'] == augmentation['applied_sha256']
        assert specimen['policy']['imports']['status'] in ('complete', 'incomplete')
        # The held string is the resolved request: the augments key is gone and
        # the source is the spliced text whose hash the reply reports.
        delivery = envelope['data']['runner_client']['request_delivery']
        assert delivery['error'] is None and delivery['bytes_written'] > held_bytes(request), delivery
        self.record('augmented', augmentation=augmentation)

    def refused_augments(self):
        policy = {'format': 'sbpl', 'sbpl_source': SOURCE, 'augments': ['pw_no_such_augment']}
        request = self.specimen('refused', policy=policy)
        rc, envelope, path = self.run('refused', request)
        assert rc == 1 and envelope['result']['normalized_outcome'] == 'bad_request', envelope['result']
        assert 'pw_no_such_augment' in envelope['result']['error'], envelope['result']
        specimen = self.common(envelope, 'refused')
        augmentation = specimen['policy']['augmentation']
        assert augmentation['status'] == 'failed' and augmentation['applied'] == [], augmentation
        assert augmentation['original_sha256'] == sha256_text(SOURCE) and augmentation['applied_sha256'] is None
        assert 'pw_no_such_augment' in augmentation['error'], augmentation
        imports = specimen['policy']['imports']
        assert imports['status'] == 'not_applicable' and imports['failure'] == 'augmentation_failed', imports
        assert imports['records'] == [] and imports['closure_sha256'] is None
        data = envelope['data']
        assert data['runner_client'] is None and data['runner_result'] is None and data['policy_check'] is None, data.keys()
        assert data['runner_sandbox_diagnostics'] is None
        assert specimen['runner_provenance'] is not None, 'the runner was selected before resolution refused'
        self.no_temp_request('refused')
        self.record('refused', error=envelope['result']['error'])

    def missing_source(self):
        request = self.specimen('no-source', policy={'format': 'sbpl'})
        rc, envelope, _ = self.run('no-source', request)
        specimen = self.common(envelope, 'no-source')
        assert specimen['policy']['augmentation'] == {'status': 'not_applicable', 'applied': [], 'original_sha256': None,
                                                      'applied_sha256': None, 'error': None}, specimen['policy']
        imports = specimen['policy']['imports']
        assert imports == {'status': 'not_applicable', 'closure_sha256': None, 'records': [], 'cycle': None,
                           'exceeded': None, 'failure': None}, imports
        # The request was still delivered; the runner owns the refusal and
        # names the missing field.
        assert envelope['data']['runner_client'] is not None
        assert rc == 1 and envelope['data']['runner_result']['normalized_outcome'] == 'bad_request', envelope['result']
        assert 'sbpl_source' in envelope['data']['runner_result']['error'], envelope['result']
        self.delivery(envelope['data'], request, 'no-source')
        self.record('no-source', runner_outcome=envelope['data']['runner_result']['normalized_outcome'])

    def controller_refusals(self):
        """Request and tool refusals retain the dossier collected so far."""
        cases = []
        # Missing argument: no path at all.
        result = subprocess.run([str(self.pw), 'run'], capture_output=True, timeout=30)
        envelope = json.loads(result.stdout)
        cases.append(('missing_argument', result.returncode, envelope, None))
        # Absent file.
        absent = str(self.out / 'absent.json')
        result = subprocess.run([str(self.pw), 'run', absent], capture_output=True, timeout=30)
        cases.append(('absent_file', result.returncode, json.loads(result.stdout), absent))
        # Not JSON, and JSON that is not an object.
        for name, raw in (('not_json', b'{not json'), ('not_object', b'[1, 2]')):
            rc, envelope, path = self.run(name, None, raw=raw)
            cases.append((name, rc, envelope, path))
        # Invalid flag values fail before request selection; D2 requires a null path.
        path = self.out / 'flag-request.json'
        path.write_text(json.dumps(self.specimen('flag')))
        for flag, value in (('--timeout-ms', 'soon'), ('--runner-mode', 'invalid')):
            result = subprocess.run([str(self.pw), 'run', str(path), flag, value], capture_output=True, timeout=30)
            cases.append(('invalid_flag_' + flag[2:], result.returncode, json.loads(result.stdout), None))
        # An unknown argument preserves the already supplied request path.
        result = subprocess.run([str(self.pw), 'run', str(path), '--bogus'], capture_output=True, timeout=30)
        envelope = json.loads(result.stdout)
        assert envelope['result']['error'] == 'unknown argument: --bogus', envelope
        cases.append(('unknown_argument', result.returncode, envelope, str(path)))
        # Built-in selection cannot find an unregistered external runner.
        request = self.specimen('unknown-runner')
        request['runner'] = {'mode': 'byoxpc', 'service': 'com.example.pw.unregistered.' + os.urandom(4).hex()}
        rc, envelope, path = self.run('unknown_runner', request)
        cases.append(('unknown_runner', rc, envelope, path))
        for name, rc, envelope, path in cases:
            malformed = name in ('not_json', 'not_object')
            assert rc == (1 if malformed else 2), (name, rc, envelope['result'])
            assert envelope['result']['ok'] is False and envelope['result']['normalized_outcome'] == ('bad_request' if malformed else 'tool_error'), (name, envelope['result'])
            if malformed:
                assert envelope['data']['request_failure'] == {'code': 'invalid_json' if name == 'not_json' else 'type_mismatch', 'path': []}, envelope
            assert isinstance(envelope['result']['error'], str) and envelope['result']['error'], (name, envelope['result'])
            specimen = self.common(envelope, name)
            assert specimen['request_path'] == path, (name, specimen['request_path'], path)
            data = envelope['data']
            for key in ('runner_client', 'runner_result', 'policy_check', 'runner_sandbox_diagnostics'):
                assert data[key] is None, (name, key)
            assert 'error' not in data, (name, data.keys())
            if name == 'unknown_runner':
                # Resolution happened: the policy was hashed and scanned before refusal.
                assert specimen['policy']['augmentation']['status'] == 'not_requested', specimen['policy']
                assert specimen['policy']['imports']['status'] == 'complete', specimen['policy']
                assert specimen['runner_provenance'] is None
                for role in ('service', 'worker', 'validator', 'unentitled_worker'):
                    record = specimen['binaries'][role]
                    assert record['verification'] == 'unavailable' and record['path'] is None, (name, role, record)
                    assert envelope['result']['error'] in record['reason'] or 'not found' in record['reason'], record
            else:
                assert specimen['policy']['augmentation']['status'] == 'not_applicable', (name, specimen['policy'])
                assert specimen['policy']['imports']['status'] == 'not_applicable', (name, specimen['policy'])
                assert specimen['runner_provenance'] is None
                assert all(specimen['binaries'][role]['verification'] == 'unavailable' for role in ('service', 'worker', 'validator', 'unentitled_worker'))
            if name == 'missing_argument':
                assert specimen['app_provenance'] is None or 'evidence_manifest_path' in specimen['app_provenance']
            self.no_temp_request(name)
        self.record('controller_refusals', cases=[c[0] for c in cases])

    def executable_overrides(self):
        work = Path(tempfile.mkdtemp(prefix='pw-dossier-', dir='/private/tmp'))
        try:
            same = work / 'worker-copy'
            shutil.copy2(self.app / WORKER_REL, same)
            different = work / 'other-worker'
            shutil.copyfile('/usr/bin/true', different)
            different.chmod(0o755)
            baseline = self.entries[WORKER_REL]['sha256']
            # A byte-identical copy at another path is observed, hashed and matched.
            request = self.specimen('override-same', overrides={'worker_executable_path': str(same)})
            rc, envelope, _ = self.run('override_same', request)
            specimen = self.common(envelope, 'override_same')
            record = specimen['binaries']['worker']
            assert record == {'path': str(same), 'actual_sha256': sha256_file(same), 'baseline_sha256': baseline,
                              'verification': 'match', 'reason': None}, record
            assert specimen['binaries']['validator'] is None
            assert envelope['data']['runner_result']['test_overrides'] == request['_test_overrides']
            # Different bytes: a mismatch, observed before invocation and not a refusal.
            request = self.specimen('override-different', overrides={'worker_executable_path': str(different)})
            rc, envelope, _ = self.run('override_different', request)
            specimen = self.common(envelope, 'override_different')
            record = specimen['binaries']['worker']
            assert record['path'] == str(different) and record['actual_sha256'] == sha256_file(different), record
            assert record['baseline_sha256'] == baseline and record['verification'] == 'mismatch', record
            assert 'differ from the manifest baseline' in record['reason'], record
            assert envelope['data']['runner_result']['test_overrides'] == request['_test_overrides']
            self.delivery(envelope['data'], request, 'override_different')
            # Missing file: observed as unavailable, invocation still happens.
            missing = str(work / 'nonexistent')
            request = self.specimen('override-missing', overrides={'worker_executable_path': missing})
            rc, envelope, _ = self.run('override_missing', request)
            specimen = self.common(envelope, 'override_missing')
            record = specimen['binaries']['worker']
            assert record['path'] == missing and record['actual_sha256'] is None and record['baseline_sha256'] == baseline, record
            assert record['verification'] == 'unavailable' and 'cannot stat' in record['reason'], record
            assert envelope['data']['runner_result']['normalized_outcome'] == 'worker_spawn_failed', envelope['data']['runner_result']
            # The manifest's own path needs no comparison.
            request = self.specimen('override-manifest')
            rc, envelope, _ = self.run('override_manifest', request,
                                       controls={'validator_executable_path': str(self.app / VALIDATOR_REL)})
            specimen = self.common(envelope, 'override_manifest')
            assert specimen['binaries'] == {'service': None, 'worker': None, 'validator': None, 'unentitled_worker': None}, specimen['binaries']
            self.record('executable_overrides', baseline=baseline)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def byoxpc_binaries(self, specimen):
        session = self.byoxpc['session']
        bundle = Path(session['bundle_path'])
        provenance = specimen['runner_provenance']
        assert provenance['runner_kind'] == 'byoxpc' and provenance['runner_service_name'] == self.byoxpc['service_name'], provenance
        assert provenance['runner_registry_id'] == self.byoxpc['runner_id'], provenance
        listing = json.loads(subprocess.run([self.pw, 'runner', 'list'], capture_output=True, check=True, timeout=30).stdout)
        record = next(r for r in listing['data']['runners'] if r['id'] == self.byoxpc['runner_id'])
        for field in ('signature', 'entitlements', 'worker_signature', 'worker_entitlements',
                      'validator_signature', 'validator_entitlements', 'unentitled_worker_signature', 'unentitled_worker_entitlements'):
            assert provenance['runner_' + field] == record[field], (field, provenance.get('runner_' + field), record.get(field))
        assert provenance['runner_worker_entitlements']['keys'] == provenance['runner_entitlements']['keys'], provenance
        assert provenance['runner_validator_entitlements'] == {'raw_plist': None, 'keys': [], 'granted': [], 'error': None}, provenance
        for role, rel, name in (('service', SERVICE_REL, 'PWRunner'), ('worker', WORKER_REL, 'pw-probe-runner'),
                                ('validator', VALIDATOR_REL, 'sb_api_validator'), ('unentitled_worker', UNENTITLED_WORKER_REL, 'pw-probe-runner-unentitled')):
            record = specimen['binaries'][role]
            path = bundle / 'Contents/MacOS' / name
            assert record['path'] == str(path), (role, record)
            assert record['actual_sha256'] == sha256_file(path), (role, record)
            assert record['baseline_sha256'] == self.entries[rel]['sha256'], (role, record)
            expected = 'match' if record['actual_sha256'] == record['baseline_sha256'] else 'mismatch'
            assert record['verification'] == expected, (role, record)
            assert (record['reason'] is None) == (expected == 'match'), (role, record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pw')
    parser.add_argument('out')
    parser.add_argument('--byoxpc', help='runner_env.json of an installed BYOXPC runner')
    parser.add_argument('--session', help='session.json of that installation')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    byoxpc = None
    if args.byoxpc:
        byoxpc = json.loads(Path(args.byoxpc).read_text())
        byoxpc['session'] = json.loads(Path(args.session).read_text())
    witness = Witness(args.pw, out, byoxpc=byoxpc)
    witness.ordinary()
    if byoxpc:
        print('BYOXPC dossier: provenance and bundle-local binaries hashed against the shipped baselines')
        return
    witness.with_imports()
    witness.import_failures()
    witness.applied_augments()
    witness.refused_augments()
    witness.missing_source()
    witness.controller_refusals()
    witness.executable_overrides()
    witness.import_forms()
    print(f'{len(witness.records)} dossier examples agree with independently read facts')


if __name__ == '__main__':
    main()
