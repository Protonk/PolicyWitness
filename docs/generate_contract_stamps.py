#!/usr/bin/env python3
"""Derive public surface stamps from annotated release trees and authored definitions."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

# Discovery also loads this module by filename from outside the source tree.
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ('docs/CONTRACT.md', 'docs/PolicyWitness.md')
BEGIN = '<!-- BEGIN GENERATED CONTRACT STAMPS -->'
END = '<!-- END GENERATED CONTRACT STAMPS -->'


def contract_module(name):
    """Load an authoring helper without colliding with tests/lib/contract.py."""
    path = Path(__file__).resolve().parent / 'contract' / (name + '.py')
    module_name = f'_pw_contract_{name}_{abs(hash(str(path)))}'
    if module_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[module_name]
            raise
    return sys.modules[module_name]


def tree_input_paths(root):
    """Discover authored inputs leniently; validation belongs to the tree reader."""
    directory = root / 'docs/contract'
    if not directory.exists():
        return set()
    import markdown_reader
    paths = {p.relative_to(root).as_posix() for p in directory.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    paths.update(markdown_reader.source_files(root))
    paths.add('docs/generator_common.py')
    paths.update(contract_module('record_definitions').input_paths(root))
    for path in sorted(directory.glob('*.surface.md')):
        try:
            document = markdown_reader.parse(path.read_text(), path.as_posix())
            for block in document.fences('contract'):
                for line in block.content.splitlines():
                    key, _, raw = line.partition(':')
                    try:
                        value = json.loads(raw)
                    except ValueError:
                        continue
                    if key in {'source', 'check'}:
                        citations = value if isinstance(value, list) else [value]
                        paths.update(citation['path'] for citation in citations
                                     if isinstance(citation, dict) and isinstance(citation.get('path'), str))
                    if key == 'goldens' and isinstance(value, list):
                        paths.update(item for item in value if isinstance(item, str))
        except (OSError, ValueError):
            continue
    return paths


# The entry point remains stable for builds and fixture discovery. Historical
# representations have independent readers under docs/contract/.
_backend = contract_module('runtime')
OUTPUTS = _backend.OUTPUTS
BEGIN, END = _backend.BEGIN, _backend.END
DOCUMENT_BEGIN, DOCUMENT_END = _backend.DOCUMENT_BEGIN, _backend.DOCUMENT_END
BASELINE = _backend.BASELINE
render, check = _backend.render, _backend.check
stamps, release_tags = _backend.stamps, _backend.release_tags
check_shapes, collected_shapes = _backend.check_shapes, _backend.collected_shapes


def input_paths(root):
    return sorted({*tree_input_paths(root), *OUTPUTS,
                   'docs/generate_contract_stamps.py', 'docs/generate_porcelain.py',
                   'docs/limits.json', 'tests/catalog.json', 'docs/porcelain.json',
                   'controller/src/runner_select.rs'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--release')
    parser.add_argument('--require-history', action='store_true', help='refuse incomplete stamp verification')
    parser.add_argument('--refresh-shapes', action='store_true', help='recollect surface shape goldens for review')
    parser.add_argument('--preview', metavar='PATH', help='render the draft tree separately from the public contract')
    parser.add_argument('--tree-check', action='store_true', help='require complete definitions and support in the draft tree')
    args = parser.parse_args()
    try:
        if args.preview or args.tree_check:
            if args.check or args.release or args.refresh_shapes or args.require_history:
                raise ValueError('draft tree modes cannot change or check release stamps')
            model = contract_module('tree')
            tree = model.load_tree(ROOT, strict=args.tree_check)
            body = model.render(tree)
            if args.preview:
                output = Path(args.preview).resolve()
                if output == (ROOT / 'docs/CONTRACT.md').resolve():
                    raise ValueError('preview must leave the current public contract intact')
                output.write_text(body)
            print(json.dumps(model.statistics(tree, body), indent=2, sort_keys=True))
            return
        if args.check and args.refresh_shapes:
            raise ValueError('--check cannot refresh goldens')
        if args.check:
            complete = check(ROOT, args.require_history)
            print('ok: contract surface stamps current' if complete else
                  'ok: contract inputs current; stamp derivation not checked (release history unavailable)')
            return
        if args.require_history and not release_tags(ROOT):
            raise ValueError('release history unavailable; fetch annotated release tags')
        results = render(ROOT, args.release, refresh_shapes=args.refresh_shapes)
        stale = [name for name, before, after in results if before != after]
        if args.check and stale:
            raise ValueError('stale contract stamps: ' + ', '.join(stale) + '; run tests/lib/python.sh docs/generate_contract_stamps.py')
        if not args.check:
            for name, before, after in results:
                if before != after:
                    (ROOT / name).parent.mkdir(parents=True, exist_ok=True)
                    (ROOT / name).write_text(after)
        print('ok: contract surface stamps current')
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'contract stamps: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
