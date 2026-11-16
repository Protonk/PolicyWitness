"""Compare a change class with a committed predecessor; never refresh goldens."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'docs'), str(ROOT / 'docs/contract')]
import build_contract
import generate_worker_identity
import runtime
import tree

parser = argparse.ArgumentParser()
parser.add_argument('--base', required=True)
parser.add_argument('--kind', choices=('placement', 'part', 'public'), required=True)
parser.add_argument('--node', action='append', default=[])
parser.add_argument('--output', required=True)
args = parser.parse_args()


def old(name):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', args.base + ':' + name])


before = json.loads(old('docs/contract/public.json'))
model = tree.load_tree(ROOT)
after = dict(format=before['format'], history=before['history'], surfaces=runtime.current_rows(model))
differences = []
removed = 0
for prior, current in zip(before['surfaces'], after['surfaces'], strict=True):
    assert prior['id'] == current['id']
    for group in ('nodes', 'shared'):
        for a, b in zip(prior['public'][group], current['public'][group], strict=True):
            assert a['id'] == b['id']
            if args.kind == 'part' and 'part' in a['facts']:
                del a['facts']['part']
                removed += 1
            if a != b:
                differences.append({'surface': prior['id'], 'group': group, 'node': a['id'],
                                    'before': a, 'after': b})
                assert args.kind == 'public' and a['id'] in args.node, (prior['id'], group, a['id'])
                # Public prose corrections may not silently change scope or shape.
                for key in ('context', 'each_scope', 'case_order', 'field', 'variants', 'referenced_types'):
                    assert a.get(key) == b.get(key), (a['id'], key)
    if args.kind != 'public':
        assert prior == current, prior['id']
if args.kind == 'part':
    assert removed > 0
if args.kind == 'public':
    assert set(args.node) == {d['node'] for d in differences}
assert (ROOT / 'docs/PolicyWitness.md').read_bytes() == old('docs/PolicyWitness.md')
assert (ROOT / runtime.BASELINE).read_bytes() == old(runtime.BASELINE)
for name in runtime.check_shapes(ROOT, tree=model):
    assert (ROOT / name).read_bytes() == old(name), name
for name in runtime.STAMP_OUTPUTS:
    assert runtime.table((ROOT / name).read_text(), name) == runtime.table(old(name).decode(), name), name
baseline = json.loads((ROOT / 'records/documentation-trace/baseline.json').read_text())
for name, digest in baseline['files_sha256'].items():
    if (name.startswith('controller/interface/') and name != 'controller/interface/README.md') or name in ('docs/porcelain.json', 'tests/fixtures/contract/abi_layout.txt'):
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
record = dict(base=args.base, kind=args.kind, removed_part_occurrences=removed,
              differences=differences, guide_shapes_counts_stamps_interfaces_preserved=True,
              build_identity=build_contract.identity(ROOT), worker_identity=generate_worker_identity.identity(ROOT))
(ROOT / args.output).write_text(runtime.canonical(record))
print(json.dumps({k: v for k, v in record.items() if k != 'differences'}))
