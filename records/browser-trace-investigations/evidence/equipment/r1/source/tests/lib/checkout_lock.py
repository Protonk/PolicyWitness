#!/usr/bin/env python3
"""Own the stable checkout lock for an operation, admit nested owned commands, and launch protected children.

`tests/.checkout.lock` serializes builds and managed test executions in one
checkout. The lock is an OS advisory lock on the file's inode; replacing the
file would let a later holder run beside the current one, so the file is
never unlinked. A held lock belongs to an open file description: every
process holding a descriptor for that description shares the hold, and the
hold ends when the last such descriptor closes. An explicit unlock by any
sharer would end it early, so nothing here unlocks; descriptors are closed.

Ownership. An owner is a live process whose scope holds the lock: either it
took the lock without blocking (the outermost owner, which writes the owner
record: pid, start time and the acquisition nonce), or a live owner admitted
it by handing over the held descriptor (a nested owner). Python callers hold
an owner for a block (`owned`); the command line holds one for its command.
The acquisition owner serves admissions on a private channel for as long as
its scope lasts. Nested owners pass that same channel onward. The channel
is a datagram socket pair created by the acquisition owner; only the
children it launches inherit the client end, so a socket pathname or a nonce
alone admits nobody.

Admission. A nested process proves ownership only through a handoff: over
the channel its environment names, it sends the root and nonce it was given
with a fresh reply socket, and the owner answers on that socket with the held
descriptor, the nonce and the lock file's inode. The admitted process checks
that the channel's socket identity matches the acquisition record and its
kernel-reported peer PID matches the acquisition owner,
the descriptor is open on this checkout's lock file and the owner record
carries the nonce. Environment values (PW_CHECKOUT_LOCK_ROOT,
PW_CHECKOUT_LOCK_NONCE, PW_CHECKOUT_LOCK_CHANNEL and PW_CHECKOUT_LOCK_FD)
only locate a claim. A missing, stale, foreign or malformed claim refuses, and
so does a claim whose owner is gone or does not answer within
HANDOFF_TIMEOUT seconds; admission never takes the lock itself, because
taking a free lock says nothing about earlier ownership.

Lifetime. An owner passes the held descriptor explicitly to each protected
child it launches (PW_CHECKOUT_LOCK_FD names it), so the hold outlives a
killed owner until the last protected descendant exits; a Python wrapper in
that lineage must pass it on, because Python closes inherited descriptors in
its children by default. Processes an owner starts outside its protected
launches never receive it. After the owner is gone its channel is closed, so
descendants that are still running keep the lock but cannot admit new nested
mutations.

Environment witness. The shell front end starts the developer directory's
Python directly, with locale coercion disabled, and exports a witness of
SDKROOT, CPATH, LIBRARY_PATH, MANPATH and LC_CTYPE. The command-line owner
compares it before taking the lock; a missing or changed value refuses.
Nothing restores environment values. A nested front end witnesses its own
caller. Python callers of owned() need no witness; builds check one again
at session-start, before any session or cache write.

    checkout_lock.sh [--root CHECKOUT] -- COMMAND [ARG...]
        The supported entrypoint: record the witness, then start this file directly.

    checkout_lock.py [--root CHECKOUT] -- COMMAND [ARG...]
        Take the lock without blocking, or be admitted by the owner of an
        inherited claim on this checkout, then supervise COMMAND in its own process group:
        forward SIGINT, SIGTERM and SIGHUP to that group, serve admissions
        while it runs and exit with its status. Cancellation allows GROUP_GRACE
        seconds before SIGKILL and KILL_GRACE seconds to observe exit, then
        returns 128 + the original signal. Requires the front end's witness.

    checkout_lock.py --verify [--root CHECKOUT]
        Be admitted by the owner of the inherited claim and exit 0.

Exit 2 names the refusal: a busy lock, an unverified claim, a missing or
changed environment witness, or a missing command. Otherwise the command's
status is returned, 128 + N for a command stopped by signal N.
"""
import argparse
import array
import errno
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
LOCK = 'tests/.checkout.lock'
ENV_FD, ENV_ROOT, ENV_NONCE, ENV_CHANNEL = ('PW_CHECKOUT_LOCK_FD', 'PW_CHECKOUT_LOCK_ROOT', 'PW_CHECKOUT_LOCK_NONCE',
                                            'PW_CHECKOUT_LOCK_CHANNEL')
