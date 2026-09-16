"""Bounded, recorded commands for the explicit release procedure. No retries."""
import json
from pathlib import Path
import shlex
import signal
import subprocess
import time
import os
import argparse
import tempfile


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def command(out, argv, *, timeout, env=None, cwd=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    argv = list(map(str, argv))
    record = dict(argv=argv, timeout_seconds=timeout, returncode=None,
                  timed_out=False, interrupted=False)
    save(out / 'command.json', record)
    print(f'==> {shlex.join(argv)}\n    evidence: {out}', flush=True)
    started = time.monotonic()
    try:
        with (out / 'stdout').open('wb') as stdout, (out / 'stderr').open('wb') as stderr:
            with subprocess.Popen(argv, stdout=stdout, stderr=stderr, env=env, cwd=cwd,
                                  start_new_session=True) as process:
                try:
                    record['returncode'] = process.wait(timeout=timeout)
                except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                    record['timed_out'] = isinstance(exc, subprocess.TimeoutExpired)
                    record['interrupted'] = isinstance(exc, KeyboardInterrupt)
                    # Give the test dispatcher a chance to finalize and stop its
                    # case groups. This also bounds a stuck Apple tool locally.
                    previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
                    try:
                        process.send_signal(signal.SIGINT)
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            pass
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        record['returncode'] = process.wait()
                    finally:
                        signal.signal(signal.SIGINT, previous)
                    raise RuntimeError(f'command {"timed out" if record["timed_out"] else "interrupted"}; '
                                       f'remote work may still be pending; see {out}') from exc
    except OSError as exc:
        record['error'] = str(exc)
        raise
    finally:
        record['elapsed_seconds'] = time.monotonic() - started
        save(out / 'command.json', record)
        for name in ('stdout', 'stderr'):
            path = out / name
            if path.exists() and path.stat().st_size:
                print(path.read_bytes().decode('utf-8', errors='replace'), end='', flush=True)
    if record['returncode'] != 0:
        raise RuntimeError(f'command exited {record["returncode"]}; see {out}')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('evidence_parent', type=Path)
    parser.add_argument('timeout_seconds', type=int)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.timeout_seconds <= 0 or not args.command or not args.evidence_parent.is_dir():
        parser.error('provide an existing evidence directory, a positive timeout, and a command')
    out = Path(tempfile.mkdtemp(prefix='release-step-', dir=args.evidence_parent.resolve()))
    try:
        command(out / 'command', args.command, timeout=args.timeout_seconds)
    except (OSError, RuntimeError, KeyboardInterrupt) as exc:
        parser.exit(1, f'STOP: {exc}\n')
