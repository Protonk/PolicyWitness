"""Controls for the Markdown reader: what the vendored parser reports, how it is
loaded, that the vendored files are the wheels' bytes and that nothing else
imports the parser.

Expected values are written by hand from CommonMark and from GitHub's rendering;
none is computed by the reader under test.

Each item's stable identity is `<Group>.<function>`, followed by a label where the
function runs once per input. Collection imports neither the reader nor the
fixture copier and creates nothing: the reader loads in the first item that asks
for it, and every temporary tree belongs to the item that makes it.
"""
import ast
import base64
import csv
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import textwrap

import pytest

ROOT = Path(__file__).resolve().parents[3]
PW_SOURCE_FILES = ('docs/markdown_reader.py', 'docs/repository_tree.py', 'tests/lib/fixture_inputs.py')

PARSER_MODULES = ('markdown_it', 'mdurl')
# The RECORD files of the wheels whose digests matched PyPI's when they were vendored.
RECORDS = {'markdown_it_py-3.0.0.RECORD': 'a1de86362d0f974969ec83963ff307aaa9f5ea30834642f3134e6b239742f95f',
           'mdurl-0.1.2.RECORD': '72e8c94bf8f6a74a6a9a113a56ae3e9cade7dcb3ce2591fe60eb161f2948167f'}

ROUTE = 'runner/AGENTS.md#sandboxed-automation-harnesses'
LINK = '[route](runner/AGENTS.md#sandboxed-automation-harnesses)'
# What `sections` reports for a name the reader refuses to resolve.
REFUSED = 'refused'


def control(group, commands='none'):
    """Give a function its identity, `group.function`, and its command scope."""
    def mark(function):
        function = pytest.mark.pw_commands(commands)(function)
        return pytest.mark.pw_id(f'{group}.{function.__name__}')(function)
    return mark


def inputs(group, names, rows, commands='none'):
    """Run a function once per `(label, value...)` row; `group.function.label` identifies each run."""
    def mark(function):
        identity = f'{group}.{function.__name__}'
        cases = [pytest.param(*values, id=label, marks=pytest.mark.pw_id(f'{identity}.{label}'))
                 for label, *values in rows]
        function = pytest.mark.pw_commands(commands)(function)
        return pytest.mark.parametrize(names, cases)(function)
    return mark


def vendor_problems(root=ROOT):
    """Each vendored parser file must have its wheel's RECORD digest, with nothing added or missing."""
    vendor = root / 'tests/lib/vendor'
    records = sorted(vendor.glob('*.RECORD'))
    problems = [f'{name}: missing' for name in sorted(set(RECORDS) - {r.name for r in records})]
    for record in records:
        if hashlib.sha256(record.read_bytes()).hexdigest() != RECORDS.get(record.name):
            problems.append(f"{record.name}: not the RECORD of the verified wheel")
        dist = record.name[:-len('.RECORD')] + '.dist-info/'
        rows = list(csv.reader(record.read_text().splitlines()))
        packages = {path.split('/')[0] for path, _, _ in rows if not path.startswith(dist)}
        listed = {path: digest for path, digest, _ in rows if not path.startswith(dist)}
        # A wheel's licenses live in its dist-info; the vendored copy keeps them in the package.
        listed.update({f'{package}/{path[len(dist):]}': digest for path, digest, _ in rows
                       if path.startswith(dist + 'LICENSE') for package in packages})
        present = {path.relative_to(vendor).as_posix() for package in packages for path in (vendor / package).rglob('*')
                   if path.is_file() and '__pycache__' not in path.parts}
        for path in sorted(set(listed) - present):
            problems.append(f'{record.name}: missing vendored file {path}')
        for path in sorted(present - set(listed)):
            problems.append(f'{record.name}: vendored file {path} is not in the wheel')
        for path in sorted(set(listed) & present):
            digest = base64.urlsafe_b64encode(hashlib.sha256((vendor / path).read_bytes()).digest()).rstrip(b'=')
            if listed[path] != 'sha256=' + digest.decode():
                problems.append(f'{record.name}: vendored file {path} differs from the wheel')
    return problems


