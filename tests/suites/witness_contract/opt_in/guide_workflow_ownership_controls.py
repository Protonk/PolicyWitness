"""Constructed ownership/command faults; the guide case owns native execution.

Use the existing fake OS tool and actual cleanup paths. Fixture teardown happens
only after preservation/removal observations; no real service is installed.
"""
import copy
import json
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import sys
from types import SimpleNamespace
from unittest import mock

import guide_workflows as gw
import session
from bundle import command, inventory, save


def refused(call):
    try:
        call()
    except (AssertionError, RuntimeError, ValueError):
        return
    raise AssertionError('ownership refusal control was accepted')


class Fixture:
    def __init__(self, out, name, home, *, external=False, installed=False, mode='success'):
        self.out = out / name
        self.out.mkdir(parents=True)
        self.app = self.out / 'Selected.app'
        (self.app / 'Contents/XPCServices/PWRunner.xpc').mkdir(parents=True)
        (self.app / 'source-marker').write_bytes(b'unchanged selected source')
        self.pw = self.app / 'Contents/MacOS/policy-witness'
        self.work = Path('/private/tmp') / ('pw-guide.' + secrets.token_hex(12))
        self.work.mkdir(mode=0o700)
        observed = self.work.stat()
        self.owner = dict(kind='guide_workflow', source_app=str(self.app), source_inventory=inventory(self.app),
            workspace=str(self.work), workspace_identity=[observed.st_dev, observed.st_ino],
            state_path=str(self.work / 'session.json'), receipt_path=str(self.out / 'session.json'),
            contract='test:fixture', invocations=[], command_uncertain=None, external=None, removed=False)
        gw.persist(self.owner, self.out)
        self.calls = []
        self.config = None
        if external:
            stage = self.work / ('runner.' + secrets.token_hex(6))
            stage.mkdir()
            service = f'com.policywitness.guide.{os.getuid()}.{stage.name}'
            session.adopt_guide(self.app, self.out / 'byoxpc-session.json', self.owner,
                                stage, stage / 'PWRunner.guide.xpc', service)
            self.nested = session.owner_object(self.out / 'byoxpc-session.json')
            bundle = Path(self.nested['bundle_path'])
            (bundle / 'Contents/MacOS').mkdir(parents=True)
            (bundle / 'Contents/MacOS/PWRunner').write_bytes(b'owned copied executable')
            record = dict(id='owned-id', service_name=service, scope='user', bundle_path=str(bundle))
            os_state = dict(loaded=installed, runners=[record] if installed else [], pending_cleanup=[])
            save(self.out / 'os.json', os_state)
            if installed:
                plist = Path(self.nested['plist_path'])
                assert plist.is_relative_to(home)
                plist.parent.mkdir(parents=True, exist_ok=True)
                plist.write_bytes(plistlib.dumps(dict(Label=service,
                    ProgramArguments=[str(bundle / 'Contents/MacOS/PWRunner')], MachServices={service: True})))
                self.nested.update(install_attempted=True, install_finished=True)
                session.persist_state(self.nested, self.out / 'byoxpc-session.json')
            self.config = dict(mode=mode, state=str(self.out / 'os.json'), receipts=str(self.out / 'fake-commands.jsonl'),
                out=str(self.out), ownership=str(self.out / 'byoxpc-session.json'), pw=str(self.pw),
                source=str(self.app / 'Contents/XPCServices/PWRunner.xpc'),
                default_registry=str(self.out / 'default-registry.json'), entitlements={}, unrelated={})
            save(self.out / 'fake-config.json', self.config)

    def invoke(self, out, argv, **kwargs):
        self.calls.append(list(map(str, argv)))
        assert self.config is not None, 'unexpected OS command in workspace-only control'
        return command(out, [sys.executable, '-B', '-S', gw.ROOT / 'tests/fixtures/byoxpc/tools.py',
                             self.out / 'fake-config.json', *argv], **kwargs)

    def cleanup(self, **kwargs):
        return gw.cleanup(self.pw, self.out, invoke=self.invoke, **kwargs)

    def dispose_constructed(self):
        # No real launchd or signing tool ran. This is fixture teardown after
        # observations, not a claim that the rejected cleanup succeeded.
        if self.work.exists():
            shutil.rmtree(self.work)


