"""Declare the archive corpus and derive its expectations independently of PW.

The corpus is data: each entry is (message, multiplicity, note). Selection and
event expectations are derived here from the documented message contract, not
from PW's predicate or parser:

- A query for worker NAME and PID selects a message when the text "Sandbox:"
  is followed by one or more spaces/tabs and then the complete token
  "NAME(PID)", and that token is followed by whitespace or the end of the
  message.
- A selected message's deny record is: the worker token, "deny(N)", one
  operation token, and the untouched remainder as the target.

Usage:
  make_manifest.py corpus  > corpus.lines          (emission order, tabs literal)
  make_manifest.py manifest RECORD.json > query_predicate.json
where RECORD.json holds emitting_pid, window {start,end} and the query bounds
recorded during generation.
"""
import json
import re
import sys

MARKER = 'PWQP:'
HOSTS = '/private/etc/hosts'

# (message, multiplicity, note). Every message begins with the marker.
CORPUS = [
    # worker pw-probe-runner(42): positives
    (f'{MARKER} Sandbox: pw-probe-runner(42) deny(1) file-read-data {HOSTS}', 2, 'ordinary; emitted twice for multiplicity'),
    (f'{MARKER} Sandbox: pw-probe-runner(42) deny(1) file-write-data /private/tmp/pw fixture/target file.txt', 1, 'path with spaces'),
    (f'{MARKER} Sandbox:  pw-probe-runner(42) deny(1) file-read-data /private/tmp/two-spaces', 1, 'two spaces after Sandbox:'),
    (f'{MARKER} Sandbox:\tpw-probe-runner(42)\tdeny(1)\tmach-lookup\tcom.apple.cfprefsd.daemon', 1, 'tab-separated tokens'),
    (f'{MARKER} Sandbox: pw-probe-runner(42) deny(1) sysctl-read kern.osrelease', 1, 'sysctl form'),
    (f'{MARKER} Sandbox: pw-probe-runner(42) deny(1) file-read-data /private/tmp/a  b', 1, 'double space inside the target'),
    (f'{MARKER} Sandbox: pw-probe-runner(42) deny(1) process-exec /usr/bin/true', 1, 'exec form'),
    (f'{MARKER} Sandbox: pw-probe-runner(42) deny(1) system-fsctl (_IO "h" 47)', 1, 'parenthesised/quoted target as the kernel prints it'),
    (f'{MARKER} 3 duplicate reports for Sandbox: pw-probe-runner(42) deny(1) file-read-data {HOSTS}', 1, 'kernel duplicate-report prefix before Sandbox:'),
    (f'{MARKER} Sandbox: pw-probe-runner(42) deny(1) syscall-unix 545', 1, 'numeric target'),
    # worker pw-probe-runner(7): positives
    (f'{MARKER} Sandbox: pw-probe-runner(7) deny(1) file-read-data {HOSTS}', 1, 'second worker identity'),
    (f'{MARKER} Sandbox: pw-probe-runner(7) deny(2) file-write-create /private/tmp/pw fixture/created', 1, 'deny count other than 1'),
    (f'{MARKER} Sandbox: pw-probe-runner(7) deny(1) mach-lookup com.apple.system.logger', 1, 'mach form'),
    # negatives for both queries
    (f'{MARKER} Sandbox: other-worker(42) deny(1) file-read-data {HOSTS}', 1, 'another worker name, same pid as 42'),
    (f'{MARKER} Sandbox: pw-probe-runner(420) deny(1) file-read-data {HOSTS}', 1, 'longer pid containing 42'),
    (f'{MARKER} Sandbox: pw-probe-runner(142) deny(1) file-read-data {HOSTS}', 1, 'longer pid containing 42'),
    (f'{MARKER} Sandbox: pw-probe-runner(43) deny(1) file-read-data {HOSTS}', 1, 'neighbouring pid of 42'),
    (f'{MARKER} Sandbox: pw-probe-runner(70) deny(1) file-read-data {HOSTS}', 1, 'longer pid containing 7'),
    (f'{MARKER} Sandbox: pw-probe-runner(8) deny(1) file-read-data {HOSTS}', 1, 'neighbouring pid of 7'),
    (f'{MARKER} Sandbox: other-worker(9) deny(1) file-read-data /private/tmp/42/pw-probe-runner(42)', 1, 'requested token only inside a path'),
    (f'{MARKER} Sandbox: other-worker(9) deny(1) mach-lookup com.example.42.7', 1, 'requested digits only in unrelated deny text'),
    (f'{MARKER} pw-probe-runner(42) deny(1) file-read-data /private/tmp/no-sandbox-prefix', 1, 'worker token without Sandbox: prefix'),
    (f'{MARKER} Sandbox: xpw-probe-runner(42) deny(1) file-read-data /private/tmp/prefixed-name', 1, 'worker name with a prefix'),
    (f'{MARKER} Sandbox: pw-probe-runner-2(42) deny(1) file-read-data /private/tmp/suffixed-name', 1, 'worker name with a suffix'),
    (f'{MARKER} Sandbox: pw-probe-runner(42)x deny(1) file-read-data /private/tmp/token-suffix', 1, 'worker token with a trailing character'),
]

