"""Worker-wait pilot driver: paced production-shaped trials with stamp recovery.

Builds a stamped disposable host and an unpatched neighbor with the same recipe,
stages both apps once into the artifacts directory and reuses those exact
executables through fresh processes. One excluded first execution of each
staged app precedes counted trials. Both apps run every cell in both regimes,
alternating which app goes first in each repetition. Every trial uses the
production validator path (no test overrides) and retains its request, CLI
output, per-trial power, sleep, load and pacing observations, the driver's
own wake spans, the host's stamp export and export marker, and the host exit
watch. Envelope validation runs after the window so it never occupies an idle
gap. The reader then writes decomposition.json, summary.json and summary.md.
A final cleanup inventories processes running from either staged bundle.

Usage: app_dir artifacts_dir identity --worker-build DIR --observer PATH
       [--cells O1,...] [--repetitions N] [--regimes rapid,idle] [--window-seconds S]
       [--trial-watchdog-seconds S] [--clock-pair-trials N] [--no-clock-pair] [--dry-run]

The clock-pair calibration runs first inside the window; without it the
reader leaves combined uncertainty not established. A schedule whose planning
estimate exceeds the window is refused before any build.

Stamped hosts and seam-built workers are not production executables; their
timings describe this instrument's flavour only. A dry run establishes
mechanics, never the quantitative decomposition, and removes its staged apps.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for path in (HERE, ROOT / 'tests/lib', ROOT / 'tests/fixtures/validator', ROOT / 'tests/fixtures/exec', ROOT / 'tests/fixtures/footprint'):
    sys.path.insert(0, str(path))
from artifact import EXECUTABLES, SERVICE, digest, inventory
import consumer
from check_ordering import specimen, step
from footprint_observer import FootprintObserver, GenerationExitObserver, generation, sha256
from footprint_workloads import actor_specimen
from lifecycle_oracle import check_record
from run_capture import RunCapture
import worker_wait_pilot_reader as reader

# ---- Integration points with tests/fixtures/worker_wait and the clock pair -------
HOST_STAMPS = ROOT / 'tests/fixtures/worker_wait/host_stamps.py'
CLOCK_PAIR = HERE / 'worker_wait_clock_pair.py'
STAMP_ROOT = Path('/private/tmp/pw-worker-wait-stamps')
SERVICE_MACOS = Path(SERVICE) / 'Contents/MacOS'
HOST = SERVICE_MACOS / 'PWRunner'
# Executable paths inside a staged bundle that final cleanup may stop.
STAGED_ROLES = {HOST: 'host', SERVICE_MACOS / 'pw-probe-runner': 'worker', SERVICE_MACOS / 'pw-probe-runner-unentitled': 'worker'}
WORKERS = dict(stamps='pw-probe-runner-stamps', plain='pw-probe-runner-plain')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_host(module, kind, artifacts, scratch, stamp_dir):
    """One host binary; the instrumented kind bakes stamp_dir, the neighbor applies no patch."""
    work = scratch / f'host-{kind}'
    return Path(module.build_host(work / 'runner', work, artifacts / f'host-{kind}',
                                  module.PATCHES if kind == 'instrumented' else [], stamp_dir))


def host_flavour(artifacts, kind):
    return json.loads((artifacts / f'host-{kind}' / 'host-build.json').read_text())['flavour']


def stage_app(module, kind, source_app, staging, identity, host, worker_build):
    """One durable signed copy; the stager writes staging.json and returns the app path."""
    return Path(module.stage(source_app, staging / kind, identity, host, worker_build / WORKERS['stamps'],
                             worker_build / WORKERS['plain'], kind == 'instrumented'))


def calibrate(module, binary, artifacts, trials):
    """Run the clock-pair matrix; the reader validates artifacts/clock-pair/calibration.json itself."""
    calibration = module.run(binary, artifacts / 'clock-pair', trials=trials)
    return calibration['complete']
# ---- end of integration points ---------------------------------------------------

APPS = ('instrumented', 'neighbor')
CELLS = ('O1', 'O64', 'O256', 'O0', 'O2P', 'A2')
REGIMES = ('rapid', 'idle')
REQUESTED_GAP_NS = {'rapid': 0, 'idle': 1_000_000_000}
# Declared before trials; out-of-range gaps are retained and excluded, never replaced.
ELIGIBLE_GAP_NS = {'rapid': [0, 100_000_000], 'idle': [1_000_000_000, 1_250_000_000]}
DEFAULT_REPETITIONS = 6
COVERAGE_MIN_ACCEPTED = 5
# Applied by the reader; an excluded trial stays in decomposition.json as diagnostic.
DECLARED_EXCLUSIONS = {
    'observer_overlap': 'the exit-watch registration span (host-exit.json activity_ns, driver clock, from reading .started '
                        'to the end of the watch; registration begin_ns/end_ns where activity_ns is absent) intersects any '
                        'held interval [worker arrival, acknowledgement] of the same trial',
    'pacing_out_of_range': 'actual gap from the previous observed cleanup to launch outside eligible_gap_ns for the regime',
    'sleep_overlapped': 'continuous and uptime clocks diverged across the trial beyond the clock-read tolerance',
    'power_transition': 'power source or low power mode differs before and after the trial',
    'power_unobserved': 'power source or low power mode unreadable before or after the trial',
}
CLI_TIMEOUT_MS = 60000
TRIAL_CLEANUP_S = 5
STAMP_WAIT_S = 3.0
CLI_MARGIN_NS = 100_000_000
# Wakes come from the CLI exit, a write into the stamp directory or this timeout cadence;
# every wake stats the .started path until it has been seen.
STARTED_CHECK = dict(fast_s=0.001, fast_window_ns=20_000_000, slow_s=0.010)
WAKE_CAUSES = dict(l='launch', t='timeout', d='stamp directory write', x='CLI exit')
SURVIVOR_GRACE_S = 1.0
KILL_WAIT_S = 5.0
# Planning estimates per entry; trial watchdogs and the window check enforce the real bound.
ESTIMATE_S = dict(idle=1.1, rapid=0.1, warm=1.0, calibration=60.0)
DRIVER_CLOCK_SLACK_NS = 1000
IOKIT_EXCLUDED = dict(operation='iokit-open-service', filter=dict(kind='iokit_registry_entry_class', value='IOSurfaceRoot'))


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def driver_ns():
    """mach_continuous_time in ns: the observer's and the stamps' clock domain (checked at window start)."""
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)


def driver_clock_check(observer):
    before = driver_ns(); value = observer.clock(); after = driver_ns()
    agrees = before - DRIVER_CLOCK_SLACK_NS <= value['begin_ns'] <= value['end_ns'] <= after + DRIVER_CLOCK_SLACK_NS
    return dict(source='time.clock_gettime_ns(CLOCK_MONOTONIC_RAW)', before_ns=before, observer=value, after_ns=after,
                slack_ns=DRIVER_CLOCK_SLACK_NS, agrees=agrees)


def text(argv):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return dict(argv=argv, returncode=None, stdout=None, error=repr(exc))
    return dict(argv=argv, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)


def capture_power():
    batt, settings = text(['/usr/bin/pmset', '-g', 'batt']), text(['/usr/bin/pmset', '-g'])
    source = re.search(r"Now drawing from '([^']+)'", batt['stdout'] or '')
    low = re.search(r'^\s*lowpowermode\s+(\S+)', settings['stdout'] or '', re.M)
    return dict(batt=batt, settings=settings, source=source and source.group(1), lowpowermode=low and low.group(1))


def static_conditions(app):
    sysctl = text(['/usr/sbin/sysctl', 'kern.osversion', 'kern.boottime', 'hw.model', 'machdep.cpu.brand_string', 'hw.ncpu', 'hw.memsize'])
    sources = [Path(__file__), Path(reader.__file__), ROOT / 'tests/lib/run_capture.py', ROOT / 'tests/lib/footprint_observer.py',
               ROOT / 'tests/lib/footprint_workloads.py', HERE / 'check_ordering.py', HOST_STAMPS, CLOCK_PAIR]
    return dict(sw_vers=text(['/usr/bin/sw_vers']), sysctl=sysctl, power=capture_power(), loadavg=os.getloadavg(),
                python=dict(executable=sys.executable, sha256=sha256(sys.executable), version=sys.version),
                source_hashes={str(p.relative_to(ROOT)): sha256(p) if p.exists() else None for p in sources},
                source_app=dict(path=str(app), provenance_sha256=sha256(app / 'Contents/Resources/Evidence/provenance.json'),
                                manifest_sha256=sha256(app / 'Contents/Resources/Evidence/manifest.json')))


def staged_identity(app):
    """Hashes plus device/inode, so reuse of the same files across trials is checkable."""
    rows = {}
    for relative in EXECUTABLES:
        path = app / relative; st = path.stat()
        rows[relative] = dict(sha256=digest(path), st_dev=st.st_dev, st_ino=st.st_ino, size=st.st_size)
    return dict(app=str(app), executables=rows, inventory=inventory(app))


# ---- cells ----------------------------------------------------------------------

def make_targets(root):
    files = [root / f't{i:03d}' for i in range(256)]
    for path in files:
        path.write_bytes(b'x')
    target, marker = root / 'a2-target', root / 'a2-marker'
    target.write_bytes(b'worker wait actor target\n'); marker.write_bytes(b'worker wait actor marker\n')
    return dict(root=root, files=files, actor_target=target, actor_marker=marker)


def excluded_step(path, name):
    return dict(step_id=name, sandbox_check=IOKIT_EXCLUDED, attempt=dict(kind='file', action='open_read', target=str(path)))


def actor_layout(request):
    actors = [a['actor_id'] for a in request['actors']]
    phases, visits, deliveries, slots = [], {}, [], {}
    for phase in request['phases']:
        actor = actors.index(phase['actor_id']); visit = visits.get(actor, 0); visits[actor] = visit + 1
        phases.append(dict(phase_id=phase['phase_id'], actor=actor, visit=visit,
                           eligible=sum(1 for action in phase['actions'] if 'sandbox_check' in action)))
        for action in phase['actions']:
            extension = action.get('extension') or {}
            if extension.get('operation') == 'transfer':
                recipient = actors.index(extension['recipient']); slot = slots.get(recipient, 0); slots[recipient] = slot + 1
                deliveries.append(dict(delivery=len(deliveries), source=actor, recipient=recipient, slot=slot))
    return dict(form='actor', actors=actors, phases=phases, deliveries=deliveries)


def cell_request(cell, targets):
    """(request, layout); the caller assigns specimen_id."""
    files = targets['files']
    if cell in ('O1', 'O64', 'O256'):
        count = int(cell[1:])
        return (specimen([step(p, 'open_read', f's{i:03d}') for i, p in enumerate(files[:count])]),
                dict(form='ordinary', phases=[dict(eligible=count)]))
    if cell == 'O0':
        return (specimen([excluded_step(p, f's{i:03d}') for i, p in enumerate(files[:64])]),
                dict(form='ordinary', phases=[dict(eligible=0)],
                     zero_eligible_form='static prediction-unavailable pair iokit-open-service + iokit_registry_entry_class; attempts match O64'))
    if cell == 'O2P':
        request = dict(schema_version=6, specimen_id='', policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
                       phases=[dict(phase_id=f'p{p}', actions=[step(path, 'open_read', f'p{p}s{i}') for i, path in enumerate(files[8 * p:8 * p + 8])])
                               for p in range(2)])
        return request, dict(form='ordinary', phases=[dict(eligible=8), dict(eligible=8)])
    if cell == 'A2':
        request, _ = actor_specimen(targets['actor_target'], targets['actor_marker'])
        assert '_test_overrides' not in request
        return request, actor_layout(request)
    raise ValueError(cell)


def build_schedule(cells, regimes, repetitions):
    """Regime blocks, rapid first; per repetition and cell both apps, alternating which goes first.

    required maps app/cell/regime to the accepted trials one homogeneous group needs."""
    entries = []
    for regime in [r for r in REGIMES if r in regimes]:
        for i in range(repetitions):
            apps = APPS if i % 2 == 0 else APPS[::-1]
            entries += [dict(app=a, cell=c, regime=regime, index=i) for c in cells for a in apps]
    required = {f"{e['app']}/{e['cell']}/{e['regime']}": min(COVERAGE_MIN_ACCEPTED, repetitions) for e in entries}
    return entries, required


def warm_cells(cells):
    return [c for c in ('O1', 'A2') if c in cells or c == 'O1']


def window_estimate(entries, warm_runs, clock_pair, watchdog_s):
    """Planning estimate of window use; the final watchdog and cleanup reserve must also fit."""
    trials = {r: sum(1 for e in entries if e['regime'] == r) for r in REGIMES}
    trials_s = sum(ESTIMATE_S[r] * n for r, n in trials.items())
    warm_s, calibration_s = ESTIMATE_S['warm'] * warm_runs, ESTIMATE_S['calibration'] if clock_pair else 0.0
    reserve_s = watchdog_s + TRIAL_CLEANUP_S
    return dict(trials=trials, trial_count=len(entries), warm_runs=warm_runs, per_entry_s=ESTIMATE_S,
                trials_s=round(trials_s, 3), warm_s=warm_s, calibration_s=calibration_s, end_reserve_s=reserve_s,
                total_s=round(trials_s + warm_s + calibration_s + reserve_s, 3),
                basis='planning estimate per entry; the end reserve is one trial watchdog plus its cleanup')


# ---- trials ---------------------------------------------------------------------

class Pilot:
    def __init__(self, args, observer, apps, stamp_dir, stamp_dir_fd, stamp_paths, exported_path, targets, flavour):
        self.args, self.observer, self.apps, self.stamp_dir, self.stamp_dir_fd = args, observer, apps, stamp_dir, stamp_dir_fd
        self.stamp_paths, self.exported_path, self.targets, self.flavour = stamp_paths, exported_path, targets, flavour
        self.power = capture_power()
        self.last_cleanup = None
        self.window_end_ns = None
        self.stopped_for = None

    def now(self):
        return self.observer.clock()['continuous_ns']

    def fits(self, regime):
        remaining = self.window_end_ns - self.now()
        need = int((self.args.trial_watchdog_seconds + TRIAL_CLEANUP_S) * 1e9) + REQUESTED_GAP_NS.get(regime, 0)
        return remaining >= need, remaining, need

    def pace(self, requested):
        """Wait until the requested gap after the previous observed cleanup has passed."""
        if self.last_cleanup is None:
            return dict(previous_cleanup_ns=None, previous_cleanup_how=None, requested_gap_ns=requested, waited_ns=0)
        previous, how = self.last_cleanup
        started = time.monotonic_ns()
        while True:
            remaining = previous + requested - self.now()
            if remaining <= 0: break
            time.sleep(remaining / 1e9)
        return dict(previous_cleanup_ns=previous, previous_cleanup_how=how, requested_gap_ns=requested,
                    waited_ns=time.monotonic_ns() - started)

    def observe_started(self, path, app, detected_by):
        """Read .started and register the host exit watch; activity_ns spans all of it on the driver clock."""
        begin = driver_ns()
        value, exits, watch = self.register_host(path, app)
        watch.update(activity_ns=[begin, driver_ns()], detected_by=detected_by)
        return value, exits, watch

    def register_host(self, path, app):
        try:
            value = json.loads(path.read_text())
        except ValueError as exc:
            return None, None, dict(state='started_unreadable', reason=repr(exc))
        exits = GenerationExitObserver(self.observer)
        try:
            registration = exits.watch(value['host_pid'])
        except (AssertionError, OSError) as exc:
            exits.close()
            return value, None, dict(state='unavailable', reason=repr(exc))
        expected = os.path.realpath(app / HOST)
        if os.path.realpath(registration['before']['path']) != expected:
            exits.close()
            return value, None, dict(state='refused_wrong_executable', registration=registration, expected_path=expected)
        return value, exits, dict(state='registered', registration=registration)

    def run(self, entry, directory, receipt_name, *, warm=False):
        kind, cell, regime, index = entry['app'], entry['cell'], entry['regime'], entry['index']
        nonce = secrets.token_hex(6)
        sid = f'warm-{kind}-{cell}-{nonce}' if warm else f'{cell}-{regime}-{index}-{nonce}'
        request, layout = cell_request(cell, self.targets); request['specimen_id'] = sid
        app = self.apps[kind]
        receipt = dict(version=1, app=kind, cell=cell, regime=regime, index=index, specimen_id=sid, nonce=nonce,
                       form=layout['form'], layout=layout, flavour=self.flavour, dry_run=self.args.dry_run, warm=warm,
                       app_path=str(app), cli_args=['--timeout-ms', str(CLI_TIMEOUT_MS)], status='prepared',
                       driver=dict(started_check=STARTED_CHECK, stamp_wait_s=STAMP_WAIT_S, watchdog_s=self.args.trial_watchdog_seconds,
                                   clock='CLOCK_MONOTONIC_RAW ns (mach_continuous_time domain)', wake_causes=WAKE_CAUSES,
                                   activity='kqueue wait on the CLI exit, writes into the stamp directory (removed once .started is '
                                            'seen) and the started_check cadence; a stat of the .started path on every wake until '
                                            'it is seen; one host exit-watch registration (instrumented)'))
        run = RunCapture(app / 'Contents/MacOS/policy-witness', directory, request, cli_args=receipt['cli_args'])
        power_before = self.power
        pacing = self.pace(REQUESTED_GAP_NS[regime] if not warm else 0)
        exits = None
        try:
            loadavg_before = os.getloadavg()
            clock_before = self.observer.clock()
            launch_before = driver_ns()
            run.start()
            launch = driver_ns()
            wakes = []
            kq = select.kqueue()
            try:
                stamp_dir_event = select.kevent(self.stamp_dir_fd, filter=select.KQ_FILTER_VNODE,
                                                flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR, fflags=select.KQ_NOTE_WRITE)
                kq.control([stamp_dir_event], 0, 0)
                try:
                    kq.control([select.kevent(run.pid, filter=select.KQ_FILTER_PROC, flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                              fflags=select.KQ_NOTE_EXIT)], 0, 0)
                except ProcessLookupError:
                    pass  # Already exited; poll() below observes it.
                started_path, stamps_path = self.stamp_paths(self.stamp_dir, sid)
                started, watch = None, dict(state='not_attempted')
                deadline = time.monotonic() + self.args.trial_watchdog_seconds
                cause, watching_dir = 'l', True
                while run.poll() is None:
                    woke = driver_ns()
                    if time.monotonic() >= deadline:
                        receipt['status'] = 'harness_timeout'
                        break
                    # Both apps stat; only the instrumented host writes the marker.
                    if started is None and started_path.exists() and kind == 'instrumented':
                        started, exits, watch = self.observe_started(started_path, app, WAKE_CAUSES[cause])
                        if watching_dir:
                            kq.control([select.kevent(self.stamp_dir_fd, filter=select.KQ_FILTER_VNODE, flags=select.KQ_EV_DELETE)], 0, 0)
                            watching_dir = False
                    now = driver_ns()
                    wakes.append([woke - launch, now - launch, cause])
                    fast = now - launch < STARTED_CHECK['fast_window_ns']
                    events = kq.control(None, 2, STARTED_CHECK['fast_s'] if fast else STARTED_CHECK['slow_s'])
                    filters = {e.filter for e in events}
                    cause = 'x' if select.KQ_FILTER_PROC in filters else 'd' if filters else 't'
            finally:
                kq.close()
            exit_clock = self.observer.clock()
            receipt['driver_wakes'] = dict(launch_ns=[launch_before, launch], spans_from_launch_ns=wakes,
                                           layout='[wake, before next wait, cause] relative to launch_ns[1]')
            if receipt['status'] == 'harness_timeout':
                run.close()
            rc = run.poll()
            if kind == 'instrumented' and started is None and started_path.exists():
                started, exits, watch = self.observe_started(started_path, app, 'after the CLI exit')
            receipt['cli'] = dict(returncode=rc, exit_clock=exit_clock)
            event = self.collect_host_exit(kind, stamps_path, started, exits)
            if event is not None:
                cleanup_ns, how = event['collection_end_ns'], 'host_exit_event'
            elif exits is None:
                cleanup_ns, how = exit_clock['end_ns'] + CLI_MARGIN_NS, 'cli_exit_plus_margin'
            else:
                cleanup_ns, how = None, 'unobserved'
            receipt['stamp_files'] = {}
            for source, name in ((started_path, 'started.json'), (stamps_path, 'stamps.json'),
                                 (self.exported_path(self.stamp_dir, sid), 'exported.json')):
                receipt['stamp_files'][name] = 'absent'
                if source.exists():
                    shutil.copyfile(source, directory / name); source.unlink()
                    receipt['stamp_files'][name] = 'copied'
            save(directory / 'host-exit.json', dict(watch, event=event, cleanup_observed_how=how, cleanup_ns=cleanup_ns,
                                                    cli_exit_clock=exit_clock, host_pid=started and started.get('host_pid')))
            self.power = capture_power()
            clock_after = self.observer.clock()
            difference = (clock_after['continuous_ns'] - clock_before['continuous_ns']) - (clock_after['uptime_ns'] - clock_before['uptime_ns'])
            tolerance = sum(c['end_ns'] - c['begin_ns'] for c in (clock_before, clock_after)) + 1_000_000
            actual = clock_before['continuous_ns'] - pacing['previous_cleanup_ns'] if pacing['previous_cleanup_ns'] is not None else None
            save(directory / 'conditions.json', dict(
                version=1, power_before=power_before, power_after=self.power, clock_before=clock_before, clock_after=clock_after,
                sleep_difference_ns=difference, sleep_tolerance_ns=tolerance, sleep_overlapped=abs(difference) > tolerance,
                loadavg_before=loadavg_before, loadavg_after=os.getloadavg(),
                pacing=dict(pacing, regime=regime, actual_gap_ns=actual, eligible_gap_ns=ELIGIBLE_GAP_NS[regime],
                            launch_clock=clock_before, rule='gap from the previous observed cleanup to the launch clock')))
            receipt['whole_request'] = dict(elapsed_ns=round(run.elapsed_seconds * 1e9) if run.elapsed_seconds is not None else None,
                                            elapsed_source='RunCapture monotonic start to first exit poll',
                                            observer_bracket_ns=exit_clock['end_ns'] - clock_before['begin_ns'])
            if receipt['status'] == 'prepared':
                receipt['status'] = 'completed' if rc == 0 else 'cli_failed'
            if how == 'unobserved':
                self.stopped_for = 'host_exit_unobserved'
            elif receipt['status'] != 'completed':
                self.stopped_for = receipt['status']
            else:
                self.last_cleanup = (cleanup_ns, how)
        except Exception as exc:
            receipt.update(status='driver_error', error=repr(exc))
            self.stopped_for = 'driver_error'
            run.close()
        finally:
            if exits is not None:
                exits.close()
            save(directory / receipt_name, receipt)
        return receipt

    def collect_host_exit(self, kind, stamps, started, exits):
        """Bounded wait for the stamp export and, when registered, the host exit event."""
        if kind != 'instrumented':
            return None
        deadline = time.monotonic() + STAMP_WAIT_S
        event = None
        while time.monotonic() < deadline:
            if exits is not None and event is None:
                event = next((e for e in exits.read_exit_events(0.02) if e['generation']['pid'] == started['host_pid']), None)
            else:
                time.sleep(0.02)
            if stamps.exists() and (exits is None or event is not None):
                break
        return event


# ---- validation after the window --------------------------------------------------

def timing_fields(value, prefix=''):
    out = {}
    if isinstance(value, dict):
        for key, item in value.items():
            path = f'{prefix}.{key}' if prefix else key
            if (key.endswith('_ms') or key == 'observed_ns') and type(item) is int:
                out[path] = item
            else:
                out.update(timing_fields(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            out.update(timing_fields(item, f'{prefix}.{index}'))
    return out


def cross_check_fields(fields):
    """Observed envelope millisecond fields (ready, sentinel, schedule and grace waits, visit timing), budgets left out."""
    return {path: value for path, value in fields.items() if path.endswith('_ms') and not path.endswith('budget_ms')}


def cell_problems(runner, cell, layout):
    problems = []
    if layout['form'] == 'ordinary':
        phases = runner['phases']
        if len(phases) != len(layout['phases']): problems.append('phase_count')
        if not all(p['arrival_observed'] and p['completion_observed'] for p in phases): problems.append('phase_unobserved')
        if not all(s['attempt']['rc'] == 0 for s in runner['steps']): problems.append('attempt_failed')
        for index, phase in enumerate(phases):
            steps = [s for s in runner['steps'] if s['phase_id'] == phase['phase_id']]
            if sum(1 for s in steps if s['comparison']['order'] == 'query_first') != layout['phases'][index]['eligible']:
                problems.append(f'eligible_queries_p{index}')
        if cell == 'O0':
            if not all(s['sandbox_check']['outcome'] == 'prediction_unavailable' for s in runner['steps']): problems.append('zero_eligible_outcome')
            if phases[0]['collection_status'] != 'not_needed': problems.append('zero_eligible_collection')
        if runner['runner_subprocess']['reaped'] is not True: problems.append('worker_unreaped')
    else:
        issues = [e for e in runner['extension_events'] if e['operation'] == 'issue']
        if not issues or not all(e['status'] == 'returned' and e['native_nonnull'] is True for e in issues): problems.append('issuance')
        if len(runner['transfers']) != len(layout['deliveries']) or not all(t['status'] == 'delivered' for t in runner['transfers']):
            problems.append('transfers')
        if not all(a['subprocess']['reaped'] for a in runner['actors']): problems.append('actor_unreaped')
        known = [s for s in runner['steps'] if s['step_id'] == 'knownread']
        if len(known) != 1 or known[0]['comparison']['order'] != 'query_first': problems.append('knownread_order')
    return problems


def validate(directory, receipt):
    problems, details, fields = [], {}, {}
    try:
        envelope = json.loads((directory / 'run.json').read_text())
        runner = envelope['data']['runner_result']
        if runner['normalized_outcome'] != 'finished': problems.append('outcome_' + str(runner['normalized_outcome']))
        details['consumer'] = consumer.validate(envelope)
        details['lifecycle_oracle'] = check_record(envelope)
        if details['consumer']: problems.append('consumer')
        if details['lifecycle_oracle']: problems.append('lifecycle_oracle')
        if runner.get('test_overrides') is not None: problems.append('test_overrides_present')
        problems += cell_problems(runner, receipt['cell'], receipt['layout'])
        fields = timing_fields(runner)
        if not any(path.endswith('_ms') for path in fields): problems.append('host_ms_fields_missing')
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        problems.append('envelope_unreadable'); details['error'] = repr(exc)
    save(directory / 'validation.json', dict(problems=problems, details=details, host_ms_fields=fields,
                                             cross_check_fields=cross_check_fields(fields)))
    return problems


# ---- final cleanup ------------------------------------------------------------------

def staged_role(path, bundles):
    """(app, role) when path lies under a staged bundle, else None."""
    real = Path(os.path.realpath(path))
    for kind, bundle in bundles.items():
        if real.is_relative_to(bundle):
            return kind, STAGED_ROLES.get(real.relative_to(bundle), 'other')
    return None


def staged_processes(observer, bundles):
    """This user's processes whose executable path (observer proc_pidpath) lies under a staged bundle.

    ps supplies the pid list only: a worker's argv[0] is a bare name, so argv cannot locate it."""
    listing = text(['/bin/ps', '-axww', '-o', 'pid=,ppid=,uid=,comm='])
    rows = []
    for line in (listing['stdout'] or '').splitlines():
        fields = line.split(None, 3)
        if len(fields) == 4 and fields[2] == str(os.getuid()) and int(fields[0]) != os.getpid():
            rows.append(dict(pid=int(fields[0]), ppid=int(fields[1]), comm=fields[3]))
    found = []
    for start in range(0, len(rows), 64):
        chunk = rows[start:start + 64]
        for row, sample in zip(chunk, observer.sample([r['pid'] for r in chunk])['samples']):
            match = staged_role(sample['path'], bundles) if sample['path'] else None
            if match:
                found.append(dict(row, app=match[0], role=match[1], path=sample['path'], status=sample['status'],
                                  generation=generation(sample) if sample['status'] == 'ok' else None))
    if found:
        commands = text(['/bin/ps', '-ww', '-o', 'pid=,command=', '-p', ','.join(str(r['pid']) for r in found)])
        argv = dict(line.strip().split(None, 1) for line in (commands['stdout'] or '').splitlines() if len(line.split(None, 1)) == 2)
        for row in found:
            row['command'] = argv.get(str(row['pid']))
    complete = listing['returncode'] == 0 and bool(rows)
    return dict(argv=listing['argv'], returncode=listing['returncode'], inspected=len(rows), complete=complete), found


