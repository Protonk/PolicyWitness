"""Constructed fresh-write records; expectations do not read production code."""
from copy import deepcopy

from extension_evidence import validate_fresh_write


def metadata(size):
    return dict(rc=0, identity=dict(device=3, inode=42, mode=33152, uid=501, gid=20), size=size)


def successful(create=False):
    observation = dict(open_rc=17, opened_stat=metadata(0 if create else 9),
                       write_rc=1, written_stat=metadata(1), close_rc=0)
    if create:
        observation['preopen_stat'] = dict(rc=-1, errno=2)
    else:
        observation.update(truncate_rc=0, truncated_stat=metadata(0))
    return dict(requested_kind='file', requested_action='create_fresh' if create else 'write_fresh',
                result_source='worker', rc=0, outcome='ok', fresh_write=observation)


def failed(attempt, error):
    attempt.update(rc=-1, outcome='write_failed')
    if error is None:
        attempt.pop('errno', None)
    else:
        attempt['errno'] = error
    return attempt


def records():
    good = [('existing', successful()), ('create', successful(True))]
    value = successful(True)
    value['fresh_write']['preopen_stat'] = dict(rc=-1, errno=13)
    good.append(('preopen_diagnostic', value))
    for create in (False, True):
        value = successful(create)
        value['fresh_write'] = dict(open_rc=-1, open_errno=13)
        if create:
            value['fresh_write']['preopen_stat'] = dict(rc=-1, errno=2)
        good.append(('open_failure_' + str(create), failed(value, 13)))
    value = successful()
    value['fresh_write']['opened_stat'] = dict(rc=-1, errno=5)
    good.append(('opened_stat_failure_keeps_later_calls', failed(value, 5)))
    value = successful()
    value['fresh_write'].update(truncate_rc=-1, truncate_errno=1, truncated_stat=metadata(9))
    value['fresh_write'].pop('write_rc'); value['fresh_write'].pop('written_stat')
    good.append(('truncate_failure', failed(value, 1)))
    value = successful()
    value['fresh_write']['truncated_stat'] = dict(rc=-1, errno=5)
    good.append(('truncated_stat_failure_keeps_write', failed(value, 5)))
    value = successful()
    value['fresh_write'].update(write_rc=-1, write_errno=28, written_stat=metadata(0))
    good.append(('write_failure', failed(value, 28)))
    value = successful()
    value['fresh_write'].update(write_rc=0, written_stat=metadata(0))
    good.append(('short_write_without_errno', failed(value, None)))
    value = successful()
    value['fresh_write']['written_stat'] = dict(rc=-1, errno=5)
    good.append(('written_stat_failure', failed(value, 5)))
    value = successful()
    value['fresh_write'].update(close_rc=-1, close_errno=9)
    good.append(('close_failure', failed(value, 9)))
    value = successful()
    value['fresh_write'].update(opened_stat=dict(rc=-1, errno=5), write_rc=-1, write_errno=28,
                                written_stat=dict(rc=-1, errno=9), close_rc=-1, close_errno=1)
    good.append(('combined_failures_keep_first', failed(value, 5)))
    value = successful()
    value['fresh_write']['written_stat']['size'] = 800
    value['fresh_write']['written_stat']['identity']['mode'] = 33188
    good.append(('metadata_observations_do_not_prove_stability', value))

    bad = []
    for key in ('open_rc', 'opened_stat', 'truncate_rc', 'truncated_stat', 'write_rc', 'written_stat', 'close_rc'):
        value = successful(); value['fresh_write'].pop(key)
        bad.append(('missing_' + key, value, 'fresh write'))
    value = successful(); value.pop('fresh_write')
    bad.append(('missing_observations', value, 'lacks syscall observations'))
    value = successful(); value.update(result_source='not_reached')
    bad.append(('unpublished_result', value, 'requires a completed'))
    value = successful(); value['requested_action'] = 'open_write'
    bad.append(('legacy_action_cannot_carry_new_evidence', value, 'requires a completed'))
    value = successful(True); value['fresh_write'].pop('preopen_stat')
    bad.append(('missing_preopen', value, 'preopen_stat'))
    value = successful(); value['fresh_write']['preopen_stat'] = dict(rc=-1, errno=2)
    bad.append(('unexpected_preopen', value, 'cannot supply preopen'))
    value = successful(True); value['fresh_write'].update(truncate_rc=0, truncated_stat=metadata(0))
    bad.append(('create_truncation', value, 'cannot supply truncation'))
    value = deepcopy(dict(good)['open_failure_False']); value['fresh_write']['write_rc'] = 1
    bad.append(('call_after_failed_open', value, 'cannot supply later'))
    value = deepcopy(dict(good)['truncate_failure']); value['fresh_write'].update(write_rc=1, written_stat=metadata(1))
    bad.append(('call_after_failed_truncate', value, 'cannot supply write'))
    value = successful(); value['fresh_write']['open_errno'] = 13
    bad.append(('success_errno', value, 'errno lacks failure'))
    value = deepcopy(dict(good)['short_write_without_errno']); value['fresh_write']['write_errno'] = 28
    bad.append(('short_write_invents_errno', value, 'errno lacks failure'))
    value = deepcopy(dict(good)['combined_failures_keep_first']); value['errno'] = 1
    bad.append(('lost_first_failure', value, 'disagree with attempt'))
    value = successful(); value['fresh_write']['opened_stat'].update(rc=-1, errno=5)
    bad.append(('failed_metadata_has_identity', value, 'carries identity/size'))
    value = successful(); value['fresh_write']['opened_stat'].pop('identity')
    bad.append(('successful_metadata_missing_identity', value, 'lacks identity/size'))
    value = successful(); value['fresh_write']['opened_stat']['size'] = True
    bad.append(('boolean_size', value, 'lacks identity/size'))
    for name, count in [('boolean', True), ('float', 1.0), ('oversized', 2), ('below_failure', -2)]:
        value = successful(); value['fresh_write']['write_rc'] = count
        bad.append(('invalid_write_' + name, value, 'invalid fresh write write result'))
    value = successful(); value['fresh_write'].pop('opened_stat'); value['fresh_write'].pop('close_rc')
    bad.append(('combined_missing_observations', value, 'fresh write'))
    return good, bad


def run_fresh_write_controls(run=None, baseline=None):
    good, bad = records()
    for name, attempt, diagnostic in [(n, a, None) for n, a in good] + bad:
        before = deepcopy(attempt)
        errors = validate_fresh_write(attempt)
        assert attempt == before, name
        assert bool(errors) == (diagnostic is not None), (name, errors)
        if diagnostic:
            assert any(diagnostic in error for error in errors), (name, errors)
        if name == 'combined_missing_observations':
            assert any('opened_stat' in error for error in errors) and any('close' in error for error in errors)
        if run is not None:
            document = deepcopy(baseline)
            step = document['data']['runner_result']['steps'][1]
            previous = step['attempt']
            previous.pop('fresh_read', None); previous.pop('errno', None)
            previous.update(deepcopy(attempt))
            comparison = step['comparison']
            comparison['operation_relation'] = 'unresolved' if attempt['requested_action'] == 'create_fresh' else 'different'
            permission = attempt.get('errno') in (1, 13)
            comparison['observation'] = 'succeeded' if attempt['rc'] == 0 else 'permission_failure' if permission else 'other_failure'
            comparison['observation_basis'] = 'permission_errno' if attempt['rc'] != 0 and permission else 'completed_worker_status'
            run('fresh_write_' + name, document, rejected_by=diagnostic)
    return dict(accepted=[name for name, _ in good], rejected=[name for name, _, _ in bad])
