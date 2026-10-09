# Build document and assessment plan

This plan builds `docs/BUILD.md`. It is committed so the work can span
sessions, and it is deleted at closeout. Nothing permanent links here: not the
README, not an AGENTS router, not the build document itself. When the plan is
gone, the repository reads as though it never existed.

Writing the document is also an assessment of the build. Reconcile the
promises in existing documents, the implementation, and observed behavior;
where they disagree, investigate and adjudicate the disagreement before
changing the account or the build. A mechanically current document is not
enough if it explains a bug as intended behavior or claims a guarantee the
checks do not establish.

Started 2026-10-08, after the Meson cutover and its audit repairs, at
v0.2.7 plus the commits on main since that tag.

## Status

- [x] Step 0: survey the build as it stands (2026-10-08; the register below
  is the survey's record)
- [ ] Step 1: assess claims, probe uncertainties, adjudicate findings
- [ ] Step 2: carry out and revalidate the adjudicated changes
- [ ] Step 3a: the manifest, generator, figure, drift case and controls, from
  the script
- [ ] Step 3b: the prose, from the script and the manifest
- [ ] Step 4: challenge the draft's claims and review with a human
- [ ] Step 5: integrate, move the build sections out of the signing document,
  verify, close out

Steps 1 and 2 recur during drafting and review. Their boxes record completion
of the initial pass; later findings remain open in the register until their
own evidence, decision and validation are complete.

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

The survey assembled each of the following from two or more places. These
are candidate claims to verify, not conclusions of an executed audit. The
document's job is to state the adjudicated account in one place, generated
where possible.

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

## Working method: assess, probe, adjudicate, change, recheck

Treat documentation work as a source of hypotheses about the build. The
initial register is a starting set, not the assessment's boundary. Follow
contradictions and unproved claims found in the script, manifests, tests,
draft or probe results, including build-process bugs that would remain even
if every document were removed. Prior audit repairs are relevant leads;
recheck them against the current revision before relying on them.

Keep three kinds of evidence distinct:

- **Mechanical grounding:** a symbol or test definition exists, a table
  matches parsed script text, generated regions are current. This detects
  specific forms of drift; it does not prove execution order or behavior.
- **Assertion coverage:** reading a cited check shows what it actually
  asserts, in which configurations, and what it leaves untested. A test's
  name or a successful run of its suite is not sufficient coverage evidence.
- **Observed behavior:** a recorded probe reaches the relevant path and
  observes the promised effect or refusal. Its conclusion is limited to the
  revision, inputs, environment and build-directory state exercised.

For each finding, move through `open -> investigating -> awaiting adjudication
-> implementing -> validating -> closed`; a documentation-only resolution
may skip implementation of code, but still needs validation. An accepted
limitation can close the investigation while remaining an explicit gap in
the document. A blocked probe stays unverified, with the missing prerequisite
recorded. Reopen a finding when new evidence contradicts its decision or a
change invalidates the evidence on which that decision rested.

Keep decisions and supporting evidence together under the register's row id.
Use a detail entry for each investigated row rather than widening the table:

- Claim, source of the expectation, affected build variants and consequence
  if false; classification as a documentation defect, build defect,
  evidence/coverage gap, supported behavior needing explanation, or no issue.
  A finding can have more than one classification.
- Source revision and local changes, implementing symbols, cited checks and
  their actual assertions; hypothesis and the observation that would refute
  it; exact probe inputs/command, expected and actual results, evidence path,
  and limits or blockers. Mark source-only conclusions as such.
- State, recommended disposition, human adjudication and rationale, scope of
  the authorized change or exact explanatory text, and affected claims to
  recheck. Record validation and any residual gap before closing the row.

The table summarizes findings; the details make them reviewable. Do not
discard a counterexample because the normal build or a broad suite passes.
Do not weaken a promise or expand a baseline merely to make the new document
and tests agree. Those are substantive decisions to adjudicate.

## Sequence

### Step 0: survey (done)

Read `build.sh`, `meson.build`, `meson.options`, the Makefile,
[SIGNING.md](SIGNING.md), [AGENTS.md](../AGENTS.md), the identity generator
and its contract section, `tests/lib/native_sources.py`,
`tests/lib/meson_receipts.py`, `tests/build-evidence.py`, and the build
controls under `tests/suites/source_drift/`. Nothing was executed for the
survey. The register below is its record, not runtime verification. At the
start of execution, record the current revision and worktree state and
refresh claims affected by changes since this survey.

### Step 1: assess, probe and adjudicate

For each candidate claim, trace the promise to the implementing branch and
the asserted check. Separate a confusing explanation from a wrong operation,
an unenforced promise or an intentional trust boundary. Prioritize claims
whose failure could compile, copy, sign or describe the wrong artifact, then
refusal ordering, variant coverage and documentation ownership.

Where inspection cannot settle a material claim, design a discriminating
probe before proposing a fix:

1. Write the expected result and the observation that distinguishes the
   competing explanations. For a refusal, identify both the diagnostic and
   the operation it must prevent; a nonzero exit alone proves neither.
2. Choose the smallest relevant cases. Consider full and `BUILD_XPC=0`
   builds, both inspection settings, fresh and reused build directories,
   direct native compilation and the public `make build` path, and relevant
   environment overrides. Exercise the dimensions that can change the
   claim; do not require an indiscriminate product of every setting.
3. Use disposable copies for source mutations or poisoned build state, and
   preserve the user's existing artifacts. Pair the adverse case with a
   valid control so that an unrelated prerequisite failure cannot masquerade
   as the promised guard. Inspect effective commands or output artifacts
   where the claim concerns what was compiled, copied or signed.
4. Record the result, including which path was reached and whether the
   protected side effect occurred. An unrelated harness, keychain or
   toolchain refusal blocks that observation; it does not exercise the
   intended guard. Follow the
   repository's harness rerun guidance when it applies. Use fresh managed
   test output and the checkout-lock/retention rules in
   [tests/README.md](../tests/README.md); do not run competing batteries in
   the same checkout.

Bring the evidence, its limits, and a recommended disposition to the human.
Adjudicate the intended behavior and scope before changing build semantics;
the present implementation is evidence of what happens, not by itself the
authority for what should happen. The agent should also say when evidence
does not establish a defect.

Dispositions:

- **Correct or clarify documentation:** behavior is accepted; change the
  inaccurate claim or state the missing boundary. Record the owning document
  and proposed wording. A footnote is one possible form, not a verdict that
  the implementation is sound.
- **Fix the build:** evidence establishes a defect against an adjudicated
  expectation. Record the behavior to restore, scope and acceptance check;
  implementation happens in step 2. Awkward prose alone is not a reason to
  redesign the build.
- **Strengthen verification:** behavior may be correct but the cited guard,
  test or observation does not establish it. Record the missing assertion or
  control, without calling unobserved behavior verified.
- **Accept a limitation or defer work:** record the consequence, rationale,
  owner or follow-up destination, and the bounded claim the document can
  make. A shortfall against a stated promise becomes a Known gap; an
  intentional trust assumption is explained as an assumption.
- **No issue:** retain the row with the evidence and reason that resolved it.

Dispositions may be combined, for example a build fix plus a regression
control and corrected prose. Routine investigation and work within an
already adjudicated scope proceed under the existing authorization; bring
new behavior choices or expanded scope back for adjudication. The initial
pass ends when every survey row has a supported disposition or an explicit
unresolved question with its next action. An unresolved question does not
count as an accepted limitation.

### Step 2: implement and revalidate adjudicated changes

Carry out each adjudicated change as a reviewable unit. For a build defect,
retain the failing reproduction, make the scoped fix, and add a durable
regression control where it protects meaningful behavior. Check that the
control distinguishes the original defect from the corrected behavior; do
not derive its expected result solely from the new manifest or implementation.
Documentation-only corrections need an evidence readback and applicable
documentation checks, not a new runtime test for every sentence.

Re-run the decisive probe and its valid control against the changed revision,
then the gates its files require: the maintenance checklist in
[AGENTS.md](../AGENTS.md), the `source_drift` suite, a rebuild and the default
battery when `build.sh`, `meson.build`, `meson.options` or the Makefile changes.
Revisit dependent claims, variants and earlier decisions affected by the
change; a green broad suite does not replace the specific reproduction.
Record the validation and residual limits, then update the manifest and prose
to describe the resulting behavior. Unexpected results return to step 1.

Independent document work can proceed while a finding is investigated.
Keep dependent wording provisional until the finding is resolved; no final
table or guarantee may present an intended fix as current behavior.

### Step 3a: manifest, generator, figure, drift case and controls

Build the machinery before the prose, from the script and the adjudicated
claims. Its design is subject to the same assessment loop: a parser that
cannot substantiate a promised grounding rule is a finding, not a reason to
overstate what the generator checks.

- **Manifest.** `docs/build.json`, reviewed, owning the document's structured
  account of the facts; it does not define correct build behavior. Steps in
  order, each with an id, its banner text, what it reads, what it writes and
  the refusals that can stop it. Refusals, each with its message prefix, the
  step it protects, the exit status and the check that exercises it. Knobs,
  each with its accepted values and what each value maps to. The signing
  list in order, with the entitlements file where one applies. The checks the
  build invokes, with the step before which each runs. Applicable branches
  and variants are explicit, including the partial bundle. The trust
  boundaries as facts on the directories they concern. Every item cites a
  source symbol and a test or rule in the citation form the other manifests
  use, so G4, G5 and G6 apply unchanged. Identify whether the cited assertion
  checks textual grounding or behavior; record missing behavioral coverage
  in the baseline below. A grounding citation cannot fill that coverage gap.
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
  the `sign_macho` and `codesign` calls, including loop expansion and branch
  scope, match the signing table in order and cover the appropriate executable
  inventory for each variant; distinguish executable signatures from bundle
  seals when comparing with `EXECUTABLES` and the README; the knob names and
  accepted values match; every generator and check the manifest names is
  invoked at the step it names. Each rule names the differing item. State
  the parser's supported forms and reject forms it cannot account for.
  Matching banners, error strings or call sites establishes textual
  consistency, not that a guard runs or precedes its protected side effect.
  Use behavioral controls for those claims, or identify the coverage gap.
- **Behavioral coverage baseline.** Each refusal row either cites a control
  that produces it or is listed as uncovered in a committed baseline that
  the rule refuses to see grow, as the prose baseline works. Apply the same
  treatment to other behavioral claims with missing controls, so textual
  grounding cannot conceal missing verification. The controls the survey
  identified (stale documents, a non-Developer-ID identity, the configured
  source and closure checks, the knob and Ninja guards) cite directly;
  the refusals exercised only by hand
  during the migration (the native policy refusals through `make build`, the
  partial bundle) are candidates for the first baseline entries to retire;
  reassess their current coverage in step 1. Each baseline entry identifies
  the unproved claim, variant and planned control. A baseline entry records
  missing verification; it does not authorize a stronger guarantee.
- **Drift case.** `tests/suites/source_drift/build.py`, registered as the
  `build_documentation` case: manifest current, idempotent regeneration,
  stale-copy refusal, broken citations refused, the grounding rules, and
  mutation controls over a disposable copy of `build.sh` (a reordered banner,
  an added refusal, a removed signing call, a renamed knob) that each rule
  must name. Separately challenge behavioral controls with mutations that
  preserve the recognizable text but bypass a guard or move it after its
  protected operation. Choose these from the assessed claims and risks,
  record which control should catch each, and distinguish detection by the
  intended assertion from failure at an unrelated prerequisite. Route any
  missed claim back through adjudication; not every behavioral control needs
  to live in the documentation drift case.

Gate: `tests/run.sh --suite source_drift` with the new case green and the
generator contract green with five generators, plus the targeted behavioral
controls selected by adjudication. Passing mechanical checks alone does not
close findings about build behavior.

### Step 3b: draft the prose from the script

Write the document from `build.sh`, `meson.build` and the manifest, not from
the signing document. For every claim, name the symbol that implements it
and the check that covers it, in the verified link form, or state the
specific coverage gap. Match the strength of the wording to the evidence:
symbol presence is not an assertion, and an assertion about membership is
not proof of the bytes a compiler used. Explain operator prerequisites
separately from automatic enforcement.

Keep a drafting log keyed to register ids. A contradiction, surprising
implementation choice, missing assertion or needed qualification becomes a
new row marked "found while drafting" and goes through steps 1 and 2. Compare
against [SIGNING.md](SIGNING.md), [AGENTS.md](../AGENTS.md) and the relevant
contract sections as claims are drafted, not only when the draft is complete.
Resolve which account is correct before consolidating text. Counts and
values reach the prose through spans; durations and sizes through limit
placeholders.

### Step 4: challenge the draft and review with a human

Read in both directions: for each consequential draft claim, find the
implementation, inspect the actual assertions and review the observations;
then walk the build from its public entry point and look for operations,
inputs, branches and refusals the account omits. Challenge universal words
such as "every", "before" and "only", especially across partial builds and
reused directories. New counterexamples return to step 1 rather than being
edited away as prose problems.

Review the draft with a human alongside the register's decisions, remaining
uncertainties and changes made. Adjudicate newly discovered findings and
route fixes through step 2. A shortfall accepted for this document is written
as a paragraph opening with "Known gap" and indexed by the document's last
section, as the architecture document does. Ordinary trust assumptions need
clear boundaries rather than being mislabeled as bugs.

This phase ends when every material claim has a supported account or an
explicitly accepted limitation, each implemented fix has its validation,
and no unadjudicated finding could change the account being published.

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
- Reconcile the final register against the final revision: re-run targeted
  probes whose premises changed during integration and confirm the moved
  prose retains its qualifications. Carry earlier evidence forward only
  after confirming that the relevant code and assumptions still hold.
  Record actual checks and blockers; skipped or environment-blocked
  execution is not a pass.
- Confirm the document contains no change-history notes, no contract version
  numbers in prose, no enumerated bundle paths that duplicate the README's
  inventory, and no link to `records/`.
- Before deleting the plan, preserve useful reproductions, adjudications and
  validation in an associated investigation record under `records/`, following
  [records/AGENTS.md](../records/AGENTS.md). Identify revision and commands so
  conclusions survive loss of local logs; identify any gitignored evidence
  as local and retain managed output under the test retention rules where
  needed. Durable regression controls and the document's accepted gaps carry
  the ongoing obligations. Deferred work needs a named follow-up destination;
  unresolved questions cannot disappear with the plan.
- Delete this plan in the same change, or the next one, only after those
  closeout conditions hold. The build document must not cite it or the
  investigation record.

## Assessment register

Each row is a place where a parsimonious account needed a footnote during the
survey; later rows can capture any documentation, build or verification
finding. The Disposition column is empty until step 1. Evidence is what the
survey saw; verify it before deciding. Add the detail entries described in
the working method as rows are investigated. A disposition is a decision,
not proof that its implementation or validation is complete.

| # | Candidate issue | Where it shows | Survey evidence | Disposition | Wording, change scope or follow-up |
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
