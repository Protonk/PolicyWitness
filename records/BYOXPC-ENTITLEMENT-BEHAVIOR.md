# A worker entitlement changes an SBPL-conditioned file operation

Investigation, 2026-10-06. No product changes.

Status: the behavior observed here is what the 2026-10-06 remediation builds on; the installer now embeds the supplied plist in the worker, the process whose entitlement the kernel consults, and selection checks that worker's true-valued keys.

## Observation

With the same SBPL and probe plan, moving an entitlement from host-only
possession to host-plus-worker possession changed both the query and the
attempt. The target was an ordinary seeded file in an owned `/private/tmp`
directory. The policy was:

```scheme
(version 1)
(allow default)
(deny file-write-data (literal "<owned-target>"))
(allow file-write-data
  (require-all
    (literal "<owned-target>")
    (require-entitlement "com.apple.security.cs.allow-jit")))
```

The step queried `file-write-data` on that target and attempted
`file/open_write`. The host carried `com.apple.security.cs.allow-jit = true`
in all three variants. The validator was unchanged.

| Worker signature | Query | Attempt | Independent file observation |
| --- | --- | --- | --- |
| Build signature, no entitlements | deny | `open_failed`, errno 1 | Seed bytes preserved |
| Re-signed Developer ID, empty entitlement dictionary | deny | `open_failed`, errno 1 | Seed bytes preserved |
| Re-signed Developer ID, entitlement true | allow | `ok` | File became byte `0x78` |

All three runs completed with top-level `ok`, valid envelopes and no test
overrides. The controlled empty-entitlements re-sign distinguishes the
entitlement change from re-signing alone. The pair's policy SHA-256 was
`e4d0e90b99d9a469a44e71490826cc350c409865cb4ad8e6b5e0544b4b54f0c7`.

This demonstrates a useful worker-entitlement capability that the ordinary
host-only installation does not provide. It supports the limited premise
that a fixed policy can produce different kernel query and operation results
with different worker entitlements. It does **not** exercise JIT, prove that
the JIT runtime exception is usable, or show that arbitrary policies consume
entitlements automatically. This specimen explicitly tests the entitlement.

## Reproduction and receipts

Create the target outside privacy-sensitive user folders and seed it before
each run. Make fresh owned bundle copies. For the two manually signed worker
variants, sign `Contents/MacOS/pw-probe-runner` with `codesign --force
--options runtime -s <identity> --timestamp --entitlements <plist>` **before**
the public installer signs the enclosing bundle. Keep host entitlements and
validator bytes fixed. Submit the specimen through the shipped controller;
only its runner selector changes between installations. Read the target
independently afterward. Capture all three executable signatures and both
individual and bundle verification. Remove each installation before the next.

Receipts are under
[signed-host-tmp](../tests/out/runs/byoxpc-investigation-20261006/signed-host-tmp/),
[signed-worker-empty-tmp](../tests/out/runs/byoxpc-investigation-20261006/signed-worker-empty-tmp/),
and [signed-worker-tmp](../tests/out/runs/byoxpc-investigation-20261006/signed-worker-tmp/).
Each includes `conditioned-write.specimen.json`, the raw envelope,
`effect.json` with before/after bytes, signing read-backs and cleanup receipts.
The [checked matrix](../tests/out/runs/byoxpc-investigation-20261006/final-check/behavior-matrix.json)
also verifies that all six signed/ad-hoc/mixed temporary-target variants used
the identical policy hash.

The candidate predicate was grounded in the installed macOS
`/System/Library/Sandbox/Profiles/application.sb`, which uses
`require-entitlement` in a `with-filter` around a Mach lookup permission.
The live run, rather than that source example, establishes its behavior here.

## A location-sensitive confound

Initial attempts targeted a file under the checkout's Desktop path. With the
entitled worker, these reached the 30-second client deadline without a reply.
An allow-all control did the same. A one-second
[sample](../tests/out/runs/byoxpc-investigation-20261006/jit-plain/sample-4683.txt)
of that control found the worker in `main → run_attempt → open → __open`.
Re-signing with an empty entitlement dictionary instead produced a completed
denied step. These results alone could not establish the desired behavioral
pair. Relocating the target to `/private/tmp` produced the completed results
above; the earlier receipts remain intact. Privacy mediation is a hypothesis,
not a diagnosed cause. This investigation did not attribute those stalls to
SBPL, JIT or signing rejection.

## Scope

macOS 14.8.9 (23J631), arm64, user scope, Developer ID Team `42D369QV8E`.
Checkout `e2115cf`; selected existing app build `435`, `33ad847-dirty`, pinned
by [binary inventory](../tests/out/runs/byoxpc-investigation-20261006/baseline/source-inventory.json).
No clean-build correspondence is asserted from that stamp. All installations
and fixture staging were removed; the original app was unchanged. Linked
receipts are gitignored local evidence, pinned in `tests/RETAINED.json`.
