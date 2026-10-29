# Workset intake

Examined source: `bf7e97faab75754efe719b0bad20e83b67762c15` on `main`,
2026-10-29. The primary executor performed this intake. It is source inspection
and equipment discovery, not test execution or acceptance evidence.

## Source and existing work

`git status --short` was empty before intake and again after the server restart.
The preceding commits record the user-approved workset: `0aa1c92` (original
draft), `3b58519` (six revisions), `801f7d0` (acceptance authority) and
`bf7e97f` (final name). No implementation has changed in this engagement.

The four included plans remain present. Their most recent scope changes are
`4365395` (C goals/design preparation), `bbfcf40` (Swift two-stage proposal),
`c8bf47d` (Binding refinement) and `aeb64a8` (Checks preparation). The current
source still has the C worker and the two Swift files named by those plans;
`records/check-support/` and `records/checks-before-check/` do not exist.
The plans are pending assignments, not evidence of completed work.

The additional worktree
`/Users/raccoon/Desktop/Security/PolicyWitness-pytest-trial-evidence` is clean
at detached `6304fef`. It belongs to the earlier trial's evidence and is not
available for this workset's mutations or cleanup.

The current catalog's public `--all --list` resolves 238 cases, 199 default,
and 42 suite/include names. This supersedes the dated test survey's counts
for this intake only. The survey's examined source is `31b8195`; subsequent
history includes removal of Rust promotion classification, the pytest trial
and reversion, four expectation corrections, and relocation of build-entry
and native controls into three default preflight cases. The current dispatcher
and case ownership contracts were read directly; the dated survey is a guide
to obligations, not a claim that its old case census remains current.

## Equipment and artifacts

| Observation | Result and qualification |
| --- | --- |
| Host | `uname -m`: arm64; `sw_vers`: macOS 26.7.1, build 25G241. |
| Python | Public selection resolves Homebrew python@3.14 to the 3.14.9 keg; helpers start it through the repository wrapper. |
| Native/build tools | Meson 1.12.1, Ninja 1.13.2, cargo/rustc 1.99.0, Apple Swift 6.4, Apple clang 21.0.0, SDK 27.0. Graphviz is on PATH. These are discovery/version observations, not a successful build. |
| Signing | Sandboxed `security find-identity -v -p codesigning` reported zero identities. The same lookup outside the automation sandbox listed `Developer ID Application: Adam Hyland (42D369QV8E)`, fingerprint `1A6E85D06FC762993C8BD3E932556DED3985F030`. Actual signing and timestamp service availability remain to be exercised. |
| Distribution | `dist/PolicyWitness.app` and ZIP exist. App plist/provenance identify v0.3.3, build 853, source `1bf0341cd06c48122af1635e8aa8cac77517d9e1`, clean at build, worker identity `1df328dcb8820120e778caa9041c0b9c381d3d6e04f1b5174b43a97a549f929c`. Signature/inventory acceptance has not been rerun by this intake. |
| Source relation to that build | `git diff --name-only 1bf0341..bf7e97f -- controller runner build.sh meson.build meson.options tests/lib/native_sources.py docs/generate_worker_identity.py` names only `controller/AGENTS.md` and `runner/AGENTS.md`. This establishes the selected tree-file comparison, not artifact integrity or behavior. |
| Caches | `builddir/` and `controller/target/` exist. The signed build pipeline will determine their compatibility; no cache was replaced or adopted manually. |
| External runners | The distribution CLI's `runner list` returns no runners/pending cleanup. `runner reconcile` returns no candidates, records or inspection errors for the default registry. No runner was installed or removed. |

## Retained evidence and cleanup

`tests/RETAINED.json` has the v0.3.3 release acceptance and default-battery
entries, both explicitly associated with source `1bf0341`. Neither entry is
new workset verification. The v0.3.3 rotation journal says `state: complete`.
The `.release-rotation/` directory remains preserved.

The supported prune preview reported the checkout idle, no failures, fourteen
completed unretained drift/planning runs eligible for deletion, the retained
release run, and preserved unmanaged release-acceptance/rotation locations.
No pruning was applied. Those drift runs may contain useful cost observations
for D1, so selection and temporary pinning precede cleanup. Raw evidence is
local and gitignored; the existence of a named record or hash does not promise
that every earlier run is still available.

## Recovery and limits

A server restart interrupted the intake after read-only commands. Recovery
confirmed the same clean commit, no new execution plan or record package,
and an idle checkout lock via the supported preview. No workset test/build,
native experiment or sub-agent had been started. There were no workset-owned
processes, external services or cleanup records to recover.

No intake blocker requires user input. Native feasibility, actual signing and
live execution remain empirical obligations of later checkpoints. The initial
counterfactual can be completed without modifying the apparatus or running a
migration trial.
