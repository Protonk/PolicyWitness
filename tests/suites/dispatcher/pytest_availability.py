"""Pytest equipment that changes between plan collection and execution.

The dispatcher decides availability when it collects the plan and again when it
checks prerequisites. These controls move a verified package target between the
two decisions, the same final rename provisioning performs, and require a terminal
account either way.
"""
import os
from pathlib import Path
import shutil

import checkout_lock
from pytest_support import read, write

ANCHOR = '    from execution_contract import capture'


def require(value, message):
    if not value:
        raise AssertionError(message)


def transition(integration, name, source, destination):
    root = integration.fixture(name)
    if source == '.tmp/pytest-staged':
        (root / '.tmp/pytest').rename(root / source)
    cli = root / 'tests/lib/test_cli.py'
    text = cli.read_text()
    require(text.count(ANCHOR) == 1, 'collection/execution boundary anchor')
    # Runs after the plan is collected and before the checkout lock is taken.
    move = (f"    if (root / {source!r}).exists():\n"
            f"        (root / {source!r}).rename(root / {destination!r})\n")
    cli.write_text(text.replace(ANCHOR, move + ANCHOR))
    return root


def account(integration, root, out, run, F):
    require(run is not None, 'no terminal run record')
    parent, later = run['case_results']
    require(parent['id'] == F and parent['state'] == 'unrun' and parent['status'] is None,
            'family result not an unrun account')
    require(parent['execution_state'] == 'not_started' and parent['accounting_state'] == 'unavailable',
            'family state not not_started/unavailable')
    require(later['id'] == 'sentinel/later' and later['status'] == 'pass', 'independent legacy case did not run')
    require(run['ok'] is False and run['completion'] == dict(completed=1, skipped=0, unrun=1, selected=2),
            'run accounting incomplete or credited')
    require(any(e['code'] == 'not_run' and parent['reason'] in e['message'] for e in run['harness_errors']),
            'unrun family has no diagnostic')
    require(not (root / 'tests/out/pytest-owners').exists(), 'unreleased family acquired command equipment')
    with checkout_lock.preview(root) as held:
        require(not held, 'a collected engine still holds the checkout')
    return parent


def provisioned_after_collection(integration):
    from pytest_integration import F
    root = transition(integration, 'availability-provisioned', '.tmp/pytest-staged', '.tmp/pytest')
    out, run = integration.run(root, expected=1)
    require((root / '.tmp/pytest').is_dir() and not (root / '.tmp/pytest-staged').exists(),
            'provisioning stimulus did not take effect between the checks')
    parent = account(integration, root, out, run, F)
    planned = next(c for c in read(out / 'plan.json')['cases'] if c['id'] == F)
    require('items' not in planned and planned.get('engine_unavailable'), 'plan does not record the uncollected family')
    require(planned['engine_unavailable'] in parent['reason'], 'outcome does not name the collection-time unavailability')
    # Later independent execution may use the now-provisioned engine.
    after, later = integration.run(root, 'after', args=('--case', F))
    require(later['ok'] and later['case_results'][0]['status'] == 'pass', 'provisioned engine unusable by a later run')
    return dict(output=str(out), later=str(after), reason=parent['reason'])


def removed_after_collection(integration):
    from pytest_integration import F
    root = transition(integration, 'availability-removed', '.tmp/pytest', '.tmp/pytest-removed')
    out, run = integration.run(root, expected=1)
    require((root / '.tmp/pytest-removed').is_dir() and not (root / '.tmp/pytest').exists(),
            'removal stimulus did not take effect between the checks')
    parent = account(integration, root, out, run, F)
    planned = next(c for c in read(out / 'plan.json')['cases'] if c['id'] == F)
    require(planned.get('items'), 'collected selection missing from the plan')
    require('pytest' in parent['reason'], 'outcome does not name the unavailable engine equipment')
    return dict(output=str(out), reason=parent['reason'])


CONTROLS = (provisioned_after_collection, removed_after_collection)


def exercise(control, integration):
    failures = []
    for check in CONTROLS:
        try:
            facts = check(integration)
        except Exception as exc:
            error = str(exc) if isinstance(exc, AssertionError) else f'{type(exc).__name__}: {exc}'
            failures.append(dict(control=check.__name__, error=error))
            print('FAILED:', check.__name__ + ':', error, flush=True)
        else:
            control.note(check.__name__, **facts)
    write(control.out / 'availability-controls.json', dict(controls=[c.__name__ for c in CONTROLS], failures=failures))
    if failures:
        raise AssertionError('availability controls failed: ' + ', '.join(f['control'] for f in failures))
