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
  cargo-admit     refuse Cargo intermediate state redirected outside the pinned target directory
  cargo-judge     record Cargo's per-target reuse judgment and fingerprint observations
  stamp-publish   publish the stamp after a successful fresh setup
  stamp-extend    after compiling: keep the stamp intact, or extend it with a newly discovered Swift compiler
  sdk-check       require every shipped Mach-O's SDK to agree with the selected SDK's version
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
anything. Every probe has a deadline (PROBE_TIMEOUT seconds) and an output
cap (PROBE_LIMIT bytes); a nonzero exit, empty output, malformed output,
overflow and a timeout are distinct failure kinds. A failure entry carries the
kind, the status and byte counts, never the tool's output. Published paths
under the home directory start with the HOME_MARKER; the exact paths stay in
the local stamp and session files.

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
import checkout_lock  # noqa: E402

SCHEMA_VERSION = 1
STAMP_SCHEMA_VERSION = 1
SESSION_SCHEMA_VERSION = 2
STAMP_NAME = 'pw-toolchain.json'
SESSION_NAME = 'pw-build-session.json'
MESSAGES_NAME = 'pw-build-messages.jsonl'
RECORD_PATH = 'Contents/Resources/Evidence/provenance.json'
PROBE_TIMEOUT = 20
PROBE_LIMIT = 64 * 1024
LINE_LIMIT = 200
HOME_MARKER = '<home>'
FRESH_REMEDY = 'set PW_FRESH_BUILD=1 to replace builddir/ and controller/target/release/'
PATH_POLICY = 'the build admits only real directories of this user inside the checkout'
TARGET = 'controller/target'
RELEASE = 'controller/target/release'
BUILDDIR = 'builddir'
SOURCE_INPUTS = ('meson.build', 'meson.options', 'controller/Cargo.lock', 'Info.plist',
                 'PolicyWitness.entitlements', 'runner/Services/PWRunner/Entitlements.plist')
FIXED_MESON_OPTIONS = ('buildtype', 'optimization', 'debug', 'warning_level', 'werror', 'strip', 'unity',
                       'b_ndebug', 'b_lto', 'b_coverage', 'b_pgo', 'b_bitcode', 'b_pie', 'b_staticpic',
                       'b_lundef', 'b_sanitize', 'c_std', 'c_args', 'c_link_args', 'swift_args',
                       'swift_link_args', 'inspection', 'xpc')
CARGO_SELECTION_ENV = ('RUSTC', 'RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_RUSTC',
                       'CARGO_BUILD_RUSTC_WRAPPER', 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER')
CARGO_FLAG_ENV = ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_RUSTFLAGS')
CARGO_LAYOUT_ENV = ('CARGO_BUILD_TARGET', 'CARGO_TARGET_DIR', 'CARGO_BUILD_BUILD_DIR', 'CARGO_HOME')
CONFIG_SELECTION_KEYS = ('rustc', 'rustc-wrapper', 'rustc-workspace-wrapper')
CONFIG_BUILD_KEYS = CONFIG_SELECTION_KEYS + ('rustflags', 'target', 'target-dir', 'build-dir')
ALLOWED_ENV = ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD', 'DEVELOPER_DIR', 'SDKROOT',
               'MACOSX_DEPLOYMENT_TARGET', 'RUSTFLAGS', 'PW_VERSION', 'PW_BUILD_NUMBER')
SUBCOMMANDS = ('session-start', 'stamp-check', 'fresh-remove', 'cargo-admit', 'cargo-judge', 'stamp-publish',
               'stamp-extend', 'sdk-check', 'worker-identity', 'inspect')
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


def bounded_line(text, limit=LINE_LIMIT):
    line = text.splitlines()[0].strip() if text.strip() else ''
    return line[:limit]


