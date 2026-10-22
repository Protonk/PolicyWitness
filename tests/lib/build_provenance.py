#!/usr/bin/env python3
"""Build provenance: bounded toolchain observations, the build-directory stamp, fresh mode and the shipped record.

build.sh runs this helper at several steps and keeps the observations of one
build in a session file under Cargo's target directory. The evidence step then
assembles `Contents/Resources/Evidence/provenance.json` from that session and
from the assembled bundle. The record is the tools' reports about the inputs
and outputs of one build: which commands were selected, what they reported
about themselves, what the build directories looked like, what Cargo said
about reusing each shipped target and what the shipped bytes carry. It does
not establish reproducibility, compiler correctness or the history of a
cached output replaced before capture.

Subcommands, in the order build.sh uses them:

  session-start   open the session with the knobs and the git stamp
  stamp-check     validate builddir/pw-toolchain.json against the tools selected now
  fresh-remove    replace the two owned cache areas after path and ownership admission
  cargo-admit     resolve Cargo's selection and child environment; refuse redirected intermediate state
  cargo-judge     record Cargo's per-target reuse judgment and fingerprint observations
  stamp-publish   publish the stamp after a successful fresh setup
  stamp-extend    after compiling: keep the stamp intact, or extend it with a newly discovered Swift compiler
  sdk-check       require every shipped Mach-O's SDK to agree with the selected SDK's version
  output-check    require every output, or every Mach-O an assembled bundle carries, to be a thin arm64 Mach-O for macOS
  worker-identity require the built worker to report the generated identity
  collect         write the record (build-evidence.py imports this)
  inspect         validate an app's record against its manifest and bytes (artifact.py imports this)

Field policy. A required observation is one the comparisons rest on: the SDK
path, version and build, the developer directory, the configured C compiler's
identity, the Swift compiler's identity when the XPC pieces are built, the
selected Rust compiler's identity, and each shipped output's load commands
and hash. A required observation that fails stops the build (exit 2 from the
subcommand that needed it). An optional observation (Xcode's version, Cargo's
fingerprint for a reused unit, a compiler wrapper's identity) that fails is
recorded as unknown with a bounded failure entry and never compares equal to
anything. Every probe has a deadline (PROBE_TIMEOUT seconds) for the whole
run and live caps on stdout and stderr (PROBE_LIMIT bytes unless the caller
names others), both drained while the tool runs; a nonzero exit, empty
output, malformed output, overflow on either stream and a timeout are
distinct failure kinds, and overflow fails even a zero exit. A failed probe's
process group is terminated and must be gone within CLEANUP_TIMEOUT seconds,
which the entry's `cleanup` reports. A failure entry carries the kind, the
stream, the status and byte counts, never the tool's output. A value a
comparison rests on is complete within its declared bound (LINE_LIMIT
characters for an identity, COMMAND_LIMIT words for a configured command,
FLAG_LIMIT flags for Cargo's effective flags, TOOLS_LIMIT build tools per
output) or it is an oversized failure, never a truncated value that could
equal another. Published paths under the home directory start with the
HOME_MARKER; the exact paths stay in the local stamp and session files.

Cargo selection. The compiler, its wrappers and the environment Cargo gives
them are resolved by cargo_config.py, as one Cargo invocation from this
directory resolves them; an unresolvable setting or an effective SDKROOT,
MACOSX_DEPLOYMENT_TARGET or DEVELOPER_DIR that differs from the build's refuses
before Cargo runs. Cargo's judgment for a shipped target is its literal boolean
`fresh` on the one artifact message bound to the binary target, a profile and
the admitted executable; anything else refuses in either mode.

Output target. The shipped executables are thin arm64 Mach-O for macOS
(output_target.py). Cargo builds them for the one triple build.sh passes with
--target, under controller/target/<triple>/release/, while its build scripts
and procedural macros stay under controller/target/release/; fresh mode
replaces both release areas. The stamp records the target the Meson directory
is configured for, from Meson's own introspection rather than a compiler's
default, and reuse refuses another one. The output target describes the
products only: nothing here observes the machine or the processes that built
them, and nothing claims that a build ran natively.

Cargo metadata policy. The reader of Cargo's internal `.fingerprint` files
supports the layout observed with Cargo 1.99: the uplifted executable is a
hard link of (or byte-identical to) exactly one `deps/<name>-<meta>` file, and
`<profile>/.fingerprint/<package>-<meta>/bin-<target>.json` is a JSON object
whose `rustflags` is a list of strings. The hash fields in that object are
opaque: they distinguish units, they do not name a compiler. An ambiguous
association (none or several candidates), a missing file or another shape is
recorded as unavailable, unsupported or malformed, never guessed. Cargo's
`fresh: true` in its artifact message means Cargo reused the output; it is
not this build's fresh mode.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cargo_config  # noqa: E402
import checkout_lock  # noqa: E402
import output_target  # noqa: E402

SCHEMA_VERSION = 3
STAMP_SCHEMA_VERSION = 2
SESSION_SCHEMA_VERSION = 3
STAMP_NAME = 'pw-toolchain.json'
SESSION_NAME = 'pw-build-session.json'
MESSAGES_NAME = 'pw-build-messages.jsonl'
RECORD_PATH = 'Contents/Resources/Evidence/provenance.json'
PROBE_TIMEOUT = 20
PROBE_LIMIT = 64 * 1024
TERM_GRACE = 1
CLEANUP_TIMEOUT = 5
LINE_LIMIT = 200
COMMAND_LIMIT = 8
FLAG_LIMIT = 64
TOOLS_LIMIT = 16
RECORD_LIMIT = 256 * 1024
HOME_MARKER = '<home>'
TRIPLE = output_target.CARGO_TRIPLE
TARGET = 'controller/target'
# Cargo's host units (build scripts, procedural macros) under release/, the shipped executables under <triple>/release/.
RELEASE = 'controller/target/release'
TRIPLE_DIR = f'controller/target/{TRIPLE}'
TRIPLE_RELEASE = f'{TRIPLE_DIR}/release'
BUILDDIR = 'builddir'
FRESH_REMEDY = f'set PW_FRESH_BUILD=1 to replace builddir/, {RELEASE}/ and {TRIPLE_RELEASE}/'
PATH_POLICY = 'the build admits only real directories of this user inside the checkout'
SOURCE_INPUTS = ('meson.build', 'meson.options', 'controller/Cargo.lock', 'Info.plist',
                 'PolicyWitness.entitlements', 'runner/Services/PWRunner/Entitlements.plist')
FIXED_MESON_OPTIONS = ('buildtype', 'optimization', 'debug', 'warning_level', 'werror', 'strip', 'unity',
                       'b_ndebug', 'b_lto', 'b_coverage', 'b_pgo', 'b_bitcode', 'b_pie', 'b_staticpic',
                       'b_lundef', 'b_sanitize', 'c_std', 'c_args', 'c_link_args', 'swift_args',
                       'swift_link_args', 'inspection', 'xpc')
CARGO_SELECTION_ENV = ('RUSTC', 'RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_RUSTC',
                       'CARGO_BUILD_RUSTC_WRAPPER', 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER')
UNRESOLVED_REMEDY = 'the compiler Cargo would select, or the environment it would give it, is unknown'
CARGO_FLAG_ENV = ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_RUSTFLAGS')
CARGO_LAYOUT_ENV = ('CARGO_BUILD_TARGET', 'CARGO_TARGET_DIR', 'CARGO_BUILD_BUILD_DIR', 'CARGO_HOME')
# Caller settings recorded at session start, alongside the witnessed requests.
ALLOWED_ENV = ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD', 'DEVELOPER_DIR', 'MACOSX_DEPLOYMENT_TARGET', 'RUSTFLAGS',
               'PW_VERSION', 'PW_BUILD_NUMBER')
SUBCOMMANDS = ('session-start', 'stamp-check', 'fresh-remove', 'cargo-admit', 'cargo-judge', 'stamp-publish',
               'stamp-extend', 'sdk-check', 'output-check', 'worker-identity', 'inspect')
OUTPUT_STAGES = ('cargo', 'native', 'assembled', 'observer', 'packaging')
CONTROLLER = 'Contents/MacOS/policy-witness'
SERVICE = 'Contents/XPCServices/PWRunner.xpc'
TOP_HELPERS = ('pw-runner-client', 'sandbox-log-observer', 'sbpl-check')
NESTED_HELPERS = ('pw-probe-runner', 'sb_api_validator', 'pw-extension-issuer')
CARGO_TARGETS = {'Contents/MacOS/policy-witness': 'policy-witness',
                 'Contents/MacOS/sandbox-log-observer': 'sandbox-log-observer',
                 'Contents/MacOS/sbpl-check': 'sbpl-check'}


class Refusal(Exception):
    """A condition the build refuses; status 1 is a disagreement, 2 an unavailable observation or admission."""

    def __init__(self, message, status=2):
        super().__init__(message)
        self.status = status


# ---- bounded probes ---------------------------------------------------------------

def redact(value, home=None):
    """A string with every occurrence of the home directory replaced by the marker, including inside URLs; other strings unchanged."""
    home = home if home is not None else os.environ.get('HOME', '')
    if isinstance(value, list):
        return [redact(v, home) for v in value]
    if not isinstance(value, str) or not home or home == '/':
        return value
    if value == home:
        return HOME_MARKER
    return value.replace(home + '/', HOME_MARKER + '/')


def first_line(text):
    """The first nonblank line, stripped, or ''."""
    return text.splitlines()[0].strip() if text.strip() else ''


def oversized(value, limit=LINE_LIMIT):
    """Whether a string, or any string in a list, exceeds its declared bound; such a value is never truncated to fit."""
    if isinstance(value, list):
        return any(oversized(item, limit) for item in value)
    return isinstance(value, str) and len(value) > limit


def probe(argv, *, cwd=None, env=None, timeout=PROBE_TIMEOUT, limit=PROBE_LIMIT, stderr_limit=PROBE_LIMIT):
    """Run a tool with a deadline and live caps on both streams; its output and first line, or a bounded failure.

    Both pipes are drained concurrently as the tool runs, and only stdout is kept,
    never beyond its cap. More than the cap on either stream is an overflow and a
    failed observation even when the tool exits zero. The deadline covers the
    whole run, including a descendant that keeps a pipe open after the leader
    exits. On overflow or deadline the tool's process group is sent SIGTERM, then
    SIGKILL after TERM_GRACE seconds, the leader is reaped, and the group must be
    gone within CLEANUP_TIMEOUT seconds; `cleanup` says whether it was. A failure
    entry carries the kind, the stream that overflowed, the status and the byte
    counts, never the tool's output."""
    argv = [str(a) for a in argv]
    record = dict(status='failed', kind='launch_failed', argv=redact(argv), returncode=None, stdout_bytes=0, stderr_bytes=0)
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
    except OSError:
        return record
    deadline = time.monotonic() + timeout
    streams = {process.stdout.fileno(): 'stdout', process.stderr.fileno(): 'stderr'}
    caps = dict(stdout=limit, stderr=stderr_limit)
    counts = dict(stdout=0, stderr=0)
    kept = bytearray()
    failure = None
    selector = selectors.DefaultSelector()
    try:
        for fd in streams:
            os.set_blocking(fd, False)
            selector.register(fd, selectors.EVENT_READ)
        while selector.get_map() and failure is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failure = ('timeout', None)
                break
            for key, _ in selector.select(min(remaining, 0.25)):
                try:
                    chunk = os.read(key.fd, 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fd)
                    continue
                name = streams[key.fd]
                counts[name] += len(chunk)
                if name == 'stdout' and len(kept) <= limit:
                    kept += chunk[:limit + 1 - len(kept)]
                if counts[name] > caps[name]:
                    failure = ('output_overflow', name)
                    break
        if failure is None:
            try:
                process.wait(timeout=max(0.0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                failure = ('timeout', None)
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
    record.update(stdout_bytes=counts['stdout'], stderr_bytes=counts['stderr'])
    if failure is not None:
        record['cleanup'] = terminate_group(process)
        record.update(kind=failure[0], returncode=process.returncode)
        if failure[1]:
            record['stream'] = failure[1]
        return record
    record['returncode'] = process.returncode
    if process.returncode != 0:
        record['kind'] = 'nonzero_exit'
        return record
    text = bytes(kept).decode('utf-8', errors='replace')
    if not text.strip():
        record['kind'] = 'empty_output'
        return record
    return dict(status='ok', argv=redact(argv), text=text, line=first_line(text), stdout_bytes=counts['stdout'],
                stderr_bytes=counts['stderr'])


def terminate_group(process):
    """Stop a probe's process group within a bound: 'complete' when the leader is reaped and no member remains."""
    pgid = process.pid
    deadline = time.monotonic() + CLEANUP_TIMEOUT
    for signum, grace in ((signal.SIGTERM, TERM_GRACE), (signal.SIGKILL, CLEANUP_TIMEOUT)):
        try:
            os.killpg(pgid, signum)
        except ProcessLookupError:
            break
        except PermissionError:
            pass  # only zombies remain; group_gone reaps the leader
        if group_gone(process, pgid, min(grace, max(0, deadline - time.monotonic()))):
            return 'complete'
    return 'complete' if group_gone(process, pgid, 0) else 'failed'


def group_gone(process, pgid, timeout):
    """Reap the leader and wait for the group's other members to exit, for at most timeout seconds.

    macOS answers EPERM, not ESRCH, while the only members left are zombies
    awaiting their parent, so that answer means not yet, never gone."""
    deadline = time.monotonic() + timeout
    while True:
        process.poll()
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            if process.poll() is not None:
                return True
        except PermissionError:
            pass
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.02)


def failed(record, kind='malformed_output'):
    """A probe record turned into a bounded failure of the given kind."""
    return dict(status='failed', kind=kind, argv=record.get('argv'), returncode=record.get('returncode', 0),
                stdout_bytes=record.get('stdout_bytes', len(record.get('text', '').encode())), stderr_bytes=record.get('stderr_bytes', 0))


def version_line(record, pattern=r'\d'):
    """A probe's first line as a version identity, complete within LINE_LIMIT; otherwise a malformed or oversized failure."""
    if record['status'] != 'ok':
        return record
    if oversized(record['line']):
        return failed(record, 'oversized_output')
    if not re.search(pattern, record['line']):
        return failed(record)
    return dict(status='ok', line=record['line'])


def required(observation, field):
    if not isinstance(observation, dict) or observation.get('status') != 'ok':
        kind = observation.get('kind', 'unknown') if isinstance(observation, dict) else 'unknown'
        raise Refusal(f'required toolchain observation failed: {field} ({kind}); the record cannot establish compatibility without it', 2)
    return observation


def sha256_file(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


# ---- ownership, path admission and the session ------------------------------------------

class BuildPaths:
    """The build's cache paths, admitted under the verified hold before anything is written or inspected through them.

    Every component of builddir/, controller/target/, its release/, its
    <triple>/ and that directory's release/ below the checkout root must be a
    real directory of this user, or absent, and the session destination an
    absent path or a regular file of this user with one link. Each admitted directory is held open; writes and removals are made
    relative to those descriptors, and each first rechecks that the path from the
    root still names the directory admitted, because the checkout lock excludes
    cooperating builds but does not make a checked pathname immutable. A missing
    controller/target/ is created only beneath the admitted controller/."""

    def __init__(self, root, *, create_target=False):
        self.root = Path(root).resolve()
        self.fds, self.identity, self.created = {}, {}, []
        self.root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            self.admit('controller', required=True)
            self.admit(TARGET)
            if TARGET in self.fds:
                self.admit_target_children()
            self.admit(BUILDDIR)
            # Admit every existing component before creating even an empty
            # cache parent. A refused sibling must leave the checkout intact.
            if create_target and TARGET not in self.fds:
                self.recheck('controller')
                self.admit(TARGET, create=True)
                self.admit_target_children()
        except BaseException:
            self.close()
            raise

    def admit_target_children(self):
        self.admit(RELEASE)
        self.admit(TRIPLE_DIR)
        if TRIPLE_DIR in self.fds:
            self.admit(TRIPLE_RELEASE)
        self.admit_file(TARGET, SESSION_NAME)

    def parent(self, relative):
        parent = str(PurePosixPath(relative).parent)
        return (self.root_fd, '') if parent == '.' else (self.fds[parent], parent)

    def unsafe(self, relative, why):
        return Refusal(f'{self.root / relative} {why}; {PATH_POLICY} (nothing was written or removed)', 2)

    def check(self, relative, info):
        if stat.S_ISLNK(info.st_mode):
            raise self.unsafe(relative, 'is a symlink')
        if not stat.S_ISDIR(info.st_mode):
            raise self.unsafe(relative, 'is not a directory')
        if info.st_uid != os.getuid():
            raise self.unsafe(relative, f'is owned by uid {info.st_uid}, not this user')

    def admit(self, relative, *, required=False, create=False):
        parent_fd, _ = self.parent(relative)
        name = PurePosixPath(relative).name
        try:
            info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            if required:
                raise self.unsafe(relative, 'is missing')
            if not create:
                return
            os.mkdir(name, 0o755, dir_fd=parent_fd)
            self.created.append(relative)
            info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        self.check(relative, info)
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        held = os.fstat(fd)
        if (held.st_dev, held.st_ino) != (info.st_dev, info.st_ino):
            os.close(fd)
            raise self.unsafe(relative, 'changed during admission')
        self.fds[relative], self.identity[relative] = fd, (info.st_dev, info.st_ino)

    def admit_file(self, directory, name):
        """A destination this build replaces: absent, or a regular file of this user with one link."""
        try:
            info = os.stat(name, dir_fd=self.fds[directory], follow_symlinks=False)
        except FileNotFoundError:
            return
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise Refusal(f'{self.root / directory / name} is not a regular file of this user with one link; '
                          f'the destination is unsafe and {PATH_POLICY} (nothing was written or removed)', 2)

    def present(self, relative):
        return relative in self.fds

    def recheck(self, relative):
        """Every admitted component from the root down to relative still names the directory admitted."""
        parts = PurePosixPath(relative).parts
        for index in range(1, len(parts) + 1):
            component = str(PurePosixPath(*parts[:index]))
            parent_fd, _ = self.parent(component)
            try:
                info = os.stat(parts[index - 1], dir_fd=parent_fd, follow_symlinks=False)
            except OSError:
                info = None
            if info is None or (info.st_dev, info.st_ino) != self.identity.get(component) or not stat.S_ISDIR(info.st_mode):
                raise self.unsafe(component, 'was replaced after admission')

    def write_json(self, directory, name, value):
        """Replace directory/name atomically through the admitted directory's descriptor."""
        self.recheck(directory)
        self.admit_file(directory, name)
        dir_fd = self.fds[directory]
        temporary = f'.{name}-{uuid.uuid4().hex}'
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dir_fd)
        try:
            with os.fdopen(fd, 'w') as stream:
                stream.write(json.dumps(value, indent=2, sort_keys=True) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            temporary = None
            os.fsync(dir_fd)
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary, dir_fd=dir_fd)
                except OSError:
                    pass

    def read_text(self, directory, name):
        """A file's text read through the admitted directory, not following a link at the leaf."""
        self.recheck(directory)
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.fds[directory])
        with os.fdopen(fd) as stream:
            return stream.read()

    def remove(self, relative, failures):
        """Remove an admitted directory and everything below it through descriptors; failures are collected, not raised."""
        self.recheck(relative)
        fd = self.fds.pop(relative)
        try:
            remove_contents(fd, self.root / relative, failures)
        finally:
            os.close(fd)
        parent_fd, _ = self.parent(relative)
        name = PurePosixPath(relative).name
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (info.st_dev, info.st_ino) != self.identity[relative]:
            raise self.unsafe(relative, 'was replaced during removal')
        if not failures:
            try:
                os.rmdir(name, dir_fd=parent_fd)
            except OSError:
                failures.append(str(self.root / relative))

    def close(self):
        for fd in self.fds.values():
            os.close(fd)
        self.fds = {}
        if self.root_fd is not None:
            os.close(self.root_fd)
            self.root_fd = None


