# Build documentation assessment and Makefile closeout

Record, 2026-10-10. This preserves the investigation, adjudications and probe
results behind the build-document and Makefile plans. It is historical evidence,
not the current behavior contract or an active plan. The starting revision for
closeout was `1c3ec36a9c83a302f4126f9f1b20482d7157eaab`; the commit carrying this
record contains the closeout edits. Earlier revisions are named in the probe
accounts below. The deleted working plans and audit prompt remain recoverable
from that starting revision with `git show`.

All evidence paths under `.tmp/` and `tests/out/` below are gitignored and
available only in the local checkout. The transcribed commands and outcomes
preserve the conclusions independently of the scratch logs. Selected managed
validation output is pinned in `tests/RETAINED.json`.

## Closeout reconciliation

The original rows are resolved by implemented guards and controls, corrected
explanations, or explicit accepted limits. The native source and dependency
checks remain membership checks, and incremental build directories remain
trusted working state. The refusal coverage baseline remains unchanged at
28 rows without a producing control; 14 rows have build-path controls and
23 more have helper-only controls. Further refusal controls, including the
stub-Cargo tier, belong to the sketches in
[the build baseline](../tests/fixtures/docs/build_baseline.json) and the gaps
in [BUILD.md](../docs/BUILD.md#known-gaps). No new build guarantee is inferred
from a generator check or a passing suite.

Closeout consolidates the build instructions in BUILD.md, retains short
SIGNING.md pointers at the old anchors, moves the shared harness note and its
checker together, and updates routing and maintenance guidance. The final
prose and manifest correct two remaining claims from row 22/27: an ad hoc
listed helper in a production-signed app fails the inspector's signer
consistency check; however, a later failure signing the standalone observer,
staging the guide or creating the ZIP can leave an app that passes inspection.
The inspector establishes bundle properties, not build completion. These
corrections are grounded in `artifact.inspect`, `signer_check.problems` and
the post-seal sequence in `build.sh`; they require no build semantic change.
The copied signing-helper docstring is corrected too. The output-directory
account now allows a caller's DIST_DIR outside the checkout.

The build script, Meson files, worker protocol sources, membership checker,
Cargo artifact reader and inspector implementation are unchanged by closeout.
Their earlier reproductions remain bounded observations at the named revisions;
new validation checks the integrated documentation and the existing guards,
rather than presenting those historical probes as fresh executions. The moved
prose retains operator responsibilities, partial-bundle limits, external SDK
and developer-directory boundaries, and the distinction between receipts and
attestation. The native direct-compile commands remain development equipment.

## Makefile decisions and observations

The Makefile audit's measured defects were fixed before closeout: test follows
DIST_DIR, the ordering control uses the dispatcher's app, the worker harness
names its argv bound, the keychain refusal distinguishes an empty listing, and
the header describes network use and per-step bounds accurately. Its local
report is `.tmp/audits/BUILD-DOC-AUDIT-MAKEFILE-REPORT.md`; the audit prompt is
recoverable as `docs/BUILD-DOC-AUDIT-MAKEFILE.md` at the starting revision.

The adopted changes are default help printed from the header itself and a
preview-first prune verb with no clean alias. Omitted APPLY previews; exactly
1 applies; other supplied values, including empty, refuse before delegation.
The help control checks both entrypoints with a changed header and executable
sentinels for other targets. Retention controls compare real fixture inventories
before and after preview/apply, preserve retained and release output, and prove
invalid APPLY values and the removed verb cannot invoke a sentinel dispatcher.
GNU Make strips leading whitespace from command-line assignments before exposing
the variable; the control uses environment values to test retained leading
whitespace. No raw command-line parser was added.

The audit's other proposals remain deferred here as the follow-up destination:
a test selector interface, retiring notarize as a verb, and a check-build verb.
None is required by an existing behavior promise; reopen only when a concrete
operator need justifies changing the corresponding boundary. No automated
cache-removal verb is added; BUILD.md names the manual reset command.

## Closeout validation

All closeout gates passed on the starting revision plus the edits in this
commit, outside the automation sandbox where compiler, keychain, signature,
socket or live XPC access required it:

- `python3 -B docs/generate_limits.py --check`, `generate_contract.py --check`,
  `generate_worker_identity.py --check`, `generate_architecture.py --check`
  and `generate_build.py --check`: current. The build generator was run after
  editing the directory description and removing an inventory count; the
  worker identity did not change.
- `PW_TEST_OUT_DIR=tests/out/runs/build-make-closeout-drift ./tests/run.sh --suite source_drift`:
  six of six cases passed, with no skips or harness errors.
- `PW_TEST_OUT_DIR=tests/out/runs/build-make-closeout-dispatcher ./tests/run.sh --suite dispatcher`:
  six of six cases passed, including the changed pruning controls.
- `PATH="/opt/homebrew/opt/rustup/bin:$PATH" make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'`:
  completed; all seven executables passed the signer check and the app, ZIP
  and guide were produced. The first attempt without the PATH prefix stopped
  because Cargo was absent from PATH (make status 2, recipe status 127),
  before compilation or assembly. Adding the installed toolchain to PATH
  required no repository repair.
- `PATH="/opt/homebrew/opt/rustup/bin:$PATH" PW_TEST_OUT_DIR=tests/out/runs/build-make-closeout-default ./tests/run.sh`:
  171 of 171 cases passed, none skipped or unrun, no harness errors, selected
  app valid before and unchanged afterwards. The Swift unit batch passed
  385 of 385 internal tests. This includes another complete drift and
  dispatcher pass against the integrated tree.
- A fresh `/bin/zsh -f -c make` with APPLY and Make flags removed from the
  environment printed the header and exited zero. Direct `make prune` and
  `make prune APPLY=1` calls in a disposable dispatcher fixture returned JSON,
  first preserving and then removing its completed owned run. The detailed
  retention control also preserved retained/release inventories and proved
  all invalid-value and removed-target refusals happened before delegation.
- Final generator currency, prose-baseline, link and whitespace checks passed
  after retiring the working plans and audit prompt. The help/explicit-build
  controls were rerun after adding a presence assertion for the header
  mutation. Final prose also scopes copy ordering to bundle copies and calls
  the inputs list working state rather than claiming every input is outside
  the checkout. These final edits change no production behavior.

The managed outputs above are pinned, together with the earlier step-four
battery `tests/out/runs/build-doc-step4-default-2`. Build logs and manual
help/pruning receipts are retained in
`tests/out/runs/build-make-closeout-default/closeout/`. All are local,
gitignored evidence. The built app carries the development stamp
`v0.2.7-55-g1c3ec36-dirty`; this was a local verification build, not a release.
Notarization, release acceptance and publication were not invoked.

Both working plans and the remaining Makefile audit prompt are removed after
the gates. The retained record, regression controls, baseline sketches and
current documentation carry their outcomes and ongoing obligations.

## Historical assessment register

The register and probe details below preserve the assessment as it developed.
Later rows supersede earlier decisions where stated, especially row 22 over
row 13 and row 23 over row 17. References to steps describe the completed
work sequence, not outstanding instructions. The closeout reconciliation
above states the final account.

| # | Candidate issue | Where it shows | Survey evidence | Disposition | Wording, change scope or follow-up |
| --- | --- | --- | --- | --- | --- |
| 1 | Three inventories must agree and nothing checks the script's | `build.sh` signing list; `EXECUTABLES` in `tests/lib/artifact.py`; README "What ships"; `tests/build-evidence.py` | [AGENTS.md](../AGENTS.md) says the three lists must agree and the preflight suite fails a build that does not match `EXECUTABLES`, but the script's `sign_macho` calls are compared with nothing. A helper copied but not listed for signing is caught only when the inspector runs. | Adjudicated 2026-10-09: strengthen verification (step 3a); correct the documentation. Audit: supported with limits. | The step 3a drift rule compares the parsed signing calls with `EXECUTABLES`, `helper_names` in the evidence generator and the README, distinguishing five embedded signatures, two seal-signed mains and the standalone observer. The survey's last sentence is wrong in both directions (detail 1); the signer gap was row 13 and is now enforced. |
| 2 | A refusal carries one of two exit statuses | `build.sh` under `set -e` | The script's own refusals exit `2`; a generator check that fails propagates `1`. The build controls assert the specific status, so the document would either state both or the script would harmonize. | Adjudicated 2026-10-09: correct the documentation. Audit: supported. | State the rule: the script's own refusals exit 2; a check's or a tool's refusal propagates that tool's status. The manifest records each refusal's status; the controls keep asserting each diagnostic and protected operation separately. |
| 3 | Build-time checks live under `tests/` | `tests/lib/native_sources.py`, `tests/lib/meson_receipts.py`, `tests/build-evidence.py` | `build.sh` invokes two of them as production steps and the receipts describe build provenance, yet all three sit in the test tree with the suites' helpers. The generators the build runs live under `docs/`. | Adjudicated 2026-10-09: accept and explain. Audit: supported. | The build runs three helpers that live with the tests (`native_sources.py`, `build-evidence.py` and now `signer_check.py`) because the suites import the same code; the receipts tool is not a build step (row 10). No move. |
| 4 | The identity's place in the build order is owned twice | [CONTRACT.md](../docs/CONTRACT.md) "Internal host/worker identity"; `build.sh` | The contract says the build generates before compiling and checks before signing; the script does it; the signing document repeats it. Which document owns the ordering claim. | Adjudicated 2026-10-09: correct the documentation (ownership). Audit: supported. | The generated step table in `BUILD.md` owns the ordering; the contract keeps the definition and digest scope. Both now say the build checks before compiling and again before signing (row 14). |
| 5 | The Makefile carries a second prose account of the sequence | Makefile header comments | The header describes each target's sequence and boundaries in prose that no rule reads; the `release` recipe's comment and the signing document's procedure describe the same chain. | Adjudicated 2026-10-09: correct the documentation. Audit: supported with limits. | The header matches the recipes and stays as the Makefile's micro account. The manifest's steps begin at `make build`, whose guard is the public entry's first refusal. The release boundary records the second strict preflight after notarization (detail 5). |
| 6 | The partial bundle is a parallel output with weaker checks | `BUILD_XPC=0` in `build.sh`; the signing document | It passes evidence generation and packaging, fails the full inspector, cannot run specimens, and is called an iteration convenience. Every inventory and every refusal table must say whether it covers the partial bundle. | Adjudicated 2026-10-09: correct the documentation; accept the limitation; the ZIP and hint stay. Audit: supported with limits. | Every manifest item carries its variants. The partial bundle's two C executables are now minimum-checked (row 11); its specimen refusal is recorded against an older build and the fresh no-Swift claim as source-grounded. |
| 7 | A parallel compile path for the validator | `controller/tools/sb_api_validator/build.sh` | Compiles the validator beside its source with `cc` and ad hoc-signs it with debug entitlements; its output is ignored and never enters the bundle. The signing document now says so; a build document must repeat or own it. | Adjudicated 2026-10-09: correct the documentation (ownership). Audit: supported. | The "never production-signed" paragraph moves to the build document's signing section and is stated once. No code change. |
| 8 | The harness note is carried in four places | [AGENTS.md](../AGENTS.md), `runner/README.md`, `tests/README.md`, [SIGNING.md](../docs/SIGNING.md) | The copy in the signing document says which build steps need an unsandboxed shell. Moving that copy into the build document keeps four copies; adding one would make five. The drift rule's file list names the copies. | Adjudicated 2026-10-09: correct the documentation; update the rule's list at step 5. Audit: supported. | The signing copy and its second paragraph move to `BUILD.md`; `HARNESS_NOTE_FILES`, the comment above it, the rule's message, the AGENTS.md pointer and the planner control's copied-file list change in the same commit. Count stays four. |
| 9 | Cargo's inputs are the one part of the build no manifest describes | `controller/build.rs`; `build.sh` | The stamp variables, `RUSTFLAGS` when inspection is on and the deployment target reach Cargo through the environment; `build.rs` declares the stamp variables for rebuilds and Cargo tracks the deployment target itself. Nothing in `docs/` lists them. | Adjudicated 2026-10-09: correct the documentation. Audit: supported with limits. | The inputs section lists them (detail 9): the stamp variables, the deployment target from the plist, `RUSTFLAGS` when unset or empty, the pinned output directory (row 17) and one `SDKROOT` selected before Cargo (row 19). Observations are bounded to this target and toolchain. |
| 10 | The receipts are described as a build artifact but produced by a test tool | `tests/lib/meson_receipts.py`; `tests/README.md` "Comparing native builds" | The signing document tells the reader what the receipt pairs and records; the tool that writes it is documented with the comparison tools under the tests README. A build document would describe it a third time. | Adjudicated 2026-10-09: correct the documentation. Audit: supported. | The build writes no receipt; `BUILD.md` says so and links the comparison tools. The two signing-document passages are reworded when the sections move. |
| 11 | The supported macOS is declared in two places and enforced in a third | `Info.plist`, `meson.build`, `build.sh` | The plist declares it, the manifest pins it, the script checks every shipped Mach-O against the plist and exports it to Cargo. The signing document says to change the plist and the manifest together; no rule compares the two declarations. | Adjudicated 2026-10-09: fix the build. Audit: supported with limits. | Implemented: every Cargo output is minimum-checked right after Cargo and every Meson output right after the configured source check, in both variants and before assembly, so the two declarations cannot disagree in a build that completes. No literal is parsed. Validation in detail 11. |
| 12 | The steps a human must run are mixed with the steps the script runs | [SIGNING.md](../docs/SIGNING.md) "Build" and the release procedure | Toolchain resets after a compiler or SDK change, fresh directories, the keychain, and the unsandboxed shell are operator steps stated beside the script's automatic ones. The document needs a line between them. | Adjudicated 2026-10-09: correct the documentation. Audit: supported with limits. | `BUILD.md` separates what the operator must ensure (unenforced, each item marked so) from what the build refuses; the manifest keeps prerequisites apart from refusals, names the exact Meson options asserted, and claims neither keychain unlock nor arbitrary-option refusal. |
| 13 | No local check reads the signer; an ad hoc-signed embedded tool passes the seal, the deep verify and the inspector | `build.sh` seal and verify steps; `tests/lib/artifact.py`; notarization | Found in step 1 (detail 13). Every compiler output arrives ad hoc-signed by the linker. A listed or unlisted ad hoc helper seals, verifies and inspects clean; only notarization refuses it, as the documents say. The audit reproduced it in a real build. | Adjudicated 2026-10-09: fix the build. Audit: supported with limits. | Implemented: `tests/lib/signer_check.py`, run by `build.sh` after the deep verify, requires every regular file directly under the app's and each service's `Contents/MacOS` to be a Mach-O signed by the named identity with the hardened runtime; the dSYM bundles are outside those directories. The inspector stays signer-agnostic. Control in `check_signed_artifacts.py`. |
| 14 | A stale committed identity is regenerated by the build and the stamp becomes dirty | `build.sh` identity generation; [CONTRACT.md](../docs/CONTRACT.md) | Found in step 1 (detail 14). A clean checkout whose committed identity copies are stale builds with a `-dirty` stamp and a modified tree instead of refusing; the release path checks cleanliness before the build and again after notarization and acceptance, before the battery; the later archive step independently refuses a dirty stamp. | Adjudicated 2026-10-09: fix the build, refusing in ordinary builds. Audit: supported with limits. | Implemented: the pre-compile step runs `--check` like the other three generators and the build writes nothing into the tree; regeneration is a developer command the refusal names; the contract, the signing document and the AGENTS.md checklist say so. Control in `contract.py`. The release-specific check was not added. |
| 15 | A refusal after assembly leaves a partial bundle at the output path | `build.sh` assembly (`rm -rf` of the previous app) | Found in step 1 (detail 15). The previous app is removed at assembly; what a later refusal leaves is unsealed and, in the observed case, ad hoc-signed by the linker. The previous ZIP and guide used to survive beside it. | Adjudicated 2026-10-09: accept and document; small fix for the stale siblings (row 18). Audit: supported with limits. | Implemented: assembly removes the previous app, ZIP and guide together, so a failed build leaves no release-named artifact beside its residue. The minimum checks moved before assembly, so fewer refusals reach that point. Transactional replacement was not adopted. |
| 16 | The build trusts the build directory's recorded source directory | `build.sh` `meson configure`; `tests/lib/native_sources.py` | Found in step 1 (detail 16). Meson accepts a copied build directory and keeps compiling the checkout it was set up for; the configured-source check compared against that recorded directory, not the running checkout; only swiftc's module-cache path check stopped the copied build, by accident. | Adjudicated 2026-10-09: fix the build. Audit: supported with limits. | Implemented: `build.sh` refuses before Cargo when the build directory's recorded source directory is not this checkout (canonical paths, both named), and `native_sources.py --root` repeats the comparison in the configured reading. Controls in `contract.py` and `check_planner.py`. |
| 17 | Cargo's output directory can diverge from the paths assembly reads | `build.sh` Cargo step | Proposed by the audit. `CARGO_TARGET_DIR` or a Cargo configuration value sends the outputs elsewhere while the script copies fixed `controller/target/release/` paths, so a build could package stale Rust tools under a new stamp. | Adjudicated 2026-10-09: fix the build. | Implemented: `cargo build --target-dir` pins the output directory to the checkout's, which overrides the environment and configuration; the copy paths derive from the same variable. Validation in detail 17. |
| 18 | A failed build left the previous ZIP and guide beside new partial output | `build.sh` assembly and packaging | Proposed by the audit as an extension of row 15: the ZIP was removed only at packaging and the guide staged late, so a manual step could pick up the previous artifact after a failed build. | Adjudicated 2026-10-09: fix the build (folded into row 15). | Implemented with row 15: assembly removes the ZIP and the guide with the previous app. `make notarize` always rebuilds, so the automated chain never submitted stale bytes; the manual steps now cannot either. |
| 19 | SDK selection was neither uniform nor a checked assignment | `build.sh` `export SDKROOT` | Proposed by the audit. Cargo ran before the export and inherited any caller `SDKROOT`; `export VAR="$(cmd)"` returns the builtin's status, so a failed `xcrun` left an empty `SDKROOT` under `set -e`. | Adjudicated 2026-10-09: fix the build. | Implemented: the SDK is selected once, before Cargo and Meson, with an explicit refusal when `xcrun` fails or returns no directory; the selection is printed. The intended contract is one SDK for every compiler (detail 19). |
| 20 | Empty knobs were defaults, and "every other native setting" overstates an enumerated list | `build.sh` knobs; [SIGNING.md](../docs/SIGNING.md) | Proposed by the audit. `${BUILD_XPC:-1}` read an empty value as `1` despite "any other spelling is refused"; Meson's assertions enumerate specific options, so "every other native setting is fixed" claimed more than the list. | Adjudicated 2026-10-09: fix the knob; correct the documentation. | Implemented: an unset knob means `1` and an empty one is refused with the other spellings; the signing document now says "the native settings `meson.build` enumerates". Control in `contract.py`. |
| 21 | The identity check before signing is a copy-currency check, not a binary snapshot | `build.sh` pre-sign identity check; [SIGNING.md](../docs/SIGNING.md) | Proposed by the audit. An edit to an identity input during the build followed by regeneration passes the late check, so "refusing a source edit made during compilation" promised more than the mechanism. | Adjudicated 2026-10-09: accept as a trust bound; correct the documentation. | The signing document and the script's comment now say the check refuses an edit made during the build without regeneration and that the build otherwise trusts the checkout not to change under it. No mechanism change. |
| 22 | A build that fails after the seal leaves a sealed app the inspector accepted | `build.sh` after the app seal; `tests/lib/artifact.py` | Plan-blind audit (W1, D1). Verification, the signer check, the observer's signature and packaging can fail after the seal; the residue is a sealed, evidenced app, and the inspector was signer-agnostic by design, so a build that failed at the signer check left an app the battery would accept. | Adjudicated 2026-10-09: fix the inspector; correct the documentation. | Implemented: `artifact.py` requires every executable to carry the controller's signer, so an ad hoc helper inside a production-signed app is refused while an ad hoc test copy stays consistent; the preflight control observes it and runs the signer command line (G5). The prose states what each phase's refusal leaves behind. |
| 23 | A Cargo target triple could move the outputs away from the paths the script copies | `build.sh` Cargo step | Plan-blind audit (D2). `--target-dir` pins the root, but `CARGO_BUILD_TARGET` or a configuration file adds a triple subdirectory, and a reused directory could then ship a stale controller that passes the minimum check. | Adjudicated 2026-10-09: fix the build. | Implemented: Cargo runs with JSON messages into a file under the pinned directory, `tests/lib/cargo_artifacts.py` reports the executable each binary was written to, and the script refuses one that is not the pinned path before any copy. Baseline entry for the refusal; row 17 reopened and closed with it. |
| 24 | An include of an absolute path outside the checkout escaped the identity closure | `tests/lib/native_sources.py` closure check | Plan-blind audit (W4, D3). Every dependency outside the checkout was taken for the SDK or the toolchain and skipped, so a fresh compile could consume bytes the identity never hashes. | Adjudicated 2026-10-09: fix the build; correct the documentation. | Implemented: a dependency outside the checkout must lie under the selected SDK or the developer directory, from `SDKROOT`, `DEVELOPER_DIR` or `xcode-select -p`; anything else is named. Control: `configured-absolute-escape` in `check_planner.py`. The signing document and the contract state the boundary. |
| 25 | The parser's textual agreement was selective | `docs/generate_build.py` | Plan-blind audit (G1). A dropped `--timestamp`, a dropped `--target-dir` and a dropped `set -e` left every rule satisfied; a propagated status is the tool's, not parsed. | Adjudicated 2026-10-09: strengthen verification; correct the documentation. | Implemented: the parser records the signing commands' flags and the tool invocations' flags and compares them, requires `set -euo pipefail` as the first instruction, and the drift case names each of the three mutations; the manifest's cargo invocation lists its flags; the captions and the prose say what is compared and that propagated statuses are the tools' documented ones. |
| 26 | Two citations claimed more than their controls observe | `docs/build.json` (`stale_guide`, `signer_mismatch`) | Plan-blind audit (G2, G5). The guide-staging refusal cited a control that stops at the first limits check; the signer row cited a control that calls the helper's function, not its command line. | Adjudicated 2026-10-09: correct the manifest; strengthen the control. | Implemented: `stale_guide` cites the staging helper's own refusal control as helper coverage; the preflight control now also runs `signer_check.py` on the mutated copy and asserts its status and header. |
| 27 | The draft overstated six claims and omitted four facts | `docs/BUILD.md` | Plan-blind audit (W2, W3, W5, W6, O1 to O4, G3, G4). "Checks before compiles" held only for the documentation and identity checks; "writes nothing into the tree" meant no tracked file; guide staging checks sources, not the staged copy; the figure chained mutually exclusive steps, mislabeled its legend and linked to a missing anchor; `set -e` stops without rows, best-effort evidence fields, `--help` and Cargo's ambient inputs, and sequential removals at assembly were unstated; the inputs list had been merged into one item by a reflow. | Adjudicated 2026-10-09: correct the documentation. | Implemented in the prose and the generator: the figure follows each variant's path with a correct legend and link, an invocations table renders the manifest's invocations, and the inputs list is a list again. The authored prose grew past the size target with the added precision. |

## Register details

Initial pass executed 2026-10-09 at 209e11c (the commit that holds this plan)
on a clean tree; no build file changed between the survey and the pass, so the
survey's rows were refreshed only by verification. Probe logs and scripts are
local and disposable under `.tmp/probe-row1/`, `.tmp/probe-row1b/`,
`.tmp/probe-row6/`, `.tmp/probe-row9/` and `.tmp/probe-row11/` (the clone
probes: `run.sh`, `run2.sh`, `run3.sh` and their logs); the commands and the
decisive outputs are transcribed below so the conclusions survive their loss.
The `source_drift` suite passed at this revision into
`tests/out/runs/build-doc-step1-drift` (five cases), which is the baseline for
step 2. The pass was audited the same day; the audit prompt and its appended report were a working file, since removed from the tree at the user's request (its text survives in the repository's history before 2026-10-10), and its fourteen text corrections are applied below with its verdict noted in the table. Adjudicated 2026-10-09: rows 11,
13, 14, 16, 17, 18, 19 and 20 are build fixes, implemented in step 2 with the
controls the table names; the rest are documentation, accepted limitations or
stated trust bounds. Step 2 validation is recorded at the end of this section.

