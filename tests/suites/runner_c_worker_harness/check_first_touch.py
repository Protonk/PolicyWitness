"""First-touch publication after application: condition, publication, sensitivity and shipped-worker oracles.

Reads the harness envelopes the run script left under the artifacts directory.
Four oracles are kept apart: `condition` (the probe page was backed by no
process through application, judged from the host's residency samples before
spawn, at the ready byte, and when the worker's applied word was first seen
before release), `application` and `enforcement` (the worker's own application
record beside the kernel's denial of its attempt), and `publication` (the host
read the pattern back through its own mapping and the worker exited 0).
Residency after reap corroborates; it never stands in for the read-back. The
two pre-touched controls must publish and still be rejected by the unchanged
`condition` oracle.

Every unit's verdicts are computed and written to first-touch-report.json
before any assertion, so a failing run retains each oracle's answer; the first
line of output then names the failing unit and oracle.
"""
import json
from pathlib import Path
import sys

PERMISSION_ERRNOS = (1, 13)
FIXTURE_UNITS = ('first_touch_v1', 'first_touch_v2', 'first_touch_v3')
CONTROL_UNITS = ('host_pretouched', 'worker_pretouched')
SHIPPED_UNITS = ('shipped_v1', 'shipped_v2', 'shipped_v3')
CONDITION_SAMPLES = ('before_spawn', 'at_ready', 'at_applied')


def load(artifacts, name):
    return json.loads((artifacts / f'{name}.json').read_text(encoding='utf-8'))


def condition(r):
    """Reasons the first-touch condition is not established; empty means established."""
    ft = r['first_touch']
    reasons = []
    if not r['ready_byte_received']:
        reasons.append('no ready byte: the pre-apply boundary was not observed')
    if not ft['probe_page_inside_capture_bytes']:
        reasons.append('probe page outside the capture bytes')
    if not ft['skip_touch'] or ft['host_touched_probe']:
        reasons.append('host touched the probe page')
    for key in CONDITION_SAMPLES:
        sample = ft['samples'][key]
        if sample['rc'] == -2:
            reasons.append(f'{key}: not sampled' + (' (applied not seen before release)' if key == 'at_applied' else ''))
        elif sample['rc'] != 0:
            reasons.append(f"{key}: mincore failed errno {sample['errno']}")
        elif sample['probe_resident']:
            reasons.append(f'{key}: probe page already resident')
    return reasons


def application(r):
    """The worker's own record: successful apply and terminal publication."""
    return bool(r['applied']) and r['apply_rc'] == 0 and bool(r['done'])


def enforcement(r):
    """Native corroboration independent of the worker's word: the kernel denied the slot's open."""
    slot = r['slots'][0]
    return slot['completed'] == 1 and slot['rc'] == 1 and slot['errno'] in PERMISSION_ERRNOS


def publication(r):
    """Decisive: the pattern read back through the host mapping, and a worker that exited 0."""
    ft = r['first_touch']
    return bool(ft['value_match']) and r['exit_code'] == 0 and r['term_signal'] is None and not r['sent_sigkill']


def corroboration(r):
    """Residency of the probe page after reap; None when the sample is unavailable."""
    after = r['first_touch']['samples']['after_reap']
    return after['probe_resident'] if after['rc'] == 0 else None


def verdict(r, stderr):
    ft = r['first_touch']
    samples = ft['samples']
    ready, after = samples['at_ready'], samples['after_reap']
    return {
        'oracles': {'condition_reasons': condition(r), 'application': application(r), 'enforcement': enforcement(r),
                    'publication': publication(r), 'corroboration_after_reap': corroboration(r)},
        'exit_code': r['exit_code'], 'term_signal': r['term_signal'], 'sent_sigkill': r['sent_sigkill'],
        'ready_byte_received': r['ready_byte_received'], 'applied': r['applied'], 'apply_rc': r['apply_rc'],
        'done': r['done'], 'slot0': r['slots'][0], 'value': ft['value'], 'pattern': ft['pattern'],
        'minflt': ft['worker_minflt'], 'worker_pid': r['worker_pid'],
        'probe_resident': {k: v['probe_resident'] for k, v in samples.items()},
        'resident_pages': {k: v['resident_pages'] for k, v in samples.items()},
        'sample_rc': {k: v['rc'] for k, v in samples.items()},
        'new_pages_after_ready': (sorted(set(after['resident_pages']) - set(ready['resident_pages']))
                                  if ready['rc'] == 0 and after['rc'] == 0 else None),
        'worker_stderr': stderr.strip()[:2000],
    }


