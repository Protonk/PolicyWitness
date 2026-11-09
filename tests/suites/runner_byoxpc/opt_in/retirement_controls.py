"""Shared process, effect and cleanup equipment for reservation controls.

The registered reservation case owns current protocol instrumentation and
execution. These helpers retain source-independent process generations,
separate effect observations, durable resource ownership and verified cleanup.
"""
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
import contract
import build_context
import session
from artifact import inventory
from bundle import command, SERVICE
from neighbor_lab import save, process_identity, generation, executable_path, wait_for, ProcessWatch

HOST = SERVICE / 'Contents/MacOS/PWRunner'
WORKER = SERVICE / 'Contents/MacOS/pw-probe-runner'
FIXTURES = ROOT / 'tests/fixtures/byoxpc'


def replace_once(source, old, new):
    assert source.count(old) == 1, f'fixture anchor changed: {old!r}'
    return source.replace(old, new, 1)


def worker_host_source(source):
    # The child still blocks on policy delivery here. This records its kernel
    # generation before the real transfer; no worker code or ABI is changed.
    anchor = '        // The transfer calls (clock, write, poll) are one injection point: the'
    return replace_once(source, anchor, '        F2Trace.workerSpawned(pid)\n' + anchor)


def specimen(name, effect=None):
    plan = [] if effect is None else [dict(step_id='append_once',
        sandbox_check=dict(operation='process-exec*', filter=dict(kind='path', value='/bin/sh')),
        attempt=dict(kind='exec', action='spawn', target='/bin/sh',
                     args=['-c', 'printf x >> "$1"', 'effect', str(effect)]))]
    return dict(contract=build_context.candidate_contract(), specimen_id=name,
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
        # Separate the installation primer before the controlled arrangement.
        # No execution request is replayed by this shared helper.
        time.sleep(config.get('ThrottleInterval', 10) + 1)
        self.assert_known_exits('installation-primer')

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
        assert returned['outcome'] == 'finished' and returned['rc'] == 0, returned
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