Signing in the clone probes used the real Developer ID identity, so the
keychain was exercised unattended; the ad hoc seals in the row 1 probes are
noted where they limit a conclusion.

### 1. The signing list and the other inventories

- **Claim.** The script's signing list is compared with nothing; a helper
  copied but not listed for signing is caught only when the inspector runs.
  Variants: both. Consequence if the survey were right: an unsigned or ad
  hoc-signed tool ships unnoticed until notarization. - **Source.** `build.sh`
  signs five Mach-Os through `sign_macho` (`pw-runner-client` only under
  `BUILD_XPC=1`, `sandbox-log-observer`, `sbpl-check`, and per service
  `pw-probe-runner` and `sb_api_validator`), seals the service bundle and the
  app, and signs the out-of-bundle observer last. `policy-witness` and
  `PWRunner` are signed by their seals only. `EXECUTABLES` lists seven paths;
  the README lists the same seven plus the evidence directory;
  `tests/build-evidence.py` hardcodes three top-level names in `helper_names`
  and discovers the service's siblings by walking its `MacOS` directory. No
  rule compares the four. The inspector's `manifest_missing` requires
  `EXECUTABLES[1:]` plus the symbols file, so a helper absent from both
  `EXECUTABLES` and `helper_names` is silently absent from the evidence
  manifest. - **Probe (unsigned helpers), `.tmp/probe-row1/probe.log`.** Four
  copies of `dist/PolicyWitness.app` (valid at start): a control; a listed
  helper with its signature removed; an unlisted, unsigned Mach-O added as
  `Contents/MacOS/extra-tool`; a service helper with its signature removed.
  Each was sealed ad hoc with the app entitlements, then verified with
  `codesign --verify --deep --strict`. Control: seal 0, verify 0. Unsigned
  listed helper: the seal itself refused, "code object is not signed at all,
  In subcomponent: .../Contents/MacOS/sbpl-check", status 1. Unsigned extra
  tool: the seal refused the same way. Unsigned service helper: the service
  seal refused; the outer seal then succeeded over the service's old seal and
  the deep verify failed. Under `set -e` the build stops at the first of
  these. Limit: the outer identity was ad hoc; the refusal is codesign's
  nested-code rule under the default resource rules and does not depend on the
  signer. A Mach-O placed outside a nested-code directory (for example under
  `Resources`) would be sealed as a resource; not probed. - **Probe (ad hoc
  helpers), `.tmp/probe-row1b/probe.log`.** Every compiler output is ad
  hoc-signed by the linker: `codesign -dvv` reports `Signature=adhoc` for
  `builddir/sb_api_validator`, `pw-probe-runner`, `pw-runner-client`,
  `controller/target/release/sbpl-check` and `policy-witness`. A listed helper
  re-signed ad hoc, and an unlisted `extra-tool` copied straight from
  `builddir`, each under an outer seal with the Developer ID identity
  (`--timestamp=none`): seal 0, deep verify 0, and `tests/lib/artifact.py`
  returned 0 for the extra tool (1 for the re-signed listed helper only
  because its manifest hash changed; the audit's real build with one signing
  call removed had a matching manifest hash, a clean seal, deep verify and
  inspection, and an ad hoc `sbpl-check`). No test or release check reads
  `Authority` or `TeamIdentifier` (grep over `tests/lib`, the preflight checks
  and `tests/accept-release.sh`: none). - **Conclusion.** The survey sentence
  is wrong in both directions: an unsigned nested Mach-O is refused by the
  seal, before the inspector; an ad hoc-signed one is refused by nothing
  local, and notarization is the gate the documents name. What remains of row
  1 is the inventory agreement, which nothing checks. The signer gap is row
  13. - **Adjudicated 2026-10-09 (as recommended):** strengthen verification
  through the step 3a drift rule (parsed `sign_macho` and `codesign` calls,
  with branch scope, against `EXECUTABLES`, `helper_names` and the README,
  seals distinguished from signatures) and correct the documentation
  (`BUILD.md` states what the seal refuses and what only notarization
  refuses). Affected: survey item 2; the "add it to that list" paragraph under
  "What `build.sh` signs"; row 13.

