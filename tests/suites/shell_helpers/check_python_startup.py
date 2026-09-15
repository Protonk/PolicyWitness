"""Observe startup refusal without relying on Python assert statements."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def snapshot(directory):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in directory.rglob('*') if path.is_file()}


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    inventory = []
    modes = [('unset', None, False), ('zero', '0', False), ('empty', '', False),
             ('one', '1', True), ('two', '2', True), ('text', 'yes', True)]
    for entry in ('dispatcher', 'direct_suite'):
        for label, optimization, blocked in modes:
            for assertion in ('pass', 'fail'):
                name = f'{entry}_{label}_{assertion}'
                work = out / name
                repo = work / 'fixture repo'
                for relative in ('tests/run.sh', 'tests/lib/testlib.sh', 'tests/lib/case.sh',
                                 'tests/lib/suite_run.py', 'tests/fixtures/shell_case/python_assertion.py'):
                    target = repo / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / relative, target)
                suite = repo / 'tests/suites/probe/run.sh'
                suite.parent.mkdir(parents=True)
                shutil.copyfile(ROOT / 'tests/fixtures/shell_case/python_startup.sh', suite)
                suite.chmod(0o755)
                child_out = repo / 'tests/out'
                child_out.mkdir()
                (child_out / 'prior.bin').write_bytes(b'prior evidence\x00\xff')
                (child_out / 'run.json').write_text('{"prior_run": true}\n')
                before = snapshot(child_out)
                started, continued, receipt = (work / leaf for leaf in ('started', 'continued', 'checker.json'))
                env = {key: value for key, value in os.environ.items()
                       if not key.startswith('PW_') and key != 'PYTHONOPTIMIZE'}
                env.update(PW_TEST_OUT_DIR=str(child_out), PW_TEST_RUN_ID=name,
                           PW_CONTROL_STARTED=str(started), PW_CONTROL_CONTINUED=str(continued),
                           PW_CONTROL_CHECKER_RECEIPT=str(receipt), PW_CONTROL_ASSERTION=assertion,
                           PYTHONDONTWRITEBYTECODE='1')
                if optimization is not None:
                    env['PYTHONOPTIMIZE'] = optimization
                argv = (['bash', str(repo / 'tests/run.sh'), '--suite', 'probe']
                        if entry == 'dispatcher' else ['bash', str(suite)])
                result = subprocess.run(argv, env=env, cwd=work, capture_output=True, timeout=15)
                (work / 'stdout').write_bytes(result.stdout)
                (work / 'stderr').write_bytes(result.stderr)
                (work / 'exit.json').write_text(json.dumps({'argv': argv, 'returncode': result.returncode}) + '\n')
                if blocked:
                    require(result.returncode == 2, f'{name}: startup must exit 2, got {result.returncode}')
                    require(b'Python assertions are disabled' in result.stderr and b'PYTHONOPTIMIZE' in result.stderr,
                            f'{name}: missing actionable startup diagnostic: {result.stderr!r}')
                    require(not started.exists() and not continued.exists() and not receipt.exists(),
                            f'{name}: rejected startup ran fixture work')
                    require(snapshot(child_out) == before, f'{name}: rejected startup changed prior evidence')
                else:
                    passed = assertion == 'pass'
                    require(result.returncode == (0 if passed else 1),
                            f'{name}: incorrect checker status {result.returncode}: {result.stderr!r}')
                    require(started.exists() and receipt.exists(), f'{name}: checker did not execute')
                    require(json.loads(receipt.read_text()) == {'assertions_enabled': True, 'mode': assertion},
                            f'{name}: checker ran without assertions')
                    require(continued.exists() == passed, f'{name}: wrong continuation after checker')
                    report = json.loads((child_out / 'suites/probe/assertions/report.json').read_text())
                    require(report['status'] == ('pass' if passed else 'fail'), f'{name}: wrong report status')
                    if not passed:
                        require(b'deliberate assertion failure' in result.stderr, f'{name}: assertion failure lost')
                    if entry == 'dispatcher':
                        summary = json.loads((child_out / 'run.json').read_text())
                        require(summary['ok'] is passed and summary['counts']['total'] == 1,
                                f'{name}: wrong dispatcher summary')
                inventory.append(name)
                print(f'{name}: ok', flush=True)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} Python startup controls passed')


if __name__ == '__main__':
    main()