def settle_survivor(observer, row):
    """SIGKILL a staged host or worker still alive after its run, once its generation is watched and a grace passed."""
    action = dict(pid=row['pid'], app=row['app'], role=row['role'], generation=row['generation'], grace_s=SURVIVOR_GRACE_S)
    if row['generation'] is None:
        action['disposition'] = 'generation_unavailable'
        return action
    exits = GenerationExitObserver(observer)
    try:
        try:
            action['registration'] = exits.watch(row['pid'], row['generation'])
        except AssertionError as exc:
            action.update(disposition='gone_or_generation_changed', reason=repr(exc)[:500])
            return action
        if exits.read_exit_events(SURVIVOR_GRACE_S):
            action['disposition'] = 'exited_within_grace'
            return action
        action['kill_ns'] = driver_ns()
        try:
            os.kill(row['pid'], signal.SIGKILL)
        except OSError as exc:
            action['kill_error'] = repr(exc)
        events = exits.read_exit_events(KILL_WAIT_S)
        action.update(signal='SIGKILL', exit=events[0] if events else None,
                      disposition='kill_unconfirmed' if not events else 'exited_before_kill' if 'kill_error' in action else 'killed')
    finally:
        exits.close()
    return action


def final_cleanup(observer_binary, apps, artifacts):
    """Inventory processes from either staged bundle; stop only a staged host or worker that survived its run."""
    bundles = {kind: Path(os.path.realpath(app)) for kind, app in apps.items()}
    record = dict(version=1, bundles={k: str(v) for k, v in bundles.items()}, roles={str(k): v for k, v in STAGED_ROLES.items()},
                  rule='every trial has ended; a staged host or worker still alive after a grace under a generation-checked '
                       'exit watch receives SIGKILL; any other staged process is recorded only',
                  started_ns=driver_ns(), found=[], actions=[], remaining=None, settled=False)
    try:
        with FootprintObserver(observer_binary) as observer:
            record['listing'], record['found'] = staged_processes(observer, bundles)
            for row in record['found']:
                if row['role'] in ('host', 'worker'):
                    record['actions'].append(settle_survivor(observer, row))
            record['listing_after'], record['remaining'] = staged_processes(observer, bundles)
        record['settled'] = record['listing']['complete'] and record['listing_after']['complete'] and not record['remaining']
    except Exception as exc:  # Recorded as unsettled; the remaining cleanup steps still run.
        record['error'] = repr(exc)[:1000]
    record['ended_ns'] = driver_ns()
    save(artifacts / 'cleanup.json', record)
    return record


