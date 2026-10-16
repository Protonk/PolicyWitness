#!/usr/bin/python3
"""Forwarding compiler wrapper: run the real compiler with the same arguments and record what was asked.

Build controls put a copy of this file on PATH, in CC, RUSTC or RUSTC_WRAPPER
and describe each copy in the JSON file PW_FORWARD_CONFIG names, keyed by the
copy's file name:

  real            the compiler to run (ignored in rustc_wrapper mode, where
                  Cargo passes the compiler path as the first argument)
  mode            "direct" (the wrapper is the compiler) or "rustc_wrapper"
  label           appended to the first line of a version query's output, so
                  two wrappers over one real compiler report distinct
                  identities; the compilation itself is unchanged
  fail_version    answer a version query with a nonzero status and no output
  hang_version    never answer a version query
  stderr_canary   text written to stderr on every version query; a record
                  that keeps stderr would carry it
  receipt         file that receives one JSON line per invocation, with the
                  checkout lock descriptor the claim names, open or not, and
                  the inode it is open on, so a control can tell whether the
                  real Cargo, Meson and Ninja passed it to the compiler

A version query is `--version` or `-vV` alone. Every other invocation is
forwarded unchanged and classified in its receipt: Cargo's capability probes
name the crate `___`, a compilation names a real crate or a C source. The
wrapper never prints a diagnostic of its own; substituted version text covers
parsing and comparison decisions, not which compiler produced an output.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def classify(args):
    if args in (['--version'], ['-vV']):
        return 'version'
    if '--crate-name' in args:
        return 'probe' if '___' in args else 'compile'
    if any(a.endswith('.c') or a.endswith('.swift') for a in args):
        return 'compile'
    return 'other'


def lock_descriptor():
    try:
        fd = int(os.environ.get('PW_CHECKOUT_LOCK_FD', ''))
    except ValueError:
        return None
    try:
        info = os.fstat(fd)
    except OSError:
        return dict(fd=fd, open=False)
    return dict(fd=fd, open=True, device=info.st_dev, inode=info.st_ino)


def main():
    tool = Path(sys.argv[0]).name
    config = json.loads(Path(os.environ['PW_FORWARD_CONFIG']).read_text())[tool]
    args = sys.argv[1:]
    if config.get('mode') == 'rustc_wrapper':
        real, args = args[0], args[1:]
    else:
        real = config['real']
    kind = classify(args)
    if config.get('receipt'):
        with Path(config['receipt']).open('a') as stream:
            stream.write(json.dumps(dict(tool=tool, real=real, args=args, cwd=os.getcwd(), kind=kind, lock=lock_descriptor())) + '\n')
    if kind == 'version':
        if config.get('stderr_canary'):
            sys.stderr.write(config['stderr_canary'] + '\n')
            sys.stderr.flush()
        if config.get('hang_version'):
            time.sleep(600)
        if config.get('fail_version'):
            return 3
        result = subprocess.run([real, *args], capture_output=True, text=True)
        text = result.stdout
        if config.get('label') and text:
            first, newline, rest = text.partition('\n')
            text = f'{first} [forward {config["label"]}]{newline}{rest}'
        sys.stdout.write(text)
        sys.stdout.flush()
        sys.stderr.write(result.stderr)
        return result.returncode
    os.execv(real, [real, *args])


if __name__ == '__main__':
    sys.exit(main())
