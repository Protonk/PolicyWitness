# Signing and notarization

`PolicyWitness.app` is intended to be a coherent, signed specimen. The build pipeline is centralized in `build.sh`.

The build also stages `dist/PolicyWitness.md` (or the corresponding path under
`DIST_DIR`) as the standalone user guide. It checks the generated limits before
compilation and again before copying the guide from `docs/PolicyWitness.md`.
Stale documentation stops the build; regenerate it with
`tests/lib/python.sh docs/generate_limits.py` and review the changes before building.
Distribute that staged guide with the release ZIP from the same build.
The tracked [dist README](../dist/README.md) describes the output directory;
builds also copy its README and AGENTS.md into a custom `DIST_DIR`.

## What `build.sh` signs

See [the signing contract](BUILD.md#the-signing-contract) for identity checks,
the generated signing order, inventory agreement and post-seal verification.
The build copies one compiled C worker into `pw-probe-runner` and `pw-probe-runner-unentitled`. It signs the selected worker with the supplied entitlements, and signs the unentitled worker and validator with the identity alone. `tests/build_equipment.py` reads those signed artifacts and writes the service-local `Contents/Resources/worker-equipment.json` before the service seal. Its bounded schema records both roles, source/ABI identity, unsigned build hash, signed hashes, CDHashes, signing identifiers, teams and full entitlement XML. It excludes the host hash to avoid a circular seal dependency.

BYOXPC installation first verifies the source service seal and inventory before changing any bytes. It signs both worker copies and the validator, refreshes inventory signing observations while preserving the source build identity, and seals the service last. A renamed or otherwise edited source service must be resealed before installation. The host reads its own sealed inventory; direct XPC execution does not rely on a controller registry snapshot. Actor execution validates both roles, even when only one is requested, and records live associated signing identity separately from static binding and native effects.

## Evidence artifacts

During the build, `tests/build-evidence.py` generates, under
`dist/PolicyWitness.app/Contents/Resources/Evidence/`:

| File | Producer and source | Sealed by |
| --- | --- | --- |
| `manifest.json` | The evidence script, from the signed bytes on disk: each helper's and service executable's hash, load-command UUID and entitlements (extracted via `codesign -d --entitlements`), the augments' hashes, and entries for the other two files with their hashes. | The app seal |
| `symbols.json` | The evidence script, from `nm` over the same executables: the exported `_pw_*` marker symbols. | The app seal, through the manifest's entry |
| `provenance.json` | The evidence script, from the build session `build.sh` kept through its steps and from the assembled bundle: the provenance record described below. | The app seal, through the manifest's entry |

All three are generated after the helpers and the service are signed and
before the outer seal, so they describe signed bytes and are themselves
sealed by the app signature; no embedded evidence is rewritten after the
seal. Both worker variants have their own manifest entries and symbol inventories, identifying their signed bytes. The controller reads the manifest at run time to locate its
runner; the service-local equipment inventory is separately read by actor execution.

### The provenance record

`provenance.json` (`schema_version` 3) is the tools' report about one build:
what was selected, what the tools said about themselves, what the build
directories looked like and what bytes shipped. It does not establish
reproducibility, compiler correctness, that particular bytes executed, or an
exhaustive account of private runtime dependencies, and it says so in its
`limits`. Its sections:

- `source`: the git commit, describe string and dirty flag, the version and
  build number the plists carry, the worker identity the built worker
  reported, and the hashes of `meson.build`, `meson.options`,
  `controller/Cargo.lock`, `Info.plist` and the two entitlement plists.
- `toolchain`: the developer directory and how it was selected; the SDK's
  path, version and build; Xcode's version and build when `xcodebuild` can
  report them, otherwise `unknown` with the failure kind; for the C and, in a
  full build, the Swift compiler, Meson's configured command, id, version and
  full version beside the identity the command reported when probed in the
  build directory's context (a partial build records the Swift compiler as
  not applicable); the pinned Python interpreter the helpers ran on: its
  path, its real path in the keg (with any Homebrew revision), the version
  the keg names and the version one isolated probe reported; the Rust
  compiler Cargo would run and its `selection`,
  resolved as one Cargo invocation from the build's directory resolves it:
  the configuration files read there, in its ancestors and in Cargo home
  (redacted) with their includes, the source of the compiler and of each
  wrapper and the lower sources each overrides, the `[env]` names with whether
  each applied (never their values), the launcher (a rustup proxy with its
  toolchain, or Cargo itself), the output triple the command passes with
  `--target` and the lower-precedence defaults (`CARGO_BUILD_TARGET`,
  `build.target`) it overrides, and the compiler's inputs in Cargo's child
  environment (`SDKROOT`, `MACOSX_DEPLOYMENT_TARGET`, `DEVELOPER_DIR`,
  `RUSTUP_TOOLCHAIN`, and whether `[env]` replaced `PATH` or `RUSTUP_HOME`);
  the command, probed without its wrappers in that environment and in the
  workspace root, with each wrapper's command and hash; and the selected
  `cargo`, `meson` and `ninja` commands with their versions. A configuration
  that cannot be resolved, or an effective input that differs from the
  build's selection, stops the build instead.
