"""Create and describe one local release attempt, without running release tools."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import plistlib
import tempfile
import zipfile

from artifact import digest

STEPS = ('staple', 'staple-validation', 'gatekeeper', 're-zip')


def create(archive=None, *, parent=None):
    archive = Path(archive).resolve() if archive is not None else None
    record = dict(schema_version=1, started_at=datetime.now(timezone.utc).isoformat(),
                  archive=str(archive) if archive else None, submitted_sha256=None, build=None)
    if archive is not None:
        record['submitted_sha256'] = digest(archive)
        with zipfile.ZipFile(archive) as zipped:
            info = plistlib.loads(zipped.read('PolicyWitness.app/Contents/Info.plist'))
        record['build'] = {key: info.get(key) for key in (
            'CFBundleShortVersionString', 'CFBundleVersion', 'PWBuildCommit', 'PWBuildDescribe')}
        parent = archive.parent
    base = Path(parent).resolve() / 'evidence'
    base.mkdir(parents=True, exist_ok=True)
    prefix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')
    out = Path(tempfile.mkdtemp(prefix=prefix, dir=base))
    (out / 'release.json').write_text(json.dumps(record, indent=2) + '\n')
    summarize(out)
    return out


def check_archive(out, archive):
    record = json.loads((Path(out) / 'release.json').read_text())
    if record['archive'] != str(Path(archive).resolve()):
        raise ValueError('release evidence belongs to a different archive')
    return record


def require_release_acceptance(report):
    """New receipt kinds are explicit; historical absent-kind receipts retain their meaning."""
    if not isinstance(report, dict):
        raise ValueError('invalid acceptance receipt')
    schema = report.get('schema_version')
    if schema is not None and (type(schema) is not int or schema not in (1, 2, 3, 4)):
        raise ValueError('unsupported acceptance receipt version')
    kind = report.get('kind')
    if (schema == 4 and kind != 'release_acceptance') or kind not in (None, 'release_acceptance'):
        raise ValueError('receipt is not release acceptance')
    # Historical absence retains its meaning; explicit candidate evidence does
    # not become release evidence by changing its version or deleting its kind.
    publication = report.get('publication')
    publication = publication if isinstance(publication, dict) else {}
    apple = report.get('apple_assessment')
    apple = apple if isinstance(apple, dict) else {}
    source = report.get('source')
    source = source if isinstance(source, dict) else {}
    contracts = (report.get('contract'), publication.get('build_contract'), source.get('build_contract'))
    if (any(isinstance(value, str) and value.startswith('development:') for value in contracts)
            or publication.get('status') == 'withheld'
            or apple.get('status') == 'not_performed' or apple.get('reason') == 'development_candidate'
            or source.get('agreement_scope') == 'build_contract_inputs'):
        raise ValueError('receipt is not release acceptance: explicit development candidate evidence')


def record_acceptance(out, acceptance):
    acceptance = Path(acceptance).resolve()
    report = json.loads(acceptance.read_text())
    require_release_acceptance(report)
    check_archive(out, report['archive'])
    pointer = dict(path=str(acceptance), ok=report['ok'], sha256=report.get('sha256_after'))
    (Path(out) / 'acceptance.json').write_text(json.dumps(pointer, indent=2) + '\n')
    summarize(out)


def summarize(out):
    out = Path(out)
    record = json.loads((out / 'release.json').read_text())
    lines = ['# Release attempt', '', f"Started: {record['started_at']}", '']
    if record['archive']:
        lines += [f"Input archive: `{record['archive']}`",
                  f"Input SHA-256: `{record['submitted_sha256']}`", '']
        build = record['build']
        lines += [f"Version: {build['CFBundleShortVersionString']}; build: {build['CFBundleVersion']}.",
                  f"Embedded source: `{build['PWBuildCommit'] or 'not recorded'}` "
                  f"(`{build['PWBuildDescribe'] or 'not recorded'}`).", '']
    lines += ['| Step | Recorded result | Evidence |', '| --- | --- | --- |']
    notary = out / 'notarization/result.json'
    if notary.is_file():
        value = json.loads(notary.read_text())
        lines.append(f"| Notarization | {value['state']} | [result](notarization/result.json) |")
    receipts = [out / step / 'command.json' for step in STEPS if (out / step / 'command.json').is_file()]
    receipts += sorted(path for path in out.glob('*/command.json') if path.parent.name not in STEPS)
    for path in receipts:
        value = json.loads(path.read_text())
        state = ('timed out' if value['timed_out'] else 'interrupted' if value['interrupted']
                 else 'launch error' if value.get('error') else 'incomplete' if value['returncode'] is None
                 else f"exit {value['returncode']}")
        lines.append(f'| {path.parent.name} | {state} | [receipt]({path.parent.name}/command.json) |')
    acceptance = out / 'acceptance.json'
    if acceptance.is_file():
        value = json.loads(acceptance.read_text())
        lines += [f"| Archive acceptance | {'passed' if value['ok'] else 'failed'} | [location](acceptance.json) |",
                  '', f"Final archive SHA-256: `{value['sha256']}`",
                  f"Acceptance report: `{value['path']}`"]
    lines += ['', 'Missing steps have no recorded result. Notarization acceptance and final archive',
              'acceptance are separate observations; rebuilding the root artifacts does not',
              'transfer these results to the new bytes.', '']
    temporary = out / 'README.md.tmp'
    temporary.write_text('\n'.join(lines))
    temporary.replace(out / 'README.md')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    try:
        print(create(args.archive))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