def import_problems(root, paths):
    """Only the reader may import the parser."""
    problems = []
    for name in paths:
        if name == 'docs/markdown_reader.py' or name.startswith('tests/lib/vendor/'):
            continue
        tree = ast.parse((root / name).read_text(), name)
        for node in ast.walk(tree):
            modules = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                       else [node.module or ''] if isinstance(node, ast.ImportFrom) else [])
            if any(module.split('.')[0] in PARSER_MODULES for module in modules):
                problems.append(f'{name}:{node.lineno}: imports the Markdown parser; use docs/markdown_reader.py')
    return problems


def tracked_python(run_command, root=ROOT):
    listed = run_command(['git', 'ls-files', '*.py'], timeout=60, cwd=root)
    assert listed.returncode == 0, listed.stderr
    return [name for name in listed.stdout.split() if (root / name).is_file()]


def parse(reader, text):
    return reader.Document(textwrap.dedent(text))


def prose(reader, text):
    document = parse(reader, text)
    return [document.text.split('\n')[line] for line in sorted(document.prose_lines)]


def links(reader, text):
    return [(l.target, l.label, l.code_label, l.image, l.autolink) for l in parse(reader, text).links]


def sections(reader, document, names):
    """Each named section's lines: None where the document has no such section, REFUSED where the reader refuses the name."""
    found = {}
    for name in names:
        try:
            section = document.section(name)
        except reader.Refused:
            found[name] = REFUSED
        else:
            found[name] = None if section is None else section.lines
    return found


def observed(expected, **observations):
    """Only the observations an input's expectation names, so one comparison reports every difference."""
    return {name: observations[name]() for name in expected}


@dataclass(frozen=True)
class Completed:
    """One settled command: its exit status and the output its owner retained."""
    returncode: int
    stdout: str
    stderr: str


@pytest.fixture(scope='session')
def reader():
    """The reader under test. Importing it loads the vendored parser, so no import happens during collection."""
    docs = str(ROOT / 'docs')
    if docs not in sys.path:
        sys.path.insert(0, docs)
    import markdown_reader
    return markdown_reader


@pytest.fixture(scope='session')
def declared(reader):
    """The shared fixture copier with the reader's declared inputs. It imports the reader, so it follows `reader`."""
    library = str(ROOT / 'tests/lib')
    if library not in sys.path:
        sys.path.insert(0, library)
    import fixture_inputs
    return fixture_inputs


@pytest.fixture
def temporary(pw_inputs):
    """Make temporary directories that this item owns.

    The caller registers a directory with `pw_inputs.track` once its starting content is in place and
    before changing it. Teardown captures every registered tree that still exists, then removes the
    directories, newest first. A capture or removal error fails the item's teardown."""
    owned = []

    def make(prefix):
        directory = tempfile.TemporaryDirectory(prefix=prefix)
        owned.append(directory)
        return Path(directory.name)

    yield make
    errors = []
    try:
        pw_inputs.capture_tracked('before cleanup')
    except Exception as error:
        errors.append(error)
    for directory in reversed(owned):
        try:
            directory.cleanup()
        except Exception as error:
            errors.append(error)
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise ExceptionGroup('temporary directories were not captured and removed', errors)


@pytest.fixture
def reader_tree(temporary, declared, pw_inputs):
    """Copy the reader's declared inputs into a tree of this item's own, registered before the item changes it."""
    def build(prefix, vendored=True):
        root = temporary(prefix)
        declared.copy_declared(ROOT, root, declared.reader_inputs(ROOT) if vendored else ['docs/markdown_reader.py'])
        pw_inputs.track(root)
        return root
    return build


@pytest.fixture
def stand_in(temporary, pw_inputs):
    """Write a one-file package into a directory of its own and return that directory, for `PYTHONPATH`."""
    def write(name, body):
        directory = temporary('pw-stand-in-')
        package = directory / name
        package.mkdir()
        (package / '__init__.py').write_text(body)
        pw_inputs.track(directory)
        return str(directory)
    return write


