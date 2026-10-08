#!/usr/bin/env python3
"""Generate the exact host/worker identity from their protocol sources.

This is a conservative source identity, not a compatibility classification or
proof of correctness. Generated regions are excluded to avoid self-reference.
The build regenerates it before compiling either side; --check is read-only.

Generator invariants: this generator holds G1, G2, G3 and G6, as stated under Generator
contracts in tests/suites/source_drift/README.md.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)"
END = "END GENERATED WORKER IDENTITY"
SOURCE_DIRS = ("controller/tools/pw_probe_runner", "runner/Sources")
SOURCE_FILES = ("docs/generate_worker_identity.py", "build.sh", "meson.build", "meson.options",
                "runner/Package.swift")
TARGETS = ("controller/tools/pw_probe_runner/pw_probe_runner_abi.h",
           "runner/Sources/PWRunnerCore/CWorker.swift", "tests/lib/contract.py")


def bounds(text):
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if BEGIN in line]
    ends = [i for i, line in enumerate(lines) if END in line]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise ValueError("expected exactly one ordered generated worker identity region")
    return lines, starts[0], ends[0]


def source_paths(root):
    """Every digest input. The walk covers ordinary files beneath the two
    directories and refuses a symlink there, because the compiler would follow
    it to bytes this digest never sees; the build separately checks that the
    compiler consumed nothing in the repository beyond these paths."""
    paths = set(SOURCE_FILES)
    for directory in SOURCE_DIRS:
        found = set()
        for p in (root / directory).rglob("*"):
            if p.is_symlink():
                raise ValueError(f"symlink under identity sources: {p.relative_to(root).as_posix()}; "
                                 "the digest covers ordinary files beneath its directories")
            if p.suffix in (".c", ".h", ".swift") and p.is_file():
                found.add(p.relative_to(root).as_posix())
        if not found:
            raise ValueError(f"missing protocol sources: {directory}")
        paths.update(found)
    return sorted(paths)


def identity(root):
    digest = hashlib.sha256(b"PolicyWitness host/worker source identity\0")
    for name in source_paths(root):
        data = (root / name).read_bytes()
        if name in TARGETS:
            lines, start, end = bounds(data.decode("utf-8"))
            data = "".join(lines[:start + 1] + lines[end:]).encode("utf-8")
        # Length framing makes both names and contents unambiguous.
        for part in (name.encode("utf-8"), data):
            digest.update(len(part).to_bytes(8, "big"))
            digest.update(part)
    return digest.hexdigest()


def render_all(root):
    value = identity(root)
    octets = ", ".join(f"0x{value[i:i + 2]}" for i in range(0, len(value), 2))
    bodies = (
        f'#define PW_WORKER_ABI_IDENTITY_HEX "{value}"\n'
        f"static const uint8_t PW_WORKER_ABI_IDENTITY[32] = {{{octets}}};\n",
        f'    static let abiIdentityHex = "{value}"\n'
        f"    static let abiIdentity: [UInt8] = [{octets}]\n",
        f'WORKER_IDENTITY = "{value}"\n',
    )
    results = []
    for name, body in zip(TARGETS, bodies):
        before = (root / name).read_text()
        lines, start, end = bounds(before)
        after = "".join(lines[:start + 1]) + body + "".join(lines[end:])
        results.append((name, before, after))
    return value, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        value, results = render_all(ROOT)
        stale = [name for name, before, after in results if before != after]
        if args.check and stale:
            raise ValueError(f"stale {', '.join(stale)}; run python3 docs/generate_worker_identity.py")
        if not args.check:
            for name, before, after in results:
                if before != after:
                    (ROOT / name).write_text(after)
        print(f"ok: worker identity {value}; " +
              ("all generated copies current" if args.check else f"{len(stale)} file(s) regenerated"))
        return 0
    except (ValueError, OSError, UnicodeError) as error:
        print(f"worker identity: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
