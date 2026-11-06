#!/usr/bin/env python3
"""Validate and render the footprint inventory. --check never writes."""
import argparse
import json
import re
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generator_common import citation, cited_paths, require_test, render_spans, format_value, DURATION_SIZE_RE, strings
import generate_limits
import markdown_reader

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = 'docs/footprint.json'
GENERATOR_NAME = 'docs/generate_footprint.py'
SPAN_DOCUMENTS = ('docs/FOOTPRINT.md',)
INPUTS = (GENERATOR_NAME, MANIFEST_NAME, 'docs/generator_common.py', 'docs/generate_limits.py',
          'docs/limits.json', 'docs/architecture.json', 'tests/catalog.json', *SPAN_DOCUMENTS)
CASES = {'waiting': 'Waiting and retained resources', 'response': 'Response storage and transport',
         'aftermath': 'State remaining after a run'}

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate key {key}')
        result[key] = value
    return result


def input_paths(root):
    root = Path(root)
    return sorted({*INPUTS, *markdown_reader.source_files(root), *cited_paths(root / MANIFEST_NAME),
                   *cited_paths(root / 'docs/limits.json')})


def fields(value, expected, owner):
    if not isinstance(value, dict) or set(value) != set(expected.split()):
        raise ValueError(f'{owner}: unexpected/missing fields')


def text(value, owner, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip() or '\n' in value:
        raise ValueError(f'{owner}: expected nonempty single-line text')


def load_manifest(path, root=ROOT):
    root = Path(root)
    data = json.loads(Path(path).read_text(), object_pairs_hook=unique_object)
    fields(data, 'schema_version document rows', 'manifest')
    if type(data['schema_version']) is not int or data['schema_version'] != 1 or data['document'] != 'docs/FOOTPRINT.md':
        raise ValueError('expected footprint schema_version 1 and registered document')
    limits = {r['id'] for r in generate_limits.load_limits(root / 'docs/limits.json', root)}
    if not isinstance(data['rows'], list) or not data['rows']:
        raise ValueError('rows must be nonempty')
    architecture = json.loads((root / 'docs/architecture.json').read_text(), object_pairs_hook=unique_object)
    nodes = {(g['id'], n['id']): n for g in architecture['graphs'] if g['id'].startswith('footprint_') for n in g['nodes']}
    used, ids = set(), set()
    for row in data['rows']:
        fields(row, 'id case title subject quantity conditions interval aftermath sources checks figure', 'row')
        ident = row['id']
        if not isinstance(ident, str) or not re.fullmatch('f[wra][1-9][0-9]*', ident) or ident in ids:
            raise ValueError('invalid/duplicate row id')
        ids.add(ident)
        if row['case'] not in CASES or ident[1] != {'waiting':'w','response':'r','aftermath':'a'}[row['case']]:
            raise ValueError(f'{ident}: invalid case')
        for key in ('title', 'conditions'):
            text(row[key], ident + '.' + key)
        fields(row['subject'], 'kind owner backing', ident)
        if row['subject']['kind'] not in {'mapping','allocation','descriptor','process','registry','file','activity'}:
            raise ValueError(f'{ident}: invalid subject kind')
        text(row['subject']['owner'], ident)
        text(row['subject']['backing'], ident, True)
        q = row['quantity']
        fields(q, 'evidence value unit limit behavior', ident)
        if q['evidence'] not in {'measured','logical','constructed','source'}:
            raise ValueError(f'{ident}: invalid evidence')
        if q['value'] is not None:
            if type(q['value']) not in (int,float) or q['value'] < 0 or not __import__('math').isfinite(q['value']):
                raise ValueError(f'{ident}: invalid quantity')
            text(q['unit'], ident)
        elif q['unit'] is not None:
            raise ValueError(f'{ident}: unit without value')
        if q['limit'] is not None and q['limit'] not in limits:
            raise ValueError(f'{ident}: unknown limit')
        text(q['behavior'], ident, True)
        if all(q[k] is None for k in ('value','limit','behavior')) or (q['value'] is not None and q['limit'] is not None):
            raise ValueError(f'{ident}: ambiguous/missing quantity')
        if q['evidence'] != 'source' and q['value'] is None and q['limit'] is None:
            raise ValueError(f'{ident}: quantity evidence needs value or limit')
        fields(row['interval'], 'starts ends ending_event', ident)
        for value in row['interval'].values():
            text(value, ident, True)
        a = row['aftermath']
        if a is not None:
            fields(a, 'at_cli_return expected_ending', ident)
            if a['at_cli_return'] not in {'present','absence_confirmed','unknown'}:
                raise ValueError(f'{ident}: invalid aftermath state')
            text(a['expected_ending'], ident, True)
        if row['case'] == 'aftermath' and a is None:
            raise ValueError(f'{ident}: aftermath state required')
        for group in ('sources','checks'):
            refs = row[group]
            if not isinstance(refs,list) or not refs:
                raise ValueError(f'{ident}: empty {group}')
            for ref in refs:
                fields(ref, 'path symbol' if group == 'sources' else 'path symbol kind form pins', ident)
                if group == 'checks':
                    if ref['kind'] not in {'assertion','receipt','value'}:
                        raise ValueError(f'{ident}: unknown check kind')
                    text(ref['pins'], ident)
                citation(ref, root, check=group == 'checks', forbidden=(MANIFEST_NAME,GENERATOR_NAME,data['document']))
        require_test(ident, row['checks'])
        for value in strings({k:v for k,v in row.items() if k != 'quantity'}):
            if DURATION_SIZE_RE.search(value):
                raise ValueError(f'{ident}: literal quantity outside quantity')
        f = row['figure']
        if f is not None:
            fields(f, 'graph node', ident)
            key = (f['graph'], f['node'])
            if key not in nodes or key in used or f['node'] != ident:
                raise ValueError(f'{ident}: invalid/duplicate figure correspondence')
            used.add(key)
    if used != set(nodes):
        raise ValueError('footprint figure nodes must correspond to rows in both directions')
    return data


def cell(value):
    return str(value if value is not None else 'Unestablished').replace('|', '&#124;').replace('\n',' ')


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                     ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows])


