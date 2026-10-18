"""Apply reviewed descriptive classifications while preserving original artifacts."""
import collections
import copy
import json
from pathlib import Path

base = Path('records/worker-language-sweep')
first = json.loads((base / 'first-inventory.json').read_text())
followup = json.loads((base / 'coverage-followup.json').read_text())
review = json.loads((base / 'trigger-review.json').read_text())
decisions = {d['id']: d for d in review['decisions']}
overrides_path = base / 'coordinator-overrides.json'
overrides = json.loads(overrides_path.read_text())['decisions'] if overrides_path.exists() else []
for override in overrides:
    decisions[override['id']] = {**decisions.get(override['id'], {}), **override}

final = copy.deepcopy(first)
final['classification_stage'] = 'coordinator reconciliation after independent trigger review'
final['scope']['uncertainty'] = [
    'C2 identifies a specific plausible local invitation, not a logically valid inference or established reader response.',
    'D2 means no sufficiently specific local trigger was identified; it does not establish external historical origin or redundancy.',
    'Mixed cells retain secondary roles or review notes. An exact trigger for one named inference does not establish every possible inference from that cell.',
    'Counts represent statement/cell occurrences, not unique claim families or documentation quality.',
    'Pure issuer housekeeping without a worker proposition is excluded rather than forced into A1 or B1.'
]
final['scope']['execution'] = 'Static source, quotation, coverage and classification review. No build, runtime test or generator execution; only sweep records and associated plan status changed.'
final['entries'] = []
final['excluded_entries'] = []
resolutions = []
for original in first['entries'] + followup['entries']:
    row = copy.deepcopy(original)
    decision = decisions.get(row['id'])
    if decision:
        if decision.get('excluded'):
            final['excluded_entries'].append({**row, 'exclusion_rationale': decision['rationale']})
            resolutions.append({'id': row['id'], 'action': 'exclude', 'reason': decision['rationale'],
                                'original_bucket': row['bucket'], 'original_split': row['split']})
            continue
        old_class = (row['bucket'], row['split'])
        row['bucket'] = decision['bucket']
        row['split'] = decision['split']
        row['confidence'] = decision['confidence']
        row['rationale'] = decision['rationale']
        for field in ('proposition', 'inference_blocked', 'secondary_role'):
            if field in decision:
                row[field] = decision[field]
        for field in ('scope_condition', 'partial_trigger_support', 'split_recommended', 'additional_triggers'):
            if field in decision:
                row[field] = copy.deepcopy(decision[field])
        if row['bucket'] == 'A1':
            row['trigger'] = row['external_origin'] = row['inference_blocked'] = None
            if original['bucket'] != 'A1' and 'secondary_role' not in decision:
                row['secondary_role'] = None
        elif row['split'] == 'C2':
            row['trigger'] = copy.deepcopy(decision['trigger'])
        else:
            row['trigger'] = None
            if isinstance(decision.get('external_origin'), dict):
                row['external_origin'] = copy.deepcopy(decision['external_origin'])
            elif decision.get('external_origin'):
                row['external_origin'] = {'status': 'unknown', 'references': [],
                    'rationale': decision['external_origin']}
            elif not row['external_origin']:
                row['external_origin'] = {'status': 'unknown', 'references': [],
                    'rationale': 'No sufficiently specific independent WORKER trigger was identified in review. External historical origin is unknown. ' + decision['rationale']}
        row['notes'] += f" Independent review: {decision['assessment']}; see trigger-review.json by ID."
        changes = [field for field in ('bucket', 'split', 'confidence', 'trigger', 'inference_blocked', 'secondary_role')
                   if row.get(field) != original.get(field)]
        if changes:
            resolutions.append({'id': row['id'], 'action': 'revise', 'fields': changes,
                'original_bucket': original['bucket'], 'original_split': original['split'],
                'final_bucket': row['bucket'], 'final_split': row['split'], 'reason': decision['rationale']})
    if original['id'].startswith('F'):
        resolutions.append({'id': row['id'], 'action': 'include_followup',
                            'reason': 'Coverage follow-up occurrence, retained after scope review.'})
    final['entries'].append(row)

final['coverage'].append({'path_or_group': 'Worker capability graph mechanical candidate cross-check',
    'method': 'search and contextual review',
    'notes': '243 candidate cells resolved by exact owning manifest references and the separate coverage follow-up. This is a coverage aid, not proof of semantic completeness.'})
final['review'] = {'reviewed_ids': review['reviewed_ids'],
                  'coverage_notes': review['coverage_notes'], 'omissions': review['omissions']}
(base / 'inventory.json').write_text(json.dumps(final, indent=2) + '\n')
record = {'revision': first['revision'],
          'method': 'Coordinator reviewed independent decisions and preserves first/follow-up/reviewer artifacts unchanged. Any coordinator overrides are recorded separately.',
          'resolutions': resolutions}
(base / 'reconciliation.json').write_text(json.dumps(record, indent=2) + '\n')
counts = collections.Counter((r['layer'], r['bucket'], r['split']) for r in final['entries'])
print(json.dumps({'included': len(final['entries']), 'excluded': len(final['excluded_entries']),
                  'counts': {':'.join(str(v) for v in k): n for k,n in sorted(counts.items())},
                  'resolutions': len(resolutions)}, indent=2))