- `configuration`: the three knobs; the fixed-policy subset of Meson's
  effective options plus `inspection` and `xpc`; the requested Rust flags
  with the source that set them and which flag variables were set; the
  caller's `requests`, kept apart from what the build selected: `SDKROOT`
  set (with its exact value, an empty one included) or unset as the
  environment `build.sh` started with held it, `DEVELOPER_DIR` and
  `MACOSX_DEPLOYMENT_TARGET` with their values, and only the set or unset
  state of `CPATH`, `LIBRARY_PATH`, `MANPATH` and `LC_CTYPE`; the fixed
  `output_target` (system `macos`, platform `1`, architecture `arm64`, a
  `thin` container and the Cargo triple `aarch64-apple-darwin`), a statement
  about the products that makes no claim about the machine or processes that
  built them; Meson's host and build machines as Meson reports them, the host
  being the platform the native products are configured for and the build
  machine a toolchain fact that is not constrained. The build's admission
  refuses a builder that is not a native process on Apple Silicon, but the
  record carries no field for that check: neither note attests it, and the
  recorded build machine and rustc host remain what the tools reported; the
  effective `deployment_target` and `sdkroot`, as Cargo's resolved environment gives
  them to the compiler, which must equal the plist's minimum, every output's
  minimum and the selected SDK's path; each build directory's state (`created`
  or `reused`, whether fresh mode replaced it, and what happened to the
  stamp), Cargo's host release area and its output triple's release area
  apart, fresh mode's replacement report and Cargo's admitted directories;
  and a projection of the toolchain stamp with its scope.
- `outputs`: for every shipped Mach-O, its bundle-relative path, UUID,
  platform, minimum and SDK from `LC_BUILD_VERSION` with the linker tool
  versions, its architectures as `lipo -archs` names them and its container
  (`thin` or `fat`) as its header declares it; its hash as signed, except the controller, whose entry says why
  the hash is absent; the nested signature's leaf, team, runtime flag,
  Developer ID chain and timestamp presence; and, for the Cargo targets,
  Cargo's own judgment, a literal boolean (`fresh: true` means Cargo reused
  the output), the profile, the fingerprint observation bound through the
  uplifted executable (`observed`, or an explicit `unavailable`, `ambiguous`,
  `malformed`, `unsupported` or `oversized`), the effective Rust flags from
  that fingerprint, labelled as Cargo's record, and the requested source by
  Cargo's precedence (`CARGO_ENCODED_RUSTFLAGS`, `RUSTFLAGS`, target rules,
  `build.rustflags`) with the sources it overrides and whether its tokens
  agree with the effective flags; target rules with `cfg()` keys stay
  unresolved and their agreement unknown.
- `signing`: the identity string and, per nested signature, the leaf, team
  and timestamp presence read from `codesign -dvv` before the record was
  sealed. The app seal is made after the record; its facts live in the
  release record, not here.

