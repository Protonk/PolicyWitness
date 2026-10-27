"""Explicit-root access to a checkout for the drift checks and generators.

A `Tree` names one root. An inventory walks a named `Scope` top-down and
removes excluded directories before descending, so a pruned subtree is never
listed. A read observes the current bytes under that root. Parse reuse is keyed
by content and diagnostic name and lasts as long as the `Tree`, which lasts for
one immutable scenario: creating, deleting or restoring files needs a fresh
`Tree`. Nothing here writes, starts a subprocess or imports a suite, generator
or parser.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


class InputError(Exception):
    """A selected or declared input could not be read from the tree."""

    def __init__(self, relative, reason):
        super().__init__(f'{relative}: {reason}')
        self.relative = relative
        self.reason = reason


class MissingInput(InputError):
    """A required input does not exist."""


class UnreadableInput(InputError):
    """An input exists but its bytes or text cannot be read."""


@dataclass(frozen=True)
class Scope:
    """A named inventory: entries under `base` whose names end with one of `suffixes`.

    `pruned` holds root-relative prefixes. A directory is removed before descent
    when its relative path plus '/' starts with a prefix, and a matching entry is
    excluded when its relative path starts with one; `builddir` therefore also
    excludes `builddir-old/`, while `records/` keeps `records-old/`. `hidden`
    excludes every path with a component beginning with '.'. A directory symlink
    is never followed. An entry whose name matches is a candidate whatever it is:
    a file symlink, a broken symlink or a directory named with the suffix, so a
    reader sees the failure instead of a silent omission. Empty `suffixes` select
    every entry that is not a directory. Enumeration errors are ignored and an
    entry whose metadata cannot be read is kept as a candidate without descent,
    as the standard library's recursive glob behaves."""
    name: str
    suffixes: tuple[str, ...]
    base: str = ''
    pruned: tuple[str, ...] = ()
    hidden: bool = False
    recursive: bool = True

    def excludes(self, relative):
        return relative.startswith(self.pruned)


# Documents that are not the repository's own: investigation records, local
# archives and evidence, scratch, build state and vendored sources.
COMMAND_DOCUMENTS = Scope('repository command documents', ('.md',),
                          pruned=('records/', 'dist/archive/', 'dist/evidence/', 'tests/out/', '.tmp/', 'builddir',
                                  'controller/target/', 'tests/lib/vendor/', 'runner/.build/'),
                          hidden=True)
# Every shell script under tests/ except retained output; hidden and vendored paths stay included.
TEST_SHELL_SCRIPTS = Scope('test shell scripts', ('.sh',), base='tests', pruned=('tests/out/',))


@dataclass(frozen=True)
class Input:
    """One declared input of a rule or generator.

    `file` must exist; `optional` is used when present; `directory` selects the
    non-directory entries under a directory, by suffix when suffixes are given,
    recursively unless stated otherwise; `scope` selects a named inventory. A declaration is an auditable account of
    what is read, not a claim of complete program reachability."""
    kind: str
    path: str = ''
    suffixes: tuple[str, ...] = ()
    recursive: bool = True
    scope: Scope | None = None


def required(path):
    return Input('file', path)


def optional(path):
    return Input('optional', path)


def directory(path, suffixes=(), recursive=True):
    return Input('directory', path, tuple(suffixes), recursive)


def inventory(scope):
    return Input('scope', scope=scope)


class Tree:
    """One checkout root; every path in or out is root-relative POSIX text."""

    def __init__(self, root):
        self.root = Path(root).absolute()
        self.listed = []  # relative directories enumerated, in walk order; '.' is the root
        self._parsed = {}

    def path(self, relative):
        return self.root / relative

    def relative(self, path):
        return Path(path).absolute().relative_to(self.root).as_posix()

    def inventory(self, scope):
        """Sorted relative paths of the entries a scope selects, without requiring Git."""
        start = self.root / scope.base if scope.base else self.root
        selected = []
        pending = [(start, scope.base)]
        while pending:
            where, relative = pending.pop()
            try:
                with os.scandir(where) as entries:
                    children = sorted(entries, key=lambda entry: entry.name)
            except OSError:
                continue
            self.listed.append(relative or '.')
            for entry in children:
                name = entry.name
                child = f'{relative}/{name}' if relative else name
                if scope.hidden and name.startswith('.'):
                    continue
                try:
                    is_directory = entry.is_dir(follow_symlinks=False)
                except OSError:
                    is_directory = False  # unreadable metadata: a candidate, never descended
                matches = name.endswith(scope.suffixes) if scope.suffixes else not is_directory
                if matches and not scope.excludes(child):
                    selected.append(child)
                if scope.recursive and is_directory and not scope.excludes(child + '/'):
                    pending.append((entry.path, child))
        return sorted(selected)

    def exists(self, relative):
        return (self.root / relative).exists()

    def read_bytes(self, relative):
        try:
            return (self.root / relative).read_bytes()
        except FileNotFoundError as error:
            raise MissingInput(relative, 'no such file') from error
        except OSError as error:
            raise UnreadableInput(relative, error.strerror or str(error)) from error

    def read_text(self, relative, encoding='utf-8'):
        data = self.read_bytes(relative)
        try:
            return data.decode(encoding)
        except UnicodeDecodeError as error:
            raise UnreadableInput(relative, f'not {encoding}: {error}') from error

    def parsed(self, relative, parser):
        """`parser(text, relative)` over the current text; reused within this Tree by content and name."""
        text = self.read_text(relative)
        key = (parser, relative, text)
        try:
            return self._parsed[key]
        except KeyError:
            value = self._parsed[key] = parser(text, relative)
            return value

    def expand(self, inputs):
        """Sorted existing relative paths the declarations select; a missing required file raises."""
        found = set()
        for declared in inputs:
            if declared.kind == 'file':
                if not self.exists(declared.path):
                    raise MissingInput(declared.path, 'no such file')
                found.add(declared.path)
            elif declared.kind == 'optional':
                if self.exists(declared.path):
                    found.add(declared.path)
            elif declared.kind == 'directory':
                found.update(self.inventory(Scope(declared.path, declared.suffixes, base=declared.path,
                                                  recursive=declared.recursive)))
            elif declared.kind == 'scope':
                found.update(self.inventory(declared.scope))
            else:
                raise ValueError(f'unknown input kind {declared.kind!r}')
        return sorted(found)
