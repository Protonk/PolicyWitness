#!/usr/bin/python3
"""Delegate to the real tool and record a receipt; a configured hook changes files beside one call.

The build script resolves cargo, meson, ninja, codesign and cp through PATH.
Each wrapper runs the real tool with the same arguments and appends one
receipt line. A hook names a tool and a matching call; its actions remove,
move, copy over, replace with a new file, truncate, append to, rewrite or
replace with a symlink a file, edit
Cargo's artifact report (set or remove fields, drop or duplicate a message), kill or signal the build's shell, the lock owner or
the wrapper itself, start a holder process beyond the wrapper, or record
whether the checkout lock is free, before or after that call, so a missing or
damaged input, a false report, a replaced path or an interruption appears at
exactly one boundary of the unchanged script. A hook may also append
arguments to the real tool's command (a cross file for `meson setup`), so a
configuration the script does not choose reaches it through the tool it
already runs. The real tool and a holder
receive the checkout lock descriptors the claim names, as every protected
launch must; Python would close them by default. A hook may also answer a call instead of running the
tool (an old ninja reporting its version). A configured stderr canary is
written on every call so a record that kept tool output would carry it. The
script's own checks make every refusal; the wrapper never prints a diagnostic
of its own.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys


def matches(hook, tool, args):
    if hook['tool'] != tool:
        return False
    match = hook.get('match', {})
    if 'args' in match and args != match['args']:
        return False
    if 'last' in match and (not args or args[-1] != match['last']):
        return False
    if 'first' in match and (not args or args[0] != match['first']):
        return False
    if 'contains' in match and match['contains'] not in args:
        return False
    if 'excludes' in match and match['excludes'] in args:
        return False
    return True


def lock_fds():
    """The claim's descriptors open in this process, passed on to the real tool and to a holder."""
    found = []
    for name in ('PW_CHECKOUT_LOCK_FD', 'PW_CHECKOUT_LOCK_CHANNEL'):
        try:
            fd = int(os.environ.get(name, ''))
            os.fstat(fd)
        except (ValueError, OSError):
            continue
        found.append(fd)
    return tuple(sorted(set(found)))


def owner_pid(lock):
    return json.loads(Path(lock).read_text())['pid']


def act(action):
    op = action['op']
    if op == 'kill_parent':
        os.kill(os.getppid(), signal.SIGKILL)
        return
    if op == 'kill_self':
        os.kill(os.getpid(), signal.SIGKILL)
        return
    if op == 'signal_owner':
        os.kill(owner_pid(action['lock']), getattr(signal, action['signal']))
        return
    path = Path(action['path'])
    if op == 'spawn_holder':
        # A protected grandchild beyond this wrapper: it waits for a release file and records its pid.
        waiter = ('import os, sys, time\n'
                  'deadline = time.monotonic() + 600\n'
                  'while not os.path.exists(sys.argv[1]) and time.monotonic() < deadline:\n'
                  '    time.sleep(0.05)\n')
        child = subprocess.Popen([sys.executable, '-B', '-c', waiter, action['release']], pass_fds=lock_fds(), start_new_session=True)
        path.write_text(json.dumps(dict(holder=child.pid, wrapper=os.getpid(), passed=list(lock_fds()))))
        return
    if op == 'probe_lock':
        import fcntl
        fd = os.open(action['lock'], os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = 'free'
        except BlockingIOError:
            state = 'held'
        finally:
            os.close(fd)
        with path.open('a') as stream:
            stream.write(state + '\n')
        return
    if op == 'delete':
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
    elif op == 'move':
        shutil.move(str(path), action['to'])
    elif op == 'copy':
        shutil.copy2(action['from'], path)
        path.chmod(0o755)
    elif op == 'replace':
        # A new file with the current time renamed over the path: nothing else that links to the old file changes, and a
        # tool that compares times (Cargo judging a cached unit) sees it as newly written, not as the source's age.
        temporary = path.with_name(path.name + '.pw-replace')
        shutil.copyfile(action['from'], temporary)
        temporary.chmod(0o755)
        os.replace(temporary, path)
    elif op == 'chmod':
        path.chmod(int(action['mode'], 8))
    elif op == 'truncate':
        path.write_bytes(path.read_bytes()[:action['keep']])
    elif op == 'append':
        with path.open('ab') as stream:
            stream.write(action['text'].encode())
    elif op == 'write':
        path.write_text(action['text'])
    elif op == 'symlink':
        path.symlink_to(action['to'])
    elif op == 'judge':
        # Edit Cargo's artifact report for one target: set or remove fields, drop its line, or add a second message for
        # it with the set fields changed.
        lines = []
        for line in path.read_text().splitlines():
            if line.strip():
                message = json.loads(line)
                if message.get('reason') == 'compiler-artifact' and (message.get('target') or {}).get('name') == action['target']:
                    if action.get('drop'):
                        continue
                    if action.get('duplicate'):
                        lines.append(line)
                    message.update(action.get('set', {}))
                    for key in action.get('unset', ()):
                        message.pop(key, None)
                    line = json.dumps(message)
            lines.append(line)
        path.write_text('\n'.join(lines) + '\n')
    else:
        raise ValueError(f'unknown action {op!r}')


def main():
    tool = Path(sys.argv[0]).name
    config = json.loads(Path(os.environ['PW_BUILD_REFUSAL_CONFIG']).read_text())
    args = sys.argv[1:]
    if config.get('stderr_canary'):
        sys.stderr.write(config['stderr_canary'] + '\n')
        sys.stderr.flush()
    fired = []
    hooks = [hook for hook in config.get('hooks', []) if matches(hook, tool, args)]
    for hook in hooks:
        if hook.get('when', 'after') == 'before':
            for action in hook.get('actions', []):
                act(action)
            fired.append(hook['label'])
    responded = [hook for hook in hooks if 'respond' in hook]
    if responded:
        hook = responded[0]
        sys.stdout.write(hook['respond'].get('stdout', ''))
        sys.stdout.flush()
        status = hook['respond'].get('status', 0)
        fired.append(hook['label'])
        executed = None
    else:
        appended = [arg for hook in hooks for arg in hook.get('append', [])]
        fired += [hook['label'] for hook in hooks if hook.get('append') and hook['label'] not in fired]
        executed = [config['tools'][tool], *args, *appended]
        status = subprocess.run(executed, pass_fds=lock_fds()).returncode
    # The receipt names every hook that fires around this call and is written before the
    # after-actions run, so an action that kills the build's shell still leaves it.
    after = [hook for hook in hooks if hook.get('when', 'after') == 'after' and 'respond' not in hook]
    fired += [hook['label'] for hook in after if hook['label'] not in fired]
    with Path(config['receipt']).open('a') as stream:
        stream.write(json.dumps(dict(tool=tool, args=args, executed=executed, status=status, fired=fired)) + '\n')
    for hook in after:
        for action in hook.get('actions', []):
            act(action)
    return status


if __name__ == '__main__':
    sys.exit(main())
