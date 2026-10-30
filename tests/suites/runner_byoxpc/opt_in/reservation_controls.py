"""Live mandatory-reservation controls using disclosed copied-source gates.

Production admission, orchestration and native effects remain in the copied
host. Independent drivers author wrong/stale/cross-connection calls. The shipped
client supplies recovery/no-replay observations; one disclosed copied client
holds capture publication after the real submission and completed host result.
No controlled XPC loss attributes any historical failure or proves production
reliability. Original F2 session/process/cleanup equipment is reused unchanged.
"""
import base64
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
sys.path[:0] = [str(ROOT / 'tests/lib'), str(ROOT / 'tests/fixtures/caller_auth'),
               str(ROOT / 'tests/fixtures/byoxpc')]
import contract
import native_sources
import session
from artifact import digest, inventory, inspect, MANIFEST
from bundle import command, sign, signature, SERVICE, CLIENT
from consumer import validate
from runner_client_capture import validate_capture, host_reply
from neighbor_lab import save, process_identity, generation, executable_path, wait_for
from retirement_controls import Arrangement, HOST, WORKER, FIXTURES, replace_once, worker_host_source, specimen


def service_source(source):
    source = replace_once(source,
        'DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(hostExitDelayMs)) { exit(0) }',
        'DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(hostExitDelayMs)) { ReservationTrace.beforeExit(); exit(0) }')
    source = replace_once(source, 'final class PWRunnerService: NSObject, PWRunnerProtocol {',
        'final class PWRunnerService: NSObject, PWRunnerProtocol {\n    var f2ClientPID: Int32?')
    source = replace_once(source,
        '    func reserveRunner(_ request: Data, withReply reply: @escaping (Data) -> Void) {',
        '    func reserveRunner(_ request: Data, withReply productionReply: @escaping (Data) -> Void) {\n'
        '        let f2 = ReservationTrace.reservation(request, clientPID: f2ClientPID)\n'
        '        let reply: (Data) -> Void = { bytes in\n'
        '            ReservationTrace.control(f2, bytes); productionReply(bytes)\n'
        '            F2Trace.event(f2, "control_reply_returned")\n'
        '        }\n'
        '        if let old = ReservationTrace.legacyControl() { reply(old); return }')
    source = replace_once(source,
        '        let decision = admission.submit(owner: connectionID, token: reservation)',
        '        let f2 = F2Trace.receive(request, clientPID: f2ClientPID)\n'
        '        let decision = admission.submit(owner: connectionID, token: reservation)\n'
        '        F2Trace.event(f2, "submission_decided", ["accepted": decision.accepted, "reason": decision.reason as Any? ?? NSNull()])')
    source = replace_once(source, '        func replyAndExit(_ result: PWRunnerRunResult) {',
        '        F2Trace.admitted(f2)\n        func replyAndExit(_ result: PWRunnerRunResult) {')
    source = replace_once(source, '            reply(true, data)',
        '            F2Trace.encoded(f2, result, data)\n'
        '            F2Trace.event(f2, "reply_invocation")\n'
        '            reply(true, data)\n'
        '            F2Trace.event(f2, "reply_returned")')
    call = '        let cResp = orchestrate(parsed, policyHash, bundleString("CFBundleIdentifier"), workerPath, validatorPath)'
    source = replace_once(source, call,
        '        F2Trace.event(f2, "orchestration_entered")\n' + call + '\n'
        '        F2Trace.orchestrationReturned(f2, cResp)')
    source = replace_once(source, '        let exported = PWRunnerService(admission: admission)',
        '        let exported = PWRunnerService(admission: admission)\n'
        '        exported.f2ClientPID = newConnection.processIdentifier\n'
        '        F2Trace.event(nil, "connection_accepted", ["client_pid": Int(newConnection.processIdentifier)])')
    return source


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
    for name in ('F2Trace.swift', 'F2Process.c', 'ReservationTrace.swift'):
        shutil.copy2(FIXTURES / name, copied / name)
        hashes['tests/fixtures/byoxpc/' + name] = dict(original=digest(FIXTURES / name), compiled_copy=digest(copied / name))
    dependencies = ['tests/suites/runner_byoxpc/opt_in/retirement_controls.py',
        'tests/suites/runner_byoxpc/opt_in/reservation_controls.py',
        'tests/suites/runner_byoxpc/opt_in/reservation_controls.sh',
        'tests/fixtures/byoxpc/ReservationDriver.swift',
        'tests/fixtures/byoxpc/ReservationClientTrace.swift',
        'tests/fixtures/byoxpc/session.py', 'tests/fixtures/byoxpc/neighbor_lab.py',
        'tests/fixtures/caller_auth/bundle.py', 'tests/lib/native_sources.py',
        'tests/lib/artifact.py', 'tests/lib/consumer.py', 'tests/lib/runner_client_capture.py',
        'tests/lib/contract.py', 'tests/build-evidence.py']
    for relative in dependencies:
        original = ROOT / relative
        backup = originals / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, backup)
        hashes[relative] = dict(original=digest(original))
    save(out / 'source-hashes.json', hashes)
    save(out / 'instrumentation.json', dict(
        source_membership=sources, host_exit_delay_ms=50, gate_watchdog_seconds=20,
        gates=['encoded grant/occupied control before invocation', 'execution reply after worker reap', 'retirement closure before exit(0)'],
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
        *[copied / p for p in sources], copied / 'F2Trace.swift', copied / 'ReservationTrace.swift', *objects], timeout=180)
    save(out / 'compiled-host.json', dict(path=str(host), sha256=digest(host)))
    return host


