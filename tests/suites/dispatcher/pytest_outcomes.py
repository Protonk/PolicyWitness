"""Independent pure/commanded observation controls through the real dispatcher."""
import copy
import json
import os
from pathlib import Path
import shutil
import sys

import execution_contract
import outcomes
import pytest_family
import pytest_packages
import release_accept
import release_runs
from pytest_support import read, write, value_digest
from repository import install_runner

ROOT = Path(__file__).resolve().parents[3]
FAMILY = 'observations/controlled'
MODULE = 'tests/suites/observations/test_observations.py'

SOURCE = '''import json, os, sys
from pathlib import Path
import pytest


def spec(name, authority=None, commands='none'):
    return dict(schema_version=1, commands=commands,
                observations=[dict(id='measurement', promise='retained integer measurement')],
                judgments=[] if authority is None else [dict(id='comparison', authority=authority,
                    proposition='measurement equals independently chosen expectation', observations=['measurement'])])


@pytest.fixture
def recorded(pw_equipment, pw_inputs, tmp_path):
    target = tmp_path / 'input.json'
    target.write_text('{"measured": 3}')
    pw_inputs.track(tmp_path)
    return pw_equipment, json.loads(target.read_text())['measured']


@pytest.mark.pw_id('enforced')
@pytest.mark.pw_contract(spec('enforced', 'enforced'))
def test_enforced(recorded):
    equipment, measured = recorded
    evidence = equipment.publish('enforced.json', dict(measured=measured))
    equipment.observation('measurement', dict(measured=measured), [evidence])
    equipment.judgment('comparison', measured == 3, 'expected three')


@pytest.mark.pw_id('advisory')
@pytest.mark.pw_contract(spec('advisory', 'advisory'))
def test_advisory(recorded):
    equipment, measured = recorded
    evidence = equipment.publish('advisory.json', dict(measured=measured))
    equipment.observation('measurement', dict(measured=measured), [evidence])
    equipment.judgment('comparison', measured == 4, 'expected four; observed three')


@pytest.mark.pw_id('informational')
@pytest.mark.pw_contract(spec('informational'))
def test_informational(recorded):
    equipment, measured = recorded
    evidence = equipment.publish('informational.json', dict(measured=measured))
    equipment.observation('measurement', dict(measured=measured), [evidence])


@pytest.mark.pw_id('commanded')
@pytest.mark.pw_contract(spec('commanded', commands='recorded'))
def test_commanded(recorded, tmp_path):
    equipment, measured = recorded
    command = equipment.command([sys.executable, '-B', '-S', '-c',
        'import json,os; print(json.dumps([os.getcwd(),os.environ.get("PW_CONTROLLED"),os.environ.get("PYTHONPATH")]))'],
        equipment.artifacts / 'command', 5, cwd=tmp_path,
        env={'PATH':'/usr/bin:/bin', 'PW_CONTROLLED':'retained setting', 'PYTHONPATH':'controlled import path'})
    assert command['returncode'] == 0
    actual = json.loads((equipment.artifacts / 'command/stdout').read_text())
    assert actual == [str(tmp_path), 'retained setting', 'controlled import path']
    equipment.observation('measurement', dict(measured=measured), [equipment.reference(equipment.artifacts / 'command/stdout')])
'''


def require(value, message):
    if not value:
        raise AssertionError(message)


def fixture(control, name, source=SOURCE, *, second_family=False):
    root = control.out / ('outcomes-' + name) / 'repo'
    cases = {'observations':dict(cases=[dict(id='controlled', engine='pytest', module=MODULE, requires=[])]),
             'sentinel':dict(command=['bash','tests/suites/sentinel/run.sh'], cases=['later'])}
    if second_family:
        cases['observations']['cases'].append(dict(id='pure', engine='pytest', module='tests/suites/observations/test_pure.py', requires=[]))
    install_runner(ROOT, root, cases)
    for relative in ('tests/lib/pytest_engine.py', 'tests/lib/pytest_command_owner.py',
                     'tests/pytest.ini', 'tests/requirements-pytest.lock'):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    packages, _ = pytest_packages.target(ROOT)
    shutil.copytree(packages, root / packages.relative_to(ROOT))
    target = root / MODULE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source)
    if second_family:
        (root / 'tests/suites/observations/test_pure.py').write_text('''import pytest
@pytest.mark.pw_id('pure')
@pytest.mark.pw_commands('none')
def test_pure(pw_equipment, pw_inputs):
    pw_equipment.publish('pure.json', dict(value=7))
    assert 7 == 7, 'independently expected pure value'
''')
    sentinel = root / 'tests/suites/sentinel/run.sh'
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text('#!/bin/bash\nset -euo pipefail\nsource tests/lib/case.sh\ntest_begin sentinel later\nprintf observed > "$PW_TEST_ARTIFACTS/external-start"\ntest_pass "independent later case completed"\n')
    return root


