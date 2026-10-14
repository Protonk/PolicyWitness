# `controller/`

The Rust controller drives a selected runner service and prints one JSON witness
per specimen. It ships as `PolicyWitness.app/Contents/MacOS/policy-witness`.
The runner owns policy application, predictions and attempts; the controller
owns request preparation, reply admission, provenance and optional log capture.
See [AGENTS.md](AGENTS.md) for working guidance and the
[user guide](../docs/PolicyWitness.md) for specimen and output formats.

## What lives in `controller/`

| Area | Sources and responsibility |
| --- | --- |
| CLI and orchestration | [main.rs](src/main.rs), [cli.rs](src/cli.rs), [run_flow.rs](src/run_flow.rs): dispatch, run preparation and envelope assembly. |
| Requests | [request_patch.rs](src/request_patch.rs): parsing, version admission and structured refusals; [runner_select.rs](src/runner_select.rs): selector validation and runner resolution; [augments.rs](src/augments.rs): named policy augmentation. |
| Reply transport and interpretation | [runner_client.rs](src/runner_client.rs): Swift-client invocation and capture; [disposition.rs](src/disposition.rs): worker disposition validation/projection; [json_contract.rs](src/json_contract.rs): envelope rendering. |
| Provenance | [dossier.rs](src/dossier.rs), [evidence.rs](src/evidence.rs), [digest.rs](src/digest.rs), [host_facts.rs](src/host_facts.rs): specimen records, manifest lookup, hashes and host facts. |
| Policy inspection | [policy_check.rs](src/policy_check.rs): independent compile-check capture; [sbpl_imports.rs](src/sbpl_imports.rs) and [sbpl_lex.rs](src/sbpl_lex.rs): bounded import scan and lexer, shared with `sbpl-check`. |
| Log evidence | [sandbox_log.rs](src/sandbox_log.rs): window, observer admission and candidate matching; [log_capture.rs](src/log_capture.rs): supervised reads and cleanup; [log_show.rs](src/log_show.rs): query and parser shared with replay controls. |
| External runners | [runner_commands.rs](src/runner_commands.rs), [runner_manager.rs](src/runner_manager.rs): commands, registry and launchd; [bundle.rs](src/bundle.rs) and [plist.rs](src/plist.rs): install-time bundle metadata. |
| Support and tests | [app_layout.rs](src/app_layout.rs), [utils.rs](src/utils.rs); inline Rust tests, shape-golden support in [shape.rs](src/shape.rs), [reply_fixtures.rs](src/reply_fixtures.rs), [log_replay_tests.rs](src/log_replay_tests.rs) and CLI tests in [integration/](integration/). |

