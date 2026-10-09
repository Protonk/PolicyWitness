# Audit prompt: the step 1 pass of the build document plan

You are auditing the initial pass of step 1 of [BUILD-DOC-PLAN.md](BUILD-DOC-PLAN.md),
recorded there under "Assessment register" and "Register details", before the
human adjudicates its sixteen rows. The pass was executed by one agent that
designed the probes and interpreted them; your job is to say, row by row,
whether the recorded evidence supports what the row claims and whether the
recommended disposition stays within that evidence. You are not re-surveying
the build, not adjudicating, and not fixing anything. Like the plan, this
file and your report are working material: nothing links them and they are
deleted with the plan.

## Revision and inputs

The pass ran at commit 209e11c on a clean tree; the register's step 1 content
is an uncommitted edit of the plan in the working tree. Read, in this order:

1. The plan's "Working method", "Step 1", the register table and every entry
   under "Register details". The dispositions there are recommendations, not
   decisions.
2. The sources the rows cite: `build.sh`, `meson.build`, `meson.options`, the
   Makefile, `controller/build.rs`, `tests/lib/native_sources.py`,
   `tests/build-evidence.py`, `tests/lib/artifact.py`,
   `docs/generate_worker_identity.py`, the build controls in
   `tests/suites/source_drift/contract.py`, `limits.py`, `generators.py`,
   `check.py` and `check_planner.py`, the "Build", "Native compile with
   Meson" and "What `build.sh` signs" sections of [SIGNING.md](SIGNING.md),
   and "Internal host/worker identity" in [CONTRACT.md](CONTRACT.md).
3. The evidence, which is local and disposable: `.tmp/probe-row1/`,
   `.tmp/probe-row1b/`, `.tmp/probe-row6/`, `.tmp/probe-row9/` and
   `.tmp/probe-row11/` (the clone probes: `run.sh`, `run2.sh`, `run3.sh`,
   their logs, the clone under `src/`, the copied checkout under `src2/` and
   the `dist-*` outputs), plus the two `source_drift` runs under
   `tests/out/runs/build-doc-step1-drift` and `build-doc-step1-drift-plan`.
   The plan transcribes the commands and the decisive outputs, so you can
   work from the plan alone if the scratch directories are gone.

## The standard to apply

Apply the plan's working method, not a general review. Keep mechanical
grounding, assertion coverage and observed behavior distinct. For a refusal,
the evidence must show both the diagnostic and the operation it prevented; a
nonzero exit proves neither. An adverse case needs its paired control, and a
conclusion is bounded to the revision, inputs, environment and build-directory
state exercised. The present implementation is evidence of what happens, not
the authority for what should happen: for every row that calls something a
defect, find the promise it fails, quote it from the document that makes it,
and say when the promise is actually the pass's own expectation. Say when a
finding is weaker than framed and when it is stronger.

## Questions, in priority order

### 1. The four rows that propose a build change: 16, 14, 13, 11

For each: does the recorded observation establish the claim at this
revision; which stated promise does it fail, or is it the pass's reading;
does the recommended disposition stay within the evidence, or does it decide
a design question the human should decide; what observation would refute it.
Then the specific challenges:

- **Row 16.** The scenario needed two steps: copying a checkout with its
  build directory, then clearing the Swift module cache. Judge its realism
  against the plan's own instruction to use disposable copies and the harness
  rerun guidance. Check whether `meson configure` accepting a copied directory
  is Meson-version-specific (Meson 1.12.1 here). Look for blind spots in the
  proposed refusal: path comparison through symlinks and `realpath`, a build
  directory that is itself a symlink, the same path with different contents,
  and what `meson setup --wipe` would do. Decide whether the root cause is in
  `build.sh` or in `native_sources.py --builddir`, which takes its root from
  `meson-info.json` rather than from the caller.
- **Row 14.** The pass corrected itself after writing the row:
  `release_archive.py` and `release_runs.py` compare the ZIP's `PWBuildCommit`
  and `PWBuildDescribe` with the tag, so a `-dirty` stamp is refused at the
  archive step, after the notarization submission and the battery. Confirm
  the exact point of refusal and whether anything earlier, such as
  acceptance, refuses too. Then weigh "defect" against the contract's explicit
  "generates … before compilation": is this a shortfall against a promise or
  a documented convenience with a late, expensive consequence?
- **Row 13.** The inference that "a real build would not show the manifest
  hash error" was not observed. Observe it: in a disposable clone, remove one
  `sign_macho` line and build with `DIST_DIR` under `.tmp/`; record whether
  evidence generation, the seal, the deep verify and
  `tests/lib/artifact.py` all pass with the helper left ad hoc-signed. Then
  judge whether a team-identifier check is the right local guard and whether
  it belongs in `build.sh` or in release acceptance, and whether the dSYM
  bundles or any other sealed content raise the same question.
- **Row 11.** The adverse cases ran only on reused directories and only at
  15.0. Say whether a fresh-directory adverse case or another value would
  change the conclusion. Check whether the proposed comparison of the
  `macos_minimum` literal with the plist can itself drift from the value
  Meson applies, and whether the source_drift rule or the `build.sh` step is
  the better owner.

### 2. Rows with noted limits: 1, 6, 9, 15

Check the limits the pass recorded and whether they weaken the row: the
ad hoc outer seals in the row 1 unsigned-helper probe; the row 6 specimen run
against a partial bundle built at an earlier commit rather than at HEAD; the
row 9 first series at an invalid version; the row 15 consequence, including
whether anything could silently use the remains.

### 3. Documentation rows: 2, 3, 4, 5, 7, 8, 10, 12

Verify the source facts only: line references, counts (24 refusal sites, 12
Makefile phase lines, 4 harness-note files, 5 signed Mach-Os), which rule or
file is cited, and whether the owning document named in the disposition is the
right one. Do not re-survey the prose.

### 4. Coverage: the first behavioral baseline

List every refusal in `build.sh`, every Meson policy assertion and every
behavioral claim the rows rely on that has no control producing it. One
discrepancy to confirm first: the plan's step 3a says controls exist for "the
knob and Ninja guards"; the pass found no test under `tests/` that mentions
`BUILD_XPC`, `PW_INSPECTION`, the "must be 0 or 1" message, `NINJA_MINIMUM`
or Meson's "fixed native policy" message. Candidates the pass did not probe:
the Meson policy refusals through `make build`, `PW_INSPECTION=0` (no dSYM,
`RUSTFLAGS` precedence), a reused `builddir` after a toolchain change,
missing `meson` or `ninja`, `sign_macho`'s non-Mach-O refusal, the
sandboxed-harness refusals, the release chain, the "no augments" warning path
and the `DIST_DIR` document copies.

