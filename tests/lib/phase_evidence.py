"""Collection/validator consistency, independent of the production encoder."""


def collection_problem(phase):
    ordering = phase.get('ordering')
    disposition = ordering.get('validator_disposition') if isinstance(ordering, dict) else None
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
    spawn = phase.get('validator_spawn_failure')
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
