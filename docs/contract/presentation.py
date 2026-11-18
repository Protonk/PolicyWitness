"""Explicit document placement, outside canonical public meaning."""
import json
from pathlib import Path
import re

import markdown_reader
import tree as model

MAP = 'docs/contract/presentation.json'
CONTRACT = 'docs/CONTRACT.md'
GUIDE = 'docs/PolicyWitness.md'
INTRO = 'docs/contract/trace-introduction.md'


def markers(region):
    return (f'<!-- BEGIN GENERATED CONTRACT {region} -->',
            f'<!-- END GENERATED CONTRACT {region} -->')


def load(root, tree):
    data = json.loads((root / MAP).read_text())
    if set(data) != {'documents', 'commitments'}:
        raise ValueError('presentation map requires documents and commitments')
    expected = {n.id for n in tree.nodes if n.kind == 'surface' or
                (n.kind == 'subject' and n.parent.kind == 'surface')}
    seen, regions, homes = set(), set(), {}
    for document, entries in data['documents'].items():
        if Path(document).parent.as_posix() != 'docs' or not document.endswith('.md') or document == GUIDE:
            raise ValueError(f'invalid statement destination: {document}')
        for entry in entries:
            if set(entry) != {'region', 'nodes'} or not re.fullmatch(r'[a-z][a-z0-9_]*', entry['region']):
                raise ValueError('invalid statement region')
            key = document, entry['region']
            if key in regions:
                raise ValueError(f'duplicate region: {key}')
            regions.add(key)
            for ident in entry['nodes']:
                if ident not in expected or ident in seen:
                    raise ValueError(f'unknown or duplicate routing unit: {ident}')
                seen.add(ident)
                node = tree.index[ident]
                members = [node, *(n for n in node.descendants()
                                  if node.kind != 'surface' or
                                  not any(p.kind == 'subject' for p in ancestors(n, node)))]
                for member in members:
                    if member.id in homes:
                        raise ValueError(f'conflicting destination: {member.id}')
                    homes[member.id] = document
    if seen != expected:
        raise ValueError('unrouted units: ' + ', '.join(sorted(expected - seen)))
    if set(homes) != set(tree.index):
        raise ValueError('presentation omits public nodes or support')
    for entry in data['commitments']:
        if set(entry) != {'document', 'region', 'nodes'}:
            raise ValueError('invalid commitment list')
        if entry['document'] not in {'docs/ARCHITECTURE.md', 'docs/CONTROLLER.md', 'docs/WORKER.md', 'docs/BUILD.md'}:
            raise ValueError('invalid commitment-list destination')
        key = entry['document'], entry['region']
        if key in regions or not re.fullmatch(r'[a-z][a-z0-9_]*', entry['region']):
            raise ValueError(f'duplicate or invalid region: {key}')
        regions.add(key)
        if not entry['nodes'] or len(set(entry['nodes'])) != len(entry['nodes']):
            raise ValueError('empty or duplicate commitment list')
        for ident in entry['nodes']:
            if ident not in tree.index or tree.index[ident].kind not in {'subject', *model.RULE_KINDS}:
                raise ValueError(f'unknown commitment: {ident}')
    return data, homes


def ancestors(node, stop):
    while node is not stop:
        yield node
        node = node.parent


def destinations(root):
    """Lenient discovery; load validates the map before any writes."""
    data = json.loads((root / MAP).read_text())
    return {*data['documents'], *(e['document'] for e in data['commitments'])}


def documents(root):
    """Markdown documents directly under docs/, which render reads for region markers outside the map."""
    return sorted(path.relative_to(root).as_posix() for path in (root / 'docs').glob('*.md'))