### 5. Omissions

Walk `build.sh` forward once from `make build`, through every branch, write
and refusal, and name anything the register lacks that could compile, copy,
sign or describe the wrong artifact. Propose a row with a probe sketch for
each; do not investigate further.

## What you may and may not do

- Read anything. Run probes on disposable copies under `.tmp/`, reusing the
  clone under `.tmp/probe-row11/src` or making a new one with
  `git clone --local`. Never run `build.sh` against the repository's own
  `dist/` or `builddir/`; set `DIST_DIR` under `.tmp/` and build in a clone.
- Builds need `PATH=/opt/homebrew/opt/rustup/bin:$PATH` for Cargo and an
  explicit `IDENTITY` naming the Developer ID Application identity that
  `security find-identity -v -p codesigning` lists; signing has run
  unattended here. If a keychain prompt appears, stop and report.
- Rerun the `source_drift` suite into a fresh
  `PW_TEST_OUT_DIR=tests/out/runs/build-doc-audit1-<name>` if you need it;
  one battery at a time, under the checkout-lock rules in
  [tests/README.md](../tests/README.md). The sandboxed-harness note in
  [SIGNING.md](SIGNING.md#sandboxed-automation-harnesses) applies.
- Never notarize, release or publish. Do not modify tracked files other than
  your report; do not edit the plan (put corrections in the report); do not
  commit.
- Do not adjudicate, do not draft wording for `docs/BUILD.md`, and do not
  widen into steps 2 to 5.

## Report

Write `docs/BUILD-DOC-AUDIT-STEP1-REPORT.md` in the working tree, uncommitted,
with these sections:

1. **Revision and execution.** The commit you audited, every command you ran
   with its run directory or log path, and what you could not run and why.
2. **Rows 1 to 16.** One entry per row, keyed by its id, with a verdict from
   `supported`, `supported with limits`, `not supported` or `overreach`, then
   one paragraph: why; the promise quoted or its absence; the refuting or
   strengthening observation if you ran one; and the exact change you would
   make to the row's disposition line.
3. **Coverage baseline candidates.** A table: claim, variant, the control
   that would produce it.
4. **Proposed new rows.** Each with the claim, the consequence and a probe
   sketch.
5. **Corrections to the plan's text.** Factual errors you found, as exact
   old and new pairs.

Keep each row to a paragraph. The reader is a human about to decide sixteen
dispositions, not a reader of narrative.

---

# Step 1 audit report

## 1. Revision and execution

Audited on 2026-10-09. The assessed implementation is `209e11c`; the plan
updates are `47fe553` and `ca8b4d1`. The original audit prompt was committed
unchanged as `0e48cde` before this report was appended. `git diff
209e11c..0e48cde --name-only` lists only the plan and audit file: the build,
tests and permanent documentation did not change between those revisions.
The prompt's statement that the step 1 register is uncommitted is stale.
The user's current instruction supersedes the prompt's separate-report and
no-commit instructions: this report is appended to the original audit file.
No disposition has been adjudicated and no implementation has been changed
in the main checkout.

The material findings for adjudication are:

- Row 16 establishes a real wrong-checkout build, within the recorded
  Meson/toolchain conditions. Fixing only the diagnostic wording would not
  address it.
- Row 13's previously inferred real-build outcome is now reproduced: an
  omitted helper-signing call leaves an ad hoc helper that passes evidence
  generation, sealing, deep verification, and artifact inspection.
- Row 14 still has an incorrect release sequence after its correction.
  Strict preflight runs again after notarization/acceptance and before the
  battery. Identity regeneration itself is explicitly documented behavior;
  changing it is a design decision, not restoration of an existing refusal.
- The proposed coverage baseline is materially larger than the plan implies.
  Knob/Ninja controls are absent, and standalone checker controls do not
  establish build-script invocation or refusal ordering.

### Commands and evidence

All new build artifacts and probe logs are local, disposable evidence under
`.tmp/build-doc-audit1/`. They are not committed or represented as managed
test runs. The decisive results and reproduction instructions are retained
below so the report does not depend on those files surviving.

Read-only inspection used `git status --short`, `git log -3 --oneline --
docs/BUILD-DOC-PLAN.md`, `git show ca8b4d1 -- docs/BUILD-DOC-PLAN.md`,
`git show 47fe553 --stat`, and the revision comparison above. `cat`, `sed -n`,
`head`, `tail`, `rg -n`, and `rg --files` read the audit/plan, `.tmp/AGENTS.md`,
all source files named by the prompt, the relevant portions of
`docs/SIGNING.md`, `docs/CONTRACT.md`, `tests/README.md`, and additionally:

- `tests/lib/release_preflight.py`, `release_accept.py`, `release_archive.py`,
  `release_runs.py`, `meson_receipts.py`, `tests/accept-release.sh`;
- `tests/suites/preflight/check_signed_artifacts.py`, `check_release.py`,
  `check_release_publish.py`, `check_release_rotation.py`;
- `controller/src/run_flow.rs`, `runner_select.rs`, and runner-selection
  references; the manual validator build script and README inventory;
- the installed Meson 1.12.1 `mesonbuild/mconf.py` and `msetup.py` under
  `/opt/homebrew/Cellar/meson/1.12.1/lib/python3.14/site-packages/`.

The coverage search was `rg -n 'BUILD_XPC|PW_INSPECTION|must be 0 or
1|NINJA_MINIMUM|fixed native policy|sign_macho' tests`, with further searches
for `build.sh`, `RUSTFLAGS`, `MACOSX_DEPLOYMENT_TARGET`, Meson invocations,
test definitions, signing, and release-stamp checks. A first search named
nonexistent `tests/lib/release_acceptance.py`; it was corrected to
`release_accept.py`. A zsh glob for dispatcher release files matched nothing;
`rg --files tests/suites` located the actual preflight controls instead.
These search failures supplied no behavioral evidence.

Read the original `probe.log` files for rows 1, 1b, 6 and 9, and row 11's
`run.sh`, `run2.sh`, `run3.sh`, `probe.log`, `probe2.log`, `probe3.log` and
reported build results. Read row 6's actual `run.json`, whose nested
`result.error` contains the missing-runner diagnostic; the probe's first
summary had looked in the wrong JSON location. Python JSON readbacks of
`tests/out/runs/build-doc-step1-drift/run.json` and
`build-doc-step1-drift-plan/run.json` both show five selected/completed
cases, all passing, no skips or unrun cases. These are prior runs, not audit
reruns. Their passing results are not evidence for unasserted build behavior.

New execution, in order:

1. `security find-identity -v -p codesigning` returned zero identities inside
   the sandbox and one outside it: `Developer ID Application: Adam Hyland
   (42D369QV8E)`. `meson --version` returned `1.12.1`. The identity query was
   rerun with escalation as the repository instructs; no keychain prompt
   appeared.
2. `git clone --local . .tmp/build-doc-audit1/src` was blocked by sandbox
   restrictions on local Git object links, then succeeded with escalation.
   The fresh clone is at `0e48cde`; no main-checkout build directory or app
   was used as the build destination.
3. From that clone, ran the following control with escalation; exit 0:

   ```sh
   PATH=/opt/homebrew/opt/rustup/bin:$PATH \
   IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' \
   DIST_DIR=/Users/raccoon/Desktop/Security/PolicyWitness/.tmp/build-doc-audit1/dist-control \
   bash build.sh > ../control.log 2>&1
   ```

   This used fresh Cargo and Meson output directories, `BUILD_XPC=1` and
   `PW_INSPECTION=1` by default. The generated identity was
   `52f1dc03684878c6a4d2a3511454e4df06a82b4af73c52bb8723d71681d5771c`,
   and the stamp was `v0.2.7-40-g0e48cde`.
4. A Python edit in the clone asserted exactly one match and removed only
   `sign_macho "${APP_BUNDLE}/Contents/MacOS/sbpl-check"` from `build.sh`.
   Repeated the preceding command with `dist-adhoc` and `../adhoc.log`;
   exit 0. The build regenerated its three identity copies as expected
   because `build.sh` is a digest input; the resulting identity was
   `98f1e5ed5d8ac731e2cdd7b81a0a7f0612c7368cb82accb3a2d0031538702be5`
   and the stamp had `-dirty`. The only intentional source mutation was
   that removed signing call. This was a reused-directory adverse case.
5. From the main checkout, for each of `control` and `adhoc`, ran
   `/usr/bin/python3 -B tests/lib/artifact.py
   .tmp/build-doc-audit1/dist-<variant>/PolicyWitness.app
   .tmp/build-doc-audit1/<variant>-inspection.json`.
   Both sandboxed inspections failed signature validation. Repeated the same
   inspections outside the sandbox, against unchanged app bytes, writing
   `<variant>-inspection-unsandboxed.json`. Both returned 0, `ok: true`,
   no errors, and eight successful signature-verification receipts each.
   The first failures are environmental only on the strength of these
   successful unchanged-byte reruns.
6. A Python readback ran `/usr/bin/codesign -dvv` on each built
   `Contents/MacOS/sbpl-check`, compared its SHA-256 with its manifest entry,
   and checked ZIP existence. Saved `signers.json` and `summary.json`.
   The control has team `42D369QV8E`; the adverse helper reports
   `Signature=adhoc`, `flags=0x20002(adhoc,linker-signed)` and
   `TeamIdentifier=not set`. Both hashes match and both ZIPs exist.
   Both build logs reach evidence generation, outer seal, deep verification,
   guide staging and ZIP completion, with exit 0. No notarization was tried.
7. A minimal Meson path probe created `meson-paths/a/meson.build` containing
   `project('path-audit')`, ran `meson setup builddir` from `a`, copied the
   entire directory to `b` with Python `shutil.copytree`, ran
   `meson configure builddir` from `b`, then
   `meson setup --wipe builddir` from `b`. All three commands returned 0;
   arguments, working directories and outputs are in
   `meson-paths/commands.json`. The copied metadata named `a` after configure
   and `b` after wipe. This probe uses no compilers and establishes path
   selection only, not a second PolicyWitness wrong-byte reproduction.

No release, notarization, publication, live XPC run, full battery, or fresh
adverse minimum-version build was executed in this audit. None is claimed
as a pass. The existing wrong-checkout and minimum-version logs are adequate
for their bounded observations; the required row 13 observation was added.
Git staging/commit of the original prompt required escalation because the
sandbox could not create `.git/index.lock`; it changed only this audit file.
The report commit is likewise restricted to this file.

Final validation: ran `PW_TEST_OUT_DIR=tests/out/runs/build-doc-audit1-report
tests/run.sh --suite source_drift` from the main checkout after appending the
report. Exit 0; all five cases passed, with five completed, zero skipped and
zero unrun in `tests/out/runs/build-doc-audit1-report/run.json`. This managed
output is retained in place under the usual test-output rules. `git diff
--check` passed. A Python byte-prefix comparison with `git show
0e48cde:docs/BUILD-DOC-AUDIT-STEP1.md` confirmed the original prompt's bytes
are unchanged. `git status --short` showed only this audit file modified.

## 2. Rows 1 to 16

**1 — supported with limits.** The inventories are not compared by a durable
rule, and the detailed correction to the survey is right: the unsigned nested
helpers were refused while sealing, whereas ad hoc nested helpers could seal
and verify. The ad hoc outer seal limits the unsigned-helper experiment to
that signing configuration; it is not a Developer ID reproduction of that
particular refusal. The separate Developer ID rerun in row 1b and this audit's
real build strengthen the ad hoc result. The promise is AGENTS.md's “The
inventory lives in three places, and they must agree,” expressed there as an inventory
maintenance rule, not an existing automated comparison. There are five
embedded `sign_macho` calls, plus a sixth standalone-observer call; the app
and service mains are signed by their bundle seals. The evidence generator
has three explicit top-level helper names and a service-directory walk,
not another seven-element constant. Replace the disposition line with:
“Strengthen textual inventory verification, distinguishing five embedded
helper signatures, two bundle/main signatures and the standalone observer;
correct the unsigned/ad hoc distinction; behavioral signer enforcement
remains row 13.”

**2 — supported.** There are 24 explicit `ERROR:` sites in `build.sh`, all
exiting 2, but propagated command failures have more than two statuses.
The cited contract/limits controls actually assert 2 for wrong identity class
and 1 for stale copies; the logs record Cargo 101, Ninja 1 and the minimum
check's 2. No promise requires harmonized status codes. The stale-copy tests
check a specific diagnostic and absent destination, but do not spy on Cargo
or codesign calls; do not inflate their names into proof of every prevented
operation. Replace the disposition line with: “Document explicit refusals
as status 2 and uncaught command failures as the command's status; retain
separate coverage for each diagnostic and protected operation.”

**3 — supported.** The build invokes `native_sources.py` and
`build-evidence.py`; `meson_receipts.py` is optional comparison equipment.
The source reader is imported by source-drift checks, and artifact/controller
readers consume the evidence format. There is no violated promise and no
observed defect attributable to directory ownership. BUILD is the appropriate
owner of their place in build execution; the tests README should retain
comparison-tool usage. Replace the disposition line with: “Explain the two
build-time helpers under tests/ and link optional receipt tooling; no move
or code change is justified by this finding.”

**4 — supported.** `build.sh:114` generates identity before the stamp and
Cargo; `build.sh:425` checks it after assembly and before production signing.
CONTRACT explicitly says “The build generates the C, Swift and test copies
before compilation and checks them again before signing.” The source and
control log agree. Moving ordering ownership to the future generated build
account while retaining identity definition/scope in CONTRACT is coherent,
but does not itself authorize changing generation into refusal. Replace the
disposition line with: “Consolidate ordering ownership in BUILD and retain
the identity definition in CONTRACT; keep current generation/check semantics
unless row 14 is separately adjudicated.”

**5 — supported with limits.** The 12 Makefile phase lines and the public
`make build` identity guard are present. The header is an abbreviated account,
not an exact enumeration: `release` invokes strict preflight once before
notarize and again via `release_preflight.py --format version` at
`Makefile:137`, after notarize returns and before the battery. The row's
source summary omits that second call, which matters to row 14. There is no
promise that every recipe operation has a phase banner. Replace the
disposition line with: “Keep the Makefile micro account; start the public
build account at its identity guard; record the second strict release
preflight when describing the release boundary; do not equate phase-line
count with complete execution coverage.”

**6 — supported with limits.** The 209e11c reused-directory partial build at
15.0 is direct evidence that packaging, signing and evidence generation
succeed while full artifact inspection fails. The specimen refusal is from
`5e5f86d-dirty`, not the audited implementation; its actual `run.json` proves
a missing built-in service manifest entry and `tool_error`, with no client
reply. Current source still requires that entry, but a current partial-bundle
specimen execution was not performed. SIGNING calls this “an iteration
convenience, never a release or test artifact”; removing the ZIP/hint is a
new product choice, not a restoration demanded by that sentence. No Swift
discovery is a fresh-configuration claim: the adverse reused directory had
already discovered Swift in the full control. Replace the disposition line
with: “Document partial output, inspector refusal, default built-in specimen
unavailability, and branch-specific checks; mark specimen runtime evidence
as older and fresh no-Swift discovery as source-grounded; separately
adjudicate suppressing ZIP/hint.”

**7 — supported.** The manual validator script uses `cc -Wall -Wextra -O2
-std=c11`, writes beside its source, and ad hoc-signs with `debug.ent`;
`build.sh` instead copies `builddir/sb_api_validator`. This agrees with
SIGNING's “never enters the bundle” account of that manual output in the
normal build. There is no violated promise or proposed semantic change.
Replace the disposition line with: “Move ownership of the manual-debugger
versus shipped-validator distinction to BUILD's signing account; no code
change.”

**8 — supported.** `HARNESS_NOTE_FILES` contains exactly AGENTS, runner README,
tests README and SIGNING; `check_harness_note_agreement` compares only their
whitespace-normalized first paragraphs. It does not prove the environmental
behavior or local explanatory paragraphs. Moving the SIGNING copy and local
paragraph rather than adding a fifth copy preserves the current maintenance
rule. The AGENTS pointer and source-check comment must move with it, and the
disposable checkout in `check_planner.py` must include BUILD when the checker
starts reading it. Replace the disposition line with: “Move the fourth copy,
update the file list/comment/AGENTS pointer and checker-fixture inputs,
retain count four, and treat agreement as textual coverage only.”

**9 — supported with limits.** Stamp inputs and deployment target are passed
as stated. The corrected 15.0/26.0/unset series supports incremental relinking
for the exercised arm64 Cargo/toolchain and `sbpl-check`, not a universal
Cargo caching guarantee; invalid 25.0 runs establish nothing about the
minimum guard. `RUSTFLAGS` is filled when unset **or empty**, using `-z
"${RUSTFLAGS:-}"`, not only when unset. Before the later SDKROOT export,
Cargo inherits any caller-provided SDKROOT; the claim that it necessarily
uses xcrun's default is too strong. CONTRACT promises that the same stamp
values reach the controller and plist; no cited promise requires exporting
SDKROOT earlier. Replace the disposition line with: “Document the actual
environment, empty/unset RUSTFLAGS defaulting and inherited SDKROOT; bound
11.0 and incremental observations to this target/toolchain; no code change
is established.”

**10 — supported.** Neither the build nor default execution invokes the
receipt writer; optional receipts capture commands, output hashes and
configuration when the comparison tool is explicitly run. The current prose
can be read as though receipts are automatic, but there is no missing
mandatory build operation. Replace the disposition line with: “State that
the build embeds evidence but writes no native comparison receipt; link the
tests README for optional capture and avoid implying automatic provenance
attestation.”

**11 — supported with limits.** The 26.0 full control, 15.0 full refusal
before production signatures, and successful 15.0 partial bundle establish
the claimed variant gap. The relevant promise is SIGNING's “Changing the
supported version means changing the plist and the manifest together”; its
per-shipped-binary promise is **not** violated by the partial app, whose
three shipped Rust executables all match its plist. Fresh directories or
another valid minimum are useful controls but unnecessary to establish this
counterexample; source pins fresh native outputs to 26.0 as well. Comparing
one parsed literal can itself drift from applied flags if another assignment,
expression or per-target override changes them. A source-drift rule can
protect repository agreement but is not a build-time refusal; if refusal
before compilation is the chosen expectation, the build step is the better
owner, with drift/mutation tests supporting it and per-binary checks retained.
Replace the disposition line with: “Adjudicate whether declaration agreement
is a build admission rule or a repository maintenance rule; add the matching
guard/control without replacing per-binary checks; bound literal comparison
to supported syntax and prove the value still feeds compile/link flags.”

**12 — supported with limits.** The operator/automatic distinction is sound:
toolchain choice, fresh state after toolchain changes, network availability,
and keychain unlock are not validated as guarantees. Keychain listing proves
identity availability at query time, not subsequent signing success. A clean
checkout is checked by strict release preflight, including its later call,
not by ordinary build. Meson option assertions enforce their enumerated
settings, not literally every native setting; knob defaulting accepts empty
strings as defaults. No independent defect is established by presenting these
facts together. Replace the disposition line with: “Separate operator
assumptions, explicit checks and propagated tool failures; specify the exact
options/checks and avoid claiming keychain unlock, arbitrary-option refusal
or empty-knob rejection.”

**13 — supported with limits.** The new paired real builds establish the
previous inference for a listed top-level helper: its linker ad hoc signature
survives a successful build, its manifest hash matches, and all eight local
inspection signature checks pass outside the sandbox. SIGNING promises
inside-out signing and says “notarization fails if any embedded tool remains
ad hoc-signed”; it does not promise an existing local authority check. No
notarization result was observed here. Matching the app's nonempty team is
useful for detecting this case, but alone does not prove Developer ID
Application class, hardened runtime or trusted timestamp; nor should it
require signatures on dSYM DWARF data, which SIGNING explicitly says are
sealed resources and unsigned. A recursive “every Mach-O under MacOS” walk
would include those dSYM files unless scoped carefully. A build guard gives
early feedback; release acceptance can additionally check the final extracted
ZIP, but occurs after submission and cannot save that expense. Replace the
disposition line with: “Adjudicate an explicit local executable-signer policy
and its placement; team matching is a candidate narrow guard for executable
code, not full production-signature proof; exclude sealed debug resources
and retain signer-agnostic general artifact inspection.”

**14 — supported with limits.** Adverse C establishes regeneration, modified
tracked copies and a dirty stamp before an identity-class refusal; it does
not execute a stale-identity release. CONTRACT's explicit generation promise
(quoted in row 4) supports current behavior. SIGNING's “Each refusal precedes
the step it protects” names stale documents, bad identity, source closure and
minimum checks; it does not promise stale identity refusal before compiling.
Calling regeneration itself a build defect is the pass's expectation.
`release_accept.py` checks artifact integrity, staple, Gatekeeper and witness
runs, not exact-tag stamps. If notarization/acceptance succeeds with the dirty
tree still present, the strict preflight at `Makefile:137` refuses tracked
changes before the battery (`release_preflight.inspect` and `main`); it need
not reach archive. Independently, `release_archive.py:144-147` refuses a
non-exact tag stamp before staging, and `release_runs.py` verifies archived
stamp consistency. These are source conclusions, not a submitted release
experiment. Replace the disposition line with: “Adjudicate documented
regeneration convenience versus earlier release/build refusal; the potential
cost is submission/acceptance followed by the second strict preflight, not
a dirty archive; a release-specific pre-build identity check is another
option besides changing ordinary builds.”

**15 — supported with limits.** Adverse A2 demonstrates an unsealed,
linker-ad-hoc-signed partial app after the minimum refusal. Its destination
was separate from the control's destination, so loss of an earlier good app
at that same path is established by `rm -rf` source, not demonstrated by the
paired probe. No promise of atomic output replacement was found. The
inspector rejects incomplete layout; the controller's default built-in path
rejects missing evidence (also covered by
`builtin_manifest_failures_refuse_before_the_client_with_one_load`). “Nothing
silently uses them” is too broad: direct helper execution is outside those
guards, and a preexisting ZIP/guide is not removed when assembly starts.
Later refusal points can leave more complete or already-signed output, not
always an unsigned partial app. Replace the disposition line with: “Document
phase-specific failure residue and non-preservation of the old app, with
source/observation distinguished; assess stale sibling ZIP/guide separately;
transactional replacement remains a human design choice.”

**16 — supported with limits.** Probe K2 establishes signed packaged native
bytes from the original checkout while the copied tree's generated identity
check and artifact inspection pass. It directly contradicts `build.sh`'s
“What Meson evaluated must be the tree” and SIGNING's promise to compare
configured sources with “the files the tree holds for it,” when “tree” means
the checkout running the build. The defect is in the boundary agreement:
`build.sh` reuses unbound state and `native_sources.active_targets/main`
choose both actual and expected roots from that state, making the check
self-consistent against the wrong root. Enforce an independently supplied
checkout root in the checker; an early build guard can additionally prevent
wrong-tree compilation rather than merely copying. Copying incremental state
is plausible, and clearing an incompatible Swift cache is plausible recovery,
but neither the plan's disposable-copy instruction nor the harness note
instructs copying build products; the harness note says rerun unchanged
bytes outside the sandbox. The observed Meson behavior is verified for
1.12.1 only (and follows its installed `mconf.Conf` implementation), not every
supported future version. Compare canonical existing paths, so symlink
aliases of the same checkout do not falsely fail; a symlinked build directory
is not intrinsically wrong if its recorded source resolves to the intended
root. Equal paths cannot attest unchanged contents, compiler state or
metadata honesty. The minimal wipe probe rebinds to the caller's copied
source, but retains Meson's saved options and is not a compiler-provenance
proof. Replace the disposition line with: “Fix the independently expected
source-root boundary in the checker and decide the early build guard; add
copied-state and canonical-path controls; preserve the trusted incremental
state qualification and limit Meson observations to tested versions.”

For the four priority rows, decisive contrary evidence would be: for 16,
recorded compiler inputs and shipped marker/identity actually belonging to
the copied tree, or refusal before any wrong-tree copy (neither occurs in
K2); for 14, no regeneration/dirty stamp from a clean committed stale copy,
or an earlier identity-specific guard before submission (not present); for
13, a reached local signer refusal or failing manifest/deep verification in
the single-call-removal build (all pass); for 11, a direct declaration guard
refusing the partial build before assembly (absent). Unrelated compiler,
keychain or harness failures would not refute these observations.

## 3. Coverage baseline candidates

“Uncovered” below means no durable control was found producing the exact
build refusal and asserting its protected side effect. Manual probe evidence
is named separately. A direct helper test is coverage for that helper,
not for placement in `build.sh`; a text search/parse is mechanical grounding.
The baseline should not simply list everything here as a defect: several
entries are supported behavior or explicit trust assumptions, and some late
guards are shadowed under ordinary input.

### Explicit build refusals

This inventories all 24 script `ERROR:` sites. All exit 2. A proposed control
must include a valid counterpart, verify the diagnostic, and record whether
the next protected operation ran, using call receipts or tangible outputs.

| Site / claim | Variant and current coverage | Control that would produce it |
| --- | --- | --- |
| `build.sh:76`: invalid knob | Both; uncovered, two knob names through one site | Pass `2`, whitespace and other invalid values separately for each knob; assert no documentation/compile/sign calls. Test unset/empty defaults separately, without expecting refusal. |
| `:100`: unknown argument | Both; uncovered | Invoke an unknown argument with valid knob values; assert usage, status 2, no build effects; pair with help and normal invocation. |
| `:144`: malformed plist minimum | Both; uncovered | Supply a present plist with malformed value, let preceding checks pass, assert no Cargo/output; separately test missing key/file as PlistBuddy failures. |
| `:156`: binary minimum mismatch or absent load command | Three Rust binaries in both; client/host/worker/validator only full; manual A2 only | Real valid build plus one altered/stale candidate per copy site; assert named binary, actual/expected minimum and no production signing. Include no `LC_BUILD_VERSION`; do not let an earlier compile failure stand in. |
| `:167`: empty IDENTITY | Both; uncovered | Reach direct-script identity gate with earlier inputs valid; assert no Cargo/output. Test Makefile's distinct earlier gate separately. |
| `:179`: non-Developer-ID identity class | Both; direct control exists | `ContractVersionTests.test_build_refuses_a_non_developer_id_identity_before_cargo` covers three rejected names, diagnostic, absent Cargo banner/builddir/destination. Add an invocation receipt if claiming no Cargo regardless of banner placement. |
| `:189`: identity absent from keychain | Both; uncovered as durable control; sandbox query failure observed here | Valid class but known-unavailable identity, paired available identity; assert no Cargo. Do not use sandbox denial as proof that a real identity is absent. |
| `:228`: missing/non-executable controller output | Both; uncovered | Controlled successful Cargo invocation omits this output; assert named path and no Meson/assembly. |
| `:232`: missing/non-executable observer output | Both; uncovered | As above, controller present, observer absent/non-executable. |
| `:236`: missing/non-executable sbpl-check output | Both; uncovered | As above, preceding two present. |
| `:254`: missing meson or ninja | Both; uncovered | Controlled PATH omits each tool separately after a valid Cargo stage; assert diagnostic and no native compile/assembly. |
| `:260`: Ninja below minimum | Both; uncovered | Stub only version response to a lower valid version, plus exact-minimum/greater controls; assert no setup/compile. Malformed version is another diagnostic path through the same site. |
| `:285`: missing C native output | Both, two loop targets; uncovered | Complete configured-source/closure prerequisites, remove worker/validator output independently at this boundary; assert no assembly. |
| `:303`: missing app plist at assembly | Both; uncovered and normally shadowed | Initial absence fails earlier at PlistBuddy, not here. A phase-controlled removal after the initial read reaches this guard; assert no copy/sign and report that assembly has already removed the prior app. |
| `:346`: missing augments directory | Both; uncovered | Remove only augments directory in clone; reach assembly and assert refusal before XPC embedding/signing. Empty present directory exercises a warning, not this refusal. |
| `:365`: missing client output | Full only; uncovered | Remove client after native checking with other targets valid; assert no client copy/sign. |
| `:381`: missing service source directory | Full only; uncovered | Remove after native compile so Meson source discovery does not fail first; assert named guard, no service assembly. |
| `:385`: missing service plist | Full only; uncovered | Remove that plist, reach service assembly with executable present; assert no service copy/sign. |
| `:389`: missing host output | Full only; uncovered | Remove host after compile/checking; assert no host copy/sign. |
| `:428`: missing app entitlements | Both; uncovered | Remove plist with all preceding stages valid; assert no production signature (assembly is already allowed). |
| `:438`: missing sign_macho target | Both; uncovered | Reach the real function with an absent target after earlier existence checks; assert no codesign invocation for that target or later packaging. |
| `:442`: non-Mach-O sign_macho target | Both; uncovered | Direct function control with a present non-Mach-O and real valid counterpart, plus a phase-controlled build case if claiming pipeline ordering; earlier minimum checks otherwise intercept it. |
| `:461`: missing assembled service bundle | Full only; uncovered | Remove assembled bundle after identity gate/before service signing; assert this diagnostic, no service/outer seal or ZIP. Earlier app-helper signatures may already exist. |
| `:465`: missing service entitlements | Full only; uncovered | Remove service entitlements in clone; assert diagnostic and no service-helper signature/service seal/outer seal; do not assert no earlier top-level signatures. |

The Makefile's empty-identity gate is a separate public-entry refusal, not a
25th script site. A `make build` control should assert it prevents invoking
`build.sh`; shell status 2 and make's failure status should be recorded
separately from any nested command's status.

### Every Meson policy assertion

No durable control under tests was found producing these policy diagnostics.
There are 19 entries in `fixed_options`, plus two inside the Swift branch.
`project(... meson_version: '>=1.12.1')` also supplies a tool-version gate.
Direct-Meson controls establish assertion behavior; public `make build`
controls are needed for the claim that poisoned/reconfigured state is refused
before copying or signing.

| Asserted option / expected value | Variant | Proposed adverse input, paired with the default |
| --- | --- | --- |
| `optimization = plain` | Both | `-Doptimization=2` |
| `debug = false` | Both | `-Ddebug=true` |
| `warning_level = 0` | Both | `-Dwarning_level=1` |
| `werror = false` | Both | `-Dwerror=true` |
| `strip = false` | Both | `-Dstrip=true` |
| `unity = off` | Both | `-Dunity=on` |
| `b_ndebug = false` | Both | `-Db_ndebug=true` |
| `b_lto = false` | Both | `-Db_lto=true` |
| `b_coverage = false` | Both | `-Db_coverage=true` |
| `b_pgo = off` | Both | `-Db_pgo=generate` |
| `b_bitcode = false` | Both | `-Db_bitcode=true` |
| `b_pie = false` | Both | `-Db_pie=true` |
| `b_staticpic = true` | Both | `-Db_staticpic=false` |
| `b_lundef = true` | Both | `-Db_lundef=false` |
| `b_sanitize = none` | Both | A toolchain-supported `-Db_sanitize=address` |
| `c_std = none` | Both | `-Dc_std=c11` |
| `c_args = []` | Both | `-Dc_args=-DPROBE=1`; fresh CFLAGS case separately |
| `c_link_args = []` | Both | `-Dc_link_args=-Wl,-headerpad_max_install_names`; fresh LDFLAGS case separately |
| `buildtype = plain` | Both | Change label while restoring the effective debug/optimization values, so earlier assertions do not mask this one |
| `swift_args = []` | Full only, after Swift discovery | A valid nonempty Swift argument; assert this message, not discovery failure |
| `swift_link_args = []` | Full only, after Swift discovery | A valid nonempty Swift link argument; assert this message |
| Meson minimum version | Both | Older executable reaches `project` and refuses its version, with a supported-version control; tool absence is a different refusal |

These sketches are not executed tests. Some unsupported settings can fail in
Meson's own option validation or compiler discovery before the policy assert;
such a failure must not be counted as the policy control passing. Fresh setup,
reconfiguration and compile-triggered regeneration are separate paths. A
small representative public-path matrix plus per-assertion direct controls
can be narrower than a Cartesian product while preserving those distinctions.

### Propagated refusals and remaining behavioral claims

| Claim | Variant / existing evidence and gap | Proposed control or bounded account |
| --- | --- | --- |
| Stale limits/guide and contract copies stop build | Both; direct build controls exist, asserting diagnostic/status/absent destination | Preserve them; add Cargo/sign invocation receipts if claiming those exact effects cannot occur under reordered banners. |
| Architecture stale/citation/parse failure stops before compile | Both; generator-level controls and textual `build_checks` exist, no corresponding executed build ordering control found | Corrupt a copied architecture output/citation and invoke build with otherwise valid prerequisites; assert diagnostic and no Cargo. |
| Identity generation rejects invalid sources/regions and pre-sign check rejects edits | Both; generator controls cover symlinks/staleness; no build race/order control | Controlled phase pause, mutate digest input after compilation without regeneration, then assert pre-sign refusal; also pair initial invalid-input generation refusal with valid input. |
| Configured source membership, duplicate targets and digest closure | File-mode and C-only configured controls exist; no public build-path adverse control and no Swift-shim escape control found | Existing `check_planner.configured_controls` is useful helper coverage; add make-build substitution/relative escape and full shim case, asserting no copies/signatures. |
| Native checker unreadable Meson/Ninja metadata, missing/stale dependencies | Both; no targeted refusal controls found | Corrupt metadata or remove/stale dependency records and assert specific checker status/diagnostic; distinguish unreadable from mismatched sources. |
| Declaration agreement / partial minimum gap | Partial/full; only manual row 11 evidence | Control chosen after adjudication; do not describe source-drift agreement as an early build guard. |
| Wrong-checkout copied native state | Full manual K/K2 and minimal path probe here; no durable build control | Copy configured state, diverge source marker/identity, handle module cache deliberately, then assert intended root refusal and absence of copying; include symlink aliases and builddir symlink. |
| Actual applied native flags and minimum per language | Source and normal build/minimum observations; no durable variant/command comparison control | Inspect effective commands and Mach-O load commands for each relevant target/setting; a literal parser does not establish use. |
| Full versus partial packaging, no Swift discovery when fresh partial | Manual partial build reused a full directory; no durable fresh partial build control | Fresh partial with no usable Swift compiler; verify two C targets, three shipped Rust executables, expected seals/evidence/ZIP, full-inspector refusal. |
| Inspection off, dSYMs, unchanged C flags, Rust defaults and caller precedence | Source only for off branch; no knob controls | Build on/off and reused transitions, inspect Swift commands/dSYM presence and Rust effective commands, test unset/empty/nonempty RUSTFLAGS and Cargo configuration precedence. |
| Cargo deployment target, stamp variables, incremental relinking | Manual sbpl-check series; no durable build-environment control | Change valid target values and stamp independently, compare actual outputs/plist/controller stamp; document target/toolchain bounds. |
| Compiler/SDK changes in reused state | Explicit unverified trust assumption, not an existing refusal | Two toolchain/SDK selections with fresh controls and reused state, inspect actual commands; or accept operator responsibility with bounded wording. |
| SDK discovery/Cargo/Meson/compile/copy/chmod/dsymutil failure propagation | Both or full for dSYM; no comprehensive build phase controls | Inject one command failure at each relevant phase, assert no subsequent protected effects and record residue. These are tool statuses, not 24 additional script messages. |
| Signing authority, runtime and timestamp | This audit observes missing helper signing pass; no existing local signer-policy control | After adjudication, omit signing before evidence generation, check correct local guard and valid counterpart; separately model same-team wrong identity class if claiming production-signature assurance. |
| Unsigned nested code rejected, sealed dSYM resources intentionally unsigned | Manual unsigned probes; inspector tamper controls are different | Developer ID paired seal probe for unsigned helper and resource tamper; exempt debug data from executable signer policy. |
| Signing/seal/deep verification failure stops packaging | Real inspector controls cover missing/damaged helpers and stale manifest, not build ordering | Fail a reached signing command or tamper before build verification; assert no new ZIP and state of previous output. |
| Evidence generation is post-signature, pre-outer-seal and complete | Text and successful probes, inspector hash/missing-entry controls; no bypass/reordering build control | Move a helper signature after BOM or omit an inventory entry; intended hash/inventory assertion must catch it; distinguish bundle seals from main hashes deliberately omitted. |
| Guide staging refusal and exact bytes | Direct generator controls exist (`test_check_and_staging_refuse_stale_or_incomplete_documents_without_writing`, `test_staged_guide_is_exact_and_standalone`) | Add build-path mid-build stale-guide case only if claiming late stage ordering and residue; generator behavior alone is already covered. |
| Custom DIST_DIR copies README/AGENTS and stages guide | New control/adverse builds exercised custom destination, no durable byte/alias assertion | Compare copies and use default, absolute, relative and same-file alias destinations; verify copies do not overwrite source unexpectedly. |
| No augments warning versus missing-directory refusal | Both; source only | Empty present directory: assert WARN and intentional successful continuation; missing directory: assert ERROR and no signing. |
| Failure leaves prior app destroyed / sibling outputs stale | Source; manual A2 only demonstrates residue in a distinct new directory | Prior-good build at same destination, induce each representative later failure, compare app/ZIP/guide inventory and consumer behavior. |
| Sandboxed keychain/signature/Swift/XPC/log failures | Documentation agreement only; keychain/signature behavior observed here | Environment-specific paired unchanged-byte reruns with explicit prerequisites; cannot turn an intermittent harness observation into a universal guarantee. |
| Release preflight, acceptance and archive stamps | Helper controls exist in `check_release.py` and `check_release_publish.py`; no complete Makefile dirty-after-build chain control found | Offline recorded-command release-chain control with a build that dirties tracked identity, proving submission/acceptance then second preflight refusal before battery/archive; never make real submissions for this control. |
| Partial/incomplete app cannot use built-in runner | Older partial probe and current source/unit manifest-failure control | Current partial-build specimen refusal, assert no client invocation; do not infer all direct tools or external-runner configurations are unusable from one fixture. |

The concrete existing release controls must not be erased by an “uncovered
release chain” label: `check_release_publish.check_preflight` tests dirty
tracked state and strict/report behavior; `check_release.check` exercises
acceptance with injected tools while retaining real layout/hash checks.
Likewise `check_signed_artifacts.py` is a real codesign tamper control. None
asserts the full public Makefile sequence or every embedded executable's
production signer.

## 4. Proposed new rows

These are hypotheses from the single forward source walk. No additional
investigation or adverse execution was performed for them.

**17 — Cargo's output directory can diverge from the path assembly reads.**
The script permits inherited Cargo configuration/environment but copies fixed
`controller/target/release/` paths after Cargo succeeds. `CARGO_TARGET_DIR`
or an alternate configured target could place new outputs elsewhere while
old executable files remain at those fixed paths. Consequence: a successful
build may package stale Rust tools under a new plist stamp, despite native
source checks and equal minimum versions. Probe sketch: baseline build in a
clone; change a visible Rust marker, select a different Cargo output directory,
rebuild with the same supported minimum, and compare marker plus controller
`--version` against plist; pair with default-directory rebuild. This tests
a root/output binding issue analogous to row 16, not hostile build-cache
integrity.

**18 — Failed builds can leave a previous release-named ZIP and guide beside
new partial output.** Assembly removes the app, but ZIP deletion happens
only at packaging; guide staging is also late. Consequence: a user handling
the existing ZIP manually can select the previous artifact after a failed
build, even if the inspector refuses the new app. Probe sketch: create a
known good app/ZIP/guide at one disposable destination, induce a reached
minimum or signing refusal, and compare all three outputs and stamps.
This is an extension of row 15's consequence, not proof that any release
command automatically submits stale bytes (make notarize rebuilds and stops
on build failure).

**19 — SDK selection is neither uniformly applied nor necessarily a checked
assignment.** Cargo runs before the explicit SDKROOT export and can inherit
a caller value. Also `export SDKROOT="$(xcrun ...)"` returns the export
builtin's status, so `set -e` alone does not establish that failed SDK lookup
stops the build at that point. Consequence: the native toolchain may fall
back to a different SDK, or fail later, while prose presents one selected
SDK. Probe sketch: valid control plus controlled SDK lookup failure and
caller-provided SDK selection in a clone, inspecting actual Cargo/native
link commands; distinguish fallback from earlier toolchain failure. Do not
fix by moving the export without deciding the intended SDK contract.

**20 — Empty knobs are defaults, and native policy is an enumerated subset.**
`${BUILD_XPC:-1}` and `${PW_INSPECTION:-1}` treat empty values like unset,
despite “any other spelling is refused.” Meson's assertions enumerate
specific options; the phrase “Every other native setting is fixed” is broader
than that list, and per-target arguments can change without changing those
options. Consequence: the new manifest/parser could encode a stronger
admission/policy guarantee than the script supplies. Probe sketch: empty,
unset, invalid and valid knob inputs with invocation receipts; independently
choose a recognized unasserted Meson option affecting commands and compare
fresh/reused public builds, rather than assuming every option must be refused.
This can become a correction to existing rows 9/12 instead of a new defect.

**21 — A current generated identity check is not a binary/source snapshot
check during concurrent edits.** The late check compares generated source
copies with the current tree, not identities read from compiled outputs.
A concurrent source change followed by regeneration could make that check
pass after some compilation has finished. Consequence: “refusing a source
edit made during compilation” is broader than the mechanism alone proves.
Probe sketch: pause a disposable build at a controlled post-compile phase,
change a worker marker and regenerate identity, then resume; compare actual
binary identities/marker and generated copies, with an unchanged control.
Adjudicate whether concurrent mutation is excluded by trusted-checkout
assumptions before treating this as an implementation defect.

## 5. Corrections to the plan's text

These are factual replacements for the plan author; the plan itself was not
edited. Design recommendations remain recommendations.

1. **Old (row 14 table):** “the release path checks cleanliness before the
   build, and the archive step refuses the dirty stamp only after the
   notarization submission.” **New:** “the release path checks cleanliness
   before the build and again after notarization/acceptance, before the
   battery; the later archive step independently refuses a dirty stamp.”
2. **Old (row 14 detail):** “but both run after the notarization submission
   and the battery. So the consequence is a spent submission and a late
   refusal, not a dirty archive.” **New:** “Those archive checks are later
   defenses. In make release, if regeneration leaves tracked copies modified,
   the second strict release_preflight.py call refuses after
   notarization/acceptance and before the battery. A spent submission remains
   possible; a dirty archive is not established.”
3. **Old (step 3a):** “the configured source and closure checks, the knob and
   Ninja guards) cite directly”. **New:** “the configured source and closure
   checks) cite directly as helper-level controls; build-path ordering is
   separate. No durable knob or Ninja-guard controls were found; include
   those in the initial coverage baseline.”
