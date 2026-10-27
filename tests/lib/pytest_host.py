"""The pytest host: a parent that starts pytest in a child and judges the child from a receipt.

A case starts this file through test_check_python, so the parent runs on the
pinned interpreter with -B -S and both streams go to the case's assertions
log. The parent imports nothing from the vendored set. It refuses any
inherited PYTEST* variable, then starts this same file in child mode with the
pinned interpreter, -B -S -P, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, every other
variable unchanged, the checkout-lock claim's descriptors passed on, and no new
session, so dispatcher cancellation reaches the child through the case's
process group. The child puts tests/lib/vendor first on sys.path, imports the
vendored pytest, and runs it with the receipt plugin and exactly the arguments
the parent chose: no ini file, environment variable or conftest can add one.

The receipt is one JSON line per event. The parent accepts only when the child
exited 0, the session finished with status 0, the recorded pytest is the
vendored pin, something was collected (and as much as the case expects, when
it says), nothing was deselected, every collected item has exactly one passed
report for each of its setup, call and teardown phases and no other item
report exists, and every subtest report passed. A collect-only or setup-only
run, an early stop, a body that calls os._exit, a killed child or a hook that
suppresses reports all leave items short of three passed reports. Terminal
text is never an acceptance input.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
VENDOR = HERE / 'vendor'
PYTEST_PIN = '9.1.1'
PHASES = ('setup', 'call', 'teardown')
RULES = ('child_exit', 'session_start', 'pytest_version', 'pytest_path', 'session_finish', 'collected',
         'expected_collected', 'deselected', 'item_reports', 'subtest_reports', 'expected_subtests')


def parse(argv):
    parser = argparse.ArgumentParser(description='Run pytest in a child and judge it from its receipt.', allow_abbrev=False)
    parser.add_argument('--receipt', required=True, help='JSON lines the child writes and the parent judges')
    parser.add_argument('--expect-collected', type=int, default=None, metavar='N',
                        help='a cross-check: the collected count must equal N')
    parser.add_argument('--expect-subtests', type=int, default=None, metavar='N',
                        help='a cross-check: the subtest report count must equal N')
    parser.add_argument('--pytest-arg', action='append', default=[], metavar='ARG',
                        help='an extra argument for pytest, for controls that give the child an option')
    parser.add_argument('--rootdir', default=None, help='the pytest root; the repository root by default')
    parser.add_argument('--drop-claim-descriptors', action='store_true',
                        help='a control knob: start the child without the checkout-lock descriptors')
    parser.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('tests', nargs='+', help='the test files pytest collects')
    return parser.parse_args(argv)


# ---- the child ---------------------------------------------------------------------------------

class Receipt:
    """Writes one JSON line per event, flushed as it happens."""

    def __init__(self, path, args, pytest_module):
        self.stream = open(path, 'w', encoding='utf-8')
        self.args = args
        self.pytest = pytest_module

    def write(self, **event):
        self.stream.write(json.dumps(event, sort_keys=True) + '\n')
        self.stream.flush()

    def pytest_sessionstart(self, session):
        self.write(event='session_start', pytest_version=self.pytest.__version__, pytest_file=self.pytest.__file__,
                   args=self.args, rootdir=str(session.config.rootpath), python=sys.executable, pid=os.getpid(),
                   site_loaded='site' in sys.modules)

    def pytest_collection_finish(self, session):
        self.write(event='collected', node_ids=[item.nodeid for item in session.items])

    def pytest_deselected(self, items):
        self.write(event='deselected', count=len(items))

    def pytest_collectreport(self, report):
        if report.failed:
            self.write(event='collect_error', node_id=report.nodeid, longrepr=str(report.longrepr)[:4000])

    def pytest_runtest_logreport(self, report):
        context = getattr(report, 'context', None)
        event = dict(event='report', node_id=report.nodeid, when=report.when, outcome=report.outcome,
                     duration=report.duration, subtest=context is not None)
        if context is not None:
            event.update(subtest_msg=context.msg, subtest_params=dict(context.kwargs))
        if report.failed or report.skipped:
            event['longrepr'] = str(report.longrepr)[:4000]
        self.write(**event)

    def pytest_sessionfinish(self, session, exitstatus):
        self.write(event='session_finish', exitstatus=int(exitstatus))
        self.stream.flush()


def child(options):
    sys.path.insert(0, str(VENDOR))
    import pytest
    root = Path(options.rootdir).resolve() if options.rootdir else HERE.parents[1]
    scratch = os.environ.get('PW_TEST_SCRATCH')
    if scratch:
        os.makedirs(scratch, exist_ok=True)
        basetemp = os.path.join(scratch, 'pytest-basetemp')
    else:
        basetemp = os.path.join(tempfile.mkdtemp(prefix='pw-pytest-', dir='/private/tmp'), 'basetemp')
    args = ['-c', '/dev/null', '--rootdir', str(root), '--noconftest', '-p', 'no:cacheprovider',
            '--import-mode=importlib', '--capture=no', '--basetemp', basetemp, '-rA', '-v', '--durations=0',
            *options.pytest_arg, *options.tests]
    receipt = Receipt(options.receipt, args, pytest)
    return int(pytest.main(args, plugins=[receipt]))


# ---- the parent --------------------------------------------------------------------------------

def refused_environment(env):
    """The inherited PYTEST* names, which pytest reads as arguments, plugins and settings."""
    return sorted(name for name in env if name.startswith('PYTEST'))


def read_receipt(path):
    """The receipt's events; a truncated last line is dropped, so a missing finish stays missing."""
    events = []
    try:
        text = Path(path).read_text(encoding='utf-8')
    except OSError:
        return events
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and isinstance(event.get('event'), str):
            events.append(event)
    return events


