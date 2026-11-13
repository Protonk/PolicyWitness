"""Assembly and release history for the contract generator entry point.

The authored tree is the current public source. Released v1 snapshots retain
its canonical public view independently of subsequent authoring syntax.
"""
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
for directory in (HERE, HERE.parent):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
import history_v0
import history_v1
import tree as model
from generate_porcelain import wire_identity

OUTPUTS = ('docs/CONTRACT.md', 'docs/PolicyWitness.md')
BEGIN = '<!-- BEGIN GENERATED CONTRACT STAMPS -->'
END = '<!-- END GENERATED CONTRACT STAMPS -->'
DOCUMENT_BEGIN = '<!-- BEGIN GENERATED PUBLIC CONTRACT -->'
DOCUMENT_END = '<!-- END GENERATED PUBLIC CONTRACT -->'
BASELINE = 'docs/contract/free_text.json'
RELEASE = history_v1.RELEASE


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + '\n'


def git(root, *args, required=True):
    result = subprocess.run(['git', '-C', str(root), *args],
                            capture_output=True, text=True)
    if result.returncode:
        if required:
            raise ValueError(f'git {args[0]}: {result.stderr.strip()}')
        return None
    return result.stdout


def read(root, name, tag=None):
    if tag:
        value = git(root, 'show', f'{tag}:{name}', required=False)
        if value is None:
            raise ValueError(f'{tag}: missing contract history input {name}')
        return value
    return (root / name).read_text()


def release_tags(root):
    top = git(root, 'rev-parse', '--show-toplevel', required=False)
    if not top or Path(top.strip()).resolve() != root.resolve():
        return []
    tags = git(root, 'for-each-ref', '--format=%(refname:short) %(objecttype) %(*objectname)',
               'refs/tags', required=False) or ''
    by_commit = {}
    for line in tags.splitlines():
        parts = line.split()
        if len(parts) == 3 and RELEASE.fullmatch(parts[0]) and parts[1] == 'tag':
            by_commit.setdefault(parts[2], []).append(parts[0])
    commits = (git(root, 'rev-list', '--reverse', '--topo-order', 'HEAD', required=False) or '').splitlines()
    return [tag for commit in commits for tag in sorted(by_commit.get(commit, []))]


def table(text, name):
    if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(BEGIN) >= text.index(END):
        raise ValueError(f'{name}: expected one ordered stamp table region')
    return text.split(BEGIN)[1].split(END)[0]


def _replace_table(text, name, body):
    table(text, name)
    left, rest = text.split(BEGIN)
    _, right = rest.split(END)
    return left + BEGIN + body + END + right


def history(root, tags=None):
    """Read each released representation with its own retained reader."""
    tags = release_tags(root) if tags is None else tags
    result = []
    for tag in tags:
        selected_read = lambda name, selected=tag: read(root, name, selected)
        if git(root, 'cat-file', '-e', f'{tag}:{history_v1.SNAPSHOT}', required=False) is not None:
            snapshot = history_v1.snapshot(selected_read)
            missing = set(snapshot['history']) - set(tags)
            if missing:
                raise ValueError(f'{tag}: release history unavailable: ' + ', '.join(sorted(missing)))
            rows = snapshot['surfaces']
            reader = history_v1
        elif git(root, 'cat-file', '-e', f'{tag}:{history_v0.MANIFEST}', required=False) is not None:
            rows = history_v0.surfaces(selected_read)
            reader = history_v0
        else:
            # Releases before public surface history carry neither generator
            # nor a public snapshot. A release that had the mechanism must
            # remain readable; deleting its representation is a refusal.
            had_generator = git(root, 'cat-file', '-e',
                                f'{tag}:docs/generate_contract_stamps.py', required=False) is not None
            if had_generator:
                raise ValueError(f'{tag}: missing or unsupported contract history layout')
            continue
        result.append((tag, [(row, reader.surface_hash(selected_read, row)) for row in rows]))
    return result


