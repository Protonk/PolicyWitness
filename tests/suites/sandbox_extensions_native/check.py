"""M1 native experiments, independent of all PW result types and classifiers."""
import copy
import hashlib
import json
import os
from pathlib import Path
import plistlib
import signal
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
SCENARIOS = ('lifecycle', 'issuer_exit', 'no_consume', 'no_release', 'no_predicate',
             'different_target', 'issue_failure', 'rejected_token', 'retained_fd')
CONTENTS = b'PW independent extension witness\n'


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def command(argv, out, label, *, required=True):
    result = subprocess.run(list(map(str, argv)), capture_output=True, timeout=60)
    (out / (label + '.stdout')).write_bytes(result.stdout)
    (out / (label + '.stderr')).write_bytes(result.stderr)
    save(out / (label + '.command.json'), dict(argv=list(map(str, argv)), returncode=result.returncode))
    if required and result.returncode:
        raise AssertionError(f'{label} failed ({result.returncode}); see retained command and streams')
    return result


def file_identity(path):
    s = path.stat()
    return dict(device=s.st_dev, inode=s.st_ino, mode=s.st_mode, uid=s.st_uid, gid=s.st_gid, size=s.st_size)


def expect_read(a, identity, *, close=True, opened=True):
    assert bool(a['open_attempted']) == opened, 'fresh/retained descriptor distinction'
    if opened:
        assert a['open_rc'] >= 0 and a['open_errno'] == 0, 'fresh open missing'
    assert a['stat_attempted'] == 1 and a['stat_rc'] == 0, 'descriptor identity missing'
    assert a['identity'] == identity, 'opened descriptor is not the controlled file'
    assert a['read_attempted'] == 1 and a['read_rc'] == len(CONTENTS), 'read missing/short'
    assert a['content_hex'] == CONTENTS.hex(), 'known bytes were not retrieved'
    assert bool(a['close_attempted']) == close, 'close/retention observation missing'
    if close:
        assert a['close_rc'] == 0, 'descriptor close failed'


def expect_denied(a):
    assert a['open_attempted'] == 1 and a['open_rc'] == -1, 'controlled fresh open did not fail'
    assert a['open_errno'] in (1, 13), 'unexpected open failure; inspect native evidence'
    assert a['read_attempted'] == a['stat_attempted'] == a['close_attempted'] == 0, 'invented access after failed open'
    assert a['content_hex'] == '', 'invented read bytes'


