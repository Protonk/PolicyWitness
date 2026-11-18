"""Source-bound expectations supplied by PW, independently of engine result fields."""
import json
from pathlib import Path

import outcomes
from pytest_support import digest, value_digest

LEGACY_PROFILE = 'pw-family-evidence-1'
PROFILE = 'pw-family-evidence-2'


def capture(root, cases):
    catalog_path = root / 'tests/catalog.json'
    source = dict(catalog=json.loads(catalog_path.read_text()), catalog_sha256=digest(catalog_path),
                  reader_sha256=digest(Path(__file__)))
    selected = []
    for case in cases:
        row = dict(id=case['id'], engine=case.get('engine', 'legacy'))
        if 'outcome_contract' in case:
            outcomes.validate_spec(case['outcome_contract'])
            row['outcome_contract'] = case['outcome_contract']
            row['report'] = f"suites/{case['report_suite']}/{case['test_id']}/report.json"
        selected.append(row)
    explicit = any('outcome_contract' in case or (case.get('items') or {}).get('schema_version') == 2 for case in cases)
    contract = dict(profile=PROFILE if explicit else LEGACY_PROFILE, source=source, selected=selected,
                    required_families=[c['id'] for c in selected if c['engine'] == 'pytest'])
    if explicit:
        contract['family_selections'] = {c['id']:c.get('items') for c in cases if c.get('engine') == 'pytest'}
    contract['identity'] = value_digest(contract)
    return contract


def defaults(root):
    """Capture family membership and authority independently before a battery runs.

    Collection uses the ordinary read-only engine and stops before eligibility;
    it neither acquires experimental equipment nor supplies a test verdict.
    """
    from types import SimpleNamespace
    from test_cli import catalog, select
    from pytest_family import Collector
    cases, suites = catalog(root)
    selected = select(cases, suites, SimpleNamespace(case=[], suite=[], all=False))
    for case in selected:
        if case.get('engine') == 'pytest':
            collector = Collector(root, case)
            try:
                case['items'] = collector.manifest
            finally:
                collector.stop()
                collector.log.close()
    return capture(root, selected)


def validate_contract(contract):
    if contract.get('profile') not in (LEGACY_PROFILE, PROFILE):
        raise ValueError('unknown producer evidence contract')
    payload = {k:v for k,v in contract.items() if k != 'identity'}
    if value_digest(payload) != contract.get('identity'):
        raise ValueError('execution contract identity mismatch')
    if contract['required_families'] != [c['id'] for c in contract['selected'] if c['engine'] == 'pytest']:
        raise ValueError('required family declaration differs from independently selected engines')
    if contract['profile'] == LEGACY_PROFILE and ('family_selections' in contract or any('outcome_contract' in row for row in contract['selected'])):
        raise ValueError('legacy producer contract cannot introduce observation authority')
    if contract['profile'] == PROFILE:
        if set(contract.get('family_selections', {})) != set(contract['required_families']):
            raise ValueError('missing independent family collection')
        for selected in contract['selected']:
            if 'outcome_contract' in selected:
                outcomes.validate_spec(selected['outcome_contract'])
                if not isinstance(selected.get('report'), str):
                    raise ValueError('explicit case has no independently required report')
        for name, selection in contract['family_selections'].items():
            if selection is None:
                continue
            if selection.get('family') != name or selection.get('schema_version') not in (1, 2):
                raise ValueError('invalid independently collected family')
            ids = [row['id'] for row in selection['items']]
            if not ids or len(set(ids)) != len(ids):
                raise ValueError('invalid independently collected item population')
            for row in selection['items']:
                if 'command_scope' in row and row['command_scope'] not in ('none', 'recorded'):
                    raise ValueError('invalid independently collected command scope')
                if 'outcome_contract' in row:
                    outcomes.validate_spec(row['outcome_contract'])
                    if row['outcome_contract'].get('commands') not in ('none', 'recorded'):
                        raise ValueError('explicit pytest item has no command declaration')


