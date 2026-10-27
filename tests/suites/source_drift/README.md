# source_drift

Cross-checks the native source lists `meson.build` declares against the
tree. The test-only SwiftPM package (`runner/Package.swift`) follows
convention and auto-discovers the host's files (no `sources:` arrays to
drift), so the SwiftPM source set equals on-disk by construction; the
comparison that can actually ship a broken binary is meson.build vs the
tree. A file added under `Sources/PWRunnerCore/` but not wired into
meson.build (or vice versa) never reaches the production binary, and a
target pointed at a substitute file compiles that substitute, with no other
signal. The shared reader in `tests/lib/native_sources.py` reads the manifest
with `meson introspect meson.build --targets`, which needs no build directory
and lists every declaration regardless of the `xpc` option, refuses a target
name declared more than once (a dead declaration could otherwise stand in for
the live one), and pins every target: the host's core files plus the service
entry point, the shim's C files, and the client's, worker's, validator's and issuer's
single files. `build.sh` applies the same expectation to the configured
build directory after compiling, which reads what Meson actually evaluated.
Both check membership only; what the compiler does to those files is the
manifest's business, reviewed through its identity and the receipts. Failed
introspection is a script error, never a pass.

## Invariants

- The tree and meson.build's targets must agree on every compiled file set,
  compared as repository-relative paths: the `PWRunner` target carries the
  core files plus the service entry point, `PWCWorkerShim` the shim's C
  files, and `pw-runner-client`, `pw-probe-runner`, `sb_api_validator` and
  `pw-extension-issuer`
  their single known files. A missing, duplicated or unexpected target is
  named.
- Discovery is recursive under the target dirs
  (`Sources/PWRunnerCore`, `Sources/PWCWorkerShim`), so moving a file
  within a target is
  invisible here; only adding/removing a compiled file trips the diff.
- `runner/Tests/`, `runner/Clients/`, `runner/Services/`, and
  `runner/augments/` are managed separately and are not part of the
  source-set check.

The shared prediction-unavailable operation/filter set in `ProbeRunner.swift`
must agree with the user guide. `planValidatorQueries` uses that set;
independent runner unit tests pin its exclusion behavior.
The checker also requires `planValidatorQueries` to branch on the shared set's
`contains` call and rejects host-local pair collections, literal operation/filter
entries and shadowing of the shared symbol. Comments, string examples and uses
outside the planner cannot satisfy the membership check. This is a mechanical
source convention, not a Swift semantic analysis; a deliberate refactor of the
condition requires reviewing the guard alongside the runtime unit tests.

The host-source check covers Swift and C sources and headers under
`runner/Sources/`. It rejects direct calls/declarations and string-named
bindings to `sandbox_check`, `sandbox_apply`, `sandbox_compile_string`,
`sandbox_create_params`, `sandbox_set_param`, `sandbox_free_params`,
`sandbox_free_profile`, `sandbox_free_error` and the native extension
issue/consume/release functions. It also rejects `dlsym` of
those symbols and `dlopen` of literal libsandbox paths, including simple named
constants. Schema properties, comments, explanatory strings, unrelated dynamic
loads and C calling conventions are accepted. Controls exercise both groups.
Computed library/symbol names and complete Swift/C analysis are outside this
check. The companion [artifact check](../preflight/README.md) inspects the
shipped host's undefined symbols; the production C worker and validator retain
their sandbox API calls outside this source scope. Both checks look at symbols
and literal lookup forms rather than file paths because libsandbox is resident
in the dyld shared cache on a current macOS install: none of
`/usr/lib/libsandbox.dylib`, `/usr/lib/libsandbox.1.dylib` or
`/usr/lib/system/libsystem_sandbox.dylib` exists as a file, and the worker and
validator bind the library through the linker, so a path's presence or absence
says nothing about whether a process uses it.

The registry checks also compare catalog suite names with the suite directories
(every directory under `tests/suites/`) and the coverage table, require every
suite directory to have a README and every `run.sh` under one to be a case
command the catalog names, and require Baseline suites to have default catalog
cases. Planner controls add a suite script no case names, a suite directory
without a README and one the catalog lacks, and each is named; a Baseline
suite whose only case is nondefault is named, and the same suite with a
default case passes.

