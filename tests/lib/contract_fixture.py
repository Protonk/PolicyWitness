"""Prepare contract authoring and history in disposable test repositories.

Fresh authoring fixtures begin before their first release. Rehearsals copied
from a released checkout instead import that checkout's actual release trees;
they never erase inherited history claims to make a release render succeed.
"""
import json
from pathlib import Path
import subprocess


def write_outputs(root, values):
    for name, _, after in values:
        path = Path(root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after)


def minimal_surfaces(root, *, checks=('fixture',)):
    """Replace authored surfaces in a disposable fixture, retaining release claims.

    The fixture owns its small definition and golden. Existing generated tables,
    public snapshot and free-text counts stay intact for history verification by
    the subsequent render. Fresh authoring separately clears inherited claims
    before its first commit; rehearsals instead seed real release ancestry.
    """
    root = Path(root)
    source_dir = root / 'docs/contract'
    source_dir.mkdir(parents=True, exist_ok=True)
    for path in source_dir.glob('*.surface.md'):
        path.unlink()
    (source_dir / '00-fixture.surface.md').write_text(
        '# Fixture contract {fixture: surface}\n\n```contract\n'
        'syntax: 1\nartifact: "Fixture"\npart: "definitions"\n'
        'goldens: ["tests/fixtures/contract/surfaces/fixture.json"]\n'
        f'checks: {json.dumps(list(checks))}\n```\n\n'
        '## Defined value {value: definition}\n\n'
        'The fixture records its own release history.\n')
    shape = root / 'tests/fixtures/contract/surfaces/fixture.json'
    shape.parent.mkdir(parents=True, exist_ok=True)
    shape.write_text(json.dumps({'records': {}}, indent=2, sort_keys=True) + '\n')


def fresh_authoring(root, generator, *, minimal=False):
    """Create a first-release source fixture before it has any Git history.

    Callers copy declared source inputs first. Generated release claims from
    that copy are deliberately not fixture inputs: this fixture has its own
    authored history beginning with its first subsequently committed snapshot.
    """
    root = Path(root)
    head = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'],
                          capture_output=True, text=True)
    if head.returncode == 0:
        raise ValueError('fresh authoring requires a fixture before its first commit')
    runtime = generator.contract_module('runtime')
    model = generator.contract_module('tree')
    if minimal:
        minimal_surfaces(root)
    (root / runtime.OUTPUTS[0]).unlink(missing_ok=True)
    (root / runtime.history_v1.SNAPSHOT).unlink(missing_ok=True)
    guide = root / runtime.OUTPUTS[1]
    before = guide.read_text() if guide.exists() else runtime.BEGIN + '\n' + runtime.END + '\n'
    guide.parent.mkdir(parents=True, exist_ok=True)
    guide.write_text(runtime._replace_table(before, str(guide), '\n'))
    tree = model.load_tree(root)
    (root / runtime.BASELINE).write_text(runtime.canonical(tree.free_counts))
    write_outputs(root, runtime.render(root, refresh_shapes=True, tree=tree))


def seed_release_history(root, source, generator):
    """Import real local release trees beneath a copied rehearsal worktree.

    Return an unused, increasing synthetic version for the fixture's next
    release. All operations concern disposable Git state and a local source.
    """
    root, source = Path(root), Path(source)
    if (root / '.git').exists():
        raise ValueError('rehearsal history requires a fresh disposable repository')
    tags = generator.release_tags(source)
    if not tags:
        raise ValueError('rehearsal requires the source checkout release history')
    command = ['git', '-C', str(root)]
    subprocess.run([*command, 'init', '-q'], check=True, capture_output=True, text=True)
    subprocess.run([*command, 'fetch', '-q', '--no-tags', str(source),
                    *(f'refs/tags/{tag}:refs/tags/{tag}' for tag in tags)],
                   check=True, capture_output=True, text=True)
    subprocess.run([*command, 'reset', '--mixed', f'{tags[-1]}^{{commit}}'],
                   check=True, capture_output=True, text=True)
    major = max(int(tag[1:].split('.')[0]) for tag in tags) + 1
    return f'v{major}.0.0'
