"""Collection/validator consistency, independent of the production encoder."""


def collection_problem(phase):
    ordering = phase.get('ordering')
    if ordering is not None and not isinstance(ordering, dict):
        return 'phase collection evidence has an invalid type'
    disposition = ordering.get('validator_disposition') if isinstance(ordering, dict) else None
    if disposition is not None and not isinstance(disposition, str):
        return 'phase collection evidence has an invalid type'
    spawn = phase.get('validator_spawn_failure')
    if spawn is not None and not isinstance(spawn, dict):
        return 'phase collection evidence has an invalid type'
    status = phase.get('collection_status')
    allowed = {
        'not_reached': (None, 'not_invoked'),
        'not_needed': ('not_needed',),
        'collected': ('not_spawned', 'reaped', 'unconfirmed'),
        'budget_exhausted': ('not_spawned',),
        # Clock failure can precede planning or follow a nonempty query plan.
        'clock_unavailable': ('not_needed', 'not_spawned'),
    }
    validator = phase.get('validator_subprocess')
    if not isinstance(status, str) or disposition not in allowed.get(status, ()) or (
            status != 'collected' and (validator is not None or spawn is not None)):
        return 'phase collection status contradicts validator evidence'
    if status == 'collected':
        if disposition == 'not_spawned':
            valid = validator is None  # Local driver setup can fail before posix_spawn.
        else:
            valid = isinstance(validator, dict) and spawn is None and \
                validator.get('reaped') is (disposition == 'reaped')
        if not valid:
            return 'phase collection status contradicts validator evidence'
    return None


def association_issues(records, eligible):
    """The issues a record list implies for an eligible query plan; mirrors the host's join."""
    groups = {}
    for record in records:
        if isinstance(record, dict) and isinstance(record.get('step_id'), str):
            groups.setdefault(record['step_id'], []).append(record)
    wanted = [step.get('step_id') for step in eligible]
    out = []
    for step in eligible:
        sid = step.get('step_id')
        matches = groups.get(sid, [])
        if len(matches) == 1:
            record, query = matches[0], step.get('sandbox_check') or {}
            prediction = record.get('outcome') in ('allow', 'deny')
            filter_type = str(query.get('filter_kind')).upper()
            filter_value = None if query.get('filter_kind') == 'none' else query.get('filter_value')
            mismatch = ((prediction or record.get('operation') is not None) and record.get('operation') != query.get('operation')) or \
                       ((prediction or record.get('filter_type') is not None) and record.get('filter_type') != filter_type) or \
                       ((prediction or record.get('filter_value') is not None) and record.get('filter_value') != filter_value)
            if mismatch:
                out.append(('query_mismatch', sid, 1))
        else:
            out.append(('missing_id' if not matches else 'duplicate_id', sid, len(matches)))
    for sid in sorted(groups):
        if sid not in wanted:
            out.append(('unexpected_id', sid, len(groups[sid])))
    unassociated = sum(1 for record in records if isinstance(record, dict) and record.get('step_id') is None)
    if unassociated:
        out.append(('unassociated', None, unassociated))
    return sorted(out, key=lambda item: (item[0], item[1] or '', item[2]))


def ownership_problem(runner, phase):
    """A phase's validator collection must name this phase, carry exactly its eligible
    query plan and the association issues its records imply. The plan is read from
    the retained per-step query decisions; PID uniqueness is not a rule."""
    block = phase.get('validator_subprocess')
    if not isinstance(block, dict):
        return None
    if not isinstance(block.get('phase_id'), str) or type(block.get('ordinal')) is not int:
        return 'validator collection lacks phase ownership'
    if block['phase_id'] != phase.get('phase_id') or block['ordinal'] != phase.get('ordinal'):
        return 'validator collection names another phase'
    steps = runner.get('steps')
    steps = [s for s in steps if isinstance(s, dict) and s.get('phase_id') == phase.get('phase_id')] if isinstance(steps, list) else []
    if any(not isinstance(s.get('sandbox_check'), dict) or not isinstance(s.get('step_id'), str) for s in steps):
        return 'validator query plan has an invalid type'
    eligible = [s for s in steps if s['sandbox_check'].get('missing_reason') != 'query_not_requested']
    expected = block.get('expected_step_ids')
    if not isinstance(expected, list):
        return 'validator collection lacks its expected plan'
    # Order is the step-order and partition checks' question; ownership asks
    # whether the plan names exactly this phase's eligible queries.
    if any(not isinstance(sid, str) for sid in expected):
        return 'validator query plan has an invalid type'
    if len(set(expected)) != len(expected) or set(expected) != {s['step_id'] for s in eligible}:
        return "validator expected IDs disagree with the phase's eligible query plan"
    records, issues = block.get('records'), block.get('association_issues')
    if not isinstance(records, list) or not isinstance(issues, list):
        return 'validator collection lacks records or association issues'
    if any(not isinstance(r, dict) or (r.get('step_id') is not None and not isinstance(r.get('step_id'), str)) for r in records) or any(
            not isinstance(i, dict) or not isinstance(i.get('kind'), str)
            or (i.get('step_id') is not None and not isinstance(i.get('step_id'), str))
            or type(i.get('count')) is not int or not 0 <= i['count'] <= (1 << 63) - 1 for i in issues):
        return 'validator association evidence has an invalid type'
    reported = sorted(((i['kind'], i.get('step_id'), i['count']) for i in issues),
                      key=lambda item: (item[0], item[1] or '', item[2]))
    if reported != association_issues(records, eligible):
        return 'validator association issues disagree with its records'
    return None
