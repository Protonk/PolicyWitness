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
import outcomes
from pytest_resources import Command, snapshot
from pytest_support import append, contained, read, rows, value_digest, write
from pytest_wire import send, receive


def validate_inputs(phase, selection, load_bytes):
    outcomes.validate_evidence(phase.get('inputs'), load_bytes)
    source = phase.get('source_snapshot')
    outcomes.validate_evidence([source], load_bytes)
    if load_bytes is None:
        raise ValueError('source input snapshot has no byte reader')
    snapshot = outcomes.decode(load_bytes(source['path']))
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get('entries'), dict):
        raise ValueError('source input snapshot is not an entry map')
    if set(snapshot['entries']) != set(selection['sources']):
        raise ValueError('source input snapshot differs from collected source population')
    references = {row['path']:row['sha256'] for row in phase['inputs']}
    if references.get(source['path']) != source['sha256']:
        raise ValueError('source input snapshot missing from phase inputs')
    for name, digest in selection['sources'].items():
        entry = snapshot['entries'][name]
        if not isinstance(entry, dict) or entry.get('kind') != 'file' or references.get('artifacts/inputs/' + entry.get('blob', '')) != digest:
            raise ValueError('captured source bytes differ from collection: ' + name)


def account(manifest, stream, returncode, ownership, operations, load_bytes=None):
    """Interpret raw engine events under the collected declarations, retaining prefixes."""
    items = {r['id']:dict(**r, phases={}, outcome='incomplete', started=False, finished=False) for r in manifest['items']}
    explicit = manifest.get('schema_version', 1) == 2
    errors, opened, session, finish, source_integrity = [], None, False, False, False
    if load_bytes is None and isinstance(stream, Path):
        load_bytes = lambda name: contained(stream.parent, stream.parent / name).read_bytes()
    for item in items.values():
        if 'outcome_contract' in item:
            outcomes.validate_spec(item['outcome_contract'])
            item['outcome_account'] = outcomes.empty_account()
    try:
        if manifest.get('schema_version', 1) not in (1, 2):
            raise ValueError('unsupported family selection schema')
        if not explicit and any('outcome_contract' in item or 'command_scope' in item for item in items.values()):
            raise ValueError('legacy family cannot introduce outcome authority')
        if isinstance(stream, Path):
            events = (outcomes.decode(line) for line in stream.read_bytes().splitlines()) if explicit else rows(stream)
        else:
            events = stream
        for row in events:
            kind = row['kind']
            if kind == 'session_start':
                if session or row['items'] != list(items):
                    raise ValueError('invalid session start')
                session = True
            elif kind == 'source_integrity':
                if not explicit or not session or finish or opened or source_integrity or not all(i['finished'] for i in items.values()):
                    raise ValueError('unexpected source integrity observation')
                source_integrity = True
                if row['sources'] != manifest['sources']:
                    errors.append('collected source identity changed during execution; applicability uncertain for all family items')
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
                elif kind == 'outcome':
                    if opened != row['id'] or 'teardown' in item['phases'] or 'outcome_contract' not in item or row['role'] not in ('observations', 'judgments', 'failures'):
                        raise ValueError('outcome outside its declared experiment')
                    item['outcome_account'][row['role']].append(row['record'])
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
                    if explicit and (not isinstance(row.get('operations'), list)
                            or any(not isinstance(value, str) or not value for value in row['operations'])
                            or len(set(row['operations'])) != len(row['operations'])):
                        raise ValueError('phase requires an explicit distinct command reference list, including an empty list for pure items')
                    if 'outcome_contract' in item:
                        if row.get('outcome_account') != item['outcome_account']:
                            raise ValueError('phase outcome projection differs from its journal')
                    elif 'outcome_account' in row:
                        raise ValueError('undeclared phase outcome account')
                    if 'outcome_contract' in item or 'command_scope' in item:
                        validate_inputs(row, manifest, load_bytes)
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
    if explicit and not source_integrity:
        errors.append('source integrity observation missing')
    if not ownership['closed']:
        errors.append('resource ownership unresolved; see ownership.json')
    declared = {op for i in items.values() for p in i['phases'].values() for op in p.get('operations', [])}
    if declared != set(operations):
        errors.append('command receipts and phase operation references differ')
    for item in items.values():
        specification = item.get('outcome_contract')
        scope = specification.get('commands') if specification is not None else item.get('command_scope')
        observed_commands = {op for p in item['phases'].values() for op in p.get('operations', [])}
        if specification is not None or 'command_scope' in item:
            if scope not in ('none', 'recorded') or ('command_scope' in item and item['command_scope'] != scope):
                errors.append(item['id'] + ': missing or contradictory command declaration')
            elif bool(observed_commands) != (scope == 'recorded'):
                errors.append(item['id'] + ': command observations differ from declared none/recorded scope')
        if specification is None:
            continue
        item['assessment'] = outcomes.assess(specification, item['outcome_account'], load_bytes)
        if not item['assessment']['valid']:
            errors.extend(item['id'] + ': ' + error for error in item['assessment']['errors'])
            item['outcome'] = 'incomplete'
        elif item['finished'] and all(p['outcome'] == 'passed' for p in item['phases'].values()):
            item['outcome'] = 'completed' if item['assessment']['accepted'] else 'failed'
        item['execution_failures'] = [dict(phase=name, diagnostic=phase.get('diagnostic'))
                                      for name, phase in item['phases'].items() if phase['outcome'] != 'passed']
    complete = finish and all(i['finished'] for i in items.values()) and not errors
    result = dict(schema_version=2 if explicit else 1, family=manifest['family'], manifest_digest=value_digest(manifest),
        execution_state='started' if session else 'unknown', accounting_state='complete' if complete else 'incomplete',
        ok=complete and returncode == 0 and all(i['outcome'] in ('passed', 'completed') for i in items.values()),
        items=list(items.values()), operations=operations, errors=errors, engine_returncode=returncode)
    if explicit:
        result['explicit'] = any('outcome_contract' in item for item in items.values())
    return result


