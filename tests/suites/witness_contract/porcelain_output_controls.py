"""Bounded serial public-output interruption controls for public JSON presentation.

The specimen only opens /etc/hosts for reading. No worker-created mutable
resource needs cleanup after the intentionally incomplete public documents.
Timing and sizes describe these executions; they do not compare performance.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import build_context
import consumer
import porcelain
from run_capture import RunCapture

WAIT_SECONDS = 120
CLI_ARGS = ('--timeout-ms', '60000')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def specimen():
    steps = [dict(step_id=f'r{i:03d}',
                  sandbox_check=dict(operation='file-read-data', filter=dict(kind='path', value='/etc/hosts')),
                  attempt=dict(kind='file', action='open_read', target='/etc/hosts')) for i in range(256)]
    return dict(contract=build_context.candidate_contract(), specimen_id='porcelain_output_dense_read',
                policy=dict(format='sbpl', sbpl_source='(version 1) (allow default)'),
                phases=[dict(phase_id=f'p{i}', actions=steps[i * 32:(i + 1) * 32]) for i in range(8)])


def complete(pw, out, request):
    before = Path('/etc/hosts').read_bytes()
    save(out / 'read-target-before.json', dict(path='/etc/hosts', bytes=len(before), sha256=digest(before)))
    with RunCapture(pw, out / 'complete', request, cli_args=CLI_ARGS) as run:
        rc = run.wait(timeout=WAIT_SECONDS)
        require(rc == 0, f'complete positive CLI failed: {rc}; see {run.stderr_path}')
        document = run.load_json()
        elapsed = run.elapsed_seconds
    after = Path('/etc/hosts').read_bytes()
    save(out / 'read-target-after.json', dict(path='/etc/hosts', bytes=len(after), sha256=digest(after)))
    require(before == after, 'independently read target changed during the positive run')
    errors = consumer.validate(document, build_context.candidate_contract())
    save(out / 'complete/consumer.json', dict(errors=errors))
    require(not errors, f'independent consumer rejected complete reply: {errors}')
    require(document['result']['ok'] is True, 'positive public result is not successful')
    runner = document['data']['runner_result']
    require(runner['normalized_outcome'] == 'finished', 'positive worker did not finish')
    require(len(runner['phases']) == 8 and len(runner['steps']) == 256, 'dense phases/actions missing')
    for index, step in enumerate(runner['steps']):
        require(step['step_id'] == f'r{index:03d}', 'action order changed')
        require(step['sandbox_check']['outcome'] == 'allow', 'positive query lacks allow observation')
        require(step['attempt']['rc'] == 0 and step['attempt'].get('observed_path'),
                'positive open_read lacks native success and path observation')
        require(step['comparison']['order'] == 'query_first', 'dense query order unestablished')
    require(runner['runner_subprocess']['reaped'] is True, 'positive worker reap not observed')
    client = document['data']['runner_client']
    require(client['transport_admission'] == 'accepted', 'client capture not admitted')
    host = client['transport']['runner_reply']
    raw = base64.b64decode(host['data_base64'], validate=True)
    require(not host['truncated'] and host['bytes_received'] == host['bytes_retained'] == len(raw),
            'positive host receipt incomplete')
    require(porcelain.decode(raw, 'reply') == runner, 'host bytes differ from public typed reply')
    (out / 'complete/host-reply.pwp').write_bytes(raw)
    stdout = (out / 'complete/run.json').read_bytes()
    # The fixed dense result must be materially larger than either consumed
    # prefix. Nonzero exit after the close supplies the actual write-failure
    # observation; this number is not a portable kernel pipe-capacity claim.
    require(len(stdout) > 262144, 'positive output too small for the declared dense interruption control')
    require(client['stdout_bytes_received'] == client['stdout_bytes_retained']
            and client['stdout_truncated'] is False, 'positive binary client capture incomplete')
    result = dict(workload='eight_phases_256_open_read_queries', cli_exit_code=rc,
                  elapsed_seconds=elapsed, elapsed_scope='wall duration through observed CLI exit; one execution',
                  public_stdout_bytes=len(stdout), public_stdout_sha256=digest(stdout),
                  host_bytes_received=host['bytes_received'], host_bytes_retained=host['bytes_retained'],
                  host_artifact_sha256=digest(raw),
                  capture_bytes_received=client['stdout_bytes_received'],
                  capture_bytes_retained=client['stdout_bytes_retained'],
                  capture_byte_source='controller counts of complete collected client stdout; not reconstructed bytes',
                  performance_claim='descriptive only; no baseline, matching, peak-memory or superiority claim')
    save(out / 'complete/measurements.json', result)
    return result


def interrupted(pw, out, request, prefix_bytes):
    directory = out / f'close-after-{prefix_bytes}'
    directory.mkdir()
    request_path = directory / 'specimen.json'
    save(request_path, request)
    argv = [str(pw), 'run', str(request_path), *CLI_ARGS]
    state = dict(argv=argv, requested_prefix_bytes=prefix_bytes, state='prepared',
                 started_unix_ns=None, elapsed_seconds=None, pid=None, returncode=None,
                 exit_code=None, term_signal=None, prefix_bytes=0, pipe_closed=False,
                 timeout_seconds=WAIT_SECONDS, timed_out=False, cleanup_kill_requested=False,
                 complete_document=False, error=None)
    save(directory / 'capture.json', state)
    prefix = bytearray()
    process = None
    started = time.monotonic()
    deadline = started + WAIT_SECONDS
    try:
        with (directory / 'stderr').open('xb') as stderr:
            state['started_unix_ns'] = time.time_ns()
            process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=stderr)
            state.update(pid=process.pid, state='reading_prefix')
            save(directory / 'capture.json', state)
            os.set_blocking(process.stdout.fileno(), False)
            with selectors.DefaultSelector() as ready:
                ready.register(process.stdout, selectors.EVENT_READ)
                while len(prefix) < prefix_bytes:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        state['timed_out'] = True
                        raise TimeoutError('no fixed public prefix before harness deadline')
                    if not ready.select(min(remaining, 1.0)):
                        continue
                    block = os.read(process.stdout.fileno(), prefix_bytes - len(prefix))
                    if not block:
                        raise AssertionError('CLI ended before the requested public prefix')
                    prefix.extend(block)
            # Close the real read endpoint at exactly the declared boundary.
            process.stdout.close()
            state.update(pipe_closed=True, state='waiting_for_exit', prefix_bytes=len(prefix))
            (directory / 'stdout.partial').write_bytes(prefix)
            save(directory / 'capture.json', state)
            try:
                rc = process.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                state['timed_out'] = True
                raise
            state.update(state='exited', returncode=rc, exit_code=rc if rc >= 0 else None,
                         term_signal=-rc if rc < 0 else None)
            require(rc != 0, 'CLI reported success after its public output pipe was closed')
            try:
                json.loads(prefix)
            except (ValueError, UnicodeDecodeError) as error:
                state['json_error'] = str(error)
            else:
                state['complete_document'] = True
                raise AssertionError('closed-pipe prefix unexpectedly forms a complete JSON document')
    except BaseException as error:
        state['error'] = str(error)
        raise
    finally:
        if process is not None:
            if process.stdout is not None and not process.stdout.closed:
                process.stdout.close()
            if process.poll() is None:
                state['cleanup_kill_requested'] = True
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    state['cleanup_error'] = 'owned CLI did not settle after cleanup kill'
            state['observed_returncode'] = process.poll()
        state['elapsed_seconds'] = time.monotonic() - started
        state['prefix_bytes'] = len(prefix)
        state['prefix_sha256'] = digest(prefix)
        (directory / 'stdout.partial').write_bytes(prefix)
        save(directory / 'capture.json', state)
    return state


def main():
    pw, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    request = specimen()
    (out / 'driver-source.py').write_bytes(Path(__file__).read_bytes())
    save(out / 'source.json', dict(script=str(Path(__file__).relative_to(ROOT)),
                                 script_sha256=digest(Path(__file__).read_bytes()),
                                 executable=str(pw), executable_sha256=digest(pw.read_bytes()),
                                 invocation_order=['complete', 'close-after-128', 'close-after-4096'],
                                 mutable_worker_resources=False))
    measurements = complete(pw, out, request)
    failures = [interrupted(pw, out, request, size) for size in (128, 4096)]
    require(all(not row['timed_out'] and not row['cleanup_kill_requested'] for row in failures),
            'harness timeout/kill cannot establish public output failure behavior')
    save(out / 'output-controls.json', dict(status='passed', complete=measurements,
          interrupted=failures, claim='actual closed public pipe yields nonzero CLI exit and an incomplete retained document',
          limits=['No complete envelope or worker disposition is inferred from either partial document.',
                  'Interrupted execution observes CLI output behavior, not XPC copying or independent host exit.',
                  'Durations and sizes are descriptive observations of one complete run.']))
    print('complete dense read-only public run validated; actual pipe closure at 128 and 4096 bytes '
          'returned nonzero with incomplete documents')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: porcelain_output_controls.py POLICY_WITNESS ARTIFACTS')
    main()
