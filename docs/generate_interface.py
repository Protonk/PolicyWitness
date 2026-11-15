#!/usr/bin/env python3
"""Maintain the committed interface inventory, its joins and its residue baseline.

The controller's build script writes the inventory from the definitions the
binary compiles and stops a build whose committed copy is stale; that is the
freshness check for the inventory. This generator checks the committed copy
without Cargo, derives the case and mutation joins from retained data and
holds the residue baseline: write mode records reductions, and additions need
--refresh-residue and a reviewed diff. --refresh-inventory first replaces the
committed inventory from a build-script run.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = 'controller/interface'
INVENTORY = DIRECTORY + '/inventory.json'
RESIDUE = DIRECTORY + '/residue.json'
JOINS = DIRECTORY + '/joins.json'
MUTATIONS = DIRECTORY + '/mutations.json'
CASES = 'controller/integration/interface_cases.json'
OUTPUTS = (INVENTORY, RESIDUE, JOINS)
GENERATOR_NAME = 'docs/generate_interface.py'
KINDS = ('admits', 'refuses_always', 'discards', 'alias', 'unenumerated')
CHECKS = ('card', 'contract', 'cases')
STATES = ('not_run', 'unchanged', 'changed', 'failed')
UNLISTED = {'unlisted': True}


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + '\n'


def read_json(root, name):
    return json.loads((root / name).read_text())


def input_paths(root):
    """Every path a default or check run reads."""
    return [GENERATOR_NAME, INVENTORY, RESIDUE, JOINS, MUTATIONS, CASES]


def built_inventory(root):
    """The inventory a build-script run writes, from an isolated Cargo output directory."""
    target = os.environ.get('PW_INTERFACE_TARGET_DIR')
    with tempfile.TemporaryDirectory(prefix='pw-interface-') as scratch:
        command = ['cargo', 'check', '--offline', '--manifest-path', str(root / 'controller/Cargo.toml'),
                   '--target', 'aarch64-apple-darwin', '--target-dir', target or scratch,
                   '--message-format=json', '--bin', 'policy-witness']
        environment = {**os.environ, 'PW_INTERFACE_REFRESH': '1'}
        environment.pop('PW_BUILD_CONTRACT', None)
        result = subprocess.run(command, capture_output=True, text=True, env=environment)
        if result.returncode:
            raise ValueError('the controller build script did not run:\n' + result.stderr[-2000:])
        for line in result.stdout.splitlines():
            message = json.loads(line)
            if message.get('reason') == 'build-script-executed' and '/controller' in message.get('package_id', ''):
                return (Path(message['out_dir']) / 'interface/inventory.json').read_text()
    raise ValueError('Cargo reported no build-script run for the controller package')


def all_ids(inventory):
    ids = [entry['id'] for entry in inventory['entries']]
    ids += [row['id'] for row in inventory['result']['rows']]
    ids += ['result.fields', inventory['example']['id']]
    return ids


def card_tokens(inventory, name):
    """Every token the card's referenced entries, example fields and result rows can supply."""
    known = {entry['id']: entry for entry in inventory['entries']}
    rows = {row['id']: row for row in inventory['result']['rows']}
    supplied = set()
    for reference in inventory['cards'][name]['references']:
        if reference in known:
            supplied.update(known[reference]['spellings'])
        elif reference in rows:
            outputs = rows[reference]['outputs']
            outcome = outputs['normalized_outcome']
            if isinstance(outcome, dict):
                supplied.update([outcome['fixed']] if 'fixed' in outcome else outcome['refusal'])
            host = rows[reference]['inputs']['host_outcome']
            if isinstance(host, dict):
                supplied.add(host['is'])
            supplied.update([json.dumps(outputs['ok']), json.dumps(outputs['exit_code'])])
        elif reference == 'result.fields':
            supplied.update(field['name'] for field in inventory['result']['fields'])
        elif reference == inventory['example']['id']:
            for phase in inventory['example']['phases']:
                supplied.add(phase['phase_id'])
                for attempt in phase['attempts']:
                    supplied.update([attempt['action'], attempt['target']])
    return supplied


