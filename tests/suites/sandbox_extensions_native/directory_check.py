"""Directory effects, independent of production PW actions and classifications."""
import copy
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import (CONTENTS, expect_denied, expect_read, file_identity, prepare,
                   run_experiment, save)

SCENARIOS = ('directory', 'directory_no_consume', 'directory_no_predicate',
             'directory_different', 'directory_read_only')
PAYLOAD = b'PW directory effect\n'
POLICY = ('(version 1) (allow default) (deny file-read-data) (deny file-write*) '
          '(allow file-read-data (extension "com.apple.app-sandbox.read") '
          '(extension "com.apple.app-sandbox.read-write")) '
          '(allow file-write* (extension "com.apple.app-sandbox.read-write"))')
NO_PREDICATE = '(version 1) (allow default) (deny file-read-data) (deny file-write*)'


def absent(p):
    assert p['attempted'] == 1 and p['rc'] == -1 and p['errno'] == 2, 'absence not observed'


def same_file(left, right):
    assert {k: v for k, v in left.items() if k != 'size'} == {
        k: v for k, v in right.items() if k != 'size'}, 'file identity changed'


def snapshot(a, content, identity):
    assert a['open_attempted'] == 1, 'external open missing'
    if content is None:
        assert a['open_rc'] == -1 and a['open_errno'] == 2, 'absent child became present'
        assert a['stat_attempted'] == a['read_attempted'] == a['close_attempted'] == 0
        assert not a['content_hex']
        return
    assert a['open_rc'] >= 0 and a['stat_attempted'] == 1 and a['stat_rc'] == 0
    assert a['read_attempted'] == 1 and a['read_rc'] == len(content), 'external read missing/short'
    assert a['content_hex'] == content.hex(), 'external contents differ'
    assert a['close_attempted'] == 1 and a['close_rc'] == 0, 'external close missing'
    same_file(a['identity'], identity)
    assert a['identity']['size'] == len(content), 'external size differs'


def observed_write(w, create, initial):
    """Model effects from individual native observations, including partial writes."""
    if create:
        absent(w['before'])
    else:
        assert w['before']['attempted'] == 1 and w['before']['rc'] == 0
        assert w['before']['identity'] == initial
    assert w['open']['attempted'] and type(w['open']['native_rc']) is int
    if w['open']['native_rc'] < 0:
        assert w['open']['native_rc'] == -1 and w['open']['errno_after_zeroing'] in (1, 13)
        for key in ('truncate', 'write', 'close', 'opened', 'truncated', 'written'):
            assert not w[key]['attempted'], 'invented result after failed open'
        return (None, None) if create else (CONTENTS, initial)
    assert w['opened']['attempted'] == 1 and w['opened']['rc'] == 0
    identity = w['opened']['identity']
    if create:
        assert stat.S_ISREG(identity['mode']) and stat.S_IMODE(identity['mode']) == 0o600
        assert identity['uid'] == os.getuid() and identity['gid'] == os.getgid()
        assert identity['size'] == 0, 'new child not empty at open'
        assert not w['truncate']['attempted'] and not w['truncated']['attempted']
        content = b''
    else:
        assert identity == initial, 'write open changed target identity or truncated implicitly'
        assert w['truncate']['attempted'] and type(w['truncate']['native_rc']) is int
        assert w['truncated']['attempted'] == 1 and w['truncated']['rc'] == 0
        same_file(w['truncated']['identity'], initial)
        content = b'' if w['truncate']['native_rc'] == 0 else CONTENTS
        assert w['truncated']['identity']['size'] == len(content), 'truncation observation missing'
    write_expected = create or w['truncate']['native_rc'] == 0
    assert bool(w['write']['attempted']) == write_expected
    if write_expected:
        count = w['write']['native_rc']
        assert type(count) is int and -1 <= count <= len(PAYLOAD)
        content = PAYLOAD[:max(0, count)]
        assert w['written']['attempted'] == 1 and w['written']['rc'] == 0
        same_file(w['written']['identity'], identity)
        assert w['written']['identity']['size'] == len(content), 'transferred size differs'
    else:
        assert not w['written']['attempted']
    assert w['close']['attempted'] and type(w['close']['native_rc']) is int, 'close result missing'
    return content, identity


