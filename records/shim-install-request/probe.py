"""Contained probe: which developer-tool shim, xcrun and xcode-select inputs request a Command Line Tools installation.

Run with nothing inherited, so no shim sees the caller's SDKROOT or DEVELOPER_DIR:

    env -i PATH=/usr/bin:/bin HOME="$HOME" /usr/bin/python3 -I -B records/shim-install-request/probe.py FIXTURE

FIXTURE must not exist. Every shim run is inside sandbox-exec with Mach lookups
denied, so no request can reach the installer, and with writes limited to the
fixture. Containment is checked first with a Mach-dependent read that must
succeed outside and fail inside; nothing else runs unless it does. Each run
starts from PATH, HOME and TMPDIR plus its condition's variables. Afterwards the
unified log is searched for lookups of the install service, each attributed to
the run whose time window contains it. FIXTURE/results.json keeps every output;
FIXTURE/summary.json keeps the comparison, with the fixture path and home
directory replaced.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

SERVICE = 'com.apple.dt.CommandLineTools.installondemand'
# The shim's own wording: the first when the request goes out, the second when it cannot be made.
PHRASES = ('requesting install', 'no install could be requested')
fixture = Path(sys.argv[1]).resolve()
fixture.mkdir(parents=True)
(fixture / 'tmp').mkdir()
home = os.environ['HOME']
BASE = dict(PATH='/usr/bin:/bin', HOME=home, TMPDIR=str(fixture / 'tmp'))
profile = fixture / 'contained.sb'
profile.write_text('(version 1)(allow default)(deny mach-lookup)'
                   '(deny file-write*)(allow file-write* (subpath ' + json.dumps(str(fixture)) + ')'
                   ' (literal "/dev/null") (literal "/dev/dtracehelper"))\n')
SANDBOX = ['/usr/bin/sandbox-exec', '-f', str(profile)]
not_an_sdk = fixture / 'not-an-sdk'
not_an_sdk.mkdir()


def output(argv):
    return subprocess.run(argv, env=BASE, capture_output=True, text=True).stdout.strip()


def run(argv, extra=None, contained=True, **labels):
    started = time.time()
    try:
        done = subprocess.run((SANDBOX if contained else []) + argv, env=dict(BASE, **(extra or {})), capture_output=True,
                              text=True, timeout=60, cwd=fixture)
        status, out, err = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as exc:
        status, out, err = 'timeout', exc.stdout or '', exc.stderr or ''
    time.sleep(0.5)  # keep each run's log window apart from the next
    return dict(labels, argv=argv, extra=extra or {}, contained=contained, status=status, stdout=out, stderr=err,
                started=started, finished=time.time())


selected = Path(output(['/usr/bin/xcode-select', '-p']))
results = dict(macos=output(['/usr/bin/sw_vers', '-productVersion']), build=output(['/usr/bin/sw_vers', '-buildVersion']),
               xcode=output(['/usr/bin/xcodebuild', '-version']).replace('\n', ' '), developer_dir=str(selected),
               profile=profile.read_text(), installer_before=output(['/usr/bin/pgrep', '-lf', 'Install Command Line Developer Tools']))
log_start = time.strftime('%Y-%m-%d %H:%M:%S')
time.sleep(1)

check = ['/usr/bin/dscl', '.', '-read', '/Users/root', 'UniqueID']
results['containment'] = dict(outside=run(check, contained=False), inside=run(check))
outside, inside = results['containment']['outside'], results['containment']['inside']
if not (outside['status'] == 0 and 'UniqueID: 0' in outside['stdout'] and inside['status'] != 0):
    (fixture / 'results.json').write_text(json.dumps(results, indent=2))
    sys.exit('containment not established; no shim was run')


def stand_in(name, tool, *, xcrun=False, app=False, xcodebuild=False):
    """A developer directory with only the named pieces, each a link to the selected one's."""
    root = fixture / 'stand-ins' / name
    developer = root / 'Fake.app/Contents/Developer' if app else root
    (developer / 'usr/bin').mkdir(parents=True)
    if app:
        for plist in ('Info.plist', 'version.plist'):
            shutil.copy2(selected.parent / plist, developer.parent / plist)
    if xcrun:
        (developer / 'usr/lib').mkdir()
        (developer / 'usr/lib/libxcrun.dylib').symlink_to(selected / 'usr/lib/libxcrun.dylib')
    for linked in (tool,) + (('xcodebuild',) if xcodebuild else ()):
        (developer / 'usr/bin' / linked).symlink_to(selected / 'usr/bin' / linked)
    return str(developer)