def remove_contents(dir_fd, path, failures):
    """Unlink every entry below an open directory without following a link; failed paths are appended."""
    with os.scandir(dir_fd) as entries:
        names = [entry.name for entry in entries]
    for name in names:
        try:
            info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        except FileNotFoundError:
            continue
        if stat.S_ISDIR(info.st_mode):
            try:
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=dir_fd)
            except OSError:
                failures.append(str(path / name))
                continue
            try:
                held = os.fstat(child)
                if (held.st_dev, held.st_ino) != (info.st_dev, info.st_ino):
                    failures.append(str(path / name))
                    continue
                remove_contents(child, path / name, failures)
            finally:
                os.close(child)
            try:
                os.rmdir(name, dir_fd=dir_fd)
            except OSError:
                failures.append(str(path / name))
        else:
            try:
                os.unlink(name, dir_fd=dir_fd)
            except OSError:
                failures.append(str(path / name))


class BuildState:
    """One helper invocation's verified hold, admitted paths and the session it reads and replaces."""

    def __init__(self, root, admission, paths, session):
        self.root, self.admission, self.paths, self.session = root, admission, paths, session

    def save(self):
        self.paths.write_json(TARGET, SESSION_NAME, self.session)


def validate_session(session, nonce):
    if not isinstance(session, dict) or session.get('schema_version') != SESSION_SCHEMA_VERSION:
        raise Refusal('build session has an unsupported shape; it was not opened by this build', 2)
    recorded = session.get('lock_nonce')
    if not isinstance(recorded, str) or not checkout_lock.NONCE_RE.fullmatch(recorded) or recorded != nonce:
        raise Refusal('build session belongs to another checkout lock hold; the session is stale', 2)
    return session


@contextmanager
def build_scope(root, *, create_target=False, session=True):
    """A helper's verified hold and admitted paths, with the current session unless it is about to be opened.

    Without a live owner's handoff, a missing or malformed session nonce or a
    session from another hold, nothing is written: every helper that creates or
    updates a session, removes a cache or publishes or extends a stamp enters here."""
    root = Path(root).resolve()
    try:
        admission = checkout_lock.admit(root)
    except checkout_lock.Refusal as exc:
        raise Refusal(f'checkout lock claim is not verified: {exc}; build helpers mutate only under an owned build', 2)
    try:
        paths = BuildPaths(root, create_target=create_target)
        try:
            current = None
            if session:
                if not paths.present(TARGET):
                    raise Refusal(f'build session is not readable: {root / TARGET / SESSION_NAME} (no {TARGET}/)', 2)
                try:
                    current = json.loads(paths.read_text(TARGET, SESSION_NAME))
                except (OSError, ValueError) as exc:
                    raise Refusal(f'build session is not readable: {root / TARGET / SESSION_NAME}: {exc}', 2)
                validate_session(current, admission.nonce)
            yield BuildState(root, admission, paths, current)
        finally:
            paths.close()
    finally:
        admission.close()


def session_start(args):
    # Check before BuildPaths can create controller/target or touch a session.
    try:
        requests = checkout_lock.verify_environment(sdk_request=(args.sdk_request_state, args.sdk_request_value))
    except checkout_lock.Refusal as exc:
        raise Refusal(str(exc), 2)
    with build_scope(args.root, create_target=True, session=False) as state:
        knobs = {}
        for item in args.knob:
            name, _, value = item.partition('=')
            knobs[name] = value
        state.session = dict(schema_version=SESSION_SCHEMA_VERSION, lock_nonce=state.admission.nonce,
                             started_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), root=str(state.root),
                             knobs=knobs, stamp=dict(describe=args.describe, commit=args.commit, version=args.version,
                                                     build_number=args.build_number, dirty=args.describe.endswith('-dirty')),
                             sdk_source='caller' if requests['SDKROOT'].get('value') else 'default',
                             output_target=dict(output_target.DECLARED),
                             requests=requests,
                             admission=dict(created=state.paths.created),
                             environment={name: os.environ.get(name) for name in ALLOWED_ENV if name in os.environ})
        state.save()
    print(f'ok: build session {state.root / TARGET / SESSION_NAME}')
    return 0


# ---- toolchain observations ------------------------------------------------------------

def developer_dir_observation(env):
    if env.get('DEVELOPER_DIR'):
        return dict(status='ok', value=env['DEVELOPER_DIR'], source='DEVELOPER_DIR')
    found = version_line(probe(['/usr/bin/xcode-select', '-p'], env=env), pattern=r'^/')
    if found['status'] != 'ok':
        return dict(found, source='xcode-select')
    return dict(status='ok', value=found['line'], source='xcode-select')


def sdk_observation(env):
    """The SDK as xcrun resolves it: the one SDKROOT names when the build has selected it, else the macosx default."""
    request = env.get('SDKROOT') or 'macosx'
    out = {}
    for name, flag, pattern in (('path', '--show-sdk-path', r'^/'), ('version', '--show-sdk-version', r'^\d+(\.\d+)*$'),
                                ('build', '--show-sdk-build-version', r'^[0-9A-Za-z]+$')):
        out[name] = version_line(probe(['/usr/bin/xcrun', '--sdk', request, flag], env=env), pattern)
    return out


def xcode_observation(env):
    found = probe(['/usr/bin/xcodebuild', '-version'], env=env)
    if found['status'] != 'ok':
        return dict(status='unknown', reason=found['kind'], returncode=found.get('returncode'))
    lines = [line.strip() for line in found['text'].splitlines() if line.strip()][:2]
    version = next((line[len('Xcode '):] for line in lines if line.startswith('Xcode ')), None)
    build = next((line[len('Build version '):] for line in lines if line.startswith('Build version ')), None)
    if not version or not build:
        return dict(status='unknown', reason='malformed_output')
    if oversized([version, build]):
        return dict(status='unknown', reason='oversized_output')
    return dict(status='ok', version=version, build=build)


def read_compilers(builddir):
    """Meson's record of the configured host compilers, or None when the directory has none."""
    path = Path(builddir) / 'meson-info/intro-compilers.json'
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    host = data.get('host') if isinstance(data, dict) else None
    if not isinstance(host, dict):
        return None
    out = {}
    for language in ('c', 'swift'):
        entry = host.get(language)
        if not isinstance(entry, dict) or not isinstance(entry.get('exelist'), list) or not entry['exelist']:
            continue
        command = [str(c) for c in entry['exelist']]
        facts = dict(id=str(entry.get('id', '')), version=str(entry.get('version', '')),
                     full_version=None if entry.get('full_version') is None else str(entry['full_version']))
        if len(command) > COMMAND_LIMIT or oversized(command) or oversized([v for v in facts.values() if v is not None]):
            # Never a prefix that could equal another configuration's: the command is unknown.
            out[language] = dict(command=None, id=None, version=None, full_version=None, oversized=True)
            continue
        out[language] = dict(command=command, **facts)
    return out


def compiler_observation(command, builddir, env):
    """The configured command probed for its identity in the build directory's context."""
    if command is None:
        return dict(status='failed', kind='oversized_output', command=None)
    found = version_line(probe([*command, '--version'], cwd=str(builddir) if Path(builddir).is_dir() else None, env=env))
    if found['status'] != 'ok':
        return dict(found, command=command)
    return dict(status='ok', command=command, identity=found['line'])


def invocation_environment():
    """The environment build.sh gives Cargo, inherited unchanged by this direct Python."""
    return dict(os.environ)


def cargo_resolution(env, cwd=None):
    """Cargo's configuration and launcher for this invocation, resolved, with the build's policy for the compiler's inputs."""
    cwd = cwd or os.getcwd()
    try:
        resolution = cargo_config.resolve(cwd, env, probe=probe, target=TRIPLE)
    except cargo_config.Unresolved as exc:
        raise Refusal(f'Cargo configuration cannot be resolved: {exc}; {UNRESOLVED_REMEDY}', 2)
    for name, effective, selected in cargo_config.conflicts(resolution, env):
        raise Refusal(f"Cargo's [env] gives the compiler {name}={redact(effective)!r}, but the build selected {redact(selected)!r}; "
                      f'the effective setting conflicts with build policy', 1)
    return resolution