def validate_family(family, ownership, selection, load_bytes=None):
    """Validate schema 1 under its old native-item contract; schema 2 is explicit."""
    errors = []
    if not all(isinstance(value, dict) for value in (family, ownership, selection)):
        return ['missing or malformed family evidence object']
    expected = [r['id'] for r in selection['items']]
    if family.get('manifest_digest') != value_digest(selection):
        errors.append('family manifest identity mismatch')
    items = family.get('items', [])
    if not isinstance(items, list) or any(not isinstance(row, dict) for row in items):
        return ['missing or malformed family item account']
    if [r.get('id') for r in items] != expected or len(set(expected)) != len(expected) or not expected:
        errors.append('incomplete family item account')
    explicit = selection.get('schema_version', 1) == 2
    if selection.get('schema_version', 1) not in (1, 2):
        errors.append('unsupported family selection schema')
    if (family.get('accounting_state') != 'complete' or family.get('ok') is not True or
            any(i.get('outcome') not in (('passed', 'completed') if explicit else ('passed',)) for i in items)):
        errors.append('family did not complete successfully')
    if not explicit and family.get('schema_version', 1) != 1:
        errors.append('legacy selection cannot accept a newer family schema')
    expected_explicit = any('outcome_contract' in row for row in selection['items'])
    if explicit and (family.get('schema_version') != 2 or family.get('explicit') is not expected_explicit):
        errors.append('explicit family projection missing')
    if explicit and ownership.get('family') != selection.get('family'):
        errors.append('ownership scope differs from collected family')
    referenced = set()
    by_id = {row['id']:row for row in selection['items']}
    for item in items:
        phases = item.get('phases', {})
        if not isinstance(phases, dict) or any(not isinstance(row, dict) for row in phases.values()):
            errors.append('missing or malformed item phase account')
            continue
        if set(phases) != {'setup', 'call', 'teardown'} or any(p.get('outcome') != 'passed' for p in phases.values()):
            errors.append('missing or unsuccessful item phases')
        if explicit and any(not isinstance(phase.get('operations'), list)
                            or any(not isinstance(value, str) or not value for value in phase['operations'])
                            or len(set(phase['operations'])) != len(phase['operations']) for phase in phases.values()):
            errors.append('item phases lack explicit distinct command reference lists')
            continue
        item_operations = {op for phase in phases.values() for op in phase.get('operations', [])}
        declaration = by_id.get(item.get('id'), {})
        specification = declaration.get('outcome_contract')
        if specification is not None:
            if not explicit or item.get('outcome_contract') != specification:
                errors.append('item authority differs from independently collected declaration')
            if load_bytes is None:
                errors.append('explicit item has no artifact byte reader')
            assessment = outcomes.assess(specification, item.get('outcome_account'), load_bytes)
            if item.get('assessment') != assessment:
                errors.append('item assessment differs from required account')
            if not assessment['accepted']:
                errors.extend(assessment['errors'])
                errors.extend('enforced judgment unfavorable: ' + row['id'] for row in assessment['blocking_judgments'])
            if bool(item_operations) != (specification.get('commands') == 'recorded'):
                errors.append('item commands differ from its none/recorded declaration')
        elif 'outcome_contract' in item or 'outcome_account' in item:
            errors.append('undeclared outcome authority')
        elif 'command_scope' in declaration:
            if not explicit or item.get('command_scope') != declaration['command_scope']:
                errors.append('item command scope differs from independently collected declaration')
            if bool(item_operations) != (declaration['command_scope'] == 'recorded'):
                errors.append('item command set differs from declared none/recorded scope')
        elif 'command_scope' in item:
            errors.append('undeclared command scope')
        elif not item_operations:
            errors.append('native item has no command observation')
        if specification is None and item.get('outcome') != 'passed':
            errors.append('ordinary enforced item did not pass')
        if specification is not None or 'command_scope' in declaration:
            for phase in phases.values():
                try:
                    from pytest_family import validate_inputs
                    validate_inputs(phase, selection, load_bytes)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    errors.append('item input evidence: ' + str(exc))
        referenced |= item_operations
    if referenced != set(family.get('operations', [])):
        errors.append('item command references differ from declared operation set')
    if ownership.get('closed') is not True or ownership.get('problems'):
        errors.append('ownership not closed')
    commands = ownership.get('commands')
    if (not isinstance(commands, list) or any(not isinstance(row, dict)
            or not isinstance(row.get('settlement'), dict) for row in commands)):
        errors.append('ownership operation set missing or malformed')
    else:
        from pytest_resources import disposition
        if any(disposition(r) != 'closed' for r in commands):
            errors.append('ownership closure lacks settlement')
        ids = [r['operation_id'] for r in commands]
        if len(set(ids)) != len(ids) or sorted(ids) != sorted(family.get('operations', [])):
            errors.append('ownership operation set differs from family command receipts')
        if explicit and any(any(row.get('settlement', {}).get(key) for key in
                                ('never_launched', 'timed_out', 'cancelled', 'group_signalled_after_leader_exit')) for row in commands):
            errors.append('experiment command did not complete without owner intervention')
    return errors


