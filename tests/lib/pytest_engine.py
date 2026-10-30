"""Pinned pytest entry point. Collection is read-only until PW releases eligibility."""
import json
import os
from pathlib import Path
import socket
import sys

from pytest_packages import target
from pytest_support import append, digest, write
from pytest_wire import send, receive

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
        path = self.artifacts / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        write(path, value)

    def command(self, argv, artifacts, timeout):
        send(PEER, dict(kind='command', item=self.plugin.current, argv=list(map(str, argv)),
                        artifacts=str(artifacts), timeout=timeout))
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


class Journal:
    out = None
    current = None
    operations = None

    def pytest_configure(self, config):
        config.addinivalue_line('markers', 'pw_id(name): stable PolicyWitness variant identity')

    def pytest_collection_finish(self, session):
        if session.testsfailed:
            send(PEER, dict(kind='collection_error', error='pytest collection failed'))
            return
        items = []
        for item in session.items:
            markers = list(item.iter_markers('pw_id'))
            if len(markers) != 1 or len(markers[0].args) != 1:
                raise ValueError('exactly one stable pw_id required: ' + item.nodeid)
            suffix = markers[0].args[0]
            if not isinstance(suffix, str) or not suffix or any(c in suffix for c in '/:\n'):
                raise ValueError('invalid pw_id')
            item.pw_id = FAMILY + '::' + suffix
            items.append(dict(id=item.pw_id, nodeid=item.nodeid))
        if not items or len({r['id'] for r in items}) != len(items):
            raise ValueError('empty or duplicate stable IDs')
        source_paths = [MODULE, 'tests/pytest.ini', 'tests/requirements-pytest.lock',
                        'tests/lib/pytest_engine.py', 'tests/lib/pytest_wire.py',
                        str(Path(MODULE).with_name('exec_domain.py')),
                        str(Path(MODULE).with_name('check_exec_evidence.py'))]
        manifest = dict(schema_version=1, family=FAMILY, items=items, pytest=pytest.__version__,
                        python=sys.version, sources={p:digest(ROOT / p) for p in source_paths},
                        configuration=['--capture=fd', '--import-mode=importlib', 'no external plugins', 'no cache'])
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

    @pytest.fixture(scope='session')
    def pw_equipment(self):
        return Equipment(self)

    def pytest_runtest_logstart(self, nodeid, location):
        self.current = next(i['id'] for i in self.manifest_items if i['nodeid'] == nodeid)
        self.operations = []
        append(self.out / 'phases.jsonl', dict(kind='item_start', id=self.current))

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        report = (yield).get_result()
        append(self.out / 'phases.jsonl', dict(kind='phase', id=item.pw_id, phase=report.when,
               outcome=report.outcome, duration=report.duration, diagnostic=str(report.longrepr) if report.longrepr else None,
               captured=[dict(name=n, text=t) for n,t in report.sections], operations=list(self.operations)))

    def pytest_runtest_logfinish(self, nodeid, location):
        append(self.out / 'phases.jsonl', dict(kind='item_finish', id=self.current))

    def pytest_sessionfinish(self, session, exitstatus):
        if self.out:
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