def run(control, integration, name, source=SOURCE, expected=0, *, second_family=False):
    root = fixture(control, name, source, second_family=second_family)
    independently_expected = execution_contract.defaults(root)
    write(root.parent / 'expected-producer.json', independently_expected)
    out, result = integration.run(root, expected=expected, environment={'PW_TEST_QUIET':'1'})
    family = read(out / 'suites' / FAMILY / 'family.json')
    require(result['case_results'][-1]['status'] == 'pass', name + ': independent neighbor did not run')
    require(read(out / 'suites' / FAMILY / 'ownership.json')['closed'], name + ': ownership unsettled')
    return root, out, result, family, independently_expected


def problems(result, expected, out):
    return execution_contract.problems(result, expected, lambda name:read(out / name), lambda name:(out / name).read_bytes())


def mechanism_comparison(control):
    """A test-local terminal proposal and the chosen phase account share obligations.

    The alternative is a complete bound account, not a status-label shortcut.
    No alternate production runner or publication format is installed.
    """
    specification = dict(schema_version=1, observations=[dict(id='measurement', promise='integer measured independently')],
        judgments=[dict(id='comparison', authority='enforced', proposition='measured integer equals three', observations=['measurement'])])
    evidence = b'{"measured":3}\n'
    observation = dict(id='measurement', facts=dict(measured=3), evidence=[outcomes.file_reference('measurement.json', evidence)])
    favorable = dict(**specification['judgments'][0], result='favorable', detail='three observed')
    cases = [
        ('enforced', specification, [observation], [favorable], [], True, True),
        ('enforced-unfavorable', {**specification, 'judgments':[{**specification['judgments'][0], 'proposition':'measured integer equals four'}]},
         [observation], [{**favorable, 'proposition':'measured integer equals four', 'result':'unfavorable'}], [], True, False),
        ('advisory-unfavorable', {**specification, 'judgments':[{**specification['judgments'][0], 'authority':'advisory', 'proposition':'measured integer equals four'}]},
         [observation], [{**favorable, 'authority':'advisory', 'proposition':'measured integer equals four', 'result':'unfavorable'}], [], True, True),
        ('informational', {**specification, 'judgments':[]}, [observation], [], [], True, True),
        ('missing-observation', specification, [], [favorable], [], False, False),
        ('contradictory-authority', specification, [observation], [{**favorable, 'authority':'advisory'}], [], False, False),
        ('cleanup-failure', specification, [observation], [favorable], [dict(kind='cleanup', message='owned fixture not settled', evidence=[])], False, False),
        ('failed-observation-phase', specification, [observation], [favorable], [], False, False),
        ('broken-observation', specification, [observation], [favorable], [], False, False),
        ('release-reread-missing', specification, [observation], [favorable], [], False, False),
    ]
    records = []
    for name, spec, observations, judgments, failures, valid, accepted in cases:
        account = dict(schema_version=1, observations=observations, judgments=judgments, failures=failures)
        terminal = dict(specification_sha256=value_digest(spec), outcome_account=account,
                        phases={phase:('failed' if name == 'failed-observation-phase' and phase == 'call' else 'passed')
                                for phase in ('setup','call','teardown')}, complete=True)
        phase_rows = [dict(role=role, record=row) for role in ('observations', 'judgments', 'failures') for row in account[role]]
        captured = outcomes.empty_account()
        for row in phase_rows:
            captured[row['role']].append(row['record'])
        files = {'measurement.json':b'corrupted' if name == 'broken-observation' else evidence}
        if name == 'release-reread-missing':
            files = {}
        def load(path):
            if path not in files:
                raise ValueError('required artifact missing: ' + path)
            return files[path]
        # Both arrangements carry the same independently selected authority,
        # engine-completion facts and cleanup obligation.
        require(terminal['specification_sha256'] == value_digest(spec) and set(terminal['phases']) == {'setup','call','teardown'},
                'terminal alternative lost binding or engine completion')
        left = outcomes.assess(spec, terminal['outcome_account'], load)
        right = outcomes.assess(spec, captured, load)
        if any(status != 'passed' for status in terminal['phases'].values()):
            for assessment in (left, right):
                assessment['errors'].append('engine observation phase failed')
                assessment.update(valid=False, accepted=False)
        require((left['valid'], left['accepted']) == (valid, accepted) and left == right,
                'mechanism contrast differed from independent expected decision: ' + name)
        records.append(dict(name=name, expected=dict(valid=valid, accepted=accepted), specification=spec,
                            terminal_proposal=terminal, attached_phase_rows=phase_rows, terminal_assessment=left, phase_assessment=right))
    # If execution stops after recording a measurement but before terminal
    # publication, an extended terminal form alone has no account to interpret.
    # A phase journal retains that prefix; it still refuses incomplete execution.
    prefix = outcomes.empty_account(); prefix['observations'].append(observation)
    partial = outcomes.assess(specification, prefix, lambda name:evidence)
    require(not partial['valid'] and partial['counts']['observations']['completed'] == 1,
            'attached account either credited incomplete execution or discarded its observation')
    records.append(dict(name='interrupted-before-terminal', terminal_proposal=None,
                        terminal_completion=False, attached_prefix=prefix, phase_assessment=partial,
                        chosen_reason='Both complete representations preserve decisions. Existing engine phases already retain prefix and lifecycle; a terminal proposal needs an additional required durable journal to preserve the same prefix.'))
    path = control.out / 'outcome-mechanism-comparison.json'
    write(path, records)
    control.note('bounded terminal-account and phase-account comparison', artifact=str(path),
                 complete_representations_equivalent=True, interruption_remains_incomplete=True)