def custom_app(source, host, scratch, out, identity, trace, gates, client=None):
    # Executed code lives with durable resource ownership, outside protected
    # Desktop/Documents paths. Compiler products remain in case scratch.
    app = trace.parent / 'PolicyWitness.app'
    command(out / 'copy-app', ['/usr/bin/ditto', source, app])
    assert inventory(app) == inventory(source), 'initial app copy differs'
    shutil.copy2(host, app / HOST)
    if client is not None:
        shutil.copy2(client, app / CLIENT)
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
    # issuer remain the selected app's original binary bytes. Only the
    # lost-capture arrangement supplies the disclosed copied client.
    command(out / 'sign-service', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', ROOT / 'runner/Services/PWRunner/Entitlements.plist', '-s', identity, app / SERVICE], timeout=90)
    command(out / 'substitution-evidence', [sys.executable, '-B', '-S', ROOT / 'tests/build-evidence.py',
        '--app-bundle', app, '--app-entitlements', ROOT / 'PolicyWitness.entitlements',
        '--substitution-of', source, '--identity', identity], timeout=120)
    command(out / 'sign-app', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', ROOT / 'PolicyWitness.entitlements', '-s', identity, app], timeout=90)
    report = inspect(app); save(out / 'artifact.json', report)
    assert report['ok'], report
    for relative in (WORKER, SERVICE / 'Contents/MacOS/sb_api_validator', SERVICE / 'Contents/MacOS/pw-extension-issuer'):
        assert digest(app / relative) == digest(source / relative), f'fixture altered runtime helper: {relative}'
    assert digest(app / CLIENT) == digest(client if client is not None else source / CLIENT)
    save(out / 'binary-hashes.json', dict(host=digest(app / HOST), worker=digest(app / WORKER),
        raw_client=digest(source / CLIENT), installed_client=digest(app / CLIENT), manifest=digest(app / MANIFEST)))
    return app


def build_callers(app, scratch, out, identity):
    out.mkdir(parents=True)
    source_id = signature(app / CLIENT, out / 'original-client-signature')['Identifier']
    build = scratch / 'callers'; build.mkdir()
    driver_source = out / 'ReservationDriver.swift'
    shutil.copy2(FIXTURES / driver_source.name, driver_source)
    driver = build / 'reservation-driver'
    command(out / 'compile-driver', ['/usr/bin/xcrun', '--sdk', 'macosx', 'swiftc', '-parse-as-library',
        '-target', 'arm64-apple-macosx26.0', '-module-cache-path', build / 'module-cache',
        driver_source, '-o', driver], timeout=90)
    sign(driver, identity, source_id, out / 'sign-driver')
    # Compile the same client source membership as the build, with only an
    # adapter-call observation and a gate before stdout publication added.
    command(out / 'meson-source-list', ['meson', 'introspect', ROOT / 'meson.build', '--targets'], timeout=60)
    targets, errors = native_sources.parse_targets((out / 'meson-source-list/stdout').read_text(), ROOT, 'meson.build')
    assert not errors, errors
    sources = targets['pw-runner-client']
    copied = out / 'client-sources'; hashes = {}
    for relative in sources:
        original = ROOT / relative
        destination = copied / relative; destination.parent.mkdir(parents=True, exist_ok=True)
        text = original.read_text()
        if relative == 'runner/Clients/PWRunnerClient/main.swift':
            text = replace_once(text, 'private func run(args: [String]) -> Never {',
                'private func run(args: [String]) -> Never {\n    ReservationClientTrace.event("client_started")')
            text = replace_once(text, '        FileHandle.standardOutput.write(bytes)',
                '        ReservationClientTrace.beforeEmit(capture)\n        FileHandle.standardOutput.write(bytes)')
        elif relative.endswith('/PWRunnerClientSession.swift'):
            text = replace_once(text,
                '        proxy()?.runReservedSpecimen(request, reservation: reservation, withReply: reply)',
                '        if let object = proxy() {\n'
                '            object.runReservedSpecimen(request, reservation: reservation, withReply: reply)\n'
                '            ReservationClientTrace.event("selector_invoked")\n        }')
        destination.write_text(text)
        hashes[relative] = dict(original=digest(original), compiled_copy=digest(destination))
        backup = out / 'original-client-sources' / relative
        backup.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(original, backup)
    trace = copied / 'ReservationClientTrace.swift'; shutil.copy2(FIXTURES / trace.name, trace)
    client = build / 'pw-runner-client'
    command(out / 'compile-client', ['/usr/bin/xcrun', '--sdk', 'macosx', 'swiftc', '-module-name', 'main',
        '-target', 'arm64-apple-macosx26.0', '-module-cache-path', build / 'module-cache',
        *[copied / relative for relative in sources], trace, '-o', client], timeout=120)
    sign(client, identity, source_id, out / 'sign-client')
    save(out / 'caller-provenance.json', dict(driver_sha256=digest(driver), client_sha256=digest(client),
        original_client_sha256=digest(app / CLIENT), source_membership=sources, sources=hashes,
        fixture_identity=source_id, same_team_authorized_test_driver=True,
        client_changes=['actual selector invocation trace', 'capture stdout publication gate'],
        production_equivalence_claimed=False))
    return driver, client


class Driver:
    def __init__(self, arrangement, executable):
        self.arrangement = arrangement
        self.folder = arrangement.out / 'driver'; self.folder.mkdir()
        self.commands = []
        runtime = arrangement.resource / 'reservation-driver'
        shutil.copy2(executable, runtime)
        assert digest(runtime) == digest(executable), 'runtime driver differs from compiled signed bytes'
        with (self.folder / 'stdout').open('wb') as stdout, (self.folder / 'stderr').open('wb') as stderr:
            self.process = subprocess.Popen([str(runtime), arrangement.service], stdin=subprocess.PIPE,
                stdout=stdout, stderr=stderr, start_new_session=True)
        arrangement.processes.append(self.process)
        save(self.folder / 'process.json', dict(argv=[str(runtime), arrangement.service],
            compiled_executable=str(executable), process=process_identity(self.process.pid),
            executable_sha256=digest(executable), runtime_sha256=digest(runtime)))

    def send(self, operation, tag, connection='owner', **fields):
        value = dict(operation=operation, tag=tag, connection=connection, **fields)
        self.commands.append(value); save(self.folder / 'commands.json', self.commands)
        self.process.stdin.write((json.dumps(value) + '\n').encode()); self.process.stdin.flush()

    def events(self):
        lines = (self.folder / 'stdout').read_bytes().splitlines(keepends=True)
        values = [json.loads(line) for line in lines if line.endswith(b'\n')]
        assert not any(row['event'] == 'local_error' for row in values), values
        return values

    def event(self, tag, kind):
        def found():
            values = [row for row in self.events() if row['tag'] == tag and row['event'] == kind]
            assert len(values) <= 1, values
            assert self.process.poll() is None, 'independent driver exited early'
            return values[0] if values else None
        return wait_for(found, 'driver ' + tag + ' ' + kind, timeout=10)

    def open(self, connection='owner', legacy=False):
        self.send('open', 'open-' + connection, connection, legacy=legacy)
        self.event('open-' + connection, 'opened')

    def reserve(self, tag='grant', connection='owner', lease_ms=5000):
        self.send('reserve', tag, connection, lease_ms=lease_ms)
        return self.event(tag, 'control_reply')


class ReservationArrangement(Arrangement):
    def arm(self):
        (self.trace / 'armed').write_bytes(b'armed after installation verification\n')
        self.armed_ns = time.monotonic_ns()
        self.ownership['kind'] = 'reservation-protocol-controls'
        self.persist()

    def effect(self, name, expected):
        path = self.effects / name
        observed = path.read_bytes() if path.exists() else None
        if not hasattr(self, 'effect_observations'):
            self.effect_observations = []
        self.effect_observations.append(dict(name=name, path=str(path), exists=observed is not None,
            bytes_hex=observed.hex() if observed is not None else None, observed_ns=time.monotonic_ns()))
        save(self.out / 'independent-effect-observations.json', self.effect_observations)
        assert observed == expected, ('independent byte effect', name, observed, expected)

    def prepare(self, name, effect=True, public=False):
        folder = self.out / 'requests' / name; folder.mkdir(parents=True)
        target = self.effects / name if effect else None
        assert target is None or not target.exists(), 'refusing reused effect target'
        spec = specimen(name, target)
        if public:
            spec['runner'] = dict(mode='byoxpc', service=self.service)
        retained = folder / 'specimen.json'; save(retained, spec)
        runtime = self.resource / 'specimens'; runtime.mkdir(exist_ok=True)
        path = runtime / (name + '.json')
        shutil.copy2(retained, path)
        assert digest(path) == digest(retained), 'runtime specimen differs from retained request'
        return folder, target, path

    def launch(self, name, *, effect=True, public=True, copied_client=False, timeout=30000):
        folder, target, path = self.prepare(name, effect, public)
        cli = self.app / 'Contents/MacOS/policy-witness' if copied_client else Path(self.pw)
        argv = [str(cli), 'run', str(path), '--timeout-ms', str(timeout)] if public else [
            str(Path(self.pw).parent / 'pw-runner-client'), 'run', '--timeout-ms', str(timeout),
            '--mach-service', self.service, str(path)]
        env = dict(self.env)
        if copied_client:
            client_trace = self.resource / 'client-trace'; client_trace.mkdir()
            env['PW_RESERVATION_CLIENT_TRACE'] = str(client_trace)
        record = dict(name=name, argv=argv, public=public, folder=str(folder), effect=str(target),
            specimen_sha256=digest(path), start_ns=time.monotonic_ns(), harness_timeout=False, returncode=None)
        with (folder / 'stdout').open('wb') as stdout, (folder / 'stderr').open('wb') as stderr:
            process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                                       env=env, start_new_session=True)
        record['client_process'] = process_identity(process.pid)
        self.processes.append(process); self.requests.append(record); save(folder / 'record.json', record)
        return process, record

    def receive(self, launched):
        process, record = launched
        folder = Path(record['folder'])
        try:
            record['returncode'] = process.wait(timeout=40)
        except subprocess.TimeoutExpired:
            record['harness_timeout'] = True
            raise AssertionError('client watchdog: ' + record['name'])
        finally:
            record['end_ns'] = time.monotonic_ns(); save(folder / 'record.json', record)
        value = json.loads((folder / 'stdout').read_bytes())
        problems = validate(value) if record['public'] else validate_capture(value)
        assert not problems, problems
        save(folder / 'validated.json', value)
        return value

    def control_gate(self, boundary):
        def found():
            values = [event for event in self.events(kind='gate_wait') if event['boundary'] == boundary]
            assert len(values) <= 1, values
            return values[0] if values else None
        return wait_for(found, self.name + ' ' + boundary + ' gate', timeout=15)

    def kill_host(self, gate):
        identity = self.live_owned_host(gate)
        save(self.out / 'controlled-host-loss.json', dict(host=identity, signal=int(signal.SIGKILL),
            boundary=gate['boundary'], requested_ns=time.monotonic_ns(), historical_attribution=False))
        os.kill(identity['pid'], signal.SIGKILL)
        self.gone(identity, 'controlled host generation exit')
        return identity

    def no_execution(self, name):
        self.effect(name, None)
        assert not self.events(name, 'orchestration_entered') and not self.events(name, 'worker_spawned')

    def no_host_execution(self, identity):
        assert not [event for event in self.events() if event['event'] in ('orchestration_entered', 'worker_spawned')
                    and generation(event['host']) == generation(identity)], 'control-only host executed work'

    def reserved_host(self, driver):
        values = [event for event in self.events(kind='control_reply_encoded')
                  if event.get('client_pid') == driver.process.pid and event.get('status') == 'granted']
        assert len(values) == 1, values
        return values[0]['host']

    def one_execution(self, name):
        self.effect(name, b'x')
        assert len(self.events(name, 'admission_claimed')) == 1
        assert len(self.events(name, 'orchestration_entered')) == 1
        self.worker_reaped(name)

    def credentials(self, executable):
        driver = Driver(self, executable); driver.open(); driver.open('other')
        grant = driver.reserve(); assert grant['control']['status'] == 'granted', grant
        owner = self.reserved_host(driver)
        occupied = driver.reserve('occupied', 'other')
        assert occupied['control']['status'] == 'occupied' and 'reservation_id' not in occupied['control']
        for label, connection, credential in [('wrong', 'owner', 'wrong'), ('cross_connection', 'other', 'grant')]:
            name = 'f2-control-' + label
            _, _, path = self.prepare(name)
            driver.send('submit', label, connection, credential=credential, request=str(path))
            refusal = driver.event(label, 'submission_refused')
            assert refusal['control']['reason'] == 'wrong', refusal
            self.no_execution(name)
            self.no_host_execution(owner)
        name = 'f2-control-credential-owner'
        _, _, path = self.prepare(name)
        driver.send('submit', 'execute', credential='grant', request=str(path))
        received = driver.event('execute', 'host_reply')
        reply = json.loads(base64.b64decode(received['data_base64'], validate=True))
        assert not validate(reply) and reply['normalized_outcome'] == 'ok', reply
        self.one_execution(name)
        assert generation(self.event(name, 'admission_claimed')['host']) == generation(owner)
        gate = self.control_gate('exit')
        replay = 'f2-control-reused'
        _, _, path = self.prepare(replay)
        driver.send('submit', 'reused', credential='grant', request=str(path))
        assert driver.event('reused', 'submission_refused')['control']['reason'] == 'consumed'
        self.no_execution(replay)
        self.release(gate); self.gone(gate['host'], 'credential owner retired')

    def unused_reservation(self, executable, expiry):
        driver = Driver(self, executable); driver.open()
        grant = driver.reserve(lease_ms=200 if expiry else 5000)
        assert grant['control']['status'] == 'granted', grant
        owner = self.reserved_host(driver)
        name = 'f2-control-' + ('expired' if expiry else 'abandoned')
        _, _, path = self.prepare(name)
        if expiry:
            gate = self.control_gate('exit')
            driver.send('submit', 'stale', credential='grant', request=str(path))
            assert driver.event('stale', 'submission_refused')['control']['reason'] == 'expired'
            self.release(gate)
        else:
            driver.send('invalidate', 'abandon')
            driver.event('abandon', 'invalidated')
            gate = self.control_gate('exit'); self.release(gate)
        assert generation(gate['host']) == generation(owner)
        self.no_execution(name); self.no_host_execution(owner)
        self.gone(owner, name + ' host retired')

    def lost_control(self, executable, occupied):
        if occupied:
            driver = Driver(self, executable); driver.open()
            assert driver.reserve()['control']['status'] == 'granted'
            owner = self.reserved_host(driver)
        name = 'f2-control-' + ('lost-occupied' if occupied else 'lost-grant')
        launched = self.launch(name)
        gate = self.control_gate('occupied' if occupied else 'granted')
        self.no_execution(name)
        self.no_host_execution(gate['host'])
        if occupied:
            assert generation(owner) == generation(gate['host'])
        old = self.kill_host(gate)
        value = self.receive(launched)
        transport = value['data']['runner_client']['transport']
        assert value['result']['ok'] and transport['submission']['state'] == 'invoked', value
        assert len(transport['attempts']) >= 2 and transport['attempts'][-1]['outcome'] == 'granted', transport
        assert sum(a['outcome'] == 'granted' for a in transport['attempts']) == 1
        current = self.event(name, 'admission_claimed')['host']
        assert generation(current) != generation(old)
        self.one_execution(name)
        save(self.out / 'recovery.json', dict(old_host=old, executing_host=current,
            acquisition_attempts=transport['attempts'], one_submission=True, one_effect=True))

    def lost_execution(self):
        name = 'f2-control-lost-execution'
        launched = self.launch(name)
        gate = self.event(name, 'gate_wait'); assert gate['boundary'] == 'reply'
        self.one_execution(name)
        assert not self.events(name, 'reply_invocation')
        self.kill_host(gate)
        value = self.receive(launched)
        client = value['data']['runner_client']
        assert client['submission'] == 'invoked' and client['transport_admission'] == 'accepted'
        assert client['transport']['terminal'] == 'xpc_error' and value['data']['runner_result'] is None
        assert value['result']['normalized_outcome'] == 'xpc_error', value
        self.one_execution(name)
        assert len(self.events(name, 'request_received')) == 1, 'execution was replayed'

    def lost_capture(self):
        name = 'f2-control-lost-helper-capture'
        launched = self.launch(name, copied_client=True)
        trace = self.resource / 'client-trace'
        ready = wait_for(lambda: list(trace.glob('*-capture_ready.json')), 'helper capture gate', timeout=20)
        assert len(ready) == 1
        event = json.loads(ready[0].read_text())
        assert event['submission'] == 'invoked' and event['terminal'] == 'runner_reply'
        self.one_execution(name)
        pid = event['pid']; before = process_identity(pid); path = executable_path(pid); after = process_identity(pid)
        assert before['observed'] and after['observed'] and generation(before) == generation(after)
        assert path == str(self.app / CLIENT), ('not the owned instrumented client', path)
        save(self.out / 'helper-loss.json', dict(event=event, before=before, after=after, executable=path,
            signal=int(signal.SIGKILL), positive_execution_boundary=self.event(name, 'admission_claimed')))
        os.kill(pid, signal.SIGKILL)
        value = self.receive(launched)
        self.gone(before, 'instrumented helper generation exited')
        client = value['data']['runner_client']
        assert client['transport_admission'] == 'missing' and client['submission'] == 'unknown', client
        assert value['data']['runner_result'] is None and value['result']['normalized_outcome'] == 'missing_runner_client'
        assert len(list(trace.glob('*-client_started.json'))) == 1, 'controller relaunched helper'
        assert len(list(trace.glob('*-selector_invoked.json'))) == 1, 'helper repeated execution selector'
        assert len(self.events(name, 'request_received')) == 1
        self.one_execution(name)
        shutil.copytree(trace, self.out / 'client-trace')

    def compatibility(self, executable, old_client):
        name = 'f2-control-' + ('old-client' if old_client else 'old-control')
        if old_client:
            driver = Driver(self, executable); driver.open(legacy=True)
            _, _, path = self.prepare(name)
            driver.send('legacy_submit', 'old-client', request=str(path))
            driver.event('old-client', 'legacy_invoked')
            wait_for(lambda: [e for e in driver.events() if e['event'] in
                ('rpc_error', 'connection_invalidated', 'connection_interrupted')], 'legacy selector refusal', timeout=10)
            assert not [e for e in driver.events() if e['event'] == 'legacy_reply']
            self.no_execution(name)
            peers = [e for e in self.events(kind='connection_accepted') if e.get('client_pid') == driver.process.pid]
            assert peers, 'legacy caller never reached the owned host'
            for peer in peers:
                self.no_host_execution(peer['host'])
            # A current call proves the same owned endpoint remains usable.
            recovery = 'f2-control-current-after-old'
            value = self.receive(self.launch(recovery))
            assert value['result']['ok'], value
            self.one_execution(recovery)
        else:
            value = self.receive(self.launch(name))
            client = value['data']['runner_client']
            assert client['submission'] == 'not_invoked' and client['transport']['terminal'] == 'protocol_error'
            assert client['transport']['error']['reason'] == 'unsupported_protocol'
            assert value['data']['runner_result'] is None
            assert self.events(kind='legacy_protocol_control_substituted')
            self.no_execution(name)
            for peer in self.events(kind='legacy_protocol_control_substituted'):
                self.no_host_execution(peer['host'])

    def cleanup(self):
        # A killed gated client has no capture; preserve its independent trace
        # even on an assertion failure before the normal copy was reached.
        trace = self.resource / 'client-trace'
        if trace.exists():
            (trace / 'allow').write_bytes(b'cleanup only\n')
            shutil.copytree(trace, self.out / 'client-trace', dirs_exist_ok=True)
        super().cleanup()


def main():
    pw, app, out, scratch, identity = sys.argv[1:]
    pw, app, out, scratch = map(lambda value: Path(value).resolve(), (pw, app, out, scratch))
    assert scratch == Path(os.environ['PW_TEST_SCRATCH']).resolve()
    assert pw == app / 'Contents/MacOS/policy-witness'
    original = inventory(app); save(out / 'original-app-before.json', original)
    host = build_host(scratch, out / 'build')
    driver, copied_client = build_callers(app, scratch, out / 'callers', identity)
    cases = ['credentials', 'expired', 'abandoned', 'lost_grant', 'lost_occupied',
             'lost_execution', 'lost_capture', 'old_client', 'old_control']
    rows, failures = [], []
    for name in cases:
        folder = out / name; folder.mkdir()
        resource = Path(tempfile.mkdtemp(prefix='pw-f2-control-', dir='/private/tmp'))
        arrangement = ReservationArrangement(name, pw, folder, resource)
        gates = {'reservation': ['exit']} if name in ('credentials', 'expired', 'abandoned') else (
            {'reservation': ['granted'] if name == 'lost_grant' else ['occupied', 'exit']} if name in ('lost_grant', 'lost_occupied') else
            {'f2-control-lost-execution': ['reply']} if name == 'lost_execution' else
            {'reservation': ['legacy_control']} if name == 'old_control' else {})
        row = dict(arrangement=name, complete=False, cleanup_verified=False, resource=str(resource))
        try:
            candidate = custom_app(app, host, scratch, folder, identity, arrangement.trace, gates,
                                   client=copied_client if name == 'lost_capture' else None)
            arrangement.configure(candidate, identity); arrangement.arm()
            if name == 'credentials': arrangement.credentials(driver)
            elif name in ('expired', 'abandoned'): arrangement.unused_reservation(driver, name == 'expired')
            elif name in ('lost_grant', 'lost_occupied'): arrangement.lost_control(driver, name == 'lost_occupied')
            elif name == 'lost_execution': arrangement.lost_execution()
            elif name == 'lost_capture': arrangement.lost_capture()
            else: arrangement.compatibility(driver, name == 'old_client')
            row['complete'] = True
        except BaseException as error:
            row['error'] = repr(error); (folder / 'failure.txt').write_text(traceback.format_exc())
            failures.append(name + ': ' + repr(error))
        finally:
            try:
                arrangement.cleanup(); row['cleanup_verified'] = True
            except BaseException as error:
                row['cleanup_error'] = repr(error); (folder / 'cleanup-failure.txt').write_text(traceback.format_exc())
                failures.append(name + ' cleanup: ' + repr(error))
            rows.append(row)
            save(out / 'reservation-controls.json', dict(arrangements=rows, failures=failures,
                historical_failure_attributed=False, production_equivalence_claimed=False))
            assert inventory(app) == original, 'controls changed the selected app'
        if not row['cleanup_verified']:
            break
    save(out / 'original-app-after.json', inventory(app))
    assert not failures, '\n'.join(failures)


if __name__ == '__main__':
    main()