### 2. Two exit statuses

- **Claim.** A refusal carries one of two exit statuses. Variants: both.
- **Source.** All 24 `ERROR:` sites in `build.sh` are followed by `exit 2`;
  the Makefile guards exit 2. Checks the script runs: the four generators'
  `--check` return 1 on a stale copy and `generate_architecture.py` returns 2
  from its `except` branch; `tests/lib/native_sources.py` returns 1 for a
  list or closure problem and 2 when Meson or Ninja cannot be read;
  `tests/build-evidence.py` returns 2 for a missing `Contents`. Tools: Cargo
  101, Meson and Ninja 1, codesign 1, PlistBuddy 1. Under `set -e` the script
  exits with the failing command's status.
- **Assertion coverage.** `contract.py`
  `test_build_refuses_a_non_developer_id_identity_before_cargo` asserts 2;
  `test_build_refuses_stale_contract_copy_before_signing_or_creating_output`
  asserts 1; `limits.py`
  `test_build_refuses_stale_guide_before_signing_or_creating_output` asserts
  1. Observed in the clone probes: identity refusal 2 (adverse C), minimum
  refusal 2 (adverse A2), Ninja failure 1 (probe K), Cargo failure 101 (the
  invalid-version probes A and B).
- **Classification.** Supported behavior needing explanation.
- **Adjudicated 2026-10-09 (as recommended):** correct the
  documentation: the manifest records each refusal's status; the prose states
  the rule (the script's own refusals exit 2; a check's or a tool's refusal
  propagates that tool's status). Harmonizing would wrap every check to exit
  2 and rewrite two control assertions for no behavioral gain.

### 3. Build-time checks under `tests/`

- **Source.** `build.sh` runs `tests/lib/native_sources.py --builddir` after
  compiling and `tests/build-evidence.py` after the nested signatures.
  `tests/lib/meson_receipts.py` is run by nothing in the build, the Makefile
  or the default battery (its only references are documentation). The source
  check is shared with `tests/suites/source_drift/check.py` and
  `check_planner.py`; the evidence manifest is read back by
  `tests/lib/artifact.py` and by the controller's provenance checks.
- **Classification.** Documentation ownership; supported behavior.
- **Adjudicated 2026-10-09 (as recommended):** accept and explain: the
  build runs two helpers that live with the tests because the suites import
  the same code. A move to a build-side directory is possible and changes no
  behavior; the manifest cites the helpers where they live.

### 4. The identity's place in the build order

- **Source.** Generation at `build.sh` line 114, after the three document
  checks and before the stamp, the plist, the identity and Cargo; the check at
  line 425, after assembly and before the entitlements check and the first
  signature. The contract's sentence and the signing document's order list
  agree with the script.
- **Observed.** Control build (`.tmp/probe-row11/control.log`): the banners
  in that order, and "ok: worker identity …; all generated copies current"
  immediately before "Codesigning embedded MacOS tools".
- **Adjudicated 2026-10-09 (as recommended):** correct the
  documentation (ownership): the generated step table owns the ordering; the
  contract keeps the definition and digest scope and points at the build
  document for when the build runs it; the signing document's sentence moves
  with its Build section. Whether the pre-compile step should generate or
  check is row 14.

### 5. The Makefile's prose account

- **Source.** The header's per-target sequence matches the recipes: `build`
  guards `IDENTITY` and runs `build.sh`; `notarize` guards two variables, runs
  the preflight in report mode, `$(MAKE) build`, then the evidence directory,
  submission, staple, validation, Gatekeeper, re-zip and acceptance in one
  shell; `release` runs the strict preflight, `$(MAKE) notarize`, a second
  strict preflight to obtain the version (which refuses a tree the build
  dirtied), the battery, the archive and the rotation; `publish` guards
  `VERSION`. The `build` guard refuses an empty `IDENTITY` with its own
  message and status 2 before `build.sh` can. Twelve `==> [target]` phase
  lines; no rule reads them. - **Classification.** Documentation; no
  behavioral issue. - **Adjudicated 2026-10-09 (as recommended):** correct the
  documentation: the manifest's steps begin at `make build` and its guard is
  the first refusal of the public entry; the header stays as the Makefile's
  own micro account, like the comments in `meson.build`; an optional grounding
  rule compares the `==> [build]` line with the manifest. The release chain
  stays in the signing document.

### 6. The partial bundle

- **Observed (adverse B2, clone at 209e11c, reused directories,
  `.tmp/probe-row11/probe2.log`, `adverseB2.log`).** `BUILD_XPC=0` with the
  plist at 15.0 (see row 11): status 0; `meson configure` with `xpc=false`;
  the source check passed with two targets; "Skipping embedded XPC build";
  two helper signatures; evidence; seal; verify; observer; guide; ZIP; and the
  closing text recommends `make notarize`. The bundle holds three Mach-Os;
  the evidence manifest lists `sandbox-log-observer`, `sbpl-check`, the
  augment and the symbols file; `codesign --verify --deep --strict` returned
  0; `tests/lib/artifact.py` returned 1 with `required_component` for
  `pw-runner-client`, `PWRunner`, `pw-probe-runner`, `sb_api_validator` and
  the service `Info.plist`, plus `manifest_missing` for the four executables.
- **Observed (specimen run, earlier partial bundle at 5e5f86d,
  `.tmp/dist-noxpc`, `.tmp/probe-row6/probe.log`).** `policy-witness run
  tests/fixtures/pw_runner/specimen_exec_spawn.json` exits 2 with
  `result.error` "built-in runner unavailable: … evidence manifest has no
  entry at Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner"; no
  runner is launched.
- **Variant facts the document must carry.** The minimum-version check runs
  only on the three Rust binaries, because nothing Meson-built ships; the
  signing list is two signatures, the app seal and the observer; the
  configured-source check expects two targets (the worker and the validator);
  no Swift compiler is discovered; the dSYM step does not run; the ZIP is
  still written under the release name.
- **Classification.** Supported behavior needing explanation; one coverage
  gap (the minimum agreement, row 11).
- **Adjudicated 2026-10-09 (as recommended):** correct the
  documentation (every manifest item carries its variants; the partial
  bundle's refusal set is explicit) and accept the limitation. Optional small
  build fix for the human to decide: skip the ZIP and the notarize hint when
  `BUILD_XPC=0`, so the partial bundle cannot be submitted by habit.

### 7. The validator's parallel compile path

- **Source.** `controller/tools/sb_api_validator/build.sh` compiles with
  `cc -Wall -Wextra -O2 -std=c11` beside the source and ad hoc-signs with
  `debug.ent`; `.gitignore` ignores the output; an ignored output dated
  2026-10-07 exists locally. The shipped validator is Meson's
  (`builddir/sb_api_validator`, copied into the service in the control build).
  The signing document's "never production-signed" paragraph is accurate.
- **Adjudicated 2026-10-09 (as recommended):** correct the
  documentation (ownership): the paragraph moves to the build document's
  signing section and is stated once. No code change.

### 8. The harness note

- **Source.** `check_harness_note_agreement` in
  `tests/suites/source_drift/check.py` compares the whitespace-normalized
  first paragraph under the heading across `HARNESS_NOTE_FILES` (AGENTS.md
  canonical, `runner/README.md`, `tests/README.md`, `docs/SIGNING.md`); each
  copy adds a local paragraph, and the signing document's addition is the
  "two build steps need an unsandboxed shell" paragraph. AGENTS.md's second
  paragraph names the four copies and what each adds. The architecture
  document's generated table cites the AGENTS, runner and tests copies;
  `docs/architecture.json` does not reference `SIGNING.md`.
- **Adjudicated 2026-10-09 (as recommended):** correct the
  documentation and update the rule at step 5: the signing copy and its
  second paragraph move to `BUILD.md`; `HARNESS_NOTE_FILES`, the comment above
  it, the rule's "four places" message and the AGENTS.md pointer change in the
  same commit; the count stays four. No issue.

### 9. Cargo's inputs

- **Source.** Cargo receives `PW_BUILD_VERSION`, `PW_BUILD_NUMBER`,
  `PW_BUILD_DESCRIBE` and `PW_BUILD_COMMIT` (declared `rerun-if-env-changed`
  in `controller/build.rs`, which also declares `../docs/contract.json`),
  `MACOSX_DEPLOYMENT_TARGET` exported from the plist, `RUSTFLAGS` `-C
  debuginfo=2 -C force-frame-pointers=yes -C opt-level=1` only when
  `PW_INSPECTION=1` and `RUSTFLAGS` is unset or empty (a caller's value wins
  silently, as the signing document says), `--release` and three `--bin`s.
  `SDKROOT` was exported after Cargo, so Cargo inherited a caller's value or
  resolved the SDK through `cc` and `xcrun`'s default; since row 19 it is
  selected once, before Cargo and Meson. `DEVELOPER_DIR` passes through. -
  **Probe, `.tmp/probe-row9/probe.log` (corrected series; the first series
  used 25.0, which clang rejects as an invalid version).** `cargo build
  --release --bin sbpl-check` into a scratch target directory: variable unset,
  minos 11.0 (rustc's default for `aarch64-apple-darwin`, not the SDK's 27.0);
  26.0, minos 26.0; then 15.0 on the same directory recompiled `objc2`,
  `block2`, `dispatch2`, `ctrlc` and `controller` and relinked to 15.0; 15.0
  again did no work; 26.0 again recompiled the same five and relinked to 26.0.
  So the crates that read the variable at compile time are re-fingerprinted
  and the link always applies the current value; the pure Rust dependencies
  are not rebuilt and carry no minimum. - **Adjudicated 2026-10-09 (as
  recommended):** correct the documentation: the inputs section lists them; it
  states that a reused `controller/target` follows the current deployment
  target (observed) and that the exercised arm64 `sbpl-check` build with the
  deployment target unset yielded minos 11.0 on the recorded toolchain, which
  the minimum check would refuse if copied; neither is a cross-target or
  future-toolchain guarantee. `SDKROOT` is now selected before Cargo (row 19)
  and the output directory is pinned (row 17).

### 10. The receipts

- **Source.** Nothing in `build.sh`, the Makefile or the default battery
  writes a receipt; `tests/lib/meson_receipts.py` is a comparison tool
  documented under "Comparing native builds". The signing document's "Native
  compile with Meson" section narrates "the receipts record each output's
  minimum version" and "The receipt pairs each output's hash and mtime…"
  inside the build account.
- **Adjudicated 2026-10-09 (as recommended):** correct the
  documentation: `BUILD.md` says the build writes no receipt and that the
  comparison tools can record one from the build directory afterwards, linking
  the tests README; the two passages are reworded when the sections move.

### 11. The supported macOS

- **Claim.** Declared in two places, enforced in a third; no rule compares the
  two declarations. Consequence if the declarations disagree: binaries built
  for one minimum ship under a plist that declares another. - **Source.**
  `Info.plist` declares 26.0; `meson.build` pins `macos_minimum = '26.0'` at
  compile and link; `build.sh` reads the plist (refusing a value that is not
  major.minor), exports it to Cargo, and `check_minimum_macos` requires the
  first `LC_BUILD_VERSION` minos to equal the plist for every copied Mach-O:
  the three Rust binaries at assembly, the client and the three service
  binaries inside the XPC block. A binary without the load command yields "?"
  and is refused. - **Probes (clone of 209e11c, `.tmp/probe-row11/`).**
  Control: plist 26.0, `BUILD_XPC=1`, fresh directories, status 0, every
  shipped Mach-O 26.0 (`probe.log`). Adverse A2 (`probe2.log`,
  `adverseA2.log`): plist 15.0, `BUILD_XPC=1`, reused directories: Cargo
  rebuilt five crates and the Rust binaries came out 15.0; the refusal was
  "pw-runner-client is built for macOS 26.0; Info.plist declares 15.0", status
  2, before any signature. Adverse B2: plist 15.0, `BUILD_XPC=0`: status 0; a
  signed bundle declaring 15.0 with three 15.0 Mach-Os while the manifest pins
  26.0 and the C outputs in `builddir` are 26.0. (Adverse A and B at 25.0 were
  invalid probes: clang rejects the value and Cargo exits 101 before any check
  of ours runs.) - **Conclusion.** The two declarations are compared only
  through shipped Meson outputs: only in `BUILD_XPC=1` builds and only at
  assembly. The signing document's "changing the plist and the manifest
  together" is an unenforced rule in the partial variant. - **Adjudicated
  2026-10-09:** fix the build. Implemented: every Cargo output is
  minimum-checked right after Cargo and every Meson output (the two C
  executables in both variants, the client and the host in full builds) right
  after the configured source check, all before assembly; the copy-time checks
  are gone and no literal is parsed. The audit's caution that a parsed literal
  can drift from applied flags is why the applied value is checked instead.
  Validation: probes B3 and A3 under Step 2 validation.

### 12. Operator steps and automatic steps

- **Classification of the signing document's Build section.** Operator,
  unenforced: the toolchain (Command Line Tools or Xcode, `DEVELOPER_DIR`, the
  SDK `xcrun` reports), separate build directories per toolchain and a fresh
  one after a toolchain change ("not fingerprinted"), an unsandboxed shell,
  network for the timestamp service, and a clean checkout at the release
  commit (enforced only by the release preflight). Enforced by the build: the
  document checks, the knob values, the Ninja minimum, Meson and Ninja
  present, the identity's class and presence in the keychain (not that the
  keychain is unlocked), Cargo's outputs present, Meson's policy assertions,
  the configured source lists and closure, the minimum version, identity
  currency, the entitlements file, the `sign_macho` target rules, the seals
  and the deep verify.
- **Adjudicated 2026-10-09 (as recommended):** correct the
  documentation: `BUILD.md` separates what the operator must ensure, each item
  marked unenforced, from what the build refuses; the manifest keeps
  prerequisites apart from refusals so the generated table cannot blur them.

### 13. No local check reads the signer (found in step 1)

- **Claim.** Every embedded tool is production-signed before the seal; an
  embedded tool left ad hoc-signed is refused. Variants: both. Consequence: an
  ad hoc-signed tool ships in the ZIP and is refused only by notarization. -
  **Evidence.** The row 1 ad hoc probe: the linker leaves every compiler
  output ad hoc-signed; a listed helper re-signed ad hoc and an unlisted ad
  hoc helper both pass the Developer ID seal, the deep verify and the
  inspector. After the seal, `build.sh` runs only the deep verify and an
  entitlements display; neither reads the authority. AGENTS.md and the signing
  document say notarization fails in this case, which is accurate and is the
  whole of the guard. - **Classification.** Evidence and coverage gap. -
  **Adjudicated 2026-10-09:** fix the build. Implemented:
  `tests/lib/signer_check.py`, run by `build.sh` after the deep verify and
  before the observer and the ZIP, requires every regular file directly under
  the app's and each service's `Contents/MacOS`, whether or not the signing
  list named it, to be a Mach-O whose leaf authority is the named identity
  with the hardened runtime; the dSYM bundles are outside those directories
  and are not checked, and the inspector stays signer-agnostic because
  `native_substitute.py` and the BYOXPC controls inspect ad hoc copies.
  Control: `check_signed_artifacts.py` re-signs one helper ad hoc on a
  disposable copy and requires exactly that path to be named. Validation:
  probe S3 under Step 2 validation.

### 14. A stale committed identity is regenerated, not refused (found in step 1)

- **Claim.** The build refuses stale generated copies before compiling. For
  the identity it does not: line 114 regenerates, and only line 425 checks. -
  **Probe (adverse C, `.tmp/probe-row11/probe.log`, `adverseC.log`).** In the
  clone, the identity in `tests/lib/contract.py` was replaced with zeros and
  committed, giving a clean tree at `v0.2.7-39-g5026b47`. `build.sh` with a
  non-Developer-ID identity: the generation step rewrote the file, the stamp
  line read `v0.2.7-39-g5026b47-dirty`, the identity refusal followed with
  status 2, and `git status` showed `M tests/lib/contract.py`. The `--check`
  afterwards reported every copy current. - **Consequence, before the fix.** A
  clean checkout whose committed identity copies were stale built with a
  `-dirty` stamp and a modified tree. The release preflight checks cleanliness
  before the build and again, in version mode, after notarization and
  acceptance and before the battery, so the second call refused the dirtied
  tree; `release_archive.py` and `release_runs.py` independently refuse a
  stamp that is not exactly the tag. The cost was a spent submission and a
  late refusal, never a dirty archive. - **Classification.** Build defect
  against the "every refusal precedes the step it protects" promise, or
  intended convenience: the contract says the build "generates … before
  compilation" so a worker edit never needs a manual regeneration. -
  **Adjudicated 2026-10-09:** refuse in ordinary builds. The audit held that
  regeneration was documented behavior and a design choice; the choice made is
  the simpler machinery: the build writes nothing into the tree, the four
  generators follow one rule, the dirty-stamp case cannot arise, and no
  release-specific guard is needed. Implemented: the pre-compile step runs
  `--check`, the contract says the build checks before compiling and again
  before signing and never writes, the signing document's order and the
  AGENTS.md checklist say the same, and the generator's docstring too.
  Control:
  `test_build_refuses_a_stale_identity_copy_before_compiling_and_writes_nothing`
  in `contract.py`. Validation: probe I3 under Step 2 validation.

### 15. A refusal after assembly leaves a partial bundle (found in step 1)

- **Observed (adverse A2).** `rm -rf` of the previous app happens at assembly,
  before the minimum, identity and signing refusals. After the minimum
  refusal, `dist-a2/PolicyWitness.app` held `policy-witness`,
  `pw-runner-client`, `sbpl-check` and `sandbox-log-observer` with the
  linker's ad hoc signatures, `Info.plist` and the augment; no evidence, no
  service, no seal, no ZIP. The previous build at that path is gone. -
  **Consequence.** A battery or a user pointing at the output path after a
  failed build finds the remains; the dispatcher's inspector refuses them
  (`signature` and `required_component`), and the controller refuses to run a
  specimen without an evidence manifest (row 6). The full inspector rejects
  incomplete output and the default built-in specimen path refuses missing
  evidence; direct helper execution and, before row 18, the previous ZIP and
  guide were outside that conclusion. The last good app is destroyed by a
  refusal that comes later. - **Classification.** Supported behavior needing
  explanation, or a small build fix. - **Adjudicated 2026-10-09:** accept and
  document, with the row 18 fix. Assembly now removes the previous app, ZIP
  and guide together, and the minimum checks moved before assembly, so what a
  later refusal leaves is an unsealed partial bundle carrying the linker's ad
  hoc signatures in the observed case and other states after later refusals,
  with no release-named sibling beside it. Transactional replacement was not
  adopted. Validation: probe R3 under Step 2 validation.

### 16. The build trusts the build directory's recorded source (found in step 1)

- **Claim.** `builddir/` is trusted working state like the checkout, and the
  configured-source check guarantees that what Meson evaluated is the tree.
  Consequence if false: the bundle carries binaries compiled from another
  checkout while every check passes. - **Probe K
  (`.tmp/probe-row11/probe2.log`, `probeK.log`).** The clone with its
  configured `builddir` was copied to `src2` (excluding `controller/target`),
  a live marker symbol was appended to the worker source and the identity
  regenerated and committed there (identity `e3f00bf1…` against the original's
  `52f1dc03…`). `meson-info.json` in the copy still recorded the original as
  its source directory. `build.sh` ran `meson configure` without complaint;
  Meson printed "Source dir: …/src"; Ninja compiled
  `…/src/controller/tools/pw_probe_runner/pw_probe_runner.c`; the build then
  stopped in the Swift targets only because the copied module cache's
  precompiled files record their own path, status 1. - **Probe K2
  (`probe3.log`, `probeK2.log`).** With `src2/builddir/ swift-module-cache`
  removed, the same build completed with status 0. The configured-source check
  printed "ok: 5 native targets carry exactly the tree's sources and the
  identity targets consumed only digest inputs (…/src2/builddir (xpc=true))",
  because it compares against the source directory the build directory
  records. The identity check in `src2` passed. The shipped worker contained
  no marker and carried the identity `52f1dc03…`; `src2`'s tree says
  `e3f00bf1…`. Deep verify 0, inspector 0, ZIP written. A signed, packaged
  bundle built from the wrong checkout, with every check clean. - **Limits.**
  Reached by copying a checkout together with its build directory, a plausible
  copied-workspace scenario, although the disposable-copy instruction does not
  require copying incremental state and the harness note prescribes an
  unchanged-byte rerun outside the sandbox. Not reached by a fresh clone or a
  worktree, which have no build directory. The incidental Swift stop protects
  only full builds with an untouched module cache. - **Classification.** Build
  defect against the "what Meson evaluated must be the tree" promise. -
  **Adjudicated 2026-10-09:** fix the build. The audit located the defect in
  the boundary: the configured reading took both roots from the build
  directory's own record. Implemented: `build.sh` refuses before Cargo when
  the build directory's recorded source directory, canonicalized, is not this
  checkout, naming both; `native_sources.py --root` repeats the comparison in
  the configured reading, and `build.sh` passes its root. Controls:
  `test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo`
  in `contract.py` (a record naming another directory, the checkout itself,
  and an unreadable record) and the `configured-copied-checkout` scenario in
  `check_planner.py` (the compiled copy copied again). The Meson observation
  stays bounded to 1.12.1. Validation: probe K3 under Step 2 validation.

### 17. Cargo's output directory could diverge from the paths assembly reads (audit)

- **Claim.** The script let Cargo inherit its configuration and environment
  but copied fixed `controller/target/release/` paths afterwards, so a
  `CARGO_TARGET_DIR` or a Cargo configuration value could send new outputs
  elsewhere while stale executables remained at the copied paths. Variants:
  both. Consequence: stale Rust tools packaged under a new stamp with every
  other check passing.
- **Evidence.** Source reading by the audit, confirmed: the three `_BIN` paths
  were literals and the `cargo build` line carried no `--target-dir`. Cargo's
  command-line flag overrides both the environment variable and
  configuration.
- **Adjudicated 2026-10-09:** fix the build. Implemented: `cargo build
  --target-dir` pins the output directory to the checkout's and the three
  copy paths derive from the same variable. Validation: probe T3 below.

### 18. A failed build left the previous ZIP and guide beside new partial output (audit)

- **Claim.** Assembly removed the app but the ZIP was removed only at
  packaging and the guide staged late, so after a failed build the previous
  release-named ZIP and guide stood beside the residue. `make notarize`
  always rebuilds, so the automated chain never submitted them; a manual step
  could.
- **Adjudicated 2026-10-09:** fix the build, folded into row 15. Implemented:
  assembly removes the previous app, ZIP and guide together. Validation:
  probe R3 below.

### 19. SDK selection was neither uniform nor a checked assignment (audit)

- **Claim.** `SDKROOT` was exported after Cargo, so Cargo inherited any
  caller's value or resolved the SDK through `cc` and `xcrun`'s default; and
  `export SDKROOT="$(xcrun …)"` returned the builtin's status, so a failed
  lookup left an empty variable under `set -e` and Meson fell back to its own
  resolution. Consequence: two SDK selections where the documents describe
  one, and a silent fallback where a refusal was promised.
- **Evidence.** Source reading by the audit, confirmed against the script;
  the shell semantics are the documented behavior of `export`.
- **Adjudicated 2026-10-09:** fix the build, and decide the contract as one
  SDK for every compiler. Implemented: the SDK is selected once, before the
  signing identity, Cargo and Meson, with an explicit refusal when `xcrun`
  fails or returns no directory, and the selection is printed as a banner.
  Validation: probe D3 below (a failed selection refuses before Cargo); the
  control build selects the same SDK Meson used before.

### 20. Empty knobs were defaults, and "every other native setting" overstated an enumerated list (audit)

- **Claim.** `${BUILD_XPC:-1}` read an empty value as `1` while the documents
  said any other spelling is refused; Meson's assertions enumerate specific
  options, so "every other native setting is fixed" claimed more than the
  list.
- **Adjudicated 2026-10-09:** fix the knob; correct the documentation.
  Implemented: `${BUILD_XPC-1}` and `${PW_INSPECTION-1}`, so an unset knob
  means `1` and an empty one is refused with the other spellings; the signing
  document says "the native settings `meson.build` enumerates". Control:
  `test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check` in
  `contract.py` (empty, `2`, ` 1` and `true` refused with status 2 before any
  check; unset, `0` and `1` reach the first documentation check). Validation:
  probe E3 below.

### 21. The identity check before signing is a copy-currency check, not a binary snapshot (audit)

- **Claim.** The late check compares the generated copies with the current
  tree, not identities read from compiled outputs; an edit to an identity
  input during the build followed by regeneration passes it. "Refusing a
  source edit made during compilation" promised more than the mechanism.
- **Adjudicated 2026-10-09:** accept as a trust bound; correct the
  documentation. The signing document's gate paragraph and the script's
  comment now say the check refuses an identity input edited during the build
  without regeneration, and that the build otherwise trusts the checkout not
  to change under it. No mechanism change; no control, since the bound is a
  stated assumption rather than a guarantee.

### Step 2 validation

Executed 2026-10-09 against the changed working tree (the step 1 register
commit plus the step 2 edits), in a copy under `.tmp/probe-step2/` that
excludes build products and `.git`; scripts `run4.sh` and `run5.sh`, logs
beside them, local and disposable. Observed:

- **Row 16, probe K3.** The copy was copied again together with its configured
  `builddir`; the build in the second copy refused before Cargo: "builddir is
  configured for …/src, not this checkout (…/src2); remove it or use a fresh
  build directory", status 2, no Cargo banner, no output directory. The
  configured reading named the same pair: `native_sources.py --builddir
  src2/builddir --root src2` exited 1 with "configured for …/src, not …/src2".
- **Row 11, probes B3 and A3.** Plist 15.0 with `BUILD_XPC=0` and with
  `BUILD_XPC=1`, reused directories: both refused right after the configured
  source check, "sb_api_validator is built for macOS 26.0; Info.plist
  declares 15.0", status 2, assembly not reached, no output directory. The
  declarations can no longer disagree in a build that completes, in either
  variant.
- **Row 14, probe I3.** The identity in `tests/lib/contract.py` zeroed:
  refused at the third banner, "stale tests/lib/contract.py; run python3
  docs/generate_worker_identity.py", status 1, no stamp, no Cargo, and the
  copy's bytes unchanged by the build.
- **Row 19, probe D3.** With the SDK name made invalid in the copy's script:
  "xcrun could not select the macOS SDK (DEVELOPER_DIR=unset)", status 2,
  after the supported-macOS banner and before the signing identity and Cargo.
- **Row 20, probe E3.** `BUILD_XPC=` (empty): "BUILD_XPC must be 0 or 1 (got
  '')", status 2, before any check.