4. **Old (candidate claim 5):** “Four generator checks before any compile”.
   **New:** “Three generator --check invocations and identity generation
   before any compile; identity --check runs after assembly before signing.”
5. **Old (row 9 detail):** “only when PW_INSPECTION=1 and the caller left it
   unset”. **New:** “only when PW_INSPECTION=1 and RUSTFLAGS is unset or
   empty”. Apply the same correction to candidate claim 3.
6. **Old (row 9 detail):** “so Cargo's link resolves the SDK through cc and
   xcrun's default rather than through the script's variable”. **New:**
   “so Cargo runs before this explicit SDKROOT selection and inherits any
   caller SDKROOT; with none set, the observed toolchain uses its normal
   SDK resolution.”
7. **Old (row 9 recommendation):** “a plain cargo build outside the script
   yields 11.0 binaries”. **New:** “the exercised arm64 sbpl-check build with
   deployment target unset yielded minos 11.0 on the recorded toolchain;
   this is not a cross-target or future-toolchain default guarantee.”
8. **Old (row 15 table/detail):** “an unsigned partial bundle”. **New:**
   “an unsealed partial bundle carrying linker ad hoc signatures in the
   observed minimum-refusal case; later failures can leave different states.”
9. **Old (row 15 detail):** “Nothing silently uses them”. **New:** “The full
   inspector rejects incomplete output and the default built-in specimen
   path refuses missing evidence; direct helpers and preexisting sibling
   ZIP/guide files are outside that conclusion.”
