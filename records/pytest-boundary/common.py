"""Candidate durability and terminal accounting; no collection or execution loop."""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(os.environ['BOUNDARY_ROOT']).resolve()
sys.path.insert(0, str(ROOT / 'tests/lib'))
import checkout_lock
import retention


def write(path, value):
    retention.atomic_json(Path(path), value)


def append(path, value):
    data = (json.dumps(value, sort_keys=True) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        if os.write(fd, data) != len(data):
            raise OSError('short journal write')
        os.fsync(fd)
    finally:
        os.close(fd)


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def account(selection, events, engine_code, resources):
    """Preserve pytest phases, never promote absent/failed phases to a pass."""
    errors, results = [], []
    if not selection or len(set(selection)) != len(selection):
        errors.append('invalid_selection')
    if any(e.get('nodeid') not in selection for e in events if 'nodeid' in e):
        errors.append('unexpected_item')
    terminal = [e for e in events if e.get('kind') == 'session_finish']
    if len(terminal) != 1 or terminal[0].get('exitstatus') != engine_code:
        errors.append('missing_or_mismatched_session_finish')
    if engine_code != 0:
        errors.append('engine_unsuccessful')
    for node in selection:
        observed = [e for e in events if e.get('nodeid') == node]
        starts = [e for e in observed if e.get('kind') == 'start']
        reports = [e for e in observed if e.get('kind') == 'report']
        phases = [e.get('when') for e in reports]
        valid = len(starts) == 1 and observed and observed[0].get('kind') == 'start'
        valid = valid and len(observed) == 1 + len(reports)
        valid = valid and phases in (['setup', 'call', 'teardown'], ['setup', 'teardown'])
        valid = valid and all(e.get('outcome') in ('passed', 'failed', 'skipped') for e in reports)
        if phases == ['setup', 'teardown'] and reports[0].get('outcome') == 'passed':
            valid = False
        if phases == ['setup', 'call', 'teardown'] and reports[0].get('outcome') != 'passed':
            valid = False
        passed = bool(valid and all(e['outcome'] == 'passed' and not e.get('wasxfail') for e in reports))
        if not valid:
            errors.append('incomplete_or_invalid_phases:' + node)
        results.append(dict(id=node, state='completed' if valid else 'unrun',
                            status='pass' if passed else 'fail', started=bool(starts), reports=reports))
    if any(r.get('state') != 'closed' for r in resources):
        errors.append('pending_resources')
    return results, errors


def finish(out, engine_code, *, recovery=False):
    owner, plan = read(out / 'owner.json'), read(out / 'plan.json')
    parse_errors = []
    try:
        events = rows(out / 'reports.jsonl')
    except (ValueError, OSError) as exc:
        events = []
        parse_errors.append('unreadable_journal:' + str(exc))
    resources = [read(p) for p in sorted((out / 'resources').glob('*/record.json'))]
    results, errors = account([c['id'] for c in plan['cases']], events, engine_code, resources)
    errors += parse_errors
    end = time.time_ns() // 1_000_000
    ok = not errors and all(c['status'] == 'pass' for c in results)
    summary = dict(schema_version=1, terminal=True, run_id=owner['run_id'],
                   started_at_unix_ms=owner['started_at_unix_ms'], finished_at_unix_ms=end,
                   duration_ms=end-owner['started_at_unix_ms'], configuration=plan['configuration'],
                   plan=plan, case_results=results, ok=ok, harness_errors=errors,
                   completion=dict(selected=len(results), completed=sum(c['state']=='completed' for c in results),
                                   skipped=0, unrun=sum(c['state']=='unrun' for c in results)),
                   engine_returncode=engine_code, recovered=recovery, resources=resources)
    write(out / 'run.json', summary)
    return 0 if ok else 1
