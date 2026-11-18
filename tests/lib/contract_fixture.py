"""Prepare contract authoring, history and guide regions in disposable test repositories.

Fresh authoring fixtures begin before their first release. Rehearsals copied
from a released checkout instead import that checkout's actual release trees;
they never erase inherited history claims to make a release render succeed.
A constructed release source also owns its guide regions: it regenerates them
from its own owners instead of presuming the copied guide equals them.
"""
import json
from pathlib import Path
import subprocess
import sys

CHECKOUT = Path(__file__).resolve().parents[2]


def write_outputs(root, values):
    for name, _, after in values:
        path = Path(root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after)


def presentation(root, documents, *, commitments=()):
    """Give a constructed tree explicit destinations supplied by its caller."""
    root = Path(root)
    data = dict(documents=documents, commitments=list(commitments))
    (root / 'docs/contract/presentation.json').write_text(json.dumps(data, indent=2) + '\n')
    (root / 'docs/contract/trace-introduction.md').write_text('# Constructed contract\n')
    regions = {name: [entry['region'] for entry in entries] for name, entries in documents.items()}
    for entry in commitments:
        regions.setdefault(entry['document'], []).append(entry['region'])
    for name, entries in regions.items():
        if name == 'docs/CONTRACT.md':
            continue
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# Constructed presentation\n\n' + '\n\n'.join(
            f'<!-- BEGIN GENERATED CONTRACT {region} -->\n<!-- END GENERATED CONTRACT {region} -->'
            for region in entries) + '\n')


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
        'syntax: 1\nartifact: "Fixture"\n'
        'goldens: ["tests/fixtures/contract/surfaces/fixture.json"]\n'
        f'checks: {json.dumps(list(checks))}\n```\n\n'
        '## Defined value {value: definition}\n\n'
        'The fixture records its own release history.\n')
    shape = root / 'tests/fixtures/contract/surfaces/fixture.json'
    shape.parent.mkdir(parents=True, exist_ok=True)
    shape.write_text(json.dumps({'records': {}}, indent=2, sort_keys=True) + '\n')
    presentation(root, {'docs/CONTRACT.md': [dict(region='fixture', nodes=['fixture'])]})


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
    (root / runtime.CONTRACT).unlink(missing_ok=True)
    (root / runtime.history_v1.SNAPSHOT).unlink(missing_ok=True)
    guide = root / runtime.GUIDE
    before = guide.read_text() if guide.exists() else runtime.BEGIN + '\n' + runtime.END + '\n'
    guide.parent.mkdir(parents=True, exist_ok=True)
    guide.write_text(runtime._replace_table(before, str(guide), '\n'))
    tree = model.load_tree(root)
    (root / runtime.BASELINE).write_text(runtime.canonical(tree.free_counts))
    write_outputs(root, runtime.render(root, refresh_shapes=True, tree=tree))


def fresh_guide_regions(root, *, run=subprocess.run):
    """Regenerate a constructed release source's limits tables and guide copies from its own owners.

    The fixture's own docs/generate_limits.py runs in strict write mode before
    the fixture is committed, tagged or staged. The generator writes beside its
    own resolved location, so a script that resolves outside the fixture, or a
    fixture that is this checkout, is refused before anything runs. Callers
    that record their launches pass their own `run`.
    """
    root = Path(root).resolve()
    script = root / 'docs/generate_limits.py'
    if root == CHECKOUT or script.resolve() != script:
        raise ValueError('guide regions are regenerated only inside a disposable fixture: ' + str(script.resolve()))
    result = run([sys.executable, '-B', '-S', str(script), '--publication'],
                 cwd=root, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError('constructed release source: ' + (result.stderr.strip() or result.stdout.strip()))
    return result


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