def reference(ref):
    return f"[`{ref['symbol']}`](../{ref['path']})"


def quantity(row):
    q = row['quantity']
    parts = []
    if q['value'] is not None:
        parts.append(format_value(q['value'], q['unit']))
    if q['limit'] is not None:
        parts.append(f"[LIMITS `{q['limit']}`](LIMITS.md)")
    if q['behavior']:
        parts.append(q['behavior'])
    return f"{q['evidence']}: " + ' '.join(parts)


def span_values(data):
    result = {}
    for row in data['rows']:
        for key,value in row['quantity'].items():
            if value is not None:
                result[f"{row['id']}.{key}"] = str(value)
        result[f"{row['id']}.quantity"] = quantity(row)
    return result


def replace_block(content, name, body):
    start, end = f'<!-- BEGIN GENERATED FOOTPRINT {name} -->', f'<!-- END GENERATED FOOTPRINT {name} -->'
    if content.count(start) != 1 or content.count(end) != 1 or content.index(start) >= content.index(end):
        raise ValueError(f'expected exactly one ordered block: {name}')
    a, b = content.index(start) + len(start), content.index(end)
    return content[:a] + '\n\n' + body + '\n\n' + content[b:]


def render_document(content, data):
    for case in CASES:
        rows = []
        for r in data['rows']:
            if r['case'] != case:
                continue
            i = r['interval']
            rows.append([r['id'], r['title'] + ' — ' + r['subject']['owner'], quantity(r), r['conditions'],
                         f"{i['starts'] or 'Unestablished'} → {i['ends'] or 'Unestablished'}",
                         r['aftermath']['at_cli_return'].replace('_',' ') if r['aftermath'] else '—'])
        content = replace_block(content, case.upper(), table(['ID','Resource / owner','Quantity / mechanism','Conditions','Interval','At CLI return'], rows))
    groups = {}
    for r in data['rows']:
        if r['subject']['backing'] is not None:
            groups.setdefault(r['subject']['backing'], []).append(r)
    content = replace_block(content, 'BACKING', table(['Backing','Views / owners'],
        [[k, '; '.join(r['id'] + ': ' + r['subject']['owner'] for r in v)] for k,v in groups.items()]) if groups else 'No backing identity established by these rows; no sum across views is implied.')
    groups = {}
    for r in data['rows']:
        groups.setdefault(r['interval']['ending_event'] or 'Unestablished', []).append(r['id'])
    content = replace_block(content, 'ENDINGS', table(['Ending event','Rows'], [[k, ', '.join(v)] for k,v in groups.items()]))
    content = replace_block(content, 'COVERAGE', table(['Row','Sources','Check / scope'],
        [[r['id'], '; '.join(reference(s) for s in r['sources']), '; '.join(reference(c) + f" ({c['kind']}): " + c['pins'] for c in r['checks'])] for r in data['rows']]))
    return render_spans(content, 'footprint', span_values(data), data['document'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        data = load_manifest(ROOT / MANIFEST_NAME)
        path = ROOT / data['document']
        old = path.read_text()
        new = render_document(old, data)
        if args.check and old != new:
            raise ValueError('stale footprint document; run docs/generate_footprint.py')
        if not args.check and old != new:
            path.write_text(new)
        print('ok: footprint manifest and generated document')
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'footprint: {error}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
