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
from run_capture import RunCapture

SERVICE_REL = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner'
WORKER_REL = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
VALIDATOR_REL = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator'
SOURCE = '(version 1)\n(allow default)\n'
TEMP_REQUEST_DIR = Path(tempfile.gettempdir()) / 'policy-witness'


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def held_bytes(request):
    """The controller serializes the resolved request once: sorted keys, two-space pretty JSON."""
    return len(json.dumps(request, indent=2, sort_keys=True, ensure_ascii=False).encode())


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
        request = {'schema_version': 1, 'specimen_id': 'dossier-' + name,
                   'policy': policy if policy is not None else {'format': 'sbpl', 'sbpl_source': SOURCE},
                   'probe_plan': plan if plan is not None else []}
        if self.byoxpc:
            request['runner'] = {'mode': 'byoxpc', 'service': self.byoxpc['service_name']}
        if overrides is not None:
            request['_test_overrides'] = overrides
        return request

    def run(self, name, request, *, cli_args=('--no-log-capture',), timeout=60, raw=None):
        directory = self.out / name
        if raw is not None:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / 'request.raw'
            path.write_bytes(raw)
            result = subprocess.run([str(self.pw), 'run', str(path), *cli_args], capture_output=True, timeout=timeout)
            (directory / 'stdout').write_bytes(result.stdout)
            (directory / 'stderr').write_bytes(result.stderr)
            return result.returncode, json.loads(result.stdout), str(path)
        with RunCapture(self.pw, directory, request, cli_args=list(cli_args)) as capture:
            rc = capture.wait(timeout=timeout)
            envelope = capture.load_json()
        return rc, envelope, str(capture.request_path) if hasattr(capture, 'request_path') else None

    def record(self, name, **facts):
        self.records.append(dict(control=name, **facts))
        (self.out / 'dossier-controls.json').write_text(json.dumps(self.records, indent=2) + '\n')
        print(f'{name}: ok', flush=True)

    # ---- shared assertions --------------------------------------------------

    def common(self, envelope, name):
        errors = consumer.validate(envelope)
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
        assert specimen['binaries'] == {'service': None, 'worker': None, 'validator': None}, specimen['binaries']
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
        assert rc == 0 and envelope['result']['normalized_outcome'] == 'ok', envelope['result']
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
        assert data['runner_sandbox_diagnostics'] is None and data['sandbox_log_capture'] is None
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
        assert rc == 1 and envelope['data']['runner_result']['normalized_outcome'] == 'bad_policy', envelope['result']
        assert 'sbpl_source' in envelope['data']['runner_result']['error'], envelope['result']
        self.delivery(envelope['data'], request, 'no-source')
        self.record('no-source', runner_outcome=envelope['data']['runner_result']['normalized_outcome'])

    def controller_refusals(self):
        """Uniform tool_error envelopes with the dossier collected so far."""
        cases = []
        # Missing argument: no path at all.
        result = subprocess.run([str(self.pw), 'run'], capture_output=True, timeout=30)
        envelope = json.loads(result.stdout)
        cases.append(('missing_argument', result.returncode, envelope, None))
        # Absent file.
        absent = str(self.out / 'absent.json')
        result = subprocess.run([str(self.pw), 'run', absent, '--no-log-capture'], capture_output=True, timeout=30)
        cases.append(('absent_file', result.returncode, json.loads(result.stdout), absent))
        # Not JSON, and JSON that is not an object.
        for name, raw in (('not_json', b'{not json'), ('not_object', b'[1, 2]')):
            rc, envelope, path = self.run(name, None, raw=raw)
            cases.append((name, rc, envelope, path))
        # Invalid flag value: the path seen so far is retained.
        path = self.out / 'flag-request.json'
        path.write_text(json.dumps(self.specimen('flag')))
        result = subprocess.run([str(self.pw), 'run', str(path), '--timeout-ms', 'soon'], capture_output=True, timeout=30)
        cases.append(('invalid_flag', result.returncode, json.loads(result.stdout), str(path)))
        # Built-in selection cannot find an unregistered external runner.
        request = self.specimen('unknown-runner')
        request['runner'] = {'mode': 'byoxpc', 'service': 'com.example.pw.unregistered.' + os.urandom(4).hex()}
        rc, envelope, path = self.run('unknown_runner', request)
        cases.append(('unknown_runner', rc, envelope, path))
        for name, rc, envelope, path in cases:
            assert rc == 2, (name, rc, envelope['result'])
            assert envelope['result']['ok'] is False and envelope['result']['normalized_outcome'] == 'tool_error', (name, envelope['result'])
            assert isinstance(envelope['result']['error'], str) and envelope['result']['error'], (name, envelope['result'])
            specimen = self.common(envelope, name)
            assert specimen['request_path'] == path, (name, specimen['request_path'], path)
            data = envelope['data']
            for key in ('runner_client', 'runner_result', 'policy_check', 'runner_sandbox_diagnostics', 'sandbox_log_capture'):
                assert data[key] is None, (name, key)
            assert 'error' not in data, (name, data.keys())
            if name == 'unknown_runner':
                # Resolution happened: the policy was hashed and scanned before refusal.
                assert specimen['policy']['augmentation']['status'] == 'not_requested', specimen['policy']
                assert specimen['policy']['imports']['status'] == 'complete', specimen['policy']
                assert specimen['runner_provenance'] is None
                for role in ('service', 'worker', 'validator'):
                    record = specimen['binaries'][role]
                    assert record['verification'] == 'unavailable' and record['path'] is None, (name, role, record)
                    assert envelope['result']['error'] in record['reason'] or 'not found' in record['reason'], record
            else:
                assert specimen['policy']['augmentation']['status'] == 'not_applicable', (name, specimen['policy'])
                assert specimen['policy']['imports']['status'] == 'not_applicable', (name, specimen['policy'])
                assert specimen['runner_provenance'] is None
                assert all(specimen['binaries'][role]['verification'] == 'unavailable' for role in ('service', 'worker', 'validator'))
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
            request = self.specimen('override-manifest', overrides={'validator_executable_path': str(self.app / VALIDATOR_REL)})
            rc, envelope, _ = self.run('override_manifest', request)
            specimen = self.common(envelope, 'override_manifest')
            assert specimen['binaries'] == {'service': None, 'worker': None, 'validator': None}, specimen['binaries']
            self.record('executable_overrides', baseline=baseline)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def byoxpc_binaries(self, specimen):
        session = self.byoxpc['session']
        bundle = Path(session['bundle_path'])
        provenance = specimen['runner_provenance']
        assert provenance['runner_kind'] == 'byoxpc' and provenance['runner_service_name'] == self.byoxpc['service_name'], provenance
        assert provenance['runner_registry_id'] == self.byoxpc['runner_id'], provenance
        for role, rel, name in (('service', SERVICE_REL, 'PWRunner'), ('worker', WORKER_REL, 'pw-probe-runner'),
                                ('validator', VALIDATOR_REL, 'sb_api_validator')):
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
    witness.applied_augments()
    witness.refused_augments()
    witness.missing_source()
    witness.controller_refusals()
    witness.executable_overrides()
    print(f'{len(witness.records)} dossier examples agree with independently read facts')


if __name__ == '__main__':
    main()
