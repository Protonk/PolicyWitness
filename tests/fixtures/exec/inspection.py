"""Assertions shared by CLI/worker tests and deliberately dirty direct controls."""
import errno
import json

ENV_KEY = 'PW_FIXTURE_CANARY'


def parse_report(raw, nonce, canary_fd):
    report = json.loads(raw)
    assert report['version'] == 1 and report['complete'] is True, 'incomplete inspection report'
    assert report['nonce'] == nonce, 'inspection belongs to a different invocation'
    assert type(report['pid']) is int and report['pid'] > 0, report
    assert report['env_key'] == ENV_KEY and report['canary_fd'] == canary_fd, report
    assert type(report['env_count']) is int and report['env_count'] >= 0, report
    assert report['env_value'] is None or isinstance(report['env_value'], str), report
    assert isinstance(report['fds'], list), report
    for item in report['fds']:
        assert len(item) == 2 and all(type(n) is int and n >= 0 for n in item), report
    numbers = [entry[0] for entry in report['fds']]
    assert len(numbers) == len(set(numbers)), 'duplicate descriptors in inspection'
    for key in ('stdin_rc', 'stdin_errno', 'canary_rc', 'canary_errno'):
        assert type(report[key]) is int, (key, report)
    assert type(report['stdin_skipped']) is bool, report
    assert isinstance(report['canary_hex'], str), report
    assert len(bytes.fromhex(report['canary_hex'])) == max(0, report['canary_rc']), report
    return report


def assert_empty_environment(report):
    assert report['env_count'] == 0 and report['env_value'] is None, (
        f"inherited environment: count={report['env_count']}, canary={report['env_value']!r}")


def assert_isolated_descriptors(report):
    numbers = sorted(entry[0] for entry in report['fds'])
    assert numbers == [0, 1, 2], f"inherited descriptors: {numbers}"
    assert report['canary_rc'] == -1 and report['canary_errno'] == errno.EBADF, (
        f"inherited canary still accessible: {report}")


def assert_stdin_eof(report):
    assert report['stdin_skipped'] is False, 'stdin inspection was skipped'
    assert report['stdin_rc'] == 0 and report['stdin_errno'] == 0, (
        f"stdin did not yield EOF: rc={report['stdin_rc']}, errno={report['stdin_errno']}")


def assert_clean(report):
    assert_empty_environment(report)
    assert_isolated_descriptors(report)
    assert_stdin_eof(report)