def validate(r, target_identity, issue_identity):
    case = r['scenario']
    assert r['issue_flags'] == 0 and r['issue_class'] == 'com.apple.app-sandbox.read', 'native issue inputs differ'
    assert r['native_issue_path'] == ('' if case == 'issue_failure' else r['resolved_issue']), 'native issue path differs'
    assert r['failure'] == 0 and r['worker_done'] == 1, 'native harness incomplete'
    assert r['worker_reaped'] == r['issuer_reaped'] == 1, 'unconfirmed child cleanup'
    assert r['worker_wait_status'] == r['issuer_wait_status'] == 0, 'child failed'
    assert len({r['host_pid'], r['worker_pid'], r['issuer_pid']}) == 3, 'roles share a process'
    assert all(r[k] == os.getuid() != 0 for k in ('worker_uid', 'worker_euid', 'issuer_uid', 'issuer_euid')), 'issuer/worker authority differs'
    assert all(r[k] == os.getgid() for k in ('worker_gid', 'worker_egid', 'issuer_gid', 'issuer_egid')), 'group credentials differ'
    assert r['capability'] == r['compile_ok'] == r['apply_count'] == 1, 'policy/capability boundary missing'
    assert r['apply']['attempted'] and r['apply']['native_rc'] == 0, 'policy not applied'
    assert r['inherited_target_fds'] == r['inherited_other_target_fds'] == 0, 'preexisting target descriptor'
    assert r['target_identity'] == target_identity and r['issue_identity'] == issue_identity, 'host target preparation mismatch'
    assert r['consume_return_bits'] == 64 and r['release_return_bits'] == 32, 'native return width'
    assert r['worker_erased_channel'] and r['token_guard_passed'], 'token confinement observation missing'
    assert r['observed_boundaries'] == len(r['boundaries']) == 4, 'missing boundary'
    for i, b in enumerate(r['boundaries']):
        assert b['index'] == i and b['ack'] == 1, 'boundary/ack association'
        assert bool(b['issuer_waitpid_observed_live']) == (case != 'issuer_exit'), 'issuer lifetime observation missing'
        assert b['query']['attempted'] and type(b['query']['native_rc']) is int, 'query not observed'
        # Queries are observations; no agreement or deny/allow/deny oracle.
    expect_read(r['parent_baseline'], target_identity)
    expect_read(r['boundaries'][0]['access'], target_identity)
    expect_denied(r['boundaries'][1]['access'])
    if case == 'issue_failure':
        assert r['issue']['attempted'] and not r['issue']['nonnull'], 'native issue refusal not established'
        assert r['token_length'] == 0 and not r['consume']['attempted'], 'invented token/consumption'
    else:
        assert r['issue']['attempted'] and r['issue']['nonnull'], 'issuance failed'
        assert 0 < r['token_length'] < 16384, 'token transfer bounds'
    if case in ('issue_failure', 'no_consume'):
        assert not r['consume']['attempted'] and r['consume']['native_rc'] is None, 'omitted consumption invented'
    elif case == 'rejected_token':
        assert r['consume']['attempted'] and r['consume']['native_rc'] == -1, 'invalid token accepted'
    else:
        assert r['consume']['attempted'] and r['consume']['native_rc'] != -1, 'real consume handle missing'
    if case in ('issue_failure', 'no_consume', 'rejected_token', 'no_release'):
        assert not r['release']['attempted'] and r['release']['native_rc'] is None, 'release without an intended usable handle'
    else:
        assert r['release']['attempted'] and type(r['release']['native_rc']) is int, 'release result missing'
    if case in ('issue_failure', 'no_consume', 'rejected_token', 'no_predicate', 'different_target'):
        expect_denied(r['boundaries'][2]['access'])
        expect_denied(r['boundaries'][3]['access'])
    else:
        expect_read(r['boundaries'][2]['access'], target_identity, close=case != 'retained_fd')
        after = r['boundaries'][3]['access']
        if after['open_rc'] >= 0:
            expect_read(after, target_identity)
        else:
            expect_denied(after)
        if case == 'no_release':
            expect_read(after, target_identity)
    if case == 'retained_fd':
        assert r['retained']['seek_attempted'] and r['retained']['seek_rc'] == 0, 'retained descriptor rewind missing'
        expect_read(r['retained'], target_identity, opened=False)
    else:
        assert not r['retained']['read_attempted'], 'unexpected retained-descriptor observation'
    assert bool(r['issuer_exited_before_queries']) == (case == 'issuer_exit'), 'issuer lifetime intervention missing'
    if r['instrumented']:
        assert r['logger_available'], 'allocator instrumentation unavailable'
        for key in ('positive_before', 'positive_after'):
            assert r[key]['alloc'] and r[key]['dealloc'], 'allocator positive control failed'
        if r['syscall_logger_available']:
            for key in ('positive_before', 'positive_after'):
                assert r[key]['vm_alloc'] and r[key]['vm_dealloc'], 'VM instrumentation positive control failed'


