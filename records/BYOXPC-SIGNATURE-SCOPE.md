# BYOXPC installation: the signature and entitlement scope

Investigation, 2026-10-06. No product changes.

## Observation

Installing a copied runner with `com.apple.security.cs.allow-jit = true`
embeds that entitlement in `PWRunner`, the host. It leaves `pw-probe-runner`
and `sb_api_validator` without entitlements. The registry records the host's
read-back. This occurred for both Developer ID and ad-hoc installation.

| Install | Host | Worker | Validator |
| --- | --- | --- | --- |
| Developer ID | Team `42D369QV8E`, runtime, entitlement present | Build signature, runtime, no entitlements | Build signature, runtime, no entitlements |
| Ad-hoc | No Team ID, runtime, entitlement present | Build signature, runtime, no entitlements | Build signature, runtime, no entitlements |

Every individual signature and both ordinary and recursive bundle verification
passed. The ad-hoc copy had its caller-auth keys removed before installation;
the Developer ID copy retained them. Both serviced a specimen.

This matters because the worker applies the specimen policy, while selection
and provenance describe the host's recorded entitlements. A successful install,
verification or entitlement-key selection does not establish worker entitlement
possession. The read-backs support the architecture's existing Known gap.

## Reproduction and receipts

Use a fresh complete copy of the shipped XPC bundle, a unique bundle/service ID,
user scope and durable ownership recorded before installation. Use the public
`runner install --identity <identity> --entitlements <plist>` command; for the
ad-hoc copy, remove `PWRunnerRequireSignedCaller` and
`PWRunnerAllowedIdentifiers`, use identity `-`, and pass `--allow-adhoc`.
Read each of the three executables with:

```sh
codesign -d --entitlements - --xml <executable>
codesign -dv --verbose=4 <executable>
codesign --verify --verbose=2 <executable>
codesign --verify --deep --strict --verbose=2 <bundle>
```

Compare the read-backs with the install envelope's registry record. Remove the
runner through the public CLI and verify service, plist and registry absence.

The [signed receipts](../tests/out/runs/byoxpc-investigation-20261006/signed-host/)
and [ad-hoc receipts](../tests/out/runs/byoxpc-investigation-20261006/adhoc-host/)
contain `registry-record.json`, `<binary>-signature/signature.json`,
`<binary>-entitlements.json`, raw command streams, and cleanup receipts.
The retained [driver](../tests/out/runs/byoxpc-investigation-20261006/investigate.py)
implements equivalent ownership and calls the existing session cleanup helper.
The source app's worker and validator hashes were respectively
`b7dc16d90805d374124860669e5111f6f5cc0885f72c9a33dc3314a1aa46f455`
and `d0b8000e85a39b9a737127ef5a6216099084063495c460273ea08efa4153f8c8`.

## Scope

macOS 14.8.9 (23J631), arm64, logged-in user session; available Developer ID
Team `42D369QV8E`. The checkout was `e2115cf`; the selected existing app reports
build `435`, `33ad847-dirty`. The receipts identify tested binary bytes through
the [app inventory](../tests/out/runs/byoxpc-investigation-20261006/baseline/source-inventory.json),
not an asserted clean build of the checkout. Sandboxed signature inspection
failed; inspection outside the automation sandbox passed against unchanged bytes.

All linked experiment output is gitignored, local-only evidence, pinned in
`tests/RETAINED.json`. The signed-path identity was the build's own identity;
this is not evidence about another developer's certificate or Team ID.
