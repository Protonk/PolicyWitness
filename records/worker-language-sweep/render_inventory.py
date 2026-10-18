"""Render the reconciled JSON as a readable record, without changing classifications."""
import collections
import json
from pathlib import Path

base = Path('records/worker-language-sweep')
data = json.loads((base / 'inventory.json').read_text())
out = ['# Worker language inventory', '',
       f"Frozen source revision: `{data['revision']}`.", '',
       'This is a descriptive classification of WORKER.md and its direct machinery. '
       'It does not assess truth or recommend wording changes. The summary and '
       'scope are in `report.md`; original collection and review remain in '
       '`first-inventory.json` and `trigger-review.json`. `inventory.json` is the '
       'complete machine-readable reconciled record.', '',
       'A1 states worker behavior, resources or constraints. B1 limits an inference; '
       'C2 has an identifiable trigger in WORKER.md and D2 has no identified local '
       'trigger. D2 origin status does not establish historical provenance.', '',
       'Counts are inventory units, with primary classes exclusive. C2 and D2 '
       'partition B1. Repeated resource-specific qualifications can occupy separate '
       'units; copied manifest/generated occurrences are linked within units.', '',
       '| Layer | A1 | B1 | C2 within B1 | D2 within B1 | Total |',
       '| --- | ---: | ---: | ---: | ---: | ---: |']

def counts(rows):
    c = collections.Counter(row['bucket'] for row in rows)
    s = collections.Counter(row['split'] for row in rows)
    return [c['A1'], c['B1'], s['C2'], s['D2'], len(rows)]

layers = [('worker_authored', 'WORKER authored'),
          ('worker_generated', 'WORKER generated'),
          ('repository', 'Direct supporting machinery')]
for layer, label in layers:
    rows = [row for row in data['entries'] if row['layer'] == layer]
    out.append('| ' + label + ' | ' + ' | '.join(map(str, counts(rows))) + ' |')
out.append('| Total | ' + ' | '.join(map(str, counts(data['entries']))) + ' |')

def ref(value):
    location = f"{value['path']}:{value['start_line']}"
    if value['end_line'] != value['start_line']:
        location += f"–{value['end_line']}"
    return f"[{location}](../../{value['path']})"

def quotation(text):
    # A fenced quotation keeps embedded relative links and table pipes literal.
    fence = '~~~~' if '```' in text else '```'
    return [fence + 'text', text, fence, '']

for bucket, split, title in [('A1', None, 'A1 — worker facts and constraints'),
                              ('B1', 'C2', 'B1 / C2 — guards with local triggers'),
                              ('B1', 'D2', 'B1 / D2 — guards without identified local triggers')]:
    out.extend(['', '## ' + title, ''])
    for layer, label in layers:
        rows = [row for row in data['entries'] if row['bucket'] == bucket and row['split'] == split and row['layer'] == layer]
        if not rows:
            continue
        out.extend(['### ' + label, ''])
        for row in rows:
            out.extend([f"#### {row['id']}", '',
                        f"{ref(row)} · {row['confidence']} confidence", ''])
            out.extend(quotation(row['quote']))
            out.extend([f"**Proposition:** {row['proposition']}", ''])
            if row['layer'] == 'worker_generated':
                out.extend(['**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.', ''])
            elif row['context'] != row['quote']:
                out.extend(['**Context:**', ''])
                out.extend(quotation(row['context']))
            out.extend([f"**Classification:** {row['rationale']}", ''])
            if row.get('partial_trigger_support'):
                out.extend(['**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.', ''])
            if row.get('scope_condition'):
                out.extend([f"**Scope condition:** {row['scope_condition']}", ''])
            for field, label2 in [('secondary_role', 'Secondary role'),
                                  ('inference_blocked', 'Blocked inference')]:
                if row.get(field):
                    out.extend([f"**{label2}:** {row[field]}", ''])
            if row.get('trigger'):
                t = row['trigger']
                out.extend([f"**Local trigger:** {ref(t)}", ''])
                out.extend(quotation(t['quote']))
                out.extend([t.get('rationale', ''), ''])
            for t in row.get('additional_triggers', []):
                out.extend([f"**Additional local trigger:** {ref(t)}", ''])
                out.extend(quotation(t['quote']))
                out.extend([t.get('rationale', ''), ''])
            if row.get('external_origin'):
                e = row['external_origin']
                out.extend([f"**External origin ({e['status']}):** {e['rationale']}", ''])
                for r in e.get('references', []):
                    out.extend([ref(r), ''])
                    out.extend(quotation(r['quote']))
            if row.get('duplicates'):
                out.extend(['**Associated occurrences:** ' + '; '.join(ref(r) for r in row['duplicates']) + '.', ''])
            if row.get('notes'):
                out.extend([f"**Notes:** {row['notes']}", ''])
if data.get('excluded_entries'):
    out.extend(['', '## Candidates excluded at scope review', '',
                'These remain visible for coverage and traceability; they are outside the primary bucket counts.', ''])
    for row in data['excluded_entries']:
        out.extend([f"### {row['id']}", '', ref(row), ''])
        out.extend(quotation(row['quote']))
        out.extend([row['exclusion_rationale'], ''])
(base / 'inventory.md').write_text('\n'.join(out).rstrip() + '\n')
