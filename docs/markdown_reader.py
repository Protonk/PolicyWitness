"""Markdown structure, read through the vendored CommonMark parser.

This is the only module that imports markdown-it-py and mdurl. It parses with
one fixed configuration and reports what the parser found: blocks and their
lines, headings and their anchors, sections, links, inline code, list items,
table cells and fenced blocks. Callers keep their own policy; nothing here
reads Markdown structure from the text with patterns.

Lines are zero-based and ranges are half-open, as the parser reports them.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / 'tests/lib/vendor'
VERSION = '3.0.0'


class Refused(ValueError):
    """Input the pinned parser reads differently from GitHub."""


def _parser():
    """The configured parser, imported only from the vendored copies."""
    # markdown-it-py 3.0.0 imports linkify_it whenever it can and constructs it
    # whatever the configuration. A None entry makes that import fail everywhere.
    if sys.modules.get('linkify_it') is not None:
        raise ImportError('linkify_it is already imported; markdown-it-py would construct it')
    sys.modules['linkify_it'] = None
    for name in ('markdown_it', 'mdurl'):
        if not (VENDOR / name / '__init__.py').is_file():
            raise ImportError(f'the vendored {name} is missing from {VENDOR}')
    vendor = str(VENDOR)
    if vendor in sys.path:
        sys.path.remove(vendor)
    sys.path.insert(0, vendor)
    import markdown_it
    import mdurl
    for module in (markdown_it, mdurl):
        if Path(module.__file__).resolve().parent.parent != VENDOR:
            raise ImportError(f'{module.__name__} loaded from {module.__file__}, not from {VENDOR}')
    if markdown_it.__version__ != VERSION:
        raise ImportError(f'markdown-it-py {markdown_it.__version__} loaded; {VERSION} is vendored')
    import markdown_it.main
    if markdown_it.main.linkify_it is not None:
        raise ImportError('markdown-it-py loaded linkify_it')
    # Without text_join, escapes and entity references stay text_special tokens,
    # so literal text can be told apart from them.
    return markdown_it.MarkdownIt('commonmark').enable('table').disable('text_join')


PARSER = _parser()


def slug(text):
    """GitHub's heading anchor for a heading's text, without a duplicate suffix."""
    return re.sub(r'[^\w -]', '', text.lower()).replace(' ', '-')


def plain(children):
    """The text a reader sees: text, escapes and code content, without markup or HTML."""
    parts = []
    for token in children:
        if token.type in ('text', 'text_special', 'code_inline'):
            parts.append(token.content)
        elif token.type == 'softbreak':
            parts.append(' ')
        elif token.type == 'hardbreak':
            parts.append('\n')
    return ''.join(parts)


@dataclass(frozen=True)
class Inline:
    """One run of inline content: a paragraph, a heading or a table cell.

    `depth` counts the lists and block quotes around it; 0 is the top level.
    """
    kind: str
    lines: tuple
    depth: int
    children: tuple

    @property
    def text(self):
        return plain(self.children)

    @property
    def code(self):
        return [token.content for token in self.children if token.type == 'code_inline']

    @property
    def pieces(self):
        """The run in order as ('text' | 'code' | 'html', str) and ('link' | 'image', Link) pairs.

        Adjacent text merges, a link's label is inside its Link, and emphasis
        leaves no piece of its own.
        """
        return _pieces(self)

    def _lead(self):
        # Emphasis processing can leave an empty text token before the first span.
        return [token for token in self.children if not (token.type == 'text' and not token.content)]

    @property
    def leading_code(self):
        """The content of a code span that opens this run, or None."""
        lead = self._lead()
        return lead[0].content if lead and lead[0].type == 'code_inline' else None

    @property
    def leading_strong(self):
        """The text of a strong span that opens this run, or None."""
        lead = self._lead()
        if not lead or lead[0].type != 'strong_open':
            return None
        end = next(i for i, token in enumerate(lead) if token.type == 'strong_close')
        return plain(lead[1:end])

    @property
    def leading_link(self):
        """The link that opens this run, or None."""
        lead = self._lead()
        return _links(self)[0] if lead and lead[0].type == 'link_open' else None


@dataclass(frozen=True)
class Link:
    """An inline link or image. `target` is the destination as written, decoded."""
    target: str
    label: str
    code_label: str | None
    image: bool
    autolink: bool
    inline: Inline


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    anchor: str
    line: int
    atx: bool
    inline: Inline


@dataclass(frozen=True)
class Block:
    """A fence, an indented code block or an HTML block."""
    kind: str
    lines: tuple
    info: str
    content: str


@dataclass(frozen=True)
class ListItem:
    """A list item in document order; `depth` is 0 in a top-level list."""
    ordered: bool
    number: str
    depth: int
    lines: tuple
    first: Inline | None


@dataclass(frozen=True)
class Table:
    lines: tuple
    header: tuple
    rows: tuple


@dataclass(frozen=True)
class Section:
    """A heading and the lines up to the next heading of the same or a higher level."""
    heading: Heading
    lines: tuple

    def holds(self, lines):
        return self.lines[0] <= lines[0] and lines[1] <= self.lines[1]


class Document:
    def __init__(self, text, name='<text>'):
        self.text, self.name = text, name
        self._starts = [0] + [m.end() for m in re.finditer('\n', text)]
        env = {}
        self.tokens = PARSER.parse(text, env)
        self.references = dict(env.get('references', {}))
        self.inlines, self.headings, self.links, self.blocks = [], [], [], []
        self.items, self.tables = [], []
        self._read()
        self._refuse_unrecognized_comments()
        self.anchors = []
        seen = set()
        for heading in self.headings:
            base, anchor, suffix = heading.anchor, heading.anchor, 0
            while anchor in seen:
                suffix += 1
                anchor = f'{base}-{suffix}'
            seen.add(anchor)
            self.anchors.append(anchor)

    def _read(self):
        lists, items, order, row, rows, header = [], [], [], None, None, None
        heading, table, quotes = None, None, 0
        for token in self.tokens:
            kind = token.type
            if kind in ('bullet_list_open', 'ordered_list_open'):
                lists.append(kind == 'ordered_list_open')
            elif kind in ('bullet_list_close', 'ordered_list_close'):
                lists.pop()
            elif kind == 'blockquote_open':
                quotes += 1
            elif kind == 'blockquote_close':
                quotes -= 1
            elif kind == 'list_item_open':
                items.append(len(order))
                order.append([lists[-1], token.info, len(lists) - 1, tuple(token.map), None])
            elif kind == 'list_item_close':
                items.pop()
            elif kind == 'heading_open':
                heading = token
            elif kind == 'table_open':
                table, rows, header = token, [], None
            elif kind == 'tr_open':
                row = []
            elif kind == 'tr_close':
                if header is None:
                    header = tuple(row)
                else:
                    rows.append(tuple(row))
            elif kind == 'table_close':
                self.tables.append(Table(tuple(table.map), header or (), tuple(rows)))
                table = None
            elif kind in ('fence', 'code_block', 'html_block'):
                self.blocks.append(Block({'fence': 'fence', 'code_block': 'code', 'html_block': 'html'}[kind],
                                         tuple(token.map), token.info.strip(), token.content))
            elif kind == 'inline':
                container = 'heading' if heading else 'cell' if row is not None else 'paragraph'
                inline = Inline(container, tuple(token.map), len(lists) + quotes, tuple(token.children or ()))
                self.inlines.append(inline)
                self.links.extend(_links(inline))
                if heading:
                    text = inline.text.strip()
                    self.headings.append(Heading(int(heading.tag[1]), text, slug(text), heading.map[0],
                                                 heading.markup.startswith('#'), inline))
                elif row is not None:
                    row.append(inline)
                elif items and order[items[-1]][4] is None:
                    order[items[-1]][4] = inline
            elif kind == 'heading_close':
                heading = None
            if kind == 'tr_close':
                row = None
        self.items = [ListItem(*item) for item in order]

    def _refuse_unrecognized_comments(self):
        for inline in self.inlines:
            for token in _flatten(inline.children):
                if token.type == 'text' and '<!--' in token.content:
                    raise Refused(f'{self.name}:{inline.lines[0] + 1}: markdown-it-py {VERSION} reads an inline '
                                  'comment containing "--" as text, but GitHub hides it; remove the "--"')

    def line_of(self, offset):
        """The zero-based line holding a character offset."""
        return bisect_right(self._starts, offset) - 1

    def offset(self, line):
        """The character offset where a zero-based line starts; the text's length past the end."""
        return self._starts[line] if line < len(self._starts) else len(self.text)

    @property
    def prose_lines(self):
        """Lines holding inline content: paragraphs, headings and table rows."""
        return {line for inline in self.inlines for line in range(*inline.lines)}

    def sections(self, text, level=None):
        found = []
        for index, heading in enumerate(self.headings):
            if heading.text != text or (level is not None and heading.level != level):
                continue
            end = next((h.line for h in self.headings[index + 1:] if h.level <= heading.level),
                       len(self._starts))
            found.append(Section(heading, (heading.line, end)))
        return found

    def section(self, text, level=None):
        """The one section with this heading text, or None; more than one is refused."""
        found = self.sections(text, level)
        if len(found) > 1:
            raise Refused(f'{self.name}: {len(found)} sections titled {text!r}')
        return found[0] if found else None

    def fences(self, info=None):
        return [b for b in self.blocks if b.kind == 'fence' and (info is None or b.info == info)]