def checker_controls(reference, identity):
    changes = {
        'missing_handle': lambda r: r['consume'].update(native_rc=-1),
        'missing_release': lambda r: r['release'].update(attempted=False),
        'missing_read': lambda r: r['boundaries'][2]['access'].update(read_attempted=0),
        'wrong_content': lambda r: r['boundaries'][2]['access'].update(content_hex='00'),
        'wrong_identity': lambda r: r['boundaries'][2]['access']['identity'].update(inode=0),
        'inherited_fd': lambda r: r.update(inherited_target_fds=1),
        'reap_unknown': lambda r: r.update(worker_reaped=0),
        'wrong_boundary': lambda r: r['boundaries'][2].update(index=1),
        'missing_query': lambda r: r['boundaries'][2]['query'].update(attempted=False),
        'token_not_erased': lambda r: r.update(worker_erased_channel=False),
        'reapply': lambda r: r.update(apply_count=2),
        'extra_authority': lambda r: r.update(issuer_euid=0),
    }
    validate(reference, identity, identity)
    for name, change in changes.items():
        value = copy.deepcopy(reference)
        change(value)
        try:
            validate(value, identity, identity)
        except AssertionError:
            continue
        raise AssertionError('checker admitted ' + name)
    # Native query and release observations are not forced to a desired pattern.
    for answer in (-1, 0, 1):
        value = copy.deepcopy(reference)
        for b in value['boundaries']:
            b['query'].update(native_rc=answer, errno_after_zeroing=22 if answer == -1 else 0)
        validate(value, identity, identity)
    value = copy.deepcopy(reference)
    value['release'].update(native_rc=-1, errno_after_zeroing=22)
    validate(value, identity, identity)
    value = copy.deepcopy(reference)
    value['boundaries'][3]['access'] = copy.deepcopy(value['boundaries'][2]['access'])
    validate(value, identity, identity)
    return dict(rejected=list(changes), accepted=['reference', 'unavailable_queries', 'unchanged_queries', 'failed_release_native_result', 'fresh_access_after_release'])


def run_experiment(binary, folder, case, target, issue, instrument):
    folder.mkdir(exist_ok=True)
    argv = [str(binary), case, str(target), str(issue), 'instrument' if instrument else 'plain']
    start = time.monotonic()
    with (folder / 'native.json').open('xb') as stdout, (folder / 'native.stderr').open('xb') as stderr:
        p = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
        timed_out = False
        try:
            p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=5)
        except BaseException:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait(timeout=5)
            raise
    save(folder / 'command.json', dict(argv=argv, host_pid=p.pid, returncode=p.returncode,
                                     harness_timeout=timed_out, elapsed_seconds=time.monotonic() - start))
    assert not timed_out, 'native experiment exceeded harness deadline'
    assert p.returncode == 0, f'{folder.name}: native failure; inspect native.json and command.json'
    r = json.loads((folder / 'native.json').read_bytes())
    assert r['host_pid'] == p.pid
    return r


def prepare(out):
    binary = out / 'native'
    identity = os.environ.get('PW_BYOXPC_IDENTITY') or os.environ.get('IDENTITY')
    assert identity and identity.startswith('Developer ID Application: '), 'explicit Developer ID identity required'
    source_files = ['tests/fixtures/sandbox_extensions/native.c', 'tests/fixtures/sandbox_extensions/build.sh',
                    'tests/suites/sandbox_extensions_native/directory_check.py', 'tests/suites/sandbox_extensions_native/directory.sh',
                    'tests/suites/sandbox_extensions_native/check.py', 'tests/suites/sandbox_extensions_native/run.sh',
                    'tests/catalog.json', 'tests/lib/case.sh', 'tests/lib/testlib.sh', 'tests/lib/python_start.sh', 'tests/lib/sdk_guard.sh', 'tests/lib/test_cli.py',
                    'tests/lib/suite_run.py', 'tests/fixtures/sandbox_extensions/README.md',
                    'tests/suites/sandbox_extensions_native/README.md']
    source_hashes = {}
    for name in source_files:
        data = (ROOT / name).read_bytes()
        destination = out / 'source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        source_hashes[name] = hashlib.sha256(data).hexdigest()
    save(out / 'source-hashes.json', source_hashes)
    for label, argv in [
        ('source-commit', ['git', 'rev-parse', 'HEAD']), ('source-status', ['git', 'status', '--short']),
        ('host', ['/usr/bin/sw_vers']), ('architecture', ['/usr/bin/uname', '-m']),
        ('credentials', ['/usr/bin/id']), ('sdk', ['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path']),
        ('compiler', ['/usr/bin/xcrun', 'clang', '--version']),
        ('identities', ['/usr/bin/security', 'find-identity', '-v', '-p', 'codesigning'])]:
        command(argv, out, label)
    command(['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp', '-s', identity, binary], out, 'sign')
    command(['/usr/bin/codesign', '--verify', '--strict', '--verbose=4', binary], out, 'verify')
    signature = command(['/usr/bin/codesign', '-dvvv', binary], out, 'signature')
    assert ('Authority=' + identity).encode() in signature.stderr and b'runtime' in signature.stderr
    ent = command(['/usr/bin/codesign', '-d', '--entitlements', ':-', binary], out, 'entitlements')
    assert not ent.stdout.strip() or plistlib.loads(ent.stdout) == {}, 'unexpected fixture entitlements'
    binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
    save(out / 'equipment.json', dict(identity=identity, binary_sha256=binary_hash,
        entitlements={}, roles_share_signed_executable=True, uid=os.getuid(), gid=os.getgid(),
        child_environment=['PATH=/usr/bin:/bin', 'LC_ALL=C']))
    return binary_hash


