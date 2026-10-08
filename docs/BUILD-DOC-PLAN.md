# Build document buildout plan

This plan builds `docs/BUILD.md`. It is committed so the work can span
sessions, and it is deleted at closeout. Nothing permanent links here: not the
README, not an AGENTS router, not the build document itself. When the plan is
gone, the repository reads as though it never existed.

Started 2026-10-08, after the Meson cutover and its audit repairs, at
v0.2.7 plus the commits on main since that tag.

## Status

- [x] Step 0: survey the build as it stands (2026-10-08; the register below
  is the survey's record)
- [ ] Step 1: triage conversation over the strain register
- [ ] Step 2: carry out the eliminations chosen in step 1
- [ ] Step 3a: the manifest, generator, figure, drift case and controls, from
  the script
- [ ] Step 3b: the prose, from the script and the manifest
- [ ] Step 4: review the draft with a human
- [ ] Step 5: integrate, move the build sections out of the signing document,
  verify, close out

## The document being built

`docs/BUILD.md` is the account of one build in time: what each step reads,
writes and refuses; the two knobs and what each governs per language; what
`meson.build` owns and what `build.sh` owns; the trust placed in the build
directories; the signing contract; the evidence the build embeds; and how the
build verifies itself. It does not ship. It does not supplant the
[user guide](PolicyWitness.md), which keeps its one sentence on the supported
macOS, and it does not replace [CONTRACT.md](CONTRACT.md), which keeps the
identity's definition, or [SIGNING.md](SIGNING.md), which keeps evidence,
notarization, release and the archives.

Today the build is described at three altitudes. [AGENTS.md](../AGENTS.md)
gives the fast path and the maintenance checklist; [SIGNING.md](SIGNING.md)
carries the build requirements, the fixed order of steps, the native compile,
the trust in the build directories and the signing contract, in prose that
grew during the Meson migration until it was the largest part of a document
titled for signing; the script itself and the comments in `meson.build` are
the micro account. What is missing is a single account that is generated from
the script where the script can be read mechanically, cited to a symbol and a
check everywhere else, and refused by a test when it drifts. That is the
document's job, and it is the same job [ARCHITECTURE.md](ARCHITECTURE.md)
does for a run.

Audience: a collaborator about to change `build.sh`, `meson.build`,
`meson.options` or the Makefile, and a reader trying to make the signing flow
do something it should not. The document is not a field reference, not a
contract, not a release procedure and not a test map; each of those exists
and is linked instead.

## What no single document states today

The survey assembled each of the following from two or more places. The
document's job is to state each in one place, generated where possible.

1. **The order of steps and the refusal that precedes each.** The script
   prints a `==>` banner at every step and an `ERROR:` line at every
   refusal; the signing document states the order in one paragraph and the
   refusals across several. Nothing ties the paragraph to the banners.
2. **The signing list.** `sign_macho` calls and two `codesign` invocations
   in `build.sh`, [`EXECUTABLES`](../tests/lib/artifact.py), the README's
   inventory under "What ships" and the evidence generator's walk must
   agree. [AGENTS.md](../AGENTS.md) says so; no check compares
   the script's list with the others.
3. **The knobs.** `BUILD_XPC` and `PW_INSPECTION` accept exactly `0` and `1`
   and map onto Meson's `xpc` and `inspection` options, `RUSTFLAGS` when it
   is unset, the dSYM step and nothing else. The mapping is in the script, the
   options' descriptions in `meson.options` and a paragraph in the signing
   document.
4. **What Meson owns and what the script owns.** The fixed native policy and
   the pinned minimum macOS live in `meson.build`; the plist's declaration,
   the per-binary check, the configured source and closure check, Cargo's
   environment and the dSYM step live in `build.sh`. The boundary is stated in
   comments on both sides.
5. **The checks the build runs and when.** Four generator checks before any
   compile, identity generation before Cargo, the identity check before
   signing, the configured source and closure check before assembly, the
   minimum-version check before signing, evidence after the helpers are
   signed and before the outer seal. Each is a line in the script and a
   sentence somewhere; the sequence is nowhere as a table.
6. **The trust boundaries.** `builddir/` and `controller/target/` are
   incremental and trusted like the checkout; the receipts record but do not
   attest; the identity covers two directories and the build checks the
   compile's closure against them; the validator is outside the identity by
   design. Stated across the signing document, the contract and the identity
   generator's docstring.
7. **The build's own inputs beyond the tree.** The git stamp, the supported
   macOS from the plist, the SDK that `xcrun --sdk macosx` reports,
   `DEVELOPER_DIR`, the keychain identity, and Cargo's stamp variables and
   deployment target. No document lists them together.

## Sequence

### Step 0: survey (done)

Read `build.sh`, `meson.build`, `meson.options`, the Makefile,
[SIGNING.md](SIGNING.md), [AGENTS.md](../AGENTS.md), the identity generator
and its contract section, `tests/lib/native_sources.py`,
`tests/lib/meson_receipts.py`, `tests/build-evidence.py`, and the build
controls under `tests/suites/source_drift/`. Nothing was executed for the
survey. The register below is its record.

### Step 1: triage conversation

A conversation between an agent and a human over the strain register. The
agent presents each row with its evidence and the available dispositions. The
human decides. The agent may recommend, and should say when it thinks a row is
not a strain at all.

Dispositions:

- **footnote**: the document states the fact as it is, in one or two
  sentences. Write the sentence into the register.
- **eliminate**: change the repository so the document need not mention it.
  Write a one-sentence scope into the register; the work happens in step 2.
- **not a strain**: strike the row with a reason.

Rules: no code changes during the conversation; new rows may be added; the
register in this file is the record of the decisions. Step 1 ends when every
row has a disposition.

### Step 2: eliminations

Carry out each "eliminate" row as its own change, with the gates its files
require: the maintenance checklist in [AGENTS.md](../AGENTS.md), the
`source_drift` suite, a rebuild and the default battery when `build.sh`,
`meson.build` or the Makefile changes. Do not begin step 3 until these land,
because the document describes current behavior and nothing else.

### Step 3a: manifest, generator, figure, drift case and controls

Build the machinery before the prose, from the script.

- **Manifest.** `docs/build.json`, reviewed, owning the facts. Steps in
  order, each with an id, its banner text, what it reads, what it writes and
  the refusals that can stop it. Refusals, each with its message prefix, the
  step it protects, the exit status and the check that exercises it. Knobs,
  each with its accepted values and what each value maps to. The signing
  list in order, with the entitlements file where one applies. The checks the
  build invokes, with the step before which each runs. The trust boundaries
  as facts on the directories they concern. Every item cites a source symbol
  and a check in the citation form the other manifests use, so G4, G5 and G6
  apply unchanged.
- **Generator.** `docs/generate_build.py`, registered as the fifth generator
  in the generator contract and reusing the architecture generator's graph,
  table, region, span and stamp rendering rather than copying it. It writes
  regions into `BUILD.md`: a dot figure of the steps in order, a step table,
  a refusal table and a signing table, each captioned with what was verified
  and nothing stronger. It has `--check`, and `build.sh` runs it beside the
  other generator checks before compiling.
- **Grounding rules.** Drift rules that read `build.sh` itself and compare
  it with the manifest, so the document cannot drift from the script without
  the suite saying so: the sequence of `==>` banners equals the manifest's
  step order; the set of `ERROR:` messages equals the manifest's refusals;
  the `sign_macho` and `codesign` calls equal the signing table in order and
  agree with `EXECUTABLES` and the README's inventory; the knob names and
  accepted values match; every generator and check the manifest names is
  invoked at the step it names. Each rule names the differing item.
- **Refusal baseline.** Every refusal row must cite a control that produces
  it. A refusal with no control is listed in a committed baseline that the
  rule refuses to see grow, as the prose baseline works, so the gap is visible
  until the control exists. The controls that exist today (stale documents,
  a non-Developer-ID identity, the configured source and closure checks, the
  knob and Ninja guards) cite directly; the refusals exercised only by hand
  during the migration (the native policy refusals through `make build`, the
  partial bundle) are the first baseline entries to retire.
- **Drift case.** `tests/suites/source_drift/build.py`, registered as the
  `build_documentation` case: manifest current, idempotent regeneration,
  stale-copy refusal, broken citations refused, the grounding rules, and
  mutation controls over a disposable copy of `build.sh` (a reordered banner,
  an added refusal, a removed signing call, a renamed knob) that each rule
  must name.

Gate: `tests/run.sh --suite source_drift` with the new case green and the
generator contract green with five generators.

### Step 3b: draft the prose from the script

Write the document from `build.sh`, `meson.build` and the manifest, not from
the signing document. For every claim, name the symbol that implements it
and the test that pins it, in the verified link form. Keep a drafting log. A
claim that needs a footnote, or has no pin, goes into the register as a new
row marked "found while drafting". After the draft is complete, diff it
against the signing document and [AGENTS.md](../AGENTS.md) for
contradictions and record those in the log. Counts and values reach the
prose through spans; durations and sizes through limit placeholders.

### Step 4: human review

Review the draft with a human. Settle any rows added in step 3 the same way
as in step 1. A row settled as "eliminate" at this point goes back through
step 2 before the document is finished. A shortfall the document must admit
is written as a paragraph opening with "Known gap" and indexed by the
document's last section, as the architecture document does.

### Step 5: integrate and close out

- Move the "Build", "Sandboxed automation harnesses" and "Native compile with
  Meson" sections and "What `build.sh` signs" out of [SIGNING.md](SIGNING.md)
  into the new document, leaving one pointer each; the harness note's copy
  moves with them, so the note stays in four places and the drift rule's
  file list changes with it. [SIGNING.md](SIGNING.md) keeps evidence,
  notarization, release and the archives.
- Add a router row in [AGENTS.md](../AGENTS.md) for the document, the
  manifest and the generator; a maintenance-checklist line (a changed step,
  refusal, knob, check or signing call updates `docs/build.json` and
  regenerates); and a line under the README's implementation details.
- Run every generator's `--check` and `tests/run.sh --suite source_drift`;
  rebuild and run the default battery, since `build.sh` gains a check.
- Confirm the document contains no change-history notes, no contract version
  numbers in prose, no enumerated bundle paths that duplicate the README's
  inventory, and no link to `records/`.
- Delete this plan in the same change, or the next one. The build document
  must not cite it.

## Strain register

Each row is a place where a parsimonious account needed a footnote during the
survey. The Disposition column is empty until step 1. Evidence is what the
survey saw; verify it before deciding.

| # | Strain | Where it shows | Evidence | Disposition | Footnote text or elimination scope |
| --- | --- | --- | --- | --- | --- |
| 1 | Three inventories must agree and nothing checks the script's | `build.sh` signing list; `EXECUTABLES` in `tests/lib/artifact.py`; README "What ships"; `tests/build-evidence.py` | [AGENTS.md](../AGENTS.md) says the three lists must agree and the preflight suite fails a build that does not match `EXECUTABLES`, but the script's `sign_macho` calls are compared with nothing. A helper copied but not listed for signing is caught only when the inspector runs. | | |
| 2 | A refusal carries one of two exit statuses | `build.sh` under `set -e` | The script's own refusals exit `2`; a generator check that fails propagates `1`. The build controls assert the specific status, so the document would either state both or the script would harmonize. | | |
| 3 | Build-time checks live under `tests/` | `tests/lib/native_sources.py`, `tests/lib/meson_receipts.py`, `tests/build-evidence.py` | `build.sh` invokes two of them as production steps and the receipts describe build provenance, yet all three sit in the test tree with the suites' helpers. The generators the build runs live under `docs/`. | | |
| 4 | The identity's place in the build order is owned twice | [CONTRACT.md](CONTRACT.md) "Internal host/worker identity"; `build.sh` | The contract says the build generates before compiling and checks before signing; the script does it; the signing document repeats it. Which document owns the ordering claim. | | |
| 5 | The Makefile carries a second prose account of the sequence | Makefile header comments | The header describes each target's sequence and boundaries in prose that no rule reads; the `release` recipe's comment and the signing document's procedure describe the same chain. | | |
| 6 | The partial bundle is a parallel output with weaker checks | `BUILD_XPC=0` in `build.sh`; the signing document | It passes evidence generation and packaging, fails the full inspector, cannot run specimens, and is called an iteration convenience. Every inventory and every refusal table must say whether it covers the partial bundle. | | |
| 7 | A parallel compile path for the validator | `controller/tools/sb_api_validator/build.sh` | Compiles the validator beside its source with `cc` and ad hoc-signs it with debug entitlements; its output is ignored and never enters the bundle. The signing document now says so; a build document must repeat or own it. | | |
| 8 | The harness note is carried in four places | [AGENTS.md](../AGENTS.md), `runner/README.md`, `tests/README.md`, [SIGNING.md](SIGNING.md) | The copy in the signing document says which build steps need an unsandboxed shell. Moving that copy into the build document keeps four copies; adding one would make five. The drift rule's file list names the copies. | | |
| 9 | Cargo's inputs are the one part of the build no manifest describes | `controller/build.rs`; `build.sh` | The stamp variables, `RUSTFLAGS` when inspection is on and the deployment target reach Cargo through the environment; `build.rs` declares the stamp variables for rebuilds and Cargo tracks the deployment target itself. Nothing in `docs/` lists them. | | |
| 10 | The receipts are described as a build artifact but produced by a test tool | `tests/lib/meson_receipts.py`; `tests/README.md` "Comparing native builds" | The signing document tells the reader what the receipt pairs and records; the tool that writes it is documented with the comparison tools under the tests README. A build document would describe it a third time. | | |
| 11 | The supported macOS is declared in two places and enforced in a third | `Info.plist`, `meson.build`, `build.sh` | The plist declares it, the manifest pins it, the script checks every shipped Mach-O against the plist and exports it to Cargo. The signing document says to change the plist and the manifest together; no rule compares the two declarations. | | |
| 12 | The steps a human must run are mixed with the steps the script runs | [SIGNING.md](SIGNING.md) "Build" and the release procedure | Toolchain resets after a compiler or SDK change, fresh directories, the keychain, and the unsandboxed shell are operator steps stated beside the script's automatic ones. The document needs a line between them. | | |

## Proposed shape of the document

Spine: one build in time, step by step, the way the architecture document
follows one run. Each step carries the same sidebar: what it reads, what it
writes, what refuses it and where that refusal is pinned.

Sections in order:

1. Why the build is shaped this way: a coherent signed specimen; the host and
   worker's exact source identity; every refusal before the step it protects.
2. Inputs beyond the tree: the git stamp, the plist's minimum macOS, the SDK
   and developer directory, the keychain identity, Cargo's environment, and
   the two build directories as trusted working state.
3. One build in time, with the generated figure and step table.
4. Refusals, generated: message, step, status, the control that produces it,
   or the baseline entry that admits none exists.
5. What Meson owns and what the script owns: the fixed policy, the two
   options, the pinned minimum, the configured source and closure check.
6. The signing contract, generated where it is a list: identity rules, the
   gates before any signature, the inside-out order, what is sealed but
   unsigned, what is never production-signed.
7. The evidence the build embeds and the receipts it can produce.
8. How the build verifies itself: the generator checks, the drift rules that
   read the script, the build controls, and what none of them establish.
9. Known gaps.

Size target: a third shorter than the architecture document. Current behavior
only.
