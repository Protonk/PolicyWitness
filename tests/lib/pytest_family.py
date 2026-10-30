"""Family adapter: identity reconciliation and operational ownership, never item scheduling."""
import collections
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time

import pytest_packages
from pytest_resources import Command, snapshot
from pytest_support import append, contained, read, rows, value_digest, write
from pytest_wire import send, receive


def account(manifest, stream, returncode, ownership, operations):
    items = {r['id']:dict(**r, phases={}, outcome='incomplete', started=False, finished=False) for r in manifest['items']}
    errors, opened, session, finish = [], None, False, False
    try:
        for row in rows(stream):
            kind = row['kind']
            if kind == 'session_start':
                if session or row['items'] != list(items):
                    raise ValueError('invalid session start')
                session = True
            elif kind == 'session_finish':
                if not session or finish or opened or row['exitstatus'] != returncode:
                    raise ValueError('invalid session finish')
                finish = True
            else:
                item = items[row['id']]
                if not session or finish:
                    raise ValueError('item evidence outside session')
                if kind == 'item_start':
                    if opened or item['started']:
                        raise ValueError('duplicate or overlapping item')
                    opened = row['id']; item['started'] = True
                elif kind == 'phase':
                    phase = row['phase']
                    if opened != row['id'] or phase not in ('setup', 'call', 'teardown') or phase in item['phases']:
                        raise ValueError('invalid/duplicate phase')
                    prior = list(item['phases'])
                    expected = ['setup'] if not prior else ['call', 'teardown'] if prior == ['setup'] else ['teardown'] if prior == ['setup', 'call'] else []
                    if phase not in expected or row['outcome'] not in ('passed', 'failed', 'skipped'):
                        raise ValueError('contradictory phase sequence')
                    if phase == 'call' and item['phases']['setup']['outcome'] != 'passed':
                        raise ValueError('call after unsuccessful setup')
                    item['phases'][phase] = row
                elif kind == 'item_finish':
                    if opened != row['id'] or 'teardown' not in item['phases']:
                        raise ValueError('finish without teardown')
                    if item['phases']['setup']['outcome'] == 'passed' and 'call' not in item['phases']:
                        raise ValueError('passing setup without body')
                    item['finished'] = True; opened = None
                    item['outcome'] = 'passed' if all(p['outcome'] == 'passed' for p in item['phases'].values()) else 'failed'
                else:
                    raise ValueError('unknown phase event')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    if not finish or not all(i['finished'] for i in items.values()):
        errors.append('incomplete execution accounting; valid earlier evidence retained')
    if not ownership['closed']:
        errors.append('resource ownership unresolved; see ownership.json')
    declared = {op for i in items.values() for p in i['phases'].values() for op in p.get('operations', [])}
    if declared != set(operations):
        errors.append('command receipts and phase operation references differ')
    complete = finish and all(i['finished'] for i in items.values()) and not errors
    return dict(schema_version=1, family=manifest['family'], manifest_digest=value_digest(manifest),
        execution_state='started' if session else 'unknown', accounting_state='complete' if complete else 'incomplete',
        ok=complete and returncode == 0 and all(i['outcome'] == 'passed' for i in items.values()),
        items=list(items.values()), operations=operations, errors=errors, engine_returncode=returncode)


