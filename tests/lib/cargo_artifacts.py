#!/usr/bin/env python3
"""The executables Cargo reports it produced, one `name<TAB>path` line per requested binary.

build.sh runs Cargo with `--message-format=json-render-diagnostics` into a
messages file and asks this helper which path each requested executable was
written to, so a target triple or a Cargo setting that sent an output under
another directory is refused before any copy, instead of a stale file at the
pinned path being copied in its place. Only `compiler-artifact` messages for
the named binaries are read; nothing else in the file is interpreted.

    cargo_artifacts.py MESSAGES.jsonl NAME [NAME...]

Exit 1 naming a requested binary Cargo reported no executable for; exit 2
when the messages file cannot be read or parsed.
"""
import json
import sys
from pathlib import Path


def executables(messages, names):
    """Map each requested binary name to the executable path of its last compiler-artifact message."""
    found = {}
    for line in messages.splitlines():
        if not line.strip():
            continue
        message = json.loads(line)
        if message.get("reason") != "compiler-artifact":
            continue
        name = message.get("target", {}).get("name")
        if name in names and message.get("executable"):
            found[name] = message["executable"]
    return found


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    path, names = Path(sys.argv[1]), sys.argv[2:]
    try:
        found = executables(path.read_text(), names)
    except (OSError, ValueError) as exc:
        print(f"cargo artifacts: {exc}", file=sys.stderr)
        return 2
    missing = [name for name in names if name not in found]
    if missing:
        print(f"cargo artifacts: Cargo reported no executable for {', '.join(missing)}", file=sys.stderr)
        return 1
    for name in names:
        print(f"{name}\t{found[name]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
