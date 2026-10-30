"""F2 investigation: trace ordinary handoff, then control three reply boundaries.

This builds a disposable host from the current production source membership,
instruments only copied sources, and keeps the real admission/orchestration and
selected app's worker/client. The 50 ms retirement timer is unchanged. Gates
are after encoding and inside the retirement closure, outside admission locks.
No request is automatically resubmitted here; the public observation sequence
retains the shipped controller's own acquisition behavior.

The baseline generated worker identity is intentionally unchanged: this is an
instrumented host paired with the original runtime worker, not a normal build
or production-equivalence result. A trace-only failure can be classified only
to its actually observed boundaries. Matching controlled XPC error numbers do
not attribute earlier failures. Trace IO itself changes timing.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
import contract
import native_sources
import session
from artifact import digest, inventory, inspect, MANIFEST
from bundle import command, SERVICE, CLIENT
from consumer import validate
from neighbor_lab import save, process_identity, generation, executable_path, wait_for, ProcessWatch

HOST = SERVICE / 'Contents/MacOS/PWRunner'
WORKER = SERVICE / 'Contents/MacOS/pw-probe-runner'
FIXTURES = ROOT / 'tests/fixtures/byoxpc'
NATURAL_REQUESTS = 24


def replace_once(source, old, new):
    assert source.count(old) == 1, f'fixture anchor changed: {old!r}'
    return source.replace(old, new, 1)


def service_source(source):
    assert source.count('let hostExitDelayMs = 50') == 1, 'production retirement delay changed'
    source = replace_once(source,
        'DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(hostExitDelayMs)) { exit(0) }',
        'DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(hostExitDelayMs)) { F2Trace.beforeExit(); exit(0) }')
    source = replace_once(source, 'final class PWRunnerService: NSObject, PWRunnerProtocol {',
        'final class PWRunnerService: NSObject, PWRunnerProtocol {\n    var f2ClientPID: Int32?')
    source = replace_once(source,
        '    func runSpecimen(_ request: Data, withReply reply: @escaping (Data) -> Void) {',
        '    func runSpecimen(_ request: Data, withReply reply: @escaping (Data) -> Void) {\n'
        '        let f2 = F2Trace.receive(request, clientPID: f2ClientPID)')
    source = replace_once(source, '            reply(pwRunnerReplyData(result))',
        '            F2Trace.event(f2, "reply_encoding_started")\n'
        '            let f2Bytes = pwRunnerReplyData(result)\n'
        '            F2Trace.encoded(f2, result, f2Bytes)\n'
        '            F2Trace.event(f2, "reply_invocation")\n'
        '            reply(f2Bytes)\n'
        '            F2Trace.event(f2, "reply_returned")')
    source = replace_once(source, '            scheduleExit()',
        '            F2Trace.willScheduleExit(f2)\n            scheduleExit()')
    source = replace_once(source, '        if !admission.claim() {',
        '        if !admission.claim() {\n            F2Trace.event(f2, "admission_refused")')
    source = replace_once(source, '            reply(pwRunnerReplyData(resp))',
        '            F2Trace.event(f2, "reply_encoding_started")\n'
        '            let f2Bytes = pwRunnerReplyData(resp)\n'
        '            F2Trace.encoded(f2, resp, f2Bytes)\n'
        '            F2Trace.event(f2, "reply_invocation")\n'
        '            reply(f2Bytes)\n'
        '            F2Trace.event(f2, "reply_returned")')
    source = replace_once(source, '        let parsed: PWRunnerRunSpec',
        '        F2Trace.admitted(f2)\n        let parsed: PWRunnerRunSpec')
    call = '        let cResp = orchestrate(parsed, policyHash, bundleString("CFBundleIdentifier"), workerPath, validatorPath)'
    source = replace_once(source, call,
        '        F2Trace.event(f2, "orchestration_entered")\n' + call + '\n'
        '        F2Trace.orchestrationReturned(f2, cResp)')
    source = replace_once(source, '        if !authorizedCaller(newConnection) {',
        '        if !authorizedCaller(newConnection) {\n'
        '            F2Trace.event(nil, "connection_refused", ["client_pid": Int(newConnection.processIdentifier)])')
    source = replace_once(source, '        let exported = PWRunnerService(admission: admission)',
        '        let exported = PWRunnerService(admission: admission)\n'
        '        exported.f2ClientPID = newConnection.processIdentifier\n'
        '        F2Trace.event(nil, "connection_accepted", ["client_pid": Int(newConnection.processIdentifier)])')
    return source


def worker_host_source(source):
    # The child still blocks on policy delivery here. This records its kernel
    # generation before the real transfer; no worker code or ABI is changed.
    anchor = '    // The transfer calls (clock, write, poll) are one injection point: the'
    return replace_once(source, anchor, '    F2Trace.workerSpawned(pid)\n' + anchor)


def build_host(scratch, out):
    command(out / 'meson-source-list', ['meson', 'introspect', ROOT / 'meson.build', '--targets'], timeout=60)
    targets, problems = native_sources.parse_targets(
        (out / 'meson-source-list/stdout').read_text(), ROOT, 'meson.build')
    problems += native_sources.problems(targets, native_sources.expected(ROOT), 'meson.build')
    assert not problems, problems
    sources = targets['PWRunner']
    assert sources[-1] == 'runner/Services/PWRunner/main.swift', sources
    assert all(p.startswith('runner/Sources/PWRunnerCore/') and p.endswith('.swift') for p in sources[:-1])
    copied = out / 'sources'
    originals = out / 'original-sources'
    hashes = {}
    for relative in [*sources, 'runner/Sources/PWCWorkerShim/PWCWorkerShim.c', 'meson.build']:
        original = ROOT / relative
        destination = copied / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        body = original.read_text()
        if relative.endswith('/PWRunnerService.swift'):
            body = service_source(body)
        elif relative.endswith('/CWorker.swift'):
            body = worker_host_source(body)
        elif relative == 'runner/Services/PWRunner/main.swift':
            body = replace_once(body, 'let listener: NSXPCListener',
                'F2Trace.event(nil, "host_started")\nlet listener: NSXPCListener')
        destination.write_text(body)
        backup = originals / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, backup)
        hashes[relative] = dict(original=digest(original), compiled_copy=digest(destination),
                                instrumented=digest(original) != digest(destination))
    for name in ('F2Trace.swift', 'F2Process.c'):
        shutil.copy2(FIXTURES / name, copied / name)
        hashes['tests/fixtures/byoxpc/' + name] = dict(original=digest(FIXTURES / name), compiled_copy=digest(copied / name))
    dependencies = ['tests/suites/runner_byoxpc/opt_in/retirement_controls.py',
        'tests/suites/runner_byoxpc/opt_in/retirement_controls.sh',
        'tests/fixtures/byoxpc/session.py', 'tests/fixtures/byoxpc/neighbor_lab.py',
        'tests/fixtures/caller_auth/bundle.py', 'tests/lib/native_sources.py',
        'tests/lib/artifact.py', 'tests/lib/consumer.py', 'tests/lib/contract.py', 'tests/build-evidence.py']
    for relative in dependencies:
        original = ROOT / relative
        backup = originals / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, backup)
        hashes[relative] = dict(original=digest(original))
    save(out / 'source-hashes.json', hashes)
    save(out / 'instrumentation.json', dict(
        source_membership=sources, host_exit_delay_ms=50, gate_watchdog_seconds=20,
        gates=['encoded reply before invocation', 'retirement closure before exit(0)'],
        unchanged_worker_identity_intentional=True,
        generated_worker_identity=contract.WORKER_IDENTITY,
        fixture_compiler_target='arm64-apple-macosx26.0', fixture_swift_optimization='-Onone',
        identity_scope='original worker/ABI and generated identity retained; host instrumentation is disclosed, not production equivalence',
        timing_limit='synchronous trace IO, hashing and kernel generation reads change timing',
        historical_attribution=False, request_retries_added=False))
    build = scratch / 'build'; build.mkdir(parents=True)
    objects = []
    for name, source in (('shim', copied / 'runner/Sources/PWCWorkerShim/PWCWorkerShim.c'),
                         ('F2Process', copied / 'F2Process.c')):
        obj = build / (name + '.o'); objects.append(obj)
        command(out / ('compile-' + name), ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang',
            '-target', 'arm64-apple-macosx26.0', '-Wall', '-Wextra', '-Werror', '-c', source, '-o', obj], timeout=60)
    host = build / 'PWRunner'
    command(out / 'compile-host', ['/usr/bin/xcrun', '--sdk', 'macosx', 'swiftc', '-Onone', '-g',
        '-target', 'arm64-apple-macosx26.0',
        '-module-cache-path', build / 'module-cache', '-o', host,
        *[copied / p for p in sources], copied / 'F2Trace.swift', *objects], timeout=180)
    save(out / 'compiled-host.json', dict(path=str(host), sha256=digest(host)))
    return host


def custom_app(source, host, scratch, out, identity, trace, gates):
    app = scratch / out.name / 'PolicyWitness.app'
    command(out / 'copy-app', ['/usr/bin/ditto', source, app])
    assert inventory(app) == inventory(source), 'initial app copy differs'
    shutil.copy2(host, app / HOST)
    app_id = 'com.policywitness.test.f2.a' + secrets.token_hex(12)
    service_id = 'com.policywitness.test.f2.s' + secrets.token_hex(12)
    for bundle, identifier in ((app, app_id), (app / SERVICE, service_id)):
        path = bundle / 'Contents/Info.plist'
        info = plistlib.loads(path.read_bytes())
        info['CFBundleIdentifier'] = identifier
        if bundle != app:
            info['PWF2Trace'] = dict(directory=str(trace), gates=gates)
            save(out / 'configured-service-info.json', info)
        path.write_bytes(plistlib.dumps(info))
    # Match the existing disposable signed-host recipe. The worker, validator,
    # issuer and raw client remain the selected app's original binary bytes.
    command(out / 'sign-service', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', ROOT / 'runner/Services/PWRunner/Entitlements.plist', '-s', identity, app / SERVICE], timeout=90)
    command(out / 'substitution-evidence', [sys.executable, '-B', '-S', ROOT / 'tests/build-evidence.py',
        '--app-bundle', app, '--app-entitlements', ROOT / 'PolicyWitness.entitlements',
        '--substitution-of', source, '--identity', identity], timeout=120)
    command(out / 'sign-app', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', ROOT / 'PolicyWitness.entitlements', '-s', identity, app], timeout=90)
    report = inspect(app); save(out / 'artifact.json', report)
    assert report['ok'], report
    for relative in (CLIENT, WORKER, SERVICE / 'Contents/MacOS/sb_api_validator', SERVICE / 'Contents/MacOS/pw-extension-issuer'):
        assert digest(app / relative) == digest(source / relative), f'fixture altered runtime helper: {relative}'
    save(out / 'binary-hashes.json', dict(host=digest(app / HOST), worker=digest(app / WORKER),
        raw_client=digest(source / CLIENT), manifest=digest(app / MANIFEST)))
    return app


def specimen(name, effect=None):
    plan = [] if effect is None else [dict(step_id='append_once',
        sandbox_check=dict(operation='process-exec*', filter=dict(kind='path', value='/bin/sh')),
        attempt=dict(kind='exec', action='spawn', target='/bin/sh',
                     args=['-c', 'printf x >> "$1"', 'effect', str(effect)]))]
    return dict(schema_version=contract.REQUEST_SCHEMA, specimen_id=name,
        policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'), probe_plan=plan)


class Arrangement:
    def __init__(self, name, pw, out, resource):
        self.name, self.pw, self.out, self.resource = name, str(pw), out, resource
        self.trace = resource / 'trace'; self.trace.mkdir()
        self.effects = resource / 'effects'; self.effects.mkdir()
        self.processes, self.requests, self.exit_observations = [], [], []
        self.state = None
        self.app = None
        self.ownership = dict(kind='f2-retirement-investigation', arrangement=name,
            resource=str(resource), artifacts=str(out), session_receipt=str(out / 'session.json'), removed=False)
        self.persist()

    def persist(self):
        save(self.resource / 'ownership.json', self.ownership)
        save(self.out / 'resource-ownership.json', self.ownership)

    def events(self, name=None, kind=None):
        values = [json.loads(path.read_text()) for path in sorted(self.trace.glob('*.json'))]
        assert not any(e['event'] == 'gate_watchdog' for e in values), 'fixture gate watchdog expired'
        return [e for e in values if (name is None or e.get('specimen_id') == name)
                and (kind is None or e['event'] == kind)]

    def event(self, name, kind):
        def observed():
            values = self.events(name, kind)
            assert len(values) <= 1, ('unexpected repeated controlled boundary', name, kind, values)
            return values[0] if values else None
        return wait_for(observed, f'{self.name}: {name} {kind}', timeout=15)

    def configure(self, app, identity):
        self.app = app
        self.ownership['custom_source_app'] = str(app)
        self.persist()
        # This helper arms durable ownership before install and uses the
        # original CLI. Its connection verification is traced but never gated.
        session.install(self.pw, app, self.out, self.out / 'runner_env.json', identity)
        self.state = json.loads((self.out / 'session.json').read_text())
        self.service = self.state['service_name']
        self.host_path = Path(self.state['bundle_path']) / 'Contents/MacOS/PWRunner'
        self.worker_path = self.host_path.with_name('pw-probe-runner')
        self.env = dict(os.environ, PW_RUNNER_REGISTRY=self.state['registry_path'])
        self.ownership.update(service_name=self.service, scope='user',
            bundle_path=self.state['bundle_path'], session_state=self.state['state_path'])
        self.persist()
        config = plistlib.loads(Path(self.state['plist_path']).read_bytes())
        save(self.out / 'launchd-configuration.json', config)
        # Only the installation primer is separated. Requests in trace_only
        # remain back-to-back; no per-request retirement wait or harness retry.
        time.sleep(config.get('ThrottleInterval', 10) + 1)
        self.assert_known_exits('installation-primer')

    def launch(self, name, *, effect=False, public=False):
        folder = self.out / 'requests' / name; folder.mkdir(parents=True)
        target = self.effects / name if effect else None
        assert target is None or not target.exists(), 'refusing reused effect path'
        spec = specimen(name, target)
        if public:
            spec['runner'] = dict(mode='byoxpc', service=self.service)
        path = folder / 'specimen.json'; save(path, spec)
        argv = [self.pw, 'run', str(path), '--timeout-ms', '30000'] if public else [
            str(Path(self.pw).parent / 'pw-runner-client'), 'run', '--timeout-ms', '30000',
            '--mach-service', self.service, str(path)]
        record = dict(name=name, argv=argv, public=public, folder=str(folder),
            effect=str(target) if target else None, specimen_sha256=digest(path), start_ns=time.monotonic_ns(),
            harness_timeout=False, returncode=None)
        with (folder / 'stdout').open('wb') as stdout, (folder / 'stderr').open('wb') as stderr:
            process = subprocess.Popen(argv, stdout=stdout, stderr=stderr,
                                       stdin=subprocess.DEVNULL, env=self.env, start_new_session=True)
        record['client_process'] = process_identity(process.pid)
        self.processes.append(process); self.requests.append(record)
        save(folder / 'record.json', record)
        return process, record

    def receive(self, launched):
        process, record = launched
        folder = Path(record['folder'])
        try:
            record['returncode'] = process.wait(timeout=40)
        except subprocess.TimeoutExpired:
            record['harness_timeout'] = True
            raise AssertionError('experiment watchdog waiting for client: ' + record['name'])
        finally:
            record['end_ns'] = time.monotonic_ns()
            save(folder / 'record.json', record)
        raw = json.loads((folder / 'stdout').read_bytes())
        problems = validate(raw)
        assert not problems, problems
        result = raw['data']['runner_result'] if record['public'] else raw
        record.update(outcome=result['normalized_outcome'], reply_pid=result['pid'], error=result.get('error'))
        if record['public']:
            record['runner_acquisition'] = raw['data']['runner_acquisition']
            record['runner_client'] = raw['data']['runner_client']
        save(folder / 'record.json', record)
        return result

    def release(self, gate):
        path = Path(gate['gate_path'])
        assert path.parent == self.trace and path.name == gate['invocation'] + '.' + gate['boundary'] + '.allow'
        with path.open('xb') as handle:
            handle.write(b'allow\n')
        save(self.out / ('release-' + path.name + '.json'), dict(gate=gate, released_ns=time.monotonic_ns()))

    def identity_state(self, identity):
        assert identity.get('observed') is True, ('kernel generation was not observed', identity)
        now = process_identity(identity['pid'])
        state = ('alive' if generation(now) == generation(identity) else 'gone') if now['observed'] else (
            'gone' if now['absent'] else 'unknown')
        observation = dict(expected=identity, observed=now, state=state, observed_ns=time.monotonic_ns())
        self.exit_observations.append(observation)
        save(self.out / 'kernel-generation-observations.json', self.exit_observations)
        return state

    def gone(self, identity, description):
        def observed():
            state = self.identity_state(identity)
            assert state != 'unknown', ('kernel generation exit is unknown', identity)
            return state == 'gone'
        wait_for(observed, description, timeout=10)

    def live_owned_host(self, event):
        identity = event['host']
        before = process_identity(identity['pid'])
        path = executable_path(identity['pid'])
        after = process_identity(identity['pid'])
        save(self.out / ('host-ownership-' + event['invocation'] + '.json'), dict(
            traced=identity, before=before, executable=path, after=after))
        assert before['observed'] and after['observed'] and identity['observed']
        assert generation(before) == generation(identity) == generation(after)
        assert path == str(self.host_path) and after['ppid'] == 1, ('not the owned launchd host', path, after)
        return identity

    def worker_reaped(self, name):
        returned = self.event(name, 'orchestration_returned')
        spawned = self.event(name, 'worker_spawned')
        assert returned.get('worker_reaped') is True and returned['worker_pid'] == spawned['worker']['pid'], returned
        assert returned['outcome'] == 'ok' and returned['rc'] == 0, returned
        self.gone(spawned['worker'], 'independent worker generation exit: ' + name)
        return returned

    def effect(self, name, expected):
        path = self.effects / name
        observed = path.read_bytes() if path.exists() else None
        save(self.out / ('effect-' + name + '.json'), dict(path=str(path), exists=observed is not None,
            bytes_hex=observed.hex() if observed is not None else None, observed_ns=time.monotonic_ns()))
        assert observed == expected, ('independent append effect', name, observed, expected)

    def assert_known_exits(self, phase):
        identities = {}
        for event in self.events():
            for field in ('host', 'worker'):
                identity = event.get(field)
                if identity is not None:
                    assert identity.get('observed') is True, ('unobserved generation', event)
                    identities[generation(identity)] = identity
        assert identities, 'no host trace recorded'
        for identity in identities.values():
            self.gone(identity, phase + ': ' + generation(identity))

    def trace_only(self):
        observed = []
        for public in (True, False):
            actor = 'public' if public else 'raw'
            for index in range(NATURAL_REQUESTS):
                name = f'f2-observe-{actor}-{index:02d}'
                result = self.receive(self.launch(name, public=public))
                observed.append(dict(name=name, actor=actor, outcome=result['normalized_outcome'], error=result.get('error'),
                    sampled_ns=time.monotonic_ns(), host_boundaries=self.events(name)))
                save(self.out / 'ordinary-observations.json', observed)
        assert not self.events(kind='gate_wait'), 'trace-only arrangement unexpectedly gated'
        xpc_errors = [row for row in observed if row['outcome'] == 'xpc_error']
        summary = dict(public_requests=NATURAL_REQUESTS, raw_requests=NATURAL_REQUESTS,
            outcomes={actor: {outcome: sum(row['actor'] == actor and row['outcome'] == outcome for row in observed)
                for outcome in sorted({row['outcome'] for row in observed if row['actor'] == actor})}
                for actor in ('public', 'raw')}, xpc_errors=xpc_errors,
            xpc_error_observed=bool(xpc_errors), historical_failure_attributed=False,
            production_reliability_accepted=False,
            limit='An unobserved boundary is not proof of nonexecution; instrumentation can alter reproduction timing.')
        save(self.out / 'ordinary-summary.json', summary)
        return summary

    def control(self):
        owner = 'f2-control-' + self.name + '-owner'
        next_name = 'f2-control-' + self.name + '-next'
        first = self.launch(owner, effect=True)
        gate = self.event(owner, 'gate_wait')
        identity = self.live_owned_host(gate)
        self.event(owner, 'admission_claimed')
        self.worker_reaped(owner)
        self.effect(owner, b'x')
        assert self.event(owner, 'reply_encoded')['encoded_outcome'] == 'ok'
        if self.name == 'lost_execution_reply':
            assert gate['boundary'] == 'reply'
            assert not self.events(owner, 'reply_invocation') and not self.events(owner, 'exit_scheduled')
            # A distinct, explicit intervention. This is not the retirement
            # timer and must not be credited as natural reply-loss causality.
            self.live_owned_host(gate)
            intervention = dict(signal=int(signal.SIGKILL), host=identity,
                requested_ns=time.monotonic_ns(), boundary='encoded execution reply held', kind='controlled_process_loss')
            save(self.out / 'intervention.json', intervention)
            os.kill(identity['pid'], signal.SIGKILL)
            intervention['kill_returned'] = True; save(self.out / 'intervention.json', intervention)
            self.gone(identity, 'controlled execution host exit')
            result = self.receive(first)
            assert result['normalized_outcome'] == 'xpc_error' and first[1]['returncode'] == 1, result
            assert not self.events(owner, 'reply_invocation')
        else:
            assert gate['boundary'] == 'exit'
            first_result = self.receive(first)
            assert first[1]['returncode'] == 0 and first_result['normalized_outcome'] == 'ok', first_result
            self.event(owner, 'reply_returned')
            second = self.launch(next_name, effect=True)
            reply_gate = self.event(next_name, 'gate_wait')
            assert reply_gate['boundary'] == 'reply' and generation(reply_gate['host']) == generation(identity)
            self.event(next_name, 'admission_refused')
            assert self.event(next_name, 'reply_encoded')['encoded_outcome'] == 'already_ran'
            assert not self.events(next_name, 'orchestration_entered') and not self.events(next_name, 'worker_spawned')
            self.effect(next_name, None)
            if self.name == 'delivered_refusal':
                self.release(reply_gate)
                result = self.receive(second)
                assert second[1]['returncode'] == 0 and result['normalized_outcome'] == 'already_ran', result
                assert result.get('runner_subprocess') is None and result['steps'] == [], result
                encoded = self.event(next_name, 'reply_encoded')
                payload = (Path(second[1]['folder']) / 'stdout').read_bytes()
                assert payload.endswith(b'\n') and hashlib.sha256(payload[:-1]).hexdigest() == encoded['reply_sha256']
                self.event(next_name, 'reply_returned')
                self.release(gate)
                self.gone(identity, 'delivered refusal owner retirement')
            else:
                assert self.name == 'lost_refusal'
                self.release(gate)
                self.gone(identity, 'retirement while refusal reply held')
                result = self.receive(second)
                assert result['normalized_outcome'] == 'xpc_error' and second[1]['returncode'] == 1, result
                assert not self.events(next_name, 'reply_invocation')
            self.event(owner, 'exit_invocation')
            self.effect(next_name, None)
        self.effect(owner, b'x')
        self.assert_known_exits('controlled completion')
        save(self.out / 'control-summary.json', dict(arrangement=self.name, client_outcome=result['normalized_outcome'],
            actual_client_error=result.get('error'), owner_effect_hex='78', host_generation=generation(identity),
            historical_failure_attributed=False, required_xpc_error_code=None))

    def preserve_custom_source(self):
        """The dispatcher deletes scratch even on failure; preserve recovery input."""
        receipt = self.out / 'session.json'
        if not receipt.exists() or self.app is None:
            return
        state = json.loads(receipt.read_text())
        durable = Path(state['state_path'])
        if durable.exists():
            state = json.loads(durable.read_text())
        if not Path(state['staging']).exists():
            return
        preserved = self.resource / 'recovery-source' / 'PolicyWitness.app'
        if not preserved.exists():
            command(self.out / 'preserve-recovery-source', ['/usr/bin/ditto', self.app, preserved])
        assert inventory(preserved) == state['source_inventory'], 'recovery source differs'
        state['original_source_app'] = state['source_app']
        state['source_app'] = str(preserved)
        session.persist_state(state, receipt)
        self.ownership['recovery_source_app'] = str(preserved)
        self.persist()

    def cleanup(self):
        errors = []
        # Release only gates emitted by this owned trace. Cleanup releases are
        # distinguished from experimental releases and never credited as proof.
        for path in sorted(self.trace.glob('*.json')):
            try:
                event = json.loads(path.read_text())
                if event['event'] == 'gate_wait':
                    gate = Path(event['gate_path'])
                    if gate.parent != self.trace or gate.name != event['invocation'] + '.' + event['boundary'] + '.allow':
                        errors.append('unexpected cleanup gate path: ' + str(gate)); continue
                    if not gate.exists():
                        gate.write_bytes(b'cleanup-only\n')
            except BaseException as error:
                errors.append('cleanup gate release: ' + repr(error))
        for process in self.processes:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait(timeout=3)
            except ProcessLookupError:
                process.wait(timeout=3)
            except BaseException as error:
                errors.append('cleanup client: ' + repr(error))
        try:
            session.cleanup(self.pw, self.out / 'session.json')
        except BaseException as error:
            errors.append(str(error))
            try:
                self.preserve_custom_source()
            except BaseException as preservation:
                errors.append('failed to preserve recovery source: ' + str(preservation))
        try:
            # Verified service removal alone does not prove that a worker
            # exited. Unknown/still-live generations retain the external inputs.
            if self.events():
                self.assert_known_exits('cleanup')
            receipt = self.out / 'session.json'
            if receipt.exists():
                state = json.loads(receipt.read_text())
                host = Path(state['bundle_path']) / 'Contents/MacOS/PWRunner'
                # A final independent sweep can discover a still-live process
                # even if it vanished from the host trace before publication.
                watch = ProcessWatch({host: 'host', host.with_name('pw-probe-runner'): 'worker'})
                watch.sweep()
                save(self.out / 'cleanup-process-sweep.json', dict(processes=watch.snapshot(), summary=watch.summary()))
                for item in watch.snapshot():
                    pid, started = item['generation'].split('@')
                    seconds, microseconds = started.split('.')
                    self.gone(dict(pid=int(pid), observed=True, start_sec=int(seconds), start_usec=int(microseconds)),
                              'cleanup process discovered by executable path: ' + item['generation'])
        except BaseException as error:
            errors.append(str(error))
        if (self.out / 'session.json').exists():
            state = json.loads((self.out / 'session.json').read_text())
            if not state.get('removed'):
                errors.append('owned service cleanup remains unresolved')
        shutil.copytree(self.trace, self.out / 'trace', dirs_exist_ok=True)
        save(self.out / 'requests.json', self.requests)
        save(self.out / 'final-effects.json', {p.name: p.read_bytes().hex() for p in self.effects.iterdir() if p.is_file()})
        self.ownership.update(removed=not errors, cleanup_errors=errors)
        self.persist()
        if not errors:
            assert self.resource.parent == Path('/private/tmp') and self.resource.name.startswith('pw-f2-control-')
            shutil.rmtree(self.resource)
        assert not errors, ('cleanup incomplete; retain ownership and inputs', str(self.resource), errors)


def main():
    pw, app, out, scratch, identity = sys.argv[1:]
    pw, app, out, scratch = Path(pw).resolve(), Path(app).resolve(), Path(out).resolve(), Path(scratch).resolve()
    assert scratch == Path(os.environ['PW_TEST_SCRATCH']).resolve(), 'build must use case scratch'
    assert pw == app / 'Contents/MacOS/policy-witness', 'original app CLI required'
    before = inventory(app)
    save(out / 'original-app-before.json', before)
    scratch.mkdir(parents=True, exist_ok=True)
    failures = []
    summaries = []
    try:
        host = build_host(scratch, out / 'build')
        for name in ('trace_only', 'delivered_refusal', 'lost_refusal', 'lost_execution_reply'):
            folder = out / name; folder.mkdir()
            resource = Path(tempfile.mkdtemp(prefix='pw-f2-control-', dir='/private/tmp'))
            arrangement = Arrangement(name, pw, folder, resource)
            gates = {} if name == 'trace_only' else ({'f2-control-' + name + '-owner': ['reply']}
                if name == 'lost_execution_reply' else {
                    'f2-control-' + name + '-owner': ['exit'], 'f2-control-' + name + '-next': ['reply']})
            row = dict(arrangement=name, complete=False, cleanup_verified=False, resource=str(resource))
            try:
                candidate = custom_app(app, host, scratch, folder, identity, arrangement.trace, gates)
                arrangement.configure(candidate, identity)
                if name == 'trace_only':
                    row['ordinary_observations'] = arrangement.trace_only()
                else:
                    arrangement.control()
                row['complete'] = True
            except BaseException as error:
                row['error'] = repr(error)
                (folder / 'failure.txt').write_text(traceback.format_exc())
                failures.append(name + ': ' + repr(error))
            finally:
                try:
                    arrangement.cleanup()
                    row['cleanup_verified'] = True
                except BaseException as error:
                    row['cleanup_error'] = repr(error)
                    (folder / 'cleanup-failure.txt').write_text(traceback.format_exc())
                    failures.append(name + ' cleanup: ' + repr(error))
                summaries.append(row)
                save(out / 'investigation.json', dict(arrangements=summaries, failures=failures,
                    historical_failure_attributed=False, production_equivalence_claimed=False))
                assert inventory(app) == before, 'investigation changed the selected app'
            # Uncertain cleanup is a stop boundary, not permission to accumulate
            # more independently installed services while ownership is unresolved.
            if not row['cleanup_verified']:
                break
    finally:
        after = inventory(app)
        save(out / 'original-app-after.json', after)
        assert after == before, 'investigation changed the selected app'
    assert not failures, '\n'.join(failures)


if __name__ == '__main__':
    main()