@pytest.fixture
def run_command(request, pw_equipment, pw_inputs):
    """Run a real command at the engine's supervised boundary and read back what its owner retained.

    Registered trees are captured before each launch. The owner writes `command.json`, `stdout` and
    `stderr` under `artifacts/commands/<identity>/launch-NNN/`. The number counts the commands this
    item asked for; processes that a command starts are outside it."""
    identity = request.node.get_closest_marker('pw_id').args[0]
    launches = 0

    def run(argv, *, timeout, cwd=None, env=None):
        nonlocal launches
        launches += 1
        directory = pw_equipment.artifacts / 'commands' / identity / f'launch-{launches:03}'
        pw_inputs.capture_tracked('before command')
        receipt = pw_equipment.command(argv, directory, timeout, cwd=cwd, env=env)
        return Completed(receipt['returncode'], (directory / 'stdout').read_text(), (directory / 'stderr').read_text())
    return run


@pytest.fixture
def fresh_reader(run_command):
    """Import the reader from a tree in a fresh interpreter: no site, no bytecode, no working-directory path entry."""
    def run(root, env=None, before=''):
        script = (before + 'import sys; sys.path.insert(0, sys.argv[1]); import markdown_reader; '
                  'print(markdown_reader.parse("x").inlines[0].text)')
        return run_command([sys.executable, '-B', '-S', '-P', '-c', script, str(root / 'docs')],
                           timeout=60, cwd=ROOT, env=dict(os.environ, **(env or {})))
    return run


# Blocks

@inputs('BlockTests', 'text, expected', [
    ('backtick-and-tilde-fences', '''\
            ````text
            ```
            hidden
            ````
            ~~~
            also hidden
            ~~~
            seen
            ''', dict(fences=[('text', (0, 4)), ('', (4, 7))], prose=['seen'])),
    # A comment opener inside a fence, before a real heading, hides nothing: the fence ends at its
    # marker and the heading that follows is the one section of that name.
    ('fake-heading-before-real',
     '```text\n<!--\n## Sandboxed automation harnesses\n```\n\n## Sandboxed automation harnesses\n\nbody\n',
     dict(headings=[(2, 'Sandboxed automation harnesses', 5)], sections={'Sandboxed automation harnesses': (5, 9)},
          prose=['## Sandboxed automation harnesses', 'body'])),
    # A body wrapped in a longer fence whose first line is a shorter marker stays hidden to its own marker.
    ('short-fence-close', '## H\n\n````text\n```\nbody [a](a.md)\n````\n\nseen\n',
     dict(prose=['## H', 'seen'], links=[])),
])
def test_fences_close_only_on_the_same_marker_at_least_as_long(reader, text, expected):
    document = parse(reader, text)
    assert observed(expected,
                    fences=lambda: [(b.info, b.lines) for b in document.fences()],
                    headings=lambda: [(h.level, h.text, h.line) for h in document.headings],
                    sections=lambda: sections(reader, document, expected['sections']),
                    prose=lambda: prose(reader, document.text),
                    links=lambda: document.links) == expected


@control('BlockTests')
def test_a_backtick_in_the_info_string_does_not_open_a_backtick_fence(reader):
    assert prose(reader, '```a`b\nseen\n') == ['```a`b', 'seen']


@control('BlockTests')
def test_a_fence_inside_a_list_item_is_a_fence(reader):
    document = parse(reader, '- item\n\n  ```sh\n  hidden\n  ```\n')
    assert [(b.info, b.content) for b in document.fences()] == [('sh', 'hidden\n')]
    assert prose(reader, document.text) == ['- item']