def probe(argv, *, cwd=None, env=None, timeout=PROBE_TIMEOUT, limit=PROBE_LIMIT):
    """Run a tool with a deadline and an output cap; its first line, or a bounded failure."""
    argv = [str(a) for a in argv]
    record = dict(status='failed', kind='launch_failed', argv=redact(argv), returncode=None, stdout_bytes=0, stderr_bytes=0)
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=err,
                                       stdin=subprocess.DEVNULL, start_new_session=True)
        except OSError:
            return record
        try:
            record['returncode'] = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            record['kind'] = 'timeout'
            return record
        record['stdout_bytes'] = out.tell()
        record['stderr_bytes'] = err.tell()
        if record['returncode'] != 0:
            record['kind'] = 'nonzero_exit'
            return record
        if record['stdout_bytes'] > limit:
            record['kind'] = 'output_overflow'
            return record
        out.seek(0)
        text = out.read(limit).decode('utf-8', errors='replace')
    if not text.strip():
        record['kind'] = 'empty_output'
        return record
    return dict(status='ok', argv=redact(argv), text=text, line=bounded_line(text))


def failed(record, kind='malformed_output'):
    """A probe record turned into a bounded failure of the given kind."""
    return dict(status='failed', kind=kind, argv=record.get('argv'), returncode=record.get('returncode', 0),
                stdout_bytes=record.get('stdout_bytes', len(record.get('text', '').encode())), stderr_bytes=record.get('stderr_bytes', 0))


def version_line(record, pattern=r'\d'):
    """A probe's first line as a version identity, or a malformed-output failure."""
    if record['status'] != 'ok':
        return record
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

    Every component of builddir/, controller/target/ and controller/target/release/
    below the checkout root must be a real directory of this user, or absent, and
    the session destination an absent path or a regular file of this user with one
    link. Each admitted directory is held open; writes and removals are made
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
            self.admit(TARGET, create=create_target)
            if TARGET in self.fds:
                self.admit(RELEASE)
                self.admit_file(TARGET, SESSION_NAME)
            self.admit(BUILDDIR)
        except BaseException:
            self.close()
            raise

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
    with build_scope(args.root, create_target=True, session=False) as state:
        if state.admission.requests is None:
            raise Refusal(checkout_lock.NO_REQUESTS, 2)
        knobs = {}
        for item in args.knob:
            name, _, value = item.partition('=')
            knobs[name] = value
        state.session = dict(schema_version=SESSION_SCHEMA_VERSION, lock_nonce=state.admission.nonce,
                             started_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), root=str(state.root),
                             knobs=knobs, stamp=dict(describe=args.describe, commit=args.commit, version=args.version,
                                                     build_number=args.build_number, dirty=args.describe.endswith('-dirty')),
                             sdk_source=args.sdk_source, requests=state.admission.requests.to_json(),
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
    lines = [bounded_line(line) for line in found['text'].splitlines() if line.strip()][:2]
    version = next((line[len('Xcode '):] for line in lines if line.startswith('Xcode ')), None)
    build = next((line[len('Build version '):] for line in lines if line.startswith('Build version ')), None)
    if not version or not build:
        return dict(status='unknown', reason='malformed_output')
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
        out[language] = dict(command=[str(c) for c in entry['exelist']][:8], id=str(entry.get('id', ''))[:LINE_LIMIT],
                             version=str(entry.get('version', ''))[:LINE_LIMIT],
                             full_version=None if entry.get('full_version') is None else str(entry['full_version'])[:LINE_LIMIT])
    return out


def compiler_observation(command, builddir, env):
    """The configured command probed for its identity in the build directory's context."""
    found = version_line(probe([*command, '--version'], cwd=str(builddir) if Path(builddir).is_dir() else None, env=env))
    if found['status'] != 'ok':
        return dict(found, command=command)
    return dict(status='ok', command=command, identity=found['line'])