def relation(inventory):
    """The result relation evaluated from its rows alone: (row id, outputs) over every input combination."""
    rows = sorted(inventory['result']['rows'], key=lambda row: row['order'])
    labels, refusals = [], []
    for row in rows:
        outcome, host = row['outputs']['normalized_outcome'], row['inputs']['host_outcome']
        if isinstance(outcome, dict) and 'fixed' in outcome:
            labels.append(outcome['fixed'])
        if isinstance(outcome, dict) and 'refusal' in outcome:
            refusals = outcome['refusal']
        if isinstance(host, dict):
            labels.append(host['is'])
    evaluated = []
    for name in dict.fromkeys(row['inputs']['class'] for row in rows):
        members = [row for row in rows if row['inputs']['class'] == name]
        reads_host = any(row['inputs']['host_outcome'] != 'unread' for row in members)
        hosts = [None, *dict.fromkeys(labels + refusals), UNLISTED] if reads_host else [None]
        for host in hosts:
            for refusal in (refusals if any(isinstance(row['outputs']['normalized_outcome'], dict)
                                            and 'refusal' in row['outputs']['normalized_outcome'] for row in members) else [None]):
                for row in members:
                    condition = row['inputs']['host_outcome']
                    holds = (condition == 'unread' or (condition == 'present' and host is not None)
                             or (condition == 'absent' and host is None)
                             or (isinstance(condition, dict) and host == condition['is']))
                    if not holds:
                        continue
                    outcome = row['outputs']['normalized_outcome']
                    label = (outcome['fixed'] if isinstance(outcome, dict) and 'fixed' in outcome
                             else refusal if isinstance(outcome, dict) else host)
                    evaluated.append((row['id'], [label, row['outputs']['ok'], row['outputs']['exit_code']]))
                    break
                else:
                    raise ValueError(f'the result relation has no row for class {name} with host label {host!r}')
    return evaluated


def validate(inventory):
    """Problems in the committed inventory that need no build to find."""
    problems = []
    ids = all_ids(inventory)
    problems += [f'duplicate identifier {name}' for name in sorted({name for name in ids if ids.count(name) > 1})]
    for entry in inventory['entries']:
        if entry['kind'] not in KINDS:
            problems.append(f'{entry["id"]}: unknown admission kind {entry["kind"]!r}')
    referenced = {}
    for name, card in inventory['cards'].items():
        text = card['text']
        if not text.endswith('\n') or text.endswith('\n\n') or not text.strip():
            problems.append(f'card {name}: must end with exactly one newline')
        for reference in card['references']:
            if reference not in ids:
                problems.append(f'card {name}: references no entry: {reference}')
            referenced.setdefault(reference, []).append(name)
        supplied = card_tokens(inventory, name)
        for token in text.split():
            if token not in supplied:
                problems.append(f'card {name}: token {token!r} comes from no referenced entry')
    for record in [*inventory['entries'], *inventory['result']['rows'], inventory['example'],
                   {'id': 'result.fields', 'cards': inventory['result']['cards']}]:
        if sorted(record['cards']) != sorted(set(referenced.get(record['id'], []))):
            problems.append(f'{record["id"]}: its cards disagree with the cards that reference it')
    base = inventory['cards'].get('base', {}).get('text', '').split()
    topics = [entry['spellings'][0] for entry in inventory['entries'] if entry['id'].startswith('topic.')]
    if base != topics:
        problems.append('the base card does not list exactly the topic addresses, in order')
    problems += [f'topic address {address!r} is flag-shaped' for address in topics if address.startswith('-')]
    # Recompute the derived result facts from the rows.
    try:
        evaluated = relation(inventory)
    except ValueError as error:
        return problems + [str(error)]
    derived, names = inventory['result']['derived'], [field['name'] for field in inventory['result']['fields']]
    if derived['outputs'] != names:
        problems.append('result: derived outputs are not the result fields')
    tuples = [outputs for _, outputs in evaluated]
    for fact in derived['output_functions']:
        source, target = names.index(fact['of']), names.index(fact['output'])
        function = not any(first[source] == second[source] and first[target] != second[target]
                           for first in tuples for second in tuples)
        if function != fact['is_a_function']:
            problems.append(f'result: {fact["output"]} as a function of {fact["of"]} is recorded as {fact["is_a_function"]}; the rows give {function}')
        for witness in fact['counterexample'] or []:
            if witness not in tuples:
                problems.append(f'result: a recorded counterexample is not reachable from the rows: {witness}')
    shared = sorted(sorted([first, second]) for index, (first, outputs) in enumerate(evaluated)
                    for second, other in evaluated[index + 1:] if first != second and outputs == other)
    shared = [pair for index, pair in enumerate(shared) if pair not in shared[:index]]
    recorded = sorted(sorted(item['rows']) for item in derived['rows_sharing_outputs'])
    if shared != recorded:
        problems.append(f'result: rows sharing outputs are recorded as {recorded}; the rows give {shared}')
    return problems


