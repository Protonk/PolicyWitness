#!/usr/bin/python3
"""Delegate to the real tool and record a receipt; a configured hook changes files beside one call.

The build script resolves cargo, meson, ninja, codesign and cp through PATH.
Each wrapper runs the real tool with the same arguments and appends one
receipt line. A hook names a tool and a matching call; its actions remove,
move, truncate, append to or rewrite a file before or after that call, so a
missing or damaged input appears at exactly one boundary of the unchanged
script. A hook may also answer a call instead of running the tool (an old
ninja reporting its version). The script's own checks make every refusal;
the wrapper never prints a diagnostic of its own.
"""
import json
import os
from pathlib import Path
import shutil
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
    return True


def act(action):
    path = Path(action['path'])
    op = action['op']
    if op == 'delete':
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
    elif op == 'move':
        shutil.move(str(path), action['to'])
    elif op == 'truncate':
        path.write_bytes(path.read_bytes()[:action['keep']])
    elif op == 'append':
        with path.open('ab') as stream:
            stream.write(action['text'].encode())
    elif op == 'write':
        path.write_text(action['text'])
    else:
        raise ValueError(f'unknown action {op!r}')


def main():
    tool = Path(sys.argv[0]).name
    config = json.loads(Path(os.environ['PW_BUILD_REFUSAL_CONFIG']).read_text())
    args = sys.argv[1:]
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
        executed = [config['tools'][tool], *args]
        status = subprocess.run(executed).returncode
    for hook in hooks:
        if hook.get('when', 'after') == 'after' and 'respond' not in hook:
            for action in hook.get('actions', []):
                act(action)
            fired.append(hook['label'])
    with Path(config['receipt']).open('a') as stream:
        stream.write(json.dumps(dict(tool=tool, args=args, executed=executed, status=status, fired=fired)) + '\n')
    return status


if __name__ == '__main__':
    sys.exit(main())