# ---- main -------------------------------------------------------------------------

def parse(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('app'); parser.add_argument('artifacts'); parser.add_argument('identity')
    parser.add_argument('--worker-build', required=True); parser.add_argument('--observer', required=True)
    parser.add_argument('--no-clock-pair', action='store_true'); parser.add_argument('--clock-pair-trials', type=int, default=100)
    parser.add_argument('--cells', default=','.join(CELLS)); parser.add_argument('--regimes', default=','.join(REGIMES))
    parser.add_argument('--repetitions', type=int); parser.add_argument('--window-seconds', type=float, default=240.0)
    parser.add_argument('--trial-watchdog-seconds', type=float, default=15.0)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    args.cells = [c for c in args.cells.split(',') if c]; args.regimes = [r for r in args.regimes.split(',') if r]
    assert args.cells and set(args.cells) <= set(CELLS), args.cells
    assert args.regimes and set(args.regimes) <= set(REGIMES), args.regimes
    if args.repetitions is None: args.repetitions = 1 if args.dry_run else DEFAULT_REPETITIONS
    assert args.repetitions >= 1 and args.window_seconds > 0 and args.trial_watchdog_seconds > 0
    assert args.dry_run or args.repetitions >= COVERAGE_MIN_ACCEPTED, \
        f'a counted pilot needs at least {COVERAGE_MIN_ACCEPTED} repetitions per app, cell and regime'
    assert args.identity, 'signing identity required before any build'
    return args


def coverage(groups, required):
    """Per app/cell/regime: the most accepted trials in one homogeneous reader group, against the requirement."""
    out = {}
    for key, need in required.items():
        app, cell, regime = key.split('/')
        counts = [g['counts']['accepted'] for g in groups if (g['app'], g['cell'], g['regime']) == (app, cell, regime)]
        out[key] = dict(required=need, accepted=max(counts, default=0), groups=len(counts))
    return out


def announce(message):
    print(f'worker-wait pilot: {message}', flush=True)


def main(argv=None):
    args = parse(sys.argv[1:] if argv is None else argv)
    source_app, artifacts = Path(args.app).resolve(), Path(args.artifacts).resolve()
    assert os.environ.get('PW_TEST_SCRATCH'), 'PW_TEST_SCRATCH is required for build intermediates'
    scratch = Path(os.environ['PW_TEST_SCRATCH']); scratch.mkdir(parents=True, exist_ok=True)
    entries, required = build_schedule(args.cells, args.regimes, args.repetitions)
    warm = warm_cells(args.cells)
    estimate = window_estimate(entries, len(warm) * len(APPS), not args.no_clock_pair, args.trial_watchdog_seconds)
    assert estimate['total_s'] <= args.window_seconds, f'declared schedule does not fit the window: {estimate}'
    source_before = inventory(source_app)
    save(artifacts / 'conditions-start.json', static_conditions(source_app))
    module = load_module('worker_wait_host_stamps', HOST_STAMPS)
    stamp_dir = Path(module.default_stamp_dir())
    assert stamp_dir.parent == STAMP_ROOT, stamp_dir
    worker_build = Path(args.worker_build).resolve()
    failures, apps, staging, stamp_dir_fd, cleanup = [], {}, artifacts / 'staging', None, None
    target_root = Path(tempfile.mkdtemp(prefix='pw-wait-', dir='/private/tmp'))
    try:
        hosts = {kind: build_host(module, kind, artifacts, scratch, stamp_dir) for kind in APPS}
        flavours = {kind: host_flavour(artifacts, kind) for kind in APPS}
        assert all(value == flavours['instrumented'] for value in flavours.values()), flavours
        apps = {kind: stage_app(module, kind, source_app, staging, args.identity, hosts[kind], worker_build) for kind in APPS}
        clock_pair = None
        if not args.no_clock_pair:
            clock_pair = load_module('worker_wait_clock_pair', CLOCK_PAIR)
            clock_binary = scratch / 'clock-pair' / 'clock_pair'
            clock_pair.build(clock_binary, artifacts / 'clock-pair-build')
        staged_before = {kind: staged_identity(apps[kind]) for kind in APPS}
        save(artifacts / 'staged-identity-before.json', staged_before)
        stamp_dir.mkdir(parents=True, mode=0o700)
        stamp_dir_fd = os.open(stamp_dir, os.O_EVTONLY)
        targets = make_targets(target_root)
        save(artifacts / 'targets.json', dict(root=str(target_root), files=len(targets['files']), ownership='driver temporary directory'))
        save(artifacts / 'schedule.json', dict(version=2, entries=entries, required=required, cells=args.cells, regimes=args.regimes,
             repetitions=args.repetitions, dry_run=args.dry_run, window_seconds=args.window_seconds, window_estimate=estimate,
             trial_watchdog_seconds=args.trial_watchdog_seconds, trial_cleanup_seconds=TRIAL_CLEANUP_S,
             requested_gap_ns=REQUESTED_GAP_NS, eligible_gap_ns=ELIGIBLE_GAP_NS, cli_timeout_ms=CLI_TIMEOUT_MS,
             coverage_rule=f'per app, cell and regime, at least min({COVERAGE_MIN_ACCEPTED}, repetitions) accepted trials in one '
                           'homogeneous reader group; excluded and skipped trials are retained and never replaced',
             declared_exclusions=DECLARED_EXCLUSIONS, started_check=STARTED_CHECK,
             stamp_wait_s=STAMP_WAIT_S, cli_exit_margin_ns=CLI_MARGIN_NS, stamp_dir=str(stamp_dir),
             clock_pair=None if args.no_clock_pair else dict(trials=args.clock_pair_trials, out='clock-pair'),
             host_flavour=flavours['instrumented'], worker_build=str(worker_build),
             warm_cells=warm, apps={k: str(v) for k, v in apps.items()},
             order='rapid block, then idle block; per repetition and cell both apps, instrumented first in even repetitions'))
        with FootprintObserver(args.observer) as observer:
            save(artifacts / 'observer-provenance.json', observer.provenance)
            pilot = Pilot(args, observer, apps, stamp_dir, stamp_dir_fd, module.stamp_paths, module.exported_path,
                          targets, flavours['instrumented'])
            driver_clock = driver_clock_check(observer)
            assert driver_clock['agrees'], f'driver clock is not the observer clock domain: {driver_clock}'
            window_start = observer.clock()
            pilot.window_end_ns = window_start['continuous_ns'] + int(args.window_seconds * 1e9)
            announce(f"window start ({args.window_seconds:.0f} s; {len(entries)} scheduled trials; estimate {estimate['total_s']:.1f} s)")
            if clock_pair is not None:
                try:
                    if not calibrate(clock_pair, clock_binary, artifacts, args.clock_pair_trials):
                        failures.append('clock-pair calibration incomplete')
                except (AssertionError, OSError, subprocess.SubprocessError) as exc:
                    failures.append(f'clock-pair calibration failed: {exc!r}')
            elif not args.dry_run:
                failures.append('clock-pair calibration not run (--no-clock-pair outside a dry run)')
            for kind in APPS:
                for cell in warm:
                    if pilot.stopped_for is not None or not pilot.fits('rapid')[0]:
                        failures.append(f'warm {kind} {cell}: not run (stopped_for={pilot.stopped_for})'); continue
                    receipt = pilot.run(dict(app=kind, cell=cell, regime='idle', index=0), artifacts / 'warm' / kind / cell, 'warm.json', warm=True)
                    if receipt['status'] != 'completed': failures.append(f'warm {kind} {cell}: {receipt["status"]}')
            for entry in entries:
                directory = artifacts / 'trials' / entry['app'] / entry['cell'] / entry['regime'] / str(entry['index'])
                if pilot.stopped_for is not None:
                    save(directory / 'trial.json', dict(entry, version=1, status='not_run_after_stop', stopped_for=pilot.stopped_for, dry_run=args.dry_run))
                    continue
                fits, remaining, need = pilot.fits(entry['regime'])
                if not fits:
                    save(directory / 'trial.json', dict(entry, version=1, status='skipped_window', remaining_ns=remaining, required_ns=need, dry_run=args.dry_run))
                    continue
                pilot.run(entry, directory, 'trial.json')
            window_end = observer.clock()
            announce(f'window end (stopped_for={pilot.stopped_for})')
            save(artifacts / 'window.json', dict(start=window_start, end=window_end, declared_seconds=args.window_seconds,
                                                 used_ns=window_end['continuous_ns'] - window_start['continuous_ns'], stopped_for=pilot.stopped_for,
                                                 estimate_s=estimate['total_s'], driver_clock=driver_clock))
        for path in sorted(artifacts.glob('warm/*/*/warm.json')) + sorted(artifacts.glob('trials/*/*/*/*/trial.json')):
            receipt = json.loads(path.read_text())
            if receipt['status'] == 'completed':
                problems = validate(path.parent, receipt)
                if problems and receipt.get('warm'): failures.append(f'warm validation {path.parent}: {problems}')
        staged_after = {kind: staged_identity(apps[kind]) for kind in APPS}
        save(artifacts / 'staged-identity-after.json', staged_after)
        if staged_after != staged_before: failures.append('staged executables changed during the pilot')
        _, summary = reader.read_artifacts(artifacts)
        if clock_pair is not None and summary['calibration_status'] != 'established':
            failures.append('clock-pair receipt not accepted: ' + summary['calibration_status'])
    finally:
        if apps:
            cleanup = final_cleanup(Path(args.observer), apps, artifacts)
            survivors = [a for a in cleanup['actions'] if a['disposition'] not in ('exited_within_grace', 'gone_or_generation_changed')]
            announce(f"final cleanup: {len(cleanup['found'])} staged processes found, {len(survivors)} survived the grace, settled {cleanup['settled']}")
            if survivors: failures.append(f"staged processes survived their runs: {[(a['app'], a['role'], a['pid'], a['disposition']) for a in survivors]}")
            if not cleanup['settled']: failures.append('final cleanup did not establish that no staged process remains; see cleanup.json')
        if stamp_dir_fd is not None:
            os.close(stamp_dir_fd)
        if stamp_dir.exists():
            residue = list(stamp_dir.iterdir())
            for path in residue:
                save(artifacts / 'stamp-dir-residue' / (path.name + '.receipt.json'), dict(name=path.name, size=path.stat().st_size))
                shutil.copyfile(path, artifacts / 'stamp-dir-residue' / path.name)
            shutil.rmtree(stamp_dir)
        if STAMP_ROOT.exists() and not any(STAMP_ROOT.iterdir()):
            STAMP_ROOT.rmdir()
        shutil.rmtree(target_root, ignore_errors=True)
        # Staging stays until no staged process is known to remain.
        if args.dry_run and staging.exists() and (cleanup is None or cleanup['settled']):
            shutil.rmtree(staging)
        assert inventory(source_app) == source_before, 'selected source app changed'
    rows = json.loads((artifacts / 'decomposition.json').read_text())['rows']
    blocking = [dict(dir=r['dir'], status=r['status'], problems=r['problems'], exclusions=r['exclusions'])
                for r in rows if r['status'] in ('failed', 'incomplete', 'refused')]
    retained = {status: [dict(dir=r['dir'], problems=r['problems'], exclusions=r['exclusions']) for r in rows if r['status'] == status]
                for status in ('excluded', 'skipped')}
    covered = coverage(summary['groups'], required)
    incomplete = sorted(key for key, value in covered.items() if value['accepted'] < value['required'])
    save(artifacts / 'pilot.json', dict(version=2, dry_run=args.dry_run, failures=failures, blocking=blocking,
                                        excluded=retained['excluded'], skipped=retained['skipped'], coverage=covered,
                                        incomplete=incomplete, counts=summary['counts'], calibration=summary['calibration_status'],
                                        cleanup_settled=(cleanup or {}).get('settled'), staging_retained=staging.exists()))
    assert not failures, failures
    assert not blocking, blocking
    assert len(rows) == len(entries), 'a scheduled entry has no receipt'
    assert not incomplete, f'incomplete pilot coverage: {incomplete}'
    print(f"worker-wait pilot: {summary['counts']['accepted']} accepted, {len(retained['excluded'])} excluded and "
          f"{len(retained['skipped'])} skipped trials; {len(covered)} app/cell/regime keys covered; "
          f"calibration {summary['calibration_status']}{'; dry run' if args.dry_run else ''}")


if __name__ == '__main__':
    main()