[Cargo.toml](Cargo.toml) builds the controller and two top-level app helpers:
[sandbox-log-observer.rs](src/bin/sandbox-log-observer.rs) captures unified-log
denials; [sbpl-check.rs](src/bin/sbpl-check.rs) independently compiles SBPL.
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
policy-witness run <request.json> [--timeout-ms <n>] [--log-timeout-ms <n>] [--no-log-capture] [--runner-mode <standard|byoxpc>]
policy-witness runner <command> [options]
policy-witness --version
```

`--version` (or `version`) prints a `kind="version"` envelope with wire versions
in `data.contract`. Every envelope's `build` object carries the git-derived
`version`, `number`, `describe` and `commit`. `build.sh` stamps the same values
into the app and service Info.plists; a plain `cargo build` reports `unknown`.
The [build-stamp contract](../docs/CONTRACT.md#build-stamp) defines these fields.

`--timeout-ms` controls the runner RPC. Independently, `--log-timeout-ms` sets
the optional collection allowance, defaulting to
<!-- span limits.log_collection_timeout.value_unit -->10,000 milliseconds<!-- /span -->.
It accepts positive integer milliseconds representable in the monotonic clock,
including deadline and cleanup-grace addition. Zero, invalid and overflowing
values fail before invocation, even with `--no-log-capture`; there is no unlimited
value. `PW_VERIFY_EVIDENCE=1` adds manifest hash verification under
`data.specimen.app_provenance.evidence_verify`.

### `run`

1. Read the request, admit its version and selectors, resolve the runner and
   named augments, and collect the specimen dossier from the selected source.
2. Remove controller-owned selection fields and serialize the resolved request
   once. Deliver those held bytes to `pw-runner-client run --request -` on stdin;
   no temporary request file is written.
3. Invoke a fresh host for the specimen. After successful policy application in
   a fresh worker, the host collects eligible validator queries against that
   waiting worker, closes collection, then releases attempts and joins the
   observations into its reply. It omits the validator when no queries are
   eligible; refusals and earlier failures can stop before either child exists.
4. Admit the reply version, complete execution evidence, optionally collect
   denial logs, and print a single `kind="run"` JSON envelope to stdout.

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
fixed service path; external selection reads the registry. Neither reads an
`Info.plist`: service names come from the manifest or registry.

The controller launches `pw-runner-client` for the selected run, `sbpl-check`
only after an admitted `xpc_error` reply, and `sandbox-log-observer` when capture
is enabled and an authoritative worker PID and valid interval exist. The
observer launches `log show`. PlistBuddy, codesign, plutil, id and launchctl
belong to the separately dispatched `runner` commands; `bundle::read_bundle_info`
is used only by install.

[`RunDependencies`](src/run_flow.rs) names the controllable app root, manifest
loader, registry location and client invocation. Orchestration tests count
manifest loads and client calls; the built-in selection control uses an app
root without an Info.plist.

### Output contract

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 4, response schema 20, controller envelope 7. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

The [output reference](../docs/PolicyWitness.md#output-envelope) owns field
definitions, including the [specimen dossier](../docs/PolicyWitness.md#the-specimen-dossier)
and [comparison records](../docs/PolicyWitness.md#reading-a-comparison-record).
The controller retains the runner reply unchanged and interprets it only after
admitting its exact response version. Another integer version produces
`unsupported_runner_response`; a missing or noninteger version produces
`malformed_runner_response`. Both retain the reply with exit 1 and withhold
runner-derived diagnostics and log capture. Request-delivery failure takes
precedence as `tool_error`, leaving any captured reply uninterpreted.

`data.runner_client` records argv, timing, stdin delivery and stdout/stderr
received/retained byte counts. Each stream retains at most
<!-- span limits.controller_output.binary -->152 MiB<!-- /span -->;
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

### Execution and log-evidence ownership

For fixed runner reply and client capture bytes, collector contents,
availability and failures cannot change execution evidence or CLI exit status.
[`complete_execution`](src/run_flow.rs) constructs `CompletedExecution` before
`attach_sandbox_logs` invokes collection. `collect_log_evidence` returns only
`LogEvidence`; separate structs flatten into the shared wire objects.

| Wire fields | Owner and production writer |
| --- | --- |
| `result`, CLI exit status | Execution: [`complete_execution`](src/run_flow.rs); early admission and usage refusals remain in [`cmd_run`](src/run_flow.rs) and [cli.rs](src/cli.rs). No log inputs. |
| `data.runner_result` | Execution: [runner_client.rs](src/runner_client.rs) parses the reply; `ExecutionData` retains it unchanged. Logs borrow worker identity and attempt evidence without a mutable runner reference. |
| `data.runner_client`, `policy_check`, `specimen`, `timeout_ms`, `request_failure` | Execution: transport, preparation, admission and independent fallback compilation in [run_flow.rs](src/run_flow.rs). Client timestamps supply the later log window. |
| Diagnostics `process_disposition`, `termination_cause`, `stop_reason`, `disposition_integrity`, `disposition_issues` | Execution: [disposition.rs](src/disposition.rs) projects the carried worker disposition and raw supporting facts after response admission. |
| Entire `data.sandbox_log_capture` | Logs: [sandbox_log.rs](src/sandbox_log.rs) supervises and admits the observer; [`finish_sandbox_log_capture`](src/run_flow.rs) replaces candidate associations. Candidates never become runner-step or comparison fields. |
| Diagnostics `correlation_status`, `permission_failures_without_record` | Logs: [`log_diagnostics`](src/run_flow.rs), using capture status, authoritative worker PID, candidate associations and per-step observations. |

Only a `captured` report with an event array and authoritative worker PID can
yield `pid_match` or `no_match`. Failed reports can retain diagnostic events but
withhold associations. Disabled capture or absent worker identity yields
`not_attempted`; unavailable capture yields `unavailable`; a successful empty
array yields `no_match`. `permission_failures_without_record` is null unless
correlation succeeds and comparisons exist; then it lists permission-shaped
steps without captured candidates, or `[]`. It says nothing about the cause of
failure or what the OS log store contains.

The independent [consumer](../tests/lib/consumer.py) validates execution and
returns denial evidence separately. Lifecycle readers project execution fields
only. [Rust controls](../tests/suites/unit/README.md),
[consumer controls](../tests/suites/blackbox_e2e/README.md) and
[live witnesses](../tests/suites/witness_contract/README.md#termination-and-denial-log-correlation)
check this separation at their respective boundaries.

### Log collection budgets and cleanup

The query uses the runner client's start/end span, rounded outward to whole
seconds and padded by
<!-- span limits.log_window_pad.value_unit -->2 seconds<!-- /span --> at each end.
`window` retains the raw milliseconds, pad and UTC bounds; the observer must
mirror the interval or capture becomes `window_mismatch`. A backwards reading
produces `invalid_window` with null bounds and no observer invocation. The pad
allows clock differences but guarantees neither continuity, delivery nor exact
run membership. Matching uses worker PID, submitted attempt operation and path
evidence, retaining ambiguity and unmatched events. It cannot establish record
origin, step order, PID-reuse protection or termination cause. See
[denial-log correlation](../docs/PolicyWitness.md#denial-log-correlation).

The OS query is `/usr/bin/log show --style syslog --info --debug` with recorded
UTC bounds. Its `eventMessage MATCHES[c]` predicate has the regex shape
`(?s).*Sandbox:[ \t]+<escaped-name>\(<pid>\)([ \t]+.*)?`: literal process name
and complete parenthesized PID, followed by whitespace or message end. The name
is regex-escaped and the pattern JSON-quoted. There is no bare-digit alternative
or emitter-PID test; parsed worker PID is checked again before association.
The [committed archive control](../tests/fixtures/deny_capture/README.md)
tests OS selection before parsing.

Collection starts immediately before observer launch. Its internal
`--collection-budget` JSON carries `timeout_ms`, `timeout_source`,
`started_monotonic_ns` and `deadline_monotonic_ns`. The observer validates the
arithmetic and shares that `CLOCK_MONOTONIC` deadline without restarting it.
Startup, `log show`, reply parsing and association consume the same allowance;
these boot-relative readings are independent of wall-clock query bounds.
Standalone show mode has the same default allowance as `run`.
Increasing the allowance changes waiting time, not query bounds or byte limits,
and promises no records. `supervision.elapsed_ms` records actual collection cost.

Cleanup has one <!-- span limits.log_cleanup_grace.value_unit -->1,000 milliseconds<!-- /span -->
grace ending no later than the original deadline plus that grace. The observer
reserves <!-- span limits.log_report_reserve.value_unit -->1,000 milliseconds<!-- /span -->
to reap its log child and report before the controller deadline. `reserve_ms`
is zero at the observer boundary and records the reserve under
`observer.data.collection`; an allowance at or below the reserve leaves no query
time. These deadlines bound supervised waits, not OS scheduling or arbitrary
controller work.

| Stream | Retained limit |
| --- | --- |
| Inner log stdout | <!-- span limits.log_show_stdout.binary -->1 MiB<!-- /span --> |
| Inner log stderr | <!-- span limits.log_show_stderr.binary -->128 KiB<!-- /span --> |
| Observer stdout | <!-- span limits.log_observer_output.binary -->32 MiB<!-- /span --> |
| Observer stderr | <!-- span limits.log_observer_stderr.binary -->128 KiB<!-- /span --> |

Reads count bytes before decoding, parsing or PID filtering; an extra byte
detects overflow without being retained. Observer stdout includes the serialized
report and newline. Its bounded serializer accounts for repeated raw lines and
JSON escaping. Event, JSON-structure and candidate allocation guards bound
derived data; the [limits inventory](../docs/LIMITS.md) defines counting rules.
These are not peak-memory guarantees. Standalone follow mode has a separate
contract and is not used by `run`.

`sandbox_log_capture.supervision` describes the controller's observer capture;
`observer.data.collection` describes the observer's direct log child when a
reply exists. Each records budget/source, elapsed time, stream counts and
errors, process identity, wait observations, cutoff and cleanup.
`processing_cutoff` identifies controller parsing/correlation limits. Read counts
describe bytes actually read, not everything a stopped producer might emit.

| Cutoff | Capture status and retained evidence |
| --- | --- |
| `deadline` | `timeout`; boundary and effective allowance. |
| `output_overflow` | `overflow`; stream, limit and observed count. |
| `event_overflow`, `json_structure_overflow`, `correlation_overflow` | `overflow`; affected structure and count/charge. Candidate charges are conservative allocation/encoding allowances. |
| `launch_error` | `requested_unavailable`; no invented process observations. Observer resolution failure uses the same status. |
| `process_exit` | `error` for a nonzero/signaled exit without earlier cutoff; recognized inner log-access refusal is `blocked`. |
| `clock_error`, `pipe_setup_error`, `read_error`, `decode_error`, `wait_error`, `pipe_open_after_exit`, `cleanup_unconfirmed` | `capture_error`; available stream, wait and cleanup observations. |

A complete reply additionally passes JSON decoding, shape admission and window
matching (`parse_error`, `invalid_reply`, `window_mismatch` otherwise).
`captured` requires complete supervised collection and processing within budget;
it does not certify complete OS delivery. An earlier cutoff can coexist with
later cleanup failure, so `timeout` or `overflow` alone does not establish cleanup.
Serializer failure leaves bounded stderr and a nonzero observer exit, without
invented inner observations. Incomplete JSON remains a bounded raw prefix,
without fragment repair; intact failed replies retain diagnostic events but
withhold all correlations.

The observer starts in a dedicated group with PGID equal to its PID; the log
child inherits it. The controller observes leader exit without reaping, signals
the owned group, then performs bounded reaping and group probes. It sends no
group signal after releasing leader ownership. Only an `ESRCH` probe establishes
`group_absent`; signal delivery, EOF and leader exit do not. Lost ownership
withholds signalling and leaves cleanup unconfirmed. The observer separately
reports its child's wait; without a reply, that child's identity and wait remain
unknown even if the controller confirms group absence.

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
stderr. The generated plist sets `ThrottleInterval` to
<!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span -->;
this configures launchd's respawn throttle, not a maximum request latency.

Verify sends a fixed allow-all request on stdin, with a default timeout of
<!-- span limits.runner_verify_wait.value_unit -->5,000 milliseconds<!-- /span -->.
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
bootout it polls for service absence for up to
<!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span -->.
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
