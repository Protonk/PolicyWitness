"""Read-only D1 inventory and compact local receipt extraction; no checking implementation.

Run with tests/lib/python.sh records/check-support/collect.py. Outputs stay here.
The source checkout must be the fixed D1 tree plus this package/owning-plan edits.
"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
STAMP = 'cf0136bbb6366d5f787c3547ec69d757772898c0'
sys.path[:0] = [str(ROOT / 'docs'), str(ROOT / 'tests/lib')]
import fixture_inputs


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def inventory():
    result = dict(source=STAMP, interpretation='Expanded declarations, not observed filesystem reads', rules=[], generators=[])
    for name in ('check', 'build_rules'):
        path = f'tests/suites/source_drift/{name}.py'
        module = load('d1_' + name, path)
        parsed = ast.parse((ROOT / path).read_text())
        table = next(n for n in parsed.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'RULES' for t in n.targets))
        for rule, declaration in zip(module.RULES, table.value.elts):
            result['rules'].append(dict(module=path, id=rule.id, declaration=ast.unparse(declaration),
                                       inputs=fixture_inputs.expand(ROOT, rule.inputs, rule.helpers)))
    for name in fixture_inputs.GENERATORS:
        gen = fixture_inputs.generator_module(name, ROOT)
        result['generators'].append(dict(name=name, inputs=fixture_inputs.generator_inputs(ROOT, name),
                                        spans=list(getattr(gen, 'SPAN_DOCUMENTS', ())),
                                        targets=list(getattr(gen, 'TARGETS', ())), regions=list(getattr(gen, 'REGIONS', ()))))
    catalog = json.loads((ROOT / 'tests/catalog.json').read_text())
    result['cases'] = [dict(suite=suite, suite_command=value['command'], **case)
                       for suite, value in catalog['suites'].items() for case in value.get('cases', [])
                       if suite == 'source_drift' or (suite == 'preflight' and case['id'] in ('build_entry_controls', 'native_policy_controls', 'native_source_controls'))]
    result['baselines'] = {p.name:json.loads(p.read_text()) for p in sorted((ROOT / 'tests/fixtures/docs').glob('*.json'))}
    save('inventory-inputs.json', result)
    receipt = json.loads((ROOT / 'docs/worker-launch-observation.json').read_text())
    trace = dict(source=STAMP, observation=receipt['observation_id'], run_id=receipt['run_id'], receipt_source=receipt['source_revision'],
                 receipt_worker_identity=receipt['worker_source_identity'], artifact_count=len(receipt['artifact_hashes']), files={})
    for path, digest in receipt['source_files'].items():
        now = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        trace['files'][path] = dict(receipt=digest, current=now, equal=digest == now)
    trace['retained'] = json.loads((ROOT / 'tests/RETAINED.json').read_text())
    architecture = json.loads((ROOT / 'docs/architecture.json').read_text())
    graph = next(g for g in architecture['graphs'] if g['id'] == 'worker_capabilities')
    trace['capabilities'] = [n for n in graph['nodes'] if any(c['symbol'] == 'launch_inventory' for c in n.get('checks', []))]
    save('l-facts.json', trace)


def costs():
    base = Path('/Users/raccoon/Desktop/Security/PolicyWitness/tests/out/runs')
    result = dict(inventory_source=STAMP, boundary='Historical costs, not a fresh execution or performance forecast', runs=[])
    for name in ('drift-plan-investigation-20261027-02', 'drift-cost-candidate-01', 'drift-acceptance-fixes-03'):
        root = base / name
        run = json.loads((root / 'run.json').read_text())
        row = dict(path=str(root), run_id=run['run_id'], duration_ms=run['duration_ms'], ok=run['ok'],
                   case_results=run['case_results'], python=run['configuration']['python'], receipts=[])
        old = root / 'investigation/report.json'
        if old.exists():
            report = json.loads(old.read_text())
            row['historical_profile'] = dict(source=report['source'], measurements=report['measurements'],
                                             sha256=hashlib.sha256(old.read_bytes()).hexdigest())
        source = root / 'investigation/source.json'
        if source.exists():
            snapshot = json.loads(source.read_text())
            mismatches = []
            for path, entry in snapshot['files'].items():
                if entry['kind'] != 'file':
                    continue
                data = subprocess.run(['git', 'show', f'{STAMP}:{path}'], cwd=ROOT, capture_output=True)
                if data.returncode or hashlib.sha256(data.stdout).hexdigest() != entry['sha256']:
                    mismatches.append(path)
            row['source_snapshot'] = dict(path=str(source.relative_to(root)), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                          head=snapshot['head'], observation=snapshot.get('observation'),
                                          changed_from_inventory=mismatches)
        files = sorted(set(root.rglob('*-receipts.json')) | set(root.rglob('receipts.json')) | set(root.rglob('controls.json')))
        for path in files:
            data = json.loads(path.read_text())
            if not isinstance(data, dict) or 'controls' not in data or 'case' not in data:
                continue
            controls = data['controls']
            snapshots = {s for control in controls for s in control.get('inputs', [])}
            observations = [json.loads((path.parent / s).read_text()) for s in sorted(snapshots)]
            row['receipts'].append(dict(path=str(path.relative_to(root)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 case=data['case'], mode=data['mode'], ok=data['ok'], complete=data['complete'], controls=len(controls),
                 launch_instrumentation_present=any('launches' in c for c in controls),
                 input_instrumentation_present=any('inputs' in c for c in controls),
                 elapsed_seconds=sum(c.get('elapsed_seconds', 0) for c in controls),
                 direct_launches=sum(len(c.get('launches', [])) for c in controls),
                 input_snapshots=len(snapshots), snapshot_selected_entries=sum(len(s['entries']) for s in observations),
                 snapshot_observed_bytes=sum(s['bytes'] for s in observations)))
        result['runs'].append(row)
    save('cost-facts.json', result)


def host_finding():
    module = load('d1_host', 'tests/suites/source_drift/check.py')
    snippets = ['sandbox_check(value)', 'sandbox_extension_issue_file(value)', 'sandbox_extension_consume(value)',
                'sandbox_extension_release(value)', 'let f = dlsym(handle, "sandbox_extension_consume")',
                'let h = dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW)', '// sandbox_extension_consume(value)']
    save('host-finding.json', dict(source=STAMP, description='Local in-process diagnostic, not a dispatcher case',
         known_symbols=sorted(module.HOST_SANDBOX_SYMBOLS),
         observations=[dict(source=s, diagnostics=[p.message for p in module.host_invariance_problems('constructed', s)]) for s in snippets]))


if __name__ == '__main__':
    changed = subprocess.check_output(['git', 'diff', '--name-only', STAMP], cwd=ROOT, text=True).splitlines()
    changed += subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    outside = [p for p in changed if not (p.startswith('records/check-support/') or
               p == 'tests/suites/source_drift/BINDING-THRU-REPLAY-PLAN.md')]
    if outside:
        raise SystemExit(f'fixed-source extraction refused: changed inputs outside D1 ownership: {outside}')
    inventory()
    costs()
    host_finding()
