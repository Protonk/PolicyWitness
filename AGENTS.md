# AGENTS.md

Read [README.md](README.md) for repository orientation and the documentation index.
This file sets the working rules for this repository.

## Quick Router (open first)

- CLI and request handling: [controller/AGENTS.md](controller/AGENTS.md) and
  the [implementation reference](controller/README.md).
- Runner implementation and native helpers: [runner/AGENTS.md](runner/AGENTS.md)
  and the [implementation reference](runner/README.md).
- Build and release work: [docs/BUILD.md](docs/BUILD.md) and
  [docs/SIGNING.md](docs/SIGNING.md#release-procedure).
- Test work and evidence: [tests/AGENTS.md](tests/AGENTS.md); the
  [harness reference](tests/README.md) describes commands and coverage.
- Documentation and shared guide content: [docs/AGENTS.md](docs/AGENTS.md).
- Local artifacts: follow [scratch guidance](.tmp/AGENTS.md) or
  [distribution guidance](dist/AGENTS.md) before cleanup.
- Preparing a plan for someone else to execute:
  [planning guidance](CONTRIBUTING.md#planning-a-change).

## Documentation

Describe current behavior. Don't add change-history notes to docs — `git log`
is authoritative. Put directory descriptions in READMEs and working rules in
`AGENTS.md` files, as described in [CONTRIBUTING.md](CONTRIBUTING.md).

## Core ideas

- **One-way sandbox per process**: preserve a fresh host and worker per specimen; never reuse a sandboxed process.
- **Host/worker split**: keep sandbox API calls and specimen application out of the XPC host so its reply path stays available.
- **Witness over interpretation**: record the observation supporting an effect; `rc == 0` alone is insufficient.
- **Predictions precede attempts**: preserve the collection/release barrier and the limited meaning of `query_first`. Rerun the opt-in `witness_contract/order_barrier_mutations` control whenever the wait, release store or eligibility rule changes.
- **No dishonest attribution**: never turn a permission-shaped failure into a sandbox-cause claim without supporting evidence, or claim agreement or disagreement between prediction and enforcement.
- **Runner simplicity**: keep orchestration in the host and post-apply work in the C worker; avoid clever abstractions and hidden pre-sandbox resource acquisition.

The [architecture tour](docs/ARCHITECTURE.md) explains the implementation
and evidence behind these constraints.

## Dev Workflow (fast path)

Run from the repository root:

```sh
make build IDENTITY='Developer ID Application: YOUR NAME (TEAMID)'
```

Use [the build guide](docs/BUILD.md) for prerequisites, settings, cache
compatibility and diagnostics; `make help` lists the operator commands.
`PW_FRESH_BUILD=1` replaces the build caches, and a changed compiler or SDK
needs it once. Adding or moving a native source requires updating its Meson
target. Build and test checks diagnose source-list, bundle inventory, signing
and provenance inconsistencies.

## External runner workflow

For BYOXPC installation, verification or cleanup, follow
[the runner commands](controller/README.md) and
[the external-runner guide](docs/PolicyWitness.md#external-runners-byoxpc).

Inspect `policy-witness runner list` and `runner reconcile` first. Record
`service_name`, `scope`, `bundle_path` and pending-cleanup ownership. Removal
warnings or `cleanup_retained: true` require recovery: retain staging and its
durable session record until absence is verified. A label prefix alone never
establishes cleanup ownership. User-scope installation needs a logged-in GUI
session; use the harness guidance below when launchctl or log access is refused.

## Testing

Follow [tests/AGENTS.md](tests/AGENTS.md) for selection, evidence reuse, output
ownership and cleanup. The default battery is `tests/run.sh` or `make test`;
`tests/run.sh --all --list` shows all cases and their requirements. Use a fresh
`PW_TEST_OUT_DIR=tests/out/runs/<name>` for separate evidence.

Never unlink `tests/.checkout.lock`; builds and test executions in one
checkout share it and run one at a time, so use a second worktree for
concurrent work. Do not bypass the helpers to remove protected evidence or
resource-cleanup records. Preserve interrupted release rotation and follow
the [test cleanup guidance](tests/AGENTS.md#preserve-and-clean-up-output).

## Sandboxed automation harnesses

A restrictive macOS automation sandbox can obstruct runner XPC lookup,
unified-log access, signing or keychain access, and Meson's Swift discovery.
It can also make signature verification fail for unchanged bytes. Inspect the
diagnostic before attributing a failure. Request escalation and rerun the same
failing command once outside that sandbox without changing the artifact under
investigation. Treat a signature failure as environmental only if that
unsandboxed verification passes; investigate failures that remain.

Follow [runner diagnostics](runner/AGENTS.md#sandboxed-automation-harnesses),
[test execution guidance](tests/AGENTS.md#sandboxed-automation-harnesses), or
[signing and compiler discovery](docs/BUILD.md#sandboxed-automation-harnesses)
for the affected workflow.

## Maintenance checklist (when changing things)

- Edit generator inputs, regenerate with the owning tool and review the result;
  never edit generated copies. The build checks them but does not regenerate
  them. [Generator contracts](tests/suites/source_drift/README.md#generator-contracts)
  identify ownership and checks; a stale-copy refusal names its generator.
- Keep build behavior and its account in [docs/build.json](docs/build.json)
  aligned. Protocol or build-input changes require worker-identity regeneration;
  layout changes also require C/Swift agreement and review of the layout golden.
- For request or evidence changes, update affected admission, transport, readers,
  fixtures and documentation together. Use [the wire contract](docs/CONTRACT.md)
  to decide version changes; its manifest owns the version values.
- For process, channel or boundary changes, update [docs/architecture.json](docs/architecture.json)
  and regenerate the architecture account. Citation checks establish that sources
  and checks exist; review whether they support the behavior being described.

Build and `source_drift` checks enforce mechanical agreement. They do not replace
review of changed semantics or the integrated tests that establish behavior.
