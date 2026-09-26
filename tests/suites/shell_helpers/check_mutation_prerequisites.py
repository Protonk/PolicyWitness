"""Run the real mutation wrapper without a resolvable signing identity.

An unsigned fixture app has no team, so the real resolver returns no identity
without consulting the keychain. Independent builder receipts catch any work
after the missing prerequisite. No compiler, signing or live XPC is exercised.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def main():
    out = Path(sys.argv[1]).resolve()
    repo = out / 'fixture repo'
    wrapper = 'tests/suites/witness_contract/opt_in/mutations.sh'
    for relative in (wrapper, 'tests/lib/case.sh', 'tests/lib/testlib.sh'):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    for directory, builder in (('validator', 'build_bridge.sh'), ('exec', 'build.sh'),
                               ('worker_harness', 'build.sh'), ('worker_lifecycle', 'build.sh')):
        target = repo / 'tests/fixtures' / directory
        target.mkdir(parents=True)
        shutil.copyfile(ROOT / 'tests/fixtures/shell_case/build.sh', target / builder)
        shutil.copyfile(ROOT / 'tests/fixtures/shell_case/command.py', target / 'command.py')
    app = repo / 'Unsigned fixture.app'
    pw = app / 'Contents/MacOS/policy-witness'
    pw.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'tests/fixtures/shell_case/script_child.sh', pw)
    pw.chmod(0o755)
    journal = out / 'builder-receipts.jsonl'
    config = out / 'config.json'
    config.write_text(json.dumps(dict(journal=str(journal), marker='forbidden-build', build_exit=17)) + '\n')
    env = {k: v for k, v in os.environ.items() if not k.startswith('PW_') and k not in ('IDENTITY', 'BASH_ENV')}
    child_out = repo / 'tests/out'
    env.update(PW_APP_DIR=str(app), PW_TEST_OUT_DIR=str(child_out),
               PW_TEST_RUN_ID='missing_identity', CONTROL_CONFIG=str(config))
    result = subprocess.run(['bash', str(repo / wrapper)], env=env, cwd=out,
                            stdin=subprocess.DEVNULL, capture_output=True, timeout=15)
    (out / 'wrapper.stdout').write_bytes(result.stdout)
    (out / 'wrapper.stderr').write_bytes(result.stderr)
    (out / 'exit.json').write_text(json.dumps(dict(returncode=result.returncode)) + '\n')
    assert result.returncode == 1, (result.returncode, result.stdout, result.stderr)
    case = child_out / 'suites/witness_contract/order_barrier_mutations'
    report = json.loads((case / 'report.json').read_text())
    assert (report['suite'], report['test_id'], report['status']) == (
        'witness_contract', 'order_barrier_mutations', 'fail'), report
    assert 'Developer ID Application identity' in report['message'], report
    assert not journal.exists(), 'builder ran without the required signing identity'
    assert not list((case / 'artifacts').iterdir()), 'equipment or assertions ran after missing identity'
    events = [json.loads(line) for line in (case / 'events.jsonl').read_text().splitlines()]
    assert [(e['step'], e['status']) for e in events] == [
        ('test_start', 'start'), ('test_end', 'fail')], events
    print('missing identity fails the actual mutation wrapper before any build, run or skip')


if __name__ == '__main__':
    main()