Two rules keep the one test interface the only one. No repository document may
show a case script as a command (`bash tests/suites/...`, `./tests/suites/...`,
a fenced script line, or a sentence telling the reader to run a script path; a
bare path in a code span is a location) or name the retired direct output
directory under `tests/out/runs/`; and the Makefile, `tests/accept-release.sh` and the
release helpers may name no `--suite`, `--case` or `--all` and may invoke
`tests/run.sh` only without arguments or with `--prune`. Planner controls add
each form to a document copy, a selector and an argument to the Makefile copy
and a selector to the acceptance copy, and require each to be named while a
location span and a comment pass.
Document discovery for the command rule is an explicit-root, pruned walk
through [repository_tree.py](../../../docs/repository_tree.py). The
command-document scope excludes `records/`, `dist/archive/`, `dist/evidence/`,
`tests/out/`, `.tmp/`, `builddir` (a prefix, so `builddir-old/` as well),
`controller/target/`, `tests/lib/vendor/` and `runner/.build/`, plus every
hidden path component, and removes those directories before descending; the
test-shell scope that `direct_python_start` uses covers `tests/**/*.sh` and
prunes only `tests/out/`. Neither scope follows a directory symlink. A matching
file symlink, a broken symlink or a directory named with the suffix remains a
candidate, so its read failure is reported rather than omitted. The prose and
link scope stays with `scanned_documents` in [generators.py](generators.py),
and generator-owned documents come from each generator's own declarations.
Inventory controls in both cases select an independently specified fixture
that includes nested and untracked files, prefix near misses, a root and a
nested `builddir`, hidden paths, the scope differences, each symlink kind, an
unreadable selected input and large excluded subtrees; an independent
instrument on directory enumeration shows that the excluded subtrees are never
entered and that the tree's own account agrees with it.
They also lock the `_test_overrides` key table in `runner/README.md` to the
stored properties of `PWRunnerTestOverrides`, since that table is the only
documented key list. Property/table agreement does not verify request admission
or decoding; integrated override cases exercise those boundaries.
Public-command controls separately verify selection and actual execution.

Dedicated rule controls remove a normalized-matrix row for an existing
`runner_outcome_*` suite, add a normalized-matrix row naming no constant, remove
and add attempt-matrix rows, add an attempt kind on either side, rename a Swift
case for a shared value, leave a numeric gap in the C enum, malform the C enum
(a precondition failure, status 2), add a test-seam row naming no property, add
a document-only prediction-unavailable pair and add an unknown landing path;
each is named, and every restoration passes.

Two rules read the handwritten text of `docs/ARCHITECTURE.md`: every
top-level paragraph opening with "Known gap" is indexed, in order, by the
bullets of the document's last section, which lists nothing else; every row of
the evidence-channels table names its landing paths as code, and each is a key
of the reply or envelope shape golden.
The `generator_contract` case holds the document graph's drift node to the
rules this script runs, and the form table below to the shared module's rules.

The Known gap rule covers ARCHITECTURE.md, BUILD.md and WORKER.md. Disposable
checkout controls add an unindexed gap, add its matching index entry, remove
the final heading and add a spurious index entry in each tour. Repaired and
restored copies pass; each rejected mutation names its document. Structure
controls hide a suite-coverage row, an outcome-matrix row, a test-seam row, a
prediction-unavailable bullet, the CLI usage block, a Known gap paragraph, the
evidence-channels table in comments, and each is reported; so
are an evidence row without a landing column and a numbered index entry.

### Workflow guidance and checked routes

Sandbox troubleshooting is available in `AGENTS.md`, `runner/AGENTS.md`,
`tests/AGENTS.md` and `docs/BUILD.md`. Each document explains the local workflow;
its wording and paragraph order are independent.

[`check_harness_guidance_routes`](check.py) requires exactly one nonempty
`Sandboxed automation harnesses` section in each document and links from the
root section to the other diagnostic sections. It reads each document through
[`docs/markdown_reader.py`](../../../docs/markdown_reader.py). Sections end at
the next heading of the same or higher level. Headings alone, comments, code
and other HTML cannot supply guidance; examples and images cannot supply a
route. The rule compares resolved paths and fragments, not link labels or
prose. A document the reader refuses is reported, and the other drift checks
still run.
G11 below also checks document links and their destination anchors.

The rule establishes presence and navigation, not the correctness or completeness
of the advice. Review the unchanged retry, signature-verification qualification
and limits on attribution when editing guidance.

