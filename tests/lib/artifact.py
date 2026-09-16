"""Read-only bundle inspection and inventories shared by test equipment.

No signing, rebuilding, or manifest repair belongs here. Signature verification
is local codesign verification, not notarization or release acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import stat
import subprocess

CODESIGN = '/usr/bin/codesign'
CONTROLLER = 'Contents/MacOS/policy-witness'
SERVICE = 'Contents/XPCServices/PWRunner.xpc'
EXECUTABLES = [CONTROLLER, *('Contents/MacOS/' + name for name in
    ('pw-runner-client', 'sandbox-log-observer', 'sbpl-check', 'sb_api_validator')),
    *(SERVICE + '/Contents/MacOS/' + name for name in
      ('PWRunner', 'pw-probe-runner', 'sb_api_validator'))]
MANIFEST = 'Contents/Resources/Evidence/manifest.json'
SYMBOLS = 'Contents/Resources/Evidence/symbols.json'


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def inventory(app):
    """Include directories/modes and links without following directory symlinks.

    scandir errors propagate: an unreadable subtree must not look like an empty
    one. Timestamps are excluded so read-only inspection does not cause drift.
    """
    result = {}

    def visit(path):
        mode = path.lstat().st_mode
        entry = {'mode': mode}
        result[str(path.relative_to(app))] = entry
        if stat.S_ISLNK(mode):
            entry['symlink'] = os.readlink(path)
        elif stat.S_ISREG(mode):
            entry['sha256'] = digest(path)
        elif stat.S_ISDIR(mode):
            with os.scandir(path) as children:
                for child in sorted(children, key=lambda c: c.name):
                    visit(Path(child.path))
        else:
            raise ValueError(f'unsupported bundle file type: {path}')

    visit(app)
    return result


def changes(before, after):
    return {name: {'before': before.get(name), 'after': after.get(name)}
            for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)}


def inspect(app):
    app = Path(app).resolve()
    report = {'schema_version': 1, 'app': str(app), 'ok': False, 'errors': [],
              'signatures': [], 'manifest_entries': []}

    def error(code, path, message, **details):
        report['errors'].append(dict(code=code, path=str(path), message=message, **details))

    def contained(relative):
        path = app / relative
        if not path.resolve().is_relative_to(app):
            raise ValueError(f'path leaves selected app: {relative}')
        return path

    for relative in [*EXECUTABLES, MANIFEST, SYMBOLS, 'Contents/Info.plist', SERVICE + '/Contents/Info.plist']:
        try:
            path = contained(relative)
            if not path.is_file():
                raise ValueError('required file missing')
            if relative in EXECUTABLES and not os.access(path, os.X_OK):
                raise ValueError('required executable is not executable')
        except (OSError, ValueError) as exc:
            error('required_component', relative, str(exc))

    for relative, executable in (('Contents/Info.plist', 'policy-witness'),
                                  (SERVICE + '/Contents/Info.plist', 'PWRunner')):
        try:
            info = plistlib.loads(contained(relative).read_bytes())
            if not isinstance(info, dict) or info.get('CFBundleExecutable') != executable:
                raise ValueError(f'expected CFBundleExecutable={executable}')
            if not isinstance(info.get('CFBundleIdentifier'), str) or not info['CFBundleIdentifier']:
                raise ValueError('missing CFBundleIdentifier')
        except (OSError, ValueError, plistlib.InvalidFileException) as exc:
            error('bundle_metadata', relative, str(exc))

    # Explicit helpers plus both seals: --deep alone can miss an unsealed extra
    # tool. Never use --deep for signing.
    for relative in ['.', SERVICE, *EXECUTABLES[1:]]:
        argv = [CODESIGN, '--verify', '--strict', '--deep', str(app / relative)]
        receipt = {'path': relative, 'argv': argv, 'returncode': None}
        try:
            contained(relative)
            result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
            receipt.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
            if result.returncode != 0:
                error('signature', relative, result.stderr.strip() or result.stdout.strip() or 'codesign verification failed')
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            error('signature', relative, str(exc))
            receipt['error'] = str(exc)
        report['signatures'].append(receipt)

    try:
        manifest = json.loads(contained(MANIFEST).read_bytes())
        if not isinstance(manifest, dict) or manifest.get('schema_version') != 1:
            raise ValueError('expected manifest schema_version=1')
        if manifest.get('app_binary_rel_path') != CONTROLLER:
            raise ValueError('manifest identifies a different controller')
        app_info = plistlib.loads(contained('Contents/Info.plist').read_bytes())
        if manifest.get('app_bundle_id') != app_info.get('CFBundleIdentifier'):
            raise ValueError('manifest app identity disagrees with Info.plist')
        entries = manifest.get('entries')
        if not isinstance(entries, list):
            raise ValueError('expected manifest entries array')
        seen = set()
        for entry in entries:
            relative = entry.get('rel_path') if isinstance(entry, dict) else None
            try:
                if (not isinstance(relative, str) or not relative or
                        PurePosixPath(relative).is_absolute() or '..' in PurePosixPath(relative).parts or
                        str(PurePosixPath(relative)) != relative or relative in seen):
                    raise ValueError('invalid or duplicate manifest path')
                seen.add(relative)
                expected = entry.get('sha256')
                actual = digest(contained(relative))
                record = dict(path=relative, expected=expected, actual=actual)
                report['manifest_entries'].append(record)
                if expected != actual:
                    error('manifest_hash', relative, 'manifest hash differs from bundle bytes', expected=expected, actual=actual)
            except (OSError, ValueError) as exc:
                error('manifest_entry', relative, str(exc))
        required = set(EXECUTABLES[1:]) | {SYMBOLS}
        # Every shipped augment must be inventoried too; the fixed executable
        # list above remains mandatory even if the manifest omits a helper.
        required.update(str(p.relative_to(app)) for p in (app / 'Contents/Resources/Augments').glob('*.sb'))
        for relative in sorted(required - seen):
            error('manifest_missing', relative, 'required component absent from manifest')
    except (OSError, ValueError, AttributeError, plistlib.InvalidFileException) as exc:
        error('manifest', MANIFEST, str(exc))
    report['ok'] = not report['errors']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    result = inspect(args.app)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    for issue in result['errors']:
        print(f"{issue['code']}: {issue['path']}: {issue['message']}")
    raise SystemExit(0 if result['ok'] else 1)