- **Controls run directly.** The four `contract.py` build controls (identity
  class, stale identity copy, knob values, build directory) pass.
- **Control build.** The copy built completely with reused directories: the
  SDK banner, every output at 26.0, "ok: 7 executables signed by … with the
  hardened runtime", app, ZIP, guide and the two dist documents present.
- **Row 13, probe S3.** With the `sbpl-check` signing line removed from the
  copy's script and the identity regenerated, the build wrote the evidence,
  sealed the app and passed the deep verify, then refused at the signer check,
  "Contents/MacOS/sbpl-check: signed by ad hoc, not Developer ID Application:
  …", status 1; no ZIP was written and the observer was not re-signed.
- **Row 17, probe T3.** `CARGO_TARGET_DIR` pointed outside the copy and
  `PW_VERSION=9.9.9`: Cargo recompiled the controller into the pinned
  directory, the other directory was never created, and the shipped
  controller's `--version` and the plist both carry 9.9.9. (A first attempt
  used `PW_BUILD_DESCRIBE`, which the script derives from git and does not
  honor as an override, so it did not discriminate; this is why the version
  override was used.)
- **Rows 15 and 18, probe R3.** The control's output directory held the app,
  ZIP and guide; with the entitlements file removed, the build refused after
  assembly, "missing entitlements plist", status 2, and left only the partial
  app (seven executables with the linker's ad hoc signatures) and the two dist
  documents: the previous ZIP and guide were gone.
- **Drift suite.** `tests/run.sh --suite source_drift` into
  `tests/out/runs/build-doc-step2-drift-2`: five cases pass, including the
  four new `contract.py` controls, the `configured-copied-checkout` planner
  scenario and the generator contract over the changed `build.sh`. The first
  attempt (`build-doc-step2-drift`) failed on two mistakes of this pass, both
  corrected: the knob control's checkout lacked `build.sh`, and the prose
  rule caught a byte count the audit report stated in prose; the number was
  removed from that report, the fact is unchanged.
- **Rebuild.** `make build` with the Developer ID identity rebuilt
  `dist/PolicyWitness.app` through the changed script; the signer check
  reported all seven executables.
- **Default battery.** `tests/run.sh` into `tests/out/runs/build-doc-step2-default`:
  170 of 170 passed, none skipped or unrun, no harness errors, app unchanged
  through the run. Every gate the plan requires for a changed `build.sh`
  ran green on the changed revision.

### Step 3a record

Built 2026-10-09 on the step 2 tree. What exists now:

- **Manifest.** `docs/build.json`, schema version 2 like the others, with
  steps (ordered, each with its banners, variants, what it reads and writes
  and the refusals it can raise), refusals (message, kind, steps, status,
  variants), the signing list in script order (target literal, signature or
  seal, entitlements, loop and step), the helper invocations with their steps,
  the two knobs, and three directories with "Trusted as" and "Refused when"
  facts. Every item cites a source symbol and at least one test or rule; each
  check citation carries a coverage kind: `behavioral` (a control drives the
  build and observes the refusal), `helper` (a control exercises the helper
  that produces it, not the build path) or `textual` (a grounding rule). The
  first step is the Makefile's `build` target, marked `where: Makefile`; the
  second, `admission`, has no banner and holds the refusals that fire before
  the first one.
- **Generator.** `docs/generate_build.py`, the fifth generator, reusing the
  architecture generator's table, citation, stamp and SVG rendering. It parses
  `build.sh`, compares the manifest with it and with `meson.build`, the
  Makefile, `EXECUTABLES`, the evidence generator's helper list, the README
  inventory and the baseline, and refuses a disagreeing manifest before it
  writes. It writes the step figure (`docs/build-steps.dot` and `.svg`, stamped)
  and six regions of `docs/BUILD.md`: figure, steps, refusals, signing, knobs,
  directories, plus spans for the counts. `build.sh` runs its `--check` under
  a new banner beside the other generator checks.
- **Parser.** The forms it accepts are stated in the generator's docstring: a
  banner is a top-level `echo "==> …"`; a refusal is a double-quoted
  `echo "ERROR: …" 1>&2` or a stderr heredoc, followed within three lines by
  a constant `exit N`; a signature is a `sign_macho "…"` call and a seal a
  `codesign --force` command; helpers run as `"${ROOT_DIR}/<path>"`; branches
  are `if`/`else`/`fi` (variants from the `BUILD_XPC` tests), loops
  `for`/`done`, and `case`/`esac` may hold refusals but no banner. A refusal
  inside a function belongs to the steps that call it. It refuses an `elif`,
  a banner in a function or case, an `ERROR` echo without a constant exit or
  not double-quoted, a `codesign` that is neither seal nor verification, an
  unterminated heredoc, an unbalanced block and a refusal in a function that
  is never called.
- **Grounding rules.** Ten, in `tests/suites/source_drift/build_rules.py`,
  each a function called from its `main()` so the `rule` citation form
  applies: banner order with variants, refusal messages with steps, statuses
  and variants, Meson's assertions, propagated refusals against invocations,
  knobs, signing order, invocations, the Makefile's build entry, the signing
  inventory against `EXECUTABLES`, `helper_names` and the README (a listed
  service bundle implies its main executable), and the baseline.
- **Baseline.** `tests/fixtures/docs/build_baseline.json`: one entry per
  refusal with neither a behavioral nor a helper control, each with its
  variants, the claim and the control that would produce it. The rule
  requires exact agreement in both directions, and `release_preflight.py`
  now refuses a grown or rewritten build baseline against the previous
  release the way it refuses the prose baseline.
- **Drift case.** `build_documentation` in the `source_drift` suite: the
  generator's check and the rules; manifest refusals (broken citations,
  references, ids, forms, coverage, variants, schema, self-citation); every
  id in its region; captions stating only what was verified; SVG stamps; stale
  copies refused then regenerated idempotently; a broken marker, a broken
  citation or a disagreeing script refused before any write; fifteen script
  mutations each named by its rule; eight unsupported forms refused by the
  parser; Meson, Makefile, inventory and baseline mutations named; the
  release growth refusal.