def rustc_observation(manifest_dir, env, cwd=None, resolution=None):
    """The compiler Cargo will run, resolved through Cargo's configuration and launcher, probed in Cargo's child environment
    and working directory (the workspace root), without its wrappers."""
    resolution = resolution or cargo_resolution(env, cwd)
    home = env.get('HOME', '')
    rustc = resolution['programs']['rustc']
    command, source = rustc['command'], rustc['source']
    selection = cargo_config.summary(resolution, home)
    out = dict(selection_environment={name: redact(env[name]) for name in CARGO_SELECTION_ENV if name in env}, selection=selection)
    found = probe([command, '-vV'], cwd=str(manifest_dir), env=resolution['child'])
    if found['status'] != 'ok':
        out.update(found, command=redact(command), source=source)
        return out
    fields = dict(re.findall(r'^(release|commit-hash|host|binary|LLVM version): (.+)$', found['text'], re.M))
    if 'release' not in fields or 'host' not in fields:
        out.update(failed(found), command=redact(command), source=source)
        return out
    reported = dict(release=fields['release'], commit_hash=fields.get('commit-hash', ''), host=fields['host'],
                    llvm_version=fields.get('LLVM version', ''))
    if oversized([found['line'], *reported.values()]):
        out.update(failed(found, 'oversized_output'), command=redact(command), source=source)
        return out
    out.update(status='ok', command=redact(command), exact_command=command, source=source, identity=found['line'], **reported)
    wrappers = {}
    for role in ('wrapper', 'workspace_wrapper'):
        entry = resolution['programs'][role]
        if entry.get('command'):
            wrapper = dict(source=entry['source'], command=redact(entry['command']))
            if Path(entry['command']).is_file():
                wrapper['sha256'] = sha256_file(entry['command'])
            wrappers[role] = wrapper
    out['wrappers'] = wrappers
    return out


def tool_observation(name, env, pattern=r'\d'):
    path = shutil.which(name, path=env.get('PATH'))
    if not path:
        return dict(status='failed', kind='launch_failed', command=None)
    found = version_line(probe([path, '--version'], env=env), pattern)
    if found['status'] != 'ok':
        return dict(found, command=redact(path))
    return dict(status='ok', command=redact(path), version=found['line'])


def python_observation(env):
    """The pinned interpreter the resolver selected and exported: its path, real path and the version its keg names,
    beside the version one isolated probe reports. An environment without the resolver's exports is a failed observation."""
    path, real, keg_version = env.get('PW_PYTHON'), env.get('PW_PYTHON_REALPATH'), env.get('PW_PYTHON_VERSION')
    if not path or not real or not keg_version:
        return dict(status='failed', kind='launch_failed', command=None)
    found = version_line(probe([path, '-I', '-S', '-B', '-c', 'import sys; print("%d.%d.%d" % sys.version_info[:3])'], env=env),
                         r'^\d+\.\d+\.\d+$')
    if found['status'] != 'ok':
        return dict(found, command=redact(path))
    return dict(status='ok', command=redact(path), realpath=redact(real), keg_version=keg_version, version=found['line'])


def observe_toolchain(builddir, manifest_dir, env, *, xpc, compilers=None):
    """env is the environment build.sh gives Cargo and the compilers (invocation_environment)."""
    """Every toolchain observation the stamp and the record use; compilers come from the directory or the stamp."""
    if compilers is None:
        compilers = read_compilers(builddir) or {}
    observed = {}
    for language, entry in compilers.items():
        observed[language] = dict(configured=entry, observed=compiler_observation(entry['command'], builddir, env))
    return dict(developer_dir=developer_dir_observation(env), sdk=sdk_observation(env), xcode=xcode_observation(env),
                compilers=observed, rustc=rustc_observation(manifest_dir, env),
                cargo=tool_observation('cargo', env), meson=tool_observation('meson', env), ninja=tool_observation('ninja', env),
                python=python_observation(env), xpc=bool(xpc))


def compatibility_fields(observation, *, xpc):
    """The comparable fields of an observation, as (field, value) with a failed observation as None."""
    fields = {}

    def put(name, entry, key='value'):
        fields[name] = entry.get(key) if isinstance(entry, dict) and entry.get('status') == 'ok' else None

    put('developer_dir', observation['developer_dir'])
    for part in ('path', 'version', 'build'):
        put(f'sdk.{part}', observation['sdk'][part], 'line')
    languages = ['c'] + (['swift'] if xpc else [])
    for language in languages:
        entry = observation['compilers'].get(language)
        if entry is None:
            fields[f'compilers.{language}.command'] = None
            fields[f'compilers.{language}.identity'] = None
            continue
        fields[f'compilers.{language}.command'] = entry['configured']['command']
        put(f'compilers.{language}.identity', entry['observed'], 'identity')
    put('rustc.command', observation['rustc'], 'exact_command')
    put('rustc.identity', observation['rustc'], 'identity')
    wrappers = observation['rustc'].get('wrappers', {}) if observation['rustc'].get('status') == 'ok' else None
    fields['rustc.wrappers'] = None if wrappers is None else {k: dict(command=v['command'], sha256=v.get('sha256')) for k, v in wrappers.items()}
    return fields


# ---- the stamp -----------------------------------------------------------------------------

def stamp_path(builddir):
    return Path(builddir) / STAMP_NAME


def read_stamp(builddir):
    """The stamp, or a Refusal naming why it cannot be used."""
    path = stamp_path(builddir)
    if path.is_symlink():
        raise Refusal(f'{path} is a symlink; a stamp is a regular file', 2)
    if not path.is_file():
        raise Refusal(f'{Path(builddir).name}/ is configured but has no {STAMP_NAME}; its toolchain is unknown and is not adopted: {FRESH_REMEDY}', 2)
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise Refusal(f'{path} is malformed ({exc.__class__.__name__}); its toolchain is unknown and is not adopted: {FRESH_REMEDY}', 2)
    if not isinstance(data, dict) or data.get('schema_version') != STAMP_SCHEMA_VERSION:
        raise Refusal(f'{path} has an unsupported schema; its toolchain is unknown and is not adopted: {FRESH_REMEDY}', 2)
    fields = data.get('fields')
    scope = data.get('scope')
    if not isinstance(fields, dict) or not isinstance(scope, dict) or 'xpc' not in scope or not isinstance(data.get('source_dir'), str):
        raise Refusal(f'{path} lacks its fields or scope; its toolchain is unknown and is not adopted: {FRESH_REMEDY}', 2)
    if any(name not in fields for name in output_fields(xpc=scope.get('xpc') is True)):
        raise Refusal(f'{path} lacks its output target fields; the target the directory was configured for is unknown and is not adopted: '
                      f'{FRESH_REMEDY}', 2)
    return data


# ---- the output target a configured directory carries -------------------------------------------------------

OUTPUT_FIELDS = ('output.system', 'output.cpu_family', 'output.c_arch', 'output.link_arch', 'output.cargo_triple')


def output_fields(*, xpc):
    return OUTPUT_FIELDS + (('output.swift_target',) if xpc else ())


def selections(parameters, flag):
    """The values that follow each occurrence of flag in one argument list, or ['(none)'] when it names none."""
    found = [parameters[index + 1] for index, item in enumerate(parameters[:-1]) if item == flag]
    return found or ['(none)']


def configured_output(builddir, *, xpc):
    """The output target a configured Meson directory carries, from Meson's own introspection, and its machines.

    The fields are Meson's host machine (where the products run) and the
    architecture each target selects with its effective arguments: clang's
    -arch at C compile and executable link, swiftc's -target. A compiler's
    default target, which its version output names, is never consulted. The
    machines name Meson's host and build machines apart; the build machine is
    where Meson reported compiling, a toolchain fact, and is not constrained.
    The Cargo triple is the one this build passes; it belongs to the same
    contract. Unreadable introspection refuses."""
    builddir = Path(builddir)
    try:
        machines = json.loads((builddir / 'meson-info/intro-machines.json').read_text())
        targets = json.loads((builddir / 'meson-info/intro-targets.json').read_text())
        found = dict(c=set(), link=set(), swift=set())
        for target in targets:
            for source in target['target_sources']:
                parameters = [str(item) for item in source.get('parameters') or []]
                if source.get('language') == 'c':
                    found['c'].update(selections(parameters, '-arch'))
                elif source.get('language') == 'swift':
                    found['swift'].update(selections(parameters, '-target'))
                elif source.get('language') is None and target['type'] == 'executable':
                    found['link'].update(selections(parameters, '-arch'))
        named = {role: dict(system=str(machines[role]['system']), cpu_family=str(machines[role]['cpu_family'])) for role in ('host', 'build')}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Refusal(f'required toolchain observation failed: the configured output target ({exc.__class__.__name__} reading '
                      f'meson-info); an unobserved field cannot establish compatibility with {STAMP_NAME}: {FRESH_REMEDY}', 2)
    fields = {'output.system': named['host']['system'], 'output.cpu_family': named['host']['cpu_family'],
              'output.c_arch': sorted(found['c']), 'output.link_arch': sorted(found['link']), 'output.cargo_triple': TRIPLE}
    if xpc:
        fields['output.swift_target'] = sorted(found['swift'])
    return fields, named


def output_contract_problems(fields, *, xpc):
    """The output fields that depart from the output target, as (field, recorded, required), in field order."""
    required = {'output.system': output_target.MESON_HOST['system'], 'output.cpu_family': output_target.MESON_HOST['cpu_family'],
                'output.c_arch': [output_target.CLANG_ARCH], 'output.link_arch': [output_target.CLANG_ARCH], 'output.cargo_triple': TRIPLE}
    out = [(name, fields.get(name), value) for name, value in required.items() if fields.get(name) != value]
    if xpc:
        swift = fields.get('output.swift_target')
        if not (isinstance(swift, list) and len(swift) == 1 and isinstance(swift[0], str) and output_target.SWIFT_TARGET.fullmatch(swift[0])):
            out.append(('output.swift_target', swift, ['arm64-apple-macosx<minimum>']))
    return out


def described(stamp_fields, configured, names):
    """The first output field the stamp records differently from the directory's configuration, or None."""
    for name in names:
        if stamp_fields.get(name) != configured.get(name):
            return name
    return None


def stamp_record(fields, *, xpc, source_dir, published_at=None, extended_at=None):
    return dict(schema_version=STAMP_SCHEMA_VERSION, scope=dict(xpc=bool(xpc)), source_dir=str(source_dir),
                published_at=published_at or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                extended_at=extended_at, fields=fields)


def compare_fields(stamped, current, names):
    """The first differing field, or None; a value absent on either side is a difference, never equality."""
    def unavailable(value):
        return value is None or (isinstance(value, dict) and any(unavailable(v) for v in value.values()))
    for name in names:
        if unavailable(stamped.get(name)) or unavailable(current.get(name)):
            return name, stamped.get(name), current.get(name), 'unavailable'
        if stamped[name] != current[name]:
            return name, stamped[name], current[name], 'changed'
    return None


def stamp_check(args):
    """A configured directory may be reused only under the toolchain its stamp records."""
    with build_scope(args.root) as state:
        return stamp_check_admitted(state, args.xpc == '1')


def stamp_check_admitted(state, xpc):
    session, root = state.session, state.root
    builddir = root / BUILDDIR
    env = dict(os.environ)
    configured = state.paths.present(BUILDDIR) and (builddir / 'build.ninja').is_file()
    session['builddir'] = dict(configured_before=configured, stamp_state=None, fresh_replaced=False)
    if not configured:
        if state.paths.present(BUILDDIR) and os.path.lexists(stamp_path(builddir)):
            raise Refusal(f'{builddir.name}/ holds {STAMP_NAME} but no configuration; the directory is in an unknown state: {FRESH_REMEDY}', 2)
        session['builddir']['stamp_state'] = 'absent'
        state.save()
        print(f'ok: {builddir.name}/ is not configured; a fresh setup will publish its stamp')
        return 0
    stamp = read_stamp(builddir)
    if Path(stamp['source_dir']).resolve() != root:
        raise Refusal(f'{STAMP_NAME} describes a build directory for {stamp["source_dir"]}, not this checkout: {FRESH_REMEDY}', 2)
    # The target first: a directory configured for any other output is not reused, whatever its toolchain.
    target = output_contract_problems(stamp['fields'], xpc=stamp['scope'].get('xpc') is True)
    if target:
        name, recorded, required = target[0]
        raise Refusal(f'builddir/ is configured for output {name} = {redact(recorded)!r}, but the output target requires {required!r}; '
                      f'a directory configured for another target cannot be reused: {FRESH_REMEDY}', 1)
    recorded = read_compilers(builddir) or {}
    for language, entry in recorded.items():
        if entry.get('oversized'):
            raise Refusal(f'required toolchain observation failed: compilers.{language}.command (oversized_output); an unobserved field '
                          f'cannot establish compatibility with {STAMP_NAME}: {FRESH_REMEDY}', 2)
    stamped_commands = {language: stamp['fields'].get(f'compilers.{language}.command') for language in ('c', 'swift')}
    if 'c' not in recorded or stamped_commands['c'] != recorded['c']['command']:
        raise Refusal(f"{STAMP_NAME} names C compiler {stamped_commands['c']} but the directory records {recorded.get('c', {}).get('command')}; "
                      f'the stamp does not describe this directory: {FRESH_REMEDY}', 2)
    # Probe the stamped commands, not a rediscovery: the question is whether the recorded selection still resolves the same way.
    compilers = {'c': recorded['c']}
    swift_applicable = xpc and stamp['scope'].get('xpc') is True
    if swift_applicable:
        if 'swift' not in recorded or stamped_commands['swift'] != recorded['swift']['command']:
            raise Refusal(f"{STAMP_NAME} names Swift compiler {stamped_commands['swift']} but the directory records "
                          f"{recorded.get('swift', {}).get('command')}; the stamp does not describe this directory: {FRESH_REMEDY}", 2)
        compilers['swift'] = recorded['swift']
    # The Swift target is compared only while the directory is configured with the XPC pieces: a partial build
    # reconfigures it without them, and the compile that enables them again regenerates the target, which stamp-extend
    # compares with the stamp after compiling.
    swift_configured = swift_applicable and meson_options(builddir).get('values', {}).get('xpc') is True
    configured, _ = configured_output(builddir, xpc=swift_configured)
    departed = described(stamp['fields'], configured, output_fields(xpc=swift_configured))
    if departed is not None:
        raise Refusal(f'{STAMP_NAME} records {departed} = {redact(stamp["fields"].get(departed))!r} but the directory is configured with '
                      f'{redact(configured.get(departed))!r}; the stamp does not describe this directory: {FRESH_REMEDY}', 2)
    observation = observe_toolchain(builddir, root / 'controller', invocation_environment(), xpc=swift_applicable, compilers=compilers)
    current = compatibility_fields(observation, xpc=swift_applicable)
    names = ['developer_dir', 'sdk.path', 'sdk.version', 'sdk.build', 'compilers.c.command', 'compilers.c.identity',
             'rustc.command', 'rustc.identity', 'rustc.wrappers']
    if swift_applicable:
        names += ['compilers.swift.command', 'compilers.swift.identity']
    for name in names:
        if current.get(name) is None:
            source = name.split('.')[0]
            kind = 'unavailable'
            entry = observation.get(source)
            if name.startswith('compilers.'):
                entry = observation['compilers'].get(name.split('.')[1], {}).get('observed')
            elif name.startswith('sdk.'):
                entry = observation['sdk'].get(name.split('.')[1])
            if isinstance(entry, dict):
                kind = entry.get('kind', kind)
            raise Refusal(f'required toolchain observation failed: {name} ({kind}); an unobserved field cannot establish '
                          f'compatibility with {STAMP_NAME}: {FRESH_REMEDY}', 2)
    difference = compare_fields(stamp['fields'], current, names)
    if difference is not None:
        name, before, now, kind = difference
        raise Refusal(f'builddir/ was configured with {name} = {redact(before)!r}, but the selected toolchain now has '
                      f'{redact(now)!r}; a changed toolchain cannot reuse this directory: {FRESH_REMEDY}', 1)
    session['builddir'].update(stamp_state='validated', stamp_scope=stamp['scope'], swift_newly_applicable=bool(xpc and not swift_applicable))
    session['toolchain'] = observation
    state.save()
    print(f'ok: {STAMP_NAME} agrees with the selected toolchain ({len(names)} fields) and the output target '
          f'({len(output_fields(xpc=swift_applicable))} fields)')
    return 0


