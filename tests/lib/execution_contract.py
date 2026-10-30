"""Source-bound expectations supplied by PW, independently of engine result fields."""
import json
from pathlib import Path

from pytest_support import digest, read, value_digest

PROFILE = 'pw-family-evidence-1'


def capture(root, cases):
    catalog_path = root / 'tests/catalog.json'
    source = dict(catalog=json.loads(catalog_path.read_text()), catalog_sha256=digest(catalog_path),
                  reader_sha256=digest(Path(__file__)))
    selected = [dict(id=c['id'], engine=c.get('engine', 'legacy')) for c in cases]
    contract = dict(profile=PROFILE, source=source, selected=selected,
                    required_families=[c['id'] for c in selected if c['engine'] == 'pytest'])
    contract['identity'] = value_digest(contract)
    return contract


def defaults(root):
    # Reuse the one catalog owner. This never collects or invokes pytest items.
    from types import SimpleNamespace
    from test_cli import catalog, select
    cases, suites = catalog(root)
    return capture(root, select(cases, suites, SimpleNamespace(case=[], suite=[], all=False)))


def validate_contract(contract):
    if contract.get('profile') != PROFILE:
        raise ValueError('unknown producer evidence contract')
    payload = {k:v for k,v in contract.items() if k != 'identity'}
    if value_digest(payload) != contract.get('identity'):
        raise ValueError('execution contract identity mismatch')
    if contract['required_families'] != [c['id'] for c in contract['selected'] if c['engine'] == 'pytest']:
        raise ValueError('required family declaration differs from independently selected engines')


def validate_family(family, ownership, selection):
    errors = []
    expected = [r['id'] for r in selection['items']]
    if family.get('manifest_digest') != value_digest(selection):
        errors.append('family manifest identity mismatch')
    items = family.get('items', [])
    if [r.get('id') for r in items] != expected or len(set(expected)) != len(expected) or not expected:
        errors.append('incomplete family item account')
    if (family.get('accounting_state') != 'complete' or family.get('ok') is not True or
            any(i.get('outcome') != 'passed' for i in items)):
        errors.append('family did not complete successfully')
    if ownership.get('closed') is not True or ownership.get('problems'):
        errors.append('ownership not closed')
    commands = ownership.get('commands')
    if not isinstance(commands, list):
        errors.append('ownership operation set missing')
    else:
        from pytest_resources import disposition
        if any(disposition(r) != 'closed' for r in commands):
            errors.append('ownership closure lacks settlement')
        ids = [r['operation_id'] for r in commands]
        if len(set(ids)) != len(ids) or sorted(ids) != sorted(family.get('operations', [])):
            errors.append('ownership operation set differs from family command receipts')
    return errors


def problems(run, expected, load):
    """load accepts bounded relative evidence names; expected is captured outside the result."""
    validate_contract(expected)
    errors = []
    if run.get('execution_contract') != expected:
        errors.append('missing or changed independently expected execution contract')
    for family in expected['required_families']:
        parents = [c for c in run.get('case_results', []) if c.get('id') == family]
        if len(parents) != 1 or parents[0].get('engine') != 'pytest':
            errors.append('required family account missing: ' + family)
            continue
        parent = parents[0]
        try:
            if parent['execution_state'] != 'started' or parent['accounting_state'] != 'complete':
                errors.append('family execution/accounting not complete: ' + family)
            reference = parent['family_report']
            # Derive roles from the checked family identity, not optional archive pointers.
            base = 'suites/' + family
            if reference != base + '/family.json':
                raise ValueError('invalid family report reference')
            errors += [family + ': ' + e for e in validate_family(load(reference),
                    load(base + '/ownership.json'), load(base + '/selection.json'))]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append('required family evidence missing or invalid: ' + family + ': ' + str(exc))
    return errors