class Collector:
    def __init__(self, root, case):
        self.root, self.case = root, case
        self.started = False
        self.result = None
        pytest_packages.target(root)
        self.peer, child = socket.socketpair()
        self.log = tempfile.TemporaryFile()
        environment = {k:v for k,v in os.environ.items() if not k.startswith(('PYTEST', 'PYTHON', 'PW_CHECKOUT', 'PW_TEST_'))}
        environment['PYTHONCOERCECLOCALE'] = '0'
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

    def command_result(self, result, family_out):
        if self.manifest.get('schema_version') == 2:
            directory = contained(family_out / 'artifacts', result['artifacts'])
            names = ('command.json', 'stdout', 'stderr') if not result.get('never_launched') else ()
            result['evidence'] = [outcomes.file_reference((directory / name).relative_to(family_out).as_posix(),
                                  (directory / name).read_bytes()) for name in names]
        return result

    def execute(self, out, run_id, scope):
        family_out = out / 'suites' / self.case['id']
        family_out.mkdir(parents=True)
        write(family_out / 'selection.json', self.manifest)
        if self.manifest.get('schema_version') == 2:
            (family_out / 'operations.jsonl').write_text('')
        command, operations, errors, started, interrupted = None, [], [], False, False
        write(family_out / 'eligibility.json', dict(run_id=run_id, lock_identity=list(scope.identity), nonce=scope.nonce))
        try:
            send(self.peer, dict(kind='eligible', out=str(family_out)))
            socket.send_fds(self.peer, [b'L'], [scope.fd])
            while self.process.poll() is None:
                if command and command.poll() is not None:
                    result = self.command_result(command.finish(), family_out)
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
                        self.started = True
                    elif message['kind'] == 'command':
                        if command or not started or message['item'] not in {r['id'] for r in self.manifest['items']}:
                            raise ValueError('invalid command ownership request')
                        artifacts = contained(family_out / 'artifacts', message['artifacts'])
                        command = Command(self.root, out, run_id, self.case['id'], message['item'],
                                          message['argv'], artifacts, message['timeout'], scope, self.process.pid,
                                          cwd=message.get('cwd'), env=message.get('environment'))
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
                        result = self.command_result(command.finish(), family_out)
                        append(family_out / 'operations.jsonl', dict(kind='settled', **result))
                    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                        errors.append(str(exc))
                self.peer.close()
                self.log.seek(0)
                (family_out / 'pytest.txt').write_bytes(self.log.read())
                self.log.close()
                ownership = snapshot(self.root, run_id, family=self.case['id'])
                if self.manifest.get('schema_version') != 2:
                    ownership.pop('family')
                write(family_out / 'ownership.json', ownership)
                family = account(self.manifest, family_out / 'phases.jsonl', self.process.returncode, ownership, operations)
                if started:
                    family['execution_state'] = 'started'
                family['errors'].extend(errors)
                family['ok'] &= not errors
                self.result = family
                write(family_out / 'family.json', family)
                display(family_out, family)
            finally:
                signal.signal(signal.SIGINT, previous)
        return family, interrupted


