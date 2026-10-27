"""Controls for the Markdown reader: what the vendored parser reports, how it is
loaded, that the vendored files are the wheels' bytes and that nothing else
imports the parser.

Expected values are written by hand from CommonMark and from GitHub's rendering;
none is computed by the reader under test.
"""
import ast
import base64
import csv
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'docs'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import receipts  # noqa: E402
import fixture_inputs  # noqa: E402
import markdown_reader as reader  # noqa: E402


PARSER_MODULES = ('markdown_it', 'mdurl')
# The RECORD files of the wheels whose digests matched PyPI's when they were vendored.
RECORDS = {'markdown_it_py-3.0.0.RECORD': 'a1de86362d0f974969ec83963ff307aaa9f5ea30834642f3134e6b239742f95f',
           'mdurl-0.1.2.RECORD': '72e8c94bf8f6a74a6a9a113a56ae3e9cade7dcb3ce2591fe60eb161f2948167f'}


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


def tracked_python(root=ROOT, run=subprocess.run):
    listed = run(['git', 'ls-files', '*.py'], cwd=root, capture_output=True, text=True, check=True)
    return [name for name in listed.stdout.split() if (root / name).is_file()]


def parse(text):
    return reader.Document(textwrap.dedent(text))


def prose(text):
    document = parse(text)
    return [document.text.split('\n')[line] for line in sorted(document.prose_lines)]


class BlockTests(receipts.TestCase):
    def test_fences_close_only_on_the_same_marker_at_least_as_long(self):
        document = parse('''\
            ````text
            ```
            hidden
            ````
            ~~~
            also hidden
            ~~~
            seen
            ''')
        self.assertEqual([(b.info, b.lines) for b in document.fences()], [('text', (0, 4)), ('', (4, 7))])
        self.assertEqual(prose(document.text), ['seen'])
        # A comment opener inside a fence, before a real heading, hides nothing: the fence ends at its
        # marker and the heading that follows is the one section of that name.
        document = parse('```text\n<!--\n## Sandboxed automation harnesses\n```\n\n## Sandboxed automation harnesses\n\nbody\n')
        self.assertEqual([(h.level, h.text, h.line) for h in document.headings], [(2, 'Sandboxed automation harnesses', 5)])
        self.assertEqual(document.section('Sandboxed automation harnesses').lines, (5, 9))
        self.assertEqual(prose(document.text), ['## Sandboxed automation harnesses', 'body'])
        # A body wrapped in a longer fence whose first line is a shorter marker stays hidden to its own marker.
        document = parse('## H\n\n````text\n```\nbody [a](a.md)\n````\n\nseen\n')
        self.assertEqual(prose(document.text), ['## H', 'seen'])
        self.assertEqual(document.links, [])

    def test_a_backtick_in_the_info_string_does_not_open_a_backtick_fence(self):
        self.assertEqual(prose('```a`b\nseen\n'), ['```a`b', 'seen'])

    def test_a_fence_inside_a_list_item_is_a_fence(self):
        document = parse('- item\n\n  ```sh\n  hidden\n  ```\n')
        self.assertEqual([(b.info, b.content) for b in document.fences()], [('sh', 'hidden\n')])
        self.assertEqual(prose(document.text), ['- item'])

    def test_indentation_opens_code_only_where_no_paragraph_continues(self):
        self.assertEqual(prose('para\n    continued\n'), ['para', '    continued'])
        self.assertEqual(prose('para\n\n    code\n'), ['para'])
        self.assertEqual(prose('# Heading\n    code\n'), ['# Heading'])
        self.assertEqual([b.kind for b in parse('# Heading\n    code\n').blocks], ['code'])
        link = '[route](runner/AGENTS.md#sandboxed-automation-harnesses)'
        self.assertEqual([l.target for l in parse('continued\n    ' + link + '\n').links], ['runner/AGENTS.md#sandboxed-automation-harnesses'])
        self.assertEqual(parse('para\n\n    ' + link + '\n').links, [])
        self.assertEqual(parse('#### Example\n    ' + link + '\n').links, [])
        self.assertEqual(prose('#### Example\n    ' + link + '\n'), ['#### Example'])

    def test_list_content_after_a_blank_line_is_prose(self):
        # The shape of the nested list under step 3 of runner/augments/README.md.
        text = '1. Step\n\n     - nested after a blank line\n       continued\n'
        self.assertEqual(prose(text), ['1. Step', '     - nested after a blank line', '       continued'])
        document = parse(text)
        self.assertEqual([(i.ordered, i.number, i.depth, i.first.text) for i in document.items],
                         [(True, '1', 0, 'Step'), (False, '', 1, 'nested after a blank line continued')])
        # A link in an item's continuation after a blank line is a link, inside the item's lines.
        document = parse('- Diagnostics are\n\n    [route](runner/AGENTS.md#sandboxed-automation-harnesses)\n')
        self.assertEqual([l.target for l in document.links], ['runner/AGENTS.md#sandboxed-automation-harnesses'])
        self.assertEqual([i.lines for i in document.items], [(0, 3)])
        self.assertTrue(document.items[0].lines[0] <= document.links[0].inline.lines[0] < document.items[0].lines[1])

    def test_an_item_opening_with_another_block_has_no_first_paragraph(self):
        document = parse('- - `inner.xpc`\n\n  `Contents/MacOS/outer` trailing\n- ```\n  code\n  ```\n  after\n')
        self.assertEqual([(i.depth, i.first and i.first.text) for i in document.items],
                         [(0, None), (1, 'inner.xpc'), (0, None)])

    def test_leading_code_strong_and_link(self):
        document = parse('- `a` b\n- **Label**: text\n- [x](#y): z\n- plain `c`\n')
        self.assertEqual([(i.first.leading_code, i.first.leading_strong,
                           i.first.leading_link and i.first.leading_link.target) for i in document.items],
                         [('a', None, None), (None, 'Label', None), (None, None, '#y'), (None, None, None)])