def main():
    out = Path(sys.argv[1]).resolve()
    binary = out / 'native'
    binary_hash = prepare(out)
    for symbol in ('malloc_logger', '__syscall_logger'):
        command([binary, '--allocation-probe', symbol], out, symbol, required=False)
    results = []
    failures = []
    with tempfile.TemporaryDirectory(prefix='pw-extension-', dir='/private/tmp') as directory:
        work = Path(directory)
        target, other, link = work / 'target', work / 'other', work / 'issue-link'
        target.write_bytes(CONTENTS); target.chmod(0o600)
        other.write_bytes(b'independent different target\n'); other.chmod(0o600)
        link.symlink_to(target.name)
        target_id, other_id = file_identity(target), file_identity(other)
        assert stat.S_ISREG(target_id['mode']) and target_id['uid'] == os.getuid()
        save(out / 'targets.json', dict(target=str(target), submitted_issue=str(link), resolved_issue=str(link.resolve()),
            target_identity=target_id, other_identity=other_id, known_content_hex=CONTENTS.hex()))
        for instrument in (False, True):
            for case in SCENARIOS:
                name = case + ('-instrumented' if instrument else '-plain')
                try:
                    r = run_experiment(binary, out / name, case, target, other if case == 'different_target' else link, instrument)
                    assert r['resolved_issue'] == str((other if case == 'different_target' else target).resolve())
                    validate(r, target_id, other_id if case == 'different_target' else target_id)
                    assert target.read_bytes() == CONTENTS and file_identity(target) == target_id, 'controlled target changed'
                    results.append(r)
                    print(name + ': passed', flush=True)
                except (AssertionError, ValueError) as error:
                    failures.append(dict(case=name, error=str(error)))
                    print(name + ': ' + str(error), flush=True)
        reference = next((r for r in results if r['scenario'] == 'lifecycle' and not r['instrumented']), None)
        if reference:
            save(out / 'checker-controls.json', checker_controls(reference, target_id))
        else:
            failures.append(dict(case='checker_controls', error='no accepted positive reference'))
    save(out / 'summary.json', dict(passed=len(results), expected=len(SCENARIOS) * 2, failures=failures,
        observations=[dict(scenario=r['scenario'], instrumented=r['instrumented'],
            consume=r['consume'], release=r['release'],
            query_returns=[b['query']['native_rc'] for b in r['boundaries']],
            fresh_open_returns=[b['access']['open_rc'] for b in r['boundaries']]) for r in results]))
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == binary_hash, 'experiment binary changed'
    assert len(results) == len(SCENARIOS) * 2, 'incomplete scenario matrix'
    assert not failures, f'{len(failures)} native controls failed; see summary.json'
    print('all native controls passed; token bytes were never retained')


if __name__ == '__main__':
    main()
