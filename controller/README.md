# `controller/`

The Rust controller drives a selected runner service and prints one JSON witness
per specimen. It ships as `PolicyWitness.app/Contents/MacOS/policy-witness`.
The runner owns policy application, predictions and attempts; the controller
owns request preparation, reply admission, provenance and execution diagnostics.
See [AGENTS.md](AGENTS.md) for working guidance and the
[user guide](../docs/PolicyWitness.md) for specimen and output formats.

## What lives in `controller/`

| Area | Sources and responsibility |
| --- | --- |
| CLI and orchestration | [main.rs](src/main.rs), [cli.rs](src/cli.rs), [run_flow.rs](src/run_flow.rs): dispatch, run preparation and envelope assembly. |
| Requests | [request_patch.rs](src/request_patch.rs): parsing, version admission and structured refusals; [runner_select.rs](src/runner_select.rs): selector validation and runner resolution; [augments.rs](src/augments.rs): named policy augmentation. |
| Reply transport and interpretation | [runner_client.rs](src/runner_client.rs): Swift-client invocation and capture; [runner_acquisition.rs](src/runner_acquisition.rs): external host generation observation and re-acquisition; [disposition.rs](src/disposition.rs): worker disposition validation/projection; [json_contract.rs](src/json_contract.rs): envelope rendering. |
| Provenance | [dossier.rs](src/dossier.rs), [evidence.rs](src/evidence.rs), [digest.rs](src/digest.rs), [host_facts.rs](src/host_facts.rs): specimen records, manifest lookup, hashes and host facts. |
| Policy inspection | [policy_check.rs](src/policy_check.rs): independent compile-check capture; [sbpl_imports.rs](src/sbpl_imports.rs) and [sbpl_lex.rs](src/sbpl_lex.rs): bounded import scan and lexer, shared with `sbpl-check`. |
| External runners | [runner_commands.rs](src/runner_commands.rs), [runner_manager.rs](src/runner_manager.rs): commands, registry and launchd; [bundle.rs](src/bundle.rs) and [plist.rs](src/plist.rs): install-time bundle metadata. |
| Support and tests | [app_layout.rs](src/app_layout.rs), [utils.rs](src/utils.rs); inline Rust tests, shape-golden support in [shape.rs](src/shape.rs), [reply_fixtures.rs](src/reply_fixtures.rs) and CLI tests in [integration/](integration/). |

[Cargo.toml](Cargo.toml) builds the controller and the top-level app helper
[sbpl-check.rs](src/bin/sbpl-check.rs), which independently compiles SBPL.
Meson builds [pw_probe_runner.c](tools/pw_probe_runner/pw_probe_runner.c) and
[sb_api_validator.c](tools/sb_api_validator/sb_api_validator.c) and
[pw_extension_issuer.c](tools/pw_probe_runner/pw_extension_issuer.c) into
`pw-probe-runner`, `sb_api_validator` and `pw-extension-issuer`. Those native helpers live inside each
XPC service's `Contents/MacOS/`, resolved relative to that service's bundle.
The [runner README](../runner/README.md) describes their implementation.

### Why the Rust launcher still shells out

The controller uses the app's `Contents/MacOS/pw-runner-client` Swift helper for
`NSXPCConnection` wiring. Rust owns orchestration and capture, and consumes the
host's reply without directly managing its worker, validator or issuer. Issuer
binary provenance uses the same observed-path/hash/baseline rules as the other
helpers. After version admission, the controller checks native publication,
local-reference association, fresh-read consistency and phase collection evidence
before exposing derived disposition claims. These checks do not validate every
response field's shape; the full test consumer owns that broader validation.
The controller preserves the parsed reply unchanged, including malformed claim
evidence and degraded reporting-failure observations.

## CLI surface (contract)

```text
policy-witness run <request.json> [--timeout-ms <n>] [--runner-mode <standard|byoxpc>]
policy-witness runner <command> [options]
policy-witness --version
```