@inputs('BlockTests', 'text, expected', [
    ('paragraph-continuation', 'para\n    continued\n', dict(prose=['para', '    continued'])),
    ('indented-after-blank-line', 'para\n\n    code\n', dict(prose=['para'])),
    ('indented-after-heading', '# Heading\n    code\n', dict(prose=['# Heading'], kinds=['code'])),
    ('route-indented-continuation', 'continued\n    ' + LINK + '\n',
     dict(targets=['runner/AGENTS.md#sandboxed-automation-harnesses'])),
    ('route-indented-example', 'para\n\n    ' + LINK + '\n', dict(links=[])),
    ('route-indented-after-heading', '#### Example\n    ' + LINK + '\n', dict(links=[], prose=['#### Example'])),
])
def test_indentation_opens_code_only_where_no_paragraph_continues(reader, text, expected):
    document = parse(reader, text)
    assert observed(expected,
                    prose=lambda: prose(reader, text),
                    kinds=lambda: [b.kind for b in document.blocks],
                    targets=lambda: [l.target for l in document.links],
                    links=lambda: document.links) == expected


@inputs('BlockTests', 'text, expected', [
    # The shape of the nested list under step 3 of runner/augments/README.md.
    ('nested-list', '1. Step\n\n     - nested after a blank line\n       continued\n',
     dict(prose=['1. Step', '     - nested after a blank line', '       continued'],
          items=[(True, '1', 0, 'Step'), (False, '', 1, 'nested after a blank line continued')])),
    # A link in an item's continuation after a blank line is a link, inside the item's lines.
    ('route-list-continuation', '- Diagnostics are\n\n    [route](runner/AGENTS.md#sandboxed-automation-harnesses)\n',
     dict(targets=['runner/AGENTS.md#sandboxed-automation-harnesses'], item_lines=[(0, 3)], link_inside_item=True)),
])
def test_list_content_after_a_blank_line_is_prose(reader, text, expected):
    document = parse(reader, text)
    assert observed(expected,
                    prose=lambda: prose(reader, text),
                    items=lambda: [(i.ordered, i.number, i.depth, i.first.text) for i in document.items],
                    targets=lambda: [l.target for l in document.links],
                    item_lines=lambda: [i.lines for i in document.items],
                    link_inside_item=lambda: (document.items[0].lines[0] <= document.links[0].inline.lines[0]
                                              < document.items[0].lines[1])) == expected


@control('BlockTests')
def test_an_item_opening_with_another_block_has_no_first_paragraph(reader):
    document = parse(reader, '- - `inner.xpc`\n\n  `Contents/MacOS/outer` trailing\n- ```\n  code\n  ```\n  after\n')
    assert [(i.depth, i.first and i.first.text) for i in document.items] == [(0, None), (1, 'inner.xpc'), (0, None)]


@control('BlockTests')
def test_leading_code_strong_and_link(reader):
    document = parse(reader, '- `a` b\n- **Label**: text\n- [x](#y): z\n- plain `c`\n')
    assert [(i.first.leading_code, i.first.leading_strong,
             i.first.leading_link and i.first.leading_link.target) for i in document.items] == \
        [('a', None, None), (None, 'Label', None), (None, None, '#y'), (None, None, None)]


# Comments

@inputs('CommentTests', 'text, expected', [
    ('inline-and-block-comments', 'text <!-- inline [a](a.md) --> after\n\n<!--\n[b](b.md)\n-->\n\n<!-- one line -->\n',
     dict(links=[], prose=['text <!-- inline [a](a.md) --> after'], blocks=[('html', (2, 5)), ('html', (6, 7))])),
    ('commented-heading-and-route', '<!--\n## Hidden\n\n[route](x.md#y)\n-->\n\n## Shown\n\ntext\n',
     dict(headings=[(2, 'Shown', 6)], sections={'Hidden': None, 'Shown': (6, 10)}, links=[],
          prose=['## Shown', 'text'])),
])
def test_comments_are_not_prose(reader, text, expected):
    document = parse(reader, text)
    assert observed(expected,
                    links=lambda: document.links,
                    prose=lambda: prose(reader, document.text),
                    blocks=lambda: [(b.kind, b.lines) for b in document.blocks],
                    headings=lambda: [(h.level, h.text, h.line) for h in document.headings],
                    sections=lambda: sections(reader, document, expected['sections'])) == expected