CLAIM_ENV = (ENV_FD, ENV_ROOT, ENV_NONCE, ENV_CHANNEL)
BUSY = ('checkout busy: another execution or mutating operation holds tests/.checkout.lock; '
        'wait for it to finish or use a second worktree')
UNSET_REMEDY = f'unset {", ".join(CLAIM_ENV)} to take the lock here'
FRONT_END = 'tests/lib/checkout_lock.sh'
NONCE_RE = re.compile(r'[0-9a-f]{32}')
ENVIRONMENT_NAMES = ('SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE')
WITNESS_PREFIX = 'PW_ENV_WITNESS_'
MESSAGE_LIMIT = 64 * 1024
HANDOFF_TIMEOUT = 10
GROUP_GRACE = 10
KILL_GRACE = 5
# Darwin sys/un.h: SOL_LOCAL / LOCAL_PEERPID. The kernel records the creator
# of a socketpair; inherited ends retain that identity across exec and forks.
SOL_LOCAL, LOCAL_PEERPID = 0, 2


class Refusal(ValueError):
    """A lock that cannot be held, a claim that cannot be admitted or an environment witness that does not match."""


# ---- environment witness -------------------------------------------------------------

def verify_environment(*, sdk_request=None):
    """Compare with the shell's witness, never repair; return the observed request states.

    Each exported witness is 'u' for unset or 's' followed by the exact value.
    Python's filesystem decoding preserves non-UTF-8 environment bytes through
    surrogateescape. No delimiter, command substitution or length bound loses
    empty values, trailing newlines or any other byte an environment can hold.
    session-start supplies SDKROOT's state from before build.sh removed it.
    """
    requests = {}
    for name in ENVIRONMENT_NAMES:
        value = os.environ.get(name)
        if name == 'SDKROOT' and sdk_request is not None:
            state, value = sdk_request
            value = value if state == 'set' else None
        witness = os.environ.get(WITNESS_PREFIX + name)
        if witness is None:
            raise Refusal(f'environment witness missing for {name}; start through {FRONT_END}')
        expected = 'u' if value is None else 's' + value
        if witness != expected:
            if name == 'LC_CTYPE' and witness == 'u' and value in ('C.UTF-8', 'UTF-8'):
                # The front end witnessed no LC_CTYPE and the interpreter set one from a C locale: it coerced the
                # locale, so PYTHONCOERCECLOCALE=0 was not honored (an -E or -I start, or a start outside the resolver).
                raise Refusal(f'environment witness differs for {name}: the helper interpreter coerced the locale to {value}; '
                              'PYTHONCOERCECLOCALE=0 was not honored (start it through python_start.sh without -E or -I)')
            raise Refusal(f'environment witness differs for {name}; start through {FRONT_END}')
        requests[name] = dict(state='unset') if value is None else dict(state='set', value=value)
    return requests


# ---- the lock file -------------------------------------------------------------------

