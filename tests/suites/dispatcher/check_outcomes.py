"""Independent dispatcher controls for declared observations and judgment authority."""
import copy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
from repository import install_runner
from release_accept import battery_problems
from execution_contract import defaults


def specification(authority):
    return dict(schema_version=1,
        observations=[dict(id='measurement', promise='Retain the constructed measurement and its value.')],
        judgments=[] if authority == 'informational' else [dict(id='expected_value', authority=authority,
            proposition='The measured value equals the independently specified value four.', observations=['measurement'])])


def pilot_script():
    return '''#!/bin/bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"
SOURCE_ROOT=''' + shlex.quote(str(ROOT)) + '''
if test_selected subject; then
  test_begin fixture subject
  "${PW_PYTHON}" -B -S -P "${SOURCE_ROOT}/tests/fixtures/dispatcher/pilot_unfavorable.py" "$SOURCE_ROOT" "${PW_TEST_ARTIFACTS}/pilot"
  evidence=()
  while IFS= read -r -d '' item; do evidence+=("$item"); done < <(
    "${PW_PYTHON}" -B -S -P -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); [sys.stdout.buffer.write(str(x).encode()+b"\\0") for x in sorted(p.rglob("*")) if x.is_file()]' "${PW_TEST_ARTIFACTS}/pilot"
  )
  test_observe measurement '{"matched_pairs":5,"valid":true}' "${evidence[@]}"
  result="$("${PW_PYTHON}" -B -S -P -c 'import json,sys; print(json.load(open(sys.argv[1]))["judgment"])' "${PW_TEST_ARTIFACTS}/pilot/conclusion.json")"
  test_judge expected_value "$result" 'five valid equal pairs do not establish improvement'
  test_complete 'constructed pilot comparison completed'
fi
for item in dependent neighbor; do
  if test_selected "$item"; then
    test_begin fixture "$item"
    printf '%s\\n' "$item" > "${PW_TEST_ARTIFACTS}/executed"
    test_pass 'legacy independent control'
  fi
done
'''


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    scenarios = [
        ('enforced_favorable', 'enforced', 4, None, True),
        ('enforced_unfavorable', 'enforced', 3, None, False),
        ('advisory_unfavorable', 'advisory', 3, None, True),
        ('informational', 'informational', 3, None, True),
        ('pilot_advisory', 'advisory', None, 'pilot', True),
        ('missing_observation', 'advisory', 3, 'omit', False),
        ('missing_evidence', 'advisory', 3, 'missing', False),
        ('mutated_evidence', 'advisory', 3, 'mutate', False),
        ('cleanup_failed', 'advisory', 3, 'cleanup', False),
        ('command_failed', 'advisory', 3, 'command', False),
        ('deleted_judgment', 'advisory', 3, 'delete', False),
        ('relabelled_judgment', 'enforced', 3, 'relabel', False),
        ('contradictory_terminal', 'advisory', 3, 'terminal', False),
        ('missing_account', 'informational', 3, 'account', False),
        ('null_account', 'informational', 3, 'null', False),
    ]
    completed = []
    for name, authority, measurement, fault, accepted in scenarios:
        work = out / name
        repo = work / 'repository'
        spec = specification(authority)
        if fault == 'pilot':
            spec['observations'][0]['promise'] = 'Retain ten constructed pilot trials, calibration, five matched pairs and the reader conclusion.'
            spec['judgments'][0]['proposition'] = 'The candidate improves held total beyond uncertainty and spread in every required pair.'
        cases = [dict(id='subject', outcome_contract=spec), dict(id='dependent', depends_on=['fixture/subject']), 'neighbor']
        install_runner(ROOT, repo, dict(fixture=dict(command=['bash', 'tests/suites/fixture/run.sh'], cases=cases)))
        script = repo / 'tests/suites/fixture/run.sh'
        script.parent.mkdir(parents=True)
        script.write_text('''#!/bin/bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"
if test_selected subject; then
  test_begin fixture subject
  printf '%s\\n' "''' + str(measurement) + '''" > "${PW_TEST_ARTIFACTS}/measurement.txt"
''' + ('' if fault == 'omit' else '''  test_observe measurement '{"value":''' + str(measurement) + '''}' "${PW_TEST_ARTIFACTS}/measurement.txt"
''') + ('' if authority == 'informational' else '''  if [[ "$(cat "${PW_TEST_ARTIFACTS}/measurement.txt")" -eq 4 ]]; then result=favorable; else result=unfavorable; fi
  test_judge expected_value "$result" "measured ''' + str(measurement) + '''; expected four"
''') + ('''  rm "${PW_TEST_ARTIFACTS}/measurement.txt"
''' if fault == 'missing' else '') + ('''  test_observation_failure cleanup 'constructed cleanup failure'
''' if fault == 'cleanup' else '') + '''  test_complete 'constructed observation completed' || terminal_rc=$?
''' + ('''  printf 'changed\\n' > "${PW_TEST_ARTIFACTS}/measurement.txt"
''' if fault == 'mutate' else '') + ('''  "${PW_PYTHON}" -B -S -P "${ROOT_DIR}/tamper.py" "${PW_TEST_DIR}"
''' if fault in ('delete', 'relabel', 'terminal', 'account', 'null') else '') + '''  exit ''' + ('7' if fault == 'command' else '${terminal_rc:-0}') + '''
fi
for item in dependent neighbor; do
  if test_selected "$item"; then
    test_begin fixture "$item"
    printf '%s\\n' "$item" > "${PW_TEST_ARTIFACTS}/executed"
    test_pass 'legacy independent control'
  fi
done
''')
        if fault == 'pilot':
            script.write_text(pilot_script())
        script.chmod(0o755)
        (repo / 'tamper.py').write_text('''import hashlib, json, pathlib, sys
p=pathlib.Path(sys.argv[1]); fault=''' + repr(fault) + '''
r=json.loads((p/'report.json').read_text())
if fault == 'terminal': r['status']='pass'
elif fault == 'account': r.pop('outcome_account')
elif fault == 'null': r['outcome_account']=None
else:
    a=json.loads((p/'outcomes.json').read_text())
    if fault == 'delete': a['judgments']=[]
    else: a['judgments'][0]['authority']='advisory'
    r['outcome_account']=a
    (p/'outcomes.json').write_text(json.dumps(a))
    (p/'outcomes.jsonl').write_text(''.join(json.dumps(dict(kind=k,record=v))+'\\n' for k in ('observations','judgments','failures') for v in a[k]))
(p/'report.json').write_text(json.dumps(r))
if fault == 'null':
    for path in (p/'events.jsonl', p.parents[2]/'events.jsonl'):
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        for row in rows:
            if row.get('step') == 'test_end': row['outcome_account_sha256']=hashlib.sha256(b'null').hexdigest()
        path.write_text(''.join(json.dumps(row)+'\\n' for row in rows))
''')
        env = {k:v for k,v in os.environ.items() if not k.startswith(('PW_', 'PYTEST'))}
        env.update(PW_TEST_RUN_ID='outcome_' + name, PW_TEST_QUIET='1')
        expected = defaults(repo)
        (work / 'expected-producer.json').write_text(json.dumps(expected, indent=2))
        result = subprocess.run(['bash', str(repo / 'tests/run.sh')], env=env, capture_output=True, timeout=40)
        (work / 'stdout').write_bytes(result.stdout)
        (work / 'stderr').write_bytes(result.stderr)
        (work / 'command.json').write_text(json.dumps(dict(argv=['bash', str(repo/'tests/run.sh')], returncode=result.returncode)))
        evidence = repo / 'tests/out/runs/default'
        run = json.loads((evidence / 'run.json').read_text())
        assert run['ok'] is accepted and result.returncode == (0 if accepted else 1), (name, run, result.stderr)
        parents = {c['id']:c for c in run['case_results']}
        assert parents['fixture/neighbor']['status'] == 'pass', (name, parents)
        assert parents['fixture/dependent']['status'] == ('pass' if accepted else None), (name, parents)
        assert (evidence / 'suites/fixture/neighbor/artifacts/executed').read_text().strip() == 'neighbor'
        dependency_effect = evidence / 'suites/fixture/dependent/artifacts/executed'
        assert dependency_effect.exists() is accepted, (name, dependency_effect)
        if accepted:
            assert dependency_effect.read_text().strip() == 'dependent'
        if accepted:
            assert parents['fixture/subject']['status'] == 'complete', (name, parents)
            assert run['counts'] == dict(**{'pass':2, 'fail':0, 'skip':0}, total=2), (name, run['counts'])
            assert run['completion'] == dict(selected=3, completed=3, skipped=0, unrun=0)
        if name == 'enforced_unfavorable':
            assert parents['fixture/subject']['status'] == 'fail'
            assert parents['fixture/subject']['assessment']['valid'] is True
            assert b'JUDGMENT FAIL' in result.stdout
        if name in ('advisory_unfavorable', 'pilot_advisory', 'cleanup_failed', 'command_failed', 'mutated_evidence'):
            assert b'ADVISORY:' in result.stdout and b'expected_value' in result.stdout
            assert str(evidence / 'suites/fixture/subject').encode() in result.stdout
        if name == 'informational':
            counts = run['outcomes']['parent']
            assert counts['informational'] == 1
            assert counts['enforced'] == counts['advisory'] == dict(favorable=0, unfavorable=0)
        # A constructed artifact-admission fact isolates the battery reader; this
        # does not claim codesign or native app execution in an offline fixture.
        candidate = copy.deepcopy(run)
        candidate['artifact_integrity'] = dict(valid_before=True, unchanged=True)
        (work / 'battery-input.json').write_text(json.dumps(candidate, indent=2))
        errors = battery_problems(candidate, Path(run['configuration']['app_dir']), expected=expected, evidence=evidence)
        (work / 'battery-errors.json').write_text(json.dumps(errors))
        assert bool(errors) is (not accepted), (name, errors)
        completed.append(dict(name=name, accepted=accepted, authority=authority, measurement=measurement, fault=fault))
    # The live pilot's driver evaluates its advisory conclusion with its own code. Run that code on the
    # reader output the pilot_advisory scenario retained and on authored verdicts, in a process of its own.
    summary = out / 'pilot_advisory/repository/tests/out/runs/default/suites/fixture/subject/artifacts/pilot/summary.json'
    conclusion = out / 'pilot_conclusion'
    argv = [sys.executable, '-B', '-S', '-P', str(ROOT / 'tests/fixtures/dispatcher/pilot_conclusion.py'),
            str(ROOT), str(summary), str(conclusion / 'receipt')]
    conclusion.mkdir()
    result = subprocess.run(argv, capture_output=True, timeout=60)
    (conclusion / 'stdout').write_bytes(result.stdout)
    (conclusion / 'stderr').write_bytes(result.stderr)
    (conclusion / 'command.json').write_text(json.dumps(dict(argv=argv, returncode=result.returncode)))
    assert result.returncode == 0, ('pilot conclusion controls failed', result.stderr.decode(errors='replace')[-2000:])
    (out / 'controls.json').write_text(json.dumps(completed, indent=2))
    print(f'{len(completed)} explicit observation controls passed; ' + result.stdout.decode().strip())


if __name__ == '__main__':
    main()
