"""Bounded observations of ordinary requests and retirement, without retries.

Completion establishes valid captures and accounted observations, not BYOXPC
reliability. Runner outcomes are data; missing evidence or a harness watchdog
is an incomplete experiment. Session cleanup belongs to the shell wrapper.
"""
import hashlib
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
import contract
from consumer import validate
from neighbor_lab import ProcessWatch, generation, process_identity, save
from receipts import Receipts
from run_capture import RunCapture

GAPS_MS = (0, 10, 30, 60)
PER_GAP = 12
REQUEST_TIMEOUT_MS = 5000
CAPTURE_WATCHDOG_SECONDS = 15
EXIT_OBSERVATION_SECONDS = 10
EXIT_SAMPLE_SECONDS = .005


def stamp():
    return dict(monotonic_ns=time.monotonic_ns(), unix_ns=time.time_ns())


class ExitObserver:
    """Direct queries of seen generations; no additional process-list sweeps."""
    def __init__(self, watch):
        self.watch, self.records, self.errors = watch, {}, []
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def observe(self):
        for sample in self.watch.snapshot():
            key = sample['generation']
            record = self.records.setdefault(key, dict(generation=key, pid=sample['pid'], checks=0,
                                                       first_check=None, last_check=None, unknown=[], observed_exit=None))
            if record['observed_exit'] is not None:
                continue
            observed = dict(**stamp(), identity=process_identity(sample['pid']))
            identity = observed['identity']
            record['checks'] += 1
            record['first_check'] = record['first_check'] or observed
            record['last_check'] = observed
            if identity['observed'] and generation(identity) != key:
                record['observed_exit'] = dict(**observed, basis='pid_reused')
            elif not identity['observed'] and identity['absent']:
                record['observed_exit'] = dict(**observed, basis='esrch')
            elif not identity['observed']:
                record['unknown'].append(observed)

    def run(self):
        try:
            while not self.stop_event.is_set():
                self.observe()
                self.stop_event.wait(EXIT_SAMPLE_SECONDS)
        except BaseException:
            self.errors.append(traceback.format_exc())

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise RuntimeError('exit observer did not stop')


def wait_capture(capture, record):
    """Blocking wait with a separate watchdog, avoiding timeout polling gaps."""
    finished = threading.Event()
    errors = []

    def receive():
        try:
            record['returncode'] = capture.wait(timeout=None)
            record['cli_exit_observed'] = stamp()
        except BaseException:
            errors.append(traceback.format_exc())
        finally:
            finished.set()

    waiter = threading.Thread(target=receive, daemon=True)
    waiter.start()
    if not finished.wait(CAPTURE_WATCHDOG_SECONDS):
        record.update(state='capture_watchdog', watchdog_observed=stamp())
        # This only owns the CLI. It is not a PolicyWitness timeout or a host
        # exit observation; the session helper owns service cleanup afterward.
        capture.close()
        waiter.join(timeout=5)
        raise TimeoutError('capture watchdog expired; no retry or later request')
    waiter.join()
    if errors:
        raise RuntimeError(errors[0])
    record['state'] = 'exited'


def identities(out, state, pw):
    """Keep app build identity separate from the checkout running this case."""
    app = Path(state['source_app'])
    assert Path(pw).resolve() == (app / 'Contents/MacOS/policy-witness').resolve()
    source = out / 'sources'
    source.mkdir()
    paths = ['tests/suites/runner_byoxpc/opt_in/retirement_observations.py',
             'tests/suites/runner_byoxpc/opt_in/retirement_observations.sh',
             'tests/fixtures/byoxpc/neighbor_lab.py', 'tests/fixtures/byoxpc/session.py',
             'tests/lib/run_capture.py', 'tests/lib/consumer.py', 'tests/lib/contract.py',
             'tests/lib/case.sh', 'tests/lib/testlib.sh', 'tests/catalog.json']
    hashes = {}
    for name in paths:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    git = {}
    for name, args in [('commit', ['rev-parse', 'HEAD']), ('status', ['status', '--porcelain']),
                       ('diff', ['diff', '--binary', 'HEAD'])]:
        result = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        (source / ('git-' + name + '.txt')).write_text(result.stdout)
        git[name] = str(source / ('git-' + name + '.txt'))
    evidence = out / 'app-evidence'
    evidence.mkdir()
    for name in ('manifest.json', 'provenance.json'):
        shutil.copy2(app / 'Contents/Resources/Evidence' / name, evidence / name)
    save(out / 'identity.json', dict(checkout=str(ROOT), git=git, source_sha256=hashes,
                                    selected_app=str(app), source_inventory=state['source_inventory'],
                                    installed_bundle=state['bundle_path'], service=state['service_name']))
    save(out / 'session-at-start.json', state)