def display(directory, family):
    lines = [f"FAMILY {family['family']}: {'PASS' if family['ok'] else 'FAIL'}; execution={family['execution_state']} accounting={family['accounting_state']}"]
    if family.get('schema_version') == 2:
        return display_observations(directory, family, lines)
    baseline = directory / 'artifacts/baseline.json'
    bad_baseline = baseline.exists() and not read(baseline)['ok']
    if bad_baseline:
        lines.append('SHARED BASELINE: ' + read(baseline)['error'] + '; artifacts/baseline.json. Production observation retained; dependent setup failures did not run their bodies or submit mutations.')
    integrity = directory / 'artifacts/input-integrity.json'
    if integrity.exists() and not read(integrity)['ok']:
        lines.append('SHARED SESSION FINALIZER: input integrity uncertain for all family items; pytest attaches this to the last item teardown. Body outcomes survive; inspect each retained sources.json and input-integrity.json for applicability.')
    finalizer = directory / 'artifacts/session-finalizer.json'
    if finalizer.exists():
        record = read(finalizer)
        lines.append('SHARED SESSION FINALIZER: ' + record['fixture'] + '; ' + record['scope'] + '; attached to last item teardown. ' + ('Cleanup failure after observations; recorded body outcomes and native assertions remain readable.' if record['kind'] == 'cleanup' else 'Input integrity uncertain; inspect per-variant source receipts.') + ' See artifacts/session-finalizer.json.')
    if not read(directory / 'ownership.json')['closed']:
        lines.append('OWNERSHIP UNRESOLVED: complete native observations remain readable; this is not a claim that their assertions failed. See ownership.json and the public recovery command.')
    for item in family['items']:
        phases = ', '.join(f'{k}={v["outcome"]}' for k,v in item['phases'].items())
        lines.append(f"  {item['id']}: {item['outcome']} ({phases or 'no phase evidence'})")
        suffix = item['id'].split('::', 1)[1]
        for phase in item['phases'].values():
            if not phase['diagnostic']:
                continue
            if bad_baseline and suffix != 'production' and phase['phase'] == 'setup' and 'call' not in item['phases'] and 'shared production baseline unavailable:' in phase['diagnostic']:
                lines.append('    setup blocked by shared baseline; body not run. Full diagnostic: phases.jsonl; pytest.txt')
            else:
                lines.append(f"    {phase['phase']}: {phase['diagnostic']}")
        if (directory / 'artifacts' / suffix).is_dir():
            lines.append(f'    Native evidence: artifacts/{suffix}/; phases.jsonl; pytest.txt')
        else:
            lines.append('    No native variant observation; see shared prerequisite/finalizer diagnosis and operations.jsonl for any setup commands.')
    lines.extend('ACCOUNT: ' + e for e in family['errors'])
    lines.append('Ownership: ownership.json; command receipts: operations.jsonl; manifest: selection.json')
    text = '\n'.join(lines) + '\n'
    (directory / 'summary.txt').write_text(text)
    print(text + f'Family report: {directory / "family.json"}', flush=True)


def display_observations(directory, family, lines):
    """Generic family display; domain-specific raw observations remain with their owner."""
    finalizer = directory / 'artifacts/session-finalizer.json'
    if finalizer.exists():
        record = read(finalizer)
        lines.append('SHARED FIXTURE FINALIZER: ' + record['fixture'] + '; ' + record['scope']
                     + '; attached to last item teardown. Earlier observations remain readable; see artifacts/session-finalizer.json.')
    for item in family['items']:
        phases = ', '.join(f'{key}={row["outcome"]}' for key, row in item['phases'].items())
        lines.append(f"  {item['id']}: {item['outcome']} ({phases or 'no phase evidence'})")
        assessment = item.get('assessment')
        if assessment:
            for row in assessment['advisory_judgments']:
                lines.append(f"    ADVISORY {row['id']}: {row['result']}; {row['proposition']}; {row['detail']}")
            for row in assessment['blocking_judgments']:
                lines.append(f"    ENFORCED {row['id']}: unfavorable; {row['proposition']}; {row['detail']}")
            for row in assessment['informational_completions']:
                lines.append(f"    OBSERVED {row['id']}; no product judgment")
            for error in assessment['errors']:
                lines.append('    OBSERVATION FAILURE: ' + error)
        for name, phase in item['phases'].items():
            if phase.get('diagnostic'):
                lines.append(f"    {name}: {phase['diagnostic']}")
        lines.append('    Evidence: phases.jsonl; artifacts/; pytest.txt')
    lines.extend('ACCOUNT: ' + error for error in family['errors'])
    lines.append('Ownership: ownership.json; command receipts: operations.jsonl; manifest: selection.json')
    text = '\n'.join(lines) + '\n'
    (directory / 'summary.txt').write_text(text)
    print(text + f'Family report: {directory / "family.json"}', flush=True)
