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


def worker_exit_witness(envelope):
    """Return (witnessed, reason); witnessed is True only on a confirmed reap."""
    if not isinstance(envelope, dict):
        return False, 'no decoded envelope; worker spawn and exit unknown'
    data = envelope.get('data')
    runner = data.get('runner_result') if isinstance(data, dict) else None
    if not isinstance(runner, dict):
        return False, 'no runner_result (reply lost or never produced); worker spawn and exit unknown'
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
