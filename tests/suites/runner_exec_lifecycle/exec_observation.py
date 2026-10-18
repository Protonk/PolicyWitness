"""Live-suite assertions for separately observed exec boundaries.

Callers establish process identity, pipe closure, liveness/exit and file effects
before reading the result. This module checks the corresponding transport facts;
it does not treat a signal request or output metadata as an effect oracle.
"""
import copy
import os
import signal


def assert_observation(attempt, pid, *, stop, leader_observed, stdout_eof,
                       stderr_eof, cleanup_requested, exit_code=None, term_signal=None):
    evidence = attempt.get('exec_observation')
    assert isinstance(evidence, dict), attempt
    assert set(evidence) == {'collection', 'cleanup', 'reap'}, evidence
    collection = evidence['collection']
    assert collection['stop_reason'] == stop, evidence
    assert collection['leader_exit_observed'] is leader_observed, evidence
    assert collection['stdout']['eof'] is stdout_eof, evidence
    assert collection['stderr']['eof'] is stderr_eof, evidence
    for field in ('waitid_errno', 'poll_errno', 'clock_fault'):
        assert collection.get(field) is None, evidence
    for stream in ('stdout', 'stderr'):
        assert collection[stream].get('read_errno') is None, evidence
        assert collection[stream].get('poll_revents') is None, evidence
    assert collection.get('deadline_kind') == ('child' if stop == 'deadline' else None), evidence
    cleanup = evidence['cleanup']
    assert cleanup['state'] == ('requested' if cleanup_requested else 'not_requested'), evidence
    if cleanup_requested:
        request = cleanup['group_request']
        assert request['target'] == -pid and request['signal'] == signal.SIGKILL, evidence
        assert request['rc'] == 0 and request.get('errno') is None, evidence
    else:
        assert cleanup.get('group_request') is None, evidence
    assert cleanup.get('leader_fallback') is None, evidence
    reap = evidence['reap']
    assert reap['stop_reason'] == 'reaped' and reap.get('clock_fault') is None, evidence
    wait = reap['last_wait']
    assert wait['rc'] == pid and wait.get('errno') is None, evidence
    status = wait['status']
    if exit_code is not None:
        assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == exit_code, evidence
    if term_signal is not None:
        assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == term_signal, evidence
    return evidence


def checker_controls(attempt, pid, **expected):
    """Mutate a live accepted result; require the unchanged assertions to reject it."""
    assert_observation(attempt, pid, **expected)
    edits = {
        'missing_metadata': lambda value: value.pop('exec_observation'),
        'cleanup_as_completion': lambda value: value['exec_observation']['collection'].update(stop_reason='leader_exit_and_eof'),
        'invented_eof': lambda value: value['exec_observation']['collection']['stdout'].update(eof=True),
        'omitted_request': lambda value: value['exec_observation']['cleanup'].update(state='not_requested'),
        'request_as_reap': lambda value: value['exec_observation']['reap']['last_wait'].update(rc=0),
        'native_errno_on_success': lambda value: value['exec_observation']['cleanup']['group_request'].update(errno=1),
    }
    rejected = []
    for name, edit in edits.items():
        changed = copy.deepcopy(attempt)
        edit(changed)
        try:
            assert_observation(changed, pid, **expected)
        except (AssertionError, KeyError):
            rejected.append(name)
        else:
            raise AssertionError('live exec checker accepted ' + name)
    return dict(positive='live deadline evidence accepted', rejected=rejected)