class Collector:
    def __init__(self, root, case):
        self.root, self.case = root, case
        pytest_packages.target(root)
        self.peer, child = socket.socketpair()
        self.log = tempfile.TemporaryFile()
        environment = {k:v for k,v in os.environ.items() if not k.startswith(('PYTEST', 'PYTHON', 'PW_CHECKOUT', 'PW_TEST_'))}
        environment['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        self.process = subprocess.Popen([sys.executable, '-B', '-S', str(root / 'tests/lib/pytest_engine.py'),
            str(root), case['id'], case['module'], str(child.fileno())], cwd=root, env=environment,
            stdin=subprocess.DEVNULL, stdout=self.log, stderr=subprocess.STDOUT, pass_fds=(child.fileno(),), start_new_session=True)
        child.close()
        self.peer.settimeout(30)
        try:
            message = receive(self.peer)
            if message['kind'] != 'collected':
                raise ValueError(str(message))
            manifest = message['manifest']
            ids = [r['id'] for r in manifest['items']]
            if manifest['family'] != case['id'] or not ids or len(ids) != len(set(ids)) or any(not i.startswith(case['id'] + '::') for i in ids):
                raise ValueError('invalid family identity manifest')
            self.manifest = manifest
            self.peer.settimeout(None)
        except BaseException:
            self.stop()
            self.log.seek(0)
            diagnostic = self.log.read().decode(errors='replace')
            self.log.close()
            raise ValueError('pytest collection failed:\n' + diagnostic)

    def stop(self):
        if self.process.poll() is None:
            try:
                send(self.peer, dict(kind='stop'))
                self.process.wait(timeout=3)
            except (OSError, EOFError, subprocess.TimeoutExpired):
                self.process.kill(); self.process.wait()
        self.peer.close()

    def execute(self, out, run_id, scope):
        family_out = out / 'suites' / self.case['id']
        family_out.mkdir(parents=True)
        write(family_out / 'selection.json', self.manifest)
        command, operations, errors, started, interrupted = None, [], [], False, False
        write(family_out / 'eligibility.json', dict(run_id=run_id, lock_identity=list(scope.identity), nonce=scope.nonce))
        try:
            send(self.peer, dict(kind='eligible', out=str(family_out)))
            socket.send_fds(self.peer, [b'L'], [scope.fd])
            while self.process.poll() is None:
                if command and command.poll() is not None:
                    result = command.finish()
                    append(family_out / 'operations.jsonl', dict(kind='settled', **result))
                    send(self.peer, dict(kind='command_result', result=result))
                    command = None
                if self.peer in select.select([self.peer], [], [], .02)[0]:
                    self.peer.settimeout(5)
                    try:
                        message = receive(self.peer)
                    finally:
                        self.peer.settimeout(None)
                    if message['kind'] == 'started':
                        started = True
                    elif message['kind'] == 'command':
                        if command or not started or message['item'] not in {r['id'] for r in self.manifest['items']}:
                            raise ValueError('invalid command ownership request')
                        artifacts = contained(family_out / 'artifacts', message['artifacts'])
                        command = Command(self.root, out, run_id, self.case['id'], message['item'],
                                          message['argv'], artifacts, message['timeout'], scope, self.process.pid)
                        operation = command.path.parent.name
                        operations.append(operation)
                        append(family_out / 'operations.jsonl', dict(kind='registered', operation_id=operation,
                               item=message['item'], artifacts=str(artifacts.relative_to(out))))
                    else:
                        raise ValueError('unexpected engine message')
        except KeyboardInterrupt:
            interrupted = True
            errors.append('execution interrupted')
        except (OSError, EOFError, ValueError, KeyError, TypeError) as exc:
            # EOF/reset is not a verdict. Reap, then read the durable prefix.
            if not isinstance(exc, EOFError):
                errors.append(str(exc))
        finally:
            previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                if command:
                    command.cancel()
                if self.process.poll() is None:
                    if interrupted or errors or command:
                        self.process.send_signal(signal.SIGINT)
                    try:
                        self.process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        self.process.kill(); self.process.wait()
                if command:
                    try:
                        result = command.finish()
                        append(family_out / 'operations.jsonl', dict(kind='settled', **result))
                    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                        errors.append(str(exc))
                self.peer.close()
                self.log.seek(0)
                (family_out / 'pytest.txt').write_bytes(self.log.read())
                self.log.close()
                ownership = snapshot(self.root, run_id)
                write(family_out / 'ownership.json', ownership)
                family = account(self.manifest, family_out / 'phases.jsonl', self.process.returncode, ownership, operations)
                if started:
                    family['execution_state'] = 'started'
                family['errors'].extend(errors)
                family['ok'] &= not errors
                write(family_out / 'family.json', family)
                display(family_out, family)
            finally:
                signal.signal(signal.SIGINT, previous)
        return family, interrupted


def display(directory, family):
    lines = [f"FAMILY {family['family']}: {'PASS' if family['ok'] else 'FAIL'}; execution={family['execution_state']} accounting={family['accounting_state']}"]
    for item in family['items']:
        phases = ', '.join(f'{k}={v["outcome"]}' for k,v in item['phases'].items())
        lines.append(f"  {item['id']}: {item['outcome']} ({phases or 'no phase evidence'})")
        for phase in item['phases'].values():
            if phase['diagnostic']:
                lines.append(f"    {phase['phase']}: {phase['diagnostic']}")
        suffix = item['id'].split('::', 1)[1]
        lines.append(f'    Native evidence: artifacts/{suffix}/; phases.jsonl; pytest.txt')
    baseline = directory / 'artifacts/baseline.json'
    if baseline.exists() and not read(baseline)['ok']:
        lines.append('SHARED BASELINE: artifacts/baseline.json; production observation retained. Dependent setup failures did not run their bodies or submit mutations.')
    integrity = directory / 'artifacts/input-integrity.json'
    if integrity.exists() and not read(integrity)['ok']:
        lines.append('SHARED SESSION FINALIZER: input integrity uncertain for all family items; pytest attaches this to the last item teardown. Body outcomes survive; inspect each retained sources.json and input-integrity.json for applicability.')
    if not read(directory / 'ownership.json')['closed']:
        lines.append('OWNERSHIP UNRESOLVED: complete native observations remain readable; this is not a claim that their assertions failed. See ownership.json and the public recovery command.')
    lines.extend('ACCOUNT: ' + e for e in family['errors'])
    lines.append('Ownership: ownership.json; command receipts: operations.jsonl; manifest: selection.json')
    text = '\n'.join(lines) + '\n'
    (directory / 'summary.txt').write_text(text)
    print(text + f'Family report: {directory / "family.json"}', flush=True)
