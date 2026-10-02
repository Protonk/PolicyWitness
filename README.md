# PolicyWitness

>Read the [user guide](docs/PolicyWitness.md) for more detail.

PolicyWitness records `sandbox_check` queries and attempted operations under
macOS sandbox policies. When prediction is available, the validator queries
the worker's PID; the worker attempts its operation after applying the policy
and receiving release from the host. Each step records available results, missing
observations, submitted-scope relations and ordering. The controller adds
request identity, source hashes, imports, runner and app provenance, host
facts and hashes of selected binaries outside the app manifest. It does not
embed the full specimen. Optional log capture adds kernel denial records
with correlation limits. No record asserts agreement or disagreement between
prediction and enforcement.

Querying `sandbox_check` about a process and attempting an operation in that process under the same policy requires managing process lifecycles. `sandbox_check` answers for an existing PID, and sandbox application is one-way — a process gets exactly one sandbox. Evaluating a policy therefore means a fresh process per evaluation: compile and apply the policy to it once, aim both the query and the attempted operation at that PID while it lives, and carry the answer out through a channel the policy under test cannot sever.

## Flow

>Specimens -> Runs -> Steps -> Evidence

PolicyWitness operates on specimens: an SBPL policy plus a probe plan. The controller launches a fresh runner per specimen. The runner is an unsandboxed XPC host plus two short-lived children: `pw-probe-runner`, a sandboxed C worker that applies the specimen policy to itself and runs the probe plan and `sb_api_validator --batch` which queries `sandbox_check` for each probe against the worker's sandboxed PID. The host stays unsandboxed so the XPC reply path survives even under a strict `(deny default)` profile, joins both children's outputs into one JSON reply, and replies; the controller wraps that reply in the envelope it prints.

After application, the worker waits for host release. The host closes validator collection before releasing the entire attempt batch. A step whose native allow/deny answer matched its planned query records that ordering as `comparison.order: query_first`; it does not establish a shared state snapshot.

Each step records two evidence channels plus their comparison:

- **Attempt** (`steps[].attempt`): in-band kernel response — `rc`, `errno`, mach `kr` — from actually performing the operation inside the sandboxed worker.
- **Prediction** (`steps[].sandbox_check`): the userland `sandbox_check` answer for the submitted operation + filter against the same PID, supplied by the validator, or the reason no answer was available.
- **Comparison** (`steps[].comparison`): what the attempt channel observed and the raw fields that observation rests on, whether the submitted query names the attempt's operation and target, whether the query is known to precede the attempt batch, and any planner or lifecycle limitation. It relates the channels; it does not say whether they agree. The guide's [reading rules](docs/PolicyWitness.md#reading-a-comparison-record) say how to use it.

Unified-log evidence for kernel denies is attached out-of-band (best-effort).
Collection has a shared ten-second allowance and a fixed one-second cleanup
grace, with bounded output. `--log-timeout-ms` changes that allowance independently
of the runner timeout. Empty queries and collection failures cannot change the
execution result, predictions, attempts or process disposition. The scan covers
the client span rounded outward and padded by two seconds at each end; matching
records identify candidates, without proving exact run membership, a unique
attempt or a termination cause. See the [collection contract](controller/README.md#log-collection-budgets-and-cleanup)
and [operating guidance](docs/PolicyWitness.md#common-flags).

## Entitlements + SBPL

macOS sandboxing isn't just SBPL: a process's effective sandbox is its SBPL profile applied on top of the entitlements its binary was codesigned with. The same SBPL can yield different kernel behavior depending on which entitlements are granted, so a specimen has to describe both halves to be a faithful witness.

By default SBPL is applied to a process holding no entitlements. To observe a different combination, copy the bundled XPC service, sign it with your own entitlements plist, and install it via `policy-witness runner install --kind byoxpc`. The copied bundle inherits the runner's signed-caller check, so sign it with a Developer ID whose team matches the app (an ad-hoc/local runner must first have the caller-auth keys removed — see the guide). Specimens then select it via `runner.id` or `runner.service`. See the user guide ([docs/PolicyWitness.md](docs/PolicyWitness.md)) for the install recipe.

## What ships

This repo builds a single distributable app bundle:

- `dist/PolicyWitness.app`
  - `Contents/MacOS/policy-witness` (Rust controller)
  - `Contents/MacOS/pw-runner-client` (Swift NSXPCConnection wrapper)
  - `Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper)
  - `Contents/MacOS/sbpl-check` (SBPL compile-check helper)
  - `Contents/MacOS/sb_api_validator` (diagnostic copy of the validator CLI)
  - `Contents/XPCServices/PWRunner.xpc` (Swift XPC host; one host + two short-lived children per specimen)
    - `Contents/MacOS/pw-probe-runner` (bundle-local C worker that applies the policy and runs probe attempts)
    - `Contents/MacOS/sb_api_validator` (bundle-local validator launched once per run for sandbox_check verdicts)
  - `Contents/Resources/Evidence/*` (generated manifests: hashes/entitlements, `symbols.json`)

Build the app bundle with `./build.sh` (sign with `IDENTITY=...`; see [docs/SIGNING.md](docs/SIGNING.md)).
The [distribution directory](dist/README.md) describes the current deliverables,
release evidence, and preserved archives.

## How this is built

All of the code here was written by AI coding agents (Claude and GPT 5.x), including the tests. This project is a bet that a focus on testing and iteration over real use on top of some reasonable architectural choices **will suffice** for narrow, well-defined problem spaces. 

## Documentation

- Using the app:
  - User guide: [docs/PolicyWitness.md](docs/PolicyWitness.md)
  - Limits: [LIMITS.md](docs/LIMITS.md)
  - FAQ: [docs/QUESTIONS.md](docs/QUESTIONS.md)
  - Signing/distribution: [docs/SIGNING.md](docs/SIGNING.md)
- Implementation details:
  - CLI contract and controller behavior: [controller/README.md](controller/README.md)
  - Runner service architecture: [runner/README.md](runner/README.md)
- Contributing:
  - Repo orientation: [AGENTS.md](AGENTS.md)
  - Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
  - Testing: [tests/README.md](tests/README.md)
