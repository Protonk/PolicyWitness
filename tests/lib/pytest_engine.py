"""Pinned pytest entry point. Collection is read-only until PW releases eligibility."""
import json
import os
from pathlib import Path
import socket
import sys

from pytest_packages import target
from pytest_support import append, contained, digest, write
from pytest_wire import send, receive
import outcomes
from receipts import InputRecorder

ROOT, FAMILY, MODULE = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
PEER = socket.socket(fileno=int(sys.argv[4]))
sys.path.insert(0, str(target(ROOT)[0]))
sys.path.insert(0, str((ROOT / MODULE).parent))
import pytest


class Equipment:
    def __init__(self, plugin):
        self.plugin = plugin
        self.completed_operations = []
        self.root = ROOT
        self.artifacts = plugin.out / 'artifacts'
        self.artifacts.mkdir(exist_ok=True)

    def publish(self, relative, value):
        path = contained(self.artifacts, self.artifacts / relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        write(path, value)
        return self.reference(path)

    def reference(self, path):
        path = contained(self.plugin.out, Path(path))
        return outcomes.file_reference(path.relative_to(self.plugin.out).as_posix(), path.read_bytes())

    def command(self, argv, artifacts, timeout, *, cwd=None, env=None):
        request = dict(kind='command', item=self.plugin.current, argv=list(map(str, argv)),
                       artifacts=str(artifacts), timeout=timeout)
        if cwd is not None:
            request['cwd'] = str(Path(cwd).absolute())
        if env is not None:
            request['environment'] = dict(env)
        send(PEER, request)
        reply = receive(PEER)
        if reply.get('kind') != 'command_result':
            raise RuntimeError('command owner unavailable: ' + str(reply))
        if reply.get('error'):
            raise RuntimeError(reply['error'])
        self.completed_operations.append(reply['result']['operation_id'])
        self.observe([reply['result']['operation_id']])
        if reply['result']['timed_out'] or reply['result']['cancelled']:
            raise AssertionError('native command timed out or was cancelled; receipt: ' + reply['result']['record'])
        if reply['result'].get('never_launched'):
            raise AssertionError('native command was not launched: ' + str(reply['result'].get('launch_error'))
                                 + '; receipt: ' + reply['result']['record'])
        if reply['result'].get('group_signalled_after_leader_exit'):
            raise AssertionError('PW signalled process-group members that remained after the native command exited; receipt: '
                                 + reply['result']['record'])
        return reply['result']

    def observe(self, operations):
        for operation in operations:
            if operation not in self.plugin.operations:
                self.plugin.operations.append(operation)

    def observation(self, name, facts, evidence):
        self.plugin.record('observations', dict(id=name, facts=facts, evidence=evidence))

    def judgment(self, name, favorable, detail=''):
        if type(favorable) is not bool:
            raise ValueError('a judgment requires an explicit boolean result')
        specification = self.plugin.specification()
        declarations = [row for row in specification['judgments'] if row['id'] == name]
        if len(declarations) != 1:
            raise ValueError('judgment was not declared before execution: ' + name)
        self.plugin.record('judgments', dict(**declarations[0], result='favorable' if favorable else 'unfavorable', detail=detail))

    def failure(self, kind, message, evidence=None):
        self.plugin.record('failures', dict(kind=kind, message=message, evidence=evidence or []))


class Journal:
    out = None
    current = None
    operations = None

    def pytest_configure(self, config):
        config.addinivalue_line('markers', 'pw_id(name): stable PolicyWitness variant identity')
        config.addinivalue_line('markers', 'pw_contract(specification): promised observations and preselected judgment authority')
        config.addinivalue_line('markers', 'pw_commands(scope): none or recorded commands; ordinary pytest assertions remain enforced')

    def pytest_collection_finish(self, session):
        if session.testsfailed:
            send(PEER, dict(kind='collection_error', error='pytest collection failed'))
            return
        items, dependencies = [], set()
        for item in session.items:
            markers = list(item.iter_markers('pw_id'))
            if len(markers) != 1 or len(markers[0].args) != 1:
                raise ValueError('exactly one stable pw_id required: ' + item.nodeid)
            suffix = markers[0].args[0]
            if not isinstance(suffix, str) or not suffix or any(c in suffix for c in '/:\n'):
                raise ValueError('invalid pw_id')
            item.pw_id = FAMILY + '::' + suffix
            declaration = dict(id=item.pw_id, nodeid=item.nodeid)
            contracts = list(item.iter_markers('pw_contract'))
            if contracts:
                if len(contracts) != 1 or len(contracts[0].args) != 1 or contracts[0].kwargs:
                    raise ValueError('exactly one pw_contract specification required')
                specification = json.loads(json.dumps(contracts[0].args[0], allow_nan=False))
                outcomes.validate_spec(specification)
                if 'commands' not in specification:
                    raise ValueError('pytest observation specifies none or recorded commands')
                declaration['outcome_contract'] = specification
            scopes = list(item.iter_markers('pw_commands'))
            if scopes:
                if len(scopes) != 1 or len(scopes[0].args) != 1 or scopes[0].kwargs or scopes[0].args[0] not in ('none', 'recorded'):
                    raise ValueError('exactly one pw_commands none/recorded scope required')
                declaration['command_scope'] = scopes[0].args[0]
                if 'outcome_contract' in declaration and declaration['command_scope'] != declaration['outcome_contract']['commands']:
                    raise ValueError('command scope contradicts outcome specification')
            items.append(declaration)
            for name in getattr(item.module, 'PW_SOURCE_FILES', ()):
                if not isinstance(name, str) or not name:
                    raise ValueError('invalid declared source dependency')
                path = contained(ROOT, ROOT / name)
                dependencies.add(path.relative_to(ROOT).as_posix())
        if not items or len({r['id'] for r in items}) != len(items):
            raise ValueError('empty or duplicate stable IDs')
        source_paths = [MODULE, 'tests/pytest.ini', 'tests/requirements-pytest.lock',
                        'tests/lib/pytest_engine.py', 'tests/lib/pytest_wire.py',
                        'tests/lib/outcomes.py', 'tests/lib/receipts.py', *sorted(dependencies)]
        manifest = dict(schema_version=2 if any('outcome_contract' in row or 'command_scope' in row for row in items) else 1,
                        family=FAMILY, items=items, pytest=pytest.__version__,
                        python=sys.version, sources={p:digest(ROOT / p) for p in source_paths},
                        configuration=['--capture=fd', '--import-mode=importlib', 'no external plugins', 'no cache'])
        self.manifest, self.item_specs, self.accounts, self.inputs = manifest, {row['id']:row for row in items}, {}, {}
        send(PEER, dict(kind='collected', manifest=manifest))
        message = receive(PEER)
        if message['kind'] == 'stop':
            pytest.exit('read-only collection complete', returncode=0)
        if message['kind'] != 'eligible':
            raise ValueError('missing PW eligibility')
        data, descriptors, _, _ = socket.recv_fds(PEER, 1, 1)
        if data != b'L' or len(descriptors) != 1:
            raise ValueError('missing checkout hold')
        self.lock_fd = descriptors[0]
        self.out = Path(message['out'])
        write(self.out / 'environment.json', dict(executable=sys.executable, python=sys.version,
            pythoncoercelocale=os.environ.get('PYTHONCOERCECLOCALE'), disable_plugin_autoload=os.environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD') == '1',
            sys_path=sys.path, lock_identity=[os.fstat(self.lock_fd).st_dev,os.fstat(self.lock_fd).st_ino],
            capture='fd', dont_write_bytecode=sys.dont_write_bytecode, site='site' in sys.modules))
        append(self.out / 'phases.jsonl', dict(kind='session_start', family=FAMILY, items=[r['id'] for r in items]))
        send(PEER, dict(kind='started'))

    def specification(self):
        spec = self.item_specs[self.current].get('outcome_contract')
        if spec is None:
            raise ValueError('explicit observation/judgment requires a collected pw_contract')
        return spec

    def record(self, role, record):
        self.specification()
        # Check serializability before publishing the durable prefix.
        record = json.loads(json.dumps(record, allow_nan=False))
        self.accounts[self.current][role].append(record)
        append(self.out / 'phases.jsonl', dict(kind='outcome', id=self.current, role=role, record=record))

    @pytest.fixture(scope='session')
    def pw_equipment(self):
        return Equipment(self)

    @pytest.fixture
    def pw_inputs(self):
        if self.current not in self.inputs:
            raise ValueError('pw_inputs requires collected command scope or outcome specification')
        recorder = self.inputs[self.current]
        yield recorder
        recorder.capture_tracked('before fixture cleanup')

    def pytest_runtest_logstart(self, nodeid, location):
        self.current = next(i['id'] for i in self.manifest_items if i['nodeid'] == nodeid)
        self.operations = []
        append(self.out / 'phases.jsonl', dict(kind='item_start', id=self.current))
        declaration = self.item_specs[self.current]
        if 'outcome_contract' in declaration:
            self.accounts[self.current] = outcomes.empty_account()
        if 'outcome_contract' in declaration or 'command_scope' in declaration:
            index = next(n for n, row in enumerate(self.manifest['items']) if row['id'] == self.current)
            recorder = InputRecorder(self.out / 'artifacts/inputs' / f'{index:04}.json', self.current)
            snapshot = recorder.capture(ROOT, list(self.manifest['sources']), 'collected sources')
            source_path = recorder.path.parent / snapshot
            recorder.source_snapshot = outcomes.file_reference(source_path.relative_to(self.out).as_posix(), source_path.read_bytes())
            self.inputs[self.current] = recorder

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        report = (yield).get_result()
        extra = {}
        if item.pw_id in self.inputs:
            recorder = self.inputs[item.pw_id]
            recorder.capture_tracked('after ' + report.when)
            extra = dict(inputs=recorder.references(self.out), source_snapshot=recorder.source_snapshot)
            if item.pw_id in self.accounts:
                extra['outcome_account'] = self.accounts[item.pw_id]
        append(self.out / 'phases.jsonl', dict(kind='phase', id=item.pw_id, phase=report.when,
               outcome=report.outcome, duration=report.duration, diagnostic=str(report.longrepr) if report.longrepr else None,
               captured=[dict(name=n, text=t) for n,t in report.sections], operations=list(self.operations), **extra))

    def pytest_runtest_logfinish(self, nodeid, location):
        append(self.out / 'phases.jsonl', dict(kind='item_finish', id=self.current))

    def pytest_sessionfinish(self, session, exitstatus):
        if self.out:
            if self.manifest['schema_version'] == 2:
                actual = {name:digest(ROOT / name) for name in self.manifest['sources']}
                append(self.out / 'phases.jsonl', dict(kind='source_integrity', sources=actual))
            append(self.out / 'phases.jsonl', dict(kind='session_finish', exitstatus=int(exitstatus)))

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        # No selection or ordering here: identity lookup follows pytest's collection.
        self.manifest_items = [dict(id=FAMILY + '::' + i.get_closest_marker('pw_id').args[0], nodeid=i.nodeid)
                               for i in items if i.get_closest_marker('pw_id')]


if __name__ == '__main__':
    try:
        raise SystemExit(pytest.main(['-c', str(ROOT / 'tests/pytest.ini'), str(ROOT / MODULE)], plugins=[Journal()]))
    finally:
        PEER.close()