def _flatten(children):
    for token in children:
        yield token
        if token.type == 'image':
            yield from _flatten(token.children or ())


def _pieces(inline):
    pieces, label = [], None
    for token in inline.children:
        if token.type == 'link_open':
            label = (token, [])
        elif token.type == 'link_close':
            opening, children = label
            code = [t for t in children if t.type == 'code_inline']
            only_code = len(children) == 1 and len(code) == 1
            pieces.append(('link', Link(unquote(opening.attrs.get('href', '')), plain(children),
                                        code[0].content if only_code else None, False,
                                        opening.markup == 'autolink', inline)))
            label = None
        elif label is not None:
            label[1].append(token)
        elif token.type == 'image':
            pieces.append(('image', Link(unquote(token.attrs.get('src', '')), plain(token.children or ()), None,
                                         True, False, inline)))
        elif token.type == 'code_inline':
            pieces.append(('code', token.content))
        elif token.type == 'html_inline':
            pieces.append(('html', token.content))
        elif token.type in ('text', 'text_special', 'softbreak', 'hardbreak'):
            text = plain([token])
            if pieces and pieces[-1][0] == 'text':
                pieces[-1] = ('text', pieces[-1][1] + text)
            elif text:
                pieces.append(('text', text))
    return pieces


def _links(inline):
    return [value for kind, value in _pieces(inline) if kind in ('link', 'image')]


@lru_cache(maxsize=256)
def parse(text, name='<text>'):
    return Document(text, name)


def read(path):
    path = Path(path)
    return parse(path.read_text(), str(path))


def source_files(root=ROOT):
    """This module and the vendored parser, as paths relative to the repository root."""
    vendored = [path for name in ('markdown_it', 'mdurl') for path in (root / 'tests/lib/vendor' / name).rglob('*')
                if path.is_file() and '__pycache__' not in path.parts]
    vendored += list((root / 'tests/lib/vendor').glob('*.RECORD'))
    return ['docs/markdown_reader.py'] + sorted(path.relative_to(root).as_posix() for path in vendored)