class CommentTests(receipts.TestCase):
    def test_comments_are_not_prose(self):
        document = parse('text <!-- inline [a](a.md) --> after\n\n<!--\n[b](b.md)\n-->\n\n<!-- one line -->\n')
        self.assertEqual(document.links, [])
        self.assertEqual(prose(document.text), ['text <!-- inline [a](a.md) --> after'])
        self.assertEqual([(b.kind, b.lines) for b in document.blocks], [('html', (2, 5)), ('html', (6, 7))])
        document = parse('<!--\n## Hidden\n\n[route](x.md#y)\n-->\n\n## Shown\n\ntext\n')
        self.assertEqual([(h.level, h.text, h.line) for h in document.headings], [(2, 'Shown', 6)])
        self.assertIsNone(document.section('Hidden'))
        self.assertEqual(document.section('Shown').lines, (6, 10))
        self.assertEqual(document.links, [])
        self.assertEqual(prose(document.text), ['## Shown', 'text'])

    def test_an_inline_comment_containing_two_hyphens_is_refused(self):
        # CommonMark 0.30 reads it as text; GitHub hides it.
        for text in ('text <!-- a -- b --> after\n', '![alt <!-- a -- b -->](x.png)\n',
                     'see <!-- a -- b [route](runner/AGENTS.md#sandboxed-automation-harnesses) -->\n'):
            with self.subTest(text=text), self.assertRaisesRegex(reader.Refused, 'remove the "--"'):
                parse(text)

    def test_an_opener_without_a_later_closer_is_text(self):
        # GitHub shows it as text too: an inline comment needs a later "-->".
        self.assertEqual(parse('The opener <!-- starts a comment in HTML.\n').inlines[0].text,
                         'The opener <!-- starts a comment in HTML.')

    def test_escaped_entity_and_code_comment_openers_are_text(self):
        document = parse('a \\<!-- b &lt;!-- c `<!--` d\n')
        self.assertEqual(document.inlines[0].text, 'a <!-- b <!-- c <!-- d')
        self.assertEqual(document.inlines[0].code, ['<!--'])

    def test_a_comment_that_begins_a_line_ends_the_paragraph(self):
        # GitHub renders the second line as raw HTML outside the paragraph.
        document = parse('one\n<!-- span a -->5<!-- /span --> two\nthree\n')
        self.assertEqual([(b.kind, b.lines) for b in document.blocks], [('html', (1, 2))])
        self.assertEqual(prose(document.text), ['one', 'three'])


