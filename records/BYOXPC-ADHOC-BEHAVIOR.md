# Ad-hoc entitlement behavior: two bounded witnesses

Investigation, 2026-10-06. No product changes.

Status: unchanged in substance by the 2026-10-06 remediation; an ad-hoc install now signs the worker and validator ad hoc as well, before the bundle seal.

## Observation

An ad-hoc-signed worker carrying `com.apple.security.cs.allow-jit = true`
completed an entitlement-conditioned file write that its host-only counterpart
could not perform. The two owned hosts were also ad-hoc signed and had their
caller-auth keys removed consistently. Their validators retained the build
signature. The policy, target and probe plan were identical:

```scheme
(version 1)
(allow default)
(deny file-write-data (literal "<owned-target>"))
(allow file-write-data
  (require-all (literal "<owned-target>")
    (require-entitlement "com.apple.security.cs.allow-jit")))
```

The host-only variant produced query `deny`, attempt `open_failed`/errno 1,
and unchanged seed bytes. The host-plus-worker variant produced query `allow`,
attempt `ok`, and the independently read byte `0x78`. Both runs completed
normally. This establishes SBPL's use of the ad-hoc worker's entitlement in
this case, not JIT runtime behavior.

## Separate hardened-runtime control

To avoid interpreting that predicate test as proof of a runtime exception,
the existing exec observation fixture was copied and signed four ways. Each
copy used hardened runtime, with Developer ID or ad-hoc signing, and with an
empty entitlement dictionary or
`com.apple.security.cs.allow-dyld-environment-variables = true`.

A Python parent directly launched each fixture with exactly two environment
entries: a plain canary and `DYLD_LIBRARY_PATH` naming an absent subdirectory
of the owned temporary staging directory. No intermediate shell or PW exec
attempt was used. The fixture reported:

| Signature | DYLD exception | Environment count | DYLD value |
| --- | --- | --- | --- |
| Developer ID | absent | 1 | null |
| Developer ID | true | 2 | supplied path |
| Ad-hoc | absent | 1 | null |
| Ad-hoc | true | 2 | supplied path |

All reports were complete and all children exited zero. This is a direct
runtime-effect witness for this exception under ad-hoc signing on this host.
It does not establish launchd-to-host or host-to-worker propagation, dynamic
library loading, JIT, other exceptions, other macOS versions, or Gatekeeper
distribution acceptance. Apple's
[DYLD exception documentation](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.allow-dyld-environment-variables)
motivated the candidate; the reports establish these local observations.

## Reproduction and receipts

For the PW pair, use fresh owned bundle copies, identical host settings and
the specimen above. Sign the worker before installing the enclosing bundle
for the positive half. Capture signing read-backs, individual and recursive
verification, the envelope and the target's independent before/after bytes.
The exact inputs and receipts are in
[adhoc-host-tmp](../tests/out/runs/byoxpc-investigation-20261006/adhoc-host-tmp/)
and [adhoc-worker-tmp](../tests/out/runs/byoxpc-investigation-20261006/adhoc-worker-tmp/).

For the direct control, build [the existing fixture](../tests/fixtures/exec/build.sh),
copy it to owned temporary paths, sign each variant with `--options runtime`,
and invoke `--inspect <nonce> --env-key DYLD_LIBRARY_PATH --read-fd 200`
using `subprocess.run(..., env=<the two entries>, stdin=DEVNULL)`. Preserve
the report and exit status separately. The
[control driver](../tests/out/runs/byoxpc-investigation-20261006/signing_controls.py)
and [four complete receipt sets](../tests/out/runs/byoxpc-investigation-20261006/dyld-direct/)
contain exact signing commands, environment inputs and outputs.

## Scope

macOS 14.8.9 (23J631), arm64, logged-in user session. The PW pair used the
selected existing app, build `435`, `33ad847-dirty`, at checkout `e2115cf`;
its [inventory](../tests/out/runs/byoxpc-investigation-20261006/baseline/source-inventory.json)
identifies the tested artifact. The supplemental fixture was compiled from
the checkout's existing source. All runner and fixture staging was removed,
and the original app remained unchanged. Linked output is gitignored
local-only evidence, pinned in `tests/RETAINED.json`.
