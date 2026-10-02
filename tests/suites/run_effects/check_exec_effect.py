"""An allowed exec helper's own file effect is real; a denied helper runs but cannot write.

Both runs use (deny default) plus the exec_baseline augment, so the helper
reaches main. The allowed run adds one file-write allow for the marker path.
The marker is observed outside PolicyWitness before the envelope is decoded.
"""
import json
from pathlib import Path
import secrets
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_capture import RunCapture  # noqa: E402
import effects  # noqa: E402


def specimen_for(name, helper, marker, allow_write):
    policy = '(version 1)\n(deny default)\n'
    if allow_write:
        policy += f'(allow file-write* (literal "{marker}"))\n'
    return {
        'schema_version': 1,
        'specimen_id': f'run_effects_exec_{name}',
        'policy': {'format': 'sbpl', 'sbpl_source': policy, 'augments': ['exec_baseline']},
        'probe_plan': [{
            'step_id': secrets.token_hex(8),
            'sandbox_check': {'operation': 'process-exec*',
                              'filter': {'kind': 'path', 'value': str(helper)}},
            'attempt': {'kind': 'exec', 'action': 'spawn', 'target': str(helper),
                        'args': ['--write', str(marker)]},
        }],
    }


def main():
    pw, out_arg, helper_arg = sys.argv[1:]
    out, helper = Path(out_arg).resolve(), Path(helper_arg).resolve()
    summary = {}
    # A supplied exec argument is capped at 127 bytes, so the marker lives in a
    # short temporary directory; its bytes are retained under the artifacts.
    scratch = Path(tempfile.mkdtemp(prefix='pw-effects-', dir='/private/tmp'))
    try:
        for name, allow_write in (('allowed', True), ('denied', False)):
            work = out / name
            work.mkdir()
            marker = scratch / f'{name}-{secrets.token_hex(4)}'
            before = effects.snapshot(marker)
            effects.record(before, work, 'before')
            effects.expect_absent(before)
            spec = specimen_for(name, helper, marker, allow_write)
            with RunCapture(pw, work / 'run', spec, cli_args=['--no-log-capture']) as run:
                rc = run.wait(timeout=30)
            after = effects.snapshot(marker)
            effects.record(after, work, 'after')
            try:
                if allow_write:
                    effects.expect_helper_marker(after)
                else:
                    effects.expect_absent(after)
            except AssertionError as exc:
                raise AssertionError(f'{name}: {exc}; {effects.describe_run(run)}') from None
            summarize_run(name, allow_write, run, rc, summary)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    (out / 'attempts.json').write_text(json.dumps(summary, indent=2) + '\n')


def summarize_run(name, allow_write, run, rc, summary):
    if True:
        assert rc == 0, f'{name}: PW exit={rc}; see {run.stdout_path}'
        envelope = run.load_json()
        assert envelope['result']['ok'] is True, name
        runner = envelope['data']['runner_result']
        assert runner['normalized_outcome'] == 'ok', (name, runner['normalized_outcome'])
        assert runner.get('test_overrides') is None, name
        augmentation = envelope['data']['specimen']['policy']['augmentation']
        assert augmentation['status'] == 'applied' and augmentation['applied'] == ['exec_baseline'], name
        assert len(runner['steps']) == 1, name
        attempt = runner['steps'][0]['attempt']
        # The helper ran in both cases; only the allowed one could write.
        assert attempt['child_pid'] > 0, (name, attempt)
        assert attempt['child_term_signal'] == 0, (name, attempt)
        if allow_write:
            assert attempt['outcome'] == 'ok' and attempt['child_exit_code'] == 0, attempt
        else:
            assert attempt['outcome'] == 'exec_failed' and attempt['child_exit_code'] == 3, attempt
            assert '--write' in attempt.get('stderr', ''), attempt
        summary[name] = {key: attempt.get(key) for key in
                         ('outcome', 'child_pid', 'child_exit_code', 'child_term_signal', 'stderr')}
        print(f'{name}: helper ran (pid {attempt["child_pid"]}); marker '
              f'{"written" if allow_write else "absent"} as expected', flush=True)


if __name__ == '__main__':
    main()
