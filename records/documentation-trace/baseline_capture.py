"""Read-only baseline capture; writes only its adjacent baseline.json record."""
from collections import Counter
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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).decode().strip()


def files(names):
    return {name: sha((ROOT / name).read_bytes()) for name in sorted(set(names))}


model = tree.load_tree(ROOT)
rows = runtime.current_rows(model)
stored = json.loads((ROOT / 'docs/contract/public.json').read_text())
assert rows == stored['surfaces'], 'current authored public payload differs from starting public.json'
shapes = runtime.check_shapes(ROOT, tree=model)
assert json.loads((ROOT / runtime.BASELINE).read_text()) == model.free_counts
tables = {name: runtime.table((ROOT / name).read_text(), name) for name in runtime.OUTPUTS}
assert len(set(tables.values())) == 1
names = ['docs/contract/public.json', runtime.BASELINE, 'docs/PolicyWitness.md',
         'docs/CONTRACT.md', 'docs/porcelain.json', 'tests/fixtures/contract/abi_layout.txt']
names += list(shapes)
names += [str(path.relative_to(ROOT)) for path in (ROOT / 'controller/interface').rglob('*') if path.is_file()]
names += list(generate_worker_identity.TARGETS)
result = {
    'starting_commit': git('rev-parse', 'HEAD'),
    'reviewed_commit': '6fcd2b5f1c84094405e2ce4de035b538a411b7cc',
    'changes_since_review': git('diff', '--name-status', '6fcd2b5f1c84094405e2ce4de035b538a411b7cc', 'HEAD'),
    'public_snapshot_source': 'git show <starting_commit>:docs/contract/public.json',
    'current_payloads_equal_starting_snapshot': True,
    'canonical_payload_sha256': {row['id']: sha(runtime.canonical(row['public']).encode()) for row in rows},
    'stamp_tables': tables,
    'free_text_counts': model.free_counts,
    'node_counts': dict(Counter(node.kind for node in model.nodes)),
    'files_sha256': files(names),
    'build_identity': build_contract.identity(ROOT),
    'build_input_sha256': files(build_contract.inputs(ROOT)),
    'worker_identity': generate_worker_identity.identity(ROOT),
    'worker_input_sha256': files(generate_worker_identity.source_paths(ROOT)),
    'reachable_annotated_release_tags': runtime.release_tags(ROOT),
    'selected_signing_identity': 'Developer ID Application: Adam Hyland (42D369QV8E)',
    'selected_signing_certificate_sha1': '1A6E85D06FC762993C8BD3E932556DED3985F030',
}
destination = Path(__file__).with_name('baseline.json')
destination.write_text(runtime.canonical(result))
print(json.dumps({key: result[key] for key in ('starting_commit', 'build_identity', 'worker_identity', 'node_counts', 'free_text_counts')}))
print(destination)
