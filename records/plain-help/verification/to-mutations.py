#!/usr/bin/env python3
"""Convert the harness observations into the retained mutation record.

usage: to-mutations.py OBSERVED.json MUTATIONS.json
"""
import json
import sys

observed = json.load(open(sys.argv[1]))
record = json.load(open(sys.argv[2]))
mutations = []
for item in observed['mutations']:
    seen = item['observed']
    first = seen['build']['result']
    regenerated = seen.get('regenerated', {})
    usable = 'cards' in seen
    generator_refused = regenerated.get('result') == 'refused'
    if usable:
        card = 'changed' if item['cards_changed'] else 'unchanged'
    elif first == 'card_validation' or generator_refused:
        card = 'failed'
    else:
        card = 'not_run'
    contract = 'failed' if seen['contract']['result'] != 'ok' else 'unchanged'
    if usable:
        moved = item['cases_newly_failing'] or seen['cases']['agreement'] != 'ok'
        cases = 'failed' if moved else 'unchanged'
    else:
        cases = 'not_run'
    entry = {
        'id': item['id'], 'entry': item['entry'], 'mutation': item['mutation'], 'patch': item['patch'],
        'checks': {'card': card, 'contract': contract, 'cases': cases},
        'first_build': first if first != 'ok' else 'built',
        'first_build_message': seen['build']['message'],
        'literal_rule': 'failed' if seen['literals']['result'] != 'ok' else 'unchanged',
    }
    if generator_refused:
        entry['generator_refusal'] = regenerated['message'].split('\n')[-1].strip()
    if 'generator_without_refresh' in seen:
        entry['residue_without_refresh'] = seen['generator_without_refresh']['result']
    if seen['contract']['result'] != 'ok':
        entry['contract_refusal'] = seen['contract']['message'][:400]
    if usable:
        entry['cards_changed'] = item['cards_changed']
        entry['cases_newly_failing'] = item['cases_newly_failing']
        entry['card_execution_agreement'] = seen['cases']['agreement']
        entry['unit_tests_newly_failing'] = item['unit_newly_failing']
    mutations.append(entry)
record['mutations'] = mutations
record['observed_on'] = {'commit': observed['head'], 'build': 'unsigned debug build in a scratch app directory',
                         'baseline_cases_failing': observed['baseline']['cases']['failing']}
json.dump(record, open(sys.argv[2], 'w'), indent=2)
open(sys.argv[2], 'a').write('\n')
print(len(mutations), 'mutations')
