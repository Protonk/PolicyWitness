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
entry point, the shim's C files, and the client's, worker's and validator's
single files. `build.sh` applies the same expectation to the configured
build directory after compiling, which reads what Meson actually evaluated.
Both check membership only; what the compiler does to those files is the
manifest's business, reviewed through its identity and the receipts. Failed
introspection is a script error, never a pass.

## Invariants

- The tree and meson.build's targets must agree on every compiled file set,
  compared as repository-relative paths: the `PWRunner` target carries the
  core files plus the service entry point, `PWCWorkerShim` the shim's C
  files, and `pw-runner-client`, `pw-probe-runner` and `sb_api_validator`
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
`sandbox_free_profile` and `sandbox_free_error`. It also rejects `dlsym` of
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

The registry checks also compare catalog suite names with suite directories and
the coverage table, and require Baseline suites to have default catalog cases.
They also lock the `_test_overrides` key table in `runner/README.md` to the
stored properties of `PWRunnerTestOverrides`, since that table is the only
documented key list, and keep the shared first paragraph of the sandboxed-harness
note identical across `AGENTS.md`, `runner/README.md`, `tests/README.md` and
`docs/SIGNING.md`, since that note is carried in four places on purpose.
Public-command controls separately verify selection and actual execution.

Three rules read the handwritten text of `docs/ARCHITECTURE.md`: every
paragraph opening with "Known gap" is indexed, in order, by the document's
last section, which lists nothing else; every landing path in the
evidence-channels table is a key of the reply or envelope shape golden; and
the principles list names the core ideas of `AGENTS.md`, lead-in by lead-in.
The `generator_contract` case holds the document graph's drift node to the
rules this script runs, and the form table below to the shared module's rules.

### Generator contracts

The `generator_contract` case in [generators.py](generators.py) holds these
invariants across the five generators. Per-generator cases retain their shape,
stale-copy, marker and build-refusal controls.

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
  Every node, edge and limit cites at least one `test` or `rule`. A common
  word that merely occurs in a file cannot satisfy a `test`.
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

The prose scan includes `docs/*.md`, the root README and AGENTS files,
`runner/AGENTS.md`, `tests/README.md`, and every Markdown document a generator
writes. It ignores fenced examples; authored spans are processed in the
documents each generator names in its `SPAN_DOCUMENTS`. The guide receives span comments
and values only by copying its shared source. Other generated or copied
regions are opaque to the span pass. A backticked link label into a non-Markdown
file denotes a symbol; use a plain filename label for an ordinary file link.
Local links must resolve, and reference-style links are refused.

Architecture and limits manifests use schema version 2. Check citations carry
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
`<graph>.nodes`, `<graph>.edges` and `<graph>.kinds.<kind>` spans. Limits exposes `<id>.value`,
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

## Success criteria

- The check script exits 0 and prints a one-line summary of how many
  files each manifest carries.
- Any disagreement fails the suite with one line per file naming the target
  that lacks or adds it, or the target that is missing, duplicated or
  unexpected.

## Fixtures

- Source-set checks read live files. Limits controls create disposable checkouts
  containing the actual generator, documents and referenced source files.
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
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/source_drift/runner_source_manifests_agree/artifacts/check.log`
- `<run>/suites/source_drift/runner_source_manifests_agree/artifacts/planner-controls/`
- `<run>/suites/source_drift/limits_documentation/artifacts/limits.log`
- `<run>/suites/source_drift/contract_versions/artifacts/contract.log`
- `<run>/suites/source_drift/architecture_documentation/artifacts/architecture.log`
- `<run>/suites/source_drift/build_documentation/artifacts/build-rules.log` and `build.log`
- `<run>/suites/source_drift/generator_contract/artifacts/generators.log`

## Run

```
./tests/run.sh --suite source_drift
```

No build required; the manifest reader needs Meson on `PATH`, which the
catalog declares as equipment. The `limits_documentation` case checks
[`docs/limits.json`](../../../docs/limits.json), generated tables (the limits
tables and the failure contract's scenario matrix rendered from
`tests/fixtures/comparison/matrix.json`), the user guide's copied limits,
questions and comparison reading rules, and local documentation links. Controls exercise the real
generator command with stale, missing and altered content; preserve both source
files and an existing staged guide on rejection; and validate a staged guide
after removing its source checkout. Internal-anchor and companion-file checks
also reject defects introduced into the shared source, even when generation
would otherwise copy them consistently. A build control proves stale guide
content stops before signing or output creation. The suite does
not compare production constants: those checks belong to `runner_abi_layout`,
`runner_unit` and the Rust unit tests. See the maintenance instructions in
[`docs/LIMITS.md`](../../../docs/LIMITS.md).

The `contract_versions` case checks [`docs/contract.json`](../../../docs/contract.json)
against every generated copy in code and documents, exercises the real generator in
a disposable checkout with changed, stale, broken-marker and malformed inputs, and
proves a stale copy stops the build before signing. Compiled values are compared
elsewhere: `runner_abi_layout` (C), `runner_unit` (Swift) and the Rust unit tests.
See [`docs/CONTRACT.md`](../../../docs/CONTRACT.md).

The `architecture_documentation` case checks
[`docs/architecture.json`](../../../docs/architecture.json) against the dot
files, SVG stamps and generated table regions of
[`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md). The generator refuses
a node or edge whose cited source file or symbol does not exist, or whose
check lacks an allowed definition and form; controls exercise broken
citations, unknown references, duplicate ids, stale dot text, a stale table, a
stale SVG stamp, regeneration without Graphviz, idempotence and refusal before
any write. An SVG is checked by the stamp naming the hash of its dot text, so
the check needs no Graphviz; rendering does.

The `build_documentation` case checks [`docs/build.json`](../../../docs/build.json)
against the dot file, SVG stamp and generated table regions of
[`docs/BUILD.md`](../../../docs/BUILD.md), and runs the grounding rules in
[build_rules.py](build_rules.py), which parse `build.sh` and compare its
banner order, refusal messages, statuses and steps, knob values, signing
calls and helper invocations with the manifest, compare the Makefile's build
entry, the Meson policy assertions and the signed inventory (against
`EXECUTABLES`, the evidence generator and the README), and require the
baseline in `tests/fixtures/docs/build_baseline.json` to list exactly the
refusals without a behavioral or helper control. Controls mutate a disposable
copy of the script (a reordered or removed banner, an added, removed or moved
refusal, a changed status, a renamed knob, a removed or moved signing call, a
moved helper), its neighbours (a Meson option, the Makefile guard, the three
inventories, the baseline) and the forms the parser refuses (a banner in a
function, a refusal without an exit, an elif, an unknown codesign form), and
each must be named by its rule. Agreement is textual: it does not establish
that a refusal fires or precedes the operation it protects; the manifest's
behavioral and helper citations and the baseline carry that distinction, and
release preflight refuses a grown baseline.

The same case checks the generated host/worker source identity and exercises
relocation, deterministic regeneration, stale generated values, malformed
markers, automatic helper discovery, layout edits and both handshake edits.
The identity changes on protocol implementation edits even when geometry does
not change. Runtime mismatch refusal is covered by `runner_c_worker_harness`
and the `runner_unit` host-driver control.