- **Gates.** `tests/run.sh --suite source_drift` into
  `tests/out/runs/build-doc-step3a-drift-2`: six cases pass, the new one
  included and the generator contract at five generators. The real app
  rebuilt through the changed script, with the build documentation check
  and the signer check reporting clean. The default battery into
  `tests/out/runs/build-doc-step3a-default`: 171 of 171 passed (the new
  case included), none
  skipped or unrun, no harness errors, app unchanged through the run.
- **Registration.** The generator contract runs over five generators (G1 to
  G11 unchanged); the document graph gained the manifest, generator,
  document, baseline and case nodes with their edges; the suite README and
  the catalog describe the case.

What the first run of the machinery counts:

| Class | Refusals | With a behavioral or helper control | In the baseline |
| --- | --- | --- | --- |
| the script's own `ERROR:` sites | 27 | 5 | 22 |
| Meson policy assertions | 21 | 0 | 21 |
| propagated from a check or a tool | 15 | 6 | 9 |
| the Makefile's guard | 1 | 0 | 1 |

Found while building the machinery, and settled without changing behavior:

- Four refusals fired before the banner of the step they protect (the plist
  minimum, the SDK, the client output) or under no banner at all (the build
  directory, the signing identity, the native toolchain, the identity check
  before signing). The parser's rule is that a refusal belongs to the banner
  that precedes it, which is honest only if every refusal follows its step's
  banner, so the banners were moved before their checks and four were added.
  The SDK selection prints its path as an indented line under its banner.
