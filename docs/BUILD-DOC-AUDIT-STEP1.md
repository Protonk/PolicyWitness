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