TOOLS = {'make': ['/usr/bin/make', '--version'], 'python3': ['/usr/bin/python3', '-V'], 'git': ['/usr/bin/git', '--version']}
runs = []
for tool, argv in TOOLS.items():
    empty = fixture / 'stand-ins' / f'{tool}-empty'
    empty.mkdir(parents=True)
    conditions = [
        ('baseline', {}),
        ('SDKROOT names a missing path', dict(SDKROOT=str(fixture / 'no-such.sdk'))),
        ('SDKROOT names an unknown SDK', dict(SDKROOT='pwnosuchsdk')),
        ('SDKROOT names a directory that is not an SDK', dict(SDKROOT=str(not_an_sdk))),
        ('SDKROOT empty', dict(SDKROOT='')),
        ('DEVELOPER_DIR missing', dict(DEVELOPER_DIR=str(fixture / 'no-such-developer'))),
        ('DEVELOPER_DIR empty', dict(DEVELOPER_DIR=str(empty))),
        ('DEVELOPER_DIR with the tool', dict(DEVELOPER_DIR=stand_in(f'{tool}-tool', tool))),
        ('DEVELOPER_DIR with libxcrun and the tool', dict(DEVELOPER_DIR=stand_in(f'{tool}-xcrun', tool, xcrun=True))),
        ('DEVELOPER_DIR Xcode-shaped, no xcodebuild', dict(DEVELOPER_DIR=stand_in(f'{tool}-app', tool, xcrun=True, app=True))),
        ('DEVELOPER_DIR Xcode-shaped with xcodebuild',
         dict(DEVELOPER_DIR=stand_in(f'{tool}-app-xcodebuild', tool, xcrun=True, app=True, xcodebuild=True))),
    ]
    for condition, extra in conditions:
        runs.append(run(argv, extra, tool=tool, condition=condition))

# An SDKROOT given as a make argument: make exports it to recipes, which run $(MAKE) and a /usr/bin/python3 leaf.
makefile = fixture / 'chain.mk'
makefile.write_text('outer:\n\t@echo "recipe SDKROOT=[$$SDKROOT] MAKE=$(MAKE)"\n'
                    '\t@$(MAKE) -s -f ' + str(makefile) + ' inner\n'
                    '\t@/usr/bin/python3 -c "print(\'leaf ran\')"\n'
                    'inner:\n\t@echo "inner SDKROOT=[$$SDKROOT]"\n')
runs.append(run(['/usr/bin/make', '-s', '-f', str(makefile), 'outer', 'SDKROOT=' + str(fixture / 'no-such.sdk')],
                tool='make', condition='SDKROOT as a make argument; recipe runs $(MAKE) and /usr/bin/python3'))

