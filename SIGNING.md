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

1. Sign nested helper tools under `Contents/MacOS/` (host-side tools).
2. Sign the runner service bundle `Contents/XPCServices/PWRunner.xpc`.
3. Sign the outer `.app` last.

Do not “fix” signing by adding `codesign --deep` to the signing steps. Explicitly sign the known nested binaries and then sign the outer app.
When you add a new embedded helper under `Contents/MacOS`, add an explicit signing step in `build.sh`. Notarization will fail if any embedded tool remains ad hoc-signed.

## Evidence artifacts

During the build, `tests/build-evidence.py` generates:

- `dist/PolicyWitness.app/Contents/Resources/Evidence/manifest.json`
- `dist/PolicyWitness.app/Contents/Resources/Evidence/symbols.json`

These are derived from the **actual signed binaries on disk** (hashes and entitlements extracted via `codesign -d --entitlements`), and are intended to make “what shipped” auditable.

## Notarization (zip artifact)

The build produces `dist/PolicyWitness.zip` suitable for notarization submission. The
required order is: sign and zip, submit the zip to notarytool, then staple the
app bundle. This is what Gatekeeper expects.

Preferred entrypoint:

```sh
make notarize NOTARY_KEYCHAIN_PROFILE=dev-profile
# or:
NOTARY_KEYCHAIN_PROFILE=dev-profile make notarize
# or (auto-select codesign identity):
make notarize NOTARY_KEYCHAIN_PROFILE=dev-profile YOLO=1
```

Manual equivalent:

```sh
xcrun notarytool submit "dist/PolicyWitness.zip" --keychain-profile "dev-profile" --wait
xcrun stapler staple "dist/PolicyWitness.app"
xcrun stapler validate -v "dist/PolicyWitness.app"
spctl -a -vv --type execute "dist/PolicyWitness.app"
ditto -c -k --sequesterRsrc --keepParent "dist/PolicyWitness.app" "dist/PolicyWitness.zip"
```