# CommonMark 0.30 reads it as text; GitHub hides it.
@inputs('CommentTests', 'text', [
    ('in-text', 'text <!-- a -- b --> after\n'),
    ('in-image-alt', '![alt <!-- a -- b -->](x.png)\n'),
    ('around-a-route', 'see <!-- a -- b [route](runner/AGENTS.md#sandboxed-automation-harnesses) -->\n'),
])
def test_an_inline_comment_containing_two_hyphens_is_refused(reader, text):
    with pytest.raises(reader.Refused, match='remove the "--"'):
        parse(reader, text)


@control('CommentTests')
def test_an_opener_without_a_later_closer_is_text(reader):
    # GitHub shows it as text too: an inline comment needs a later "-->".
    assert parse(reader, 'The opener <!-- starts a comment in HTML.\n').inlines[0].text == \
        'The opener <!-- starts a comment in HTML.'


@control('CommentTests')
def test_escaped_entity_and_code_comment_openers_are_text(reader):
    document = parse(reader, 'a \\<!-- b &lt;!-- c `<!--` d\n')
    assert document.inlines[0].text == 'a <!-- b <!-- c <!-- d'
    assert document.inlines[0].code == ['<!--']


@control('CommentTests')
def test_a_comment_that_begins_a_line_ends_the_paragraph(reader):
    # GitHub renders the second line as raw HTML outside the paragraph.
    document = parse(reader, 'one\n<!-- span a -->5<!-- /span --> two\nthree\n')
    assert [(b.kind, b.lines) for b in document.blocks] == [('html', (1, 2))]
    assert prose(reader, document.text) == ['one', 'three']


# Links

@inputs('LinkTests', 'text, expected', [
    ('code-label-and-wrapped-label', '[`a.py`](a.py) [wrapped\nlabel](b.md#c)\n',
     [('a.py', 'a.py', 'a.py', False, False), ('b.md#c', 'wrapped label', None, False, False)]),
    ('label-split-by-a-blank-line', '[split\n\nlabel](b.md)\n', []),
    ('route-split-label', '[Split `diagnostic\n\nwording`](runner/AGENTS.md#sandboxed-automation-harnesses)\n', []),
    ('route-wrapped-label', '[Wrapped diagnostic\nwording](runner/AGENTS.md#x)\n',
     [('runner/AGENTS.md#x', 'Wrapped diagnostic wording', None, False, False)]),
])
def test_labels_may_hold_code_and_wrap_but_not_cross_a_blank_line(reader, text, expected):
    assert links(reader, text) == expected


@inputs('LinkTests', 'text, expected', [
    ('image-escape-code-and-autolink', '![alt](p.png) \\[x](y.md) `[c](d.md)` <https://example.com/a>\n',
     [('p.png', 'alt', None, True, False),
      ('https://example.com/a', 'https://example.com/a', None, False, True)]),
    ('route-fenced', '```markdown\n[l](' + ROUTE + ')\n```\n', []),
    ('route-code-label-example', '`` [`runner/AGENTS.md`](' + ROUTE + ') ``\n', []),
    ('route-inline-example', '`[l](' + ROUTE + ')`\n', []),
    ('route-image', '![l](' + ROUTE + ')\n', [(ROUTE, 'l', None, True, False)]),
    ('route-code-label', '[`runner/AGENTS.md`](' + ROUTE + ')\n',
     [(ROUTE, 'runner/AGENTS.md', 'runner/AGENTS.md', False, False)]),
])
def test_images_escapes_code_and_autolinks(reader, text, expected):
    assert links(reader, text) == expected


@control('LinkTests')
def test_destinations_are_decoded(reader):
    assert links(reader, '[a](<two words.md>) [b](a\\_b.py#frag)\n') == \
        [('two words.md', 'a', None, False, False), ('a_b.py#frag', 'b', None, False, False)]


@control('LinkTests')
def test_pieces_keep_order_and_fold_labels_into_links(reader):
    inline = parse(reader, 'Use `a` and *b*.\nThen [`c`](c.py) ![i](i.png) <!-- span x.y -->1<!-- /span -->\n').inlines[0]
    assert [(kind, value if kind in ('text', 'code', 'html') else value.target) for kind, value in inline.pieces] == \
        [('text', 'Use '), ('code', 'a'), ('text', ' and b. Then '), ('link', 'c.py'), ('text', ' '),
         ('image', 'i.png'), ('text', ' '), ('html', '<!-- span x.y -->'), ('text', '1'),
         ('html', '<!-- /span -->')]