# xcrun and xcode-select are separate binaries, not the shim: build.sh resolves the caller's SDK request with
# xcrun --sdk ... --show-sdk-path, and the direct Python resolver runs xcode-select -p.
missing_sdk = str(fixture / 'no-such.sdk')
xcrun_empty = fixture / 'stand-ins' / 'xcrun-empty'
xcrun_empty.mkdir(parents=True)
xcrun_app = stand_in('xcrun-app', 'make', xcrun=True, app=True)
for tool, condition, argv, extra in (
        ('xcrun', 'baseline: --sdk macosx', ['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'], {}),
        ('xcrun', '--sdk names a missing path', ['/usr/bin/xcrun', '--sdk', missing_sdk, '--show-sdk-path'], {}),
        ('xcrun', '--sdk names an unknown SDK', ['/usr/bin/xcrun', '--sdk', 'pwnosuchsdk', '--show-sdk-path'], {}),
        ('xcrun', '--sdk names a directory that is not an SDK', ['/usr/bin/xcrun', '--sdk', str(not_an_sdk), '--show-sdk-path'], {}),
        ('xcrun', '--show-sdk-version; --sdk names a missing path', ['/usr/bin/xcrun', '--sdk', missing_sdk, '--show-sdk-version'], {}),
        ('xcrun', '--show-sdk-version; --sdk names a directory that is not an SDK',
         ['/usr/bin/xcrun', '--sdk', str(not_an_sdk), '--show-sdk-version'], {}),
        ('xcrun', '--show-sdk-path; SDKROOT names a missing path', ['/usr/bin/xcrun', '--show-sdk-path'], dict(SDKROOT=missing_sdk)),
        ('xcrun', '-f clang; SDKROOT names a missing path', ['/usr/bin/xcrun', '-f', 'clang'], dict(SDKROOT=missing_sdk)),
        ('xcrun', '--sdk macosx; DEVELOPER_DIR empty', ['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'],
         dict(DEVELOPER_DIR=str(xcrun_empty))),
        ('xcrun', '--sdk macosx; DEVELOPER_DIR Xcode-shaped, no xcodebuild',
         ['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'], dict(DEVELOPER_DIR=xcrun_app)),
        ('xcode-select', '-p; DEVELOPER_DIR empty', ['/usr/bin/xcode-select', '-p'], dict(DEVELOPER_DIR=str(xcrun_empty))),
        ('xcode-select', '-p; SDKROOT names a missing path', ['/usr/bin/xcode-select', '-p'], dict(SDKROOT=missing_sdk))):
    runs.append(run(argv, extra, tool=tool, condition=condition))

time.sleep(2)
results['installer_after'] = output(['/usr/bin/pgrep', '-lf', 'Install Command Line Developer Tools'])
log = subprocess.run(['/usr/bin/log', 'show', '--style', 'ndjson', '--start', log_start, '--predicate',
                      f'eventMessage CONTAINS "{SERVICE}"'], env=BASE, capture_output=True, text=True)
lookups = []
for line in log.stdout.splitlines():
    if line.startswith('{'):
        event = json.loads(line)
        if 'timestamp' in event and 'log run' not in event.get('eventMessage', ''):
            when = datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S.%f%z').timestamp()
            lookups.append(dict(at=when, message=event['eventMessage']))
results['log_status'] = log.returncode
for record in runs + [inside, outside]:
    record['install_lookups'] = [e['message'] for e in lookups if record['started'] <= e['at'] <= record['finished']]
results['runs'] = runs
results['unattributed_lookups'] = [e['message'] for e in lookups
                                   if not any(r['started'] <= e['at'] <= r['finished'] for r in runs)]
(fixture / 'results.json').write_text(json.dumps(results, indent=2))


def scrub(text):
    return text.replace(str(fixture), '<fixture>').replace(home, '~')


summary = dict({k: results[k] for k in ('macos', 'build', 'xcode', 'developer_dir', 'installer_before', 'installer_after',
                                         'log_status', 'unattributed_lookups')},
               containment=dict(outside=outside['status'], inside=inside['status'], inside_stderr=scrub(inside['stderr'].strip())),
               runs=[])
for record in runs:
    text = scrub(record['stderr'] + record['stdout'])
    summary['runs'].append(dict(
        tool=record['tool'], condition=record['condition'], status=record['status'],
        install_lookups=len(record['install_lookups']) // 2,  # the kernel's denial and launchd's report
        install_messages=[line for line in text.splitlines() if any(p in line for p in PHRASES)],
        first_error=next((line for line in text.splitlines() if 'error' in line and 'DVT' not in line), None)))
(fixture / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
for row in summary['runs']:
    print('%-12s %-52s %-8s lookups=%d %s' % (row['tool'], row['condition'], row['status'], row['install_lookups'],
                                            (row['install_messages'] or [row['first_error'] or ''])[0][:90]))
print('installer before/after:', repr(summary['installer_before']), repr(summary['installer_after']),
      '| unattributed lookups:', len(summary['unattributed_lookups']))