def check(verdicts):
    for name in FIXTURE_UNITS:
        v = verdicts[name]
        o = v['oracles']
        assert not o['condition_reasons'], f'{name} condition: not established: {o["condition_reasons"]}'
        assert o['application'], f"{name} application: the worker did not record a successful apply and done: " \
                                 f"applied {v['applied']} apply_rc {v['apply_rc']} done {v['done']}"
        assert o['enforcement'], f"{name} enforcement: slot 0 does not show the kernel denying the open: {v['slot0']}"
        assert o['publication'], (f"{name} publication: not established: value {v['value']} against pattern "
                                  f"{v['pattern']}, exit {v['exit_code']}, signal {v['term_signal']}, "
                                  f"sigkill {v['sent_sigkill']}")
        assert o['corroboration_after_reap'] is True, (
            f"{name} corroboration: residency after reap did not show the probe page although the value read "
            f"back matched (sample rc {v['sample_rc']['after_reap']})")

    # Sensitivity A: the host backed the probe page before spawn. Publication is
    # unchanged; the before-spawn sample rejects the condition.
    v = verdicts['host_pretouched']
    o = v['oracles']
    assert o['application'] and o['enforcement'] and o['publication'], \
        f'host_pretouched control: must still publish: {o}'
    expected = {'host touched the probe page'} | {f'{k}: probe page already resident' for k in CONDITION_SAMPLES}
    assert set(o['condition_reasons']) == expected, \
        f"host_pretouched control: not rejected as expected by the condition oracle: {o['condition_reasons']}"

    # Sensitivity B: the worker backed the probe page before application through
    # a private mapping; the host never touched it. Only the worker-side samples
    # can reject this, and only while mincore reports residency in the shared
    # object rather than translations in the sampling process.
    v = verdicts['worker_pretouched']
    o = v['oracles']
    assert 'first_touch_pretouch: touched offset' in v['worker_stderr'], \
        f"worker_pretouched control: did not record touching the probe page before main: {v['worker_stderr']!r}"
    assert o['application'] and o['enforcement'] and o['publication'], \
        f'worker_pretouched control: must still publish: {o}'
    assert v['sample_rc']['before_spawn'] == 0 and v['probe_resident']['before_spawn'] is False, \
        f"worker_pretouched control: the host must not have backed the probe page: {v['probe_resident']}"
    assert o['condition_reasons'] == ['at_ready: probe page already resident',
                                      'at_applied: probe page already resident'], (
        'worker_pretouched control: must be rejected by the ready-byte and applied samples alone; a pass here '
        f"would mean the residency sample no longer sees pages another process backed: {o['condition_reasons']}")

    # Shipped worker under the same skip-touch rows: in these executions the
    # probe page stayed unbacked and the pages resident at the ready byte were
    # the pages resident at done and after reap. One slot, three policies; an
    # observation of these runs, not an invariant over every plan.
    for name in SHIPPED_UNITS:
        v = verdicts[name]
        o = v['oracles']
        assert o['application'] and o['enforcement'] and v['exit_code'] == 0 and not v['sent_sigkill'], \
            f'{name} shipped: did not apply, get denied and exit 0: {o} exit {v["exit_code"]}'
        assert not o['condition_reasons'], f"{name} shipped: probe page not unbacked through application: {o['condition_reasons']}"
        assert v['value'] == '0' * 16 and not o['publication'], \
            f"{name} shipped: the shipped worker has no seam; the probe word must stay zero: {v['value']}"
        rc = v['sample_rc']
        assert all(rc[k] == 0 for k in ('at_ready', 'at_done', 'after_reap')), f'{name} shipped: residency samples unavailable: {rc}'
        pages = v['resident_pages']
        assert pages['at_ready'] == pages['at_done'] == pages['after_reap'], (
            f"{name} shipped: pages resident changed between the ready byte and done/reap: "
            f"{pages['at_ready']} -> {pages['at_done']} -> {pages['after_reap']}")
        assert v['probe_resident']['after_reap'] is False, f"{name} shipped: probe page became resident: {pages}"


def main():
    artifacts = Path(sys.argv[1])
    verdicts = {}
    for name in FIXTURE_UNITS + CONTROL_UNITS + SHIPPED_UNITS:
        stderr_path = artifacts / f'{name}.stderr'
        stderr = stderr_path.read_text(encoding='utf-8', errors='replace') if stderr_path.is_file() else ''
        verdicts[name] = verdict(load(artifacts, name), stderr)
    (artifacts / 'first-touch-report.json').write_text(json.dumps(verdicts, indent=2, sort_keys=True) + '\n')
    try:
        check(verdicts)
    except AssertionError as error:
        print(f'FAIL {error}')
        return 1
    shipped_pages = verdicts['shipped_v1']['resident_pages']['at_ready']
    print(f"first-touch store read back under deny-default v1/v2/v3 from a page unbacked at the ready byte and at "
          f"the worker's applied word before release; host- and worker-pretouched controls published but were "
          f"rejected; shipped worker published only into pages {shipped_pages} resident at the ready byte")
    return 0


if __name__ == '__main__':
    sys.exit(main())