`--version` (or `version`) prints a `kind="version"` envelope with wire versions
in `data.contract`. Every envelope's `build` object carries the git-derived
`version`, `number`, `describe` and `commit`. `build.sh` stamps the same values
into the app and service Info.plists; a plain `cargo build` reports `unknown`.
The [build-stamp contract](../docs/CONTRACT.md#build-stamp) defines these fields.

`--timeout-ms` controls the runner RPC. `PW_VERIFY_EVIDENCE=1` adds manifest hash verification under
`data.specimen.app_provenance.evidence_verify`.

### `run`

1. Read the request, admit its version and selectors, resolve the runner and
   named augments, and collect the specimen dossier from the selected source.
2. Remove controller-owned selection fields and serialize the resolved request
   once. Deliver those held bytes to `pw-runner-client run --request -` on stdin;
   no temporary request file is written.
3. Invoke a fresh host for the specimen. For an external runner, an admitted
   `already_ran` with empty steps and no worker permits re-acquisition only after
   its live PID and start time identify the selected executable and that
   generation is observed gone. All attempts share the original timeout.
   Unknown process observations stop acquisition with the refusal. After successful policy application in
   a fresh worker, the host collects eligible validator queries against that
   waiting worker, closes collection, then releases attempts and joins the
   observations into its reply. It omits the validator when no queries are
   eligible; refusals and earlier failures can stop before either child exists.
4. Admit the reply version, complete execution evidence, and print a single `kind="run"` JSON envelope to stdout.

The validator uses batch NDJSON and `SANDBOX_CHECK_NO_REPORT` for every query,
including `none` filters, which pass no filter argument and report
`filter_type_id: 0` / `filter_value: null`. Predictions produce no denial records.
The [filter reference](../docs/PolicyWitness.md#what-policywitness-understands)
lists predicted and unavailable pairs; the
[batch contract](../tests/suites/validator_batch_mode/README.md) describes transport.
A failed launch retains `validator_spawn_failure` with its native code and
diagnostic, without inventing a validator subprocess or verdict.

| Exit | Meaning |
| --- | --- |
| `0` | `result.ok=true`. |
| `1` | Runner-reported failure, `bad_request`, or unreadable/unsupported reply. Malformed request JSON, versions, selectors and augments are `bad_request`, including controller refusals before XPC. `data.request_failure` carries the structured refusal. |
| `2` | Usage or tool failure: missing/unreadable request, unavailable runner, manifest failure or request-delivery failure. The run envelope retains the dossier collected so far and any client capture already obtained. |

### What a run reads and launches

[run_flow.rs](src/run_flow.rs) reads the request with `std::fs::read_to_string`;
[request_patch.rs](src/request_patch.rs) parses and admits it. A run also reads
the app evidence manifest once, requested augment files under
`Contents/Resources/Augments/`, the literal SBPL import closure, selected binary
bytes needed for dossier hashes, and host `sysctl` facts. Evidence verification
additionally hashes manifest entries. Built-in selection uses the manifest's
fixed service path; external selection reads the registry. External host re-acquisition also reads
process start times with `proc_pidinfo` and executable paths with `proc_pidpath`;
only ESRCH or an observed different start time establishes retirement. Neither reads an
`Info.plist`: service names come from the manifest or registry.

The controller launches `pw-runner-client` for the selected run, `sbpl-check`
only after an admitted `xpc_error` reply. PlistBuddy, codesign, plutil, id and launchctl
belong to the separately dispatched `runner` commands; `bundle::read_bundle_info`
is used only by install.

[`RunDependencies`](src/run_flow.rs) names the controllable app root, manifest
loader, registry location, process observer and client invocation. Orchestration tests count
manifest loads and client calls; the built-in selection control uses an app
root without an Info.plist.

### Output contract

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 5, response schema 23, controller envelope 8. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

The [output reference](../docs/PolicyWitness.md#output-envelope) owns field
definitions, including the [specimen dossier](../docs/PolicyWitness.md#the-specimen-dossier)
and [comparison records](../docs/PolicyWitness.md#reading-a-comparison-record).
The controller retains the runner reply unchanged and interprets it only after
admitting its exact response version. Another integer version produces
`unsupported_runner_response`; a missing or noninteger version produces
`malformed_runner_response`. Both retain the reply with exit 1 and withhold
runner-derived diagnostics. Request-delivery failure takes
precedence as `tool_error`, leaving any captured reply uninterpreted.

`data.runner_acquisition` records qualifying refused attempts, their client
captures, refusing generations and exit or failed-wait observations. It is empty
when none qualified. The final attempt alone supplies `runner_client`,
`runner_result`; refusal records never supply downstream
worker evidence. `runner verify` uses the same acquisition procedure and retains
the same refusal array.

`data.runner_client` records argv, timing, stdin delivery and stdout/stderr
received/retained byte counts. Each stream retains at
most <!-- span limits.controller_output.binary -->152 MiB<!-- /span -->;
full output is collected first, so this is not a streaming allocation bound.
`stdout_capture_error` identifies prefix loss and `stdout_parse_error` malformed
untruncated JSON/UTF-8. Accepted stdin writes prove neither client reads nor XPC
delivery. Capture is null when the client was not invoked.

`data.policy_check` is an independent compilation report, available only on the
admitted `xpc_error` fallback path. It retains the helper envelope and exit code
separately and copies an admitted helper's outcome without deriving another
verdict. It establishes neither worker progress nor the cause of a lost reply.
Worker evidence and transfer diagnostics pass through unchanged. Likewise,
`runner_reporting_failed` retains the host's diagnostic and available native
observations without per-step comparisons; `evidence_retained: false` identifies
the minimal reply when evidence-preserving serialization also failed.

### Execution evidence ownership

[`complete_execution`](src/run_flow.rs) derives CLI status from the admitted
runner outcome and preserves the reply unchanged. `execution_envelope` assembles
the dossier, transport, acquisition history, independent fallback compilation
and execution diagnostics. [disposition.rs](src/disposition.rs) validates the
carried worker disposition against supporting facts before projecting
`process_disposition`, `termination_cause`, `stop_reason`,
`disposition_integrity` and `disposition_issues`.

Worker identity comes only from `runner_subprocess.pid`; a host or client PID
is never a fallback. The client's start/end timestamps remain raw execution
observations, including backwards wall-clock readings. A failed attempt or a
signal alone does not establish sandbox cause.

### Runner selection (external entitlements)

Selection accepts `runner: { mode, id, service, required_entitlements }` and
top-level aliases `runner_mode`, `runner_id`, `runner_service`,
`required_entitlements`. Non-null nested values take precedence per field,
including an empty entitlement list; null means absent. Unknown nested keys,
wrong types and nonstring entitlement entries are refused, including malformed
shadowed aliases. These controller-owned fields are removed before XPC delivery.

The built-in mode is `standard`; an explicit mode with an external selection
must be `byoxpc`. Required keys must be present with value `true` in the worker's
recorded entitlement read-back (`worker_entitlements.granted`), using the
manifest for the built-in worker. Host entitlements do not satisfy requirements.
A missing or nongranted key refuses selection before contacting the host. Older
external records without worker read-back require reinstall when entitlements
are required, and remain selectable when none are required.

### `runner` (external runner manager)

```text
policy-witness runner install --bundle <path-to-xpc-bundle> [--kind byoxpc] [--service-name <name>] [--scope user|system]
                             [--identity <codesign-id>] [--entitlements <plist>]
                             [--allow-adhoc]
                             [--env KEY=VALUE]
                             [--skip-bootstrap]
policy-witness runner list
policy-witness runner status --id <runner-id> | --service-name <name>
policy-witness runner verify --id <runner-id> | --service-name <name> [--timeout-ms <n>]
policy-witness runner remove --id <runner-id> | --service-name <name> [--skip-bootout]
policy-witness runner validate
policy-witness runner reconcile
```

The [BYOXPC guide](../docs/PolicyWitness.md#external-runners-byoxpc) gives install
and signing recipes. The bundle must have `CFBundlePackageType=XPC!`; its Mach
service equals `CFBundleIdentifier`, and `CFBundleExecutable` selects the host.
Entitlements require `--identity` or `--allow-adhoc`. Install signs worker with
entitlements, validator without them, then the enclosing bundle; verifies the
tree recursively; and reads back each binary separately. Missing helpers refuse
installation. The inherited signed-caller check requires a matching Team ID;
the [ad-hoc recipe](../docs/PolicyWitness.md#caller-authentication-and-ad-hoc-signing)
describes the alternative configuration.

Install saves `pending` before creating the plist, then `installed` after
bootstrap (or plist creation with `--skip-bootstrap`). `data.state` and observed
`loaded` are separate. Errors after the pending save identify recovery state on
stderr. The generated plist sets `ThrottleInterval`
to <!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span -->;
this configures launchd's respawn throttle, not a maximum request latency.

Verify sends a fixed allow-all request on stdin, with a default timeout
of <!-- span limits.runner_verify_wait.value_unit -->5,000 milliseconds<!-- /span -->.
Status, verify and remove return `not_found` envelopes with exit 2 for unknown
registry keys. Validate checks the bundle recursively and each binary
individually, refreshing signature/entitlement observations and reporting
`data.invalid` and per-binary `data.failures`; it does not reconcile launchd.

### Registry ownership and recovery

The registry defaults to
`~/Library/Application Support/PolicyWitness/runners.json`; `PW_RUNNER_REGISTRY`
overrides it. Schema 1 accepts additive fields: absent state defaults to
`installed`, ownership and helper read-backs are optional, and absent
`pending_cleanup` and entitlement `granted` lists default empty. Ownership
records retain absolute bundle/executable/plist paths, launchd domain, installer
UID and expected plist hash. Cleanup retains this identity and before/after
observations independently of test output. Install checks service, bundle and
executable conflicts in both collections.

Install, remove and validate hold an OS advisory lock beside the registry
across modifications and launchd actions; competing modifiers fail as busy.
The stable `.lock` file remains in place. Atomic rename publishes complete old
or new registries to unlocked list/status/verify/reconcile readers. List exposes
both collections; status/verify report pending installation, which specimen
selection refuses.

Remove accepts either collection, rechecks executable/plist ownership, and
atomically moves ownership into `pending_cleanup` before cleanup. After its own
bootout it polls for service absence for up
to <!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span -->.
Warnings, `cleanup_retained` and `retained_record` expose unfinished recovery.
Retirement requires verified service/plist absence and a saved update. Unknown
inspection or permission failures preserve recovery; `--skip-bootout` retains it
while service presence is observed or unknown.

Reconcile is report-only: recorded state, observed service/plist presence and
ownership (`owned`, `unowned`, `ambiguous`, `unknown`). It also scans user
LaunchAgents and readable system LaunchDaemons for unrecorded
`com.policywitness.*` labels or `PWRunner` executables. These are reporting
candidates, not cleanup authorization. Reconcile creates no registry or lock and
makes no machine changes.
