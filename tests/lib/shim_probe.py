"""Contained developer-tool probes; see tests/AGENTS.md for the safe CLI launch.

prepare() gates a profile once and returns a sandbox-exec prefix for shell
wrappers. The caller owns the fixture and keeps that profile unchanged until
the last use. run() also dispatches and records the requested command.
"""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

SERVICE = 'com.apple.dt.CommandLineTools.installondemand'
DSCL = ['/usr/bin/dscl', '.', '-read', '/Users/root', 'UniqueID']
PHRASES = ('requesting install', 'no install could be requested')


class ContainmentError(RuntimeError):
    pass


def installation_requests(*outputs):
    return [line for output in outputs for line in output.splitlines()
            if any(phrase in line for phrase in PHRASES)]


def base_environment(fixture):
    return dict(PATH='/usr/bin:/bin', HOME=os.environ['HOME'], TMPDIR=str(Path(fixture) / 'tmp'))


def execute(argv, *, env, cwd, timeout=60):
    record = dict(argv=list(map(str, argv)), started=time.time(), complete=False,
                  status=None, pid=None, stdout='', stderr='')
    try:
        process = subprocess.Popen(record['argv'], env=env, cwd=cwd, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        record['pid'] = process.pid
        try:
            out, err = process.communicate(timeout=timeout)
            record['complete'] = True
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            out, err = process.communicate()
        record.update(status=process.returncode, stdout=out, stderr=err)
    except OSError as exc:
        record['stderr'] = str(exc)
    record['finished'] = time.time()
    record['install_requests'] = installation_requests(record['stdout'], record['stderr'])
    return record


def gate_errors(results):
    """Decide collected evidence; constructed unit inputs never enter prepare()."""
    errors = []
    for name in ('outside', 'inside', 'permitted'):
        result = results.get(name, {})
        if result.get('complete') is not True or type(result.get('status')) is not int:
            errors.append(f'{name}: check did not complete')
        elif name == 'inside':
            if result['status'] == 0:
                errors.append('inside: dscl succeeded')
        elif result['status'] != 0:
            errors.append(f'{name}: check failed')
        if name == 'outside' and 'UniqueID: 0' not in result.get('stdout', ''):
            errors.append('outside: missing UniqueID: 0')
    return errors


def profile_text(write_paths, exec_allowlist=None):
    def literal(path):
        return json.dumps(str(Path(path).resolve()))
    text = '(version 1)(allow default)(deny mach-lookup)(deny file-write*)'
    text += '(allow file-write* (literal "/dev/null") (literal "/dev/dtracehelper")'
    text += ''.join(' (subpath ' + literal(path) + ')' for path in write_paths) + ')'
    if exec_allowlist is not None:
        allowed = sorted({str(Path(path).resolve()) for path in exec_allowlist} | {'/usr/bin/dscl'})
        text += '(deny process-exec)(allow process-exec'
        text += ''.join(' (literal ' + json.dumps(path) + ')' for path in allowed) + ')'
    return text + '\n'


def prepare(fixture, *, write_paths=(), exec_allowlist=None, success_command=None):
    fixture = Path(fixture).resolve()
    fixture.mkdir(parents=True, exist_ok=True)
    (fixture / 'tmp').mkdir(exist_ok=True)
    if exec_allowlist is None:
        success = ['/usr/bin/true']
    else:
        success = success_command or ['/usr/bin/xcrun', '--version']
        if str(Path(success[0]).resolve()) not in {str(Path(p).resolve()) for p in exec_allowlist}:
            raise ValueError('the success command must be in the exec allow-list')
    profile = fixture / 'contained.sb'
    with profile.open('x') as stream:
        stream.write(profile_text([fixture, *write_paths], exec_allowlist))
    prefix = ['/usr/bin/sandbox-exec', '-f', str(profile)]
    env = base_environment(fixture)
    checks = dict(outside=execute(DSCL, env=env, cwd=fixture),
                  inside=execute(prefix + DSCL, env=env, cwd=fixture),
                  permitted=execute(prefix + success, env=env, cwd=fixture))
    errors = gate_errors(checks)
    (fixture / 'containment.json').write_text(json.dumps(dict(checks=checks, errors=errors), indent=2) + '\n')
    if errors:
        raise ContainmentError('containment not established: ' + '; '.join(errors))
    return prefix


def run(fixture, argv, *, env=None, write_paths=(), exec_allowlist=None, success_command=None, timeout=60):
    prefix = prepare(fixture, write_paths=write_paths, exec_allowlist=exec_allowlist, success_command=success_command)
    environment = env if env is not None else base_environment(fixture)
    record = execute(prefix + list(argv), env=environment,
                     cwd=fixture, timeout=timeout)
    record['requests'] = {name: dict(state='set', value=environment[name]) if name in environment else dict(state='unset')
                          for name in ('SDKROOT', 'DEVELOPER_DIR')}
    (Path(fixture) / 'invocation.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def install_denials(events, records):
    """Keep service denials attributed by the PID in the kernel's process label."""
    found = []
    for event in events:
        message = event.get('eventMessage', '')
        if SERVICE not in message or 'deny' not in message:
            continue
        for record in records:
            if re.search(r'\(' + re.escape(str(record['pid'])) + r'\)\s+deny\(', message):
                found.append(dict(pid=record['pid'], message=message))
                break
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True, type=Path)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--write-path', action='append', default=[])
    parser.add_argument('--allow-exec', action='append')
    parser.add_argument('--env', action='append', default=[], metavar='NAME=VALUE')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not args.prepare and not command:
        parser.error('a command is required unless --prepare is given')
    options = dict(write_paths=args.write_path, exec_allowlist=args.allow_exec)
    try:
        if args.prepare:
            print(json.dumps(prepare(args.fixture, **options)))
            return 0
        env = base_environment(args.fixture.resolve())
        for entry in args.env:
            key, sep, value = entry.partition('=')
            if not sep or not key:
                parser.error('--env needs NAME=VALUE')
            env[key] = value
        record = run(args.fixture.resolve(), command, env=env, **options)
        print(json.dumps(record, indent=2))
        return 0 if record['complete'] and record['status'] == 0 and not record['install_requests'] else 1
    except (ContainmentError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
