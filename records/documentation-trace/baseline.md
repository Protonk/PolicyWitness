# Documentation tracing baseline

Captured on 2026-11-15 for `DOCUMENTATION-TRACE-PLAN.md`. This is an inspection
record, not build, suite, live-specimen or release-history derivation evidence.

## Reconciled source

The starting commit is `2fcf9dbc9f08b1643426b4cf9b9b32e3782c86cc`. The checkout
was clean before capture. Its only difference from the reviewed commit
`6fcd2b5f1c84094405e2ce4de035b538a411b7cc` is the added plan, through commits
`f684a370`, `35f2a3bd` and `2fcf9dbc`. No production assumption changed during
that reconciliation.

`baseline.json` records per-surface canonical payload hashes, both stamp-table
bodies, free-text counts, current node counts, guide and interface artifact
hashes, shape golden hashes, build and worker identities, their selected input
hashes, and the 14 reachable annotated release tags. Full source bytes remain
in the starting commit rather than duplicated here. In particular:

```sh
git show 2fcf9dbc9f08b1643426b4cf9b9b32e3782c86cc:docs/contract/public.json
git show 2fcf9dbc9f08b1643426b4cf9b9b32e3782c86cc:docs/PolicyWitness.md
```

`baseline_capture.py` used the owning parser and `runtime.current_rows` to
establish that the current authored payloads equal the starting snapshot's
`surfaces` exactly. `runtime.check_shapes` found every current collected shape
equal to its golden. The free-text counts equal the carried ratchet, and the
CONTRACT and guide stamp-table bodies are identical. Every table row says
`unreleased`. The capture script is retained to describe how these observations
were obtained; rerunning it would replace the baseline and is not a comparison.

For placement proofs, compare `runtime.current_rows(tree)` against the
starting snapshot's `surfaces`, then compare the recorded file hashes, free
counts and stamp bodies. Hashes use SHA-256 of file bytes; payload hashes use
SHA-256 of `runtime.canonical(row['public']).encode()`. A `part` retirement
proof must compare structured public values after removing only `part` facts
from the predecessor, including shared/imported nodes. A public-change proof
must inspect the changed named nodes and effective scope, rather than comparing
only stamps or accepting refreshed shapes.

Starting build identity:
`development:31d146ab9ec5baad7afe66cd7ac7d2c267edfabc7c33c0b838990d333c6ca15c`.
Starting worker identity:
`ee5a7e5c6f3e254ff843b1329b17b8b01b5f575e0b73455d6816492480881ea2`.
The input hashes identify the files responsible for later identity changes.

## Equipment observations

`baseline-equipment.json` retains the command outputs and local prerequisite
inspection made by `baseline_equipment.py`. Selected build identity:

```sh
IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

`security find-identity -v -p codesigning` initially returned zero identities
inside the automation sandbox. The identical command with escalation returned
one valid Developer ID Application identity, SHA-1
`1A6E85D06FC762993C8BD3E932556DED3985F030`. The user keychain search list names
the login keychain. This establishes discovery, not use of the private key;
actual signing and timestamp-service access remain for the final build.

Both native-host sysctl reads failed with `Operation not permitted` in the
sandbox. Identical escalated retries succeeded: `hw.optional.arm64` was `1`
and `sysctl.proc_translated` was `0`. The observed host is macOS 26.7.1 arm64.
Xcode resolves to `/Applications/Xcode.app/Contents/Developer`; its SDK is
27.2, clang is Apple 21.0.0 (`clang-2100.4.1.1`) and Swift is 6.4.2.
Rust/cargo are 1.99.0, the arm64 Darwin target and rustfmt are installed,
Meson is 1.12.1, Ninja is 1.13.2 and the pinned Python is 3.14.9.
The recorded compiler, SDK and Rust versions in `builddir/pw-toolchain.json`
match these observations; full cache compatibility remains the build's check.

The interpreter-specific pytest 9.0.2 target passes its existing package
identity and file-hash validation. All three example operands are readable
regular files with nonempty prefixes and distinct device/inode pairs; their
sampled prefixes differ. These are prerequisite observations only, not the
round-trip case's before/after samples. The current app exists but was neither
verified nor credited; the plan requires the final signed build.

No required tool is presently known missing. XPC reachability, private-key use,
timestamp service access, full compiler discovery/build operation and native
execution have not been established. No suites, signed build or live specimens
ran for this capture. No existing evidence was modified.