@control('LinkTests')
def test_an_image_inside_a_link_label_is_an_image(reader):
    assert links(reader, '[![badge](missing.png)](target.md)\n') == \
        [('missing.png', 'badge', None, True, False), ('target.md', '', None, False, False)]


@inputs('LinkTests', 'text, expected', [
    ('defined-reference', '[x][ref]\n\n[ref]: target.md\n', dict(references=['REF'])),
    ('undefined-reference', '[x][undefined]\n', dict(links=[])),
])
def test_reference_definitions_are_reported(reader, text, expected):
    document = parse(reader, text)
    assert observed(expected,
                    references=lambda: list(document.references),
                    links=lambda: document.links) == expected


# Headings, sections and anchors

@inputs('HeadingTests', 'text, expected', [
    ('setext-atx-and-excluded-contexts', '''\
            Title
            =====

            Sub
            ---

            ## ATX `code` [link](u.md) ##

            ```
            ## fenced
            ```

            <!--
            ## commented
            -->

                ## indented
            ''', dict(forms=[(1, 'Title', 0, False), (2, 'Sub', 3, False), (2, 'ATX code link', 6, True)])),
    ('fake-heading-before-real', '```text\n<!--\n## fake\n```\n\n## real\n', dict(headings=[(2, 'real', 5)])),
])
def test_levels_text_and_where_headings_are_not(reader, text, expected):
    document = parse(reader, text)
    assert observed(expected,
                    forms=lambda: [(h.level, h.text, h.line, h.atx) for h in document.headings],
                    headings=lambda: [(h.level, h.text, h.line) for h in document.headings]) == expected


@inputs('HeadingTests', 'text, expected', [
    ('nested-levels', '# A\n## B\ntext\n### C\nmore\n## D\n# E\n', dict(sections={'B': (1, 5), 'A': (0, 6)})),
    ('body-after-peer-level-2', '## A\n\n## Other\n\nbody\n', dict(sections={'A': (0, 2)}, body=[])),
    ('body-after-parent-level-1', '## A\n\n# Other\n\nbody\n', dict(sections={'A': (0, 2)}, body=[])),
    ('body-after-peer-level-3', '### A\n\n### Other\n\nbody\n', dict(sections={'A': (0, 2)}, body=[])),
    ('body-after-parent-level-2', '### A\n\n## Other\n\nbody\n', dict(sections={'A': (0, 2)}, body=[])),
    ('absent-section', '### A\n\n## Other\n\nbody\n', dict(sections={'Z': None})),
    ('duplicate-section', '## B\n## B\n', dict(sections={'B': REFUSED})),
])
def test_sections_end_at_the_same_or_a_higher_level(reader, text, expected):
    document = parse(reader, text)
    assert observed(expected,
                    sections=lambda: sections(reader, document, expected['sections']),
                    body=lambda: [i.text for i in document.inlines
                                  if i.kind != 'heading' and document.section('A').holds(i.lines)]) == expected


@control('HeadingTests')
def test_a_multi_line_setext_heading_anchors_without_the_break(reader):
    document = parse(reader, 'Foo\nbar\n===\n')
    assert (document.headings[0].text, document.anchors) == ('Foo bar', ['foobar'])


@inputs('HeadingTests', 'text, expected', [
    ('heading-anchors', '## Test seam: `_test_overrides`\n## Repeated\n## Repeated\n## Ünïcode\n',
     dict(anchors=['test-seam-_test_overrides', 'repeated', 'repeated-1', 'ünïcode'])),
    ('slug', 'One build in time', dict(slug='one-build-in-time')),
])
def test_anchors_keep_underscores_and_number_duplicates(reader, text, expected):
    assert observed(expected,
                    anchors=lambda: parse(reader, text).anchors,
                    slug=lambda: reader.slug(text)) == expected