def _claimed_history(root):
    claimed = set()
    for name in OUTPUTS:
        path = root / name
        if path.exists():
            claimed.update(re.findall(r'\| (v[0-9]+\.[0-9]+\.[0-9]+) \|', table(path.read_text(), name)))
    if (root / history_v1.SNAPSHOT).exists():
        claimed.update(history_v1.snapshot(lambda name: read(root, name))['history'])
    return claimed


def require_available_history(root, tags, release=None):
    missing = _claimed_history(root) - set(tags)
    if release:
        missing.discard(release)
    if missing:
        raise ValueError('release history unavailable; restore annotated release tags: ' + ', '.join(sorted(missing)))


def current_rows(tree):
    return [dict(id=surface.id, artifact=surface.facts['artifact'],
                 goldens=surface.facts['goldens'], public=model.public_payload(tree, surface.id))
            for surface in tree.surfaces]


def collected_shapes(root, tree=None):
    """Collect public field declarations under their authored surface owners."""
    tree = tree or model.load_tree(root)
    values = {surface.id: {'records': {}} for surface in tree.surfaces}
    for node in tree.nodes:
        if node.kind != 'subject' or not node.record:
            continue
        record = tree.records[node.record]
        # Wire tags belong to the wire surface. Native storage names,
        # mutability and initializer syntax are not public JSON shape.
        fields = {name: {k: v for k, v in definition.items()
                         if k in {'name', 'swift_type', 'optional', 'json_null',
                                  'projection', 'omission', 'conditional_presence',
                                  'shape_only', 'required_key'}}
                  for name, definition in record['fields'].items()}
        public = {k: record[k] for k in ('input', 'open', 'additional_type', 'variants') if k in record}
        public['fields'] = fields
        values[node.surface_id]['records'][node.record] = public
    if 'wire' in values:
        values['wire']['wire_schema'] = wire_identity(json.loads(read(root, 'docs/porcelain.json')))
    limits = {row['id']: row for row in json.loads(read(root, 'docs/limits.json'))['limits']}
    reservation = {name: {key: limits[name][key] for key in ('value', 'unit', 'counting', 'effect', 'control')}
                   for name in ('client_rpc_wait', 'reservation_lease', 'reservation_rpc_wait',
                                'reservation_attempts', 'reservation_retry_delay')}
    for surface in ('transport', 'installation'):
        if surface in values:
            values[surface]['reservation_limits'] = reservation
    if 'request' in values:
        values['request']['controller_keys'] = model.controller_keys(lambda name: read(root, name))
    return {f'tests/fixtures/contract/surfaces/{ident}.json': canonical(value)
            for ident, value in values.items()}


def check_shapes(root, refresh=False, tree=None):
    values = collected_shapes(root, tree)
    stale = [name for name, body in values.items()
             if not (root / name).exists() or read(root, name) != body]
    if stale and not refresh:
        raise ValueError('stale surface shape goldens: ' + ', '.join(stale) +
                         '; run tests/lib/python.sh docs/generate_contract_stamps.py --refresh-shapes and review the diff')
    return values


def check_ratchet(root, tree, prior=None):
    name = BASELINE
    if prior is None:
        if not (root / name).exists():
            raise ValueError('missing free-text baseline; record the stage-one baseline after reviewing the complete tree')
        prior = json.loads(read(root, name))
    if not isinstance(prior, dict) or set(prior) != set(model.FREE_KINDS):
        raise ValueError('invalid free-text baseline')
    if any(type(value) is not int or value < 0 for value in prior.values()):
        raise ValueError('free-text baseline counts must be nonnegative integers')
    growth = {kind: (prior[kind], tree.free_counts[kind]) for kind in prior
              if tree.free_counts[kind] > prior[kind]}
    if growth:
        raise ValueError('free-text count grew: ' + canonical(growth).strip())


