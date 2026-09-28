"""Read the registered lifecycle claims from one envelope without deriving any.

The adapter normalizes wire spellings through tests/lib/lifecycle_contract.py
and reports what the reply says. It never computes an answer from raw facts and
calls no production code; tests/lib/lifecycle_oracle.py does the checking.

`read_lifecycle(envelope)` returns:

    {'reporting': 'reported' | 'not_reported' | 'no_worker' | 'no_runner_reply' | 'malformed',
     'schema_version': int | None,
     'record': the raw record or None,
     'questions': {name: {'state', 'answer'?, 'value'?, 'reason'?, 'issue'?, 'basis', 'recognized', 'raw'}},
     'steps': [{'index', 'step_id', 'slot', 'attempt_support', 'questions': {...}}],
     'issues': [record issues],
     'projections': {'process_disposition', 'termination_cause', 'stop_reason', 'disposition_integrity',
                     'disposition_issues', 'partial_steps', 'step_lifecycle': [...],
                     'step_limitations': [...], 'error'},
     'malformed': [reasons]}

`recognized` is False when a state, answer or reason spelling is not one this
contract knows; the raw value is retained. `not_reported` means the reply
predates the record or omits it; only the oracle decides whether that omission
is legal for the reply's version.
"""
from copy import deepcopy

import lifecycle_contract as C


def _claim(name, raw, malformed, where):
    if not isinstance(raw, dict):
        malformed.append(f'{where}: claim is not an object')
        return {'state': None, 'recognized': False, 'raw': raw, 'basis': []}
    q = C.question(name)
    basis = raw.get('basis', [])
    if not isinstance(basis, list) or any(not isinstance(token, str) for token in basis):
        malformed.append(f'{where}: basis must be an array of reference strings')
        basis = []
    claim = {'state': raw.get('state'), 'basis': basis, 'recognized': True,
             'raw': deepcopy(raw)}
    if claim['state'] not in C.CLAIM_STATES:
        malformed.append(f'{where}: claim state is not one of the four contract states')
        claim['recognized'] = False
        return claim
    if claim['state'] == 'supported':
        claim['answer'] = raw.get('answer')
        if 'value' in raw:
            claim['value'] = raw['value']
        if not isinstance(claim['answer'], str):
            malformed.append(f'{where}: supported claim without a string answer')
            claim['recognized'] = False
        elif claim['answer'] not in {a.value for a in q.answers}:
            claim['recognized'] = False
    elif claim['state'] in ('unresolved', 'inapplicable'):
        claim['reason'] = raw.get('reason')
        allowed = C.reasons(name) if claim['state'] == 'unresolved' else (q.inapplicable,)
        if not isinstance(claim['reason'], str):
            malformed.append(f'{where}: claim without a string reason')
            claim['recognized'] = False
        elif claim['reason'] not in allowed:
            claim['recognized'] = False
    else:  # conflicting
        claim['issue'] = raw.get('issue')
        if type(claim['issue']) is not int:
            malformed.append(f'{where}: conflicting claim without an issue index')
    return claim