def exercised(arguments, inventory):
    """The entries one argument vector reaches, derived from the spellings and rules the inventory records."""
    entries = {entry['id']: entry for entry in inventory['entries']}
    commands = {entry['spellings'][0]: entry for entry in entries.values() if entry['id'].startswith('command.')}
    if not arguments or not isinstance(arguments[0], str) or arguments[0] not in commands:
        return []
    command = commands[arguments[0]]
    reached, tail = [command['id']], arguments[1:]
    name = command['id'].split('.', 1)[1]
    rule = command['relationships']['tail']
    if rule == 'topic':
        topics = {entry['spellings'][0]: entry['id'] for entry in entries.values() if entry['id'].startswith('topic.')}
        if tail and isinstance(tail[0], str) and tail[0] in topics:
            reached.append(topics[tail[0]])
            tail = tail[1:]
        if tail:
            reached.append('tail.' + name)
    elif rule == 'run_arguments':
        options = {entry['spellings'][0]: entry for entry in entries.values() if entry['id'].startswith('run.option.')}
        prefix = entries['run.unknown_flag']['relationships']['flag_prefix']
        terminator = entries['run.terminator']['spellings'][0]
        index = 0
        while index < len(tail):
            argument = tail[index] if isinstance(tail[index], str) else '�'
            if argument == terminator:
                reached.append('run.terminator')
                break
            if not argument.startswith(prefix):
                reached.append('run.request_path')
                index += 1
                continue
            if argument not in options:
                reached.append('run.unknown_flag')
                break
            reached.append(options[argument]['id'])
            reader = options[argument]['relationships']['value'].get('runner_kind_reader')
            value = tail[index + 1] if index + 1 < len(tail) else None
            word = next((entry['id'] for entry in entries.values() if reader and isinstance(value, str)
                         and entry['id'].startswith('runner_kind.') and entry['id'].endswith('@' + reader)
                         and entry['spellings'] == [value]), None)
            if word:
                reached.append(word)
            index += 2
    elif rule == 'unenumerated' or tail:
        reached.append('tail.' + name)
    return list(dict.fromkeys(reached))


def content_entries(step, inventory):
    """Entries a step reaches through what it publishes or submits, not through an argument's spelling."""
    entries = {entry['id']: entry for entry in inventory['entries']}
    reached = exercised(step['args'], inventory)
    found = []
    # A successful `example` publishes the example document.
    if 'command.example' in reached and step.get('status') == 0:
        found.append(inventory['example']['id'])
    # A submitted request file's runner.mode is read by the request selector.
    for content in (step.get('files') or {}).values():
        try:
            mode = json.loads(content.replace('{contract}', 'c')).get('runner', {}).get('mode')
        except (ValueError, AttributeError):
            continue
        found += [name for name, entry in entries.items()
                  if name.startswith('runner_kind.') and name.endswith('@request_selector') and entry['spellings'] == [mode]]
    return found