10. **Old (row 16 limits):** “which the harness rerun guidance and this
    plan's own 'disposable copies' instruction both invite”. **New:**
    “a plausible copied-workspace scenario, although the disposable-copy
    instruction does not require copying incremental state and the harness
    note prescribes an unchanged-byte rerun outside the sandbox.”
11. **Old (row 5 source):** “release runs the strict preflight, $(MAKE)
    notarize, the battery, the archive and the rotation”. **New:** “release
    runs strict preflight, $(MAKE) notarize, another strict preflight to
    obtain the version, the battery, the archive and rotation.”
12. **Old (row 13 recommendation):** “every Mach-O under the app's and the
    service's Contents/MacOS carries the app's team identifier”. **New:**
    “every executable code object in the agreed signing inventory carries
    the required signer properties; explicitly distinguish unsigned sealed
    dSYM DWARF resources from executable code.” Team identity versus full
    production-signature requirements still needs adjudication.
13. **Old (row 13 evidence):** “a real build would not show” the manifest
    hash error. **New:** “the audit's real single-signing-call-removal build
    has matching helper evidence hash, successful seals/deep verification
    and artifact inspection, while sbpl-check remains ad hoc-signed.”
14. **Old (candidate claim 3):** “BUILD_XPC and PW_INSPECTION accept exactly
    0 and 1”. **New:** “Unset or empty BUILD_XPC/PW_INSPECTION default to 1;
    remaining supplied values must be exactly 0 or 1.”

No accepted limitation, new automated coverage, or completed implementation
is implied by this report. It supplies evidence and bounded recommendations
for the human's sixteen dispositions and the next assessment pass.
