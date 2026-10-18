"""The output target every executable the build delivers must satisfy: a thin arm64 Mach-O for macOS.

PolicyWitness's supported product is macOS code for Apple Silicon. This module
states that target once and decides, from a file's bytes and two tools'
reports about them, whether one output satisfies it. It never executes the
file and never asks about the machine it runs on: where the build ran, and
whether any process was translated, are not facts about an output.

Observation and decision are kept apart. `observe` reads the Mach-O header for
the container (a thin Mach-O with its file type, or a fat container with its
slice count), takes the architecture names from `lipo -archs`, and takes a thin
file's platform from its LC_BUILD_VERSION through the caller's load-command
reader. `target_problems` then compares an observation with the target: a thin
container, exactly the one architecture arm64 (arm64e is another
architecture, and a list that merely contains arm64 is not the target), and
the macOS platform. A missing or unreadable file, a file that is not a Mach-O,
a truncated header, a failed, empty, malformed or inconsistent tool report and
an unknown architecture name are observation problems; they refuse too, never
pass.

`runnable_code` lists the Mach-O files below a directory that can run or be
loaded: every regular file whose header is a Mach-O or fat container, except
dSYM companion files (file type MH_DSYM), whose debug metadata is not a
runnable output's platform contract. The scan reads headers, not names or
manifests, so a renamed or unlisted executable is still found.

The bounded probe and the load-command reader are the caller's
(`build_provenance.probe` and `build_provenance.output_metadata`), passed in
the way cargo_config takes its probe, so this module imports neither.
"""
import os
from pathlib import Path
import re
import stat
import struct

SYSTEM = 'macos'
PLATFORM = '1'            # LC_BUILD_VERSION platform 1, PLATFORM_MACOS
ARCHITECTURE = 'arm64'
CONTAINER = 'thin'
CARGO_TRIPLE = 'aarch64-apple-darwin'
DECLARED = dict(system=SYSTEM, platform=PLATFORM, architecture=ARCHITECTURE, container=CONTAINER, cargo_triple=CARGO_TRIPLE)
PLATFORM_NAMES = {'1': 'macOS', '2': 'iOS', '3': 'tvOS', '4': 'watchOS', '5': 'bridgeOS', '6': 'Mac Catalyst',
                  '7': 'iOS simulator', '8': 'tvOS simulator', '9': 'watchOS simulator', '10': 'DriverKit',
                  '11': 'visionOS', '12': 'visionOS simulator'}
# The architecture names lipo prints for Apple's Mach-O CPU types; any other name is not understood here.
ARCHITECTURES = frozenset({'arm64', 'arm64e', 'arm64_32', 'x86_64', 'x86_64h', 'i386', 'armv6', 'armv6m', 'armv7',
                           'armv7s', 'armv7k', 'armv7m', 'armv7em', 'ppc', 'ppc64'})
LIPO = '/usr/bin/lipo'
THIN_MAGICS = {b'\xcf\xfa\xed\xfe': ('<', 32), b'\xce\xfa\xed\xfe': ('<', 28),
               b'\xfe\xed\xfa\xcf': ('>', 32), b'\xfe\xed\xfa\xce': ('>', 28)}
