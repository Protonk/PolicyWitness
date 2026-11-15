#!/usr/bin/env python3
"""Apply governing-source mutations to a candidate worktree and record what each check does.

usage: mutate.py WORKTREE CARGO_TARGET_DIR SPEC.json OUT.json

Each mutation is a list of exact single-occurrence edits. For each one the
harness builds, regenerates a stale inventory with its owner, compares the card
bytes, and runs the literal check, the contract check, the case corpus, the
card-versus-execution test, the unit tests and any listed probes against an
unsigned build placed in a scratch app directory. The worktree is restored
with `git checkout` after every mutation.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

WT, TARGET, SPEC, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
SCRATCH = Path(TARGET).parent / ('mutation-app-' + WT.name)
BIN = SCRATCH / 'Mut.app/Contents/MacOS/policy-witness'
ENV = {**os.environ, 'PATH': '/opt/homebrew/opt/rustup/bin:' + os.environ['PATH'], 'CARGO_TARGET_DIR': TARGET,
       'PW_BUILD_CONTRACT': 'test:mutation', 'PW_INTERFACE_TARGET_DIR': TARGET}
CARGO = ['cargo', 'build', '--offline', '--target', 'aarch64-apple-darwin', '--bin', 'policy-witness']


def run(command, cwd=WT, env=None):
    started = time.time()
    result = subprocess.run(command, cwd=cwd, env=env or ENV, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr, round(time.time() - started, 1)


def build():
    status, output, seconds = run(CARGO, WT / 'controller')
    if status == 0:
        kind, message = 'ok', ''
    elif 'inventory.json is stale' in output:
        kind, message = 'stale_inventory', 'controller/interface/inventory.json is stale'
    elif 'error: help cards:' in output:
        kind = 'card_validation'
        message = re.search(r'error: (help cards: .*)', output)[1]
    else:
        kind = 'compile_error'
        message = '; '.join(dict.fromkeys(re.findall(r'^(error(?:\[E\d+\])?: .*)$', output, re.M)))[:600]
    return {'result': kind, 'message': message, 'seconds': seconds}


def cards():
    return {name: card['text'] for name, card in json.loads((WT / 'controller/interface/inventory.json').read_text())['cards'].items()}


def generator(refresh):
    command = ['tests/lib/python.sh', 'docs/generate_interface.py'] + (['--refresh-residue'] if refresh else [])
    status, output, seconds = run(command)
    return {'result': 'ok' if status == 0 else 'refused', 'message': output.strip()[-700:], 'seconds': seconds}


def install():
    BIN.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(TARGET) / 'aarch64-apple-darwin/debug/policy-witness', BIN)


def cases():
    env = {**ENV, 'PW_INTEGRATION': '1', 'PW_BIN_PATH': str(BIN), 'PW_APP_DIR': str(SCRATCH / 'Mut.app')}
    status, output, seconds = run(['cargo', 'test', '--offline', '--target', 'aarch64-apple-darwin', '--test', 'cli_contract',
                                   '--', 'interface_cases_hold', 'help_cards_agree'], WT / 'controller', env)
    agreement = re.search(r'test help_cards_agree_with_execution \.\.\. (\w+)', output)
    panic = re.search(r"help_cards_agree_with_execution[^\n]*panicked at [^\n]*\n([^\n]*(?:\n[^\n]*){0,3})", output)
    return {'failing': sorted(set(re.findall(r'^(\S+) step \d+:', output, re.M))),
            'agreement': agreement[1] if agreement else 'not_run',
            'agreement_message': panic[1].strip()[:400] if panic and agreement and agreement[1] != 'ok' else '',
            'ran': bool(re.search(r'test interface_cases_hold_on_the_signed_controller \.\.\. ', output)),
            'seconds': seconds}


def unit():
    status, output, seconds = run(['cargo', 'test', '--offline', '--target', 'aarch64-apple-darwin', '--bin', 'policy-witness'],
                                  WT / 'controller')
    return {'failing': sorted(set(re.findall(r'^test (\S+) \.\.\. FAILED', output, re.M))),
            'ran': 'test result:' in output, 'seconds': seconds}


def contract():
    status, output, seconds = run(['tests/lib/python.sh', 'docs/generate_contract_stamps.py', '--check'])
    return {'result': 'ok' if status == 0 else 'refused', 'message': output.strip()[:900], 'seconds': seconds,
            'public_snapshot_sha256': hashlib.sha256((WT / 'docs/contract/public.json').read_bytes()).hexdigest()}


def literals():
    status, output, seconds = run(['tests/lib/python.sh', 'tests/suites/source_drift/interface_literals.py'])
    return {'result': 'ok' if status == 0 else 'refused', 'message': output.strip()[:700], 'seconds': seconds}


def probe(arguments):
    result = subprocess.run([str(BIN), *arguments], capture_output=True, stdin=subprocess.DEVNULL)
    try:
        envelope = json.loads(result.stdout)
        shown = {'error': envelope.get('result', {}).get('error'), 'exit_code': envelope.get('result', {}).get('exit_code'),
                 'normalized_outcome': envelope.get('result', {}).get('normalized_outcome')}
    except ValueError:
        shown = {'stdout': result.stdout.decode(errors='replace')[:300]}
    return {'args': arguments, 'status': result.returncode, **shown, 'stderr': result.stderr.decode(errors='replace')[:200]}


def observe(spec):
    record = {'build': build()}
    first = record['build']['result']
    if first == 'stale_inventory':
        if spec.get('generator_without_refresh'):
            record['generator_without_refresh'] = generator(False)
        record['regenerated'] = generator(True)
        record['build_after_regeneration'] = build()
    usable = record.get('build_after_regeneration', record['build'])['result'] == 'ok'
    record['literals'] = literals()
    record['contract'] = contract()
    if usable:
        install()
        record['cards'] = cards()
        record['cases'] = cases()
        record['unit'] = unit()
        record['probes'] = [probe(arguments) for arguments in spec.get('probes', [])]
    return record


def main():
    spec = json.loads(SPEC.read_text())
    assert run(['git', 'status', '--porcelain'])[1].strip() == '', 'the worktree must be clean'
    probes = [json.loads(text) for text in sorted({json.dumps(p) for m in spec['mutations'] for p in m.get('probes', [])})]
    baseline = observe({'probes': probes})
    results = {'worktree': str(WT), 'head': run(['git', 'rev-parse', 'HEAD'])[1].strip(), 'baseline': baseline, 'mutations': []}
    for mutation in spec['mutations']:
        try:
            for edit in mutation['edits']:
                path = WT / edit['path']
                text = path.read_text()
                assert text.count(edit['old']) == 1, f'{mutation["id"]}: {edit["path"]}: {text.count(edit["old"])} matches for {edit["old"][:60]!r}'
                path.write_text(text.replace(edit['old'], edit['new']))
            diff = run(['git', 'diff', '--', *sorted({edit['path'] for edit in mutation['edits']})])[1]
            observed = observe(mutation)
        finally:
            run(['git', 'checkout', '--', '.'])
        summary = {'id': mutation['id'], 'entry': mutation['entry'], 'mutation': mutation['description'], 'patch': diff,
                   'observed': observed}
        if 'cards' in observed:
            summary['cards_changed'] = sorted(name for name, text in observed['cards'].items() if text != baseline['cards'][name])
            summary['cases_newly_failing'] = sorted(set(observed['cases']['failing']) - set(baseline['cases']['failing']))
            summary['cases_newly_passing'] = sorted(set(baseline['cases']['failing']) - set(observed['cases']['failing']))
            summary['unit_newly_failing'] = sorted(set(observed['unit']['failing']) - set(baseline['unit']['failing']))
        summary['public_snapshot_changed'] = (observed['contract']['public_snapshot_sha256']
                                              != baseline['contract']['public_snapshot_sha256'])
        results['mutations'].append(summary)
        OUT.write_text(json.dumps(results, indent=2) + '\n')
        print(mutation['id'], observed['build']['result'], summary.get('cards_changed'), observed['literals']['result'],
              observed['contract']['result'], len(summary.get('cases_newly_failing', [])), flush=True)
    restored = build()
    assert restored['result'] == 'ok', restored
    OUT.write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