class LinkTests(receipts.TestCase):
    def links(self, text):
        return [(l.target, l.label, l.code_label, l.image, l.autolink) for l in parse(text).links]

    def test_labels_may_hold_code_and_wrap_but_not_cross_a_blank_line(self):
        self.assertEqual(self.links('[`a.py`](a.py) [wrapped\nlabel](b.md#c)\n'),
                         [('a.py', 'a.py', 'a.py', False, False), ('b.md#c', 'wrapped label', None, False, False)])
        self.assertEqual(self.links('[split\n\nlabel](b.md)\n'), [])
        self.assertEqual(self.links('[Split `diagnostic\n\nwording`](runner/AGENTS.md#sandboxed-automation-harnesses)\n'), [])
        self.assertEqual(self.links('[Wrapped diagnostic\nwording](runner/AGENTS.md#x)\n'),
                         [('runner/AGENTS.md#x', 'Wrapped diagnostic wording', None, False, False)])

    def test_images_escapes_code_and_autolinks(self):
        self.assertEqual(self.links('![alt](p.png) \\[x](y.md) `[c](d.md)` <https://example.com/a>\n'),
                         [('p.png', 'alt', None, True, False),
                          ('https://example.com/a', 'https://example.com/a', None, False, True)])
        route = 'runner/AGENTS.md#sandboxed-automation-harnesses'
        self.assertEqual(self.links('```markdown\n[l](' + route + ')\n```\n'), [])
        self.assertEqual(self.links('`` [`runner/AGENTS.md`](' + route + ') ``\n'), [])
        self.assertEqual(self.links('`[l](' + route + ')`\n'), [])
        self.assertEqual(self.links('![l](' + route + ')\n'), [(route, 'l', None, True, False)])
        self.assertEqual(self.links('[`runner/AGENTS.md`](' + route + ')\n'), [(route, 'runner/AGENTS.md', 'runner/AGENTS.md', False, False)])

    def test_destinations_are_decoded(self):
        self.assertEqual(self.links('[a](<two words.md>) [b](a\\_b.py#frag)\n'),
                         [('two words.md', 'a', None, False, False), ('a_b.py#frag', 'b', None, False, False)])

    def test_pieces_keep_order_and_fold_labels_into_links(self):
        inline = parse('Use `a` and *b*.\nThen [`c`](c.py) ![i](i.png) <!-- span x.y -->1<!-- /span -->\n').inlines[0]
        self.assertEqual([(kind, value if kind in ('text', 'code', 'html') else value.target) for kind, value in inline.pieces],
                         [('text', 'Use '), ('code', 'a'), ('text', ' and b. Then '), ('link', 'c.py'), ('text', ' '),
                          ('image', 'i.png'), ('text', ' '), ('html', '<!-- span x.y -->'), ('text', '1'),
                          ('html', '<!-- /span -->')])

    def test_an_image_inside_a_link_label_is_an_image(self):
        self.assertEqual(self.links('[![badge](missing.png)](target.md)\n'),
                         [('missing.png', 'badge', None, True, False), ('target.md', '', None, False, False)])

    def test_reference_definitions_are_reported(self):
        document = parse('[x][ref]\n\n[ref]: target.md\n')
        self.assertEqual(list(document.references), ['REF'])
        self.assertEqual(parse('[x][undefined]\n').links, [])