def main(pw, directory):
    artifacts = Path(directory)
    out = artifacts / 'retirement'
    out.mkdir()
    receipts = Receipts(out / 'receipts.json', 'runner_byoxpc/retirement_observations', 'observation')
    records, captures, errors = [], [], []
    watch = observer = log = None
    log_record = dict(started=None, stop_requested=None, returncode=None, forced_kill=False)
    sequence = dict(started=None, finished=None, exit_observation_started=None, finished_observing=None)
    summary = dict(complete=False, meaning='completed observational experiment only; no BYOXPC reliability acceptance')
    try:
        state = json.loads(Path(json.loads((artifacts / 'session.json').read_text())['state_path']).read_text())
        service = json.loads((artifacts / 'runner_env.json').read_text())['service_name']
        assert service == state['service_name']
        identities(out, state, pw)
        macos = Path(state['bundle_path']) / 'Contents/MacOS'
        watched = {str(macos / 'PWRunner'): 'host', str(macos / 'pw-probe-runner'): 'worker'}
        plan = dict(gaps_ms=list(GAPS_MS), requests_per_gap=PER_GAP, request_timeout_ms=REQUEST_TIMEOUT_MS,
                    capture_watchdog_seconds=CAPTURE_WATCHDOG_SECONDS, exit_observation_seconds=EXIT_OBSERVATION_SECONDS,
                    exit_sample_pause_seconds=EXIT_SAMPLE_SECONDS, initial_retirement_wait=False, harness_retries=False,
                    gap_basis='minimum from previous observed CLI completion; first request has no predecessor',
                    log_attachment='asynchronous; no attachment delay or claim of complete event coverage', watched=watched)
        save(out / 'plan.json', plan)
        # Prepare outside the timed sequence. Parsing, validation and process
        # association also stay outside the hot path; only the watcher scans.
        for gap in GAPS_MS:
            for position in range(PER_GAP):
                index = len(records)
                folder = out / f'{index:02d}-gap-{gap:02d}-{position:02d}'
                specimen = dict(schema_version=contract.REQUEST_SCHEMA, specimen_id=f'retirement-{index:02d}',
                                runner=dict(mode='byoxpc', service=service),
                                policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'), probe_plan=[])
                captures.append(RunCapture(pw, folder, specimen, cli_args=('--timeout-ms', REQUEST_TIMEOUT_MS)))
                records.append(dict(index=index, gap_ms=gap, position=position, state='prepared', folder=str(folder),
                                    started=None, cli_exit_observed=None, actual_gap_ns=None))
        predicate = ' OR '.join('processImagePath == ' + json.dumps(path) for path in watched)
        predicate += ' OR eventMessage CONTAINS ' + json.dumps(service)
        argv = ['/usr/bin/log', 'stream', '--style', 'ndjson', '--level', 'debug', '--predicate', predicate]
        log_record.update(argv=argv, started=stamp())
        with (out / 'unified-log.ndjson').open('wb') as stdout, (out / 'unified-log.stderr').open('wb') as stderr:
            log = subprocess.Popen(argv, stdout=stdout, stderr=stderr)
        watch = ProcessWatch(watched).start()
        observer = ExitObserver(watch).start()
        sequence['started'] = stamp()
        previous = None
        for capture, record in zip(captures, records):
            if previous is not None:
                remaining = (previous + record['gap_ms'] * 1_000_000 - time.monotonic_ns()) / 1_000_000_000
                if remaining > 0:
                    time.sleep(remaining)
            record['started'] = stamp()
            if previous is not None:
                record['actual_gap_ns'] = record['started']['monotonic_ns'] - previous
            record['state'] = 'started'
            capture.start()
            wait_capture(capture, record)
            previous = record['cli_exit_observed']['monotonic_ns']
        sequence['finished'] = stamp()
    except BaseException:
        errors.append(traceback.format_exc())
    finally:
        for capture in captures:
            try:
                capture.close()
            except BaseException:
                errors.append(traceback.format_exc())
        if watch is not None:
            sequence['exit_observation_started'] = stamp()
            deadline = time.monotonic() + EXIT_OBSERVATION_SECONDS
            # This bounded post-sequence observation never delays a request or
            # retries one. Missing exits make the experiment incomplete.
            while observer is not None and observer.thread.is_alive() and time.monotonic() < deadline:
                seen = watch.snapshot()
                if all(observer.records.get(s['generation'], {}).get('observed_exit') is not None for s in seen):
                    break
                time.sleep(.01)
            if not watch.thread.is_alive():
                errors.append('process watcher stopped before observation finished')
            watch.stop()
            if watch.thread.is_alive():
                errors.append('process watcher did not stop')
            if observer is not None:
                try:
                    # The last full sweep can add a generation after the first
                    # completion check. Give that frozen set the same remaining
                    # observation budget, never a new deadline.
                    while observer.thread.is_alive() and time.monotonic() < deadline:
                        if all(observer.records.get(s['generation'], {}).get('observed_exit') is not None
                               for s in watch.snapshot()):
                            break
                        time.sleep(.01)
                    observer.stop()
                    observer.observe()  # Account for the watcher's final sweep.
                except BaseException:
                    errors.append(traceback.format_exc())
                errors.extend(observer.errors)
            samples = watch.snapshot()
            exits = observer.records if observer is not None else {}
            missing = [s['generation'] for s in samples if exits.get(s['generation'], {}).get('observed_exit') is None]
            if missing:
                errors.append('no direct pre-cleanup exit observation for: ' + ', '.join(missing))
            if not watch.sweeps:
                errors.append('process watcher completed no sweeps')
            save(out / 'processes.json', dict(generations=samples, sampler=watch.summary(), sweeps_ns=watch.sweeps,
                                             exits=exits, missing_direct_exits=missing,
                                             limitations='unseen is not exited; processes shorter than a sweep may be missed'))
        if log is not None:
            try:
                if log.poll() is not None:
                    errors.append('unified log stream exited before requested stop')
                else:
                    log_record['stop_requested'] = stamp()
                    log.send_signal(signal.SIGINT)
                try:
                    log.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    log_record['forced_kill'] = True
                    log.kill()
                    log.wait(timeout=5)
                    errors.append('unified log stream required watchdog termination')
                log_record['returncode'] = log.returncode
            except BaseException:
                errors.append(traceback.format_exc())
        sequence['finished_observing'] = stamp()
        save(out / 'unified-log-capture.json', log_record)
        # Preserve every result, including malformed/nonzero captures. Neither
        # an outcome nor a nonzero CLI status causes a retry or removes evidence.
        counts = {str(gap): dict(ok=0, already_ran=0, xpc_error=0, xpc_timeout=0) for gap in GAPS_MS}
        for capture, record in zip(captures, records):
            try:
                if record['state'] != 'exited':
                    record['validation_errors'] = ['capture did not complete normally']
                else:
                    envelope = capture.load_json()
                    record['validation_errors'] = validate(envelope)
                    reply = envelope.get('data', {}).get('runner_result')
                    if not isinstance(reply, dict) or not isinstance(reply.get('normalized_outcome'), str):
                        record['validation_errors'].append('missing runner result/outcome')
                    else:
                        record.update(outcome=reply['normalized_outcome'], reply_pid=reply.get('pid'),
                                      worker_pid=(reply.get('runner_subprocess') or {}).get('pid'),
                                      acquisitions=envelope['data'].get('runner_acquisition', []))
                        group = counts[str(record['gap_ms'])]
                        group[record['outcome']] = group.get(record['outcome'], 0) + 1
                if record['validation_errors']:
                    errors.append(f"request {record['index']}: {record['validation_errors']}")
            except BaseException:
                record['validation_errors'] = [traceback.format_exc()]
                errors.extend(record['validation_errors'])
            save(Path(record['folder']) / 'observation.json', record)
            receipts.add(**record)
        if len(records) != len(GAPS_MS) * PER_GAP or any(r['state'] != 'exited' for r in records):
            errors.append('the predeclared 48-request sequence is incomplete')
        summary.update(complete=not errors, timing=sequence, outcomes_by_gap_ms=counts, requests=records, errors=errors,
                       source_app_inventory_check='owned by subsequent session cleanup; consult cleanup receipts',
                       interpretation='outcomes, acquisition records and observed exits do not identify a cause')
        save(out / 'summary.json', summary)
        receipts.finish(ok=not errors, complete=not errors)
    if errors:
        raise AssertionError('observational experiment incomplete; see retirement/summary.json')
    print(json.dumps(dict(completed_requests=len(records), outcomes_by_gap_ms=counts,
                          meaning=summary['meaning']), indent=2))


if __name__ == '__main__':
    main(*sys.argv[1:])
