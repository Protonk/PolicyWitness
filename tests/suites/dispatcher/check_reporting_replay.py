"""Independent raw replay inputs; derived summaries are deliberately untrustworthy."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


def read(path):
    return json.loads(path.read_bytes())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def raw_fixture(out):
    """Construct a three-parent producer-v1 input, not a run of any product."""
    out.mkdir()
    cases = [dict(id='fixture/' + name, suite='fixture', test_id=name,
                  report_suite='fixture', context='standard', skip_reasons=[],
                  requires=['app'] if name == 'obligation' else [], depends_on=[],
                  command=['/constructed/command', name]) for name in ('obligation', 'neighbor')]
    family_id = 'fixture/family'
    manifest = dict(schema_version=1, family=family_id,
                    items=[dict(id=family_id + '::one', nodeid='one')])
    cases.append(dict(id=family_id, suite='fixture', test_id='family', report_suite='fixture',
                      context='standard', skip_reasons=[], requires=[], depends_on=[],
                      engine='pytest', items=manifest))
    contract = dict(profile='pw-family-evidence-1', source=dict(fixture='independently constructed replay input'),
                    selected=[dict(id=c['id'], engine=c.get('engine', 'legacy')) for c in cases],
                    required_families=[family_id])
    contract['identity'] = digest(contract)
    plan = dict(cases=cases, selection=dict(mode='default', suites=[], cases=[]),
                configuration=dict(app_dir='/constructed/app', python=dict(realpath=sys.executable)),
                execution_contract=contract)
    write(out / 'plan.json', plan)
    write(out / 'owner.json', dict(run_id='constructed-replay', started_at_unix_ms=1))
    write(out / 'artifact-integrity/before.json', {})
    write(out / 'artifact-integrity/after.json', {})
    write(out / 'artifact-integrity/inspection.json',
          dict(ok=True, errors=[], scope='constructed input, no app inspection'))
    invocations, events = [], []
    for index, case in enumerate(cases):
        invocations.append(dict(index=index, cases=[case], state='exited', returncode=0,
                                started_at_unix_ms=10 + index * 10, finished_at_unix_ms=19 + index * 10,
                                system_sleep_ms=0, system_sleep_error=None,
                                reports=[dict(status='fail', invented=True)],
                                case_results=[dict(state='unrun', invented=True)],
                                harness_errors=[dict(code='invented')]))
        if case.get('engine') == 'pytest':
            continue
        report = dict(suite='fixture', test_id=case['test_id'], status='pass',
                      message='independently specified', interpreter=dict(realpath=sys.executable))
        write(out / 'suites' / case['id'] / 'report.json', report)
        for step, status in [('test_start', 'start'), ('test_end', 'pass')]:
            events.append(dict(kind='test_event', run_id='constructed-replay', suite='fixture',
                               test_id=case['test_id'], step=step, status=status))
    (out / 'events.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in events))
    write(out / 'dispatch.json', dict(run_id='constructed-replay', invocations=invocations))
    base = out / 'suites' / family_id
    write(base / 'selection.json', manifest)
    phases = [dict(kind='session_start', family=family_id, items=[family_id + '::one']),
              dict(kind='item_start', id=family_id + '::one')]
    for phase in ('setup', 'call', 'teardown'):
        phases.append(dict(kind='phase', id=family_id + '::one', phase=phase, outcome='passed',
                           duration=0.1, diagnostic=None, operations=['op']))
    phases.extend([dict(kind='item_finish', id=family_id + '::one'),
                   dict(kind='session_finish', exitstatus=0)])
    (base / 'phases.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in phases))
    command = dict(operation_id='op', state='closed', token='bound', command_pid=10,
                   settlement=dict(token='bound', authority_revoked=True, group_absent=True,
                                   command_pid=10, returncode=0))
    write(base / 'ownership.json', dict(closed=True, problems=[], commands=[command]))
    operations = [dict(kind='registered', operation_id='op'),
                  dict(kind='settled', operation_id='op', returncode=0)]
    (base / 'operations.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in operations))
    # Only engine_returncode is an input; every judgment here is deliberately false.
    write(base / 'family.json', dict(engine_returncode=0, ok=False, items=[],
                                     errors=['invented'], accounting_state='incomplete'))
    write(out / 'run.json', dict(run_id='constructed-replay', ok=False, terminal=False,
                                 counts={'pass': 99, 'fail': 99, 'skip': 99, 'total': 297}))


def require(value, message):
    if not value:
        raise AssertionError(message)


def check_replay(out, root):
    """Use fresh interpreter processes so candidate module imports cannot mix."""
    work = out / 'reporting-replay'
    work.mkdir()
    reader = work / 'reader'
    sources = {}
    for source in sorted((root / 'tests/lib').glob('*.py')):
        relative = source.relative_to(root)
        destination = reader / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        destination.write_bytes(data)
        sources[str(relative)] = hashlib.sha256(data).hexdigest()
    write(reader / 'reader-snapshot.json', dict(commit=None, kind='current file snapshot', sources=sources))
    baseline = work / 'raw-baseline'
    raw_fixture(baseline)
    helper = root / 'tests/lib/reporting_replay.py'
    observed = []
    expectations = {
        'valid': dict(ok=True, counts={'pass': 2, 'fail': 0, 'skip': 0, 'total': 2}, completed=3, unrun=0, errors=[]),
        'enforced_failure': dict(ok=False, counts={'pass': 1, 'fail': 1, 'skip': 0, 'total': 2}, completed=3, unrun=0, errors=['suite_exit']),
        'missing_report': dict(ok=False, counts={'pass': 1, 'fail': 0, 'skip': 0, 'total': 1}, completed=2, unrun=1, errors=['missing_report', 'unrun_case']),
        'contradictory_terminal': dict(ok=False, counts={'pass': 1, 'fail': 1, 'skip': 0, 'total': 2}, completed=3, unrun=0, errors=['status_mismatch']),
        'corrupt_operation': dict(ok=False, counts={'pass': 2, 'fail': 0, 'skip': 0, 'total': 2}, completed=2, unrun=1, errors=['suite_exit', 'unrun_case']),
        'artifact_changed': dict(ok=False, counts={'pass': 2, 'fail': 0, 'skip': 0, 'total': 2}, completed=3, unrun=0, errors=['artifact_changed']),
    }
    write(work / 'independent-expectations.json', expectations)
    for name, expected in expectations.items():
        source = work / (name + '-raw')
        shutil.copytree(baseline, source)
        report = source / 'suites/fixture/obligation/report.json'
        if name in ('enforced_failure', 'contradictory_terminal'):
            value = read(report)
            value.update(status='fail', message='designated enforced proposition failed')
            write(report, value)
        if name == 'enforced_failure':
            events = [json.loads(line) for line in (source / 'events.jsonl').read_text().splitlines()]
            events[1]['status'] = 'fail'
            (source / 'events.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in events))
            commands = read(source / 'dispatch.json')
            commands['invocations'][0]['returncode'] = 1
            write(source / 'dispatch.json', commands)
        elif name == 'missing_report':
            report.unlink()
        elif name == 'corrupt_operation':
            path = source / 'suites/fixture/family/phases.jsonl'
            phases = [json.loads(line) for line in path.read_text().splitlines()]
            phases[3]['operations'] = ['not-registered']
            path.write_text(''.join(json.dumps(event) + '\n' for event in phases))
        elif name == 'artifact_changed':
            write(source / 'artifact-integrity/after.json', {'changed': {'mode': 33188, 'sha256': 'a' * 64}})
        target = work / (name + '-replayed')
        argv = [sys.executable, '-B', '-S', str(helper), 'replay', str(reader), str(source), str(target)]
        command = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        write(work / (name + '-command.json'), dict(argv=argv, returncode=command.returncode,
                                                   stdout=command.stdout, stderr=command.stderr))
        require(command.returncode == 0, name + ': replay apparatus failed: ' + command.stderr)
        replay = read(target / 'replay.json')
        run = read(target / 'run.json')
        require(run['ok'] is expected['ok'], name + ': incorrect acceptance')
        require(run['counts'] == expected['counts'], name + ': incorrect legacy report counts')
        require(run['completion'] == dict(selected=3, completed=expected['completed'], skipped=0, unrun=expected['unrun']),
                name + ': incorrect completion counts')
        require(sorted(error['code'] for error in run['harness_errors']) == sorted(expected['errors']),
                name + ': wrong failure reasons: ' + str(run['harness_errors']))
        require(bool(replay['battery_problems']) == (not expected['ok']), name + ': battery eligibility differs')
        require(run['case_results'][1]['status'] == 'pass', name + ': valid neighbor lost')
        require('ok' in replay['target_differences'] if expected['ok'] else 'counts' in replay['target_differences'],
                name + ': poisoned derived target was not distinguished')
        if name == 'corrupt_operation':
            family = read(target / 'suites/fixture/family/family.json')
            require('command receipts and phase operation references differ' in family['errors'],
                    'operation fault did not identify its own boundary')
        elif name not in ('missing_report',):
            require(len(read(target / 'suites/fixture/family/family.json')['items']) == 1,
                    name + ': nested item count changed')
        observed.append(dict(name=name, expected=expected, exit_code=replay['exit_code'],
                             battery_problems=replay['battery_problems']))
    for name in ('missing_ownership', 'changed_reader'):
        source = work / (name + '-raw')
        shutil.copytree(baseline, source)
        selected_reader = reader
        if name == 'missing_ownership':
            (source / 'suites/fixture/family/ownership.json').unlink()
            expected_reason = 'ownership.json'
        else:
            selected_reader = work / 'changed-reader'
            shutil.copytree(reader, selected_reader)
            changed = selected_reader / 'tests/lib/suite_run.py'
            changed.write_text(changed.read_text() + '\n')
            expected_reason = 'reader snapshot bytes changed'
        target = work / (name + '-replayed')
        argv = [sys.executable, '-B', '-S', str(helper), 'replay', str(selected_reader), str(source), str(target)]
        command = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        write(work / (name + '-command.json'), dict(argv=argv, returncode=command.returncode,
                                                   stdout=command.stdout, stderr=command.stderr))
        require(command.returncode == 2 and expected_reason in command.stderr,
                name + ': incomplete replay input was not refused: ' + command.stderr)
        if name == 'missing_ownership':
            require(read(target / 'suites/fixture/neighbor/report.json')['status'] == 'pass',
                    'earlier observation lost after later missing receipt')
        observed.append(dict(name=name, refusal=expected_reason, returncode=command.returncode))
    write(work / 'observations.json', observed)
    return ['reporting-replay/' + row['name'] for row in observed]