@control('HeadingTests')
def test_explicit_anchor_elements_are_destinations_without_changing_heading_slugs(reader):
    document = parse(reader, '<a id="contract-request-policy"></a>\n\n'
                             '## Repeated\n\n<a id="repeated"></a>\n\n## Repeated\n\n'
                             'Inline <a class="target" id=inline-anchor></a> destination.\n\n'
                             '<A NAME=legacy-anchor></A>\n\n'
                             '<a\n title="attribute contains >"\n id="entity&amp;anchor"></a>\n')
    assert document.anchors == ['repeated', 'repeated-1', 'contract-request-policy',
                                'repeated', 'inline-anchor', 'legacy-anchor', 'entity&anchor']


@control('HeadingTests')
def test_explicit_anchor_examples_in_code_comments_and_escaped_text_are_not_destinations(reader):
    document = parse(reader, '```html\n<a id="fenced"></a>\n```\n\n'
                             '    <a id="indented"></a>\n\n'
                             'Inline `<a id="inline-code"></a>` example.\n\n'
                             '<!-- <a id="commented"></a> -->\n\n'
                             'Text <!-- <a id="inline-comment"></a> --> continues.\n\n'
                             '&lt;a id="escaped"&gt;&lt;/a&gt;\n\n'
                             '<a href="#link-only"></a>\n\n'
                             '<script>const example = \'<a id="script-text"></a>\';</script>\n')
    assert document.anchors == []


# Tables

@control('TableTests')
def test_cells_hold_inline_content(reader):
    document = parse(reader, '| A | B |\n| --- | --- |\n| `a\\|b` | [l](t.md) |\n| x | y |\n')
    table, = document.tables
    assert [c.text for c in table.header] == ['A', 'B']
    assert [[c.text for c in row] for row in table.rows] == [['a|b', 'l'], ['x', 'y']]
    assert table.rows[0][0].code == ['a|b']
    assert table.rows[1][0].lines == (3, 4)


@control('TableTests')
def test_a_table_in_a_comment_or_fence_is_not_a_table(reader):
    assert parse(reader, '<!--\n| A |\n| --- |\n| x |\n-->\n\n```\n| A |\n| --- |\n```\n').tables == []


# Lines

@control('LineTests')
def test_lines_and_offsets(reader):
    document = parse(reader, 'a\n\nb\nc\n')
    assert [i.lines for i in document.inlines] == [(0, 1), (2, 4)]
    assert [document.line_of(o) for o in (0, 1, 2, 3, 5)] == [0, 0, 1, 2, 3]


# Vendored bytes and the import rule

@control('VendorTests')
def test_vendored_files_are_the_wheels_bytes():
    assert vendor_problems() == []


@control('VendorTests')
def test_a_changed_added_or_missing_vendored_file_is_named(reader_tree):
    root = reader_tree('pw-vendor-')
    vendor = root / 'tests/lib/vendor'
    changed = vendor / 'markdown_it/rules_inline/html_inline.py'
    changed.write_text(changed.read_text() + '\n')
    (vendor / 'mdurl/extra.py').write_text('')
    (vendor / 'markdown_it/LICENSE.markdown-it').unlink()
    assert vendor_problems(root) == [
        'markdown_it_py-3.0.0.RECORD: missing vendored file markdown_it/LICENSE.markdown-it',
        'markdown_it_py-3.0.0.RECORD: vendored file markdown_it/rules_inline/html_inline.py differs from the wheel',
        'mdurl-0.1.2.RECORD: vendored file mdurl/extra.py is not in the wheel',
    ]


@control('VendorTests')
def test_a_rewritten_record_is_named(reader_tree):
    root = reader_tree('pw-record-')
    vendor = root / 'tests/lib/vendor'
    changed = vendor / 'markdown_it/rules_inline/html_inline.py'
    changed.write_text(changed.read_text() + '\n')
    digest = 'sha256=' + base64.urlsafe_b64encode(hashlib.sha256(changed.read_bytes()).digest()).rstrip(b'=').decode()
    record = vendor / 'markdown_it_py-3.0.0.RECORD'
    rows = [row if row[0] != 'markdown_it/rules_inline/html_inline.py' else [row[0], digest, str(changed.stat().st_size)]
            for row in csv.reader(record.read_text().splitlines())]
    record.write_text(''.join(','.join(row) + '\n' for row in rows))
    assert vendor_problems(root) == ['markdown_it_py-3.0.0.RECORD: not the RECORD of the verified wheel']


