"""Declared fixture inputs and the copier that expands them into a disposable checkout.

A fixture holds exactly what its declarations name: a generator's `input_paths`,
a rule table's declared inputs and helper modules, the build entry's files, or
a literal list. Expansion is discovery; validation stays with the generator or
rule, so a malformed manifest still reaches the command that refuses it. The
copier reports what it copied and what that cost. Declarations are a reviewed
account of what is read, not a claim that every read is declared: review new
reads and imports against them.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / 'docs') not in sys.path:
    sys.path.insert(0, str(ROOT / 'docs'))
import markdown_reader  # noqa: E402
import repository_tree  # noqa: E402
from repository_tree import directory, pattern, required  # noqa: E402

GENERATORS = ('contract', 'worker_identity', 'limits', 'architecture', 'build')
# What build.sh admits and reads before its first generator check: the script, the lock front end and its Python
# resolver, the SDK guard, the plists and entitlements it validates, and the augment profiles it inventories.
BUILD_ENTRY = (required('build.sh'), required('tests/lib/checkout_lock.py'), required('tests/lib/checkout_lock.sh'),
               required('tests/lib/python_start.sh'), required('tests/lib/sdk_guard.sh'), required('Info.plist'),
               required('PolicyWitness.entitlements'), required('runner/Services/PWRunner/Info.plist'),
               required('runner/Services/PWRunner/Entitlements.plist'), pattern('runner/augments/*.sb'))
# What the script's later steps read before the gate a build-entry control stops at: the version and provenance
# helpers, cargo configuration and its vendored TOML reader, and the signing inventory helpers.
BUILD_SCRIPT_HELPERS = (required('tests/lib/build_provenance.py'), required('tests/lib/cargo_config.py'),
                        directory('tests/lib/vendor/tomli'), required('tests/lib/vendor/README.md'),
                        required('tests/lib/artifact.py'), required('tests/build-evidence.py'),
                        required('tests/lib/signer_check.py'), required('tests/lib/output_target.py'))


@dataclass(frozen=True)
class Copied:
    files: int
    directories: int
    bytes: int
    seconds: float


def generator_module(name, root=ROOT):
    """The generator loaded from `root` under a module name of its own, so several roots can coexist."""
    path = Path(root) / f'docs/generate_{name}.py'
    spec = importlib.util.spec_from_file_location(f'fixture_inputs_{name}_{abs(hash(str(path)))}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generator_inputs(root, name):
    """Every path generator `name` reads under `root`, from the generator's own declarations.

    The worker identity generator hashes its own source, so its adapter lives here: its `source_paths`
    discovery plus its targets."""
    root = Path(root)
    gen = generator_module(name)
    if name == 'worker_identity':
        return sorted({*gen.source_paths(root), *gen.TARGETS})
    return sorted(gen.input_paths(root))


def expand(root, inputs, helpers=()):
    """The relative paths a declaration list selects under `root`, plus named helper modules."""
    return sorted(set(repository_tree.Tree(root).expand(tuple(inputs))) | set(helpers))


def rule_inputs(root, rules):
    """The union of every rule's declared inputs and helpers over `root`."""
    found = set()
    for rule in rules:
        found.update(expand(root, rule.inputs, rule.helpers))
    return sorted(found)


def build_entry_inputs(root=ROOT):
    return expand(root, BUILD_ENTRY)


def build_script_inputs(root=ROOT):
    return expand(root, BUILD_ENTRY + BUILD_SCRIPT_HELPERS)


def reader_inputs(root=ROOT):
    """The Markdown reader and its vendored parser."""
    return list(markdown_reader.source_files(Path(root)))


def copy_declared(root, destination, paths, extra=()):
    """Copy each named relative path from `root` into `destination`.

    A directory entry is created empty; a file symlink is recreated as a symlink; a missing path is a
    refusal, since a declaration names what must exist. Returns what was copied and the time it took."""
    root, destination = Path(root), Path(destination)
    start = time.perf_counter()
    files = directories = size = 0
    for relative in sorted(set(paths) | set(extra)):
        source = root / relative
        target = destination / relative
        if source.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(os.readlink(source), target)
            files += 1
        elif source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            directories += 1
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            files += 1
            size += source.stat().st_size
        else:
            raise repository_tree.MissingInput(relative, 'no such file')
    return Copied(files, directories, size, time.perf_counter() - start)


def snapshot(root):
    """Every file under the fixture, by relative path, including sentinels and files no generator owns."""
    root = Path(root)
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}