def result_rows(expected, inventory):
    """The result rows whose outputs equal a case's required result fields."""
    names = [field['name'] for field in inventory['result']['fields']]
    required = expected.get('stdout_json') or {}
    if expected.get('stdout_json', {}).get('/kind') != 'run' or any('/result/' + name not in required for name in names):
        return []
    wanted = [required['/result/' + name] for name in names]
    evaluated = relation(inventory)
    listed = {outputs[0] for _, outputs in evaluated if isinstance(outputs[0], str)}
    # A label the relation spells nowhere can only be a retained host label.
    return list(dict.fromkeys(row for row, outputs in evaluated
                              if outputs == wanted or (outputs[0] == UNLISTED and wanted[0] not in listed
                                                       and outputs[1:] == wanted[1:])))


def joins(root, inventory):
    cases = read_json(root, CASES)['cases'] if (root / CASES).exists() else []
    mutations = read_json(root, MUTATIONS) if (root / MUTATIONS).exists() else {'mutations': [], 'declared_associations': []}
    ids = all_ids(inventory)
    problems, by_case = [], {}
    declared = {}
    for item in mutations.get('declared_associations', []):
        if item['entry'] not in ids:
            problems.append(f'declared association names no entry: {item["entry"]}')
        declared.setdefault(item['case'], []).append(item['entry'])
    for case in cases:
        steps = case.get('steps') or [case]
        reached, ambiguous = [], []
        for step in steps:
            reached += exercised(step['args'], inventory) + content_entries(step, inventory)
            rows = result_rows(step, inventory)
            if len(rows) == 1:
                reached += rows + ['result.fields']
            elif rows:
                ambiguous.append(rows)
        reached += declared.get(case['id'], [])
        by_case[case['id']] = {
            'entries': list(dict.fromkeys(reached)),
            'ambiguous_rows': ambiguous,
            'declared': declared.get(case['id'], []),
            'test_owned_inputs': any(step.get('files') or step.get('env') for step in steps),
        }
    for case in declared:
        if case not in by_case:
            problems.append(f'declared association names no case: {case}')
    reaching = {name: [case for case, value in by_case.items() if name in value['entries']] for name in ids}
    table = []
    for mutation in mutations.get('mutations', []):
        if mutation['entry'] not in ids:
            problems.append(f'mutation {mutation["id"]}: names no entry: {mutation["entry"]}')
        states = mutation['checks']
        if set(states) != set(CHECKS) or any(state not in STATES for state in states.values()):
            problems.append(f'mutation {mutation["id"]}: each of {CHECKS} takes one of {STATES}')
            continue
        moved = [name for name in CHECKS if states[name] in ('changed', 'failed')]
        table.append({'id': mutation['id'], 'entry': mutation['entry'], **states,
                      'not_run': [name for name in CHECKS if states[name] == 'not_run'],
                      'only_cases_moved': moved == ['cases']})
    report = {
        'cases': by_case,
        'entries_no_case_reaches': sorted(name for name, found in reaching.items() if not found),
        'entries_reached_only_with_test_owned_inputs': sorted(
            name for name, found in reaching.items() if found and all(by_case[case]['test_owned_inputs'] for case in found)),
        'mutations': table,
        'entries_no_mutation_names': sorted(set(ids) - {item['entry'] for item in table}),
    }
    return problems, report


def residue(inventory, report, expansions):
    """The residue classes, each as member identifiers with their count, and the recorded expansions."""
    def members(names):
        names = sorted(names)
        return {'count': len(names), 'members': names}
    non_admits = {}
    for entry in inventory['entries']:
        if entry['kind'] != 'admits':
            reader = entry['reader'].get('reader') or entry['reader']['symbol']
            non_admits.setdefault(entry['kind'], {}).setdefault(reader, []).append(entry['id'])
    uncarded = [record['id'] for record in [*inventory['entries'], *inventory['result']['rows'], inventory['example']]
                if not record['cards']]
    exceptions = [f'{name}:{item["role"]}:{item["token"]}' for name, card in inventory['cards'].items()
                  for item in card.get('token_exceptions', [])]
    return {
        'classes': {
            'non_admits': {kind: {reader: members(names) for reader, names in sorted(readers.items())}
                           for kind, readers in sorted(non_admits.items())},
            'referenced_by_no_card': members(uncarded),
            'reached_only_with_test_owned_inputs': members(report['entries_reached_only_with_test_owned_inputs']),
            'token_exceptions': members(exceptions),
        },
        'expansions': expansions,
    }


