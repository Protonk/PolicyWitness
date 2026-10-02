"""Independent fake codesign for offline dispatch controls: a file-change model.

Only isolated copies of artifact.py point to this executable. Production has no
environment override or switch to bypass signing checks. Seals live outside the
app; they are a file-change model, not a claim about Apple's signing behavior.
`repository.install_runner` copies this file verbatim, with a shebang, into the
fixture repository, so it imports nothing but the standard library and knows no
bundle layout: `seal` is told which paths to seal.
"""
import hashlib
import json
from pathlib import Path
import sys


def fingerprint(path):
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


def seal(app, targets):
    seals = {str(p): fingerprint(p) for p in targets}
    app.with_suffix('.fixture-seals.json').write_text(json.dumps(seals))


def main():
    target = Path(sys.argv[-1]).resolve()
    app = next(p for p in (target, *target.parents) if p.suffix == '.app')
    receipt = app.with_suffix('.fixture-verification.jsonl')
    with receipt.open('a') as stream:
        stream.write(json.dumps(sys.argv[1:]) + '\n')
    try:
        seals = json.loads(app.with_suffix('.fixture-seals.json').read_text())
        valid = target.exists() and seals[str(target)] == fingerprint(target)
    except (OSError, KeyError):
        valid = False
    if not valid:
        print('fixture signature invalid', file=sys.stderr)
    return 0 if valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