The guidance check runs in `source_drift/runner_source_manifests_agree`, included
in the default battery. It is not a direct `build.sh` gate. Disposable-checkout
controls run the real checker: independent rewrites, paragraph reordering,
rewrapping, changed, code or wrapped link labels, routes on indented
continuation lines and routes in list content after a blank line pass; missing,
duplicated or empty sections and missing or incorrect root routes fail. Fake
guidance or routes in examples, comments or the wrong section fail, as do
routes indented after a blank line or heading, labels split by a blank line and
an inline comment containing `--`, which the reader refuses. Every touched input
is restored between controls and the restored documents must pass. Inputs and
command receipts are retained alongside the planner controls.

### Generator contracts

The `generator_contract` case in [generators.py](generators.py) holds these
invariants across the five generators. Per-generator cases retain their shape,
stale-copy, marker and build-refusal controls.

The limits manifest is a reviewed description; production code does not load
it. Every row cites a test or rule, and a value owner must be a test in the
generator's declared owner set. A check citation's `form` identifies the kind
of definition, while its `kind` distinguishes value, boundary and path
coverage. Admission rows carry `refusal_field`, the exact
`admission_failure.field` text, and each `control` begins with Fixed, Flag,
Derived or Not enforced.

`tests/lib/python.sh docs/generate_limits.py --check` validates the manifest, source and
check references, generated tables, copied guide sections and the guide's
internal links. The shared sections contain every limit and shared question
without requiring companion files or web pages. `--stage-guide PATH` performs
the same checks before copying the guide and refuses stale documents without
regenerating them. The build checks freshness before compilation and stages
the guide before packaging. These checks establish documentation consistency;
compiled-value and behavioral checks establish implementation agreement.

- **G1. One owner, nothing outside.** Every region (including an authored
  scalar span) and whole-file output has exactly one generator, which changes no byte outside them. A document holds
  each marker pair once, in order; a broken pair stops the generator before
  any write.
- **G2. Idempotence.** A second run immediately after a first writes nothing.
- **G3. Check mode before signing.** Every generator has `--check`, which
  writes nothing and exits nonzero on any stale copy, and the build runs
  every generator's check before signing.
- **G4. Citations resolve.** Every citation names a repository-relative file
  that exists and a symbol that occurs in it.
- **G5. Check citations have a form and a definition.** Every check citation
  in every manifest carries a form. A `test` is defined in the cited file, in
  that file's language; a `rule` is a drift-rule function; a `control` is a
  fixture, golden, helper or compiled C control a test compares against.
  Worker-capability rows may have an empty check list, rendered as source-only
  support. Each of their check citations names its reviewed assertion scope;
  the generator requires nonempty scope text but does not verify its relevance.
  Other nodes and edges, limits, and nonempty worker check lists cite at least
  one `test` or `rule`. A common word that merely occurs in a file cannot
  satisfy a `test`.
- **G6. No self-citation.** A manifest cites neither itself nor any region or
  whole-file output of its own generator, since the generator would then
  verify text it wrote.
- **G7. Declared vocabulary.** A graph declares the fact keys its nodes and
  edges may use, in column order; an undeclared or unused key is an error.
- **G8. Durations and sizes render from limits.** The architecture manifest
  states a duration or size only through a limit placeholder; a literal one
  anywhere in the manifest is an error.
- **G9. Counts and values reach prose through spans.** A span is owned by one
  generator, rendered from its manifest, checked for a stale value or an
  unknown name, and authored outside every region; a copy region carries it
  as bytes. Prose does not restate arithmetic over a spanned value.
- **G10. Captions state the verified guarantee.** A generated caption or
  summary says what the generator verified about citations, presence and
  definition, and nothing stronger; it never says a test exercises, covers or
  proves a row.
- **G11. Prose citations use the rendered form and are verified.** A drift
  rule verifies, in every Markdown document it scans, the symbol behind each
  link whose text is a backticked symbol and whose target is not Markdown,
  and resolves every `#anchor` against the target's headings.

For G9 and G11, distinguish implementation of the mechanism from its prose
coverage. The baseline records sites outside each mechanism; coverage is
complete when the baseline's entries for that invariant are empty.

G1 through G8, G10 and G11 have complete coverage in this scan. G9 has a
working mechanism and partial prose coverage: the remaining sites live in
[prose_baseline.json](../../fixtures/docs/prose_baseline.json). The case reports
entries per invariant, zero included. Convert a site to a span or a symbol-form link and remove
its baseline entry in the same change. Counts without a mechanical pattern
are surveyed manually; their exact text must remain present until converted.
Literal and citation-pair entries must match the scan exactly, including
repeated occurrences. Review any baseline addition as added unverified prose.
Release preflight refuses additions or rewritten entries against the nearest
annotated release tag reachable before HEAD; if that release predates
the baseline, it reports that fact. `--report` turns a growth refusal into a
warning. This baseline is retained even when empty.