def check(out):
    out.mkdir()
    home = out / 'constructed-home'
    home.mkdir()
    fixtures, observations = [], []
    def make(name, **kwargs):
        value = Fixture(out, name, home, **kwargs)
        fixtures.append(value)
        return value
    try:
        with mock.patch.object(Path, 'home', return_value=home):
            # A repeated run cannot replace an interrupted owner or issue tools.
            f = make('existing-owner')
            original = (f.out / 'session.json').read_bytes()
            with mock.patch.object(gw, 'command') as launch:
                refused(lambda: gw.Workflow(f.app, 'identity', f.out))
                assert not launch.called
            assert (f.out / 'session.json').read_bytes() == original
            f.cleanup()
            observations.append('existing owner preserved before any guide command')

            f = make('dangling-auxiliary-owner')
            stage = f.work / 'runner.dangling'; stage.mkdir()
            receipt = f.out / 'byoxpc-session.json'
            foreign = f.out / 'foreign-not-created'
            receipt.symlink_to(foreign)
            before = (f.work / 'session.json').read_bytes()
            refused(lambda: session.adopt_guide(f.app, receipt, f.owner, stage,
                stage / 'PWRunner.guide.xpc', f'com.policywitness.guide.{os.getuid()}.{stage.name}'))
            assert not os.path.lexists(foreign) and receipt.is_symlink() and f.calls == []
            assert (f.work / 'session.json').read_bytes() == before and f.owner['external'] is None
            assert not any(stage.iterdir()), 'refused adoption wrote staged or durable state'
            receipt.unlink(); f.cleanup()
            observations.append('dangling auxiliary receipt refuses before parent arming or foreign target creation')

            # Valid foreign owners remain foreign: exact immutable joins matter.
            a, b = make('owner-a', external=True), make('owner-b', external=True)
            marker = b.work / 'foreign-marker'; marker.write_bytes(b'foreign bytes')
            original = (a.out / 'byoxpc-session.json').read_bytes()
            (a.out / 'byoxpc-session.json').write_bytes((b.out / 'byoxpc-session.json').read_bytes())
            refused(a.cleanup)
            assert a.calls == [] and b.calls == [] and marker.read_bytes() == b'foreign bytes'
            assert a.work.is_dir() and b.work.is_dir()
            (a.out / 'byoxpc-session.json').write_bytes(original)
            # Recover only the recorded durable location when auxiliary output is lost.
            (a.out / 'byoxpc-session.json').unlink()
            a.cleanup(); assert not a.work.exists()
            b.cleanup(); assert not b.work.exists()
            observations.append('valid foreign nested owner refused; missing auxiliary owner recovered from exact durable path')

            for mode in ('foreign-state-path', 'changed-identity', 'symlink-owner', 'guide-registry'):
                f = make(mode, external=True)
                marker = f.out / 'foreign-marker'; marker.write_bytes(b'untouched')
                if mode == 'guide-registry':
                    original = (f.out / 'byoxpc-session.json').read_bytes()
                    bad = json.loads(original)
                    foreign = f.out / bad['service_name'] / 'runners.json'
                    foreign.parent.mkdir(); foreign.write_bytes(b'{"runners":[]}')
                    lock = foreign.with_suffix('.json.lock'); lock.write_bytes(b'foreign lock')
                    bad['registry_path'] = str(foreign)
                    session.persist_state(bad, f.out / 'byoxpc-session.json')
                    refused(lambda: session.cleanup(f.pw, f.out / 'byoxpc-session.json', invoke=f.invoke))
                    assert foreign.read_bytes() == b'{"runners":[]}' and lock.read_bytes() == b'foreign lock'
                    session.persist_state(json.loads(original), f.out / 'byoxpc-session.json')
                else:
                    durable = f.work / 'session.json'; original = durable.read_bytes()
                    bad = json.loads(original)
                    if mode == 'foreign-state-path': bad['state_path'] = str(marker)
                    if mode == 'changed-identity': bad['workspace_identity'][1] += 1
                    if mode == 'symlink-owner':
                        durable.unlink(); durable.symlink_to(marker)
                    else: save(durable, bad)
                    refused(f.cleanup)
                    assert marker.read_bytes() == b'untouched'
                    if durable.is_symlink(): durable.unlink()
                    durable.write_bytes(original)
                assert f.calls == [] and f.work.exists()
                f.cleanup()
            observations.append('foreign path, changed inode, owner symlink and foreign registry refused before OS calls or foreign writes')

            # The durable journal may legitimately be newer than its artifact.
            f = make('durable-ahead', external=True)
            durable = session.owner_object(f.work / 'session.json')
            durable['command_uncertain'] = 'constructed lost capture'
            save(f.work / 'session.json', durable)
            (f.work / 'effect').write_bytes(b'latest journal protects this effect')
            refused(f.cleanup)
            assert f.calls == [] and (f.work / 'effect').read_bytes() == b'latest journal protects this effect'
            assert Path(f.nested['staging']).exists()
            # The artifact now retains uncertainty; only the newer durable
            # checkpoint clears it. Cleanup must consult that latest journal.
            durable = session.owner_object(f.work / 'session.json')
            durable['command_uncertain'] = None
            save(f.work / 'session.json', durable)
            f.cleanup(); assert not f.work.exists()
            observations.append('newer durable uncertainty retains effects; newer cleared progress permits cleanup')

            # Simulated submission writes an independent effect then times out.
            f = make('uncertain-submission', external=True)
            request = f.work / 'run.json'; request.write_text('{}')
            w = gw.Workflow.__new__(gw.Workflow)
            w.out, w.work, w.state, w.number = f.out, f.work, f.owner, 0
            w.contract, w.env = 'test:fixture', dict(os.environ)
            w.state_file, w.values_file = f.out / 'shell-state.sh', f.out / 'shell-values'
            w.guide = SimpleNamespace(used=[])
            submissions = []
            def timeout(destination, argv, **kwargs):
                submissions.append(list(map(str, argv)))
                (f.work / 'effect').write_bytes(b'observed before lost capture')
                save(f.out / 'submission-receipt.json', dict(argv=submissions[-1], harness_timeout=True,
                     effect_hex=(f.work / 'effect').read_bytes().hex()))
                raise TimeoutError('constructed command interruption')
            with mock.patch.object(gw, 'command', side_effect=timeout):
                try: w.invoke('run', '"$PW" run "$PW_WORK/run.json"\n', 'result.json')
                except TimeoutError: pass
                else: raise AssertionError('interruption was accepted')
                refused(f.cleanup)
            assert len(submissions) == 1 and f.calls == []
            assert (f.work / 'effect').read_bytes() == b'observed before lost capture'
            assert f.work.exists() and Path(f.nested['staging']).exists()
            observations.append('one simulated submission/effect; interruption retains owners and issues no replay/removal')

            # Consumer admission is injected here; the actual worker-reap and
            # host-refusal cleanup predicates are exercised independently.
            for mode in ('reaped', 'not-reaped', 'admission-refusal'):
                f = make('disposition-' + mode, external=True)
                runner = dict(runner_subprocess=dict(pid=321, reaped=mode == 'reaped'))
                value = dict(kind='run', build=dict(contract='test:fixture'), data=dict(runner_result=runner))
                if mode == 'admission-refusal':
                    failure = dict(code='invalid_capture_nonce', path=['policy', 'capture_nonce'])
                    runner.update(normalized_outcome='bad_request', runner_subprocess=None, steps=[], phases=[], request_failure=failure)
                    value['data']['request_failure'] = failure
                    value['result'] = dict(normalized_outcome='bad_request')
                save(f.work / 'result.json', value)
                f.owner['invocations'] = [dict(name=mode, output='result.json', admission_refusal=mode == 'admission-refusal')]
                gw.persist(f.owner, f.out)
                with mock.patch.object(gw.consumer, 'validate', return_value=[]):
                    if mode == 'not-reaped':
                        refused(f.cleanup)
                        assert f.calls == [] and f.work.exists()
                    else:
                        f.cleanup(); assert not f.work.exists()
            observations.append('after injected consumer admission: actual reaped/host-refusal predicates permit cleanup; missing reap retains')

            # Independent fake OS states exercise each required absence, and
            # an incomplete install with/without recorded ownership.
            for mode in ('success', 'remove_keeps_service', 'remove_keeps_plist', 'remove_keeps_record', 'uncertain-record', 'uncertain-no-record'):
                f = make('absence-' + mode, external=True, installed=mode != 'uncertain-no-record', mode=mode)
                if mode.startswith('uncertain'):
                    nested = session.owner_object(f.out / 'byoxpc-session.json')
                    nested.update(install_attempted=True, install_finished=False)
                    session.persist_state(nested, f.out / 'byoxpc-session.json')
                if mode in ('success', 'uncertain-record'):
                    f.cleanup(); assert not f.work.exists()
                else:
                    refused(f.cleanup)
                    assert f.work.exists() and Path(f.nested['staging']).exists()
                    assert session.owner_object(f.out / 'session.json').get('cleanup_error')
                assert all(args[1] != 'run' and args[1:3] not in (['runner', 'verify'], ['runner', 'install']) for args in f.calls)
            observations.append('actual helper cleanup requires service, plist and registry absence; incomplete install requires recorded owner')

            # Deletion interruption keeps durable ownership and resumes after
            # machine cleanup, even when earlier output files are already gone.
            f = make('partial-deletion')
            (f.work / 'a-evidence').write_bytes(b'copied before deletion')
            (f.work / 'z-remaining').mkdir()
            (f.work / 'z-remaining/marker').write_bytes(b'remains')
            def interrupted(path):
                raise OSError('controlled interruption after earlier child deletion')
            refused(lambda: f.cleanup(remove_tree=interrupted))
            assert not (f.work / 'a-evidence').exists() and (f.work / 'session.json').is_file()
            assert (f.work / 'z-remaining/marker').read_bytes() == b'remains'
            latest = session.owner_object(f.work / 'session.json')
            assert latest['cleanup_verified'] and latest['cleanup_error']
            latest['invocations'] = [dict(name='already-verified', output='a-evidence', admission_refusal=False)]
            gw.persist(latest, f.out)
            with mock.patch.object(gw, 'safe_disposition', side_effect=AssertionError('re-read deleted output')):
                f.cleanup()
            assert not f.work.exists() and session.owner_object(f.out / 'session.json')['removed']
            f.cleanup()
            f = make('final-receipt-write-failure')
            original_save, failed = gw.save, []
            def fail_completed_receipt(path, value):
                if path == f.out / 'session.json' and value.get('removed') and not failed:
                    failed.append(True)
                    raise OSError('controlled final receipt write failure after rmdir')
                original_save(path, value)
            with mock.patch.object(gw, 'save', side_effect=fail_completed_receipt):
                refused(f.cleanup)
            assert failed and not f.work.exists()
            assert session.owner_object(f.out / 'session.json')['cleanup_error']
            f.cleanup()
            assert session.owner_object(f.out / 'session.json')['removed']
            assert 'cleanup_error' not in session.owner_object(f.out / 'session.json')
            f = make('absent-work-receipt-recovery')
            f.owner.update(cleanup_verified=True, cleanup_error='constructed post-deletion error')
            gw.persist(f.owner, f.out)
            shutil.rmtree(f.work)
            f.cleanup()
            assert session.owner_object(f.out / 'session.json')['removed']
            assert 'cleanup_error' not in session.owner_object(f.out / 'session.json')
            f = make('verified-empty-remainder')
            f.owner['cleanup_verified'] = True; gw.persist(f.owner, f.out)
            (f.work / 'session.json').unlink()
            f.cleanup(); assert not f.work.exists()
            f = make('unverified-missing-owner')
            (f.work / 'session.json').unlink(); (f.work / 'marker').write_bytes(b'retain')
            refused(f.cleanup); assert (f.work / 'marker').read_bytes() == b'retain'
            observations.append('durable-last partial deletion resumes without old outputs; exact verified empty remainder recovers; missing unverified owner retains')

            # The entry guard must stop before staging/sign/install/validate.
            for collection in ('runners', 'pending_cleanup'):
                calls = []
                w = gw.Workflow.__new__(gw.Workflow)
                w.guide = SimpleNamespace(fence=lambda *a: '"$PW" runner list\n"$PW" runner reconcile\n')
                w.run = lambda name, text: calls.append(name)
                rows = dict(runners=[], pending_cleanup=[])
                rows[collection] = [dict(id='foreign', service_name='foreign.runner')]
                w.envelope = lambda *a: dict(data=copy.deepcopy(rows))
                before = copy.deepcopy(rows)
                refused(w.external)
                assert calls == ['list-before', 'reconcile-before'] and rows == before
            observations.append('installed and pending foreign rows stop before any staging or mutating runner command')
    finally:
        for fixture in fixtures:
            fixture.dispose_constructed()
    save(out / 'controls.json', dict(scope='constructed command/reader inputs; real file operations and existing cleanup', observations=observations))