def stamp_publish(args):
    """After a fresh setup: publish the directory's stamp from the toolchain selected now."""
    with build_scope(args.root) as state:
        return stamp_publish_admitted(state)


def stamp_publish_admitted(state):
    session, root = state.session, state.root
    builddir = root / BUILDDIR
    if not state.paths.present(BUILDDIR) or not (builddir / 'build.ninja').is_file():
        raise Refusal(f'{builddir.name}/ has no configuration to stamp', 2)
    if os.path.lexists(stamp_path(builddir)):
        raise Refusal(f'{builddir.name}/ already holds {STAMP_NAME}; a fresh setup publishes into a directory without one', 2)
    compilers = read_compilers(builddir)
    if not compilers or 'c' not in compilers:
        raise Refusal(f'{builddir.name}/ records no C compiler after setup', 2)
    xpc = 'swift' in compilers
    observation = observe_toolchain(builddir, root / 'controller', invocation_environment(), xpc=xpc, compilers=compilers)
    fields = compatibility_fields(observation, xpc=xpc)
    for name, value in fields.items():
        if value is None:
            raise Refusal(f'required toolchain observation failed: {name}; a stamp never records an unknown value', 2)
    fields.update(configured_output(builddir, xpc=xpc)[0])
    state.paths.write_json(BUILDDIR, STAMP_NAME, stamp_record(fields, xpc=xpc, source_dir=root))
    session.setdefault('builddir', {}).update(stamp_state='published', stamp_scope=dict(xpc=xpc), swift_newly_applicable=False)
    session['toolchain'] = observation
    state.save()
    print(f'ok: published {STAMP_NAME} ({len(fields)} fields; Swift {"included" if xpc else "not configured"})')
    return 0


def stamp_extend(args):
    """After compiling: the stamp still describes the directory; a Swift compiler discovered by this build extends it."""
    with build_scope(args.root) as scope:
        return stamp_extend_admitted(scope, args.xpc == '1')