def _json_rows(data):
    rows = [outcomes.decode(line) for line in data.splitlines()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError('raw evidence stream requires object records')
    return rows


def _family_raw(family, ownership, selection, load_bytes):
    """Compare terminal projection with raw phases and registered/settled commands."""
    from pytest_family import account
    events = _json_rows(load_bytes('phases.jsonl'))
    operations = _json_rows(load_bytes('operations.jsonl'))
    registered, settled = {}, {}
    for row in operations:
        operation = row['operation_id']
        if row['kind'] == 'registered' and operation not in registered and operation not in settled:
            registered[operation] = row
        elif row['kind'] == 'settled' and operation in registered and operation not in settled:
            settled[operation] = row
        else:
            raise ValueError('invalid operation registration/settlement sequence')
    if any(not isinstance(row, dict) or not isinstance(row.get('settlement'), dict)
           for row in ownership['commands']):
        raise ValueError('malformed raw command ownership/settlement')
    commands = {row['operation_id']:row for row in ownership['commands']}
    item_ids = {row['id'] for row in selection['items']}
    prefix = 'suites/' + selection['family'] + '/'
    if set(registered) != set(settled) or set(registered) != set(commands):
        raise ValueError('raw operation accounting differs from ownership')
    for operation, command in commands.items():
        if command.get('family') != selection['family'] or command.get('item') not in item_ids:
            raise ValueError('raw command identity differs from collected family/item')
        if registered[operation]['item'] != command['item']:
            raise ValueError('registered command item differs from ownership')
        receipt = settled[operation]
        if any(receipt.get(key) != value for key, value in command['settlement'].items()):
            raise ValueError('raw settlement contradicts ownership')
        if receipt.get('context') != command.get('context'):
            raise ValueError('raw settlement contradicts command context')
        directory = registered[operation]['artifacts']
        if not isinstance(directory, str) or not directory.startswith(prefix + 'artifacts/'):
            raise ValueError('registered command artifacts leave their family')
        directory = directory[len(prefix):]
        names = [directory + '/' + name for name in ('command.json', 'stdout', 'stderr')]
        if selection.get('schema_version') == 2:
            outcomes.validate_evidence(receipt.get('evidence'), load_bytes)
            if [row['path'] for row in receipt['evidence']] != names:
                raise ValueError('command evidence differs from required raw receipt/output set')
        raw_command = outcomes.decode(load_bytes(names[0]))
        if raw_command != dict(argv=command['argv'], context=command['context'], **command['settlement']):
            raise ValueError('raw command receipt contradicts ownership')
        for name in names[1:]:
            if not isinstance(load_bytes(name), bytes):
                raise ValueError('raw command output is unavailable')
    replayed = account(selection, events, family['engine_returncode'], ownership, list(registered), load_bytes)
    if family != replayed:
        raise ValueError('terminal family account differs from raw execution evidence')


def _shell_raw(report, specification, load_bytes, *, run_id=None, expected_events=None):
    if not isinstance(report, dict) or type(report.get('schema_version')) is not int or report['schema_version'] != 2:
        raise ValueError('explicit case requires schema 2 report')
    if outcomes.decode(load_bytes('outcome-contract.json')) != specification:
        raise ValueError('case authority differs from independently selected specification')
    journal = outcomes.empty_account()
    for row in _json_rows(load_bytes('outcomes.jsonl')):
        if set(row) != {'kind', 'record'} or row['kind'] not in ('observations', 'judgments', 'failures'):
            raise ValueError('invalid outcome journal row')
        journal[row['kind']].append(row['record'])
    if outcomes.decode(load_bytes('outcomes.json')) != journal or report.get('outcome_account') != journal:
        raise ValueError('terminal outcome account differs from its journal')
    assessment = outcomes.assess(specification, journal, load_bytes)
    if report.get('assessment') != assessment:
        raise ValueError('terminal assessment differs from required account')
    status = 'complete' if assessment['accepted'] else 'fail'
    if report.get('status') != status:
        raise ValueError('terminal case status contradicts required account')
    events = _json_rows(load_bytes('events.jsonl'))
    if expected_events is not None and events != expected_events:
        raise ValueError('local and run case lifecycle evidence differ')
    identity = (report.get('suite'), report.get('test_id'))
    if any(row.get('kind') != 'test_event' or (row.get('suite'), row.get('test_id')) != identity
           or (run_id is not None and row.get('run_id') != run_id) for row in events):
        raise ValueError('case lifecycle identity differs from selected run/case')
    starts = [index for index, row in enumerate(events) if row.get('step') == 'test_start']
    ends = [index for index, row in enumerate(events) if row.get('step') == 'test_end']
    if starts != [0] or ends != [len(events) - 1] or len(events) < 2 or events[0].get('status') != 'start':
        raise ValueError('case lifecycle requires one ordered start and terminal event')
    terminal = events[-1]
    if (terminal.get('status') != status or terminal.get('duration_ms') != report.get('duration_ms')
            or terminal.get('outcome_account_sha256') != value_digest(journal)):
        raise ValueError('terminal event contradicts required account')
    return assessment


def problems(run, expected, load, load_bytes=None):
    """Expected authority is captured outside mutable results. Byte loaders are bounded."""
    validate_contract(expected)
    errors, assessments, observation_reports = [], [], []
    if not isinstance(run, dict):
        return ['missing or malformed run evidence object']
    parents_reported = run.get('case_results', [])
    if not isinstance(parents_reported, list) or any(not isinstance(row, dict) for row in parents_reported):
        errors.append('missing or malformed parent case account')
        parents_reported = []
    if run.get('execution_contract') != expected:
        errors.append('missing or changed independently expected execution contract')
    current = expected['profile'] == PROFILE
    def read_object(name):
        if current:
            if load_bytes is None:
                raise ValueError('current evidence requires an artifact byte reader')
            return outcomes.decode(load_bytes(name))
        return load(name)
    if current:
        plan = run.get('plan')
        planned = plan.get('cases') if isinstance(plan, dict) else None
        if not isinstance(planned, list) or any(not isinstance(row, dict) for row in planned):
            errors.append('missing or malformed run selection')
            planned = []
        if [(row.get('id'), row.get('engine', 'legacy')) for row in planned] != [(row['id'], row['engine']) for row in expected['selected']]:
            errors.append('run selection differs from independently selected cases')
        for selected in expected['selected']:
            case = [row for row in planned if row.get('id') == selected['id']]
            if len(case) != 1 or case[0].get('outcome_contract') != selected.get('outcome_contract'):
                errors.append('case authority differs from independently selected expectation: ' + selected['id'])
            if 'outcome_contract' not in selected:
                continue
            try:
                if load_bytes is None:
                    raise ValueError('explicit case has no artifact byte reader')
                report = read_object(selected['report'])
                parts = selected['report'].split('/')
                if (len(parts) != 4 or parts[0] != 'suites' or parts[3] != 'report.json'
                        or not isinstance(report, dict) or (report.get('suite'), report.get('test_id')) != tuple(parts[1:3])):
                    raise ValueError('case report identity differs from selected report path')
                base = selected['report'].rsplit('/', 1)[0] + '/'
                events = [row for row in _json_rows(load_bytes('events.jsonl'))
                          if (row.get('suite'), row.get('test_id')) == tuple(parts[1:3])]
                assessment = _shell_raw(report, selected['outcome_contract'], lambda name:load_bytes(base + name),
                                        run_id=run.get('run_id'), expected_events=events)
                assessments.append(('parent', selected['id'], assessment))
                observation_reports.append(report)
                if not assessment['accepted']:
                    errors.extend(selected['id'] + ': ' + error for error in assessment['errors'])
                    errors.extend(selected['id'] + ': enforced judgment unfavorable: ' + row['id'] for row in assessment['blocking_judgments'])
                parents = [row for row in parents_reported if row.get('id') == selected['id']]
                if len(parents) != 1 or parents[0].get('state') != 'completed' or parents[0].get('status') != report['status']:
                    raise ValueError('parent outcome contradicts required case report')
                if parents[0].get('assessment') != assessment:
                    raise ValueError('parent assessment contradicts required case account')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append('required case outcome evidence: ' + selected['id'] + ': ' + str(exc))
    for family in expected['required_families']:
        parents = [c for c in parents_reported if c.get('id') == family]
        if len(parents) != 1 or parents[0].get('engine') != 'pytest':
            errors.append('required family account missing: ' + family)
            continue
        parent = parents[0]
        try:
            if parent['execution_state'] != 'started' or parent['accounting_state'] != 'complete':
                errors.append('family execution/accounting not complete: ' + family)
            reference = parent['family_report']
            base = 'suites/' + family
            if reference != base + '/family.json':
                raise ValueError('invalid family report reference')
            selection = read_object(base + '/selection.json')
            planned = [c for c in run['plan']['cases'] if c['id'] == family]
            if len(planned) != 1 or planned[0].get('items') != selection:
                raise ValueError('family selection differs from the collection fixed in the parent plan')
            if current and selection != expected['family_selections'][family]:
                raise ValueError('family authority or membership differs from independently collected expectation')
            family_result, ownership = read_object(reference), read_object(base + '/ownership.json')
            byte_reader = (lambda name:load_bytes(base + '/' + name)) if load_bytes is not None else None
            errors += [family + ': ' + e for e in validate_family(family_result, ownership, selection, byte_reader)]
            if current:
                if byte_reader is None:
                    raise ValueError('current family has no raw evidence byte reader')
                _family_raw(family_result, ownership, selection, byte_reader)
                for item in family_result['items']:
                    if 'outcome_contract' in item:
                        assessments.append(('nested', item['id'], outcomes.assess(item['outcome_contract'], item['outcome_account'], byte_reader)))
                status = ('complete' if family_result.get('explicit') else 'pass') if family_result['ok'] else 'fail'
                if parent.get('status') != status or parent.get('state') != 'completed':
                    raise ValueError('parent family status contradicts independently checked completion')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append('required family evidence missing or invalid: ' + family + ': ' + str(exc))
    if current:
        if run.get('outcomes') != outcomes.summarize(assessments):
            errors.append('run outcome summary differs from independently checked accounts')
        reported = run.get('observation_reports')
        def keyed(reports):
            return {(row['suite'], row['test_id']):row for row in reports}
        try:
            if (not isinstance(reported, list) or len(reported) != len(observation_reports)
                    or len(keyed(reported)) != len(reported) or keyed(reported) != keyed(observation_reports)):
                errors.append('run observation report account differs from required case reports')
        except (KeyError, TypeError):
            errors.append('invalid run observation report account')
    return errors
