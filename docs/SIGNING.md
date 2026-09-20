# Signing, building, and notarization

`PolicyWitness.app` is intended to be a coherent, signed specimen. The build pipeline is centralized in `build.sh`.

## Build

Preferred entrypoint:

```sh
make build
# or:
make build YOLO=1
# or:
IDENTITY='Developer ID Application: YOUR NAME (TEAMID)' ./build.sh
# or:
YOLO=1 ./build.sh
```

Key requirements:

- `IDENTITY` must be set to a **Developer ID Application** identity present in your keychain, or
  pass `YOLO=1` to auto-select the first matching identity.
- Xcode Command Line Tools are required (`swiftc` is discovered via `xcrun`).

## What `build.sh` signs

Signing is “inside-out”:

1. Sign nested helper tools under the app's `Contents/MacOS/` (host-side tools).
2. Sign helper tools embedded inside each runner service bundle, such as
   `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner`.
3. Sign the runner service bundle `Contents/XPCServices/PWRunner.xpc`.
4. Sign the outer `.app` last.

Do not “fix” signing by adding `codesign --deep` to the signing steps. Explicitly sign the known nested binaries and then sign the outer app.
When you add a new embedded helper under either the app's top-level
`Contents/MacOS` or an XPC service's nested `Contents/MacOS`, add an
explicit signing step in `build.sh`. Notarization will fail if any
embedded tool remains ad hoc-signed.

## Evidence artifacts

During the build, `tests/build-evidence.py` generates:

- `dist/PolicyWitness.app/Contents/Resources/Evidence/manifest.json`
- `dist/PolicyWitness.app/Contents/Resources/Evidence/symbols.json`

These are derived from the **actual signed binaries on disk** (hashes and entitlements extracted via `codesign -d --entitlements`), and are intended to make “what shipped” auditable.

## Release procedure

Run commands from the repository root, outside an automation sandbox. `make
notarize` **builds again**, even if you already built and tested the app. Its last
step tests the actual final ZIP; a successful earlier test run is not release
acceptance. For an already-built ZIP, use the individual steps below.

```sh
make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail YOLO=1
# Or choose the signing identity explicitly:
make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: YOUR NAME (TEAMID)'
```

`entitlement-jail` is the working keychain profile on the maintainer's machine.
It is an explicit input, not a built-in default. Other machines need their own
configured profile and Developer ID identity.

The Makefile keeps these steps in order and stops on any failure:

| Step | Changes | Evidence of success |
| --- | --- | --- |
| Build and sign | App, embedded manifest, initial ZIP | Inside-out signatures verify |
| Submit once | Uploads a retained copy of the ZIP | Recognized submission ID saved locally |
| Wait once | No local artifact change | Explicit `Accepted` for that submission |
| Staple | Attaches Apple's ticket to the app | `stapler staple` succeeds |
| Validate | Reads the stapled app | Staple validation and Gatekeeper assessment succeed |
| Re-zip | Replaces ZIP with the stapled app | ZIP creation succeeds |
| Accept archive | Extracts a disposable copy and runs checks | `acceptance.json` has `ok: true` for the final ZIP's SHA-256 |

`notarize.py` owns only submission and one bounded wait. It preserves the input
as `dist/notarization-*/submitted.zip` (or beside the ZIP in a custom `DIST_DIR`).
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
retains its outputs under `dist/release-step-*`. These deadlines stop local work;
they do not cancel or classify work at Apple.

### Individual steps and manual equivalent

Build once with `make build YOLO=1` (or an explicit `IDENTITY`). Then submit the
existing ZIP with the bounded helper:

```sh
/usr/bin/python3 -B notarize.py dist/PolicyWitness.zip entitlement-jail
```

To perform its two Apple calls yourself, retain the submitted ZIP and their raw
responses in a new evidence directory first. A successful upload is not approval:

```sh
NOTARY_EVIDENCE="$(mktemp -d "$PWD/dist/notarization-manual-XXXXXX")"
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
xcrun stapler staple dist/PolicyWitness.app
xcrun stapler validate -v dist/PolicyWitness.app
spctl -a -vv --type execute dist/PolicyWitness.app
rm -f dist/PolicyWitness.zip
ditto -c -k --sequesterRsrc --keepParent dist/PolicyWitness.app dist/PolicyWitness.zip
bash tests/accept-release.sh dist/PolicyWitness.zip
```

Run these one at a time and stop if any command fails. For the same local deadline
and retained output as the Makefile, prefix an Apple command with
`/usr/bin/python3 -B tests/lib/release_commands.py dist 60`.
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
Only distribute the ZIP matching a successful report. This is a local macOS
assessment, not a claim about every recipient's machine or Gatekeeper cache.