FAT_MAGICS = (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf')
MH_DSYM = 0xa
# A fat header names its slice count; a larger count is not a Mach-O container (a Java class file shares the magic).
SLICE_LIMIT = 16
NAME_LIMIT = 32


def header(path):
    """What a file's first bytes declare: a thin Mach-O with its file type, a fat container with its slice count,
    a truncated Mach-O header, or None for any other file. OSError propagates: an unreadable file is not a non-Mach-O."""
    with open(path, 'rb') as stream:
        data = stream.read(32)
    magic = data[:4]
    if magic in THIN_MAGICS:
        order, size = THIN_MAGICS[magic]
        if len(data) < size:
            return dict(container='thin', truncated=True)
        return dict(container='thin', filetype=struct.unpack(order + 'I', data[12:16])[0])
    if magic in FAT_MAGICS:
        if len(data) < 8:
            return dict(container='fat', truncated=True)
        slices = struct.unpack('>I', data[4:8])[0]
        if not 0 < slices <= SLICE_LIMIT:
            return None
        return dict(container='fat', slices=slices)
    return None


def observe(path, *, probe, read_metadata):
    """The container, file type, architecture names and platform one file carries, with every observation problem.

    probe runs `lipo -archs` with the caller's bounds; read_metadata reads a
    thin file's load commands. A fat container's platform is per slice and is
    not read: the container alone refuses it."""
    path = str(path)
    out = dict(path=path, container=None, slices=None, filetype=None, architectures=None, platform=None, problems=[])
    try:
        found = header(path)
    except OSError as exc:
        out['problems'].append(f'unreadable ({exc.__class__.__name__})')
        return out
    if found is None:
        out['problems'].append('not a Mach-O file')
        return out
    out['container'] = found['container']
    if found.get('truncated'):
        out['problems'].append('the Mach-O header is truncated')
        return out
    out['slices'], out['filetype'] = found.get('slices'), found.get('filetype')
    listed = probe([LIPO, '-archs', path], limit=4096, stderr_limit=4096)
    if listed['status'] != 'ok':
        out['problems'].append(f"lipo -archs failed ({listed['kind']})")
    else:
        names = listed['text'].split()
        expected = 1 if out['container'] == 'thin' else out['slices']
        if len(names) > SLICE_LIMIT or any(len(name) > NAME_LIMIT for name in names):
            out['problems'].append('lipo -archs reported an oversized list')
        elif len(names) != expected:
            out['problems'].append(f'lipo -archs reported {len(names)} architecture(s) for a {out["container"]} file with {expected}')
        elif any(name not in ARCHITECTURES for name in names):
            out['problems'].append('lipo -archs reported an unknown architecture: ' + ' '.join(n for n in names if n not in ARCHITECTURES))
        else:
            out['architectures'] = names
    if out['container'] == 'thin':
        metadata = read_metadata(path)
        platform = metadata.get('platform')
        if platform is None or not re.fullmatch(r'\d{1,4}', str(platform)):
            out['problems'].append('no readable LC_BUILD_VERSION platform')
        else:
            out['platform'] = platform
    return out


def target_problems(observation):
    """Why an observation does not satisfy the output target, or [] when it does. Observation problems come first
    and are reasons on their own; an unknown fact never satisfies the target."""
    if observation['problems']:
        return list(observation['problems'])
    found = []
    names = ' '.join(observation['architectures'])
    if observation['container'] != CONTAINER:
        found.append(f"a fat container with {observation['slices']} slice(s) ({names}), not a thin Mach-O")
    if observation['architectures'] != [ARCHITECTURE]:
        found.append(f'architecture {names}, not exactly {ARCHITECTURE}')
    if observation['container'] == CONTAINER and observation['platform'] != PLATFORM:
        name = PLATFORM_NAMES.get(observation['platform'], 'unknown')
        found.append(f"platform {observation['platform']} ({name}), not macOS ({PLATFORM})")
    return found


def describe(observation):
    """One bounded line: the path and why it is outside the target, or that it satisfies it."""
    problems = target_problems(observation)
    if problems:
        return f"{observation['path']}: " + '; '.join(problems)
    return f"{observation['path']}: thin {ARCHITECTURE} Mach-O for macOS"


def runnable_code(root):
    """Every regular file below root, in path order, whose header is a Mach-O or fat container, except dSYM companion
    files. Symbolic links are neither followed nor listed; an unreadable directory or file raises."""
    root = Path(root)
    found = []

    def onerror(exc):
        raise exc

    for directory, names, files in os.walk(root, onerror=onerror, followlinks=False):
        names.sort()
        for name in sorted(files):
            path = Path(directory) / name
            if not stat.S_ISREG(path.lstat().st_mode):
                continue
            kind = header(path)
            if kind is None or (kind['container'] == 'thin' and kind.get('filetype') == MH_DSYM):
                continue
            found.append(path)
    return found