- The step 2 validation remains valid: no refusal, check or signing call
  changed, only where its banner prints. The step 2 control assertions that
  named the old "Selected SDK" banner were updated.
- The audit's coverage tables were right in scale: of the sixty-four
  refusals the manifest names, fifty-three have no control that produces them.

Behavioral controls challenged against bypasses that preserve the text: the
knob check moved after the first banner is caught by the knob control
(`Checking limits documentation` must not print); the stale identity check
moved after the stamp by the identity control (`Build stamp` must not print);
the build-directory guard moved after the signing identity by its control
(the guard's message must precede the identity's); the minimum checks and the
signer check moved to another step are caught only textually, by the
invocation rule, and remain baseline entries for behavioral coverage.

### Tier-one retirements

Adjudicated 2026-10-09 at the step 3a pause: the step table begins at
`make build`, as built, so the Makefile's targets stay in the account for the
people and agents who choose to learn them; and the baseline's cheap tier is
retired now, the stub-Cargo tier is decided separately, and the rest stays
listed. Retired, each control observing the diagnostic and the operation it
prevented beside the valid run:

- In `contract.py`: an unknown argument (and `--help` as the one accepted
  argument), a malformed plist minimum after its banner and before the SDK,
  a Developer ID string the keychain lacks before Cargo, a stale architecture
  copy and a stale build-document copy before compiling, and the Makefile's
  guard, which stops before a stub `build.sh` runs and otherwise passes the
  identity and `DIST_DIR` through.