def exercise(control, integration):
    mechanism_comparison(control)
    root, out, result, family, expected = run(control, integration, 'mixed')
    items = family['items']
    require(family['ok'] and family['accounting_state'] == 'complete', 'valid mixed family refused')
    require([row['outcome'] for row in items] == ['completed'] * 4, 'observation completion credited as legacy product pass')
    require(items[0]['assessment']['counts']['enforced'] == dict(favorable=1, unfavorable=0), 'enforced judgment count')
    require(items[1]['assessment']['counts']['advisory'] == dict(favorable=0, unfavorable=1), 'advisory judgment count')
    require([row['assessment']['counts']['informational'] for row in items] == [0,0,1,1], 'informational completions counted as judgments')
    require([bool({op for phase in row['phases'].values() for op in phase['operations']}) for row in items] == [False,False,False,True], 'pure/commanded scopes differ')
    require(not problems(result, expected, out), 'battery reader refused valid mixed outcome family')
    terminal = (root.parent / 'run-invocation/stdout').read_text()
    require('ADVISORY comparison: unfavorable' in terminal and 'Family report:' in terminal, 'quiet display concealed unfavorable advisory')
    ownership = read(out / 'suites' / FAMILY / 'ownership.json')
    require(len(ownership['commands']) == 1 and ownership['commands'][0].get('explicit_context') is True,
            'controlled command context not registered once')
    require('environment' not in ownership['commands'][0], 'raw caller environment published in ownership')
    require(ownership['commands'][0]['context']['test_environment'] == {'PYTHONPATH':'controlled import path'},
            'explicit controlled test environment was not retained')
    control.note('pure enforced, unfavorable advisory, informational and commanded items retain exact counts and controlled context', output=str(out))

    # The battery validator is tested with independently constructed app admission
    # facts. This establishes reporting acceptance, not signature or live-app credit.
    candidate = copy.deepcopy(result)
    app = Path('/controlled/extracted/PolicyWitness.app')
    candidate['configuration']['app_dir'] = str(app)
    candidate['artifact_integrity'] = dict(valid_before=True, unchanged=True)
    require(not release_accept.battery_problems(candidate, app, expected=expected, evidence=out),
            'candidate battery refused valid non-gating judgment')
    acceptance = root.parent / 'portable-source'
    shutil.copytree(out, acceptance / 'tests')
    write(acceptance / 'acceptance.json', dict(schema_version=3, ok=True, execution_contract=expected))
    entry = dict(path='release-acceptance/outcome-control', run_id=result['run_id'], source='0'*40,
                 app_inventory=None, reason='constructed pure/commanded outcome account')
    portable = root.parent / 'portable-valid'
    release_runs.pack(portable, tag='v0.0.0', source='0'*40, runs={'acceptance':(acceptance, entry)},
                      battery=('acceptance','tests/run.json'), expected_contract=expected)
    release_runs.verify_bundle(portable, expected_contract=expected)
    missing = acceptance / 'tests/suites' / FAMILY / 'artifacts/advisory.json'
    missing.unlink()
    try:
        release_runs.pack(root.parent / 'portable-missing', tag='v0.0.0', source='0'*40,
                          runs={'acceptance':(acceptance, entry)}, battery=('acceptance','tests/run.json'),
                          expected_contract=expected)
    except (OSError, ValueError, KeyError) as exc:
        write(root.parent / 'portable-missing-refusal.json', dict(error=str(exc)))
    else:
        raise AssertionError('portable evidence accepted a missing advisory observation artifact')
    control.note('candidate and portable readers accept valid unfavorable advisory and refuse missing raw observation', output=str(root.parent))

    _, pair_out, pair_result, _, pair_expected = run(control, integration, 'two-families', second_family=True)
    first = read(pair_out / 'suites' / FAMILY / 'ownership.json')
    second = read(pair_out / 'suites/observations/pure/ownership.json')
    require(len(first['commands']) == 1 and second['commands'] == [] and first['closed'] and second['closed'],
            'family ownership includes another family command or conceals unresolved work')
    require(not problems(pair_result, pair_expected, pair_out), 'two-family ownership refused by candidate reader')
    require(pair_result['outcomes']['nested']['experiments'] == 4 and pair_result['outcomes']['nested']['informational'] == 2,
            'two-family nested scope double counts parent completion')
    control.note('commanded then pure families have distinct ownership accounts within one run', output=str(pair_out))
    pure = read(pair_out / 'suites/observations/pure/family.json')
    require(pure['items'][0]['outcome'] == 'passed' and 'assessment' not in pure['items'][0]
            and pure['items'][0]['command_scope'] == 'none', 'pure ordinary assertions were relabelled informational')
    pure_root = fixture(control, 'pure-enforced-failure', second_family=True)
    module = pure_root / 'tests/suites/observations/test_pure.py'
    module.write_text(module.read_text().replace('assert 7 == 7', 'assert 7 == 8'))
    pure_out, pure_result = integration.run(pure_root, expected=1)
    pure_failed = read(pure_out / 'suites/observations/pure/family.json')
    require(pure_failed['items'][0]['phases']['call']['outcome'] == 'failed'
            and 'independently expected pure value' in pure_failed['items'][0]['phases']['call']['diagnostic'],
            'incorrect pure enforced fact was not its designated assertion failure')
    require(pure_result['case_results'][-1]['status'] == 'pass', 'pure enforced failure suppressed valid neighbor')
    control.note('pure ordinary assertions preserve enforced pass/failure authority without invented judgment counts', output=str(pure_out))
    for mode, scope, expected_exit in (('commanded-enforced','recorded',0), ('pure-acquired-command','none',1)):
        scoped_root = fixture(control, mode, second_family=True)
        module = scoped_root / 'tests/suites/observations/test_pure.py'
        body = module.read_text().replace("pw_commands('none')", "pw_commands(" + repr(scope) + ")")
        body = body.replace("    assert 7 == 7", "    receipt = pw_equipment.command(['/bin/echo','scoped'],pw_equipment.artifacts/'scoped-command',5)\n    assert receipt['returncode'] == 0\n    assert (pw_equipment.artifacts/'scoped-command/stdout').read_text() == 'scoped\\n'\n    assert 7 == 7")
        module.write_text(body)
        scoped_expected = execution_contract.defaults(scoped_root)
        scoped_out, scoped_result = integration.run(scoped_root, expected=expected_exit)
        scoped = read(scoped_out / 'suites/observations/pure/family.json')
        owned = read(scoped_out / 'suites/observations/pure/ownership.json')
        require(len(owned['commands']) == 1 and owned['closed'], 'ordinary commanded item lost complete own command account')
        require(bool(problems(scoped_result, scoped_expected, scoped_out)) == bool(expected_exit), 'command scope admission differs at battery reader')
        require(scoped_result['case_results'][-1]['status'] == 'pass', 'command scope fault suppressed neighbor')
        if expected_exit:
            require(any('declared none/recorded' in error for error in scoped['errors']), 'undeclared command has no designated validity failure')
        else:
            require(scoped['items'][0]['outcome'] == 'passed' and 'assessment' not in scoped['items'][0], 'ordinary commanded enforcement changed authority')
        control.note('ordinary pytest command scope ' + mode, output=str(scoped_out))

    contrasts = [
        ('enforced-false', 'measured == 3', 'measured == 4', 'blocking'),
        ('missing-observation', "equipment.observation('measurement', dict(measured=measured), [evidence])\n    equipment.judgment('comparison', measured == 4", "equipment.judgment('comparison', measured == 4", 'missing'),
        ('missing-judgment', "    equipment.judgment('comparison', measured == 4, 'expected four; observed three')", "    pass", 'missing'),
        ('unexpected-assertion', "    equipment.judgment('comparison', measured == 4, 'expected four; observed three')", "    equipment.judgment('comparison', measured == 4, 'expected four; observed three')\n    assert False, 'independent unexpected execution failure'", 'phase'),
        ('changed-artifact', "    equipment.judgment('comparison', measured == 4, 'expected four; observed three')", "    equipment.judgment('comparison', measured == 4, 'expected four; observed three')\n    (equipment.artifacts / 'advisory.json').write_text('changed after observation')", 'changed'),
        ('teardown-failure', "    return pw_equipment, json.loads(target.read_text())['measured']", "    yield pw_equipment, json.loads(target.read_text())['measured']\n    assert False, 'independent teardown failure'", 'cleanup'),
    ]
    for name, before, after, kind in contrasts:
        require(SOURCE.count(before) == 1, 'control mutation must have exactly one target: ' + name)
        _, fault_out, fault_result, fault_family, fault_expected = run(control, integration, name, SOURCE.replace(before, after), 1)
        require(not fault_family['ok'] and problems(fault_result, fault_expected, fault_out), name + ': invalid observation accepted')
        if kind == 'blocking':
            judged = fault_family['items'][0]
            require(judged['assessment']['valid'] and judged['assessment']['blocking_judgments'][0]['id'] == 'comparison', 'enforced false became failed apparatus')
        elif kind in ('phase', 'cleanup'):
            judged = fault_family['items'][1]
            require(judged['assessment']['advisory_judgments'][0]['result'] == 'unfavorable', 'independent fault erased advisory')
            phase = 'call' if kind == 'phase' else 'teardown'
            require(judged['phases'][phase]['outcome'] == 'failed', 'independent execution failure lost phase')
        control.note('outcome control ' + name, output=str(fault_out))

    # Alter terminal projections while fixing their immediate manifest digest.
    # The independently captured expectation is never changed.
    folder = out / 'suites' / FAMILY
    original = {name:path.read_bytes() for path in folder.rglob('*') if path.is_file()
                for name in [path.relative_to(out).as_posix()]}
    for name in ('relabelled', 'deleted-judgment', 'dropped-member', 'dropped-command', 'missing-command-output', 'changed-command-output', 'foreign-command-owner', 'malformed-settlement', 'duplicate-phase-key', 'duplicate-family-key', 'scalar-phase-event', 'missing-pure-operations', 'null-account', 'malformed-observations', 'missing-input', 'contradictory-projection', 'missing-run-summary', 'false-run-summary', 'false-parent-status'):
        files = dict(original)
        altered_result = copy.deepcopy(result)
        def replace(relative, value):
            files['suites/' + FAMILY + '/' + relative] = json.dumps(value).encode()
        if name == 'missing-run-summary':
            altered_result.pop('outcomes')
        elif name == 'false-run-summary':
            altered_result['outcomes']['nested']['advisory']['unfavorable'] = 0
        elif name == 'false-parent-status':
            altered_result['case_results'][0]['status'] = 'pass'
        elif name in ('relabelled', 'deleted-judgment', 'contradictory-projection'):
            altered = copy.deepcopy(family)
            account = altered['items'][1]['outcome_account']
            if name == 'relabelled': account['judgments'][0]['authority'] = 'enforced'
            elif name == 'deleted-judgment': account['judgments'] = []
            else: altered['items'][1]['assessment']['advisory_judgments'] = []
            replace('family.json', altered)
        elif name == 'dropped-member':
            selection = read(folder / 'selection.json'); selection['items'] = selection['items'][:-1]
            replace('selection.json', selection)
            altered_result['plan']['cases'][0]['items'] = selection
        elif name == 'dropped-command':
            files['suites/' + FAMILY + '/operations.jsonl'] = b''
        elif name in ('missing-command-output', 'changed-command-output'):
            path = 'suites/' + FAMILY + '/artifacts/command/stdout'
            if name == 'missing-command-output':
                del files[path]
            else:
                files[path] = b'changed after command settlement'
        elif name in ('null-account', 'malformed-observations'):
            altered = copy.deepcopy(family)
            if name == 'null-account':
                altered['items'][1]['outcome_account'] = None
            else:
                altered['items'][1]['outcome_account']['observations'] = {'unexpected':'map'}
            replace('family.json', altered)
        elif name == 'malformed-settlement':
            altered = read(folder / 'ownership.json')
            altered['commands'][0]['settlement'] = []
            replace('ownership.json', altered)
        elif name == 'missing-pure-operations':
            altered = copy.deepcopy(family)
            target = altered['items'][0]
            for phase in target['phases'].values():
                phase.pop('operations')
            replace('family.json', altered)
            path = 'suites/' + FAMILY + '/phases.jsonl'
            events = [json.loads(line) for line in files[path].splitlines()]
            for event in events:
                if event.get('kind') == 'phase' and event.get('id') == target['id']:
                    event.pop('operations')
            files[path] = b''.join(json.dumps(event).encode() + b'\n' for event in events)
        elif name == 'scalar-phase-event':
            files['suites/' + FAMILY + '/phases.jsonl'] = b'null\n'
        elif name == 'duplicate-family-key':
            path = 'suites/' + FAMILY + '/family.json'
            files[path] = b'{"schema_version":2,' + files[path][1:]
        elif name == 'duplicate-phase-key':
            path = 'suites/' + FAMILY + '/phases.jsonl'
            first, *rest = files[path].splitlines()
            files[path] = b'\n'.join([b'{"kind":"session_start",' + first[1:], *rest]) + b'\n'
        elif name == 'foreign-command-owner':
            altered = read(folder / 'ownership.json')
            altered['commands'][0]['family'] = 'foreign/family'
            replace('ownership.json', altered)
        else:
            reference = items[0]['phases']['setup']['inputs'][0]['path']
            del files['suites/' + FAMILY + '/' + reference]
        errors = execution_contract.problems(altered_result, expected,
                    lambda relative:json.loads(files[relative]), lambda relative:files[relative])
        require(errors, 'tampered evidence accepted: ' + name)
        write(root.parent / ('rejected-' + name + '.json'), dict(errors=errors))
    require({name:(out / name).read_bytes() for name in original} == original, 'rereading controls changed original evidence')
    control.note('independently captured authority and raw receipts reject deletion, relabeling and contradictory terminal accounts', output=str(root.parent))