def cargo_configuration_files(manifest_dir, env):
    """Cargo configuration files in the discovery chain, with the build-relevant keys each names (never values)."""
    candidates = []
    directory = Path(manifest_dir).resolve()
    while True:
        for name in ('config.toml', 'config'):
            candidates.append(directory / '.cargo' / name)
        if directory.parent == directory:
            break
        directory = directory.parent
    home = Path(env.get('CARGO_HOME') or (Path(env.get('HOME', '/')) / '.cargo'))
    for name in ('config.toml', 'config'):
        candidates.append(home / name)
    files = []
    for path in candidates:
        if not path.is_file():
            continue
        keys = set()
        section = ''
        try:
            lines = path.read_text(errors='replace').splitlines()[:2000]
        except OSError:
            files.append(dict(path=redact(str(path)), readable=False))
            continue
        for line in lines:
            text = line.split('#', 1)[0].strip()
            header = re.match(r'^\[\s*([^\]]+?)\s*\]$', text)
            if header:
                section = header.group(1).strip().strip('"').strip("'")
                continue
            key = re.match(r'^([A-Za-z0-9_.\-"\']+)\s*=', text)
            if not key:
                continue
            name = key.group(1).strip('"').strip("'")
            full = f'{section}.{name}' if section else name
            if full.startswith('build.') and full[len('build.'):] in CONFIG_BUILD_KEYS:
                keys.add(full)
            elif full.startswith('target.') and (full.endswith('.rustflags') or full.endswith('.linker')):
                keys.add('target.<rule>.' + full.rsplit('.', 1)[1])
        files.append(dict(path=redact(str(path)), readable=True, keys=sorted(keys)))
    return files


def rustc_observation(manifest_dir, env):
    """The Rust compiler Cargo will select from the environment and PATH, probed; configuration files are named, not resolved."""
    files = cargo_configuration_files(manifest_dir, env)
    unresolved = sorted({key for f in files for key in f.get('keys', []) if key[len('build.'):] in CONFIG_SELECTION_KEYS})
    selection = {}
    for name in CARGO_SELECTION_ENV:
        if name in env:
            selection[name] = redact(env[name])
    if env.get('RUSTC'):
        command, source = env['RUSTC'], 'RUSTC'
    elif env.get('CARGO_BUILD_RUSTC'):
        command, source = env['CARGO_BUILD_RUSTC'], 'CARGO_BUILD_RUSTC'
    else:
        command, source = shutil.which('rustc', path=env.get('PATH')), 'PATH'
    out = dict(selection_environment=selection, configuration_files=files, unresolved_configuration=unresolved)
    if unresolved:
        out.update(status='failed', kind='unresolved_configuration', source=source,
                   detail='a Cargo configuration file defines ' + ', '.join(unresolved) + '; set RUSTC or CARGO_BUILD_RUSTC explicitly')
        return out
    if not command:
        out.update(status='failed', kind='launch_failed', source=source, detail='no rustc on PATH')
        return out
    found = probe([command, '-vV'], env=env)
    if found['status'] != 'ok':
        out.update(found, command=redact(command), source=source)
        return out
    fields = dict(re.findall(r'^(release|commit-hash|host|binary|LLVM version): (.+)$', found['text'], re.M))
    if 'release' not in fields or 'host' not in fields:
        out.update(failed(found), command=redact(command), source=source)
        return out
    out.update(status='ok', command=redact(command), exact_command=command, source=source, identity=found['line'],
               release=fields['release'][:LINE_LIMIT], commit_hash=fields.get('commit-hash', '')[:LINE_LIMIT],
               host=fields['host'][:LINE_LIMIT], llvm_version=fields.get('LLVM version', '')[:LINE_LIMIT])
    wrappers = {}
    for name, key in (('RUSTC_WRAPPER', 'wrapper'), ('CARGO_BUILD_RUSTC_WRAPPER', 'wrapper'),
                      ('RUSTC_WORKSPACE_WRAPPER', 'workspace_wrapper'), ('CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER', 'workspace_wrapper')):
        if env.get(name) and key not in wrappers:
            path = Path(env[name])
            entry = dict(source=name, command=redact(env[name]))
            if path.is_file():
                entry['sha256'] = sha256_file(path)
            wrappers[key] = entry
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


