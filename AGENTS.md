# AGENTS.md

This file is for contributors and agents. It says how to act in this repository. What is here is described in [README.md](README.md); this file points at those descriptions rather than repeating them.

PolicyWitness is a sandbox witness harness. Each run hands a specimen (an SBPL policy plus a probe plan) to a fresh, unsandboxed XPC host, which spawns one sandboxed worker and one validator child, joins their outputs into one JSON reply, replies, and exits; the controller wraps that reply in the envelope it prints. The architecture and the path from specimens to evidence are in [README.md → Flow](README.md#flow).

## Quick Router (open first)

Pick what you’re changing:

- **CLI behavior / JSON contract** → [controller/README.md](controller/README.md), [controller/src/cli.rs](controller/src/cli.rs), [controller/src/run_flow.rs](controller/src/run_flow.rs)
- **Runner service (self-sandboxing witness)** → [runner/README.md](runner/README.md), [runner/Services/PWRunner/](runner/Services/PWRunner/)
- **Runner test machinery (unit tests, `_test_overrides`)** → [runner/AGENTS.md](runner/AGENTS.md)
- **Runner API types** → [runner/Sources/PWRunnerCore/PWRunnerAPI.swift](runner/Sources/PWRunnerCore/PWRunnerAPI.swift)
- **Query/attempt ordering (release barrier, `comparison.order`)** → [tests/FAILURE-PROPAGATION-CONTRACT.md → The record](tests/FAILURE-PROPAGATION-CONTRACT.md#the-record), [`wait_for_proceed`](controller/tools/pw_probe_runner/pw_probe_runner.c) in pw_probe_runner.c, the post-applied hook in [CWorker.swift](runner/Sources/PWRunnerCore/CWorker.swift), [`ComparisonEvidence`](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) in CWorkerOrchestrator.swift
- **Runner client (NSXPCConnection wrapper)** → [runner/Clients/PWRunnerClient/](runner/Clients/PWRunnerClient/)
- **Build + signing** → [build.sh](build.sh), [meson.build](meson.build), [docs/SIGNING.md](docs/SIGNING.md)
- **Release (tag preflight, notarize, archive, rotate, publish)** → [Makefile](Makefile), [docs/SIGNING.md → Release procedure](docs/SIGNING.md#release-procedure), `release_preflight.py`, `release_archive.py`, `release_runs.py`, `release_cleanup.py`, `release_rotate.py` and `release_publish.py` under [tests/lib/](tests/lib/)
- **Scratch work** → [.tmp/AGENTS.md](.tmp/AGENTS.md); scratch contents are disposable, except that tracked policy file.
- **Distribution output + release archives** → [dist/README.md](dist/README.md), [dist/AGENTS.md](dist/AGENTS.md)
- **Evidence generation / manifests** → [tests/build-evidence.py](tests/build-evidence.py)
- **Tests** → [tests/README.md](tests/README.md), [tests/run.sh](tests/run.sh)
- **Opt-in tests registry** → [tests/OPT_IN_TESTS.md](tests/OPT_IN_TESTS.md)
- **Limits and their documentation** → [docs/LIMITS.md](docs/LIMITS.md), [docs/limits.json](docs/limits.json), [docs/generate_limits.py](docs/generate_limits.py)
- **Wire contracts (request/response schema, worker identity, envelope)** → [docs/CONTRACT.md](docs/CONTRACT.md), [docs/contract.json](docs/contract.json), [docs/generate_contract.py](docs/generate_contract.py)
- **Architecture (one run in time, boundaries, the document graph, BYOXPC)** → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); its figures come from [docs/architecture.json](docs/architecture.json) through [docs/generate_architecture.py](docs/generate_architecture.py). Behavior that falls short of a stated promise is written there inline as a paragraph opening with "Known gap" and indexed in its last section.
- **Generators and the regions they write (invariants G1 to G11)** → [tests/suites/source_drift/README.md → Generator contracts](tests/suites/source_drift/README.md#generator-contracts)
- **Accepted-input teaching examples and refusal diagnostics** → [docs/REQUEST-GRAMMAR.md](docs/REQUEST-GRAMMAR.md), [tests/fixtures/request_contract/examples.json](tests/fixtures/request_contract/examples.json)
- **User guide** → [docs/PolicyWitness.md](docs/PolicyWitness.md); its Limits and Questions sections are copied from [docs/LIMITS.md](docs/LIMITS.md) and [docs/QUESTIONS.md](docs/QUESTIONS.md) by [docs/generate_limits.py](docs/generate_limits.py)

## Vocabulary (repo-anchored)

- **Specimen**: the unit of input for a run — policy (SBPL + params) plus a probe plan.
- **Controller**: the host-side orchestrator (`policy-witness`) that drives the runner and prints a JSON envelope.
- **Runner**: the ephemeral XPC service (`PWRunner.xpc`) described above. All processes are single-use per specimen.
- **Probe step**: a `sandbox_check` query paired with an attempted operation. The attempt kinds the worker implements are listed in [the user guide](docs/PolicyWitness.md#attempt-kinds-the-runner-implements).

## Bundle layout is a contract

Tests and evidence generation assume fixed paths inside `dist/PolicyWitness.app`. The inventory lives in three places, and they must agree:

- [README.md → What ships](README.md#what-ships) is the readable list.
- [tests/lib/artifact.py](tests/lib/artifact.py) (`EXECUTABLES`) is the machine-checked list; the `preflight` suite fails a build that does not match it.
- [build.sh](build.sh) holds the signing list; notarization fails if any embedded tool is left ad hoc-signed.

Read those before adding, renaming, or moving anything under `Contents/`. One convention is not obvious from the list. The C worker and the validator are embedded inside each XPC service bundle rather than at the app's top level, so the built-in runner and a BYOXPC copy each resolve their own helpers relative to their own bundle. What to update when a path changes is in the maintenance checklist below.

## CLI surface is a contract

The shipped CLI is intentionally small: `run` plus the `runner` management subcommands. The exact surface and flags are in [controller/README.md → CLI surface](controller/README.md#cli-surface-contract). Adding a flag or subcommand means updating that section and the usage text in [controller/src/cli.rs](controller/src/cli.rs) in the same change.

## Documentation

Describe current behavior. Don't add change-history notes to docs — `git log` is authoritative.

## Core ideas

- **One-way sandbox per process**: the worker applies exactly one sandbox to itself and exits. A new specimen means a fresh XPC host plus a fresh worker.
- **Host/worker split**: the XPC host never applies the specimen policy. That keeps the reply path alive under arbitrary `(deny default)` profiles and makes worker exit status (signal vs clean exit, partial vs full report) the source of truth for `runner_subprocess` + `normalized_outcome`.
- **Witness over interpretation**: “rc == 0” is never sufficient evidence of effect; the system must record the observation that supports a claim.
- **Predictions precede attempts**: the worker attempts nothing until the host has closed validator collection and stored `proceed`; `comparison.order: "query_first"` claims only that interval, never equal state or runtime identity; no record asserts agreement or disagreement between the channels. Changes to the wait, the release store or the eligibility rule must rerun the opt-in `witness_contract/order_barrier_mutations` control.
- **No dishonest attribution**: permission-shaped failures must not be collapsed into “sandbox denied” unless the run includes supporting evidence.
- **Runner simplicity**: runner code is meant to be inspectable and boring (avoid clever abstractions and avoid hidden pre-sandbox resource acquisition). Host-side orchestration belongs in `PWRunnerService.swift` and `CWorkerOrchestrator.swift`; post-apply work belongs in `pw-probe-runner` (the C worker).

## Dev Workflow (fast path)

- Build: `make build` (or `./build.sh`)
  - Requires `IDENTITY` to be set to a **Developer ID Application** identity in your keychain (see [docs/SIGNING.md](docs/SIGNING.md)).
  - If you are in a sandboxed automation harness, signing/keychain access may fail; ask for approval/escalation and rerun (see the harness note below).
- If you add a helper under the app or XPC bundle `Contents/MacOS`, update the [build.sh](build.sh) signing list; notarization fails if any embedded tool is left ad hoc-signed.
- Run: `dist/PolicyWitness.app/Contents/MacOS/policy-witness run tests/fixtures/pw_runner/<request>.json > result.json`

Build knobs worth knowing (debugging/iteration):

- `BUILD_XPC=0` skips building/embedding `PWRunner.xpc` + `pw-runner-client` (Rust-only iteration).
- The app version is derived from git (nearest `v*` tag, commit count); `PW_VERSION`/`PW_BUILD_NUMBER` override it. See [docs/CONTRACT.md → Build stamp](docs/CONTRACT.md#build-stamp).
- `PW_INSPECTION=1` (default) keeps symbols/frame pointers; set `PW_INSPECTION=0` for a more optimized build.
- Evidence is generated during build by [tests/build-evidence.py](tests/build-evidence.py) and embedded under `Contents/Resources/Evidence/`.

## External runner workflow (agents)

Use this when you are asked to install, verify, or clean up BYOXPC runners.

The `runner` subcommands (install/list/status/verify/remove/validate/reconcile) and the manual launchctl/plist cleanup recipes for both user and system scope live in [controller/README.md](controller/README.md) and [docs/PolicyWitness.md](docs/PolicyWitness.md). Agent-specific guidance:

- Inspect first: `policy-witness runner list` and `runner reconcile`; note `service_name`, `scope`, `bundle_path` and pending-cleanup ownership before acting. Removal warnings or `cleanup_retained: true` require recovery; keep test staging and its durable session record until absence is verified. A label prefix alone never establishes cleanup ownership.
- User-scope installs require a logged-in GUI session; sandboxed harnesses may block launchctl/log capture, so request escalation if needed (see the harness note below).

## Testing

- Default battery: `tests/run.sh` (or `make test`)
- Every registered case, including opt-ins: `tests/run.sh --all`
- Inspect selection without execution: `tests/run.sh --all --list`
- Smoke only: `tests/run.sh --suite smoke`
- Preview cleanup: `tests/run.sh --prune`; apply: `tests/run.sh --prune --apply` (also `make clean`). Only completed, owned, unretained direct children of `tests/out/runs/` are disposable. Standalone files, release acceptance and unmanaged output are preserved.
- After inspecting unfinished managed output, remove it explicitly with `tests/run.sh --prune --apply --unfinished <name>`. This command retains overlap checks and checkout locking; completed or retained targets are rejected.
- Opt-in tests (signing, launchd, and implementation-mutation controls) live under `tests/suites/<suite>/opt_in/` with wrappers under [tests/suites/opt_in/](tests/suites/opt_in/), and are documented in [tests/OPT_IN_TESTS.md](tests/OPT_IN_TESTS.md).
- Execution defaults to `tests/out/runs/default`; use fresh explicit `PW_TEST_OUT_DIR=tests/out/runs/<name>` paths for separate evidence. `tests/RETAINED.json` protects indexed paths, including absent local copies. Only completed, owned, unretained output can be replaced; interrupted, ambiguous and unmanaged evidence is preserved.
- Successful release packaging is the automatic test-cleanup checkpoint. Keep the latest release's acceptance and battery plus the newest completed local output, including failures; create fresh run directories freely during development. Cleanup also retires older owned interrupted output, but preserves active acceptance and pending external-runner recovery. Explicit pins have an omitted or null `release`; routine release entries rotate. No test-start, time-based or size-based cleanup runs. Preserve `tests/out/.release-rotation/` after an interruption and resume the archive's `release_rotate.py --apply` transaction; see [the cleanup procedure](docs/SIGNING.md#portable-test-evidence-and-release-cleanup).
- Execution holds `tests/.checkout.lock` across revalidation, execution and finalization. Competing runs fail with checkout-busy even for another output path; use a second worktree for parallel execution. Never unlink the lock file: a new inode would bypass an existing holder. Help and `--list` remain read-only and available.

### Runner test machinery (deep contract)

Two runner-specific testing contracts live in [runner/AGENTS.md](runner/AGENTS.md): the **Swift runner unit tests (SwiftPM)** layout (when to add a `runner_unit` test vs an e2e suite, stubbing `@convention(c)` pointers, adding a test file) and **`normalized_outcome` failure paths via `_test_overrides`** (the four-assertion recipe, where the supported keys are tabulated, and the rules for adding a new override). Read that file before touching either.

## Sandboxed automation harnesses

Some automation and agent harnesses run commands under a macOS sandbox. Inside one, XPC lookup of the runner can be refused (`NSCocoaErrorDomain` code 4099, or error 159 “Sandbox restriction”), so no runner launches; the unified log tool can refuse to run (`log: Cannot run while sandboxed`), so deny evidence cannot be captured; and `codesign --verify` can report “invalid signature (code or signature have been modified)” for an unchanged, validly signed app. These refusals can be environment constraints. Request escalation and rerun the same command once outside the automation sandbox against unchanged artifact bytes. Treat a signature failure as environmental only after the unsandboxed check passes; debug any failure that remains.

From here, the constraint touches three workflows in this file: building (keychain access for signing), external runners (launchctl and a GUI session), and testing (signature verification, live XPC and log capture). The copy of this note in [runner/README.md](runner/README.md#sandboxed-automation-harnesses) says what the refusal looks like in the envelope. The copy in [tests/README.md](tests/README.md#sandboxed-automation-harnesses) says what the dispatcher can detect and which suites never launch the XPC service.

## Maintenance checklist (when changing things)

- If host/worker protocol sources change: the build regenerates the exact identity with `python3 docs/generate_worker_identity.py`; direct source tests should regenerate first. Layout changes still require C/Swift agreement and review of the layout golden.
- If a wire contract version changes: edit [docs/contract.json](docs/contract.json) and run `python3 docs/generate_contract.py`; never edit a generated copy. Semantic response and envelope readers accept exactly the current versions; request admission and the worker ABI follow their own contracts (see [docs/CONTRACT.md](docs/CONTRACT.md)).
- If you change the specimen schema: update [PWRunnerAPI.swift](runner/Sources/PWRunnerCore/PWRunnerAPI.swift), [PWRunnerService.swift](runner/Sources/PWRunnerCore/PWRunnerService.swift), the worker plumbing ([CWorker.swift](runner/Sources/PWRunnerCore/CWorker.swift), [CWorkerOrchestrator.swift](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), [ValidatorClient.swift](runner/Sources/PWRunnerCore/ValidatorClient.swift), plus [pw_probe_runner.c](controller/tools/pw_probe_runner/pw_probe_runner.c) and [sb_api_validator.c](controller/tools/sb_api_validator/sb_api_validator.c) if the C side is affected), fixtures under [tests/fixtures/](tests/fixtures/), and any controller parsing assumptions.
- If you change shipped paths: update [build.sh](build.sh), [tests/build-evidence.py](tests/build-evidence.py), the [`EXECUTABLES`](tests/lib/artifact.py) list in tests/lib/artifact.py, [README.md → What ships](README.md#what-ships), tests that locate binaries, and any docs that enumerate the bundle layout.
- If you change evidence fields: update the envelope assembly in [controller/src/run_flow.rs](controller/src/run_flow.rs) and [controller/src/evidence.rs](controller/src/evidence.rs), any tests that validate output, and the docs that describe evidence channels.
- If you change who spawns whom, a channel between processes, or the guard on a boundary: update [docs/architecture.json](docs/architecture.json) and run `python3 docs/generate_architecture.py` (rendering needs Graphviz; `--check` does not). Every node and edge cites a source symbol and a check, and the generator refuses a citation it cannot find.
