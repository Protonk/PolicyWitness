#!/usr/bin/env python3
"""Run the request fixtures through two apps and compare normalized envelopes.

`run` executes every request under tests/fixtures/pw_runner/ through one app's
controller and retains the raw envelope, stderr and exit status per fixture.
`compare` validates each retained envelope with the shared consumer, then
compares the two apps' envelopes leaf by leaf. Only leaves at the explicit
field paths below may differ, and each such difference is reported with its
class: process identifiers; wall-clock and monotonic times and deadlines;
durations; the observer's raw log output and deny lines; temporary-copy
bundle and service names and paths; the client argv; byte counts affected by
longer identifiers; and, with --across-builds, the four build stamp values.
The worker identity is compared with --expect-identity when given and must be
equal otherwise. Everything else, including every comparison record, verdict,
attempt outcome and disposition, must be equal.

    envelope_compare.py run APP OUT
    envelope_compare.py compare CANDIDATE_DIR BASELINE_DIR --out REPORT
                        [--across-builds] [--expect-identity HEX]

Exit 1 on a validation error or an unexplained difference.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import consumer

FIXTURES = ROOT / 'tests/fixtures/pw_runner'
CONTROLLER = 'Contents/MacOS/policy-witness'

# Generic leaf paths (list indexes written as []) that may differ, by class.
VOLATILE = {
    'pid': (
        'data.runner_result.pid', 'data.runner_result.runner_subprocess.pid',
        'data.runner_result.steps[].sandbox_check.pid', 'data.runner_result.validator_subprocess.pid',
        'data.runner_result.steps[].attempt.child_pid',
        'data.sandbox_log_capture.deny_events[].pid', 'data.sandbox_log_capture.observer.data.pid',
        'data.sandbox_log_capture.observer.data.deny_events[].pid',
        'data.sandbox_log_capture.observer.data.collection.cleanup.target',
        'data.sandbox_log_capture.observer.data.collection.process.pid',
        'data.sandbox_log_capture.supervision.cleanup.target', 'data.sandbox_log_capture.supervision.process.pid',
        'data.sandbox_log_capture.observer.data.predicate',  # the log predicate embeds the worker PID
    ),
    'time': (
        'generated_at_unix_ms', 'data.runner_client.started_at_unix_ms', 'data.runner_client.ended_at_unix_ms',
        'data.sandbox_log_capture.window.start', 'data.sandbox_log_capture.window.end',
        'data.sandbox_log_capture.window.started_at_unix_ms', 'data.sandbox_log_capture.window.ended_at_unix_ms',
        'data.sandbox_log_capture.observer.data.start', 'data.sandbox_log_capture.observer.data.end',
        'data.sandbox_log_capture.observer.generated_at_unix_ms',
        'data.sandbox_log_capture.observer.data.collection.budget.deadline_monotonic_ns',
        'data.sandbox_log_capture.observer.data.collection.budget.started_monotonic_ns',
        'data.sandbox_log_capture.supervision.budget.deadline_monotonic_ns',
        'data.sandbox_log_capture.supervision.budget.started_monotonic_ns',
    ),
    'duration': (
        'data.sandbox_log_capture.observer.data.collection.elapsed_ms', 'data.sandbox_log_capture.supervision.elapsed_ms',
        'data.sandbox_log_capture.observer.data.duration_ms',
    ),
    'observer_log': (
        'data.sandbox_log_capture.deny_events[].raw_line', 'data.sandbox_log_capture.observer.data.deny_events[].raw_line',
        'data.sandbox_log_capture.observer.data.log_stdout', 'data.sandbox_log_capture.observer.data.log_stderr',
        'data.sandbox_log_capture.observer.data.observed_lines',
    ),
    'bundle_identity': (
        'data.runner_result.bundle_id', 'data.specimen.runner_provenance.runner_bundle_id',
        'data.specimen.runner_provenance.runner_service_name',
    ),
    'bundle_path': (
        'data.specimen.app_provenance.evidence_manifest_path', 'data.specimen.runner_provenance.runner_bundle_path',
        'data.specimen.runner_provenance.runner_executable_path',
    ),
    'client_argv': ('data.runner_client.argv[]',),
    'bytes': (
        'data.runner_client.stdout_bytes_received', 'data.runner_client.stdout_bytes_retained',
        'data.sandbox_log_capture.stdout_bytes_received', 'data.sandbox_log_capture.stdout_bytes_retained',
        'data.sandbox_log_capture.supervision.stdout.bytes_read', 'data.sandbox_log_capture.supervision.stdout.bytes_retained',
        'data.sandbox_log_capture.observer.data.collection.stdout.bytes_read',
        'data.sandbox_log_capture.observer.data.collection.stdout.bytes_retained',
    ),
}
STAMPS = ('build.commit', 'build.describe', 'build.number', 'build.version',
          'data.sandbox_log_capture.observer.build.commit', 'data.sandbox_log_capture.observer.build.describe',
          'data.sandbox_log_capture.observer.build.number', 'data.sandbox_log_capture.observer.build.version')
IDENTITY = 'data.runner_result.runner_subprocess.worker_evidence.abi_identity'
GENERIC_INDEX = re.compile(r'\[\d+\]')


def leaves(value, path=''):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, f'{path}.{key}' if path else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, f'{path}[{index}]')
    else:
        yield path, value


def run_fixtures(app, out):
    out.mkdir(parents=True)
    controller = Path(app) / CONTROLLER
    results = {}
    for fixture in sorted(FIXTURES.glob('*.json')):
        name = fixture.stem
        started = time.monotonic()
        result = subprocess.run([str(controller), 'run', str(fixture)], capture_output=True, text=True, timeout=600)
        (out / f'{name}.json').write_text(result.stdout)
        (out / f'{name}.stderr').write_text(result.stderr)
        results[name] = dict(fixture=str(fixture), returncode=result.returncode,
                             elapsed_seconds=round(time.monotonic() - started, 3), stdout_bytes=len(result.stdout))
        (out / f'{name}.run.json').write_text(json.dumps(results[name], indent=2) + '\n')
    (out / 'runs.json').write_text(json.dumps(dict(app=str(app), controller=str(controller), fixtures=results), indent=2) + '\n')
    return results


def classify(generic):
    for klass, paths in VOLATILE.items():
        if generic in paths:
            return klass
    return None


def compare(candidate_dir, baseline_dir, *, across_builds=False, expect_identity=None):
    report = dict(candidate=str(candidate_dir), baseline=str(baseline_dir), across_builds=across_builds,
                  expect_identity=expect_identity, fixtures={}, ok=True)
    for fixture in sorted(FIXTURES.glob('*.json')):
        name = fixture.stem
        entry = dict(validation={}, explained=[], unexplained=[], identity={})
        documents = {}
        for side, directory in (('candidate', candidate_dir), ('baseline', baseline_dir)):
            try:
                documents[side] = json.loads((Path(directory) / f'{name}.json').read_text())
                entry['validation'][side] = consumer.validate(documents[side])
            except (OSError, ValueError) as error:
                entry['validation'][side] = [f'unreadable envelope: {error}']
        if any(entry['validation'].values()) or len(documents) != 2:
            entry['ok'] = False
            report['fixtures'][name] = entry
            report['ok'] = False
            continue
        left = dict(leaves(documents['candidate']))
        right = dict(leaves(documents['baseline']))
        for path in sorted(set(left) | set(right)):
            if path in left and path in right and left[path] == right[path]:
                continue
            generic = GENERIC_INDEX.sub('[]', path)
            record = dict(path=path, candidate=left.get(path, '<absent>'), baseline=right.get(path, '<absent>'))
            if generic == IDENTITY:
                continue  # checked below
            klass = classify(generic)
            if klass is None and across_builds and generic in STAMPS:
                klass = 'stamp'
            if klass is None:
                entry['unexplained'].append(record)
            else:
                entry['explained'].append(dict(record, **{'class': klass}))
        identity = dict(candidate=left.get(IDENTITY), baseline=right.get(IDENTITY))
        if expect_identity is not None:
            identity['expected'] = expect_identity
            identity['ok'] = identity['candidate'] == expect_identity
        else:
            identity['ok'] = identity['candidate'] == identity['baseline']
        entry['identity'] = identity
        entry['ok'] = not entry['unexplained'] and identity['ok']
        report['fixtures'][name] = entry
        report['ok'] = report['ok'] and entry['ok']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='mode', required=True)
    runner = sub.add_parser('run')
    runner.add_argument('app', type=Path)
    runner.add_argument('out', type=Path)
    comparer = sub.add_parser('compare')
    comparer.add_argument('candidate', type=Path)
    comparer.add_argument('baseline', type=Path)
    comparer.add_argument('--out', type=Path, required=True)
    comparer.add_argument('--across-builds', action='store_true')
    comparer.add_argument('--expect-identity')
    args = parser.parse_args()
    if args.mode == 'run':
        results = run_fixtures(args.app.resolve(), args.out.resolve())
        print(json.dumps(results, indent=2))
        return 0
    report = compare(args.candidate.resolve(), args.baseline.resolve(), across_builds=args.across_builds,
                     expect_identity=args.expect_identity)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    summary = {name: dict(ok=e['ok'], validation=e['validation'], explained=len(e['explained']),
                          unexplained=e['unexplained'], identity=e['identity']) for name, e in report['fixtures'].items()}
    print(json.dumps(dict(ok=report['ok'], fixtures=summary), indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
