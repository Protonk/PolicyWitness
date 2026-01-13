# Signing, building, and notarization

`PolicyWitness.app` is intended to be a coherent, signed specimen. The build pipeline is centralized in `build.sh`.

## Build

Preferred entrypoint:

```sh
make build
# or:
IDENTITY='Developer ID Application: YOUR NAME (TEAMID)' ./build.sh
```

Key requirements:

- `IDENTITY` must be set to a **Developer ID Application** identity present in your keychain.
- Xcode Command Line Tools are required (`swiftc` is discovered via `xcrun`).

## What `build.sh` signs

Signing is “inside-out”:

1. Sign nested helper tools under `Contents/MacOS/` (host-side tools).
2. Sign the runner service bundle `Contents/XPCServices/PWRunner.xpc`.
3. Sign the outer `.app` last.

Do not “fix” signing by adding `codesign --deep` to the signing steps. Explicitly sign the known nested binaries and then sign the outer app.

## Evidence artifacts

During the build, `tests/build-evidence.py` generates:

- `PolicyWitness.app/Contents/Resources/Evidence/manifest.json`
- `PolicyWitness.app/Contents/Resources/Evidence/symbols.json`

These are derived from the **actual signed binaries on disk** (hashes and entitlements extracted via `codesign -d --entitlements`), and are intended to make “what shipped” auditable.

## Notarization (zip artifact)

The build also produces `PolicyWitness.zip` suitable for notarization submission. Notarytool invocation and stapling are intentionally not automated in this repo; keep those steps in your release checklist.