The prose scan includes `docs/*.md`, root `README.md` and `AGENTS.md`,
`controller/AGENTS.md`, `runner/AGENTS.md`, `tests/README.md`, `tests/AGENTS.md`,
and every Markdown document a generator writes. It reads each document through
[`docs/markdown_reader.py`](../../../docs/markdown_reader.py), so fenced and
indented code, comments and other HTML are not prose. A literal site is a
source line of a paragraph, heading, list item or table row, with span values
blanked. A citation pair is a backticked identifier followed by a link to a
code file that holds it, in one paragraph, heading or table cell with no
sentence end, `|` or other link between them; it is recorded as
`` `identifier` … [label](target) ``. A span marker in a scanned document sits
in a paragraph, list item or table cell, opens and closes there, and belongs to
a generator that names the document. Authored spans are processed in the
documents each generator names in its `SPAN_DOCUMENTS`. The guide receives span comments
and values only by copying its shared source. Other generated or copied
regions are opaque to the span pass. A backticked link label into a non-Markdown
file denotes a symbol; use a plain filename label for an ordinary file link.
Local links must resolve, and reference-style links are refused.

The architecture manifest uses schema version 3; limits uses schema version 2.
Each architecture graph may select a registered document, defaulting to the
manifest destination. ARCHITECTURE.md and WORKER.md are registered; unknown or
escaping destinations, duplicate output ownership and misplaced markers refuse
generation. All destinations validate and all figures render before any write.
A cluster may position its label at the top or bottom to keep crossing edge
labels legible; omitted positions preserve the existing top placement. Check citations carry
`form` (`test`, `rule`, `control`); the limits `kind` (`value`, `boundary`,
`path`) is independent. Python definitions and drift-rule calls are checked
through the AST; Rust, Swift and shell definitions use the documented source
conventions, with suite-owned catalog case IDs also accepted. These checks
locate definitions, not test assertions. The shared helpers live in
[generator_common.py](../../../docs/generator_common.py).

| Form | Allowed files | Definition convention |
| --- | --- | --- |
| `test` | `tests/suites/**`, `runner/Tests/**`, or Rust sources with `#[test]` | Python function; Rust function within three lines after `#[test]`; Swift function or run label ending in a colon; shell `test_selected` or `PW_TEST_ID`; or a case ID in the cited file's owning suite in `tests/catalog.json`. |
| `rule` | `tests/suites/source_drift/*.py` | Python function with a call from `main()`. |
| `control` | `tests/fixtures/**`, `tests/lib/**`, `build.sh`, or C sources under `tests/` | Symbol presence; Python functions and C function-line definitions are required in those languages. |


Graphs declare ordered `node_facts` and `edge_facts`; every declared key must
be used, and every used key declared. Architecture durations and sizes use
`{limit:<id>}` placeholders, resolved through the limits loader and formatter.
The same values reach table cells and dot tooltips, and therefore SVG stamps.
Architecture exposes `graphs`, `nodes`, `edges`, `unpinned`, and per-graph
`<graph>.nodes`, `<graph>.edges`, `<graph>.kinds.<kind>` and
`documents.<lowercase-document-stem>.graphs` spans. Limits exposes `<id>.value`,
`<id>.value_unit` and, for a byte limit that is a whole number of MiB or KiB,
`<id>.binary`. Author a span outside generated/copied regions; a document may author the
same name in more than one sentence:

```html
<!-- span architecture.graphs -->4<!-- /span -->
```

The ownership control mutates inputs in disposable checkouts and compares all
files outside declared regions and whole-file outputs. Deliberate outside
writes, unresolved placeholders, invalid definitions, malformed markers,
stale spans, broken links, unlisted prose and release growth must be detected.
Refused commands must leave the checkout unchanged. Guide staging is tested
as a whole-file output, including idempotence; SVG rendering failure is checked
before any output publication.

### Markdown reader