class HeadingTests(receipts.TestCase):
    def test_levels_text_and_where_headings_are_not(self):
        document = parse('''\
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
            ''')
        self.assertEqual([(h.level, h.text, h.line, h.atx) for h in document.headings],
                         [(1, 'Title', 0, False), (2, 'Sub', 3, False), (2, 'ATX code link', 6, True)])
        self.assertEqual([(h.level, h.text, h.line) for h in parse('```text\n<!--\n## fake\n```\n\n## real\n').headings],
                         [(2, 'real', 5)])

    def test_sections_end_at_the_same_or_a_higher_level(self):
        document = parse('# A\n## B\ntext\n### C\nmore\n## D\n# E\n')
        self.assertEqual(document.section('B').lines, (1, 5))
        self.assertEqual(document.section('A').lines, (0, 6))
        for text in ('## A\n\n## Other\n\nbody\n', '## A\n\n# Other\n\nbody\n', '### A\n\n### Other\n\nbody\n', '### A\n\n## Other\n\nbody\n'):
            with self.subTest(text=text):
                document = parse(text)
                section = document.section('A')
                self.assertEqual(section.lines, (0, 2))
                self.assertEqual([i.text for i in document.inlines if i.kind != 'heading' and section.holds(i.lines)], [])
        self.assertIsNone(document.section('Z'))
        with self.assertRaises(reader.Refused):
            parse('## B\n## B\n').section('B')

    def test_a_multi_line_setext_heading_anchors_without_the_break(self):
        document = parse('Foo\nbar\n===\n')
        self.assertEqual((document.headings[0].text, document.anchors), ('Foo bar', ['foobar']))

    def test_anchors_keep_underscores_and_number_duplicates(self):
        document = parse('## Test seam: `_test_overrides`\n## Repeated\n## Repeated\n## Ünïcode\n')
        self.assertEqual(document.anchors,
                         ['test-seam-_test_overrides', 'repeated', 'repeated-1', 'ünïcode'])
        self.assertEqual(reader.slug('One build in time'), 'one-build-in-time')


class TableTests(receipts.TestCase):
    def test_cells_hold_inline_content(self):
        document = parse('| A | B |\n| --- | --- |\n| `a\\|b` | [l](t.md) |\n| x | y |\n')
        table, = document.tables
        self.assertEqual([c.text for c in table.header], ['A', 'B'])
        self.assertEqual([[c.text for c in row] for row in table.rows], [['a|b', 'l'], ['x', 'y']])
        self.assertEqual(table.rows[0][0].code, ['a|b'])
        self.assertEqual(table.rows[1][0].lines, (3, 4))

    def test_a_table_in_a_comment_or_fence_is_not_a_table(self):
        self.assertEqual(parse('<!--\n| A |\n| --- |\n| x |\n-->\n\n```\n| A |\n| --- |\n```\n').tables, [])


class LineTests(receipts.TestCase):
    def test_lines_and_offsets(self):
        document = parse('a\n\nb\nc\n')
        self.assertEqual([i.lines for i in document.inlines], [(0, 1), (2, 4)])
        self.assertEqual([document.line_of(o) for o in (0, 1, 2, 3, 5)], [0, 0, 1, 2, 3])


