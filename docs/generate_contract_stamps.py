#!/usr/bin/env python3
"""Derive public surface stamps from annotated release trees and authored definitions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

# Discovery also loads this module by filename from outside the source tree.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_porcelain import wire_identity

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'docs/contract_surfaces.json'
OUTPUTS = ('docs/CONTRACT.md', 'docs/PolicyWitness.md')
BEGIN = '<!-- BEGIN GENERATED CONTRACT STAMPS -->'
END = '<!-- END GENERATED CONTRACT STAMPS -->'
RELEASE = re.compile(r'v[0-9]+\.[0-9]+\.[0-9]+')


def git(root, *args, required=True):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    if result.returncode:
        if required:
            raise ValueError(f'git {args[0]}: {result.stderr.strip()}')
        return None
    return result.stdout


def read(root, name, tag=None):
    if tag:
        value = git(root, 'show', f'{tag}:{name}', required=False)
        if value is None:
            raise ValueError(f'{tag}: missing surface input {name}')
        return value
    return (root / name).read_text()


def manifest(root, tag=None):
    value = json.loads(read(root, MANIFEST, tag))
    if set(value) != {'surfaces'} or not isinstance(value['surfaces'], list):
        raise ValueError('invalid contract surfaces manifest')
    seen = set()
    suites = json.loads(read(root, 'tests/catalog.json', tag))['suites']
    for row in value['surfaces']:
        if set(row) - {'definitions'} != {'id', 'artifact', 'goldens', 'definition', 'checks'}:
            raise ValueError('invalid surface fields')
        if not re.fullmatch('[a-z][a-z0-9_]*', row['id']) or row['id'] in seen:
            raise ValueError('duplicate or invalid surface id')
        seen.add(row['id'])
        if not row['goldens'] or not row['checks']:
            raise ValueError(f'{row["id"]}: missing golden or verification')
        if any(check not in suites for check in row['checks']):
            raise ValueError(f'{row["id"]}: unknown verification suite')
        for name in [row['definition'], *row['goldens'], *(item.split('#')[0] for item in row.get('definitions', []))]:
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('surface input must be repository-relative')
    return value['surfaces']


def collected_shapes(root):
    """Reviewable views of the response golden and closed request keys."""
    shape = json.loads((root / 'tests/fixtures/contract/response_shape.json').read_text())['shape']
    def owner(path):
        if path.startswith('reply.producer'): return 'envelope'
        if path.startswith('reply.steps'): return 'steps'
        if 'compiled_profile' in path: return 'profile'
        if any(word in path for word in ('subprocess', 'disposition', 'termination_request', 'wait_errors')):
            return 'lifecycle'
        if any(word in path for word in ('equipment', 'resources', 'authority_setup', 'bindings', 'transfers', 'extension_events')):
            return 'equipment'
        if path.startswith('reply.actors'): return 'equipment'
        if any(word in path for word in ('request_failure', 'admission_failure', 'reporting_failure')):
            return 'refusals'
        if any(word in path for word in ('phases', 'schedule', 'sandboxed_after_apply', 'partial_steps', 'clock')):
            return 'lifecycle'
        return 'envelope'
    values = {name: {} for name in ('steps', 'profile', 'equipment', 'refusals', 'lifecycle',
              'request', 'policy', 'probes', 'actors', 'envelope', 'dossier', 'transport', 'installation')}
    for path, fields in shape.items():
        for key, kind in fields.items():
            values[owner(path + '.' + key)].setdefault('shape', {}).setdefault(path, {})[key] = kind
    key_owners = {
        'PWRunnerRunSpec': 'request', 'PWRunnerTestOverrides': 'request',
        'PWRunnerPolicySpec': 'policy', 'PWRunnerSandboxCheck': 'probes',
        'PWRunnerSandboxFilter': 'probes', 'PWRunnerAttempt': 'probes', 'PWRunnerProbeStep': 'probes',
        'PWRunnerPhase': 'actors', 'PWRunnerActorSandbox': 'actors', 'PWRunnerActor': 'actors',
        'PWRunnerAfterTermination': 'actors', 'PWRunnerExtensionOperation': 'actors',
        'PWRunnerExtensionAction': 'actors',
        'PWRunnerReservationRequest': 'transport', 'PWRunnerControlReply': 'transport',
        'ActorEquipmentManifest.Worker': 'installation', 'ActorEquipmentManifest': 'installation',
    }
    for path in sorted((root / 'runner/Sources/PWRunnerCore').glob('*.swift')):
        for index, match in enumerate(re.finditer(r'enum CodingKeys: String, CodingKey, CaseIterable \{(.*?)\}', path.read_text(), re.S)):
            cases = re.findall(r'\bcase\s+([^;\n}]+)', match.group(1))
            names = []
            for case in cases:
                for value in case.split(','):
                    field = re.fullmatch(r'\s*(\w+)(?:\s*=\s*("(?:[^"\\]|\\.)*"))?\s*', value)
                    if field is None:
                        raise ValueError(f'{path.name}: cannot collect CodingKeys field {value!r}')
                    names.append(json.loads(field[2]) if field[2] else field[1])
            declarations = re.findall(r'^(?:private |public |internal )?(?:struct|enum) (\w+)', path.read_text()[:match.start()], re.M)
            declaration = declarations[-1]
            if path.name == 'ActorEquipment.swift':
                declaration = ('ActorEquipmentManifest.Worker', 'ActorEquipmentManifest')[index]
            if declaration not in key_owners:
                raise ValueError(f'unassigned closed object: {declaration}')
            surface = key_owners[declaration]
            values[surface].setdefault('closed_keys', {})[declaration] = sorted(names)
    selector = (root / 'controller/src/runner_select.rs').read_text()
    values['request']['controller_keys'] = {}
    for key in ('SELECTOR_FIELDS', 'RUNNER_SELECTOR_FIELDS'):
        match = re.search(r'const ' + key + r':.*?= &\[(.*?)\];', selector, re.S)
        if match is None: raise ValueError(f'missing selector declaration {key}')
        values['request']['controller_keys'][key] = sorted(re.findall(r'"([^"\\]*)"', match[1]))
    # The registry and command records use serde directly. Pin field types and
    # serialization attributes, including flatten/default/alias behavior.
    records = {}
    for name in ('runner_manager.rs', 'runner_commands.rs', 'runner_select.rs'):
        text = (root / 'controller/src' / name).read_text()
        for match in re.finditer(r'#\[derive\(([^)]*)\)\]\s*(?:#\[[^\n]*\]\s*)*(?:pub )?struct (\w+)\s*\{([^}]+)\}', text):
            if 'Serialize' not in match[1]: continue
            body = re.sub(r'//[^\n]*', '', match[3])
            records[match[2]] = ' '.join(body.split())
    values['installation']['serde_records'] = records
    wire = json.loads((root / 'docs/porcelain.json').read_text())
    # Include the complete decoder identity: host records also carry field tags,
    # integer widths and presentation rules that a JSON shape cannot witness.
    values['transport']['wire_schema'] = wire_identity(wire)
    limits = {row['id']: row for row in json.loads((root / 'docs/limits.json').read_text())['limits']}
    reservation_limits = {
        name: {key: limits[name][key] for key in ('value', 'unit', 'counting', 'effect', 'control')}
        for name in ('client_rpc_wait', 'reservation_lease', 'reservation_rpc_wait',
                     'reservation_attempts', 'reservation_retry_delay')
    }
    values['transport']['reservation_limits'] = reservation_limits
    values['installation']['reservation_limits'] = reservation_limits
    values['installation']['reservation_keys'] = values['transport']['closed_keys']
    envelope = json.loads((root / 'tests/fixtures/contract/envelope_shape.json').read_text())['shape']
    def envelope_owner(path):
        if path.startswith('envelope.data.specimen'): return 'dossier'
        if path.startswith('envelope.data.runner_client'): return 'transport'
        if path.startswith('envelope.data.request_failure'): return 'refusals'
        return 'envelope'
    for path, fields in envelope.items():
        for key, kind in fields.items():
            surface = envelope_owner(path + '.' + key)
            values[surface].setdefault('shape', {}).setdefault(path, {})[key] = kind
    return {f'tests/fixtures/contract/surfaces/{name}.json': json.dumps(value, indent=2, sort_keys=True) + '\n'
            for name, value in values.items()}


def check_shapes(root, refresh=False):
    values = collected_shapes(root)
    stale = [name for name, body in values.items() if not (root / name).exists() or (root / name).read_text() != body]
    if stale and not refresh:
        raise ValueError('stale surface shape goldens: ' + ', '.join(stale) +
                         '; run tests/lib/python.sh docs/generate_contract_stamps.py --refresh-shapes and review the diff')
    if refresh:
        for name in stale:
            (root / name).write_text(values[name])


def input_paths(root):
    rows = manifest(root)
    return sorted({MANIFEST, 'docs/generate_contract_stamps.py', 'docs/generate_porcelain.py', 'docs/limits.json', 'tests/catalog.json', 'tests/fixtures/contract/response_shape.json', 'tests/fixtures/contract/envelope_shape.json', *OUTPUTS, 'docs/porcelain.json', 'controller/src/runner_select.rs', 'controller/src/runner_manager.rs', 'controller/src/runner_commands.rs',
                   *(p.relative_to(root).as_posix() for p in (root / 'runner/Sources/PWRunnerCore').glob('*.swift')),
                   *(name for row in rows for name in [row['definition'], *row['goldens'], *(item.split('#')[0] for item in row.get('definitions', []))])})


def surface_hash(root, row, tag=None):
    text = read(root, row['definition'], tag)
    begin, end = f'<!-- BEGIN CONTRACT {row["id"]} -->', f'<!-- END CONTRACT {row["id"]} -->'
    if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) >= text.index(end):
        raise ValueError(f'{row["id"]}: expected one ordered definition region')
    definition = ' '.join(text.split(begin)[1].split(end)[0].split())
    for item in row.get('definitions', []):
        name, region = item.split('#')
        prose = read(root, name, tag)
        start, stop = f'<!-- BEGIN CONTRACT {region} -->', f'<!-- END CONTRACT {region} -->'
        if prose.count(start) != 1 or prose.count(stop) != 1 or prose.index(start) >= prose.index(stop):
            raise ValueError(f'{item}: expected one ordered definition region')
        definition += ' ' + ' '.join(prose.split(start)[1].split(stop)[0].split())
    values = [json.loads(read(root, name, tag)) for name in row['goldens']]
    data = json.dumps([definition, values], sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(data.encode()).hexdigest()


def release_tags(root):
    # Only annotated releases on this tree's ancestry belong to its contract history.
    top = git(root, 'rev-parse', '--show-toplevel', required=False)
    if not top or Path(top.strip()).resolve() != root.resolve():
        return []
    tags = git(root, 'for-each-ref', '--format=%(refname:short) %(objecttype) %(*objectname)', 'refs/tags', required=False) or ''
    by_commit = {}
    for line in tags.splitlines():
        parts = line.split()
        if len(parts) == 3 and RELEASE.fullmatch(parts[0]) and parts[1] == 'tag':
            by_commit.setdefault(parts[2], []).append(parts[0])
    commits = (git(root, 'rev-list', '--reverse', '--topo-order', 'HEAD', required=False) or '').splitlines()
    return [tag for commit in commits for tag in sorted(by_commit.get(commit, []))]


def stamps(root, release=None):
    if release is not None and not RELEASE.fullmatch(release):
        raise ValueError('--release requires v<major>.<minor>.<patch>')
    state = {}
    for tag in release_tags(root):
        if git(root, 'cat-file', '-e', f'{tag}:{MANIFEST}', required=False) is None:
            continue
        rows = {row['id']: row for row in manifest(root, tag)}
        for ident in state.keys() - rows.keys():
            if not state[ident]['removed']:
                state[ident].update(stamp=tag, removed=True, hash=None)
        for ident, row in rows.items():
            digest = surface_hash(root, row, tag)
            prior = state.get(ident)
            stamp = tag if prior is None or prior['hash'] != digest else prior['stamp']
            state[ident] = dict(row=row, hash=digest, stamp=stamp, removed=False)
    rows = {row['id']: row for row in manifest(root)}
    for ident in state.keys() - rows.keys():
        if not state[ident]['removed']:
            state[ident].update(stamp=release or 'unreleased', removed=True, hash=None)
    for ident, row in rows.items():
        digest = surface_hash(root, row)
        prior = state.get(ident)
        stamp = release or 'unreleased' if prior is None or prior['hash'] != digest else prior['stamp']
        state[ident] = dict(row=row, hash=digest, stamp=stamp, removed=False)
    return state


def render(root, release=None):
    if release is None and not release_tags(root) and any(
            re.search(r'\| v[0-9]+\.[0-9]+\.[0-9]+ \|', read(root, name)) for name in OUTPUTS):
        raise ValueError('release history unavailable; restore annotated release tags before regenerating stamps')
    state = stamps(root, release)
    lines = ['| Surface | User artifact | Last changed |', '| --- | --- | --- |']
    for ident, value in sorted(state.items()):
        suffix = ' (removed)' if value['removed'] else ''
        lines.append(f'| `{ident}`{suffix} | {value["row"]["artifact"]} | {value["stamp"]} |')
    body = '\n' + '\n'.join(lines) + '\n'
    results = []
    for name in OUTPUTS:
        before = read(root, name)
        if before.count(BEGIN) != 1 or before.count(END) != 1 or before.index(BEGIN) >= before.index(END):
            raise ValueError(f'{name}: expected one ordered stamp table region')
        left, rest = before.split(BEGIN)
        _, right = rest.split(END)
        results.append((name, before, left + BEGIN + body + END + right))
    return results


def check(root, require_history=False):
    """Validate current inputs everywhere; history is needed to derive last change."""
    check_shapes(root)
    for row in manifest(root):
        surface_hash(root, row)
    if not release_tags(root):
        if require_history:
            raise ValueError('release history unavailable; fetch annotated release tags for full verification')
        tables = []
        for name in OUTPUTS:
            text = read(root, name)
            if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(BEGIN) >= text.index(END):
                raise ValueError(f'{name}: expected one ordered stamp table region')
            tables.append(text.split(BEGIN)[1].split(END)[0])
        if len(set(tables)) != 1:
            raise ValueError('stale contract stamps: docs/CONTRACT.md, docs/PolicyWitness.md; tables disagree')
        return False
    stale = [name for name, before, after in render(root) if before != after]
    if stale:
        raise ValueError('stale contract stamps: ' + ', '.join(stale) + '; run tests/lib/python.sh docs/generate_contract_stamps.py')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--release')
    parser.add_argument('--require-history', action='store_true', help='refuse incomplete stamp verification')
    parser.add_argument('--refresh-shapes', action='store_true', help='recollect surface shape goldens for review')
    args = parser.parse_args()
    try:
        if args.check and args.refresh_shapes:
            raise ValueError('--check cannot refresh goldens')
        if args.check:
            complete = check(ROOT, args.require_history)
            print('ok: contract surface stamps current' if complete else
                  'ok: contract inputs current; stamp derivation not checked (release history unavailable)')
            return
        if args.require_history and not release_tags(ROOT):
            raise ValueError('release history unavailable; fetch annotated release tags')
        check_shapes(ROOT, args.refresh_shapes)
        results = render(ROOT, args.release)
        stale = [name for name, before, after in results if before != after]
        if args.check and stale:
            raise ValueError('stale contract stamps: ' + ', '.join(stale) + '; run tests/lib/python.sh docs/generate_contract_stamps.py')
        if not args.check:
            for name, before, after in results:
                if before != after:
                    (ROOT / name).write_text(after)
        print('ok: contract surface stamps current')
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'contract stamps: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