[`docs/markdown_reader.py`](../../../docs/markdown_reader.py) is the only code
that imports the vendored markdown-it-py 3.0.0 and mdurl 0.1.2 in
[`tests/lib/vendor/`](../../lib/vendor/README.md). It loads them only from that
directory and refuses another copy or version. It also keeps `linkify_it`
from loading, because markdown-it-py 3.0.0 constructs it whenever it can be
imported. The parser uses the CommonMark preset with tables and without
`text_join`, so escapes and entity references stay distinguishable from
literal text. The reader refuses an inline comment containing `--`: CommonMark
0.30, which the pinned parser implements, reads such a comment as text, while
GitHub hides it.

The `markdown_reader` case in [markdown.py](markdown.py) holds the reader to
hand-written expectations for fences, indented code, list content, comments,
links and images, headings and sections, anchors, tables and line ranges. It
runs the import guard against stand-in packages and a changed version,
compares every vendored file with its wheel's `RECORD` digest and refuses an
import of either package anywhere else.

## Success criteria

- The check script exits 0 and prints a one-line summary of how many
  files each manifest carries.
- Any disagreement fails the suite with one line per file naming the target
  that lacks or adds it, or the target that is missing, duplicated or
  unexpected.

## Fixtures

- Source-set checks read live files. Limits controls create disposable checkouts
  containing the actual generator, documents and referenced source files.
- Inventory controls build their own tree under the planner's output and in a
  temporary directory for the shell scope; the selected entries, entered
  directories and timings are retained as `inventory-controls.json`.
