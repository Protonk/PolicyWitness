"""One-shot native observations; run only in a root-scheduled execution window.

Usage: python3 run_native.py /absolute/path/to/native_read /new/output/directory
The caller compiles native_read.c and holds the shared checkout execution lock.
This is investigation equipment, not an entry in the test battery.
"""
import copy
import errno
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def check_small(rows):
    by_key = {(r['mode'], r['capacity_argument']): r for r in rows}
    size = by_key['size', 0]['returned_length']
    assert by_key['size', 0]['rc'] == 0 and 1 < size < 4096, 'small sizing premise'
    for capacity in (size, 4096):
        row = by_key['read', capacity]
        assert not row['buffer_is_null'], 'read needs a value buffer'
        assert row['rc'] == 0, 'fitting read failed'
        assert row['returned_length'] == size, 'returned length is not supplied capacity'
        assert row['bytes_differing_from_sentinel'] > 0, 'no independently observed write'
    for capacity in (0, 1, size - 1):
        row = by_key['read', capacity]
        assert not row['buffer_is_null'], 'zero capacity must not become size-only'
        assert row['rc'] == -1 and row['errno_after_call'] == errno.ENOMEM, 'short-read control'
        # This assertion is bounded to the observed kern.osrelease userland call,
        # not a universal declaration about all sysctl handlers or failure causes.
        assert row['returned_length'] <= capacity, 'returned length is not discovered required size'
    assert all(r['canaries_ok'] for r in rows), 'canary changed'


def main():
    executable = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    observations = []
    commands = []

    def observe(name, mode, capacity):
        argv = [str(executable), name, mode, str(capacity)]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        commands.append({'argv': argv, 'exit_code': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        assert result.returncode == 0, 'native equipment failed'
        row = json.loads(result.stdout)
        observations.append(row)
        (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
        return row

    small = observe('kern.osrelease', 'size', 0)
    assert small['rc'] == 0 and 1 < small['returned_length'] < 4096
    for capacity in dict.fromkeys((0, 1, small['returned_length'] - 1, small['returned_length'], 4096)):
        observe('kern.osrelease', 'read', capacity)
    small_rows = list(observations)
    check_small(small_rows)
    mutants = []
    for name in ('capacity_as_returned_length', 'required_size_after_short_read', 'zero_capacity_as_size_only'):
        rows = copy.deepcopy(small_rows)
        if name == 'capacity_as_returned_length':
            next(r for r in rows if r['mode'] == 'read' and r['capacity_argument'] == 4096)['returned_length'] = 4096
        elif name == 'required_size_after_short_read':
            next(r for r in rows if r['mode'] == 'read' and r['capacity_argument'] == 1)['returned_length'] = small['returned_length']
        else:
            next(r for r in rows if r['mode'] == 'read' and r['capacity_argument'] == 0)['buffer_is_null'] = True
        try:
            check_small(rows)
        except AssertionError as error:
            mutants.append({'mutation': name, 'rejected_by': str(error)})
        else:
            raise AssertionError('checker accepted ' + name)
    (out / 'checker-controls.json').write_text(json.dumps(mutants, indent=2) + '\n')

    large_candidates = ['kern.proc.all', 'net.inet.tcp.pcblist64', 'net.inet.tcp.pcblist_n']
    large = None
    for name in large_candidates:
        row = observe(name, 'size', 0)
        if row['rc'] == 0 and 4096 < row['returned_length'] <= 1024 * 1024:
            large = row
            break
    if large:
        observe(large['name'], 'read', 4096)
        observe(large['name'], 'read', large['returned_length'])
        observe(large['name'], 'size', 0)
    # Missing names and errors preserve oldlen as an observation, not a size claim.
    observe('kern.pw_nonexistent_sysctl_control', 'read', 4096)
    summary = {'small_controls_passed': True, 'checker_mutations_rejected': len(mutants),
               'large_candidate': large, 'equipment_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
               'scope': 'native userland calls without specimen sandbox; no raw values retained'}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
