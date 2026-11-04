"""Decide from an envelope whether the host witnessed its worker's exit.

Test-owned cleanup may remove staging a worker could still hold, such as a FIFO
the worker is blocked opening, only after the run's own record confirms the
worker is gone. The one positive witness in an envelope is
runner_subprocess.reaped == true with a valid worker PID: the host waited on
the identified child it spawned. A malformed subprocess is not a witness.

Every other shape lacks that witness and is retained. A client-synthesized
xpc_timeout reply and a lost reply carry no runner_result or subprocess record
although the request was already sent; the service's minimal reporting-failure
reply drops subprocess evidence by design; a subprocess record without a reap
says the worker may still run. Missing evidence is never read as worker
absence, and the reason names what is missing so the owner can recover by hand.
"""


def actor_exit_witness(runner):
    """The actor form: every actor that launched must carry a reaped subprocess
    with a valid PID; an actor the host never launched needs no reap. Missing
    actor records or an unreaped actor withhold the witness."""
    actors = runner.get('actors')
    if not isinstance(actors, list) or not actors:
        return False, 'actor-form reply without actor records; actor launches and exits unknown'
    reaped = []
    for actor in actors:
        if not isinstance(actor, dict):
            return False, 'malformed actor record; actor exit unknown'
        name = actor.get('actor_id')
        sub = actor.get('subprocess')
        launch = actor.get('launch')
        if sub is None:
            if launch is not None or actor.get('setup_status') not in ('not_launched', 'launch_refused', 'setup_timeout'):
                return False, f'actor {name!r} claims a launch without a subprocess record; its exit is unknown'
            continue
        if not isinstance(sub, dict):
            return False, f'malformed subprocess record for actor {name!r}; its exit is unknown'
        pid = sub.get('pid')
        if type(pid) is not int or pid <= 0:
            return False, f'no valid pid for actor {name!r} ({pid!r}); its exit is unknown'
        if sub.get('reaped') is not True:
            return False, f'actor {name!r} pid {pid} not reaped (reaped={sub.get("reaped")!r}); it may still run'
        reaped.append(f'{name}={pid}')
    if not reaped:
        return True, 'no actor was launched'
    return True, 'host reaped every launched actor: ' + ', '.join(reaped)


def worker_exit_witness(envelope):
    """Return (witnessed, reason); witnessed is True only on a confirmed reap
    of the worker, or of every launched actor in the actor form."""
    if not isinstance(envelope, dict):
        return False, 'no decoded envelope; worker spawn and exit unknown'
    data = envelope.get('data')
    runner = data.get('runner_result') if isinstance(data, dict) else None
    if not isinstance(runner, dict):
        return False, 'no runner_result (reply lost or never produced); worker spawn and exit unknown'
    if runner.get('execution_form') == 'actors':
        return actor_exit_witness(runner)
    sub = runner.get('runner_subprocess')
    if not isinstance(sub, dict):
        outcome = runner.get('normalized_outcome')
        return False, (f'no runner_subprocess record beside normalized_outcome {outcome!r}; '
                       'worker spawn and exit unknown')
    pid = sub.get('pid')
    if type(pid) is not int or pid <= 0:
        return False, f'no valid worker pid in subprocess record ({pid!r}); worker exit unknown'
    if sub.get('reaped') is True:
        return True, f'host reaped worker pid {pid}'
    return False, f'worker pid {pid} not reaped (reaped={sub.get("reaped")!r}); it may still run'