def validate(r, target_identity, issue_identity, initial):
    case = r['scenario']
    assert case in SCENARIOS
    assert r['issue_class'] == ('com.apple.app-sandbox.read' if case == 'directory_read_only'
                                else 'com.apple.app-sandbox.read-write')
    assert r['issue_flags'] == 0 and r['native_issue_path'] == r['resolved_issue']
    assert r['policy'] == (NO_PREDICATE if case == 'directory_no_predicate' else POLICY)
    assert r['failure'] == 0 and r['worker_done'] == 1
    assert r['worker_reaped'] == r['issuer_reaped'] == 1, 'unconfirmed cleanup'
    assert r['worker_wait_status'] == r['issuer_wait_status'] == 0
    assert len({r['host_pid'], r['worker_pid'], r['issuer_pid']}) == 3
    assert all(r[k] == os.getuid() != 0 for k in ('worker_uid', 'worker_euid', 'issuer_uid', 'issuer_euid'))
    assert all(r[k] == os.getgid() for k in ('worker_gid', 'worker_egid', 'issuer_gid', 'issuer_egid'))
    assert r['capability'] == r['compile_ok'] == r['apply_count'] == 1
    assert r['apply']['attempted'] and r['apply']['native_rc'] == 0
    assert r['inherited_target_fds'] == r['inherited_other_target_fds'] == r['directory']['inherited_file_fds'] == 0
    assert r['target_identity'] == target_identity and r['issue_identity'] == issue_identity
    assert r['consume_return_bits'] == 64 and r['release_return_bits'] == 32
    assert r['worker_erased_channel'] and r['token_guard_passed']
    assert r['issue']['attempted'] and r['issue']['nonnull'] and 0 < r['token_length'] < 16384
    consume = case != 'directory_no_consume'
    assert bool(r['consume']['attempted']) == bool(r['release']['attempted']) == consume
    if consume:
        assert type(r['consume']['native_rc']) is int and r['consume']['native_rc'] != -1
        assert type(r['release']['native_rc']) is int
    else:
        assert r['consume']['native_rc'] is r['release']['native_rc'] is None
    assert r['observed_boundaries'] == len(r['boundaries']) == len(r['directory']['boundaries']) == 4
    assert not r['retained']['read_attempted'] and not r['instrumented']
    paths = []
    for i, (b, d) in enumerate(zip(r['boundaries'], r['directory']['boundaries'])):
        assert b['index'] == d['index'] == i and b['ack'] == 1
        assert b['issuer_waitpid_observed_live'] == 1
        for key in ('query', 'write_query'):
            assert b[key]['attempted'] and type(b[key]['native_rc']) is int
        assert d['existing'] == str(Path(r['target']) / f'existing-{i}')
        assert d['child'] == str(Path(r['target']) / f'child-{i}')
        paths.extend((d['existing'], d['child']))
        assert d['existing_identity'] == initial[i]
        absent(d['issuance_absence']); absent(d['host_absence'])
        assert d['child_prediction'] == dict(attempted=False, reason='unresolved_absent_child')
        read_allowed = i == 0 or (i == 2 and case in ('directory', 'directory_read_only'))
        if i == 3 and case in ('directory', 'directory_read_only'):
            read_allowed = b['access']['open_rc'] >= 0
        if read_allowed:
            expect_read(b['access'], initial[i])
        else:
            expect_denied(b['access'])
        assert len(d['operations']) == 2
        for create, op in enumerate(d['operations']):
            w = op['write']
            content, identity = observed_write(w, bool(create), initial[i])
            must_succeed = i == 0 or (i == 2 and case == 'directory')
            must_deny = i == 1 or (i > 1 and case != 'directory')
            if must_succeed:
                assert w['open']['native_rc'] >= 0 and content == PAYLOAD, 'positive write effect missing'
                assert w['close']['native_rc'] == 0, 'positive close failed'
                if not create:
                    assert w['truncate']['native_rc'] == 0
            if must_deny:
                assert w['open']['native_rc'] == -1, 'negative control opened write target'
            snapshot(op['completed'], content, identity)
            snapshot(op['after_exit'], content, identity)
            if i < 3:
                snapshot(op['after_release'], content, identity)
            else:
                snapshot(op['after_release'], None if create else CONTENTS, None if create else initial[i])
    assert len(set(paths)) == 8, 'boundary target reused'