def observe_toolchain(builddir, manifest_dir, env, *, xpc, compilers=None):
    """Every toolchain observation the stamp and the record use; compilers come from the directory or the stamp."""
    if compilers is None:
        compilers = read_compilers(builddir) or {}
    observed = {}
    for language, entry in compilers.items():
        observed[language] = dict(configured=entry, observed=compiler_observation(entry['command'], builddir, env))
    return dict(developer_dir=developer_dir_observation(env), sdk=sdk_observation(env), xcode=xcode_observation(env),
                compilers=observed, rustc=rustc_observation(manifest_dir, env),
                cargo=tool_observation('cargo', env), meson=tool_observation('meson', env), ninja=tool_observation('ninja', env),
                xpc=bool(xpc))


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
    return data


def stamp_record(fields, *, xpc, source_dir, published_at=None, extended_at=None):
    return dict(schema_version=STAMP_SCHEMA_VERSION, scope=dict(xpc=bool(xpc)), source_dir=str(source_dir),
                published_at=published_at or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                extended_at=extended_at, fields=fields)


def compare_fields(stamped, current, names):
    """The first differing field, or None; a value absent on either side is a difference, never equality."""
    for name in names:
        if name not in stamped or stamped[name] is None or current.get(name) is None:
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
    recorded = read_compilers(builddir) or {}
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
    observation = observe_toolchain(builddir, root / 'controller', env, xpc=swift_applicable, compilers=compilers)
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
    print(f'ok: {STAMP_NAME} agrees with the selected toolchain ({len(names)} fields)')
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
    observation = observe_toolchain(builddir, root / 'controller', os.environ, xpc=xpc, compilers=compilers)
    fields = compatibility_fields(observation, xpc=xpc)
    for name, value in fields.items():
        if value is None:
            raise Refusal(f'required toolchain observation failed: {name}; a stamp never records an unknown value', 2)
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
    observation = observe_toolchain(builddir, root / 'controller', os.environ, xpc=xpc, compilers=compilers)
    state = 'intact'
    if xpc and not stamp['scope'].get('xpc'):
        # Swift is newly applicable: validate the discovered compiler, then extend without touching other fields.
        current = compatibility_fields(observation, xpc=True)
        for name in ('compilers.swift.command', 'compilers.swift.identity'):
            if current.get(name) is None:
                raise Refusal(f'required toolchain observation failed: {name}; the newly discovered Swift compiler cannot be recorded', 2)
        retained = {k: v for k, v in stamp['fields'].items()}
        difference = compare_fields(retained, current, [k for k in retained if not k.startswith('compilers.swift.')])
        if difference is not None:
            name, before, now, kind = difference
            raise Refusal(f'{STAMP_NAME} cannot be extended: {name} is {redact(before)!r} in the stamp but {redact(now)!r} now: {FRESH_REMEDY}', 1)
        retained.update({name: current[name] for name in ('compilers.swift.command', 'compilers.swift.identity')})
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
    """Remove the two owned cache areas, both admitted before either is touched, through their held descriptors."""
    session, root = state.session, state.root
    targets = {'builddir': BUILDDIR, 'cargo_release': RELEASE}
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
    session['cargo_release'] = dict(existed_before=replacement['cargo_release']['existed'], fresh_replaced=replacement['cargo_release']['removed'])
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
    env = dict(os.environ, CARGO_TARGET_DIR=str(pinned))
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
        build_directory = Path(metadata.get('build_directory', metadata['target_directory']))
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
    session['cargo_release'] = dict(session.get('cargo_release', {}), existed_before=state.paths.present(RELEASE),
                                    fresh_replaced=session.get('cargo_release', {}).get('fresh_replaced', False))
    state.save()
    print(f'ok: Cargo intermediate and final release state admitted under {pinned}')
    return 0


def artifact_messages(state, names):
    """The last compiler-artifact message per requested executable name, from Cargo's own report."""
    found = {}
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
        name = (message.get('target') or {}).get('name')
        if name in names and message.get('executable'):
            found[name] = message
    return found


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
    out.update(status='observed', rustflags=[f[:LINE_LIMIT] for f in data['rustflags'][:64]],
               rustc_fingerprint=str(data.get('rustc')) if isinstance(data.get('rustc'), int) else None,
               profile_fingerprint=str(data.get('profile')) if isinstance(data.get('profile'), int) else None,
               limitation='hash fields are opaque unit fingerprints; they do not identify a compiler or a wrapper')
    return out