def rebase(text, document, homes):
    anchors = {'contract-' + ident.replace('.', '-'): home for ident, home in homes.items()}
    anchors.update({'contract-' + ident.replace('.', '-') + '-details': CONTRACT for ident in homes})
    anchors.update({'contract-notation': CONTRACT, 'contract-support-grades': CONTRACT})
    parsed = markdown_reader.parse(text, document)
    replacements = {}
    for link in parsed.links:
        path, separator, anchor = link.target.partition('#')
        if separator and anchor.startswith('contract-') and path in ('', 'CONTRACT.md', './CONTRACT.md'):
            if anchor not in anchors:
                raise ValueError(f'{document}: unknown contract link {link.target}')
            target = ('' if anchors[anchor] == document else Path(anchors[anchor]).name) + '#' + anchor
            replacements[link.target] = target
    # The Markdown reader identifies actual links and reference definitions.
    # Preserve code examples, destination brackets and optional link titles.
    lines = text.splitlines(keepends=True)
    pattern = re.compile(r'(`+)(?!`)(.*?)(?<!`)\1(?!`)|\]\(\s*(<)?([^\s)>]+)(?(3)>)', re.DOTALL)

    def replace_target(match, group):
        start, end = match.span(group)
        return (match.string[match.start():start] +
                replacements.get(match.group(group), match.group(group)) +
                match.string[end:match.end()])

    for start, end in sorted({link.inline.lines for link in parsed.links}, reverse=True):
        body = ''.join(lines[start:end])
        body = pattern.sub(lambda m: m.group(0) if m.group(1) else replace_target(m, 4), body)
        lines[start:end] = body.splitlines(keepends=True)
    reference = re.compile(r'\]:\s*(<)?([^\s>]+)(?(1)>)')
    for value in parsed.references.values():
        if value['href'] in replacements:
            start, end = value['map']
            body = reference.sub(lambda m: replace_target(m, 2), ''.join(lines[start:end]), count=1)
            lines[start:end] = body.splitlines(keepends=True)
    return ''.join(lines)


def replace_region(text, document, region, body):
    begin, end = markers(region)
    if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) >= text.index(end):
        raise ValueError(f'{document}: expected one ordered contract region {region}')
    a = text.index(begin) + len(begin)
    b = text.index(end)
    return text[:a] + '\n' + body.rstrip() + '\n' + text[b:]


def indexes(tree, data, homes):
    lines = ['## Find a commitment', '', '| Identity | Complete statement |', '| --- | --- |']
    units = [tree.index[ident] for entries in data['documents'].values()
             for entry in entries for ident in entry['nodes'] if tree.index[ident].kind == 'subject']
    for node in units:
        lines.append(f'| `{node.id}` | {model._link(node)} |')
    lines += ['', '## Follow a changed item', '',
              'Declarations own meaning; source and check citations supply the stated support. '
              'A file association identifies candidates for review, not every behavior that file can affect.', '',
              '| Changed item | Relationship | Candidate commitment |', '| --- | --- | --- |']
    rows = set()
    for node in units:
        rows.add((node.source, 'authored declaration', node.id))
    for node in tree.nodes:
        if node.kind == 'owner':
            for kind in ('source', 'check'):
                values = node.facts.get(kind, [])
                for value in values if isinstance(values, list) else [values]:
                    rows.add((value['path'] + ': ' + value['symbol'], kind + ' support', node.parent.id))
        if node.record:
            rows.add((node.record, 'imported record declaration', node.id))
        for ident in node.facts.get('interface', []):
            rows.add((ident, 'interface association; see the partial join', node.id))
        if 'document' in node.facts:
            value = node.facts['document']
            rows.add((value['path'] + ': ' + value['symbol'], 'extracted example', node.id))
    for item, kind, ident in sorted(rows):
        lines.append('| ' + model._cell('`' + item + '`') + ' | ' + kind + ' | ' + model._link(tree.index[ident]) + ' |')
    return '\n'.join(lines) + '\n'