class VendorTests(receipts.TestCase):
    def test_vendored_files_are_the_wheels_bytes(self):
        self.assertEqual(vendor_problems(), [])

    def test_a_changed_added_or_missing_vendored_file_is_named(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-vendor-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root, fixture_inputs.reader_inputs(ROOT))
        self.track_inputs(root)
        vendor = root / 'tests/lib/vendor'
        changed = vendor / 'markdown_it/rules_inline/html_inline.py'
        changed.write_text(changed.read_text() + '\n')
        (vendor / 'mdurl/extra.py').write_text('')
        (vendor / 'markdown_it/LICENSE.markdown-it').unlink()
        self.assertEqual(vendor_problems(root), [
            'markdown_it_py-3.0.0.RECORD: missing vendored file markdown_it/LICENSE.markdown-it',
            'markdown_it_py-3.0.0.RECORD: vendored file markdown_it/rules_inline/html_inline.py differs from the wheel',
            'mdurl-0.1.2.RECORD: vendored file mdurl/extra.py is not in the wheel',
        ])

    def test_a_rewritten_record_is_named(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-record-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root, fixture_inputs.reader_inputs(ROOT))
        self.track_inputs(root)
        vendor = root / 'tests/lib/vendor'
        changed = vendor / 'markdown_it/rules_inline/html_inline.py'
        changed.write_text(changed.read_text() + '\n')
        digest = 'sha256=' + base64.urlsafe_b64encode(hashlib.sha256(changed.read_bytes()).digest()).rstrip(b'=').decode()
        record = vendor / 'markdown_it_py-3.0.0.RECORD'
        rows = [row if row[0] != 'markdown_it/rules_inline/html_inline.py' else [row[0], digest, str(changed.stat().st_size)]
                for row in csv.reader(record.read_text().splitlines())]
        record.write_text(''.join(','.join(row) + '\n' for row in rows))
        self.assertEqual(vendor_problems(root), ['markdown_it_py-3.0.0.RECORD: not the RECORD of the verified wheel'])

    def test_only_the_reader_imports_the_parser(self):
        self.assertEqual(import_problems(ROOT, tracked_python(run=self.run_command)), [])

    def test_another_importer_is_named(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-importer-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.track_inputs(root)
        (root / 'a.py').write_text('import os\nimport markdown_it.main\n')
        (root / 'b.py').write_text('from mdurl import decode\n')
        (root / 'c.py').write_text('"""import markdown_it"""\n# from mdurl import x\nname = "markdown_it"\n')
        self.assertEqual(import_problems(root, ['a.py', 'b.py', 'c.py']), [
            'a.py:2: imports the Markdown parser; use docs/markdown_reader.py',
            'b.py:1: imports the Markdown parser; use docs/markdown_reader.py',
        ])


class ImportGuardTests(receipts.TestCase):
    """The parser loads only from the vendored copies, and linkify_it never loads."""

    def run_reader(self, root, env=None, before=''):
        script = (before + 'import sys; sys.path.insert(0, sys.argv[1]); import markdown_reader; '
                  'print(markdown_reader.parse("x").inlines[0].text)')
        return self.run_command([sys.executable, '-B', '-S', '-P', '-c', script, str(root / 'docs')], capture_output=True, text=True,
                              env=dict(os.environ, **(env or {})), timeout=60)

    def checkout(self, vendored=True):
        directory = tempfile.TemporaryDirectory(prefix='pw-markdown-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root, fixture_inputs.reader_inputs(ROOT) if vendored else ['docs/markdown_reader.py'])
        self.track_inputs(root)
        return root

    def stand_in(self, name, body):
        directory = tempfile.TemporaryDirectory(prefix='pw-stand-in-')
        self.addCleanup(directory.cleanup)
        package = Path(directory.name) / name
        package.mkdir()
        (package / '__init__.py').write_text(body)
        self.track_inputs(package.parent)
        return directory.name

    def test_the_vendored_copy_loads(self):
        result = self.run_reader(self.checkout())
        self.assertEqual((result.returncode, result.stdout), (0, 'x\n'), result.stderr)

    def test_a_missing_vendored_copy_is_refused(self):
        path = self.stand_in('markdown_it', '__version__ = "3.0.0"\nclass MarkdownIt: pass\n')
        result = self.run_reader(self.checkout(vendored=False), {'PYTHONPATH': path})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('the vendored markdown_it is missing from', result.stderr)

    def test_a_copy_already_imported_from_elsewhere_is_refused(self):
        path = self.stand_in('markdown_it', '__version__ = "3.0.0"\nclass MarkdownIt: pass\n')
        result = self.run_reader(self.checkout(), {'PYTHONPATH': path}, before='import markdown_it; ')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'markdown_it loaded from {path}', result.stderr)

    def test_an_already_imported_linkify_it_is_refused(self):
        path = self.stand_in('linkify_it', 'class LinkifyIt: pass\n')
        result = self.run_reader(self.checkout(), {'PYTHONPATH': path}, before='import linkify_it; ')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('linkify_it is already imported', result.stderr)

    def test_another_version_is_refused(self):
        root = self.checkout()
        init = root / 'tests/lib/vendor/markdown_it/__init__.py'
        init.write_text(init.read_text().replace('__version__ = "3.0.0"', '__version__ = "3.0.1"'))
        result = self.run_reader(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('markdown-it-py 3.0.1 loaded; 3.0.0 is vendored', result.stderr)

    def test_an_installed_linkify_it_is_never_imported(self):
        marker = Path(tempfile.mkdtemp(prefix='pw-linkify-')) / 'imported'
        self.addCleanup(shutil.rmtree, marker.parent)
        path = self.stand_in('linkify_it', f'open({str(marker)!r}, "w").close()\nraise SystemExit("linkify_it imported")\n')
        result = self.run_reader(self.checkout(), {'PYTHONPATH': path})
        self.assertEqual((result.returncode, result.stdout), (0, 'x\n'), result.stderr)
        self.assertFalse(marker.exists())


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/markdown_reader', 'markdown'))
