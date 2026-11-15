"""No literal spelling match beside the interface tables.

The interface inventory names the code that reads each governing table. In
those functions a string or character literal may not be compared, matched or
searched for: every spelling a governed path recognizes is a definition in
`controller/src/interface/`. The card renderer may hold no literal equal to a
card token or line. A word the runner-kind table resolves as an alias may not
be written anywhere else in the controller's non-test source.

This is a mechanical source convention over a token scan, not Rust semantic
analysis. A comparison built without a literal token, such as one against a
constant defined outside the tables, is outside it.
"""
from pathlib import Path
import re

TABLES = 'controller/src/interface/'
SOURCE = 'controller/src'
RENDERER = 'controller/interface/cards.rs'
# The help dispatcher reads the stored cards by topic; it is governed with the readers the inventory names.
EXTRA_READERS = (('controller/src/help.rs', 'pub fn card'), ('controller/src/help.rs', 'pub fn cmd_help'))
COMPARING_CALLS = {'starts_with', 'ends_with', 'contains', 'strip_prefix', 'strip_suffix', 'eq', 'ne', 'find',
                   'eq_ignore_ascii_case', 'matches', 'split_once', 'trim_start_matches'}
TOKEN = re.compile(r'''
    (?P<raw>b?r(?P<hashes>\#*)"(?:.|\n)*?"(?P=hashes))
  | (?P<string>b?"(?:\\(?:.|\n)|[^"\\])*")
  | (?P<char>b?'(?:\\[^'\n]+|[^'\\\n])')
  | (?P<lifetime>'[A-Za-z_][A-Za-z0-9_]*)
  | (?P<word>[A-Za-z_][A-Za-z0-9_]*!?)
  | (?P<operator>==|!=|=>|->|::|&&|\|\||[{}()\[\]|,;=<>.&:!?+\-*/%@#^~$])
  | (?P<number>[0-9][A-Za-z0-9_.]*)
''', re.X)


def tokens(text):
    """(kind, text, offset) for every token outside whitespace and comments; block comments nest."""
    out, index = [], 0
    while index < len(text):
        if text[index].isspace():
            index += 1
        elif text.startswith('//', index):
            end = text.find('\n', index)
            index = len(text) if end < 0 else end
        elif text.startswith('/*', index):
            depth, index = 1, index + 2
            while depth and index < len(text):
                if text.startswith('/*', index):
                    depth, index = depth + 1, index + 2
                elif text.startswith('*/', index):
                    depth, index = depth - 1, index + 2
                else:
                    index += 1
        else:
            match = TOKEN.match(text, index)
            if not match:
                raise ValueError(f'unreadable Rust source at offset {index}: {text[index:index + 30]!r}')
            out.append((match.lastgroup, match[0], index))
            index = match.end()
    return out


def body(text, symbol):
    """The tokens of the braced block that follows the one occurrence of `symbol`."""
    if text.count(symbol) != 1:
        raise ValueError(f'expected one occurrence of {symbol!r}, found {text.count(symbol)}')
    stream = [token for token in tokens(text) if token[2] >= text.index(symbol)]
    start = next(i for i, token in enumerate(stream) if token[1] == '{')
    depth = 0
    for index in range(start, len(stream)):
        depth += {'{': 1, '}': -1}.get(stream[index][1], 0)
        if depth == 0:
            return stream[start:index + 1]
    raise ValueError(f'unbalanced block after {symbol!r}')


def compared_literals(stream):
    """Literal tokens in a comparing position: (text, offset, reason)."""
    found = []
    for index, (kind, text, offset) in enumerate(stream):
        if kind not in ('string', 'raw', 'char'):
            continue
        before = [token[1] for token in stream[max(0, index - 3):index]]
        after = [token[1] for token in stream[index + 1:index + 6]]
        closing = [item for item in after if item != ')']
        reason = None
        if before[-1:] in (['=='], ['!=']) or after[:1] in (['=='], ['!=']):
            reason = 'compared with a literal'
        elif closing[:1] in (['=>'], ['|']) or before[-1:] == ['|'] or before[-1:] == ['let']:
            reason = 'matched against a literal pattern'
        elif len(before) >= 2 and before[-1] == '(' and before[-2].rstrip('!') in COMPARING_CALLS:
            reason = f'{before[-2]} on a literal'
        if reason is None:
            # A literal anywhere inside matches!(...) is a pattern.
            depth = 0
            for back in range(index - 1, -1, -1):
                depth += {')': 1, '(': -1}.get(stream[back][1], 0)
                if depth < 0:
                    if back and stream[back - 1][1] == 'matches!':
                        reason = 'matched against a literal pattern'
                    break
        if reason:
            found.append((text, offset, reason))
    return found


def non_test(text):
    """The source before its unit-test module."""
    match = re.search(r'^#\[cfg\(test\)\]\s*\nmod ', text, re.M)
    return text[:match.start()] if match else text


def readers(inventory):
    cited = {(entry['reader']['path'], entry['reader']['symbol']) for entry in inventory['entries']}
    cited.add((inventory['result']['reader']['path'], inventory['result']['reader']['symbol']))
    return sorted((path, symbol) for path, symbol in cited | set(EXTRA_READERS) if not path.startswith(TABLES))


def findings(root, inventory):
    """(path, line, message) for every literal the convention refuses under `root`."""
    root = Path(root)
    found = []
    for path, symbol in readers(inventory):
        text = (root / path).read_text()
        try:
            stream = body(non_test(text), symbol)
        except (ValueError, StopIteration) as error:
            found.append((path, None, f'{path}: cannot read the governed block {symbol!r}: {error}'))
            continue
        for literal, offset, reason in compared_literals(stream):
            line = text.count('\n', 0, offset) + 1
            found.append((path, line, f'{path}:{line}: {symbol}: {reason}: {literal}; define the spelling in {TABLES}'))
    # The card renderer holds no text of its own: none of its literals is a card token or a card line.
    printed = {token for card in inventory['cards'].values() for token in card['text'].split()}
    printed |= {line.strip() for card in inventory['cards'].values() for line in card['text'].splitlines()}
    text = (root / RENDERER).read_text()
    for kind, literal, offset in tokens(text):
        if kind in ('string', 'raw') and literal[literal.index('"') + 1:literal.rindex('"')] in printed:
            line = text.count('\n', 0, offset) + 1
            found.append((RENDERER, line, f'{RENDERER}:{line}: the card renderer spells a card element itself: {literal}'))
    # A word the runner-kind table gives some reader a rule other than plain admission is spelled in the tables only.
    restricted = sorted({spelling for entry in inventory['entries']
                         if entry['id'].startswith('runner_kind.') and entry['kind'] != 'admits'
                         for spelling in entry['spellings']})
    for source in sorted((root / SOURCE).rglob('*.rs')):
        relative = source.relative_to(root).as_posix()
        if relative.startswith(TABLES):
            continue
        text = non_test(source.read_text())
        for kind, literal, offset in tokens(text):
            if kind in ('string', 'raw') and any(
                    re.search(r'(?<![A-Za-z0-9_])' + re.escape(word) + r'(?![A-Za-z0-9_])', literal) for word in restricted):
                line = text.count('\n', 0, offset) + 1
                found.append((relative, line, f'{relative}:{line}: a literal spells a word the runner-kind table aliases: {literal}'))
    return found
