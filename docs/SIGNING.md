# Signing, building, and notarization

`PolicyWitness.app` is intended to be a coherent, signed specimen. The build pipeline is centralized in `build.sh`.

The build also stages `dist/PolicyWitness.md` (or the corresponding path under
`DIST_DIR`) as the standalone user guide. It checks the generated limits before
compilation and again before copying the guide from `docs/PolicyWitness.md`.
Stale documentation stops the build; regenerate it with
`python3 docs/generate_limits.py` and review the changes before building.
Distribute that staged guide with the release ZIP from the same build.
The tracked [dist README](../dist/README.md) describes the output directory;
builds also copy its README and AGENTS.md into a custom `DIST_DIR`.

## Build

Preferred entrypoint:

```sh
make build IDENTITY='Developer ID Application: YOUR NAME (TEAMID)'
# or:
IDENTITY='Developer ID Application: YOUR NAME (TEAMID)' ./build.sh
```

Requirements:

- `IDENTITY` names a **Developer ID Application** identity present in your
  login keychain. Nothing is selected automatically and any other identity
  class is refused; the rules are under [What `build.sh` signs](#what-buildsh-signs).
- Xcode Command Line Tools; `clang` and `swiftc` come from the selected
  developer directory and the macOS SDK that `xcrun --sdk macosx` reports.
  The build selects that SDK once, as `SDKROOT`, before Cargo and Meson run,
  and refuses when `xcrun` cannot.
- Meson 1.12.1 or newer and Ninja 1.13.2 or newer (`brew install meson ninja`).
  `meson.build` enforces Meson's minimum and `build.sh` Ninja's.
- The two knobs, `BUILD_XPC` and `PW_INSPECTION`, take exactly `0` or `1`,
  and an unset knob means `1`; any other value, including an empty one, is
  refused rather than read as one of them.

The order is fixed: documentation and identity checks, git stamp, the
supported macOS from `Info.plist`, the SDK, the build directory, signing
identity, Cargo and the minimum-version check of its outputs, Meson, the
configured source and closure check and the minimum-version check of its
outputs, bundle assembly, identity check, nested signing, evidence, outer
seal, verification and the signer check, the standalone observer, guide, ZIP.
Each refusal precedes the step it protects: a stale document or identity copy
stops the build before any compile, a build directory configured for another
checkout and a bad identity before Cargo, a wrong source list or closure
before any output is copied, a wrong minimum version before assembly, an
executable that does not carry the named identity before the ZIP.

`PW_INSPECTION=1` (default) builds Swift with `-Onone -g`, gives the Rust
tools debug info, frame pointers and `opt-level=1` unless `RUSTFLAGS` is
already set, and leaves a `.dSYM` beside each Swift executable in the bundle;
`PW_INSPECTION=0` builds Swift with `-O` and omits the dSYMs. The C executables
are `-O2` without debug info in both variants. The knob is not one setting
across languages.

### Sandboxed automation harnesses

Some automation and agent harnesses run commands under a macOS sandbox. Inside
one, XPC lookup of the runner can be refused (`NSCocoaErrorDomain` code 4099,
or error 159 “Sandbox restriction”), so no runner launches; the unified log
tool can refuse to run (`log: Cannot run while sandboxed`), so deny evidence
cannot be captured; `codesign --verify` can report “invalid signature (code or
signature have been modified)” for an unchanged, validly signed app; and
Meson's Swift compiler discovery can fail because swiftc's default module
cache is not writable, so `meson setup` and therefore `build.sh` stop before
compiling. These refusals can be environment constraints. Request escalation
and rerun the same command once outside the automation sandbox against
unchanged artifact bytes. Treat a signature failure as environmental only
after the unsandboxed check passes; debug any failure that remains.

Two build steps need an unsandboxed shell. The signing identity lives in the
login keychain, which the sandbox may not open, and Meson's Swift discovery
compiles a sanity program with swiftc's default per-user module cache, which
the sandbox may not let it write; the targets themselves use the cache under
`builddir/`, but discovery runs first and only once per build directory. Both
refusals happen before anything is copied or signed. `BUILD_XPC=0` discovers
no Swift compiler, and the checks that only read the manifest (the
`source_drift` suite and the order-barrier control's reader) use file-mode
introspection, which discovers no compiler at all.

### Native compile with Meson

The root [meson.build](../meson.build) and [meson.options](../meson.options)
own the native compile: the C worker and validator, the C shim and the two
Swift executables, with their source lists, module names and flags. Both
files are host/worker identity inputs. `build.sh` runs Meson after Cargo into
the ignored `builddir/` and copies the four executables from there into the
bundle; the shim is linked into the host and is not a product.

`build.sh` passes exactly two options on every build (`meson setup` the first
time, `meson configure` afterwards, which regenerates only when a value
changed), so a build directory never retains an earlier variant and an
unchanged tree compiles nothing: `inspection` from `PW_INSPECTION` and `xpc`
from `BUILD_XPC` (false skips the Swift client and host and the shim; the two
C executables still build and no Swift compiler is discovered). The native
settings `meson.build` enumerates are fixed there and checked as effective
values on setup and on every regeneration: `meson configure` with any other
change, `-Dc_args=...`, a sanitizer, a changed optimization or debug level or
a different buildtype label makes the next build refuse with a message naming
the setting (the effective values are asserted before the label), before any
output is copied or signed. Meson reads `CFLAGS` and the other environment
flag variables only when a directory is first set up, and a fresh directory
refuses them the same way. Executables are linked with `b_asneeded=false`
declared per target, so a global value cannot add `-dead_strip_dylibs`. Meson
adds `-headerpad_max_install_names` and `-fdiagnostics-color` of its own,
compiles and links in separate steps and tracks included headers; those are
the accepted backend additions, and `tests/lib/meson_receipts.py` records the
effective commands so any further difference is visible. Because the link is a
separate step, swiftc no longer runs `dsymutil` itself; `build.sh` runs it for
inspection builds.

The supported macOS is the one this repository is tested on, declared in
`Info.plist` as `LSMinimumSystemVersion` and pinned in `meson.build`, which
passes it at compile and at link for the C and Swift executables; `build.sh`
exports the same value to Cargo for the Rust ones and refuses, before assembly
and in both variants, any Cargo or Meson output whose minimum version differs
from the plist, so the two declarations cannot disagree in a build that
completes. The selected SDK's default and an inherited
`MACOSX_DEPLOYMENT_TARGET` cannot change the native outputs, and the receipts
record each output's minimum version. Changing the supported version means
changing the plist and the manifest together; building for an older macOS from
a checkout is possible that way but not supported.

Before Cargo, `build.sh` refuses a build directory whose recorded source
directory is not this checkout, because Meson keeps compiling the directory it
was set up for; the configured source check repeats that comparison. After
compiling, `build.sh` reads the configured directory's targets, the ones Meson
actually evaluated, and refuses unless every target's sources are exactly the
files the tree holds for it; a manifest that compiles a substitute, or a dead
declaration standing in for a live one, stops there, before any output is
copied. The same check reads Ninja's dependency log for the worker and the
shim: every repository file the compiler consumed must be an identity digest
input, so an include that reaches outside the digest's directories, by a
relative path or through a symlink, stops the build as well. The
`source_drift` suite applies the source-list expectation to the manifest read
without a build directory, through the shared reader in
`tests/lib/native_sources.py`. Both check membership, not what the compiler
does with those files.

`builddir/` and `controller/target/` are incremental build directories and
trusted working state, like the checkout they sit in, and for that checkout
only: a build directory configured for another is refused, and Cargo's output
directory is pinned to the checkout's. The build reads them: Meson, Ninja and
Cargo decide what is up to date from their own records, and nothing attests
that an output came from the current sources beyond those records.
Reproducibility rests on the source identity and a clean checkout at the
release commit, which the release procedure requires; reset a directory after
a toolchain change. The receipt pairs each output's hash and mtime with its
entry in Ninja's log; the recorded time precedes the file's by a few tens of
milliseconds for a cc rule, so a lag of seconds means the output changed after
Ninja produced it. That is evidence to read, not a verdict.

To build the native executables alone, run the same commands directly:

```sh
SDKROOT="$(xcrun --sdk macosx --show-sdk-path)" meson setup builddir -Dinspection=true -Dxpc=true
meson compile -C builddir
```

With `BUILD_XPC=0`, `build.sh` still runs Cargo, builds and minimum-checks
both C executables, checks the signing identity and signs and packages a
partial bundle without the XPC service, client or embedded helpers. That
bundle passes evidence generation but not the full artifact inspection, and it
cannot run specimens; it is an iteration convenience, never a release or test
artifact.

Toolchain selection is the operator's responsibility and is not fingerprinted.
Keep separate build directories for the Command Line Tools and Xcode, and use
a fresh directory, or `meson setup --wipe`, after changing the selected
compiler or SDK; reuse a directory for incremental builds under one selection:

```sh
DEVELOPER_DIR=/Library/Developer/CommandLineTools \
SDKROOT="$(DEVELOPER_DIR=/Library/Developer/CommandLineTools xcrun --sdk macosx --show-sdk-path)" \
meson setup builddir-clt
```

Meson discovers Swift by compiling a sanity program with swiftc's default
module cache; the targets themselves use `builddir/swift-module-cache`. The
tools that compare one native build with another, and the two checks that
read the manifest, are described under
[comparing native builds](../tests/README.md#comparing-native-builds).

## What `build.sh` signs

**Identity.** `IDENTITY` must name a Developer ID Application identity and
that identity must be listed by `security find-identity -v -p codesigning`.
Any other class (Apple Development, Mac Developer, ad hoc, self-signed) is
refused before Cargo runs, and nothing is ever selected automatically: the
build signs with the identity you named or does not sign at all. The tests
resolve their own identity separately (`PW_BYOXPC_IDENTITY`, then `IDENTITY`,
then a keychain identity whose team matches the app's).

**Gates before any signature.** The three generated identity copies must be
current (`generate_worker_identity.py --check`, run before compiling and again
before signing, where it refuses an identity input edited during the build
without regeneration; the build otherwise trusts the checkout not to change
under it), every Cargo and Meson output must have carried the plist's minimum
macOS, and the configured source lists and closure must have matched the tree,
all before assembly.

**Order.** Signing is “inside-out”, every signature with
`--force --options runtime --timestamp` (the timestamp needs network access
to Apple's timestamp service):

1. The helper tools under the app's `Contents/MacOS/`: `pw-runner-client`
   (when `BUILD_XPC=1`), `sandbox-log-observer`, `sbpl-check`.
2. The helpers embedded inside each runner service bundle:
   `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner` and
   `sb_api_validator`.
3. The service bundle `Contents/XPCServices/PWRunner.xpc`, with
   `runner/Services/PWRunner/Entitlements.plist`.
4. The evidence manifest, generated from the signed bytes of steps 1 to 3
   (see [Evidence artifacts](#evidence-artifacts)).
5. The outer `.app`, with `PolicyWitness.entitlements`, sealing everything
   under `Contents/` including the manifest. The dSYM bundles beside the Swift
   executables are sealed as resources; their DWARF files are not themselves
   signed.
6. `codesign --verify --deep --strict` of the result, then the signer check:
   every executable directly under the app's and the service's
   `Contents/MacOS`, whether or not the list named it, must carry the named
   identity with the hardened runtime; the dSYM bundles are resources, not
   executables.
7. The standalone `controller/target/release/sandbox-log-observer`, for
   direct use from the checkout; it is not part of the bundle.

`sign_macho` refuses a missing or non-Mach-O target: the signing list names
exactly the executables this build produced. When you add a helper under
either the app's top-level `Contents/MacOS` or an XPC service's nested
`Contents/MacOS`, add it to that list in `build.sh`, to `EXECUTABLES` in
`tests/lib/artifact.py`, to `tests/build-evidence.py` and to the README's
inventory; a helper left off the list arrives with the linker's ad hoc
signature, passes the seal and the deep verification, and is refused by the
signer check before the ZIP, as notarization would refuse it later.

Do not “fix” signing by adding `codesign --deep` to the signing steps.
Explicitly sign the known nested binaries and then sign the outer app.
`--deep` would sign whatever happens to be nested, which is the opposite of
a list.

**What is never production-signed.** The manual validator debugger helper,
`controller/tools/sb_api_validator/build.sh`, compiles the validator beside
its source and ad hoc-signs it with `debug.ent` for local debugging. Its
output is ignored by git, never enters the bundle, and is not the validator
Meson builds.

## Evidence artifacts

During the build, `tests/build-evidence.py` generates:

- `dist/PolicyWitness.app/Contents/Resources/Evidence/manifest.json`
- `dist/PolicyWitness.app/Contents/Resources/Evidence/symbols.json`

These are derived from the **actual signed binaries on disk** (hashes and
entitlements extracted via `codesign -d --entitlements`), and are intended to
make “what shipped” auditable. They are generated after the helpers and the
service are signed and before the outer seal, so the manifest describes
signed bytes and is itself sealed by the app signature.

## Release procedure

Run commands from the repository root, outside an automation sandbox, at a clean
checkout of the release commit. Tag first: `build.sh` derives the version it
stamps from the nearest `v*` tag, so a build made before tagging is stamped with
the previous version. `tests/lib/release_preflight.py` refuses a release from an
untagged or dirty tree, from a lightweight tag, when the remote already holds a
different tag of that name, or when `dist/archive/<tag>/` already exists.
It also refuses additions or rewritten sites in the committed
[prose baseline](../tests/fixtures/docs/prose_baseline.json) compared with the
nearest preceding annotated release tag. A preceding release without a baseline
is reported as such; `--report` turns a growth refusal into a warning.

```sh
git tag -a v0.2.4 -m "PolicyWitness 0.2.4"
make release NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: YOUR NAME (TEAMID)' RELEASE_NOTES=/path/to/notes.md
git commit tests/RETAINED.json -m "Retain the 0.2.4 release evidence"
make publish VERSION=0.2.4
```

`make release` runs the preflight, then the `make notarize` chain below (build,
sign, submit, wait, staple, validate, re-zip, accept), then the full default
battery against the stapled app into `tests/out/runs/release-<version>-default`,
then `tests/lib/release_archive.py`, which archives the accepted release under
`dist/archive/v<version>/`. Archiving stages the ZIP, guide, checksums, original
command receipts, notes and complete test evidence, verifies the copy, and
exposes the completed archive by rename. The attempt's receipts end up under
`evidence/`, with a `<attempt>.archived` pointer under `dist/evidence/`.
The acceptance and battery working directories are added to `tests/RETAINED.json`.
Finally, `tests/lib/release_rotate.py` removes eligible older working test output
as described below. Commit the resulting retention index change.
Archiving and rotation each hold the test checkout lock across their reads and
mutations; acceptance and the battery also use that lock. Run no other battery
while `make release` runs. Nothing in `make release` leaves the machine except
the notarization submission.

### Portable test evidence and release cleanup

Each archive contains `evidence/test-runs/runs.tar.gz`, with the full acceptance
directory under `acceptance/` and the default battery under `battery/` when
provided. Its `manifest.json` records the original retention entries, per-file
hashes, modes, symlink targets, and checksums of the compressed archive and
standalone summaries. `release.json` binds that manifest by SHA-256. Its
`acceptance.path` and `battery.path` resolve to summaries within the release
archive; `original_path` records the former location under `tests/out`.
Original command receipts retain their original paths. Verifying the portable
copy does not need the working test directories or extract any archive member.

Successful release packaging is the automatic cleanup checkpoint. Tests can
create fresh run directories freely during development; no new-test hook,
schedule, age threshold or disk-size threshold prunes other output. Growth
during a refactor is expected until the next packaged release.

Cleanup keeps the new release's working acceptance and battery plus the newest
completed local output under `tests/out/runs/` or `tests/out/release-acceptance/`.
The recorded completion timestamp determines newest, including failed runs;
ties are all kept. Names, file modification times and sizes do not determine
retention. Starting cleanup for an older release while a newer one is indexed
is refused. Explicit manual pins remain protected exceptions.

Both release retention entries carry `"release": "v<version>"`, making them
eligible at a later release checkpoint. An omitted or null `release` is an
explicit pin. Release entries should carry their established tag, including
entries for older archives without portable bundles. Do not infer ownership
from directory names or reason text. Absent older rotating entries are retired
from the index too; absent pins remain protected.

Older owned runs and acceptance output are disposable at the checkpoint.
Interrupted or ambiguous output with valid ownership is eligible when it started
before the new release battery. Newer unfinished work survives until a later
checkpoint. Acceptance holds a separate lifetime lock through extraction, its
nested dispatcher, final checks and receipts, so even work outside the nested
tests stays protected. Legacy acceptance requires a report and valid nested
dispatcher ownership. Unknown ownership, symlink redirects, explicit pins,
overlaps, and pending external-runner cleanup are kept with reported reasons.
Session removal and registry-recovery receipts must establish cleanup before
their output can be removed; release cleanup never removes machine services.

The new release's portable evidence must verify before cleanup begins. Older
development output is not automatically archived before deletion, and historical
release archives are not modified. There is no off-machine evidence backup,
monitoring, or backup prerequisite. `.tmp` is outside test cleanup and follows
[its disposable-scratch policy](../.tmp/AGENTS.md), preserving that policy file.

Cleanup holds `tests/.checkout.lock` through planning, atomic retention
replacement and deletion. It records ownership and file inventories in
`evidence/rotation.json`, then renames eligible directories into a private
transaction under `tests/out/.release-rotation/`. Only after staging does it
retire their index entries and delete the quarantined copies. That directory
is outside ordinary pruning. The journal survives interruption, including a
partial deletion; resumption rechecks the new archive, pins and remaining bytes.
It never deletes a replacement run at an original path. Keep the quarantine and
journal together until completion. A later checkpoint refuses to start while
an earlier transaction still has quarantined output; resume that transaction first.

Preview or resume just this last step with the archived version:

```sh
python3 -B tests/lib/release_rotate.py dist/archive/v0.2.7
python3 -B tests/lib/release_rotate.py dist/archive/v0.2.7 --apply
```

Preview is read-only. `--apply` either creates a journal or resumes its existing
transaction; a completed journal is a no-op, so later test runs cannot trigger
another sweep under the same release. A cleanup failure does not require
rebuilding or resubmitting the release. Evidence archives remain local, ignored
files; the three published assets do not include the test evidence bundle.

### Publication

`make publish` is the outward step. `tests/lib/release_publish.py` pushes the
tag if the remote lacks it, creates the GitHub release once from the archived
assets with `--verify-tag`, reads the release back, downloads every asset,
compares bytes and digests with `SHA256SUMS`, and only then records the release
and asset URLs in `release.json` and the reply in `evidence/github-release.json`.
Re-running it verifies an existing release and creates nothing. Archives that
declare portable test evidence must pass its verification before any push or
GitHub operation. It needs an authenticated `gh`; `RELEASE_NOTES=` overrides
the archived notes.

### Lower-level notarization

`make notarize` is the lower-level chain. It **builds again**, even if you
already built and tested the app, and its last step tests the actual final ZIP;
a successful earlier test run is not release acceptance. It prints the preflight
findings as warnings rather than stopping, so a rehearsal still records what it
stamps. For an already-built ZIP, use the individual steps below.

```sh
make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: YOUR NAME (TEAMID)'
```

`entitlement-jail` is the working keychain profile on the maintainer's machine.
It is an explicit input, not a built-in default. Other machines need their own
configured profile and Developer ID identity.

The Makefile keeps these steps in order and stops on any failure. After the
build, it creates one `dist/evidence/<UTC timestamp>-<unique suffix>/` attempt
(or `evidence/` under a custom `DIST_DIR`). Its `release.json` records the input
ZIP hash and embedded build stamp; its README indexes the results as steps finish.
Named `notarization/`, `staple/`, `staple-validation/`, `gatekeeper/`, and `re-zip/`
directories hold raw receipts. Missing steps have no recorded result.

| Step | Changes | Evidence of success |
| --- | --- | --- |
| Build and sign | App, embedded manifest, initial ZIP | Inside-out signatures verify |
| Submit once | Uploads a retained copy of the ZIP | Recognized submission ID saved locally |
| Wait once | No local artifact change | Explicit `Accepted` for that submission |
| Staple | Attaches Apple's ticket to the app | `stapler staple` succeeds |
| Validate | Reads the stapled app | Staple validation and Gatekeeper assessment succeed |
| Re-zip | Replaces ZIP with the stapled app | ZIP creation succeeds |
| Accept archive | Extracts a disposable copy and runs checks | `acceptance.json` has `ok: true` for the final ZIP's SHA-256 |
| Battery (`make release`) | Runs the default battery against the stapled app | `run.json` passes with no skips, unrun cases or harness errors and an unchanged app |
| Archive (`make release`) | Verifies staged assets, receipts and portable test evidence; retains working runs | `dist/archive/v<version>/release.json` with `origin: null` |
| Cleanup (`make release`) | Keeps the release and newest local evidence; retires older owned output under the checkout lock | `evidence/rotation.json` records a completed transaction |
| Publish (`make publish`) | Pushes the tag, creates the release, verifies uploads | `release.json` records `origin` and `evidence/github-release.json` exists |

`notarize.py` owns only submission and one bounded wait. It preserves the input
as `evidence/<attempt>/notarization/submitted.zip` beside the input ZIP.
That directory also holds `result.json`, the submission ID, the archive hash,
and raw stdout/stderr plus command/exit/timing records for both calls. A zero
exit requires recognized acceptance; process success alone is insufficient.
It accepts extra response fields but treats malformed, missing, mismatched, or
unrecognized status data as **unknown**, never as acceptance. The captured bytes
remain authoritative for manual inspection; this parser is not a promise about
Apple's future responses.

The upload has a 180-second local deadline. Apple's `notarytool wait` is invoked
once with `--timeout 5m`, with a 330-second local backstop. The tool does its own
waiting; our code adds no polling loop, retry, resubmission, or resume state
machine. Stapling and assessment commands also have 60-second local deadlines
through `tests/lib/release_commands.py`, which prints the exact command and
retains its outputs under that attempt's named step directory. These deadlines stop local work;
they do not cancel or classify work at Apple.

### Individual steps and manual equivalent

Build once with `make build IDENTITY=...`. Then submit the
existing ZIP with the bounded helper:

```sh
RELEASE_EVIDENCE="$(/usr/bin/python3 -B tests/lib/release_evidence.py dist/PolicyWitness.zip)"
/usr/bin/python3 -B notarize.py dist/PolicyWitness.zip entitlement-jail --evidence-dir "$RELEASE_EVIDENCE"
```

Without `--evidence-dir`, `notarize.py` creates a new attempt and prints its
notarization directory. An existing attempt must identify the same archive and
input hash; its notarization directory cannot be reused for a second submission.

To perform its two Apple calls yourself, retain the submitted ZIP and their raw
responses in a new evidence directory first. A successful upload is not approval:

```sh
RELEASE_EVIDENCE="$(/usr/bin/python3 -B tests/lib/release_evidence.py dist/PolicyWitness.zip)"
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
/usr/bin/python3 -B tests/lib/release_commands.py --step staple "$RELEASE_EVIDENCE" 60 xcrun stapler staple dist/PolicyWitness.app
/usr/bin/python3 -B tests/lib/release_commands.py --step staple-validation "$RELEASE_EVIDENCE" 60 xcrun stapler validate -v dist/PolicyWitness.app
/usr/bin/python3 -B tests/lib/release_commands.py --step gatekeeper "$RELEASE_EVIDENCE" 60 spctl -a -vv --type execute dist/PolicyWitness.app
rm -f dist/PolicyWitness.zip
/usr/bin/python3 -B tests/lib/release_commands.py --step re-zip "$RELEASE_EVIDENCE" 60 ditto -c -k --sequesterRsrc --keepParent dist/PolicyWitness.app dist/PolicyWitness.zip
bash tests/accept-release.sh dist/PolicyWitness.zip --evidence-dir "$RELEASE_EVIDENCE"
```

Run these one at a time and stop if any command fails. A named step cannot
overwrite an earlier receipt. For a standalone command, omit `--step` and pass
the distribution directory: `/usr/bin/python3 -B tests/lib/release_commands.py
dist 60 COMMAND ...` creates a separate dated attempt under `dist/evidence/`.
Manually issued Apple calls retain raw replies but do not synthesize the
helper's `result.json`; their status must be read from those replies.
Stapling intentionally changes the app after submission, and re-zipping changes
the archive hash. The submitted and final ZIPs therefore have separate evidence.

### Apple replies now, later, or never

A nonzero exit, timeout, interruption, pending status, or unfamiliar response
stops automatic continuation. Read the recorded stdout **and** stderr. Do not
infer rejection from a timeout, infer acceptance from an exit code or prose, or
run `make notarize` again merely to check progress: it rebuilds and submits again.
If Apple asks for a policy agreement, stop and let the maintainer resolve it and
wait for Apple's systems. There is no special string-matching retry path.

If an ID is available, a later **manual, one-shot** status query is:

```sh
xcrun notarytool info "$SUBMISSION_ID" --keychain-profile entitlement-jail
# For an explicit rejection, inspect its detailed log:
xcrun notarytool log "$SUBMISSION_ID" --keychain-profile entitlement-jail
```

Preserve that output as well. No ID means submission state is uncertain; inspect
the responses and, if necessary, the account's submission history before deciding
whether a new submission is appropriate. There is no automatic retry in either
case. Do not edit or regenerate the manifest to make a failed artifact pass.
For a one-shot history query, use
`xcrun notarytool history --keychain-profile entitlement-jail` and retain its output.

After later acceptance, continue from stapling, not rebuilding. If `dist` has
changed, set `NOTARY_EVIDENCE` to the retained submission directory and extract
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
`/private/tmp`. It checks the extracted app's signatures and manifest, validates
its staple, assesses Gatekeeper, and runs two existing contracts through its own
controller and bundled standard XPC runner: an allowed read and a denied read.
It verifies both cases completed successfully and preserves all test evidence.
Neither case signs anything, installs an external runner, or rebuilds the app.
Inherited `PW_*` settings cannot select a local fallback build.

The input ZIP and extracted app must remain unchanged throughout acceptance.
The temporary extraction is removed; reports, command outputs, and inventories
remain in a fresh `tests/out/release-acceptance/run-*` directory. That directory
is printed, and `acceptance.json` binds the result to the final archive hash.
With `--evidence-dir`, a small `acceptance.json` pointer in the release attempt
records that report's location, result and final hash; test evidence stays under
`tests/out/release-acceptance/` and follows the existing retention rules.
Only distribute the ZIP matching a successful report. This is a local macOS
assessment, not a claim about every recipient's machine or Gatekeeper cache.

## Preserved release archives

`dist/archive/<version>/` contains exact release assets, `SHA256SUMS`, a
`release.json` provenance record, and supporting `evidence/`, including the
portable test bundle and rotation receipt when produced by these helpers. `make release`
creates one per version through `tests/lib/release_archive.py`; the two earlier
examples, `v2.3.0` and `v0.2.3`, were assembled by hand on either side of the
version reset. The guide is included when it was distributed. Provenance records
distinguish a verified published asset (`origin.kind: github_release`, written
by `make publish`) from locally retained material; unknown source commits remain
null. An archive's directory name is not evidence that a corresponding Git tag
is available. Original command receipts retain their original paths.

These artifacts are ignored and local. Recover published assets from their
recorded release URL and verify their checksums; a rebuild of a tag does not
recover the original signed release bytes.