- Planner controls run the actual checker in a disposable checkout with a
  three-pair mirror, an extra fourth pair, inferred literal entries, shadowing,
  and missing/comment-only/string-only membership checks. Formatting and
  commented/string examples remain accepted. Inputs and command receipts are
  retained, and the restored fixture must pass. Additional mutations check
  native Swift bindings and C-shim calls/lookups, accepting explanatory text
  and unrelated native APIs. Manifest mutations drop a core file from or add
  a missing file to meson.build's host target, rename the host and shim
  targets, add a dead duplicate host declaration beside a live one missing a
  file, and point the worker at a substitute file; each must be named by the
  checker and the restored manifest passes. Configured-directory controls run
  `meson setup` with `xpc=false` on the copied checkout and require the
  build-time reading to pass unmodified and to name a substituted worker file.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`.

- `<run>/suites/source_drift/runner_source_manifests_agree/artifacts/check.log`
- `<run>/suites/source_drift/runner_source_manifests_agree/artifacts/planner-controls/`
- `<run>/suites/source_drift/runner_source_manifests_agree/artifacts/planner-controls/inventory-controls.json`
- `<run>/suites/source_drift/limits_documentation/artifacts/limits.log`
- `<run>/suites/source_drift/contract_versions/artifacts/contract.log`
- `<run>/suites/source_drift/architecture_documentation/artifacts/architecture.log`
- `<run>/suites/source_drift/build_documentation/artifacts/build-rules.log` and `build.log`
- `<run>/suites/source_drift/generator_contract/artifacts/generators.log`
- `<run>/suites/source_drift/markdown_reader/artifacts/markdown.log`

## Run

```
./tests/run.sh --suite source_drift
```

No build required; the manifest reader needs Meson on `PATH`, which the
catalog declares as equipment. The `limits_documentation` case checks
[docs/limits.json](../../../docs/limits.json), generated tables (the limits
tables and the failure contract's scenario matrix rendered from
`tests/fixtures/comparison/matrix.json`), the user guide's copied limits,
questions, comparison reading rules and extension status tables, and local documentation links. Controls exercise the real
generator command with stale, missing and altered content; preserve both source
files and an existing staged guide on rejection; and validate a staged guide
after removing its source checkout. Internal-anchor and companion-file checks
also reject defects introduced into the shared source, even when generation
would otherwise copy them consistently. A build control proves stale guide
content stops before signing or output creation. The suite does
not compare production constants: those checks belong to `runner_abi_layout`,
`runner_unit` and the Rust unit tests. See the
[documentation guidance](../../../docs/AGENTS.md#editing-limits-and-shared-guide-content)
and [limit-change verification guidance](../../AGENTS.md#verify-a-limit-change).

The `contract_versions` case checks [docs/contract.json](../../../docs/contract.json)
against every generated copy in code and documents, exercises the real generator in
a disposable checkout with changed, stale, broken-marker and malformed inputs, and
proves a stale copy stops the build before signing. The same case pins the
native builder check as `build.sh`'s first executable block, built from
builtins and the two `/usr/sbin/sysctl` probes ahead of the knobs, arguments,
tracked inputs, Python and SDK setup and the lock front end. Under a profile
that lets only bash and sysctl execute and denies Mach lookups, an unreadable
`hw.optional.arm64` beside a bad knob, an unknown argument and an invalid
`SDKROOT` yields the builder refusal as the only output; the same native shell
without that rule passes the check and meets the knob refusal; and a probe the
profile forbids to execute names both failed probes instead of exiting under
`set -e`. Compiled values are compared elsewhere: `runner_abi_layout` (C), `runner_unit` (Swift) and the Rust unit tests.
See [docs/CONTRACT.md](../../../docs/CONTRACT.md).

The `architecture_documentation` case checks
[docs/architecture.json](../../../docs/architecture.json) against the dot
files, SVG stamps and generated table regions of
[docs/ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) and
[docs/WORKER.md](../../../docs/WORKER.md). The generator refuses
a node or edge whose cited source file or symbol does not exist, or whose
check lacks an allowed definition and form; controls exercise broken
citations, unknown references, duplicate ids, stale dot text, a stale table, a
stale SVG stamp, regeneration without Graphviz, idempotence and refusal before
any write. Routing controls move a graph between documents, test stale copies
in both destinations and reject misplaced or broken second-document markers.
The ownership control fails rendering on the last graph after earlier renders
have completed with controlled SVG text (no Graphviz prerequisite), and requires both documents and every figure to remain unchanged.
An SVG is checked by the stamp naming the hash of its dot text, so
the check needs no Graphviz; rendering does.

The `build_documentation` case checks [docs/build.json](../../../docs/build.json)
against the dot file, SVG stamp and generated table regions of
[docs/BUILD.md](../../../docs/BUILD.md), and runs the grounding rules in
[build_rules.py](build_rules.py), which parse `build.sh` and compare its
banner order with each step's fresh-mode condition, refusal messages,
statuses and steps, knob values, signing calls and helper invocations with
their subcommands with the manifest, compare the Makefile's build entry, the
Meson assertion family (one manifest row carrying the shared message
template and every asserted option in `meson.build`'s order) and the signed
inventory (against `EXECUTABLES`, the evidence generator and the README), and
require the baseline in `tests/fixtures/docs/build_baseline.json` to list
exactly the refusals without a behavioral or helper control. Controls mutate
a disposable copy of the script (a reordered or removed banner, a banner
moved out of its fresh-mode condition, an added, removed or moved refusal, a
changed status, a renamed knob, a removed or moved signing call, a moved
helper, a changed helper subcommand), its neighbours (a Meson option added,
removed or reordered, the family's template, the Makefile's build banner, the
three inventories, the baseline) and the forms the parser refuses (a banner
in a function, a refusal without an exit, an elif, an unknown codesign form),
and each must be named by its rule. The per-option Meson control poisons
every asserted option in turn and requires the next regeneration to refuse it
by name; a bypass control removes one assertion from a disposable copy of
`meson.build` and shows that option's control failing while the rule names
the option. The output-target control gives Meson an x86_64 macOS host
through a cross file and requires setup to refuse it by name, refuses at the
regeneration of a copy configured for x86_64 before the assertion existed and
before anything compiles, and shows the setup succeeding and the rule naming
the missing row when the assertion is removed, and naming a changed host
requirement. Agreement is textual: it does not establish that a refusal fires
or precedes the operation it protects; the manifest's behavioral and helper
citations and the baseline carry that distinction, and release preflight
refuses a grown baseline.

The same case checks the generated host/worker source identity and exercises
relocation, deterministic regeneration, stale generated values, malformed
markers, automatic helper discovery, layout edits and both handshake edits.
The identity changes on protocol implementation edits even when geometry does
not change. Runtime mismatch refusal is covered by `runner_c_worker_harness`
and the `runner_unit` host-driver control.

### Direct Python ancestry

`direct_python_start` checks the Python commands in `build.sh`,
`tests/lib/checkout_lock.sh`, `tests/run.sh`, `tests/lib/python.sh`,
`tests/accept-release.sh` and the Makefile, refusing `/usr/bin/python3`,
`env python3` and bare `python3` invocations. It also requires the three
build-control wrappers to start with `#!/usr/bin/env -S ${PW_PYTHON} -B`.
Disposable copies with each forbidden invocation or a changed wrapper line
must fail; restored copies and comments pass. Leaf Python scripts are outside
this check. Its shell inventory is the pruned test-shell scope described under
the invariants, checked against a fixture of its own. Runtime preservation and contained resolver refusals belong to
`preflight/build_provenance_controls` and `contract_versions`.