def judge(events, returncode, *, expect_collected=None, expect_subtests=None, vendor=VENDOR, pin=PYTEST_PIN):
    """Every violated rule as (rule, detail), in the order the rules are judged; empty means accepted."""
    problems = []
    if returncode != 0:
        problems.append(('child_exit', f'the pytest child exited {returncode}'
                         + (' (a signal)' if returncode < 0 else '')))
    starts = [e for e in events if e['event'] == 'session_start']
    if len(starts) != 1:
        problems.append(('session_start', f'{len(starts)} session_start records; expected one'))
    else:
        start = starts[0]
        if start.get('pytest_version') != pin:
            problems.append(('pytest_version', f"pytest {start.get('pytest_version')!r} ran; the vendored pin is {pin}"))
        try:
            Path(str(start.get('pytest_file'))).resolve().relative_to(Path(vendor).resolve())
        except ValueError:
            problems.append(('pytest_path', f"pytest loaded from {start.get('pytest_file')!r}, outside {vendor}"))
    finishes = [e for e in events if e['event'] == 'session_finish']
    if len(finishes) != 1:
        problems.append(('session_finish', f'{len(finishes)} session_finish records; expected one'))
    elif finishes[0].get('exitstatus') != 0:
        problems.append(('session_finish', f"the session finished with status {finishes[0].get('exitstatus')}"))
    collections = [e for e in events if e['event'] == 'collected']
    collected = list(collections[0].get('node_ids', [])) if len(collections) == 1 else []
    if len(collections) != 1 or not collected or any(not isinstance(n, str) for n in collected):
        problems.append(('collected', 'nothing was collected' if len(collections) == 1
                         else f'{len(collections)} collection records; expected one'))
    elif expect_collected is not None and len(collected) != expect_collected:
        problems.append(('expected_collected', f'{len(collected)} items collected; the case expects {expect_collected}'))
    deselected = sum(int(e.get('count', 0)) for e in events if e['event'] == 'deselected')
    if deselected:
        problems.append(('deselected', f'{deselected} items were deselected'))
    reports = [e for e in events if e['event'] == 'report']
    items = {node: {phase: [] for phase in PHASES} for node in collected}
    strays = []
    for report in reports:
        if report.get('subtest'):
            continue
        if report.get('node_id') not in items or report.get('when') not in PHASES:
            strays.append(report)
            continue
        items[report['node_id']][report['when']].append(report)
    for node in collected:
        for phase in PHASES:
            found = items[node][phase]
            if len(found) != 1:
                problems.append(('item_reports', f'{node}: {len(found)} {phase} reports; expected one'))
            elif found[0].get('outcome') != 'passed':
                problems.append(('item_reports', f"{node}: {phase} {found[0].get('outcome')}"))
    for report in strays:
        problems.append(('item_reports', f"{report.get('node_id')}: {report.get('when')} report for an uncollected item"))
    subtests = [r for r in reports if r.get('subtest')]
    for report in subtests:
        if report.get('outcome') != 'passed':
            problems.append(('subtest_reports', f"{report.get('node_id')} [{report.get('subtest_msg')}] "
                                                f"{report.get('subtest_params')}: {report.get('outcome')}"))
    if expect_subtests is not None and len(subtests) != expect_subtests:
        problems.append(('expected_subtests', f'{len(subtests)} subtest reports; the case expects {expect_subtests}'))
    order = {rule: index for index, rule in enumerate(RULES)}
    return sorted(problems, key=lambda problem: order[problem[0]])


def parent(options):
    refused = refused_environment(os.environ)
    if refused:
        print(f"ERROR: pytest_environment_set: {', '.join(refused)} set; the pytest host takes no pytest environment "
              f'(unset it)', file=sys.stderr)
        return 2
    receipt = Path(options.receipt)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text('')
    import checkout_lock
    argv = [sys.executable, '-B', '-S', '-P', str(Path(__file__).resolve()), '--child', '--receipt', str(receipt)]
    if options.rootdir:
        argv += ['--rootdir', options.rootdir]
    for extra in options.pytest_arg:
        argv.append(f'--pytest-arg={extra}')  # the = form carries a value that starts with a dash
    argv += ['--', *options.tests]
    pass_fds = () if options.drop_claim_descriptors else checkout_lock.inherited_fds()
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    process = subprocess.Popen(argv, env=env, pass_fds=pass_fds)
    while True:
        try:
            returncode = process.wait()
            break
        except KeyboardInterrupt:
            continue  # the child received the same signal; its exit decides
    problems = judge(read_receipt(receipt), returncode, expect_collected=options.expect_collected,
                     expect_subtests=options.expect_subtests)
    if problems:
        rule, detail = problems[0]
        print(f'ERROR: pytest host refused: {rule}: {detail}', file=sys.stderr)
        for rule, detail in problems[1:]:
            print(f'  also: {rule}: {detail}', file=sys.stderr)
        return 1
    events = read_receipt(receipt)
    collected = next(e for e in events if e['event'] == 'collected')['node_ids']
    subtests = sum(1 for e in events if e['event'] == 'report' and e.get('subtest'))
    print(f'pytest host: {len(collected)} items and {subtests} subtest reports passed; receipt {receipt}', flush=True)
    return 0


def main(argv=None):
    options = parse(sys.argv[1:] if argv is None else argv)
    return child(options) if options.child else parent(options)


if __name__ == '__main__':
    sys.exit(main())