def stamp_extend_admitted(scope, xpc):
    session, root = scope.session, scope.root
    builddir = root / BUILDDIR
    if not scope.paths.present(BUILDDIR):
        raise Refusal(f'{builddir.name}/ is absent after compiling; there is no stamp to keep', 2)
    stamp = read_stamp(builddir)
    compilers = read_compilers(builddir) or {}
    if 'c' not in compilers or stamp['fields'].get('compilers.c.command') != compilers['c']['command']:
        raise Refusal(f'{STAMP_NAME} no longer describes the C compiler the directory records: {FRESH_REMEDY}', 2)
    if xpc and 'swift' not in compilers:
        raise Refusal(f'{builddir.name}/ records no Swift compiler although the XPC pieces were compiled', 2)
    configured, machines = configured_output(builddir, xpc=xpc)
    swift_stamped = stamp['scope'].get('xpc') is True
    departed = described(stamp['fields'], configured, output_fields(xpc=xpc and swift_stamped))
    if departed is not None:
        raise Refusal(f'{STAMP_NAME} no longer describes the output target the directory is configured for: {departed} is '
                      f'{redact(stamp["fields"].get(departed))!r} in the stamp but {redact(configured.get(departed))!r} now: {FRESH_REMEDY}', 2)
    observation = observe_toolchain(builddir, root / 'controller', invocation_environment(), xpc=xpc, compilers=compilers)
    state = 'intact'
    if xpc and not stamp['scope'].get('xpc'):
        # Swift is newly applicable: validate the discovered compiler, then extend without touching other fields.
        current = compatibility_fields(observation, xpc=True)
        for name in ('compilers.swift.command', 'compilers.swift.identity'):
            if current.get(name) is None:
                raise Refusal(f'required toolchain observation failed: {name}; the newly discovered Swift compiler cannot be recorded', 2)
        retained = {k: v for k, v in stamp['fields'].items()}
        # The output fields were compared with the directory's configuration above; the rest with the toolchain now.
        difference = compare_fields(retained, current, [k for k in retained if not k.startswith(('compilers.swift.', 'output.'))])
        if difference is not None:
            name, before, now, kind = difference
            raise Refusal(f'{STAMP_NAME} cannot be extended: {name} is {redact(before)!r} in the stamp but {redact(now)!r} now: {FRESH_REMEDY}', 1)
        retained.update({name: current[name] for name in ('compilers.swift.command', 'compilers.swift.identity')})
        retained['output.swift_target'] = configured['output.swift_target']
        scope.paths.write_json(BUILDDIR, STAMP_NAME, stamp_record(retained, xpc=True, source_dir=stamp['source_dir'],
                                                                  published_at=stamp.get('published_at'),
                                                                  extended_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
        state = 'extended'
    elif xpc and stamp['fields'].get('compilers.swift.command') != compilers['swift']['command']:
        raise Refusal(f'{STAMP_NAME} no longer describes the Swift compiler the directory records: {FRESH_REMEDY}', 2)
    # The record names what happened to the stamp in this build: published at setup, validated on reuse, or extended.
    before = session.get('builddir', {}).get('stamp_state')
    session.setdefault('builddir', {})['stamp_after_compile'] = 'extended' if state == 'extended' else before
    session['toolchain'] = observation
    session['meson_options'] = meson_options(builddir)
    session['meson_machines'] = machines
    scope.save()
    print(f'ok: {STAMP_NAME} {state}')
    return 0


def meson_options(builddir):
    path = Path(builddir) / 'meson-info/intro-buildoptions.json'
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return dict(status='unknown')
    values = {}
    for option in data if isinstance(data, list) else []:
        if isinstance(option, dict) and option.get('name') in FIXED_MESON_OPTIONS:
            values[option['name']] = option.get('value')
    return dict(status='ok', values=values)


# ---- fresh mode ---------------------------------------------------------------------------

def fresh_remove(args):
    with build_scope(args.root) as state:
        return fresh_remove_admitted(state)


def fresh_remove_admitted(state):
    """Remove the three owned cache areas, all admitted before any is touched, through their held descriptors: builddir/,
    Cargo's host release area and its output triple's release area. Other profiles and other triples stay."""
    session, root = state.session, state.root
    targets = {'builddir': BUILDDIR, 'cargo_release': RELEASE, 'cargo_target_release': TRIPLE_RELEASE}
    replacement = {}
    for name, relative in targets.items():
        existed = state.paths.present(relative)
        entry = dict(path=relative, existed=existed, removed=False)
        replacement[name] = entry
        if not existed:
            continue
        failures = []
        try:
            state.paths.remove(relative, failures)
        except OSError as exc:
            failures.append(f'{root / relative} ({exc.__class__.__name__})')
        if failures or os.path.lexists(root / relative):
            session['fresh'] = dict(requested=True, replacement=replacement, failed=name)
            state.save()
            raise Refusal(f'fresh mode could not remove {root / relative} ({len(failures)} path(s) remain, first: '
                          f'{redact(failures[0]) if failures else root / relative}); remove it by hand before building again', 1)
        entry['removed'] = True
    session['fresh'] = dict(requested=True, replacement=replacement)
    session['builddir'] = dict(configured_before=False, stamp_state='absent', fresh_replaced=replacement['builddir']['removed'])
    for name in ('cargo_release', 'cargo_target_release'):
        session[name] = dict(existed_before=replacement[name]['existed'], fresh_replaced=replacement[name]['removed'])
    state.save()
    print('ok: fresh mode replaced ' + ', '.join(f"{v['path']} ({'removed' if v['removed'] else 'absent'})" for v in replacement.values()))
    return 0


# ---- Cargo ----------------------------------------------------------------------------------

def cargo_admit(args):
    """Cargo's effective intermediate directory must be the pinned target directory."""
    with build_scope(args.root) as state:
        return cargo_admit_admitted(state)


def cargo_admit_admitted(state):
    session = state.session
    pinned = state.root / TARGET
    manifest_path = state.root / 'controller/Cargo.toml'
    invocation = invocation_environment()
    # Cargo's compiler selection, its child environment and the requested flags, resolved before Cargo runs in either
    # mode: an unresolvable setting or an effective input that conflicts with build policy refuses here.
    resolution = cargo_resolution(invocation)
    observation = rustc_observation(state.root / 'controller', invocation, resolution=resolution)
    required(observation, 'rustc.command')
    try:
        # Target rules belong to the output triple the command passes, whatever host the compiler reports.
        requested = cargo_config.requested_flags(resolution['merged'], invocation, TRIPLE)
    except cargo_config.Unresolved as exc:
        raise Refusal(f'Cargo configuration cannot be resolved: {exc}; {UNRESOLVED_REMEDY}', 2)
    session.setdefault('cargo', {}).update(selection=observation['selection'], host=observation.get('host'), target=TRIPLE,
                                           requested_flags=requested)
    env = dict(invocation, CARGO_TARGET_DIR=str(pinned))
    cargo = shutil.which('cargo', path=env.get('PATH'))
    if not cargo:
        raise Refusal('cargo is not on PATH; the intermediate directory cannot be established', 2)
    found = probe([cargo, 'metadata', '--format-version', '1', '--no-deps', '--offline', '--manifest-path', str(manifest_path)],
                  env=env, limit=4 * 1024 * 1024)
    if found['status'] != 'ok':
        raise Refusal(f"cargo metadata did not report the intermediate directory ({found['kind']}); it cannot be admitted", 2)
    try:
        metadata = json.loads(found['text'])
        target_directory = Path(metadata['target_directory'])
        # Without Cargo's own report of the build directory nothing establishes where intermediates go.
        build_directory = Path(metadata['build_directory'])
    except (ValueError, KeyError, TypeError):
        raise Refusal('cargo metadata output does not name the target and build directories; they cannot be admitted', 2)
    observed = dict(target_directory=redact(str(target_directory)), build_directory=redact(str(build_directory)),
                    exact=dict(target_directory=str(target_directory), build_directory=str(build_directory)),
                    layout_environment={name: redact(env[name]) for name in CARGO_LAYOUT_ENV if name in os.environ})
    session.setdefault('cargo', {})['admission'] = observed
    if build_directory.resolve() != pinned:
        state.save()
        raise Refusal(f'Cargo would keep intermediate release state under {redact(str(build_directory))}, outside the admitted '
                      f'{redact(str(pinned))}; unset CARGO_BUILD_BUILD_DIR or the build.build-dir setting (nothing was removed)', 1)
    for name, relative in (('cargo_release', RELEASE), ('cargo_target_release', TRIPLE_RELEASE)):
        session[name] = dict(session.get(name, {}), existed_before=state.paths.present(relative),
                             fresh_replaced=session.get(name, {}).get('fresh_replaced', False))
    state.save()
    print(f'ok: Cargo intermediate and final release state admitted under {pinned} (output triple {TRIPLE})')
    return 0


def artifact_messages(state, names):
    """Every compiler-artifact message for each requested target name, from Cargo's own report."""
    found = {name: [] for name in names}
    try:
        lines = state.paths.read_text(TARGET, MESSAGES_NAME).splitlines()
    except OSError as exc:
        raise Refusal(f"Cargo's artifact messages are not readable: {exc}", 2)
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            raise Refusal(f"Cargo's artifact messages are malformed at line {number}", 2)
        if not isinstance(message, dict) or message.get('reason') != 'compiler-artifact':
            continue
        target = message.get('target')
        name = target.get('name') if isinstance(target, dict) else None
        if name in names:
            found[name].append(message)
    return found


def judgment_problem(name, messages, admitted):
    """Why Cargo's report establishes no judgment for a shipped target, or None: exactly one message, bound to the binary
    target, a profile and the admitted executable, with a literal boolean `fresh`."""
    if not messages:
        return 'no artifact message'
    if len(messages) > 1:
        return f'{len(messages)} artifact messages (ambiguous or contradictory)'
    message = messages[0]
    target = message['target']
    if not isinstance(target.get('kind'), list) or 'bin' not in target['kind']:
        return 'the message is not for a binary target'
    if message.get('executable') != str(admitted):
        return 'the message names another executable than the admitted one'
    if not isinstance(message.get('profile'), dict):
        return 'the message carries no profile'
    profile_problems = []
    CARGO_PROFILE(message['profile'], 'profile', profile_problems)
    if profile_problems:
        return 'the message carries an invalid binary profile: ' + '; '.join(profile_problems)
    if 'fresh' not in message:
        return 'fresh is missing'
    if type(message['fresh']) is not bool:
        return f"fresh is {json.dumps(message['fresh'])[:40]}, not a boolean"
    if not isinstance(message.get('package_id'), str):
        return 'the message carries no package id'
    return None


def fingerprint_observation(message, target_dir):
    """Cargo's fingerprint for this unit, bound through the uplifted executable, or an explicit limitation."""
    executable = Path(message['executable'])
    profile_dir = executable.parent
    deps = profile_dir / 'deps'
    stem = message['target']['name'].replace('-', '_')
    out = dict(status='unavailable', binding=None, limitation=None)
    if not deps.is_dir():
        out['limitation'] = 'no deps directory beside the executable'
        return out
    try:
        info = executable.stat()
    except OSError:
        out['limitation'] = 'executable is not readable'
        return out
    candidates = sorted(p for p in deps.iterdir() if re.fullmatch(re.escape(stem) + r'-[0-9a-f]{16}', p.name) and p.is_file())
    same_inode = [p for p in candidates if p.stat().st_ino == info.st_ino and p.stat().st_dev == info.st_dev]
    if len(same_inode) == 1:
        bound, how = same_inode[0], 'hard link'
    else:
        digest = sha256_file(executable)
        same_bytes = [p for p in candidates if sha256_file(p) == digest]
        if len(same_bytes) != 1:
            out['limitation'] = f'ambiguous association: {len(same_bytes)} deps candidates share the executable bytes'
            out['status'] = 'ambiguous'
            return out
        bound, how = same_bytes[0], 'identical bytes'
    meta = bound.name.rsplit('-', 1)[1]
    package = re.sub(r'[#@].*$', '', message['package_id'].rsplit('/', 1)[-1]).split('#')[0]
    name = message['package_id'].split('#', 1)[1].split('@', 1)[0] if '#' in message['package_id'] and '@' in message['package_id'].split('#', 1)[1] else None
    package_name = name or Path(message['manifest_path']).parent.name
    fingerprint = profile_dir / '.fingerprint' / f'{package_name}-{meta}' / f"bin-{message['target']['name']}.json"
    out.update(binding=dict(deps_file=bound.name, how=how, metadata_hash=meta, fingerprint=str(fingerprint.relative_to(target_dir)) if target_dir in fingerprint.parents else redact(str(fingerprint))))
    if not fingerprint.is_file():
        out['limitation'] = 'fingerprint file is missing'
        return out
    try:
        data = json.loads(fingerprint.read_text())
    except (OSError, ValueError):
        out.update(status='malformed', limitation='fingerprint file is not a JSON object')
        return out
    if not isinstance(data, dict) or not isinstance(data.get('rustflags'), list) or not all(isinstance(f, str) for f in data['rustflags']):
        out.update(status='unsupported', limitation='fingerprint has no rustflags list; the layout is not the supported one')
        return out
    if len(data['rustflags']) > FLAG_LIMIT or oversized(data['rustflags']):
        out.update(status='oversized', limitation=f"fingerprint lists {len(data['rustflags'])} flags or a flag beyond the record's "
                                                  f'bounds ({FLAG_LIMIT} flags of {LINE_LIMIT} characters); none is recorded')
        return out
    out.update(status='observed', rustflags=list(data['rustflags']),
               rustc_fingerprint=str(data.get('rustc')) if isinstance(data.get('rustc'), int) else None,
               profile_fingerprint=str(data.get('profile')) if isinstance(data.get('profile'), int) else None,
               limitation='hash fields are opaque unit fingerprints; they do not identify a compiler or a wrapper')
    return out


def flag_attribution(effective, requested, rustflags_source):
    """The requested source by Cargo's precedence and whether its tokens equal Cargo's record of the effective flags.

    Equality alone never names a source: the source is the first one present in
    Cargo's order, and a source whose tokens cannot be established (target rules
    with cfg() keys, an environment rule) stays unresolved."""
    labels = {'caller': 'RUSTFLAGS (caller)', 'script': 'RUSTFLAGS (script default)', 'none': 'RUSTFLAGS'}
    kind = requested['source']
    if kind == 'RUSTFLAGS':
        kind = labels[rustflags_source]
    agrees = None
    if effective is not None and requested.get('resolved') and requested.get('tokens') is not None:
        agrees = requested['tokens'] == effective
    return dict(kind=kind, resolved=bool(requested.get('resolved')), tokens=requested.get('tokens'),
                overrides=requested.get('overrides', []), rules=requested.get('rules'), agrees=agrees,
                effective_source="Cargo's fingerprint for the unit")


def cargo_judge(args):
    with build_scope(args.root) as state:
        return cargo_judge_admitted(state, args)


def cargo_judge_admitted(state, args):
    session = state.session
    target_dir = state.root / TARGET
    env = invocation_environment()
    messages = artifact_messages(state, set(args.bin))
    requested = (session.get('cargo') or {}).get('requested_flags')
    if not isinstance(requested, dict):
        try:
            requested = cargo_config.requested_flags({}, env, TRIPLE)
        except cargo_config.Unresolved as exc:
            raise Refusal(f'Cargo configuration cannot be resolved: {exc}; {UNRESOLVED_REMEDY}', 2)
    judgments, problems = {}, []
    for name in args.bin:
        problem = judgment_problem(name, messages[name], target_dir / TRIPLE / 'release' / name)
        if problem is not None:
            judgments[name] = dict(status='unknown', fresh=None, problem=problem)
            problems.append(f'{name} ({problem})')
            continue
        message = messages[name][0]
        fingerprint = fingerprint_observation(message, target_dir)
        judgments[name] = dict(status='reported', fresh=message['fresh'], profile=message['profile'],
                               package_id=redact(message['package_id']), executable=redact(message['executable']),
                               exact_executable=message['executable'], fingerprint=fingerprint,
                               effective_rustflags=fingerprint.get('rustflags'),
                               rustflags_source=flag_attribution(fingerprint.get('rustflags'), requested, args.rustflags_source))
    session.setdefault('cargo', {})['judgments'] = judgments
    session['cargo']['flag_environment'] = {name: ('set' if name in env else 'unset') for name in CARGO_FLAG_ENV}
    tokens = env.get('RUSTFLAGS', '').split()
    session['cargo']['requested_rustflags'] = (dict(source=args.rustflags_source, tokens=tokens)
                                               if len(tokens) <= FLAG_LIMIT and not oversized(tokens)
                                               else dict(source=args.rustflags_source, tokens=None, oversized=True))
    state.save()
    if problems:
        raise Refusal("Cargo's report establishes no literal boolean fresh judgment for the admitted executable of "
                      + ', '.join(problems) + '; reuse cannot be recorded', 2)
    reused = [name for name, j in judgments.items() if j['fresh'] is not False]
    if args.require_rebuilt == '1' and reused:
        raise Refusal('fresh mode requires Cargo to report rebuilding every shipped target, but '
                      + ', '.join(f'{name} (reused)' for name in reused), 1)
    summary = ', '.join(f"{name}: {'reused' if j['fresh'] else 'rebuilt'}" for name, j in judgments.items())
    print(f'ok: Cargo judgments recorded ({summary})')
    return 0


# ---- outputs ----------------------------------------------------------------------------------

def normalize_version(text):
    """A dotted numeric version as a tuple without trailing zeros, or None when malformed."""
    if not isinstance(text, str) or not re.fullmatch(r'\d+(\.\d+)*', text.strip()):
        return None
    parts = [int(p) for p in text.strip().split('.')]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def parse_build_version(otool_text):
    """LC_BUILD_VERSION and LC_UUID from otool -l text: platform, minos, sdk and the tools, or what is missing."""
    out = dict(uuid=None, platform=None, minos=None, sdk=None, tools=[], problems=[])
    commands = re.split(r'^Load command \d+\n', otool_text, flags=re.M)
    build_versions = [c for c in commands if re.search(r'^\s*cmd LC_BUILD_VERSION\s*$', c, re.M)]
    uuids = [c for c in commands if re.search(r'^\s*cmd LC_UUID\s*$', c, re.M)]
    if len(uuids) == 1:
        match = re.search(r'^\s*uuid (\S+)', uuids[0], re.M)
        out['uuid'] = match.group(1) if match else None
    if out['uuid'] is None:
        out['problems'].append('no readable LC_UUID')
    if len(build_versions) != 1:
        out['problems'].append(f'{len(build_versions)} LC_BUILD_VERSION commands; exactly one is readable')
        return out
    text = build_versions[0]
    for key in ('platform', 'minos', 'sdk'):
        match = re.search(r'^\s*' + key + r' (\S+)\s*$', text, re.M)
        value = match.group(1) if match else None
        if value is None or value == 'n/a':
            out['problems'].append(f'LC_BUILD_VERSION {key} is missing')
        out[key] = value
    for tool, version in re.findall(r'^\s*tool (\S+)\s*\n\s*version (\S+)\s*$', text, re.M):
        out['tools'].append(dict(tool=tool, version=version))
    return out


def output_metadata(path):
    found = probe(['/usr/bin/otool', '-l', str(path)], limit=4 * 1024 * 1024)
    if found['status'] != 'ok':
        return dict(status='failed', kind=found['kind'], problems=[f"otool {found['kind']}"])
    parsed = parse_build_version(found['text'])
    parsed['status'] = 'ok' if not parsed['problems'] else 'incomplete'
    return parsed


def sdk_check(args):
    with build_scope(args.root) as state:
        return sdk_check_admitted(state, args)


def sdk_check_admitted(state, args):
    session = state.session
    selected = normalize_version(args.sdk_version)
    if selected is None:
        raise Refusal(f'the selected SDK version {args.sdk_version!r} is not a numeric version; outputs cannot be compared with it', 1)
    results = {}
    problems = []
    for path in args.path:
        metadata = output_metadata(path)
        results[redact(path)] = dict(sdk=metadata.get('sdk'), minos=metadata.get('minos'), platform=metadata.get('platform'))
        if metadata.get('status') != 'ok':
            problems.append(f"{path}: {'; '.join(metadata.get('problems') or ['unreadable load commands'])}")
            continue
        found = normalize_version(metadata['sdk'])
        if found is None:
            problems.append(f"{path}: LC_BUILD_VERSION sdk {metadata['sdk']!r} is not a numeric version")
        elif found != selected:
            problems.append(f"{path}: built against SDK {metadata['sdk']}; the selected SDK is {args.sdk_version}")
    session['sdk_check'] = dict(selected=args.sdk_version, outputs=results, problems=problems)
    state.save()
    if problems:
        raise Refusal('shipped outputs disagree with the selected SDK version:\n  ' + '\n  '.join(problems), 1)
    print(f'ok: {len(args.path)} outputs carry SDK {args.sdk_version}')
    return 0


def output_observation(path):
    """One file observed against the output target with this module's bounded probe and load-command reader."""
    return output_target.observe(path, probe=probe, read_metadata=output_metadata)


def output_check(args):
    with build_scope(args.root) as state:
        return output_check_admitted(state, args)


def output_check_admitted(state, args):
    """Every named output, and with --app every Mach-O the assembled bundle carries, is a thin arm64 Mach-O for macOS.

    The build variant's required executables are checked even when missing or
    no longer recognizable as Mach-O. The header scan adds any unlisted code;
    dSYM companions are debug data and are not code. Each stage's
    observations are recorded in the session; any departure, unreadable file
    or failed observation refuses, and nothing is thinned or repaired."""
    session = state.session
    paths, problems = [Path(path) for path in args.path], []
    if args.app is not None:
        expected = FULL_OUTPUTS if session['knobs']['BUILD_XPC'] == '1' else PARTIAL_OUTPUTS
        paths += [Path(args.app) / relative for relative in expected]
        try:
            paths += output_target.runnable_code(args.app)
        except OSError as exc:
            problems.append(f'{redact(str(args.app))}: the bundle cannot be scanned ({exc.__class__.__name__})')
    if not paths and not problems:
        problems.append('no output was named or found')
    paths = list(dict.fromkeys(paths))
    results = {}
    for path in paths:
        observation = output_observation(path)
        found = output_target.target_problems(observation)
        results[redact(str(path))] = dict(container=observation['container'], architectures=observation['architectures'],
                                          platform=observation['platform'], problems=found)
        if found:
            problems.append(redact(output_target.describe(observation)))
    session.setdefault('output_check', {})[args.stage] = dict(outputs=results, problems=problems)
    state.save()
    if problems:
        raise Refusal('outputs are not thin arm64 Mach-O executables for macOS:\n  ' + '\n  '.join(problems), 1)
    print(f'ok: {len(paths)} outputs are thin {output_target.ARCHITECTURE} Mach-O for macOS ({args.stage})')
    return 0


def worker_identity(args):
    with build_scope(args.root) as state:
        return worker_identity_admitted(state, args)


def worker_identity_admitted(state, args):
    session = state.session
    found = probe([args.worker, '--version'])
    if found['status'] != 'ok':
        session['worker_identity'] = dict(status='failed', kind=found['kind'])
        state.save()
        raise Refusal(f"the built worker did not report its identity ({found['kind']})", 2)
    match = re.search(r'\babi_identity=([0-9a-f]{64})\b', found['line'])
    if not match:
        session['worker_identity'] = dict(status='failed', kind='malformed_output')
        state.save()
        raise Refusal('the built worker reported no abi_identity', 2)
    reported = match.group(1)
    session['worker_identity'] = dict(status='ok', reported=reported, expected=args.expected)
    state.save()
    if reported != args.expected:
        raise Refusal(f'the built worker reports identity {reported}, not the generated {args.expected}; '
                      f'the worker in builddir/ was compiled from other identity inputs: {FRESH_REMEDY}', 1)
    print(f'ok: the built worker reports the generated identity {reported[:12]}...')
    return 0


# ---- the record -----------------------------------------------------------------------------------

def shipped_outputs(app):
    """Bundle-relative paths of every shipped Mach-O, in inventory order."""
    paths = [CONTROLLER]
    for name in TOP_HELPERS:
        if (app / 'Contents/MacOS' / name).is_file():
            paths.append('Contents/MacOS/' + name)
    service = app / SERVICE
    if service.is_dir():
        paths.append(SERVICE + '/Contents/MacOS/PWRunner')
        paths += [SERVICE + '/Contents/MacOS/' + name for name in NESTED_HELPERS if (service / 'Contents/MacOS' / name).is_file()]
    return paths


def collect(session, app, root, identity, *, manifest_entries, signature):
    """The record, from the session's observations and the assembled bundle. `signature` reads codesign facts."""
    app, root = Path(app).resolve(), Path(root).resolve()
    toolchain = session.get('toolchain')
    if not isinstance(toolchain, dict):
        raise Refusal('the session carries no toolchain observation; the record cannot be written', 2)
    knobs = session.get('knobs', {})
    xpc = knobs.get('BUILD_XPC') == '1'
    for name in ('developer_dir', 'sdk', 'rustc', 'cargo', 'meson', 'ninja'):
        if name == 'sdk':
            for part in ('path', 'version', 'build'):
                required(toolchain['sdk'][part], f'sdk.{part}')
        else:
            required(toolchain[name], name)
    required(toolchain['compilers'].get('c', {}).get('observed', {}), 'compilers.c.identity')
    if xpc:
        required(toolchain['compilers'].get('swift', {}).get('observed', {}), 'compilers.swift.identity')
    worker = session.get('worker_identity') or {}
    if worker.get('status') != 'ok':
        raise Refusal('the session carries no worker identity observation; the record cannot be written', 2)
    judgments = (session.get('cargo') or {}).get('judgments')
    if not isinstance(judgments, dict):
        raise Refusal('the session carries no Cargo judgments; the record cannot be written', 2)
    hashes = {}
    for relative in SOURCE_INPUTS:
        path = root / relative
        if not path.is_file():
            raise Refusal(f'source input is missing: {relative}', 2)
        hashes[relative] = sha256_file(path)
    stamp = session.get('stamp', {})
    source = dict(commit=stamp.get('commit'), describe=stamp.get('describe'), dirty=bool(stamp.get('dirty')),
                  version=stamp.get('version'), build_number=stamp.get('build_number'),
                  worker_identity=worker['reported'], input_hashes=hashes)

    def published(entry):
        """A toolchain entry without its exact private paths."""
        if not isinstance(entry, dict):
            return entry
        return {k: published(v) for k, v in entry.items() if k != 'exact_command'}

    compilers = {}
    for language in ('c', 'swift'):
        entry = toolchain['compilers'].get(language)
        # A partial build compiles no Swift, even in a directory an earlier full build configured with a Swift compiler.
        if language == 'swift' and not xpc:
            entry = None
        if entry is None:
            compilers[language] = dict(status='not applicable', reason='partial build: the XPC pieces were not compiled') if language == 'swift' else dict(status='unknown')
        else:
            compilers[language] = dict(configured=dict(command=entry['configured']['command'], id=entry['configured']['id'],
                                                       version=entry['configured']['version'], full_version=entry['configured']['full_version']),
                                       observed=published(entry['observed']))
    developer = toolchain['developer_dir']
    toolchain_record = dict(developer_dir=dict(value=redact(developer['value']), source=developer['source']),
                            sdk=dict({part: toolchain['sdk'][part]['line'] for part in ('path', 'version', 'build')},
                                     source='SDKROOT named by the caller' if session.get('sdk_source') == 'caller' else 'xcrun --sdk macosx default'),
                            xcode=toolchain['xcode'], compilers=compilers, rustc=published(toolchain['rustc']),
                            cargo=toolchain['cargo'], meson=toolchain['meson'], ninja=toolchain['ninja'],
                            python=toolchain.get('python'))
    toolchain_record['sdk']['path'] = redact(toolchain_record['sdk']['path'])
    toolchain_record['rustc']['selection_note'] = ('the command Cargo would run, resolved through its configuration files and '
                                                   'includes, environment overrides and launcher, and probed now without its '
                                                   'wrappers in the environment and directory Cargo gives it; a probe today does '
                                                   'not identify the compiler that produced a reused output')
    builddir_state = session.get('builddir', {})
    fresh = session.get('fresh', {})
    stamp_projection = None
    try:
        data = read_stamp(root / 'builddir')
        stamp_projection = dict(scope=data['scope'], published_at=data.get('published_at'), extended_at=data.get('extended_at'),
                                fields={k: redact(v) for k, v in data['fields'].items()})
    except Refusal as exc:
        stamp_projection = dict(status='unavailable', reason=str(exc)[:LINE_LIMIT])
    requested = (session.get('cargo') or {}).get('requested_rustflags', {})
    effective = ((session.get('cargo') or {}).get('selection') or {}).get('child_environment')
    if not isinstance(effective, dict) or not effective.get('MACOSX_DEPLOYMENT_TARGET') or not effective.get('SDKROOT'):
        raise Refusal("the session carries no effective deployment target and SDK from Cargo's resolved environment; the record cannot be written", 2)
    machines = session.get('meson_machines')
    if not isinstance(machines, dict) or set(machines) != {'host', 'build'}:
        raise Refusal("the session carries no Meson host and build machines; the record cannot be written", 2)

    def cargo_directory(name):
        # A directory fresh mode replaced was created anew, as builddir/ records after its replacement.
        state = session.get(name, {})
        return dict(state='reused' if state.get('existed_before') and not state.get('fresh_replaced') else 'created',
                    replaced_by_fresh_mode=bool(state.get('fresh_replaced')))

    configuration = dict(
        knobs={name: knobs.get(name) for name in ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD')},
        meson_options=session.get('meson_options', dict(status='unknown')),
        rustflags=dict(requested=dict(source=requested.get('source'), tokens=requested.get('tokens', [])),
                       flag_environment=(session.get('cargo') or {}).get('flag_environment', {}),
                       note='effective flags are recorded per output from Cargo\'s fingerprint; they are additional compiler arguments, not the complete command'),
        requests=caller_requests(session),
        output_target=dict(output_target.DECLARED,
                           note='the fixed target every shipped executable must satisfy, observed per output below; it describes the '
                                'products, not the machine or processes that built them, and makes no claim about translation'),
        meson_machines=dict(host=machines['host'], build=machines['build'],
                            note="Meson's host machine is the platform the native products are configured for; its build machine is "
                                 'where Meson reported compiling, a toolchain fact that is not constrained'),
        deployment_target=effective['MACOSX_DEPLOYMENT_TARGET'],
        sdkroot=effective['SDKROOT'],
        build_directories=dict(
            builddir=dict(state='reused' if builddir_state.get('configured_before') else 'created',
                          replaced_by_fresh_mode=bool(builddir_state.get('fresh_replaced')),
                          stamp=builddir_state.get('stamp_after_compile') or builddir_state.get('stamp_state')),
            cargo_release=cargo_directory('cargo_release'),
            cargo_target_release=cargo_directory('cargo_target_release'),
            fresh_mode=dict(requested=bool(fresh.get('requested')), replacement=fresh.get('replacement')),
            cargo_admission={k: v for k, v in ((session.get('cargo') or {}).get('admission') or {}).items() if k != 'exact'}),
        toolchain_stamp=dict(scope_note='the stamp covers the Meson configuration and the compatibility inputs observed at setup; '
                                        'it does not attest to how independently retained Cargo outputs were produced',
                             projection=stamp_projection))
    outputs = []
    manifest_hashes = {e['rel_path']: e.get('sha256') for e in manifest_entries if isinstance(e, dict)}
    for relative in shipped_outputs(app):
        path = app / relative
        metadata = output_metadata(path)
        if metadata.get('status') != 'ok':
            raise Refusal(f"{relative}: load commands are not readable ({'; '.join(metadata.get('problems') or [metadata.get('kind', 'unknown')])})", 2)
        if len(metadata['tools']) > TOOLS_LIMIT or oversized([v for tool in metadata['tools'] for v in tool.values()]):
            raise Refusal(f"{relative}: {len(metadata['tools'])} build tools in LC_BUILD_VERSION exceed the record's bounds", 2)
        observed = output_observation(path)
        departures = output_target.target_problems(observed)
        if departures:
            raise Refusal(f"{relative}: outside the output target ({'; '.join(departures)})", 2)
        entry = dict(rel_path=relative, uuid=metadata['uuid'], platform=metadata['platform'], minos=metadata['minos'],
                     sdk=metadata['sdk'], tools=metadata['tools'], architectures=observed['architectures'], container=observed['container'])
        if relative != CONTROLLER:
            entry['sha256'] = sha256_file(path)
            if manifest_hashes.get(relative) != entry['sha256']:
                raise Refusal(f'{relative}: the manifest records {manifest_hashes.get(relative)} but the bundle bytes hash to {entry["sha256"]}', 2)
            entry['signature'] = signature(path)
        else:
            entry['sha256'] = None
            entry['note'] = 'the controller is sealed by the app signature after this record; its final hash is in the release record'
        name = CARGO_TARGETS.get(relative)
        if name is not None:
            judgment = judgments.get(name, dict(status='unavailable'))
            entry['cargo'] = {k: v for k, v in judgment.items() if k != 'exact_executable'}
            entry['cargo']['note'] = ('fresh means Cargo reused an output it judged current; the hash above identifies the captured bytes and '
                                      'does not authenticate their compilation history')
        outputs.append(entry)
    nested = [dict(rel_path=o['rel_path'], **{k: o['signature'].get(k) for k in ('leaf', 'team', 'timestamp')})
              for o in outputs if 'signature' in o]
    record = dict(schema_version=SCHEMA_VERSION, generated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                  source=source, toolchain=toolchain_record, configuration=configuration, outputs=outputs,
                  signing=dict(identity=identity, nested=nested,
                               note='the app seal is made after this record and verified afterwards; its facts live in the release record'),
                  limits=['tool reports and hashes of the captured bytes; not reproducibility, compiler correctness, '
                          'execution of particular bytes or an exhaustive account of private runtime dependencies',
                          'a cached executable replaced before capture can be reported reusable by Cargo and still agree with these hashes'])
    problems = record_shape_problems(record)
    if problems:
        raise Refusal('the record fails its own validation: ' + '; '.join(problems[:5]), 2)
    text = json.dumps(record, indent=2, sort_keys=True)
    forbidden = forbidden_content(text, os.environ)
    if forbidden:
        raise Refusal('the record would publish ' + forbidden, 2)
    if len(text.encode()) > RECORD_LIMIT:
        raise Refusal('the record exceeds its size bound', 2)
    return record


def caller_requests(session):
    """What the caller asked for, apart from what the build then selected.

    SDKROOT and the other witnessed variables describe the build's starting
    environment; DEVELOPER_DIR and MACOSX_DEPLOYMENT_TARGET are recorded at
    session start. Only the SDK, developer directory and deployment target
    publish their values.
    """
    requests = session.get('requests')
    if not isinstance(requests, dict):
        raise Refusal("the session carries no caller requests; the record cannot be written", 2)
    out = {}
    for name in ('SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE'):
        entry = requests.get(name)
        if not isinstance(entry, dict) or entry.get('state') not in ('set', 'unset'):
            raise Refusal(f"the session's request for {name} is malformed; the record cannot be written", 2)
        out[name] = dict(state=entry['state'])
        if name == 'SDKROOT' and entry['state'] == 'set':
            out[name]['value'] = redact(entry.get('value', ''))
    environment = session.get('environment') or {}
    for name in ('DEVELOPER_DIR', 'MACOSX_DEPLOYMENT_TARGET'):
        out[name] = dict(state='set', value=redact(environment[name])) if name in environment else dict(state='unset')
    return out


def forbidden_content(text, env):
    """A description of forbidden content in the record text, or None."""
    home = env.get('HOME')
    if home and home != '/' and home in text:
        return 'a home-prefixed path'
    path = env.get('PATH')
    if path and path in text:
        return 'the PATH value'
    return None


# ---- the record's shape -----------------------------------------------------------------------------

HEX64 = re.compile(r'[0-9a-f]{64}')
UUID = re.compile(r'[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}')
VERSION = re.compile(r'\d+(\.\d+)*')
TEXT_LIMIT = 2000
FAILURE_KINDS = ('launch_failed', 'timeout', 'nonzero_exit', 'empty_output', 'malformed_output', 'output_overflow', 'oversized_output')
FULL_OUTPUTS = (CONTROLLER, *('Contents/MacOS/' + n for n in TOP_HELPERS), SERVICE + '/Contents/MacOS/PWRunner',
                *(SERVICE + '/Contents/MacOS/' + n for n in NESTED_HELPERS))
PARTIAL_OUTPUTS = (CONTROLLER, 'Contents/MacOS/sandbox-log-observer', 'Contents/MacOS/sbpl-check')


class Shape:
    """A typed check of one value: exact types (a bool is not an integer), bounds, and whether null is allowed."""

    def __init__(self, check, nullable=False):
        self.check, self.nullable = check, nullable

    def __call__(self, value, where, problems):
        if value is None:
            if not self.nullable:
                problems.append(f'{where} is null')
            return
        self.check(value, where, problems)


def text(limit=LINE_LIMIT, pattern=None, nullable=False, empty=False):
    def check(value, where, problems):
        if type(value) is not str:
            problems.append(f'{where} is not a string')
        elif len(value) > limit:
            problems.append(f'{where} exceeds {limit} characters')
        elif not value and not empty:
            problems.append(f'{where} is empty')
        elif pattern is not None and value and not pattern.fullmatch(value):
            problems.append(f'{where} is malformed')
    return Shape(check, nullable)


def boolean(nullable=False):
    return Shape(lambda value, where, problems: None if type(value) is bool else problems.append(f'{where} is not a boolean'), nullable)


def integer(nullable=False):
    return Shape(lambda value, where, problems: None if type(value) is int else problems.append(f'{where} is not an integer'), nullable)


def one_of(*values, nullable=False):
    return Shape(lambda value, where, problems: None if value in values and type(value) is type(values[0])
                 else problems.append(f'{where} is not one of {", ".join(map(str, values))}'), nullable)


def array(item, limit, nullable=False, empty=True):
    def check(value, where, problems):
        if type(value) is not list:
            problems.append(f'{where} is not an array')
            return
        if len(value) > limit:
            problems.append(f'{where} holds more than {limit} items')
        if not value and not empty:
            problems.append(f'{where} is empty')
        for index, element in enumerate(value[:limit]):
            item(element, f'{where}[{index}]', problems)
    return Shape(check, nullable)


def mapping(value_shape, limit=64, key=None, nullable=False):
    def check(value, where, problems):
        if type(value) is not dict:
            problems.append(f'{where} is not an object')
            return
        if len(value) > limit:
            problems.append(f'{where} holds more than {limit} entries')
        for name, element in value.items():
            if key is not None and not key.fullmatch(name):
                problems.append(f'{where} has a malformed key')
            value_shape(element, f'{where}.{name}', problems)
    return Shape(check, nullable)


def obj(required=None, optional=None, nullable=False, closed=False):
    required, optional = required or {}, optional or {}

    def check(value, where, problems):
        if type(value) is not dict:
            problems.append(f'{where} is not an object')
            return
        for name, shape in required.items():
            if name not in value:
                problems.append(f'{where}.{name} is missing')
            else:
                shape(value[name], f'{where}.{name}', problems)
        for name, shape in optional.items():
            if name in value:
                shape(value[name], f'{where}.{name}', problems)
        if closed:
            for name in value:
                if name not in required and name not in optional:
                    problems.append(f'{where}.{name} is not a field of this record')
    return Shape(check, nullable)


def alternatives(*cases, nullable=False):
    """The first case whose discriminating `status` matches decides; a status no case names is a problem."""
    def check(value, where, problems):
        if type(value) is not dict:
            problems.append(f'{where} is not an object')
            return
        for status, shape in cases:
            if value.get('status') == status:
                shape(value, where, problems)
                return
        problems.append(f"{where}.status is not one of {', '.join(status for status, _ in cases)}")
    return Shape(check, nullable)


ANY_TEXT = text(TEXT_LIMIT)
NOTE = text(TEXT_LIMIT)
COMMAND = array(text(LINE_LIMIT), COMMAND_LIMIT, empty=False)
FLAGS = array(text(LINE_LIMIT, empty=True), FLAG_LIMIT)
FLAGS_OR_NULL = array(text(LINE_LIMIT, empty=True), FLAG_LIMIT, nullable=True)


def request_shape(*, private=False):
    def check(value, where, problems):
        if type(value) is not dict:
            problems.append(f'{where} is not an object')
            return
        state = value.get('state')
        if state == 'set' and 'value' in value and not private:
            obj(dict(state=one_of('set'), value=text(TEXT_LIMIT, empty=True)), closed=True)(value, where, problems)
        elif state == 'set' and private:
            obj(dict(state=one_of('set')), closed=True)(value, where, problems)
        elif state == 'unset':
            obj(dict(state=one_of('unset')), closed=True)(value, where, problems)
        else:
            problems.append(f'{where}.state is not set or unset')
    return Shape(check)


OBSERVED_COMPILER = obj(dict(configured=obj(dict(command=COMMAND, id=text(), version=text(empty=True), full_version=text(nullable=True, empty=True))),
                             observed=obj(dict(status=one_of('ok'), command=COMMAND, identity=text()))))
PROGRAM = obj(dict(source=text(), command=text(TEXT_LIMIT, nullable=True), overrides=array(text(), 8), file=text(TEXT_LIMIT, nullable=True),
                   disabled=boolean()))
def selection_shape():
    fields = dict(
        files=array(obj(dict(path=text(TEXT_LIMIT), includes=array(obj(dict(path=text(TEXT_LIMIT), optional=boolean(), loaded=boolean())), 64))), 64),
        launcher=obj(dict(kind=one_of('cargo', 'rustup proxy'), toolchain=text(nullable=True))),
        programs=obj(dict(rustc=PROGRAM, wrapper=PROGRAM, workspace_wrapper=PROGRAM)),
        env_entries=mapping(obj(dict(applied=boolean(), force=boolean(), relative=boolean(), file=text(TEXT_LIMIT, nullable=True))), 256),
        child_environment=obj(dict(SDKROOT=text(TEXT_LIMIT, nullable=True), MACOSX_DEPLOYMENT_TARGET=text(nullable=True),
                                   DEVELOPER_DIR=text(TEXT_LIMIT, nullable=True), RUSTUP_TOOLCHAIN=text(nullable=True),
                                   path_replaced_by_env=boolean(), rustup_home_replaced_by_env=boolean())),
        target=obj(dict(source=one_of('--target'), triple=one_of(TRIPLE),
                        overrides=array(one_of('CARGO_BUILD_TARGET', 'build.target'), 2)), closed=True))
    return obj(fields)


WRAPPER = obj(dict(source=text(), command=text(TEXT_LIMIT)), dict(sha256=text(64, HEX64)))


def rustc_shape():
    return obj(dict(status=one_of('ok'), command=text(TEXT_LIMIT), source=one_of('RUSTC', 'CARGO_BUILD_RUSTC', 'build.rustc', 'default'),
                    identity=text(), release=text(), commit_hash=text(empty=True), host=text(), llvm_version=text(empty=True),
                    wrappers=obj(optional=dict(wrapper=WRAPPER, workspace_wrapper=WRAPPER), closed=True),
                    selection_environment=mapping(text(TEXT_LIMIT, empty=True), 16), selection=selection_shape(), selection_note=NOTE))


TOOL = obj(dict(status=one_of('ok'), command=text(TEXT_LIMIT), version=text()))
# The pinned interpreter: the keg's version and the probed version agree by the resolver's own check.
INTERPRETER = obj(dict(status=one_of('ok'), command=text(TEXT_LIMIT), realpath=text(TEXT_LIMIT), keg_version=text(16, VERSION),
                       version=text(16, VERSION)), closed=True)
FINGERPRINT = alternatives(
    ('observed', obj(dict(binding=mapping(text(TEXT_LIMIT), 8), rustflags=FLAGS, rustc_fingerprint=text(nullable=True),
                          profile_fingerprint=text(nullable=True), limitation=NOTE))),
    *((status, obj(dict(binding=mapping(text(TEXT_LIMIT), 8, nullable=True), limitation=NOTE)))
      for status in ('unavailable', 'ambiguous', 'malformed', 'unsupported', 'oversized')))
FLAG_SOURCE = obj(dict(kind=text(), resolved=boolean(), tokens=array(text(LINE_LIMIT, empty=True), FLAG_LIMIT, nullable=True),
                       overrides=array(text(), 8), agrees=boolean(nullable=True), effective_source=text()),
                  dict(rules=array(text(), 64, nullable=True)))
CARGO_PROFILE = obj(dict(opt_level=one_of('0', '1', '2', '3', 's', 'z'),
                         debuginfo=Shape(lambda v, w, p: None if (type(v) is int and v in (0, 1, 2)) or
                                         (type(v) is str and v in ('none', 'limited', 'full', 'line-directives-only', 'line-tables-only'))
                                         else p.append(f'{w} is not a Cargo debuginfo level'), nullable=True),
                         debug_assertions=boolean(), overflow_checks=boolean(), test=one_of(False)), closed=True)
CARGO_JUDGMENT = obj(dict(status=one_of('reported'), fresh=boolean(), profile=CARGO_PROFILE, package_id=text(TEXT_LIMIT),
                          executable=text(TEXT_LIMIT), fingerprint=FINGERPRINT, effective_rustflags=FLAGS_OR_NULL,
                          rustflags_source=FLAG_SOURCE, note=NOTE))
SIGNATURE = obj(dict(status=one_of('ok'), leaf=text(nullable=True), team=text(nullable=True), timestamp=boolean(), runtime=boolean(),
                     adhoc=boolean(), developer_id_chain=boolean()))


def output_shape():
    fields = dict(rel_path=text(TEXT_LIMIT), uuid=text(36, UUID), platform=text(8, re.compile(r'\d+')), minos=text(16, VERSION),
                  sdk=text(16, VERSION), tools=array(obj(dict(tool=text(16), version=text(32)), closed=True), TOOLS_LIMIT),
                  sha256=text(64, HEX64, nullable=True),
                  architectures=array(text(output_target.NAME_LIMIT), output_target.SLICE_LIMIT, empty=False),
                  container=one_of('thin', 'fat'))
    return obj(fields, dict(signature=SIGNATURE, note=NOTE, cargo=CARGO_JUDGMENT))


BUILD_DIRECTORY = obj(dict(state=one_of('created', 'reused'), replaced_by_fresh_mode=boolean()), dict(stamp=text(nullable=True)))
TIMESTAMP = text(32, re.compile(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ'))
STAMP_FIELDS = {
    'developer_dir': text(TEXT_LIMIT), 'sdk.path': text(TEXT_LIMIT), 'sdk.version': text(16, VERSION), 'sdk.build': text(32),
    'compilers.c.command': COMMAND, 'compilers.c.identity': text(), 'rustc.command': text(TEXT_LIMIT), 'rustc.identity': text(),
    'rustc.wrappers': obj(optional={name: obj(dict(command=text(TEXT_LIMIT), sha256=text(64, HEX64, nullable=True)), closed=True)
                                  for name in ('wrapper', 'workspace_wrapper')}, closed=True),
}
SELECTIONS = array(text(LINE_LIMIT), 8, empty=False)
STAMP_OUTPUT_FIELDS = {'output.system': text(32), 'output.cpu_family': text(32), 'output.c_arch': SELECTIONS,
                       'output.link_arch': SELECTIONS, 'output.cargo_triple': text(64)}


def stamp_projection_shape():
    def check(value, where, problems):
        if isinstance(value, dict) and value.get('status') == 'unavailable':
            obj(dict(status=one_of('unavailable'), reason=NOTE), closed=True)(value, where, problems)
            return
        obj(dict(scope=obj(dict(xpc=boolean()), closed=True), published_at=TIMESTAMP,
                 extended_at=text(32, re.compile(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ'), nullable=True), fields=obj()), closed=True)(value, where, problems)
        if not isinstance(value, dict) or not isinstance(value.get('scope'), dict):
            return
        fields = dict(STAMP_FIELDS)
        swift = value['scope'].get('xpc') is True
        if swift:
            fields.update({'compilers.swift.command': COMMAND, 'compilers.swift.identity': text()})
        fields.update(STAMP_OUTPUT_FIELDS)
        if swift:
            fields['output.swift_target'] = SELECTIONS
        obj(fields, closed=True)(value.get('fields'), where + '.fields', problems)
    return Shape(check)


MESON_OPTION_SHAPES = {name: text() for name in FIXED_MESON_OPTIONS}
MESON_OPTION_SHAPES.update({name: boolean() for name in ('debug', 'werror', 'strip', 'b_lto', 'b_coverage', 'b_bitcode',
                                                        'b_pie', 'b_staticpic', 'b_lundef', 'inspection', 'xpc')})
MESON_OPTION_SHAPES.update({name: FLAGS for name in ('c_args', 'c_link_args', 'swift_args', 'swift_link_args')})
# Meson has published b_sanitize as both a string and an array across supported versions.
MESON_OPTION_SHAPES['b_sanitize'] = Shape(lambda v, w, p: (text() if isinstance(v, str) else FLAGS)(v, w, p))
MACHINE = obj(dict(system=text(32), cpu_family=text(32)), closed=True)


# The cache areas fresh mode replaces, as the record names them.
CACHE_AREAS = (('builddir', BUILDDIR), ('cargo_release', RELEASE), ('cargo_target_release', TRIPLE_RELEASE))


def record_shape():
    """The documented record of the current schema version."""
    replacement = obj({name: obj(dict(path=one_of(relative), existed=boolean(), removed=boolean()), closed=True)
                       for name, relative in CACHE_AREAS}, closed=True, nullable=True)
    directories = {name: BUILD_DIRECTORY for name, _ in CACHE_AREAS}
    configuration = dict(
        knobs=obj({name: one_of('0', '1') for name in ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD')}, closed=True),
        meson_options=alternatives(('ok', obj(dict(values=obj(optional=MESON_OPTION_SHAPES, closed=True)))), ('unknown', obj())),
        rustflags=obj(dict(requested=obj(dict(source=one_of('caller', 'script', 'none'), tokens=array(text(LINE_LIMIT, empty=True), FLAG_LIMIT, nullable=True)),
                                         dict(oversized=boolean())),
                           flag_environment=mapping(one_of('set', 'unset'), 8), note=NOTE)),
        requests=obj({name: request_shape(private=name in ('CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE'))
                      for name in ('SDKROOT', 'DEVELOPER_DIR', 'MACOSX_DEPLOYMENT_TARGET', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE')},
                     closed=True),
        deployment_target=text(16, re.compile(r'\d+\.\d+')),
        sdkroot=text(TEXT_LIMIT),
        build_directories=obj(dict(directories,
                                   fresh_mode=obj(dict(requested=boolean(), replacement=replacement)),
                                   cargo_admission=obj(dict(target_directory=text(TEXT_LIMIT), build_directory=text(TEXT_LIMIT)),
                                                       dict(layout_environment=mapping(text(TEXT_LIMIT, empty=True), 8))))),
        toolchain_stamp=obj(dict(scope_note=NOTE, projection=stamp_projection_shape())),
        output_target=obj(dict(system=one_of(output_target.SYSTEM), platform=one_of(output_target.PLATFORM),
                               architecture=one_of(output_target.ARCHITECTURE), container=one_of(output_target.CONTAINER),
                               cargo_triple=one_of(output_target.CARGO_TRIPLE), note=NOTE), closed=True),
        meson_machines=obj(dict(host=MACHINE, build=MACHINE, note=NOTE), closed=True))
    return obj(dict(
        schema_version=one_of(SCHEMA_VERSION),
        generated_at=text(32, re.compile(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ')),
        source=obj(dict(commit=text(64), describe=text(), dirty=boolean(), version=text(32, VERSION), build_number=text(16, re.compile(r'\d+')),
                        worker_identity=text(64, HEX64), input_hashes=obj({name: text(64, HEX64) for name in SOURCE_INPUTS}, closed=True))),
        toolchain=obj(dict(
            developer_dir=obj(dict(value=text(TEXT_LIMIT), source=one_of('DEVELOPER_DIR', 'xcode-select'))),
            sdk=obj(dict(path=text(TEXT_LIMIT), version=text(16, VERSION), build=text(32), source=one_of('SDKROOT named by the caller', 'xcrun --sdk macosx default'))),
            xcode=alternatives(('ok', obj(dict(version=text(), build=text()))),
                               ('unknown', obj(dict(reason=one_of(*FAILURE_KINDS)), dict(returncode=integer(nullable=True))))),
            compilers=obj(dict(c=OBSERVED_COMPILER, swift=Shape(lambda v, w, p: None))),
            rustc=rustc_shape(), cargo=TOOL, meson=TOOL, ninja=TOOL, python=INTERPRETER)),
        configuration=obj(configuration),
        outputs=array(output_shape(), 16, empty=False),
        signing=obj(dict(identity=text(), nested=array(obj(dict(rel_path=text(TEXT_LIMIT), leaf=text(nullable=True), team=text(nullable=True),
                                                                timestamp=boolean()), closed=True), 16), note=NOTE)),
        limits=array(NOTE, 8, empty=False)), closed=True)


RECORD_SHAPE = record_shape()


def record_shape_problems(record):
    """Every way a record departs from the documented shape of the current schema version: required fields present and
    not null, exact types, bounds, the variant's compilers and outputs, permitted unknowns only where the field policy
    allows them, and signing claims that repeat the outputs' own. Every output must be described as the output target
    and Meson's host machine as the target's. A record of any other version is refused, never interpreted."""
    version = record.get('schema_version') if type(record) is dict else None
    if type(version) is not int or version != SCHEMA_VERSION:
        return [f'record.schema_version is not {SCHEMA_VERSION}']
    problems = []
    RECORD_SHAPE(record, 'record', problems)
    if problems:
        return problems
    full = record['configuration']['knobs']['BUILD_XPC'] == '1'
    configuration = record['configuration']
    directories = configuration['build_directories']
    fresh = directories['fresh_mode']
    if fresh['requested'] != (configuration['knobs']['PW_FRESH_BUILD'] == '1'):
        problems.append('record.configuration fresh mode disagrees with PW_FRESH_BUILD')
    if fresh['requested'] != (fresh['replacement'] is not None):
        problems.append('record.configuration fresh mode must carry replacement observations exactly when requested')
    for name, _ in CACHE_AREAS:
        directory = directories[name]
        replacement = (fresh['replacement'] or {}).get(name)
        if replacement and (replacement['existed'] != replacement['removed'] or
                            directory['replaced_by_fresh_mode'] != replacement['removed'] or directory['state'] != 'created'):
            problems.append(f'record.configuration.build_directories.{name} disagrees with its fresh replacement')
        if directory['replaced_by_fresh_mode'] and not fresh['requested']:
            problems.append(f'record.configuration.build_directories.{name} claims replacement without fresh mode')
    options = configuration['meson_options']
    if options['status'] == 'ok':
        values = options['values']
        for name in FIXED_MESON_OPTIONS:
            if name.startswith('swift_') and not full:
                continue
            if name not in values:
                problems.append(f'record.configuration.meson_options.values.{name} is missing')
        if values.get('xpc') != full or values.get('inspection') != (configuration['knobs']['PW_INSPECTION'] == '1'):
            problems.append('record.configuration.meson_options disagrees with the build knobs')
    swift = record['toolchain']['compilers']['swift']
    if full:
        OBSERVED_COMPILER(swift, 'record.toolchain.compilers.swift', problems)
    elif swift != dict(status='not applicable', reason='partial build: the XPC pieces were not compiled'):
        problems.append('record.toolchain.compilers.swift is not the partial build\'s not-applicable entry')
    paths = [o['rel_path'] for o in record['outputs']]
    expected = FULL_OUTPUTS if full else PARTIAL_OUTPUTS
    if sorted(paths) != sorted(expected) or len(set(paths)) != len(paths):
        problems.append(f"record.outputs name {sorted(paths)}, not the {'full' if full else 'partial'} build's shipped executables")
    for output in record['outputs']:
        where = f"record.outputs[{output['rel_path']}]"
        controller = output['rel_path'] == CONTROLLER
        if controller != (output['sha256'] is None):
            problems.append(f'{where}.sha256 must be null exactly for the controller')
        if controller == ('signature' in output):
            problems.append(f'{where}.signature belongs to every nested output and never to the controller')
        if (output['rel_path'] in CARGO_TARGETS) != ('cargo' in output):
            problems.append(f'{where}.cargo belongs to the Cargo targets and only to them')
        if fresh['requested'] and output.get('cargo', {}).get('fresh') is True:
            problems.append(f'{where}.cargo.fresh reports reuse in a fresh build')
        if (output['architectures'] != [output_target.ARCHITECTURE] or output['container'] != output_target.CONTAINER
                or output['platform'] != output_target.PLATFORM):
            problems.append(f"{where} describes {output['container']} {' '.join(output['architectures'])} for platform "
                            f"{output['platform']}, not the output target (thin {output_target.ARCHITECTURE} for macOS)")
    if configuration['meson_machines']['host'] != output_target.MESON_HOST:
        problems.append("record.configuration.meson_machines.host is not the output target's Meson host machine")
    claimed = [(n['rel_path'], n['leaf'], n['team'], n['timestamp']) for n in record['signing']['nested']]
    actual = [(o['rel_path'], o['signature']['leaf'], o['signature']['team'], o['signature']['timestamp']) for o in record['outputs'] if 'signature' in o]
    if claimed != actual:
        problems.append('record.signing.nested does not repeat the outputs\' signature facts in order')
    minimum = record['configuration']['deployment_target']
    for output in record['outputs']:
        if normalize_version(output['minos']) != normalize_version(minimum):
            problems.append(f"record.outputs[{output['rel_path']}].minos {output['minos']} differs from the effective deployment target {minimum}")
        if normalize_version(output['sdk']) != normalize_version(record['toolchain']['sdk']['version']):
            problems.append(f"record.outputs[{output['rel_path']}].sdk {output['sdk']} differs from the selected SDK {record['toolchain']['sdk']['version']}")
    if record['configuration']['sdkroot'] != record['toolchain']['sdk']['path']:
        problems.append('record.configuration.sdkroot differs from the selected SDK path')
    request = configuration['requests']['SDKROOT']
    caller_sdk = request['state'] == 'set' and bool(request.get('value'))
    if caller_sdk != (record['toolchain']['sdk']['source'] == 'SDKROOT named by the caller'):
        problems.append('record.toolchain.sdk.source disagrees with the preserved SDKROOT request')
    child = record['toolchain']['rustc']['selection']['child_environment']
    if child['MACOSX_DEPLOYMENT_TARGET'] != minimum or child['SDKROOT'] != record['configuration']['sdkroot']:
        problems.append("record.toolchain.rustc.selection.child_environment disagrees with the effective deployment target or SDK")
    return problems


# ---- inspection of a record ----------------------------------------------------------------------------

def record_problems(app, manifest, *, read_metadata=output_metadata, observe=None, signatures=None):
    """Problems a record has against its manifest and bundle bytes, as (code, path, message) triples.

    The record must be of the current schema, have its documented shape
    (record_shape_problems) and agree with the manifest and the bytes on every
    hash, with each executable's load commands on UUID, platform, minimum, SDK
    and linker tools, with each executable's observed architectures and
    container, and, where the inspector supplies independently observed
    signature facts, with each nested signature it claims. The declared output
    target alone satisfies nothing: every claim is compared with the bytes."""
    observe = observe or output_observation
    app = Path(app)
    problems = []
    path = app / RECORD_PATH
    try:
        with path.open('rb') as stream:
            raw = stream.read(RECORD_LIMIT + 1)
        if len(raw) > RECORD_LIMIT:
            raise ValueError(f'record exceeds {RECORD_LIMIT} bytes')
        record = json.loads(raw)
    except (OSError, ValueError) as exc:
        return [('provenance', RECORD_PATH, f'record is not readable: {exc}')]
    if not isinstance(record, dict) or record.get('schema_version') != SCHEMA_VERSION:
        return [('provenance', RECORD_PATH, f'expected provenance schema_version={SCHEMA_VERSION}')]
    for problem in record_shape_problems(record):
        problems.append(('provenance', RECORD_PATH, problem))
    outputs = record.get('outputs')
    if not isinstance(outputs, list):
        return problems + [('provenance', RECORD_PATH, 'record outputs must be a list')]
    expected = shipped_outputs(app)
    seen = {}
    for entry in outputs:
        relative = entry.get('rel_path') if isinstance(entry, dict) else None
        if (not isinstance(relative, str) or not relative or PurePosixPath(relative).is_absolute()
                or '..' in PurePosixPath(relative).parts or str(PurePosixPath(relative)) != relative):
            problems.append(('provenance_output', str(relative), 'invalid output path'))
            continue
        if relative in seen:
            problems.append(('provenance_output', relative, 'duplicate output entry'))
            continue
        seen[relative] = entry
    for relative in expected:
        if relative not in seen:
            problems.append(('provenance_output', relative, 'shipped executable absent from the record'))
    for relative in seen:
        if relative not in expected:
            problems.append(('provenance_output', relative, 'record names an executable the bundle does not ship'))
    manifest_hashes = {e.get('rel_path'): e.get('sha256') for e in (manifest or {}).get('entries', []) if isinstance(e, dict)}
    for relative, entry in seen.items():
        if relative not in expected:
            continue
        actual = app / relative
        if not actual.is_file():
            problems.append(('provenance_output', relative, 'recorded executable is missing'))
            continue
        digest = sha256_file(actual)
        if relative == CONTROLLER:
            if entry.get('sha256') is not None:
                problems.append(('provenance_hash', relative, 'the controller hash cannot live inside the sealed record'))
        else:
            if entry.get('sha256') != digest:
                problems.append(('provenance_hash', relative, 'record hash differs from bundle bytes'))
            if manifest_hashes.get(relative) != entry.get('sha256'):
                problems.append(('provenance_hash', relative, 'record hash differs from the manifest entry'))
        metadata = read_metadata(actual)
        if metadata.get('status') != 'ok':
            problems.append(('provenance_metadata', relative, 'load commands are not readable'))
            continue
        for key in ('uuid', 'platform', 'minos', 'sdk', 'tools'):
            if entry.get(key) != metadata.get(key):
                problems.append(('provenance_metadata', relative, f'record {key} {entry.get(key)!r} differs from the load commands {metadata.get(key)!r}'))
        observed = observe(actual)
        for key in ('architectures', 'container'):
            if entry.get(key) != observed.get(key):
                problems.append(('provenance_metadata', relative, f'record {key} {entry.get(key)!r} differs from the bytes {observed.get(key)!r}'))
        if signatures is not None and relative != CONTROLLER:
            observed = signatures.get(relative)
            claimed = entry.get('signature')
            if observed is None:
                problems.append(('provenance_signature', relative, 'no independent signature observation for the claimed signature'))
            elif claimed != observed:
                claimed = claimed if isinstance(claimed, dict) else {}
                differing = sorted(k for k in set(observed) | set(claimed) if claimed.get(k) != observed.get(k))
                problems.append(('provenance_signature', relative, f"record signature facts differ from codesign's display: {', '.join(differing)}"))
    return problems


def read_zip_record(archive):
    """The record bytes and controller digest from a release ZIP; no archived code is executed.

    The record must be of the current schema version with its documented shape,
    and every nested output it names must hash to its recorded value. Load
    commands, architectures, containers and signatures are observed on temporary
    copies of the named executables, never trusted from the record. A record of
    any other version is refused."""
    import zipfile
    import signer_check
    with zipfile.ZipFile(archive) as zipped:
        try:
            with zipped.open('PolicyWitness.app/' + RECORD_PATH) as stream:
                record = stream.read(RECORD_LIMIT + 1)
        except KeyError:
            raise ValueError('the accepted ZIP carries no provenance record')
        if len(record) > RECORD_LIMIT:
            raise ValueError(f'the accepted ZIP carries a provenance record beyond {RECORD_LIMIT} bytes')

        def member_digest(relative):
            hasher = hashlib.sha256()
            try:
                with zipped.open('PolicyWitness.app/' + relative) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        hasher.update(block)
            except KeyError:
                raise ValueError(f'the accepted ZIP lacks {relative}, which its provenance record names')
            return hasher.hexdigest()
        controller = member_digest(CONTROLLER)
        try:
            data = json.loads(record.decode('utf-8'))
        except ValueError:
            raise ValueError('the accepted ZIP carries an unreadable provenance record')
        if not isinstance(data, dict) or data.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('the accepted ZIP carries an unsupported provenance record')
        problems = record_shape_problems(data)
        if problems:
            raise ValueError('the accepted ZIP carries an invalid provenance record: ' + '; '.join(problems[:5]))
        with tempfile.TemporaryDirectory(prefix='pw-archive-provenance-') as temporary:
            path = Path(temporary) / 'executable'
            for output in data['outputs']:
                relative = output['rel_path']
                if relative != CONTROLLER and member_digest(relative) != output['sha256']:
                    raise ValueError(f"the accepted ZIP's {relative} differs from its provenance record's hash")
                with zipped.open('PolicyWitness.app/' + relative) as source, path.open('wb') as destination:
                    shutil.copyfileobj(source, destination)
                metadata = output_metadata(path)
                if metadata.get('status') != 'ok' or any(metadata.get(k) != output[k] for k in ('uuid', 'platform', 'minos', 'sdk', 'tools')):
                    raise ValueError(f"the accepted ZIP's {relative} differs from its provenance record's load commands")
                observed = output_observation(path)
                if any(observed.get(k) != output[k] for k in ('architectures', 'container')):
                    raise ValueError(f"the accepted ZIP's {relative} differs from its provenance record's architectures or container")
                if relative != CONTROLLER:
                    observed = signer_check.signature(path)
                    if not observed.get('readable') or signer_check.facts(observed) != output['signature']:
                        raise ValueError(f"the accepted ZIP's {relative} differs from its provenance record's signature facts")
    return record, controller


# ---- the command line ---------------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    commands = parser.add_subparsers(dest='command', required=True)

    def owned_helper(name, function):
        sub = commands.add_parser(name)
        sub.add_argument('--root', required=True, type=Path, help='the checkout; the session, caches and stamp live at fixed paths below it')
        sub.set_defaults(run=function)
        return sub

    sub = owned_helper('session-start', session_start)
    sub.add_argument('--sdk-request-state', choices=('set', 'unset'), default='unset')
    sub.add_argument('--sdk-request-value', default='')
    sub.add_argument('--knob', action='append', default=[], metavar='NAME=VALUE')
    sub.add_argument('--describe', required=True)
    sub.add_argument('--commit', required=True)
    sub.add_argument('--version', required=True)
    sub.add_argument('--build-number', required=True)
    for name, function in (('stamp-check', stamp_check), ('stamp-extend', stamp_extend)):
        owned_helper(name, function).add_argument('--xpc', required=True, choices=('0', '1'))
    owned_helper('stamp-publish', stamp_publish)
    owned_helper('fresh-remove', fresh_remove)
    owned_helper('cargo-admit', cargo_admit)
    sub = owned_helper('cargo-judge', cargo_judge)
    sub.add_argument('--bin', action='append', required=True)
    sub.add_argument('--require-rebuilt', required=True, choices=('0', '1'))
    sub.add_argument('--rustflags-source', required=True, choices=('caller', 'script', 'none'))
    sub = owned_helper('sdk-check', sdk_check)
    sub.add_argument('--sdk-version', required=True)
    sub.add_argument('path', nargs='+')
    sub = owned_helper('output-check', output_check)
    sub.add_argument('--stage', required=True, choices=OUTPUT_STAGES)
    sub.add_argument('--app', type=Path, help='an assembled bundle whose every Mach-O, found by header, is checked')
    sub.add_argument('path', nargs='*')
    sub = owned_helper('worker-identity', worker_identity)
    sub.add_argument('--worker', required=True)
    sub.add_argument('--expected', required=True)
    sub = commands.add_parser('inspect')
    sub.add_argument('app', type=Path)
    sub.set_defaults(run=None)
    assert set(commands.choices) == set(SUBCOMMANDS), 'the subcommand list names every subparser'
    args = parser.parse_args(argv)
    try:
        if args.command == 'inspect':
            manifest = json.loads((args.app / 'Contents/Resources/Evidence/manifest.json').read_bytes())
            found = record_problems(args.app, manifest)
            for code, path, message in found:
                print(f'{code}: {path}: {message}')
            return 1 if found else 0
        return args.run(args)
    except Refusal as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return exc.status
    except OSError as exc:
        print(f'ERROR: build helper: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