def checker_controls(reference, target, initial):
    def operation(r):
        return r['directory']['boundaries'][2]['operations'][0]
    changes = {
        'issuance_absence': lambda r: r['directory']['boundaries'][2]['issuance_absence'].update(rc=0),
        'host_absence': lambda r: r['directory']['boundaries'][2]['host_absence'].update(attempted=0),
        'worker_absence': lambda r: r['directory']['boundaries'][2]['operations'][1]['write']['before'].update(rc=0),
        'truncate': lambda r: operation(r)['write']['truncate'].update(attempted=False),
        'write': lambda r: operation(r)['write']['write'].update(native_rc=0),
        'close': lambda r: operation(r)['write']['close'].update(attempted=False),
        'identity': lambda r: operation(r)['write']['opened']['identity'].update(inode=0),
        'release_contents': lambda r: operation(r)['after_release'].update(content_hex='00'),
        'exit_contents': lambda r: operation(r)['after_exit'].update(content_hex='00'),
        'reused_child': lambda r: r['directory']['boundaries'][3].update(child=r['directory']['boundaries'][2]['child']),
        'missing_query': lambda r: r['boundaries'][2]['write_query'].update(attempted=False),
        'invented_prediction': lambda r: r['directory']['boundaries'][2]['child_prediction'].update(attempted=True),
        'inherited_fd': lambda r: r['directory'].update(inherited_file_fds=1),
        'cleanup': lambda r: r.update(worker_reaped=0),
        'erasure': lambda r: r.update(worker_erased_channel=False),
        'reapply': lambda r: r.update(apply_count=2),
        'issuer_authority': lambda r: r.update(issuer_euid=0),
        'handle': lambda r: r['consume'].update(native_rc=-1),
    }
    validate(reference, target, target, initial)
    for name, change in changes.items():
        value = copy.deepcopy(reference); change(value)
        try:
            validate(value, target, target, initial)
        except AssertionError:
            continue
        raise AssertionError('checker admitted ' + name)
    for answer in (-1, 0, 1):
        value = copy.deepcopy(reference)
        for b in value['boundaries']:
            for key in ('query', 'write_query'):
                b[key].update(native_rc=answer, errno_after_zeroing=22 if answer == -1 else 0)
        validate(value, target, target, initial)
    value = copy.deepcopy(reference)
    value['release'].update(native_rc=-1, errno_after_zeroing=22)
    validate(value, target, target, initial)
    return dict(rejected=list(changes), accepted=['reference', 'unavailable_queries', 'unchanged_queries', 'failed_release_result'])


def main():
    out = Path(sys.argv[1]).resolve()
    binary = out / 'native'
    binary_hash = prepare(out)
    results, failures = [], []
    with tempfile.TemporaryDirectory(prefix='pw-directory-', dir='/private/tmp') as directory:
        root = Path(directory)
        for case in SCENARIOS:
            target, other = root / case, root / (case + '-other')
            target.mkdir(mode=0o700); other.mkdir(mode=0o700)
            for i in range(4):
                p = target / f'existing-{i}'; p.write_bytes(CONTENTS); p.chmod(0o600)
            initial = [file_identity(target / f'existing-{i}') for i in range(4)]
            target_id, other_id = file_identity(target), file_identity(other)
            issue = other if case == 'directory_different' else target
            try:
                r = run_experiment(binary, out / case, case, target, issue, False)
                save(out / case / 'preparation.json', dict(target_identity=target_id, issue_identity=other_id if issue == other else target_id,
                     existing=initial, initial_contents_hex=CONTENTS.hex(), write_payload_hex=PAYLOAD.hex()))
                assert r['resolved_issue'] == str(issue.resolve())
                validate(r, target_id, other_id if issue == other else target_id, initial)
                external = []
                for d in r['directory']['boundaries']:
                    for path, op in zip((d['existing'], d['child']), d['operations']):
                        p = Path(path)
                        actual = dict(path=path, exists=p.exists())
                        if p.exists():
                            actual.update(identity=file_identity(p), content_hex=p.read_bytes().hex())
                            assert actual['content_hex'] == op['after_exit']['content_hex']
                            assert actual['identity'] == op['after_exit']['identity']
                        else:
                            assert op['after_exit']['open_rc'] == -1 and op['after_exit']['open_errno'] == 2
                        external.append(actual)
                save(out / case / 'external-after-exit.json', external)
                assert list(other.iterdir()) == [], 'other directory changed'
                if case == 'directory':
                    save(out / 'checker-controls.json', checker_controls(r, target_id, initial))
                results.append(r)
                print(case + ': passed', flush=True)
            except (AssertionError, ValueError) as error:
                failures.append(dict(case=case, error=str(error)))
                print(case + ': failed: ' + str(error), flush=True)
    save(out / 'summary.json', dict(passed=len(results), expected=len(SCENARIOS), failures=failures,
        observations=[dict(scenario=r['scenario'], issue_class=r['issue_class'], consume=r['consume'], release=r['release'],
            read_queries=[b['query']['native_rc'] for b in r['boundaries']],
            write_queries=[b['write_query']['native_rc'] for b in r['boundaries']],
            read_opens=[b['access']['open_rc'] for b in r['boundaries']],
            write_opens=[[op['write']['open']['native_rc'] for op in b['operations']] for b in r['directory']['boundaries']]) for r in results]))
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == binary_hash
    assert len(results) == len(SCENARIOS) and not failures, 'incomplete directory matrix; see summary.json'
    print('directory effects and persistence independently observed; tokens never retained')


if __name__ == '__main__':
    main()