def read_lifecycle(envelope):
    view = {'reporting': None, 'schema_version': None, 'record': None, 'questions': {}, 'steps': [],
            'issues': [], 'projections': {}, 'malformed': []}
    data = envelope.get('data') if isinstance(envelope, dict) else None
    runner = data.get('runner_result') if isinstance(data, dict) else None
    diagnostics = data.get('runner_sandbox_diagnostics') if isinstance(data, dict) else None
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    view['projections'] = {key: diagnostics.get(key) for key in C.DIAGNOSTICS_KEYS}
    view['projections'].update(error=None, partial_steps=None, step_lifecycle=[], step_limitations=[])
    if not isinstance(runner, dict):
        view['reporting'] = 'no_runner_reply'
        return view
    view['schema_version'] = runner.get('schema_version')
    view['projections']['error'] = runner.get('error')
    sub = runner.get('runner_subprocess')
    steps = runner.get('steps') if isinstance(runner.get('steps'), list) else []
    view['projections']['step_lifecycle'] = [
        ((s.get('attempt') or {}).get(C.STEP_LIFECYCLE_KEY) if isinstance(s, dict) else None) for s in steps]
    view['projections']['step_limitations'] = [
        [l for l in (((s.get('comparison') or {}).get('limitations') or []) if isinstance(s, dict) else [])
         if isinstance(l, str) and l.startswith('attempt:')] for s in steps]
    if not isinstance(sub, dict):
        view['reporting'] = 'no_worker'
        return view
    view['projections']['partial_steps'] = sub.get('partial_steps')
    record = sub.get(C.RECORD_KEY)
    if record is None:
        view['reporting'] = 'not_reported'
        return view
    view['record'] = deepcopy(record)
    malformed = view['malformed']
    if not isinstance(record, dict):
        malformed.append('record is not an object')
        view['reporting'] = 'malformed'
        return view
    questions = record.get('questions')
    if not isinstance(questions, dict):
        malformed.append('record.questions is not an object')
    else:
        for name in C.RUN_QUESTIONS:
            if name not in questions:
                malformed.append(f'record.questions lacks {name}')
                continue
            view['questions'][name] = _claim(name, questions[name], malformed, f'questions.{name}')
        for extra in sorted(set(questions) - set(C.RUN_QUESTIONS)):
            view['questions'][extra] = {'state': None, 'recognized': False, 'raw': deepcopy(questions[extra]),
                                        'basis': []}
    entries = record.get('steps')
    if not isinstance(entries, list):
        malformed.append('record.steps is not an array')
    else:
        for position, entry in enumerate(entries):
            if not isinstance(entry, dict):
                malformed.append(f'steps[{position}] is not an object')
                continue
            item = {'index': entry.get('index'), 'step_id': entry.get('step_id'), 'slot': entry.get('slot'),
                    'attempt_support': entry.get('attempt_support'), 'questions': {}}
            if type(item['index']) is not int or item['index'] != position:
                malformed.append(f'steps[{position}] carries index {item["index"]!r}')
            if not isinstance(item['step_id'], str) or not item['step_id']:
                malformed.append(f'steps[{position}] lacks a string step_id')
            if item['slot'] not in C.SLOT_STATES:
                malformed.append(f'steps[{position}] slot {item["slot"]!r} unrecognized')
            if item['attempt_support'] not in C.ATTEMPT_SUPPORT:
                malformed.append(f'steps[{position}] attempt_support {item["attempt_support"]!r} unrecognized')
            claims = entry.get('questions')
            if not isinstance(claims, dict):
                malformed.append(f'steps[{position}].questions is not an object')
            else:
                for name in C.STEP_QUESTIONS:
                    if name not in claims:
                        malformed.append(f'steps[{position}].questions lacks {name}')
                        continue
                    item['questions'][name] = _claim(name, claims[name], malformed, f'steps[{position}].{name}')
            view['steps'].append(item)
    issues = record.get('issues')
    if not isinstance(issues, list):
        malformed.append('record.issues is not an array')
    else:
        for position, issue in enumerate(issues):
            if not isinstance(issue, dict) or issue.get('kind') not in C.ISSUE_KINDS \
                    or not isinstance(issue.get('rule'), str) or issue['rule'] not in C.RULES \
                    or not isinstance(issue.get('observations'), list) or not issue['observations'] \
                    or any(not isinstance(token, str) for token in issue['observations']):
                malformed.append(f'issues[{position}] malformed')
            view['issues'].append(deepcopy(issue))
    view['reporting'] = 'malformed' if malformed else 'reported'
    return view


def summaries(view):
    """The per-step lifecycle summary values the reply projects, or None where absent."""
    return [(entry or {}).get('summary') if isinstance(entry, dict) else None
            for entry in view['projections'].get('step_lifecycle', [])]