Field policy. A required observation (the SDK, the developer directory, the
compilers' identities, the Rust compiler, each output's load commands,
architectures, container and hash) that fails stops the build, and so does an
output outside the output target. An optional one (Xcode's version, a
fingerprint for a reused unit, a wrapper's identity) is recorded as unknown
with a bounded failure entry naming its kind, status and byte counts, never
the tool's output, and never compares equal to anything. Every probe has a
fixed deadline and live caps on both output streams; overflow on either one
is a failed observation even when the tool exits zero, and the probe's
process group is terminated within a bound. An identity, a configured
command, an effective flag list or an output's build tools longer than its
declared bound is recorded as an oversized failure, never truncated. Paths
under the home directory are published
with a `<home>` marker; the exact paths stay in the local stamp
(`builddir/pw-toolchain.json`) and session (`controller/target/pw-build-session.json`),
which are not shipped. The record never carries `PATH`, other environment
variables, keychain contents or raw tool output.

Validation. One typed validator defines the record above
([`record_shape_problems`](../tests/lib/build_provenance.py)): every section and
required field present and not null, exact booleans, strings and integers,
bounded strings and lists, the full build's or the partial build's compilers
and outputs, only the documented observation statuses and the unknowns the
field policy permits, no undefined top-level field, signing entries
that repeat the outputs' signature facts, effective settings that agree
with the outputs, and every output and Meson's host machine described as the
output target. The evidence step refuses to write a record it rejects; the
inspector applies it and then compares every claimed load-command field,
linker tools included, with the bytes and each nested signature claim with
`codesign -dvv`'s display; the release-archive reader applies it to the
accepted ZIP's record and binds each nested output's hash to that ZIP's
member. It copies the named executables to a temporary directory to compare
their load commands, architectures, containers and signature displays too;
it never executes them. The declared output target satisfies nothing on its
own: both readers compare each output's claims with its bytes, and the
inspector checks the bytes of every executable whatever the record says.
Both readers enforce the helper's [`RECORD_LIMIT`](../tests/lib/build_provenance.py) before parsing. Cargo profiles,
Meson options, toolchain-stamp projections and fresh-mode replacement
observations have typed fields; fresh-mode observations must agree with the
knob, directory states and per-target rebuild judgments.
A record that leaves a required field null is refused, not reinterpreted.
The inspector, archiving and archive verification read only the current
schema version and refuse any other.

What the hashes mean. A newly calculated output hash identifies the bytes the
record captured; it does not authenticate their compilation history. A cached
executable replaced before evidence capture can be reported reusable by Cargo
and can agree with the record's hashes, SDK and minimum checks; the record
states that limit, and the inspector refuses the separate faults it can see:
a record that disagrees with the manifest or the bytes, wrong load-command
metadata or linker tools, a signature claim the display contradicts, an
incomplete or duplicated output inventory, a record of the wrong shape, and
any change after capture or sealing. The build document explains the [cache compatibility
checks](BUILD.md#cache-compatibility-replacement-and-recovery) that precede
the compiles and [what the record separates](BUILD.md#the-evidence-the-build-embeds).

### The release record

`dist/archive/v<version>/release.json` carries, beside the ZIP hash, a
`provenance` object: the path and hash of `evidence/provenance.json`, which
is the record copied byte for byte out of the accepted final ZIP; the final
controller hash (`controller_sha256`), read from the same ZIP; and
`app_signature`, the app seal's leaf, team, chain, runtime flag and timestamp
presence as `codesign -dvv` displays them on an extraction of that ZIP. These
are the facts the sealed record cannot hold about itself. Archive
verification reads them back against the ZIP before the archive is exposed
by rename and again before publication; a working app that has since been
rebuilt never supplies them.

## Release procedure

Run commands from the repository root, outside an automation sandbox. First
transcribe the preceding release's footprint receipts as described below,
render and review the pending surface stamps, then include them with the
complete reviewed release change in one commit and create the annotated tag.
Build from that clean tagged tree: only this state emits
`release:vX.Y.Z`; an untagged or dirty build emits a development contract.
`tests/lib/release_preflight.py` refuses an untagged or dirty tree, a lightweight
or ambiguous release tag, scoped bytes that differ from the tag even when the
Git index hides the edit, stale surface tables or remaining `unreleased` rows,
a remote holding a different tag of that name, or an existing
`dist/archive/<tag>/`. New releases must increase numerically beyond the newest
complete local archive, including after older archives expire. Release
operations require this checkout's `dist/` root.
It also refuses added or rewritten sites in the committed
[prose baseline](../tests/fixtures/docs/prose_baseline.json) and added or rewritten
entries in the committed [build baseline](../tests/fixtures/docs/build_baseline.json),
compared with the nearest preceding annotated release tag. A preceding release
without a baseline is recorded as such; `--report` turns growth refusals into warnings. The contract's
free-text relationship counts also compare by kind with the preceding
release; removing that baseline or increasing any kind refuses release.

```sh
tests/lib/python.sh docs/generate_contract_stamps.py --release v0.3.7
git status --short
git diff
# After checking that the tree contains only the intended release change:
git add -A
git diff --cached
git commit -m "Prepare PolicyWitness v0.3.7"
git tag -a v0.3.7 -m "PolicyWitness 0.3.7"
tests/lib/python.sh docs/generate_contract_stamps.py --check
make release NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: YOUR NAME (TEAMID)' RELEASE_NOTES=/path/to/notes.md
make publish VERSION=0.3.7
```

`make release` runs the preflight, then the `make notarize` chain below (a
fresh build, sign, submit, wait, staple, validate, re-zip, accept), then
`tests/lib/release_archive.py`, which archives the accepted release under
`dist/archive/v<version>/`. Acceptance is where the tests run: it extracts the
final ZIP and runs the full default battery against the extracted app through
`tests/run.sh` with no selectors, the same command and selection as `make
test`, into the acceptance's own `tests/` directory. There is no second battery
and no release-specific selection. The
release build is fresh: `notarize` passes `PW_FRESH_BUILD=1` to its recursive
`make build`, so `builddir/`, `controller/target/release/` and
`controller/target/aarch64-apple-darwin/release/` are replaced and Cargo
rebuilds every shipped target, and a caller's conflicting
`PW_FRESH_BUILD` value, in the environment or on the make command line, is
refused before anything builds rather than overridden silently. Archiving
stages the ZIP, guide, checksums, original command receipts, notes, the
provenance record read out of the accepted ZIP and complete test evidence,
verifies the copy including the record's binding to the ZIP, requires the
battery's recorded inventory of the extracted app to equal a fresh extraction
of the archived ZIP in full (every mode, hash and symlink target), and exposes
the completed archive by rename. The attempt's receipts end up under
`evidence/`, with a `<attempt>.archived` pointer under `dist/evidence/`.
The newest archive supplies protection for its acceptance working directory,
battery inside. Finally, ordinary pruning applies the release window and removes
eligible working test output as described below.

The default battery includes the three footprint measurement cases
(`witness_contract/response_footprint`, `witness_contract/held_phase_footprint`
and `run_effects/aftermath_footprint`), so the archived acceptance holds the
receipts behind every measured row of [FOOTPRINT](FOOTPRINT.md), taken on the
released binaries. During preparation of release N+1, transcribe release N's
rows into [footprint.json](footprint.json) from the case artifacts inside
`evidence/test-runs/runs.tar.gz` (`acceptance/tests/suites/<suite>/<case>/artifacts/`).
Name N's archive and acceptance/battery identities in FOOTPRINT's provenance
section and regenerate the document before committing and tagging N+1.
Preflight requires that provenance to cite the newest complete local archive;
it checks attribution freshness, not agreement of the measured values with
receipts. With no local archive, the comparison is explicitly unavailable.
The tagged tree reports the previous release's measurements, and main may lag
until the next preparation. No post-tag retention or footprint commit is
required. The build, acceptance (with its battery), archiving and pruning hold the
checkout lock for their own duration; `make release` holds no outer lock, so
run no other build or battery in the checkout while it runs. The notarization
submission is the only remote step in `make release`.

### Portable test evidence and release cleanup

Each archive contains `evidence/test-runs/runs.tar.gz` with the full acceptance
directory under `acceptance/`, the default battery's dispatcher run nested at
`acceptance/tests/`. Its `manifest.json` (`schema_version` 3) records the
original acceptance identity, per-file hashes, modes and symlink targets, which file inside
the acceptance is the battery summary, and checksums of the compressed archive
and the standalone `acceptance.json` and `battery.json` summaries.
`release.json` binds that manifest by SHA-256. Its `acceptance.path` and
`battery.path` resolve to summaries within the release archive;
`original_path` records the former location under `tests/out`. Schema 3 also
binds the selected families to the producer's execution contract, captured before
the battery starts and retained independently in `release.json`. Verification,
publication and pruning require each family's selection, phase account and
terminal ownership receipt against that contract. Passing item reports alone
do not establish complete execution or resolved ownership.

Only portable bundle schema 3 is accepted for archive verification and
publication, with a mandatory captured execution contract in the schema-2
`release.json`. Those are different format counters. Rereading an archive uses
its captured contract, not today's catalog. Unsupported bundles are not
converted or rewritten. Original command receipts retain their original paths;
verification reads the portable copy independently of working test directories.
Provenance verification derives the executable inventory from the ZIP's actual
Mach-O members, excluding debug companions by file type. It checks every named
output's hashes, load commands and signature facts against those bytes, without
requiring the current checkout's executable names. Current-build validation
and new archive creation additionally require the current checkout's executable
layout for the declared build variant. New archival refuses missing, renamed
or extra executables even when the ZIP and provenance agree with each other;
rereading a retained archive continues to use its own observed layout.

Successful archival is followed by ordinary pruning, the same operation as
`make prune APPLY=1`. It keeps the four newest complete local archives in
numeric version order and only the newest archive's unpacked acceptance, with
its battery. Accepted unarchived attempts matching the current final ZIP
protect their acceptance until archival or established supersession. There are
no manual pins, newest-development exception, completion requirement or age
cutoff. Expired archives, positively linked attempts and archived pointers are
removed together. Publish while the local archive remains in the window; an
unpublished archive can expire too. Git history, annotated tags and published
assets remain intact. No backup or remote deletion is involved.

Every unprotected managed run is disposable once inactive and free of resource
cleanup obligations. An interrupted run or malformed completion summary is not
an exemption. Ownership is checked independently; unknown ownership, redirects,
active acceptance, unresolved pytest ownership and pending external-runner
cleanup remain blockers. The checkout lock and acceptance lifetime locks
establish inactivity; timestamps do not. Pruning never removes machine
services to settle an obligation.

Cleanup requires current portable evidence and verifies it before mutation.
Unsupported or corrupt storage blocks cleanup.

Apply holds `tests/.checkout.lock`, journals the exact target inventories inside
`tests/out/.retention/`, and renames targets into that quarantine before deletion.
Both distribution and test output must permit same-filesystem staging. Surviving
archives receive no writes. The journal supports partial-deletion recovery;
resumption rechecks remaining bytes and preserves replacements at original
paths. Once complete, the journal and transaction directory are removed. Stdout
reports the result; no permanent deletion-receipt archive is kept.

```sh
make prune
make prune APPLY=1
```

Preview is read-only. Apply resumes a leftover transaction before any fresh
pruning; a separate later call plans afresh. Keep the journal and quarantine
together until completion. Unfinished journals from the old rotation procedure
or leftover `.release-rotation/` output block the new planner and require the
original recovery tools. Scratch remains outside cleanup under
[its own guidance](../.tmp/AGENTS.md).

### Publication

Publication holds the checkout lock while reading and updating its archive, so
pruning cannot retire those bytes during publication.

`make publish` is the outward step. `tests/lib/release_publish.py` pushes the
tag if the remote lacks it, creates the GitHub release once from the archived
assets with `--verify-tag`, reads the release back, downloads every asset,
compares bytes and digests with `SHA256SUMS`, and only then records the release
and asset URLs in `release.json` and the reply in `evidence/github-release.json`.
Re-running it verifies an existing release and creates nothing. The archive,
its portable test evidence included, must pass verification before any push
or GitHub operation. It needs an authenticated `gh`; `RELEASE_NOTES=` overrides
the archived notes.

### Lower-level notarization

`make notarize` is the lower-level chain. It **builds again, fresh**, even if
you already built and tested the app: the caches are replaced and every
shipped target is compiled, and a `PW_FRESH_BUILD` value other than `1`
supplied by the caller refuses the chain before the build. Its last step
establishes release acceptance by running the default battery against the
actual final ZIP's contents, so a rehearsal is a complete rehearsal and takes
the battery's duration. It
reports preflight findings as warnings and continues, so a rehearsal still
records what it stamps. For an already-built ZIP, use the individual steps below.

```sh
make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: YOUR NAME (TEAMID)'
```

`entitlement-jail` is the working keychain profile on the maintainer's machine.
Pass it explicitly. Other machines need their own configured profile and
Developer ID identity.

The Makefile keeps these steps in order and stops on any failure. After the
build, it creates one `dist/evidence/<UTC timestamp>-<unique suffix>/` attempt
(or `evidence/` under a custom `DIST_DIR`). Its `release.json` records the input
ZIP hash and embedded build stamp; its README indexes the results as steps finish.
Named `notarization/`, `staple/`, `staple-validation/`, `gatekeeper/`, and `re-zip/`
directories hold raw receipts. Missing steps have no recorded result.

| Step | Changes | Evidence of success |
| --- | --- | --- |
| Build and sign (fresh) | Replaced caches, app, embedded manifest and provenance record, initial ZIP | Inside-out signatures verify with the Developer ID chain and secure timestamps; Cargo reports rebuilding every target |
| Submit once | Uploads a retained copy of the ZIP | Recognized submission ID saved locally |
| Wait once | No local artifact change | Explicit `Accepted` for that submission |
| Staple | Attaches Apple's ticket to the app | `stapler staple` succeeds |
| Validate | Reads the stapled app | Staple validation and Gatekeeper assessment succeed |
| Re-zip | Replaces ZIP with the stapled app | ZIP creation succeeds |
| Accept archive | Extracts a disposable copy, checks it, and runs the default battery against it through `tests/run.sh` with no selectors under its fixed two-hour bound | `acceptance.json` has `ok: true` for the final ZIP's SHA-256 and a `battery` summary; the nested `tests/run.json` passes with no skips, unrun cases or harness errors and an unchanged app |
| Archive (`make release`) | Verifies staged assets, receipts, the record copied from the accepted ZIP with the final controller hash and seal facts, the battery's inventory against a fresh extraction of the ZIP, and portable test evidence; retains the acceptance run | `dist/archive/v<version>/release.json` with `origin: null`, a `provenance` object bound to the ZIP and a `battery` naming the nested run |
| Cleanup (`make release`) | Keeps the four newest archives and only the newest unpacked acceptance; prunes other inactive owned output under the checkout lock | The apply report lists removals and blockers; completed quarantine is removed |
| Publish (`make publish`) | Pushes the tag, creates the release, verifies uploads | `release.json` records `origin` and `evidence/github-release.json` exists |

`notarize.py` owns only submission and one bounded wait. It preserves the input
as `evidence/<attempt>/notarization/submitted.zip` beside the input ZIP.
That directory also holds `result.json`, the submission ID, the archive hash,
and raw stdout/stderr plus command/exit/timing records for both calls. A zero
exit requires recognized acceptance.
It accepts extra response fields but treats malformed, missing, mismatched, or
unrecognized status data as **unknown**, never as acceptance. The captured bytes
remain authoritative for manual inspection.

The upload has a 180-second local deadline. Apple's `notarytool wait` is invoked
once with `--timeout 5m`, with a 330-second local backstop. The tool does its own
waiting; our code adds no polling loop, retry, resubmission, or resume state
machine. Stapling and assessment commands also have 60-second local deadlines
through `tests/lib/release_commands.py`, which prints the exact command and
retains its outputs under that attempt's named step directory. These deadlines stop local work;
they do not cancel or classify work at Apple.

### Individual steps and manual equivalent

Build once with `make build IDENTITY=...`. Then submit the
existing ZIP with the bounded helper. Start every helper through
`tests/lib/python.sh`, as `make` does, never the `/usr/bin/python3` shim:

```sh
RELEASE_EVIDENCE="$(tests/lib/python.sh tests/lib/release_evidence.py dist/PolicyWitness.zip)"
tests/lib/python.sh notarize.py dist/PolicyWitness.zip entitlement-jail --evidence-dir "$RELEASE_EVIDENCE"
```

Without `--evidence-dir`, `notarize.py` creates a new attempt and prints its
notarization directory. An existing attempt must identify the same archive and
input hash; its notarization directory cannot be reused for a second submission.

To perform its two Apple calls yourself, retain the submitted ZIP and their raw
responses in a new evidence directory first. Upload the ZIP, then use the
returned submission ID to obtain Apple's decision:

```sh
RELEASE_EVIDENCE="$(tests/lib/python.sh tests/lib/release_evidence.py dist/PolicyWitness.zip)"
NOTARY_EVIDENCE="$RELEASE_EVIDENCE/notarization"
mkdir "$NOTARY_EVIDENCE"
cp dist/PolicyWitness.zip "$NOTARY_EVIDENCE/submitted.zip"
shasum -a 256 "$NOTARY_EVIDENCE/submitted.zip" > "$NOTARY_EVIDENCE/sha256.txt"
xcrun notarytool submit "$NOTARY_EVIDENCE/submitted.zip" --keychain-profile entitlement-jail --no-wait --output-format json > "$NOTARY_EVIDENCE/submit.stdout" 2> "$NOTARY_EVIDENCE/submit.stderr"
```

Inspect both files. If Apple returned a submission ID, set `SUBMISSION_ID` to that
exact value, then make one bounded wait call:

```sh
SUBMISSION_ID='the ID returned by Apple'
xcrun notarytool wait "$SUBMISSION_ID" --keychain-profile entitlement-jail --timeout 5m --output-format json > "$NOTARY_EVIDENCE/wait.stdout" 2> "$NOTARY_EVIDENCE/wait.stderr"
```

Inspect the response and require explicit acceptance of that submission before
continuing. The helper provides local deadlines even for a stuck upload or wait;
the direct commands above rely on your supervision if the tool itself stalls.
After acceptance, with the same app that was submitted:

```sh
tests/lib/python.sh tests/lib/release_commands.py --step staple "$RELEASE_EVIDENCE" 60 xcrun stapler staple dist/PolicyWitness.app
tests/lib/python.sh tests/lib/release_commands.py --step staple-validation "$RELEASE_EVIDENCE" 60 xcrun stapler validate -v dist/PolicyWitness.app
tests/lib/python.sh tests/lib/release_commands.py --step gatekeeper "$RELEASE_EVIDENCE" 60 spctl -a -vv --type execute dist/PolicyWitness.app
rm -f dist/PolicyWitness.zip
tests/lib/python.sh tests/lib/release_commands.py --step re-zip "$RELEASE_EVIDENCE" 60 ditto -c -k --sequesterRsrc --keepParent dist/PolicyWitness.app dist/PolicyWitness.zip
bash tests/accept-release.sh dist/PolicyWitness.zip --evidence-dir "$RELEASE_EVIDENCE"
```

Run these one at a time and stop if any command fails. A named step cannot
overwrite an earlier receipt. For a standalone command, omit `--step` and pass
the distribution directory: `tests/lib/python.sh tests/lib/release_commands.py
dist 60 COMMAND ...` creates a separate dated attempt under `dist/evidence/`.
Read the status of manually issued Apple calls from their retained raw replies.
The helper writes `result.json` for calls it issues itself.
Stapling intentionally changes the app after submission, and re-zipping changes
the archive hash. The submitted and final ZIPs therefore have separate evidence.

### Apple replies now, later, or never

A nonzero exit, timeout, interruption, pending status, or unfamiliar response
stops automatic continuation. Read the recorded stdout **and** stderr. Do not
infer rejection from a timeout, infer acceptance from an exit code or prose, or
run `make notarize` again merely to check progress: it rebuilds and submits again.
If Apple asks for a policy agreement, stop and let the maintainer resolve it and
wait for Apple's systems.

If an ID is available, a later **manual, one-shot** status query is:

```sh
xcrun notarytool info "$SUBMISSION_ID" --keychain-profile entitlement-jail
# For an explicit rejection, inspect its detailed log:
xcrun notarytool log "$SUBMISSION_ID" --keychain-profile entitlement-jail
```

Preserve that output as well. No ID means submission state is uncertain; inspect
the responses and, if necessary, the account's submission history before deciding
whether a new submission is appropriate. Do not edit or regenerate the manifest
to make a failed artifact pass.
For a one-shot history query, use
`xcrun notarytool history --keychain-profile entitlement-jail` and retain its output.

After later acceptance, continue from stapling the retained submitted app.
If `dist` has changed, set `NOTARY_EVIDENCE` to the retained submission directory and extract
its `submitted.zip` under `/private/tmp`:

```sh
RECOVERY_DIR="$(mktemp -d /private/tmp/pw-release-recovery-XXXXXX)"
ditto -x -k "$NOTARY_EVIDENCE/submitted.zip" "$RECOVERY_DIR"
```

Use `$RECOVERY_DIR/PolicyWitness.app` in each staple/validate/assessment command
above. Write the new ZIP to `$NOTARY_EVIDENCE/PolicyWitness-final.zip`, then pass
that exact path to `tests/accept-release.sh`. Keep the retained submitted ZIP
intact. If stapling or assessment fails or stalls, inspect its
recorded output and stop; retrying that individual command is a manual decision.

### What archive acceptance proves

`bash tests/accept-release.sh PATH/TO/PolicyWitness.zip` requires an explicit ZIP.
It records the hash, checks archive layout, and extracts with `ditto` under
`/private/tmp`. It checks the extracted app's signatures and manifest, requires
that its plist and extracted `--version` report `release:<tag>` for its version,
validates its staple, assesses Gatekeeper, and runs the default battery against the
extracted app through `tests/run.sh` with no selectors, the one test interface
under its ordinary selection and accounting. The battery must pass with no
skipped or unrun cases, no harness errors and an unchanged app, and its two
specimen envelopes must name the bundled standard runner. The battery runs under
a fixed two-hour bound, `BATTERY_TIMEOUT_SECONDS` in `tests/lib/release_accept.py`;
the receipt in `execution/command.json` records the bound and the elapsed time,
and expiry fails acceptance while keeping whatever the dispatcher wrote. The
bound is an initial operational ceiling, revised from recorded elapsed times. Nothing in the battery signs, installs an external runner
or rebuilds the app, because those cases are not default members. Inherited
`PW_*` settings cannot select a local fallback build.

The input ZIP and extracted app must remain unchanged throughout acceptance.
The temporary extraction is removed; reports, command outputs, and inventories
remain in a fresh `tests/out/release-acceptance/run-*` directory with the
battery's dispatcher output under its `tests/`. That directory
is printed, and `acceptance.json` binds the result to the final archive hash
and summarizes the battery.
With `--evidence-dir`, a small `acceptance.json` pointer in the release attempt
records that report's location, result and final hash; test evidence stays under
`tests/out/release-acceptance/` and follows the existing retention rules.
Only distribute the ZIP matching a successful report. The assessment applies
to the local macOS environment and Gatekeeper state at acceptance time.

## Preserved release archives

`dist/archive/<version>/` contains exact release assets, `SHA256SUMS`, a
`release.json` release record, and supporting `evidence/`, including the
embedded provenance record copied from the accepted ZIP, the portable test
bundle. Completed rotation receipts in older archives remain historical evidence. `make release`
creates one per version through `tests/lib/release_archive.py`. Provenance
records distinguish a verified published asset (`origin.kind: github_release`,
written by `make publish`) from locally retained material. Check Git separately
for the corresponding tag's availability. Original command receipts retain
their original paths.

These artifacts are ignored and local. Recover published assets from their
recorded release URL and verify their checksums to recover the original signed
release bytes.