def owner_record(pid):
    return dict(pid=pid, started_at_unix_ms=time.time_ns() // 1_000_000, nonce=uuid.uuid4().hex)


def read_owner(fd):
    """The owner record the outermost holder wrote, or None when the file holds no valid record."""
    try:
        raw = os.pread(fd, 4096, 0)
        record = json.loads(raw.decode('utf-8'))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def lock_identity(root):
    """The lock file's (device, inode), refusing a missing, linked or irregular file."""
    try:
        info = os.lstat(Path(root) / LOCK)
    except OSError as exc:
        raise Refusal(f'lock file is not readable: {exc}')
    if not stat.S_ISREG(info.st_mode):
        raise Refusal('lock file is not a regular file')
    return info.st_dev, info.st_ino


def acquire(root):
    """Open the lock file and take the lock without blocking: the non-inheritable descriptor and the owner record."""
    root = Path(root).resolve()
    lock = root / LOCK
    lock.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise Refusal(BUSY)
    record = owner_record(os.getpid())
    os.ftruncate(fd, 0)
    os.pwrite(fd, (json.dumps(record) + '\n').encode(), 0)
    return fd, record


def bind_channel(fd, channel):
    """Publish this acquisition's client socket identity before launching any children."""
    record = read_owner(fd)
    info = os.fstat(channel.fileno())
    record['channel'] = dict(device=info.st_dev, inode=info.st_ino)
    os.ftruncate(fd, 0)
    os.pwrite(fd, (json.dumps(record) + '\n').encode(), 0)


@contextmanager
def preview(root):
    """Observe whether the lock is held, without creating the file; True when busy.

    When the lock is free the probe holds it for the block, so the caller sees a
    consistent snapshot; it writes no owner record and reserves nothing after."""
    path = Path(root) / LOCK
    if not os.path.lexists(path):
        yield False
        return
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            busy = False
        except BlockingIOError:
            busy = True
        yield busy
    finally:
        os.close(fd)


# ---- claims and admission --------------------------------------------------------------

def claim_present(env):
    return any(name in env for name in CLAIM_ENV)


def claim_for(root, env):
    """Whether the environment's claim, well formed or not, names this checkout; a claim names exactly one."""
    if not claim_present(env):
        return False
    named = env.get(ENV_ROOT)
    return not named or Path(named).resolve() == Path(root).resolve()


def claim(env):
    """The inherited claim, or None when the environment makes none; a malformed claim refuses."""
    if not claim_present(env):
        return None
    missing = [name for name in (ENV_ROOT, ENV_NONCE, ENV_CHANNEL) if not env.get(name)]
    if missing:
        raise Refusal(f'malformed claim: {", ".join(missing)} not set')
    if not NONCE_RE.fullmatch(env[ENV_NONCE]):
        raise Refusal(f'malformed claim: {ENV_NONCE} is not an acquisition nonce')
    try:
        channel = int(env[ENV_CHANNEL])
        lifetime = int(env[ENV_FD]) if env.get(ENV_FD) else None
    except ValueError:
        raise Refusal(f'malformed claim: {ENV_CHANNEL} and {ENV_FD} must be descriptor numbers')
    if channel < 0 or (lifetime is not None and lifetime < 0):
        raise Refusal('malformed claim: negative descriptor number')
    return dict(root=env[ENV_ROOT], nonce=env[ENV_NONCE], channel=channel, fd=lifetime)


def inherited_fds(env=None):
    """The claim's descriptors that are open here, for a wrapper to pass on to the tool it runs."""
    env = os.environ if env is None else env
    found = []
    for name in (ENV_FD, ENV_CHANNEL):
        try:
            fd = int(env.get(name, ''))
            os.fstat(fd)
        except (ValueError, OSError):
            continue
        found.append(fd)
    return tuple(sorted(set(found)))


class Admission:
    """A descriptor a live owner handed over, open on this checkout's lock file, with the acquisition it belongs to."""

    def __init__(self, root, fd, nonce, identity):
        self.root, self.fd, self.nonce, self.identity = root, fd, nonce, identity

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


def send_request(channel, request, reply_fd, deadline):
    """Bound the send as well as the answer without changing the shared socket's flags."""
    while True:
        try:
            channel.sendmsg([request], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [reply_fd]))], socket.MSG_DONTWAIT)
            return
        except BlockingIOError:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([], [channel], [], remaining)[1]:
                raise Refusal('the owner channel did not accept the request before the handoff deadline')
        except OSError as exc:
            if exc.errno == errno.ENOBUFS:
                raise Refusal('the owner channel queue is full')
            raise


