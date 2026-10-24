"""Observe what reaches a case and its children under the dispatcher and as a direct suite: the five witnessed
names, the interpreter's identity, and the import boundary. Imports no harness code; the fixture leaf imports none."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from repository import install_runner

NAMES = ('SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE')
KEG = '/opt/homebrew/Cellar/python@3.14/'
LEAF = '''"""Record what this checker and a child see; nothing here reads harness code."""
import json, os, subprocess, sys
NAMES = %r
child = subprocess.run(['/usr/bin/env', '-0'], capture_output=True).stdout.decode()
seen = dict(entry.split('=', 1) for entry in child.split('\\0') if entry)
# A Python child started the way checkers start theirs reports its own identity and import path.
grandchild = subprocess.run([sys.executable, '-B', '-S', '-P', '-c',
                             'import json, os, sys; print(json.dumps(dict(executable=os.path.realpath(sys.executable), '
                             'site_loaded="site" in sys.modules, sys_path=[os.path.realpath(p) if p else p for p in sys.path], '
                             'prefix=os.path.realpath(sys.prefix))))'], capture_output=True, text=True)
record = dict(executable=os.path.realpath(sys.executable), version=list(sys.version_info[:2]),
              own={n: os.environ.get(n) for n in NAMES}, child={n: seen.get(n) for n in NAMES},
              site_loaded='site' in sys.modules, sys_path=[os.path.realpath(p) if p else p for p in sys.path],
              prefix=os.path.realpath(sys.prefix), cwd=os.getcwd(),
              python_child=json.loads(grandchild.stdout) if grandchild.returncode == 0 else dict(error=grandchild.stderr[-400:]))
with open(os.environ['PW_PROBE_RECEIPT'], 'w') as stream:
    json.dump(record, stream)
''' % (NAMES,)
SUITE = '''#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin probe boundary
test_check_python "${PW_TEST_ARTIFACTS}/probe.log" "probe failed" "${ROOT_DIR}/tests/fixtures/probe/leaf.py"
test_pass "probe recorded"
'''


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def minimal_env(work):
    """A C locale with none of the witnessed names, no PYTHON* variable and a working directory outside the checkout."""
    return dict(PATH='/usr/bin:/bin', HOME=os.environ['HOME'], TMPDIR=str(work / 'tmp'),
                __CF_USER_TEXT_ENCODING=os.environ.get('__CF_USER_TEXT_ENCODING', f'0x{os.getuid():X}:0x0:0x0'))


def check_record(name, record, repo, *, outside_checkout, declared):
    require(record['own'] == {n: None for n in NAMES}, f'{name}: the leaf inherited {record["own"]}')
    require(record['child'] == {n: None for n in NAMES}, f'{name}: the child inherited {record["child"]}')
    require(record['version'] == [3, 14], f'{name}: interpreter {record["version"]} is not 3.14')
    require(record['executable'].startswith(KEG), f'{name}: {record["executable"]} is not in the keg')
    require(record['site_loaded'] is False, f'{name}: site was imported; the resolver starts helpers with -S')
    outside = [p for p in record['sys_path'] if not (p.startswith(record['prefix'] + '/') or p.startswith(str(repo) + '/'))]
    require(not outside, f'{name}: sys.path reaches outside the interpreter and the tree: {outside}; '
                         'the resolver starts helpers with -S (and -P for inline starts) and refuses PYTHON* so nothing else is an input')
    child = record['python_child']
    require('error' not in child, f'{name}: the Python child did not report: {child}')
    require(child['executable'] == record['executable'], f'{name}: the Python child ran {child["executable"]}, not {record["executable"]}')
    require(child['site_loaded'] is False, f'{name}: the Python child imported site; children start with -S too')
    child_outside = [p for p in child['sys_path'] if not (p.startswith(child['prefix'] + '/') or p.startswith(str(repo) + '/'))]
    require(not child_outside, f'{name}: the Python child reaches outside the interpreter and the tree: {child_outside}')
    if outside_checkout:
        require(not record['cwd'].startswith(str(repo)), f'{name}: the probe ran inside the checkout, which would hide a missing -P')
    require(declared.get('realpath') == record['executable'],
            f'{name}: the report declares {declared.get("realpath")} but the case ran {record["executable"]}')


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    inventory = []
    for entry in ('dispatcher', 'direct_suite'):
        for mode in ('clean', 'pythonpath'):
            name = f'{entry}_{mode}'
            work = out / name
            repo = work / 'fixture repo'
            install_runner(ROOT, repo, {'probe': {'command': ['bash', 'tests/suites/probe/run.sh'], 'cases': ['boundary']}})
            (repo / 'tests/fixtures/probe').mkdir(parents=True)
            (repo / 'tests/fixtures/probe/leaf.py').write_text(LEAF)
            suite = repo / 'tests/suites/probe/run.sh'
            suite.parent.mkdir(parents=True)
            suite.write_text(SUITE)
            suite.chmod(0o755)
            (work / 'tmp').mkdir(parents=True)
            child_out = repo / 'tests/out/runs/default'
            receipt = work / 'receipt.json'
            env = dict(minimal_env(work), PW_TEST_OUT_DIR=str(child_out), PW_TEST_RUN_ID=name, PW_PROBE_RECEIPT=str(receipt))
            if entry == 'direct_suite':
                # A case script started on its own carries the dispatcher's context.
                env.update(PW_TEST_CASES='boundary', PW_TEST_EVENTS=str(child_out / 'events.jsonl'))
            if mode == 'pythonpath':
                env['PYTHONPATH'] = str(work / 'elsewhere')
            argv = (['bash', str(repo / 'tests/run.sh'), '--suite', 'probe'] if entry == 'dispatcher'
                    else ['bash', str(suite)])
            result = subprocess.run(argv, env=env, cwd=work, capture_output=True, text=True, timeout=120)
            (work / 'stdout').write_text(result.stdout)
            (work / 'stderr').write_text(result.stderr)
            if mode == 'pythonpath':
                require(result.returncode == 2, f'{name}: expected the resolver to refuse with status 2, got {result.returncode}: {result.stderr}')
                require('python_environment_set' in result.stderr and 'PYTHONPATH' in result.stderr,
                        f'{name}: the refusal does not name python_environment_set and PYTHONPATH: {result.stderr}')
                require(not receipt.exists(), f'{name}: the leaf ran after a refusal')
                require(not (child_out / 'owner.json').exists(), f'{name}: a refused start initialized output')
            else:
                require(result.returncode == 0, f'{name}: status {result.returncode}: {result.stderr}')
                require(receipt.exists(), f'{name}: the leaf wrote no receipt')
                # The dispatcher runs every case from the checkout root; a direct suite runs from the work directory,
                # outside the checkout, so an inline start without -P would show there.
                report = json.loads((child_out / 'suites/probe/boundary/report.json').read_text())
                declared = report.get('interpreter') or {}
                check_record(name, json.loads(receipt.read_text()), repo, outside_checkout=entry == 'direct_suite', declared=declared)
                require(declared.get('realpath', '').startswith(KEG) and declared.get('version', '').startswith('3.14.'),
                        f'{name}: the report declares {declared}')
                if entry == 'dispatcher':
                    summary = json.loads((child_out / 'run.json').read_text())
                    require(summary['ok'] is True and summary['counts']['total'] == 1, f'{name}: wrong dispatcher summary')
                    require(summary['configuration']['python']['realpath'] == declared['realpath'],
                            f'{name}: run.json resolved {summary["configuration"]["python"]} but the report declares {declared}')
            inventory.append(name)
            print(f'{name}: ok', flush=True)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} interpreter boundary controls passed')


if __name__ == '__main__':
    main()
