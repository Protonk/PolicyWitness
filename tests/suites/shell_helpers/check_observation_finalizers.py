"""Observe explicit shell finalizers without using the dispatcher as an oracle."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def check(out):
    completed = []
    for name, authority, result, action, expected_status, expected_return in (
        ('information', None, None, 'test_complete', 'complete', 0),
        ('advisory', 'advisory', 'unfavorable', 'test_complete', 'complete', 0),
        ('enforced', 'enforced', 'unfavorable', 'test_complete', 'fail', 1),
        ('late_failure', 'advisory', 'unfavorable', 'test_fail', 'fail', 1),
        ('wrong_finalizer', None, None, 'test_pass', 'fail', 1),
    ):
        work = out / name
        work.mkdir(parents=True)
        output = work / 'output'
        spec = dict(schema_version=1, observations=[dict(id='value', promise='Capture a constructed value.')],
                    judgments=[] if authority is None else [dict(id='expectation', authority=authority,
                        proposition='The constructed value is four.', observations=['value'])])
        script = work / 'run.sh'
        script.write_text('''#!/bin/bash
set -u
source "$1/tests/lib/testlib.sh"
test_begin fixture observation
printf 'three\\n' > "$PW_TEST_ARTIFACTS/raw"
test_observe value '{"value":3}' "$PW_TEST_ARTIFACTS/raw"
if [[ -n "$2" ]]; then test_judge expectation "$2" "$4"; fi
"$3" "$4"
status=$?
printf '%s\\n' "$status" > "$PW_TEST_ARTIFACTS/returned"
exit "$status"
''')
        message = 'literal "quote" \'apostrophe\' \\ λ $(touch CANARY)\nsecond line'
        env = {k:v for k,v in os.environ.items() if not k.startswith('PW_TEST_')}
        env.update(PW_TEST_OUT_DIR=str(output), PW_TEST_EVENTS=str(output/'events.jsonl'),
                   PW_TEST_CASES='observation', PW_TEST_RUN_ID='finalizer_' + name,
                   PW_TEST_QUIET='0' if name == 'wrong_finalizer' else '1',
                   PW_TEST_OUTCOME_CONTRACTS=json.dumps({'fixture/observation':spec}))
        argv = ['bash', str(script), str(ROOT), result or '', action, message]
        command = subprocess.run(argv, cwd=work, env=env, capture_output=True, timeout=15)
        (work/'stdout').write_bytes(command.stdout)
        (work/'stderr').write_bytes(command.stderr)
        (work/'input.json').write_text(json.dumps(dict(argv=argv, specification=spec, returncode=command.returncode)))
        assert command.returncode == expected_return, (name, command.stderr)
        assert not (work/'CANARY').exists()
        case = output/'suites/fixture/observation'
        report = json.loads((case/'report.json').read_text())
        assert report['schema_version'] == 2 and report['status'] == expected_status
        assert report['message'] == message
        account = report['outcome_account']
        assert account == json.loads((case/'outcomes.json').read_text())
        assert account['observations'] == [dict(id='value', facts={'value':3},
            evidence=[dict(path='artifacts/raw', sha256=hashlib.sha256(b'three\n').hexdigest())])]
        if authority:
            assert account['judgments'] == [dict(**spec['judgments'][0], result=result, detail=message)]
        else:
            assert account['judgments'] == []
        terminal = json.loads((case/'events.jsonl').read_text().splitlines()[-1])
        expected_hash = hashlib.sha256(json.dumps(account,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert terminal['status'] == expected_status and terminal['outcome_account_sha256'] == expected_hash
        assert (case/'events.jsonl').read_bytes() == (output/'events.jsonl').read_bytes()
        if name == 'late_failure':
            assert account['failures'][0]['kind'] == 'execution'
            assert not (case/'artifacts/returned').exists(), 'test_fail returned'
        else:
            assert (case/'artifacts/returned').read_text() == str(expected_return) + '\n'
        if name == 'wrong_finalizer':
            assert account['failures'][0]['kind'] == 'validity'
            assert b'] fail:' in command.stdout and b'] pass:' not in command.stdout
        if name in ('information', 'advisory'):
            assert report['assessment']['accepted'] is True
        else:
            assert report['assessment']['accepted'] is False
        completed.append(name)
    (out/'controls.json').write_text(json.dumps(completed,indent=2))
    print(f'{len(completed)} observation finalizer controls passed')


if __name__ == '__main__':
    check(Path(sys.argv[1]).resolve())
