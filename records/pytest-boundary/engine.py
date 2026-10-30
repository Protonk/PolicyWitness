"""Pytest owns collection, selection, fixture order and ordinary execution."""
import json
import os
from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pytest
from common import append, write


class Journal:
    def __init__(self, channel):
        self.channel, self.out = channel, None

    def pytest_collection_finish(self, session):
        if session.testsfailed:
            return
        ids = [item.nodeid for item in session.items]
        self.channel.send(json.dumps(dict(op='selection', ids=ids, preview=session.config.option.collectonly)).encode())
        data, fds, _, _ = socket.recv_fds(self.channel, 65536, 2)
        reply = json.loads(data)
        if reply['op'] != 'eligible':
            pytest.exit(reply.get('reason', 'publication refused'), returncode=2)
        if session.config.option.collectonly:
            return
        if len(fds) != 2:
            raise RuntimeError('missing lock handoff')
        os.environ.update(reply['env'])
        os.environ['PW_CHECKOUT_LOCK_FD'] = str(fds[0])
        os.environ['PW_CHECKOUT_LOCK_CHANNEL'] = str(fds[1])
        self.out = Path(reply['out'])
        write(self.out / 'engine_configuration.json', dict(pytest=pytest.__version__, python=sys.version,
              capture=session.config.option.capture, optimize=sys.flags.optimize,
              external_plugins=[d.project_name for _, d in session.config.pluginmanager.list_plugin_distinfo()],
              environment={k:os.environ.get(k) for k in ('PYTEST_ADDOPTS','PYTHONPATH','PYTEST_DISABLE_PLUGIN_AUTOLOAD')}))
        session.config.boundary = self

    def pytest_runtest_logstart(self, nodeid, location):
        append(self.out / 'reports.jsonl', dict(kind='start', nodeid=nodeid))

    def pytest_runtest_logreport(self, report):
        append(self.out / 'reports.jsonl', dict(kind='report', nodeid=report.nodeid,
               when=report.when, outcome=report.outcome, wasxfail=getattr(report, 'wasxfail', None),
               longrepr=str(report.longrepr) if report.longrepr else '',
               stdout=report.capstdout, stderr=report.capstderr))

    def pytest_sessionfinish(self, session, exitstatus):
        if self.out is not None:
            append(self.out / 'reports.jsonl', dict(kind='session_finish', exitstatus=int(exitstatus)))

    def acquire(self, nodeid):
        self.channel.send(json.dumps(dict(op='acquire', nodeid=nodeid)).encode())
        response = json.loads(self.channel.recv(65536))
        if response['op'] != 'acquired':
            raise RuntimeError(response)
        return response


if __name__ == '__main__':
    assert pytest.__version__ == '9.0.2', pytest.__version__
    channel = socket.socket(fileno=int(sys.argv[1]))
    channel.settimeout(60)
    raise SystemExit(pytest.main(sys.argv[2:], plugins=[Journal(channel)]))