def flat(value, prefix=''):
    """Every (class path, member) pair of the residue classes."""
    if 'members' in value and 'count' in value:
        return {(prefix, member) for member in value['members']}
    return {pair for key, child in value.items() for pair in flat(child, f'{prefix}/{key}')}


def expanded(baseline, inventory, replaced, added):
    """The expansion records after `replaced`, an unenumerated entry of the baseline, gave way to enumerated ones."""
    ids = all_ids(inventory)
    kept = [item for item in (baseline or {}).get('expansions', []) if any(name in ids for name in item['exposed'])]
    if replaced is None:
        return kept
    opaque = {member for path, member in flat((baseline or {}).get('classes', {})) if path.startswith('/non_admits/unenumerated/')}
    if replaced not in opaque:
        raise ValueError(f'--expand names no unenumerated entry of the baseline: {replaced}')
    if replaced in ids:
        raise ValueError(f'--expand: {replaced} is still an inventory entry; expansion replaces it')
    exposed = sorted({member for _, member in added} | (set(ids) - set(baseline.get('identifiers', ids))))
    if not exposed:
        raise ValueError(f'--expand: no entry is new beside the removal of {replaced}')
    return kept + [{'replaced': replaced, 'exposed': exposed}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='write nothing; refuse a stale or inconsistent committed copy')
    parser.add_argument('--refresh-inventory', action='store_true',
                        help='replace the committed inventory from a build-script run before the rest')
    parser.add_argument('--refresh-residue', action='store_true', help='accept residue additions; review the diff of members and counts')
    parser.add_argument('--expand', metavar='ENTRY',
                        help='with --refresh-residue: the unenumerated entry whose path the new entries enumerate')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.check and (args.refresh_residue or args.refresh_inventory):
            raise ValueError('--check refreshes nothing')
        if args.expand and not args.refresh_residue:
            raise ValueError('--expand records an expansion during --refresh-residue')
        text = built_inventory(root) if args.refresh_inventory else (root / INVENTORY).read_text()
        inventory = json.loads(text)
        problems = validate(inventory)
        join_problems, report = joins(root, inventory)
        problems += join_problems
        if problems:
            raise ValueError('interface inventory:\n  ' + '\n  '.join(problems))
        baseline = read_json(root, RESIDUE) if (root / RESIDUE).exists() else None
        if baseline is None and not args.refresh_residue:
            raise ValueError(f'{RESIDUE} is missing; record it with --refresh-residue and review it')
        current = residue(inventory, report, (baseline or {}).get('expansions', []))
        added = sorted(flat(current['classes']) - flat(baseline['classes'])) if baseline is not None else []
        if added and not args.refresh_residue:
            raise ValueError('new residue members need --refresh-residue and a reviewed diff:\n  '
                             + '\n  '.join(f'{path}: {member}' for path, member in added))
        current['expansions'] = expanded(baseline, inventory, args.expand, added)
        current['identifiers'] = sorted(all_ids(inventory))
        values = {INVENTORY: text, JOINS: canonical(report), RESIDUE: canonical(current)}
        stale = [name for name, value in values.items() if not (root / name).exists() or (root / name).read_text() != value]
        if args.check:
            if stale:
                raise ValueError('stale: ' + ', '.join(stale) + f'; run tests/lib/python.sh {GENERATOR_NAME}')
        else:
            for name in stale:
                (root / name).write_text(values[name])
        print(f'ok: interface inventory: {len(all_ids(inventory))} identifiers, {len(inventory["cards"])} cards, '
              f'{len(report["cases"])} cases, {len(report["mutations"])} mutations; '
              + ('committed copies current' if args.check or not stale else 'wrote ' + ', '.join(stale)))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'interface: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