def flag_source(effective, env, script_default):
    """Which requested source the effective flags equal, when one does; otherwise an explicit unresolved kind."""
    if effective is None:
        return dict(kind='unknown', detail='effective flags were not observed')
    candidates = []
    if 'CARGO_ENCODED_RUSTFLAGS' in env:
        candidates.append(('CARGO_ENCODED_RUSTFLAGS', [t for t in env['CARGO_ENCODED_RUSTFLAGS'].split('\x1f') if t]))
    if 'CARGO_BUILD_RUSTFLAGS' in env:
        candidates.append(('CARGO_BUILD_RUSTFLAGS', env['CARGO_BUILD_RUSTFLAGS'].split()))
    if 'RUSTFLAGS' in env:
        candidates.append((script_default, env['RUSTFLAGS'].split()))
    for kind, tokens in candidates:
        if tokens == effective:
            return dict(kind=kind, tokens=tokens[:64])
    if not effective:
        return dict(kind='none', detail='no additional flags')
    return dict(kind='cargo configuration or target rules', detail='no named environment source equals the effective flags; configuration files are not resolved by this record')


def cargo_judge(args):
    with build_scope(args.root) as state:
        return cargo_judge_admitted(state, args)


def cargo_judge_admitted(state, args):
    session = state.session
    target_dir = state.root / TARGET
    env = dict(os.environ)
    messages = artifact_messages(state, set(args.bin))
    judgments = {}
    script_default = {'caller': 'RUSTFLAGS (caller)', 'script': 'RUSTFLAGS (script default)', 'none': 'RUSTFLAGS'}[args.rustflags_source]
    for name in args.bin:
        message = messages.get(name)
        if message is None:
            judgments[name] = dict(status='unavailable', fresh=None)
            continue
        fingerprint = fingerprint_observation(message, target_dir)
        judgments[name] = dict(status='reported', fresh=bool(message.get('fresh')), profile=message.get('profile'),
                               package_id=redact(message['package_id']), executable=redact(message['executable']),
                               exact_executable=message['executable'], fingerprint=fingerprint,
                               effective_rustflags=fingerprint.get('rustflags'),
                               rustflags_source=flag_source(fingerprint.get('rustflags'), env, script_default))
    session.setdefault('cargo', {})['judgments'] = judgments
    session['cargo']['flag_environment'] = {name: ('set' if name in env else 'unset') for name in CARGO_FLAG_ENV}
    session['cargo']['requested_rustflags'] = dict(source=args.rustflags_source, tokens=env.get('RUSTFLAGS', '').split()[:64])
    state.save()
    reused = [name for name, j in judgments.items() if j['status'] != 'reported' or j['fresh']]
    if args.require_rebuilt == '1' and reused:
        raise Refusal('fresh mode requires Cargo to report rebuilding every shipped target, but ' + ', '.join(
            f"{name} ({'reused' if judgments[name].get('fresh') else 'no judgment'})" for name in reused), 1)
    summary = ', '.join(f"{name}: {'reused' if j.get('fresh') else 'rebuilt' if j['status'] == 'reported' else 'no judgment'}" for name, j in judgments.items())
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
                            cargo=toolchain['cargo'], meson=toolchain['meson'], ninja=toolchain['ninja'])
    toolchain_record['sdk']['path'] = redact(toolchain_record['sdk']['path'])
    toolchain_record['rustc']['selection_note'] = ('the command Cargo resolves from the environment and PATH, probed now; '
                                                   'configuration files are listed, not resolved')
    builddir_state = session.get('builddir', {})
    cargo_state = session.get('cargo_release', {})
    fresh = session.get('fresh', {})
    stamp_projection = None
    try:
        data = read_stamp(root / 'builddir')
        stamp_projection = dict(scope=data['scope'], published_at=data.get('published_at'), extended_at=data.get('extended_at'),
                                fields={k: redact(v) for k, v in data['fields'].items()})
    except Refusal as exc:
        stamp_projection = dict(status='unavailable', reason=str(exc)[:LINE_LIMIT])
    requested = (session.get('cargo') or {}).get('requested_rustflags', {})
    configuration = dict(
        knobs={name: knobs.get(name) for name in ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD')},
        meson_options=session.get('meson_options', dict(status='unknown')),
        rustflags=dict(requested=dict(source=requested.get('source'), tokens=requested.get('tokens', [])),
                       flag_environment=(session.get('cargo') or {}).get('flag_environment', {}),
                       note='effective flags are recorded per output from Cargo\'s fingerprint; they are additional compiler arguments, not the complete command'),
        deployment_target=session.get('environment', {}).get('MACOSX_DEPLOYMENT_TARGET'),
        sdkroot=redact(session.get('environment', {}).get('SDKROOT')),
        build_directories=dict(
            builddir=dict(state='reused' if builddir_state.get('configured_before') else 'created',
                          replaced_by_fresh_mode=bool(builddir_state.get('fresh_replaced')),
                          stamp=builddir_state.get('stamp_after_compile') or builddir_state.get('stamp_state')),
            cargo_release=dict(state='reused' if cargo_state.get('existed_before') else 'created',
                               replaced_by_fresh_mode=bool(cargo_state.get('fresh_replaced'))),
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
        entry = dict(rel_path=relative, uuid=metadata['uuid'], platform=metadata['platform'], minos=metadata['minos'],
                     sdk=metadata['sdk'], tools=metadata['tools'][:8])
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
    text = json.dumps(record, indent=2, sort_keys=True)
    forbidden = forbidden_content(text, os.environ)
    if forbidden:
        raise Refusal('the record would publish ' + forbidden, 2)
    if len(text) > 256 * 1024:
        raise Refusal('the record exceeds its size bound', 2)
    return record


def forbidden_content(text, env):
    """A description of forbidden content in the record text, or None."""
    home = env.get('HOME')
    if home and home != '/' and home in text:
        return 'a home-prefixed path'
    path = env.get('PATH')
    if path and path in text:
        return 'the PATH value'
    return None


# ---- inspection of a record ----------------------------------------------------------------------------

def record_problems(app, manifest, *, read_metadata=output_metadata):
    """Problems a record has against its manifest and bundle bytes, as (code, path, message) triples."""
    app = Path(app)
    problems = []
    path = app / RECORD_PATH
    try:
        record = json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        return [('provenance', RECORD_PATH, f'record is not readable: {exc}')]
    if not isinstance(record, dict) or record.get('schema_version') != SCHEMA_VERSION:
        return [('provenance', RECORD_PATH, f'expected provenance schema_version={SCHEMA_VERSION}')]
    for key in ('source', 'toolchain', 'configuration', 'outputs', 'signing'):
        if key not in record:
            problems.append(('provenance', RECORD_PATH, f'record lacks {key}'))
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
        for key in ('uuid', 'platform', 'minos', 'sdk'):
            if entry.get(key) != metadata.get(key):
                problems.append(('provenance_metadata', relative, f'record {key} {entry.get(key)!r} differs from the load commands {metadata.get(key)!r}'))
    return problems


def read_zip_record(archive):
    """The record bytes and the controller's digest from a release ZIP, read without extraction."""
    import zipfile
    with zipfile.ZipFile(archive) as zipped:
        try:
            record = zipped.read('PolicyWitness.app/' + RECORD_PATH)
        except KeyError:
            raise ValueError('the accepted ZIP carries no provenance record')
        hasher = hashlib.sha256()
        with zipped.open('PolicyWitness.app/' + CONTROLLER) as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                hasher.update(block)
    data = json.loads(record.decode('utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('the accepted ZIP carries an unsupported provenance record')
    return record, hasher.hexdigest()


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
    sub.add_argument('--knob', action='append', default=[], metavar='NAME=VALUE')
    sub.add_argument('--describe', required=True)
    sub.add_argument('--commit', required=True)
    sub.add_argument('--version', required=True)
    sub.add_argument('--build-number', required=True)
    sub.add_argument('--sdk-source', default='default', choices=('default', 'caller'))
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