def receive_answer(channel, deadline):
    """Read a bounded stream through EOF; SCM_RIGHTS may accompany any chunk."""
    chunks, received, size, flags = [], [], 0, 0
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise socket.timeout()
            channel.settimeout(remaining)
            chunk, fds, observed, _ = socket.recv_fds(channel, MESSAGE_LIMIT + 1 - size, 2)
            received.extend(fds)
            flags |= observed
            size += len(chunk)
            if size > MESSAGE_LIMIT or len(received) > 1 or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                raise Refusal('the owner answer exceeds the handoff bound')
            if not chunk:
                return b''.join(chunks), received, flags
            chunks.append(chunk)
    except BaseException:
        for fd in received:
            os.close(fd)
        raise


def admit(root, env=None, *, timeout=HANDOFF_TIMEOUT):
    """Be admitted by the owner of the inherited claim: an Admission, or a Refusal. Never takes the lock."""
    env = os.environ if env is None else env
    root = Path(root).resolve()
    found = claim(env)
    if found is None:
        raise Refusal('no inherited checkout lock claim')
    if Path(found['root']).resolve() != root:
        raise Refusal(f"claim belongs to another checkout: {found['root']}")
    try:
        info = os.fstat(found['channel'])
    except OSError:
        raise Refusal(f"descriptor {found['channel']} is not open in this process; the claim names no owner channel")
    if not stat.S_ISSOCK(info.st_mode):
        raise Refusal(f"descriptor {found['channel']} is not an owner channel")
    channel = socket.socket(fileno=os.dup(found['channel']))
    local, remote = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    received = []
    try:
        if channel.family != socket.AF_UNIX or channel.type != socket.SOCK_DGRAM:
            raise Refusal(f"descriptor {found['channel']} is not an owner channel")
        # A socket plus a copied nonce/inode does not establish a handoff. Bind
        # the channel to the acquisition owner before trusting any reply.
        record_fd = os.open(root / LOCK, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            if not stat.S_ISREG(os.fstat(record_fd).st_mode):
                raise Refusal('lock file is not a regular file')
            owner = read_owner(record_fd)
        finally:
            os.close(record_fd)
        try:
            peer_pid = channel.getsockopt(SOL_LOCAL, LOCAL_PEERPID)
        except OSError:
            raise Refusal('the owner of this claim is gone; its channel has no connected peer')
        if not owner or type(owner.get('pid')) is not int or peer_pid != owner['pid']:
            raise Refusal('the channel was not created by the acquisition owner')
        if owner.get('channel') != dict(device=info.st_dev, inode=info.st_ino):
            raise Refusal('the channel does not belong to this acquisition')
        deadline = time.monotonic() + timeout
        request = json.dumps(dict(v=1, op='admit', root=str(root), nonce=found['nonce'])).encode()
        try:
            send_request(channel, request, remote.fileno(), deadline)
        except OSError:
            raise Refusal('the owner of this claim is gone; nothing new can be admitted under it')
        remote.close()
        try:
            message, received, flags = receive_answer(local, deadline)
        except socket.timeout:
            raise Refusal(f'the owner of this claim did not answer within {timeout} s')
        except OSError as exc:
            raise Refusal(f'the owner of this claim is gone ({exc.__class__.__name__})')
        if not message:
            raise Refusal('the owner of this claim is gone; nothing new can be admitted under it')
        try:
            reply = json.loads(message.decode())
        except ValueError:
            raise Refusal('the owner sent a malformed answer')
        if not isinstance(reply, dict) or reply.get('v') != 1:
            raise Refusal('the owner sent a malformed answer')
        if reply.get('status') != 'ok':
            raise Refusal(f"the owner refused the claim: {str(reply.get('reason'))[:200]}")
        if len(received) != 1 or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
            raise Refusal('the owner sent no single lock descriptor')
        fd = received[0]
        handed = os.fstat(fd)
        expected = lock_identity(root)
        if not stat.S_ISREG(handed.st_mode) or (handed.st_dev, handed.st_ino) != expected:
            raise Refusal(f'the handed descriptor is not open on this checkout\'s {LOCK}')
        if [reply.get('device'), reply.get('inode')] != list(expected) or reply.get('nonce') != found['nonce']:
            raise Refusal('the owner answered for another acquisition')
        record = read_owner(fd)
        if not record or record.get('nonce') != found['nonce'] or record.get('pid') != owner['pid']:
            raise Refusal('owner record does not carry the claimed nonce')
        received = []
        return Admission(root, fd, found['nonce'], expected)
    finally:
        for fd in received:
            os.close(fd)
        channel.close()
        local.close()
        remote.close()


@contextmanager
def admitted(root, env=None):
    """Hold a handed-over descriptor for the block: the Admission, or a Refusal before the block runs."""
    admission = admit(root, env)
    try:
        yield admission
    finally:
        admission.close()


# ---- owners ------------------------------------------------------------------------------

class Scope:
    """A live owner: the held descriptor, its acquisition, and the channel it serves."""

    def __init__(self, root, fd, nonce, identity, *, nested, channel=None):
        self.root, self.fd, self.nonce, self.identity = Path(root), fd, nonce, identity
        self.nested = nested
        if nested:
            self.server, self.client = None, socket.socket(fileno=os.dup(channel))
        else:
            self.server, self.client = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
            bind_channel(fd, self.client)
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self.serve, name='checkout-lock-owner', daemon=True)

    def start(self):
        if self.nested:
            return
        self.server.settimeout(0.2)
        self.thread.start()

    def serve(self):
        while not self.stopping.is_set():
            try:
                message, fds, flags, _ = socket.recv_fds(self.server, MESSAGE_LIMIT, 4)
            except socket.timeout:
                continue
            except OSError:
                return
            self.answer(message, fds, flags)

    def answer(self, message, fds, flags):
        reply = None
        try:
            if len(fds) != 1 or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                return  # no reply socket to answer on
            reply = socket.socket(fileno=fds.pop())
            reply.settimeout(2)
            if reply.family != socket.AF_UNIX or reply.type != socket.SOCK_STREAM:
                return
            try:
                request = json.loads(message.decode())
            except ValueError:
                request = None
            if not isinstance(request, dict) or request.get('v') != 1 or request.get('op') != 'admit':
                reason = 'malformed request'
            elif request.get('root') != str(self.root):
                reason = 'the claim names another checkout'
            elif request.get('nonce') != self.nonce:
                reason = 'the claim names another acquisition'
            else:
                answer = dict(v=1, status='ok', nonce=self.nonce, device=self.identity[0], inode=self.identity[1])
                encoded = json.dumps(answer).encode()
                sent = socket.send_fds(reply, [encoded], [self.fd])
                reply.sendall(encoded[sent:])
                return
            reply.sendall(json.dumps(dict(v=1, status='refused', reason=reason)).encode())
        except OSError:
            pass
        finally:
            for fd in fds:
                os.close(fd)
            if reply is not None:
                reply.close()

    def child_env(self, base=None):
        """An environment for a protected child: this owner's claim, stale claims dropped."""
        base = os.environ if base is None else base
        env = {k: v for k, v in base.items() if k not in CLAIM_ENV}
        env.update({ENV_ROOT: str(self.root), ENV_NONCE: self.nonce, ENV_FD: str(self.fd),
                    ENV_CHANNEL: str(self.client.fileno())})
        return env

    def pass_fds(self):
        return (self.fd, self.client.fileno())

    def popen(self, argv, *, env=None, pass_fds=(), **kwargs):
        """Launch a protected child: it holds the lock descriptor and may ask this owner for nested admission."""
        return subprocess.Popen(argv, env=self.child_env(env), pass_fds=tuple(sorted(set(pass_fds) | set(self.pass_fds()))), **kwargs)

    def supervise(self, argv, *, env=None):
        """Run a protected command in its own process group, forwarding termination; its status as an exit code."""
        child = self.popen(argv, env=env, start_new_session=True)
        forwarded = []
        cancelled_at = []

        def forward(signum, _frame):
            forwarded.append(signum)
            if not cancelled_at:
                cancelled_at.append(time.monotonic())
            try:
                os.killpg(child.pid, signum)
            except (ProcessLookupError, PermissionError):
                pass

        previous = {signum: signal.signal(signum, forward) for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
        try:
            while child.poll() is None and not cancelled_at:
                time.sleep(0.05)
            if cancelled_at:
                remaining = max(0, cancelled_at[0] + GROUP_GRACE - time.monotonic())
                if not group_finished(child.pid, remaining, child):
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass
                    if not group_finished(child.pid, KILL_GRACE, child):
                        print(f'WARN: protected processes of the cancelled command are still running; {LOCK} stays held until they exit',
                              file=sys.stderr)
                return 128 + forwarded[0]
            status = child.returncode
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
        return 128 - status if status < 0 else status

    def close(self):
        self.stopping.set()
        if self.server is not None:
            try:
                self.server.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.server.close()
        if self.thread.is_alive():
            self.thread.join(timeout=2)
        self.client.close()
        os.close(self.fd)


def group_finished(pgid, timeout, child=None):
    """Whether every member of a process group has exited, observed for up to timeout seconds.

    macOS answers EPERM while the only members left are zombies, so that answer means not yet."""
    deadline = time.monotonic() + timeout
    while True:
        if child is not None:
            child.poll()  # reap the leader so it cannot keep the group alive as a zombie
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            pass
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)