QUERIES = [
    {'name': 'worker_42', 'process_name': 'pw-probe-runner', 'pid': 42},
    {'name': 'worker_7', 'process_name': 'pw-probe-runner', 'pid': 7},
]


def selects(message, name, pid):
    """The documented selection rule, written without reference to PW's regex."""
    token = f'{name}({pid})'
    at = message.find('Sandbox:')
    while at != -1:
        rest = message[at + len('Sandbox:'):]
        stripped = rest.lstrip(' \t')
        if len(stripped) < len(rest) and stripped.startswith(token):
            tail = stripped[len(token):]
            if tail == '' or tail[0] in ' \t':
                return True
        at = message.find('Sandbox:', at + 1)
    return False


def deny_record(message):
    """The documented record shape: worker token, deny(N), operation, remainder."""
    at = message.find('Sandbox:')
    body = message[at + len('Sandbox:'):].lstrip(' \t')
    m = re.match(r'([^ \t]+)[ \t]+(deny\(\d+\))[ \t]+([^ \t]+)[ \t]+(.*)$', body)
    if not m:
        return None
    worker, _deny, operation, target = m.groups()
    pm = re.match(r'(.*)\((\d+)\)$', worker)
    return {'pid': int(pm.group(2)), 'process': pm.group(1), 'operation': operation, 'path': target}


def expanded():
    out = []
    for message, count, _note in CORPUS:
        assert message.startswith(MARKER + ' ') and '\n' not in message
        out.extend([message] * count)
    return out


def main():
    mode = sys.argv[1]
    if mode == 'corpus':
        sys.stdout.write('\n'.join(expanded()) + '\n')
        return
    record = json.load(open(sys.argv[2]))
    queries = []
    for q in QUERIES:
        selected = [m for m in expanded() if selects(m, q['process_name'], q['pid'])]
        assert selected, q
        events = [deny_record(m) for m in selected]
        assert all(events), (q, selected)
        bounds = record['queries'].get(q['name'], record['window'])
        queries.append({'name': q['name'], 'pid': q['pid'], 'process_name': q['process_name'],
                        'start': bounds['start'], 'end': bounds['end'],
                        'selected_messages': selected, 'deny_events': events})
    for q in queries:
        assert record['emitting_pid'] != q['pid']
    manifest = {'schema_version': 1, 'message_marker': MARKER, 'emitting_pid': record['emitting_pid'],
                'window': record['window'], 'messages': expanded(), 'queries': queries,
                'notes': [f'{count}x {note}' for _m, count, note in CORPUS]}
    json.dump(manifest, sys.stdout, indent=2)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
