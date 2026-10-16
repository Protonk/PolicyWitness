#!/usr/bin/env python3
"""Hold the stable checkout lock across a command, or verify an inherited hold.

`tests/.checkout.lock` serializes builds and managed test executions in one
checkout. The lock is an OS advisory lock on the file's inode; replacing the
file would let a later holder run beside the current one, so the file is
never unlinked. A held lock belongs to an open file description: every
process that inherits the descriptor shares the hold, and the hold ends when
the last such descriptor closes. An explicit unlock by any sharer would end
it early, so nothing here unlocks; descriptors are only closed.

    checkout_lock.py [--root CHECKOUT] -- COMMAND [ARG...]
        Acquire the lock without blocking, or share a verified inherited
        hold, then replace this process with COMMAND. The descriptor stays
        open across the exec and is inherited by COMMAND's descendants, so
        the hold outlives a killed parent while a protected child runs.

    checkout_lock.py --verify [--root CHECKOUT]
        Verify that the inherited claim in the environment is a real hold of
        this checkout's lock: the named descriptor is open on the lock file's
        inode, its open file description already holds the lock, and the
        file's owner record carries the claimed nonce. Exit 0 when verified.

The claim is three environment variables the launcher sets for its command:
PW_CHECKOUT_LOCK_FD (the descriptor number), PW_CHECKOUT_LOCK_ROOT (the
checkout the lock belongs to) and PW_CHECKOUT_LOCK_NONCE (the owner record's
nonce). The variables alone grant nothing: a descriptor opened separately on
the same inode cannot take the lock while the holder lives, so the
non-blocking lock attempt on the inherited descriptor is what establishes
shared ownership. A claim that names another checkout, a closed descriptor,
another file, a stale nonce or a descriptor that does not hold the lock is
refused, and the real holder's lock is left unchanged.

Exit 2 names the refusal: a busy lock, an unverified claim or a missing
command. A verified command exec never returns here.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import stat
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
LOCK = 'tests/.checkout.lock'
ENV_FD, ENV_ROOT, ENV_NONCE = 'PW_CHECKOUT_LOCK_FD', 'PW_CHECKOUT_LOCK_ROOT', 'PW_CHECKOUT_LOCK_NONCE'
BUSY = ('checkout busy: another execution or mutating operation holds tests/.checkout.lock; '
        'wait for it to finish or use a second worktree')


class Refusal(Exception):
    """A lock that cannot be held or a claim that cannot be verified."""


def owner_record(pid):
    return dict(pid=pid, started_at_unix_ms=time.time_ns() // 1_000_000, nonce=uuid.uuid4().hex)


def read_owner(fd):
    """The owner record the holder wrote, or None when the file holds no valid record."""
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        raw = os.read(fd, 4096)
        record = json.loads(raw.decode('utf-8'))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def claim(env):
    """The inherited claim, or None when the environment makes none."""
    if not any(name in env for name in (ENV_FD, ENV_ROOT, ENV_NONCE)):
        return None
    try:
        fd = int(env.get(ENV_FD, ''))
    except ValueError:
        raise Refusal(f'{ENV_FD} is not a descriptor number')
    if fd < 0 or not env.get(ENV_ROOT) or not env.get(ENV_NONCE):
        raise Refusal(f'{ENV_FD}, {ENV_ROOT} and {ENV_NONCE} must all be set')
    return dict(fd=fd, root=env[ENV_ROOT], nonce=env[ENV_NONCE])


def verify(root, env=os.environ):
    """Verify the inherited claim against this checkout's lock; the verified descriptor, or a Refusal."""
    root = Path(root).resolve()
    found = claim(env)
    if found is None:
        raise Refusal('no inherited checkout lock claim')
    if Path(found['root']).resolve() != root:
        raise Refusal(f"claim belongs to another checkout: {found['root']}")
    lock = root / LOCK
    try:
        expected = os.lstat(lock)
    except OSError as exc:
        raise Refusal(f'lock file is not readable: {exc}')
    try:
        actual = os.fstat(found['fd'])
    except OSError:
        raise Refusal(f"descriptor {found['fd']} is not open in this process")
    if not stat.S_ISREG(expected.st_mode) or not stat.S_ISREG(actual.st_mode):
        raise Refusal('lock file is not a regular file')
    if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
        raise Refusal(f"descriptor {found['fd']} is open on another file, not {LOCK}")
    # The same open file description re-takes a held lock without blocking; a
    # separately opened descriptor on this inode cannot while the holder lives.
    try:
        fcntl.flock(found['fd'], fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise Refusal(f"descriptor {found['fd']} does not hold the lock; another process holds it")
    record = read_owner(found['fd'])
    if not record or record.get('nonce') != found['nonce']:
        raise Refusal('owner record does not carry the claimed nonce')
    return found['fd']


def acquire(root):
    """Open the lock file and take the lock without blocking; the inheritable descriptor and its record."""
    root = Path(root).resolve()
    lock = root / LOCK
    lock.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise Refusal(BUSY)
    record = owner_record(os.getpid())
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, (json.dumps(record) + '\n').encode())
    os.set_inheritable(fd, True)
    return fd, record


def hold_and_exec(root, command, env=os.environ):
    root = Path(root).resolve()
    if not command:
        raise Refusal('no command to run under the checkout lock')
    environment = dict(env)
    if claim(env) is not None:
        fd = verify(root, env)
        os.set_inheritable(fd, True)
    else:
        fd, record = acquire(root)
        environment.update({ENV_FD: str(fd), ENV_ROOT: str(root), ENV_NONCE: record['nonce']})
    os.execvpe(command[0], list(command), environment)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     allow_abbrev=False)
    parser.add_argument('--root', type=Path, default=ROOT, help='the checkout whose lock is held (default: this repository)')
    parser.add_argument('--verify', action='store_true', help='verify the inherited claim and exit')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='-- COMMAND [ARG...] to run under the lock')
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    try:
        if args.verify:
            if command:
                parser.error('--verify takes no command')
            try:
                fd = verify(args.root)
            except Refusal as exc:
                raise Refusal(f'checkout lock claim is not verified: {exc}; unset {ENV_FD}, {ENV_ROOT} and {ENV_NONCE} to take the lock here')
            print(f'ok: inherited descriptor {fd} holds {LOCK} for {Path(args.root).resolve()}')
            return 0
        hold_and_exec(args.root, command)
    except Refusal as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    except OSError as exc:
        print(f'ERROR: checkout lock: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