@contextmanager
def owned(root, *, env=None, purpose='execution'):
    """Own the checkout lock for the block: take it, or be admitted by the owner of an inherited claim on this checkout.

    The acquisition scope serves admissions until its block ends; nested
    scopes preserve its channel. A claim on another checkout is not a claim
    on this one: separate worktrees have independent locks, so the scope takes
    this one itself and its children inherit only its own claim."""
    if purpose not in ('execution', 'recovery', 'disposal'):
        raise Refusal('unknown checkout ownership purpose')
    env = os.environ if env is None else env
    root = Path(root).resolve()
    if claim_for(root, env):
        try:
            admission = admit(root, env)
        except Refusal as exc:
            raise Refusal(f'checkout lock claim is not verified: {exc}; {UNSET_REMEDY}')
        scope = Scope(root, admission.fd, admission.nonce, admission.identity, nested=True,
                      channel=claim(env)['channel'])
    else:
        fd, record = acquire(root)
        held = os.fstat(fd)
        scope = Scope(root, fd, record['nonce'], (held.st_dev, held.st_ino), nested=False)
    scope.start()
    try:
        if purpose == 'execution':
            from pytest_resources import guard
            try:
                guard(root)
            except (ValueError, OSError) as exc:
                raise Refusal(str(exc))
        yield scope
    finally:
        scope.close()


# ---- the command line ------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     allow_abbrev=False)
    parser.add_argument('--root', type=Path, default=ROOT, help='the checkout whose lock is held (default: this repository)')
    parser.add_argument('--verify', action='store_true', help='be admitted by the owner of the inherited claim and exit')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='-- COMMAND [ARG...] to run under the lock')
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    root = Path(args.root).resolve()
    try:
        if args.verify:
            if command:
                parser.error('--verify takes no command')
            try:
                admission = admit(root)
            except Refusal as exc:
                raise Refusal(f'checkout lock claim is not verified: {exc}; {UNSET_REMEDY}')
            try:
                print(f'ok: admitted by the owner of {LOCK} for {root} (acquisition {admission.nonce[:12]})', file=sys.stderr)
            finally:
                admission.close()
            return 0
        if not command:
            raise Refusal('no command to run under the checkout lock')
        verify_environment()
        with owned(root) as scope:
            return scope.supervise(command)
    except Refusal as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    except OSError as exc:
        print(f'ERROR: checkout lock: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