def render(root, tree):
    data, homes = load(root, tree)
    # An obsolete marker must not keep an old statement alive outside the
    # declared region inventory. Validate every destination before assembly.
    expected = {document: {e['region'] for e in entries}
                for document, entries in data['documents'].items() if document != CONTRACT}
    for entry in data['commitments']:
        expected.setdefault(entry['document'], set()).add(entry['region'])
    for document, regions in expected.items():
        text = (root / document).read_text()
        begins = re.findall(r'<!-- BEGIN GENERATED CONTRACT ([a-z][a-z0-9_]*) -->', text)
        ends = re.findall(r'<!-- END GENERATED CONTRACT ([a-z][a-z0-9_]*) -->', text)
        if set(begins) != regions or set(ends) != regions or len(begins) != len(regions) or len(ends) != len(regions):
            raise ValueError(f'{document}: expected one ordered contract region for each declared entry; orphaned or missing region')
        # Replacing an enclosing region would erase the markers of the region inside it.
        opened = None
        for kind, region in re.findall(r'<!-- (BEGIN|END) GENERATED CONTRACT ([a-z][a-z0-9_]*) -->', text):
            if kind == 'BEGIN' and opened:
                raise ValueError(f'{document}: contract region {region} begins inside contract region {opened}; '
                                 'declared regions must not overlap')
            if kind == 'END' and region != opened:
                raise ValueError(f'{document}: expected one ordered contract region {region}')
            opened = region if kind == 'BEGIN' else None
    for document in documents(root):
        if document not in expected and document not in data['documents']:
            found = re.findall(r'<!-- (?:BEGIN|END) GENERATED CONTRACT ([a-z][a-z0-9_]*) -->', (root / document).read_text())
            if found:
                raise ValueError(f'{document}: contract region markers in a document the presentation map does not name: ' +
                                 ', '.join(sorted(set(found))))
    values = {}
    for document, entries in data['documents'].items():
        text = (root / document).read_text() if document != CONTRACT else (root / INTRO).read_text().rstrip() + '\n\n'
        for entry in entries:
            nodes = [tree.index[ident] for ident in entry['nodes']]
            body = model.render(tree, nodes, appendix=False, title=False)
            inherited = []
            for node in nodes:
                if node.kind == 'subject' and homes[node.parent.id] != document:
                    for owner in node.parent.children:
                        if owner.kind == 'owner' and owner.facts.get('scope') == 'subtree':
                            notice = ('Inherited surface support: ' + model._link(owner) +
                                      ' (original subtree scope).')
                            if notice not in inherited:
                                inherited.append(notice)
            body = '\n\n'.join([*inherited, body])
            body = rebase(body, document, homes)
            if document == CONTRACT:
                begin, end = markers(entry['region'])
                text += begin + '\n' + body.rstrip() + '\n' + end + '\n\n'
            else:
                text = replace_region(text, document, entry['region'], body)
        if document == CONTRACT:
            text += '<!-- CONTRACT SURFACE TABLE -->\n\n'
            text += rebase(indexes(tree, data, homes), document, homes) + '\n'
            text += rebase(model.render(tree, [], title=False), document, homes)
        values[document] = text
    for entry in data['commitments']:
        document = entry['document']
        text = values.get(document, (root / document).read_text())
        body = 'Commitments explained here:\n\n' + '\n'.join(
            '- ' + model._link(tree.index[ident]) + ' (`' + ident + '`).' for ident in entry['nodes'])
        values[document] = replace_region(text, document, entry['region'], rebase(body, document, homes))
    return values


def ownership(root):
    data = json.loads((root / MAP).read_text())
    regions = {GUIDE: [('<!-- BEGIN GENERATED CONTRACT STAMPS -->', '<!-- END GENERATED CONTRACT STAMPS -->')]}
    for document, entries in data['documents'].items():
        if document != CONTRACT:
            regions[document] = [markers(entry['region']) for entry in entries]
    for entry in data['commitments']:
        regions.setdefault(entry['document'], []).append(markers(entry['region']))
    return regions, {CONTRACT}
