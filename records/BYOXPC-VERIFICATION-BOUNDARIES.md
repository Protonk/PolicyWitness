# BYOXPC signature verification: integrity and authority boundaries

Investigation, 2026-10-06. No product changes.

## Observations

A Developer ID host, an ad-hoc worker carrying an entitlement, and a
build-signed validator coexisted in one installed copy. Ordinary bundle
verification, recursive strict verification, and individual verification all
passed. The host accepted the shipped client and the worker completed an
entitlement-conditioned file write. Thus neither successful verification nor
successful execution established a common authority across the three binaries.
The available Developer ID was the build's own; no second Developer ID team
was exercised. The ad-hoc worker supplies a witnessed authority difference.

An additional, never-launched copy isolated verification behavior:

| Copied bundle state | Installer's ordinary bundle check | Recursive strict bundle check | Individual worker check |
| --- | --- | --- | --- |
| Worker re-signed ad-hoc; old enclosing seal | fail | fail | pass |
| Enclosing bundle re-signed with Developer ID | pass | pass | pass |
| One signed worker code byte changed after sealing | pass | fail | fail |

The last row matters: a successful result from the exact command used by
`codesign_verify` did not establish integrity of the worker's code pages.
This was an offline verification experiment; the corrupted copy was never
installed or executed. It does not show that macOS would execute those bytes
or that a later launch would succeed. No Gatekeeper/notarization claim follows.

The [implementation](../controller/src/runner_manager.rs) invokes
`codesign --verify --verbose=2` on the bundle. Its signature metadata read-back
is another operation. Neither a read-back nor the successful ordinary check
in this control substitutes for the recursive or individual observation.

## Reproduction and receipts

For mixed-authority execution, sign only the worker ad-hoc with the test
entitlement before using the public installer to sign the host with the
matching Developer ID. Preserve caller authorization on the host. Capture
all three read-backs and the specimen's independent effect; remove the owned
installation with absence verified. Receipts are in
[mixed-worker-tmp](../tests/out/runs/byoxpc-investigation-20261006/mixed-worker-tmp/).

For the offline control, copy the shipped XPC bundle to owned temporary
staging. Re-sign its worker with `codesign --force --options runtime -s -`.
Run the three checks below before and after re-signing the enclosing bundle:

```sh
codesign --verify --verbose=2 <bundle>
codesign --verify --deep --strict --verbose=2 <bundle>
codesign --verify --verbose=2 <worker>
```

In a final unlaunched control, flip one bit of the worker byte at offset
16,384, leaving its code-signature blob intact, and repeat the checks. The
offset is specific to the retained binary, not a portable Mach-O editing
recipe. The [driver](../tests/out/runs/byoxpc-investigation-20261006/signing_controls.py)
and [verification receipts](../tests/out/runs/byoxpc-investigation-20261006/verification-controls/)
retain the exact command outputs and changed-byte description.

## Scope

macOS 14.8.9 (23J631), arm64; user-scope live installation; Developer ID Team
`42D369QV8E`. The source artifact's exact
[inventory](../tests/out/runs/byoxpc-investigation-20261006/baseline/source-inventory.json)
is retained. It reports build `435`, `33ad847-dirty`; the checkout was
`e2115cf`. The original artifact was not modified. All owned copies were
removed. Linked receipts are gitignored local-only evidence, pinned in
`tests/RETAINED.json`.