- In `build.py`: every Meson policy assertion but the label, driven directly:
  a fresh configured directory, `meson configure` with another value, then
  `meson compile`. Coverage kind `helper`, since Meson is driven, not the
  script.

Found while retiring: `meson configure` with a refused value exits 0 and
records the value; the assertion runs at the next regeneration, which the
compile step triggers (or at setup, for a fresh directory). The manifest had
placed Meson's refusals under the configure step alone; they now name
configure and compile, and the step facts say so. The `buildtype` assertion
cannot fire on its own because Meson derives the label from optimization and
debug, whose assertions fire first; its baseline entry says so, and the
public-path placement proof for the whole group waits for the stub-Cargo
tier. The baseline holds twenty-seven entries after this pass.

Open for the human at the step 3a pause were the two questions settled
above and whether the generated tables read as the account the prose should
follow; the prose was started on that basis.

### Step 3b drafting log and the step 4 reading

The prose was written 2026-10-09 from `build.sh`, `meson.build` and the
manifest, in the proposed shape, around the generated regions. Every claim
links its symbol and its check in the verified form or names its gap; counts
reach the prose through the build spans; the three accepted limitations are
"Known gap" paragraphs indexed by the last section, and the known-gap index
rule in `check.py` now covers this document as it covers the architecture
document (the planner control's copied checkout holds it too). The authored
prose is a little over the size target: about two thousand seven hundred
words against a target of two thirds of the architecture document's. Found
while drafting, keyed to the register:

- **Row 9.** The signing document said `RUSTFLAGS` is filled "unless it is
  already set"; the script fills it when the variable is unset or empty.
  Corrected to "set to a nonempty value". The build document states the
  script's behavior.
- **Row 9.** `PW_BUILD_DESCRIBE` and `PW_BUILD_COMMIT` are not overridable;
  only `PW_VERSION` and `PW_BUILD_NUMBER` are (observed in probe T3, which
  first tried the describe variable as a marker). The build document says
  so; the script's own comment says only that the two overrides exist.
- **Row 6.** The partial bundle's specimen refusal was observed against an
  older build; the current claim rests on the controller's manifest lookup
  in source. The prose states the mechanism, not a fresh observation.
- **Rows 15 and 18.** The prose states what a refusal leaves behind in both
  halves: before assembly the previous outputs are untouched; after it, no
  seal, no evidence and no ZIP.
- **Row 16.** The prose scopes the "belongs to another checkout" refusal to
  the Meson build directory; Cargo's directory is pinned, not checked.
- **Forward walk.** Two facts the tables could not hold were missing from
  the prose: the one warning the script prints that is not a refusal (an
  empty augments directory) and the packaging step with its second guide
  check. Both are stated now.
- **Universal words.** "Every Cargo and Meson output" became "every Cargo
  and Meson executable", since the shim is neither shipped nor checked.
  "Leaves nothing that looks finished" became the precise statement above.

The agent's step 4 reading found no counterexample that returns to step 1.
A plan-blind audit prompt was written for the pause; its reading and the human review followed.

### Step 4 record: the plan-blind audit and its remediation

The plan-blind reader worked from a prompt that was committed and then moved out of the tree with its report, both local under `.tmp/audits/` at the user's choice; it reported six wrong claims, four omissions, five unestablished guarantees,
three defect candidates and five claims that held, and rows 22 to 27 carry its substance.
Every finding was accepted. The three build changes were adjudicated as the
agent recommended: the inspector's signer consistency instead of a cleanup
trap, Cargo's reported artifact paths, and the closure bounded to the SDK and
the developer directory. The reader's own suite run inside its sandbox failed
the two Swift-option Meson controls at `meson setup`, and passed them outside
the sandbox against unchanged files, which is the harness constraint the
documents describe.

Validation of the remediation:

- Unit: the `build_documentation` case passes with the three new script
  mutations, the errexit refusal and the figure control; the preflight signer
  control passes nine scenarios against the real app, including the
  inspector naming the ad hoc helper and the signer command line refusing it;
  the configured-source check on the real build directory passes under the
  bounded closure.
- Suite: `tests/run.sh --suite source_drift` into
  `tests/out/runs/build-doc-step4-drift`, six cases green.
- Rebuild: `make build` through the changed script, with Cargo's reported
  artifact paths accepted, the build documentation check and the signer check
  clean.
- Battery: the first run into `tests/out/runs/build-doc-step4-default` failed
  six cases on one cause of this pass, the fixture runner copying the
  inspector without its new module; the fixture copies it now, and the
  consistency rule was narrowed to signed executables because a fixture's
  only signed executable is a linker-signed stub beside shell scripts. The
  dispatcher and shell helpers suites then passed alone, and the full battery
  into `tests/out/runs/build-doc-step4-default-2` passed 171 of 171, none
  skipped or unrun, no harness errors, app unchanged.
### Narrative audit record

A third audit followed step 4: a newcomer's narrative of adding a fourth
top-level helper, `pw-stamp`, through the whole build in a disposable copy,
logging every expectation with its outcome and each surprise with a valence,
plus a challenge to do one non-obvious thing with the build machinery. Its
prompt and report are local under `.tmp/audits/`; the report arrived as
commit 4442751 under `docs/` and was moved out because its measured
durations trip the prose baseline.

Result. The helper came back to green: `make build`, the inspector and, once
the one file the prompt's copy recipe had excluded was restored, all six
`source_drift` cases. The auditor recorded twenty-one calibrations and eleven
surprises. Four of the surprises belong to this repository, all in test
machinery and none in the script, the manifest or the document:

- the planner fixture staged a literal list of C sources beside the
  expectation in `native_sources.py`, and nothing pointed to it;
- two inventory mutation controls replaced text without asserting its
  presence, and the seal control hardcoded its entry number, so a moved
  needle failed by blaming the generator;
- the Meson policy control needs Swift discovery, which the tests README
  harness note did not say;
- that control showed only stderr on a setup failure, which Meson leaves
  blank.

The challenge, an exact coverage query over the manifest, established that
the sixteen cited controls partition the thirty-seven covered refusals and
that one helper control, the Meson policy test, supplies twenty of them;
behavioral coverage is fourteen rows of sixty-five. The query was not kept.
The generator's comparison functions were used as an import by the auditor;
that surface stays undeclared on purpose, since its only supported consumers
are the rules and the drift case, which pin it through the suite.

Fixes, landed with this record: the two inventory mutations use the
presence-asserting helper and the seal index comes from the manifest; the
setup assertion shows stdout with stderr; the planner fixture derives its C
sources from the native expectation; the tests README names the case;
BUILD.md says Reads and Writes are description; the AGENTS.md shipped-paths
line names the manifest row, the native target and the regeneration.
Validated: the build-document tests, the planner controls and the six
`source_drift` cases. Deferred to step 5: thinning spelled-out counts such as
"the two C executables" to inventory references, since the prose baseline
sees numbers with units, not words. Unmeasured by this engagement: the
refusals a maintainer who edits before reading would meet, because the
auditor read first and made every edit in one action.