def stamps(root, release=None, tree=None, shapes=None):
    if release is not None and not RELEASE.fullmatch(release):
        raise ValueError('--release requires v<major>.<minor>.<patch>')
    tree = tree or model.load_tree(root)
    tags = release_tags(root)
    require_available_history(root, tags, release)
    released = history(root, tags)
    state = {}

    def apply(rows, stamp):
        ids = {row['id'] for row, _ in rows}
        for ident in state.keys() - ids:
            if not state[ident]['removed']:
                state[ident].update(stamp=stamp, removed=True, hash=None)
        for row, digest in rows:
            prior = state.get(row['id'])
            changed = prior is None or prior['hash'] != digest
            state[row['id']] = dict(row=row, hash=digest,
                                    stamp=stamp if changed else prior['stamp'], removed=False)

    for tag, rows in released:
        apply(rows, tag)
    shapes = shapes or {}
    current_read = lambda name: shapes[name] if name in shapes else read(root, name)
    rows = current_rows(tree)
    apply([(row, history_v1.surface_hash(current_read, row)) for row in rows], release or 'unreleased')
    return state


def stamp_table(state):
    lines = ['| Surface | User artifact | Last changed |', '| --- | --- | --- |']
    for ident, value in sorted(state.items()):
        suffix = ' (removed)' if value['removed'] else ''
        lines.append(f'| `{ident}`{suffix} | {value["row"]["artifact"]} | {value["stamp"]} |')
    return '\n' + '\n'.join(lines) + '\n'


def assemble(tree, body):
    rendered = model.render(tree).rstrip()
    # Stamp identity follows the authored identity opening; the renderer owns
    # all public prose and derived views, and the orchestrator owns this table.
    marker = '<!-- CONTRACT SURFACE TABLE -->'
    stamp = BEGIN + body + END
    if marker in rendered:
        if rendered.count(marker) != 1:
            raise ValueError('duplicate surface table position')
        rendered = rendered.replace(marker, stamp)
    else:
        rendered += '\n\n## Surface history\n\n' + stamp
    return DOCUMENT_BEGIN + '\n' + rendered + '\n' + DOCUMENT_END + '\n'


def render(root, release=None, refresh_shapes=False, tree=None):
    tree = tree or model.load_tree(root)
    tags = release_tags(root)
    require_available_history(root, tags, release)
    check_ratchet(root, tree)
    shapes = check_shapes(root, refresh_shapes, tree)
    state = stamps(root, release, tree, shapes)
    body = stamp_table(state)
    selected = [tag for tag, _ in history(root, tags)]
    if release and release not in selected:
        selected.append(release)
    snapshot = dict(format=history_v1.FORMAT, history=selected, surfaces=current_rows(tree))
    values = {OUTPUTS[0]: assemble(tree, body),
              OUTPUTS[1]: _replace_table(read(root, OUTPUTS[1]), OUTPUTS[1], body),
              history_v1.SNAPSHOT: canonical(snapshot), BASELINE: canonical(tree.free_counts)}
    if refresh_shapes:
        values.update(shapes)
    return [(name, read(root, name) if (root / name).exists() else '', value)
            for name, value in values.items()]


def check(root, require_history=False):
    tree = model.load_tree(root)
    check_shapes(root, tree=tree)
    check_ratchet(root, tree)
    tags = release_tags(root)
    if tags:
        values = render(root, tree=tree)
    else:
        if require_history:
            raise ValueError('release history unavailable; fetch annotated release tags for full verification')
        tables = [table(read(root, name), name) for name in OUTPUTS]
        if len(set(tables)) != 1:
            raise ValueError('stale contract stamps: tables disagree')
        snapshot = history_v1.snapshot(lambda name: read(root, name))
        expected = dict(format=history_v1.FORMAT, history=snapshot['history'], surfaces=current_rows(tree))
        values = [(OUTPUTS[0], read(root, OUTPUTS[0]), assemble(tree, tables[0])),
                  (history_v1.SNAPSHOT, read(root, history_v1.SNAPSHOT), canonical(expected)),
                  (BASELINE, read(root, BASELINE), canonical(tree.free_counts))]
    stale = [name for name, before, after in values if before != after]
    if stale:
        raise ValueError('stale generated contract: ' + ', '.join(stale) +
                         '; run tests/lib/python.sh docs/generate_contract_stamps.py')
    return bool(tags)