@control('VendorTests', commands='recorded')
def test_only_the_reader_imports_the_parser(run_command):
    assert import_problems(ROOT, tracked_python(run_command)) == []


@control('VendorTests')
def test_another_importer_is_named(temporary, pw_inputs):
    root = temporary('pw-importer-')
    pw_inputs.track(root)
    (root / 'a.py').write_text('import os\nimport markdown_it.main\n')
    (root / 'b.py').write_text('from mdurl import decode\n')
    (root / 'c.py').write_text('"""import markdown_it"""\n# from mdurl import x\nname = "markdown_it"\n')
    assert import_problems(root, ['a.py', 'b.py', 'c.py']) == [
        'a.py:2: imports the Markdown parser; use docs/markdown_reader.py',
        'b.py:1: imports the Markdown parser; use docs/markdown_reader.py',
    ]


# The import guard: the parser loads only from the vendored copies, and linkify_it never loads.

@control('ImportGuardTests', commands='recorded')
def test_the_vendored_copy_loads(reader_tree, fresh_reader):
    result = fresh_reader(reader_tree('pw-markdown-'))
    assert (result.returncode, result.stdout) == (0, 'x\n'), result.stderr


@control('ImportGuardTests', commands='recorded')
def test_a_missing_vendored_copy_is_refused(reader_tree, stand_in, fresh_reader):
    path = stand_in('markdown_it', '__version__ = "3.0.0"\nclass MarkdownIt: pass\n')
    result = fresh_reader(reader_tree('pw-markdown-', vendored=False), {'PYTHONPATH': path})
    assert result.returncode != 0
    assert 'the vendored markdown_it is missing from' in result.stderr


@control('ImportGuardTests', commands='recorded')
def test_a_copy_already_imported_from_elsewhere_is_refused(reader_tree, stand_in, fresh_reader):
    path = stand_in('markdown_it', '__version__ = "3.0.0"\nclass MarkdownIt: pass\n')
    result = fresh_reader(reader_tree('pw-markdown-'), {'PYTHONPATH': path}, before='import markdown_it; ')
    assert result.returncode != 0
    assert f'markdown_it loaded from {path}' in result.stderr


@control('ImportGuardTests', commands='recorded')
def test_an_already_imported_linkify_it_is_refused(reader_tree, stand_in, fresh_reader):
    path = stand_in('linkify_it', 'class LinkifyIt: pass\n')
    result = fresh_reader(reader_tree('pw-markdown-'), {'PYTHONPATH': path}, before='import linkify_it; ')
    assert result.returncode != 0
    assert 'linkify_it is already imported' in result.stderr


@control('ImportGuardTests', commands='recorded')
def test_another_version_is_refused(reader_tree, fresh_reader):
    root = reader_tree('pw-markdown-')
    init = root / 'tests/lib/vendor/markdown_it/__init__.py'
    init.write_text(init.read_text().replace('__version__ = "3.0.0"', '__version__ = "3.0.1"'))
    result = fresh_reader(root)
    assert result.returncode != 0
    assert 'markdown-it-py 3.0.1 loaded; 3.0.0 is vendored' in result.stderr


@control('ImportGuardTests', commands='recorded')
def test_an_installed_linkify_it_is_never_imported(temporary, pw_inputs, reader_tree, stand_in, fresh_reader):
    marker = temporary('pw-linkify-') / 'imported'
    pw_inputs.track(marker.parent)
    path = stand_in('linkify_it', f'open({str(marker)!r}, "w").close()\nraise SystemExit("linkify_it imported")\n')
    result = fresh_reader(reader_tree('pw-markdown-'), {'PYTHONPATH': path})
    assert (result.returncode, result.stdout) == (0, 'x\n'), result.stderr
    assert not marker.exists()
