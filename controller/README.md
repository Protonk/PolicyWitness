# `controller/` (Rust controller: specimen-first CLI)

This is developer documentation for the Rust code in `controller/`. It builds the command-line controller that ships as:

- `dist/PolicyWitness.app/Contents/MacOS/policy-witness`

PolicyWitness is **specimen-first**. The launcher’s job is to drive the embedded runner service (`PWRunner.xpc`) and to print a stable, machine-readable JSON witness for each run. The runner is an unsandboxed XPC host with two short-lived children: `pw-probe-runner` applies the policy and attempts operations; `sb_api_validator --batch` queries that worker PID. Their observations are joined into one envelope. The controller treats that as an implementation detail of the runner — it only consumes the host's reply.

For the Swift runner implementation details, see `runner/README.md`.

## What lives in `controller/`

Core controller modules:

- `controller/src/main.rs` — entry point and module wiring
- `controller/src/cli.rs` — CLI usage text + top-level dispatch
- `controller/src/run_flow.rs` — run orchestration and JSON envelope assembly
- `controller/src/runner_select.rs` — runner selection + provenance
- `controller/src/runner_client.rs` — wrapper around `pw-runner-client`
- `controller/src/sandbox_log.rs` — unified-log capture mapping for sandbox denials
- `controller/src/log_capture.rs` — bounded log subprocess reads, deadlines and owned cleanup
- `controller/src/log_show.rs` — the observer's show collector/parser, also used by supplied-text replay
- `controller/src/runner_commands.rs` — external runner install/list/status/verify/remove/validate/reconcile

Support modules:

- `controller/src/app_layout.rs` — app bundle layout + embedded tool resolution
- `controller/src/plist.rs` — PlistBuddy-backed Info.plist reads for BYOXPC install only; no run reads a plist
- `controller/src/bundle.rs` — bundle metadata reader for external runners
- `controller/src/request_patch.rs` — request file reading
- `controller/src/policy_check.rs` — host-side `sbpl-check` wiring
- `controller/src/utils.rs` — shared time + output helpers
- `controller/src/evidence.rs` — evidence manifest parsing, exact-path entry lookup and verification
- `controller/src/dossier.rs` — the specimen dossier (`data.specimen`): augmentation and import records, host facts, binary baselines
- `controller/src/host_facts.rs`, `sbpl_imports.rs`, `sbpl_lex.rs` — host facts, the import scan and the SBPL lexer, shared with `sbpl-check` through `#[path]` includes
- `controller/src/json_contract.rs` — JSON envelope rendering with sorted keys
- `controller/src/runner_manager.rs` — external runner registry + launchd wiring

Standalone helper tools (embedded into the `.app`):

- `controller/src/bin/sandbox-log-observer.rs` → `dist/PolicyWitness.app/Contents/MacOS/sandbox-log-observer`
  - Captures unified-log sandbox deny lines by PID + process name
- `controller/src/bin/sbpl-check.rs` → `dist/PolicyWitness.app/Contents/MacOS/sbpl-check`
  - Compiles SBPL policies independently of the runner; `policy-witness run` invokes it only on the `xpc_error` fallback path, and it is also a standalone diagnostic
- `controller/tools/sb_api_validator/sb_api_validator` — embedded inside
  each XPC service bundle as `…/Contents/MacOS/sb_api_validator`. The
  runner host launches it once per run in `--batch` NDJSON mode to
  cross-check `sandbox_check` verdicts inline alongside the C worker.
- `controller/tools/pw_probe_runner/pw_probe_runner` → embedded INSIDE
  each XPC service bundle at
  `…/Contents/XPCServices/<svc>.xpc/Contents/MacOS/pw-probe-runner`
  (not in the app's top-level `Contents/MacOS/`). The runner host
  resolves it relative to its own bundle so built-in and BYOXPC
  runners both pick up the correct copy. It owns the post-apply
  syscall surface and is the runner's production code path.

## CLI surface (contract)

The launcher intentionally exposes a minimal surface:

```text
policy-witness run <request.json> [--timeout-ms <n>] [--log-timeout-ms <n>] [--no-log-capture] [--runner-mode <standard|byoxpc>]
policy-witness runner <command> [options]
policy-witness --version
```

`--version` (or `version`) prints a `kind="version"` envelope whose `data.contract`
holds the wire contract versions the build was made with. Every envelope carries
a top-level `build` object: `version` (nearest `v*` git tag), `number` (commit
count), `describe` (`git describe --dirty`) and `commit`. build.sh derives them
from git and stamps the same values into the app and XPC service Info.plists;
a plain `cargo build` reports `unknown`. The stamp says which code produced an
envelope; the contract numbers say how to read it.

`run --log-timeout-ms <n>` sets the optional log collection allowance (default
10,000 ms). It accepts positive integer milliseconds representable in the shared
monotonic clock, including deadline and cleanup-grace addition. Zero, invalid or
overflowing values fail before runner invocation, even with `--no-log-capture`.
There is no unlimited value. The runner's `--timeout-ms` is independent.

### `run`

Runs a **single runner evaluation** against the selected runner service:

- Reads a request JSON file (runner request schema) that contains:
  - a sandbox policy (`sbpl` source),
  - and a probe plan (steps with `sandbox_check` + an attempted operation).
- Checks the request version and runner-selector types, resolves augments,
  removes controller-owned selection fields, serializes the request once, scans it for the dossier and
  delivers the same bytes to `pw-runner-client run --request -` on stdin. No
  temporary request file is written; `data.runner_client.request_delivery`
  records the bytes written and any delivery error.
- Starts a fresh runner instance (one XPC host + two short-lived children), applies the policy exactly once inside the C worker, executes the probe plan and validator batch in parallel, and returns the runner's structured JSON result.
- Captures supporting evidence (best-effort) using `sandbox-log-observer` and attaches it to the output. The requested `log show` interval is the runner client's own start-to-end span, rounded outward to whole seconds and padded by two seconds at each end, with no fixed lookback. A backwards wall-clock reading prevents the scan. The interval does not guarantee that every denied attempt has a log record. Pass `--no-log-capture` to skip this scan entirely. The scan's cost varies with the host's log archive, from a fraction of a second to seconds for the same short span; the reply records it as `data.sandbox_log_capture.supervision.elapsed_ms`, and the retained cost receipt (`tests/RETAINED.json`, run `followup-final-gate-03`, `supplemental/cost/`) is a measurement, not a guarantee.
- The embedded `sb_api_validator` runs in `--batch` NDJSON mode (one
  process per run), spawned by the runner host alongside the C
  worker. It reads NDJSON probes from stdin and writes NDJSON
  verdicts to stdout; the host folds each verdict into the matching
  `runner_result.steps[*].sandbox_check` block and surfaces process
  metadata as `runner_result.validator_subprocess`. See
  `tests/suites/validator_batch_mode/README.md` for the wire contract.
  Failed launches retain `runner_result.validator_spawn_failure` with the
  native return code, executable path, operation and diagnostic, forwarded
  unchanged even for unfamiliar codes. This is host evidence, not a validator
  verdict; no subprocess is invented when launch fails.
  Validator coverage rules:
  - **Predicted** filter kinds (the validator calls `sandbox_check`):
    `path`, `global_name`, `local_name`, `none`. `none`-filter probes
    call `sandbox_check(pid, op, 0)` with no filter argument and emit
    `filter_value: null` / `filter_type_id: 0` in the verdict.
  - **Skipped — prediction unavailable** (verified-unreliable op+filter
    pairs the runner accepts but deliberately does not predict for; see
    `docs/PolicyWitness.md` "Filter kinds where prediction is unavailable"):
    `(iokit-open-service, iokit_registry_entry_class)`,
    `(iokit-open-user-client, iokit_user_client_class)`,
    `(sysctl-read, sysctl_name)`. The runner short-circuits to
    `sandbox_check.outcome="prediction_unavailable"` (`rc=-1`); the
    `attempt` result is the reliable evidence.
  - **Unrecognized filter kinds** reject the specimen as `bad_request`.
    Known kinds requiring a value reject an absent
    or empty value as `bad_request` before any worker spawn.
- Prints a single JSON envelope to stdout (no output directories; stdout is the artifact).
- Emits `data.specimen`, the dossier that keeps results auditable: request path,
  policy augmentation and imports, host facts, runner and app provenance, and
  hashes of any selected binary the app manifest does not describe.

Exit codes:

- `0`: `result.ok=true`
- `1`: `result.ok=false`: a runner-reported failure, `bad_request`, or a reply
  the controller cannot read (`unsupported_runner_response` for another response
  schema, `malformed_runner_response` for a missing or noninteger version)
  Malformed JSON, versions, selectors and augment instructions are `bad_request`
  even when the controller refuses them before XPC. `data.request_failure`
  supplies a stable code and bounded field path; runner refusals are copied
  from `runner_result.request_failure`. See the [request refusal record](../docs/CONTRACT.md#structured-request-refusals).
- `2`: usage / tool error (`result.normalized_outcome: tool_error`): a missing or
  invalid usage argument, an absent or unreadable request, a runner-availability or
  manifest failure, or a request-delivery failure. The same `kind: "run"`
  envelope is printed with `result.error`, null execution records and the
  dossier collected so far.

### What a run reads and launches

The ordinary built-in `run` path, `run_flow::cmd_run` → `run`, reaches these
helpers and nothing else that touches the system:

- Reads: the request file (`request_patch::read_json_file`), the app evidence
  manifest once (`evidence::load_manifest`, under `PW_VERIFY_EVIDENCE=1` also
  the hashes `evidence::verify_manifest` compares), augment files under
  `Contents/Resources/Augments/` only when the request names augments, the
  literal import closure of the SBPL source (`sbpl_imports`), the selected
  binaries' bytes for the dossier's hashes (`dossier::Binaries::observe`), and
  the four host `sysctl` strings. Runner selection reads the manifest entry at
  the fixed shipped path (`runner_select::builtin_runner_target`); an external
  selection reads the registry JSON. No `Info.plist` is read on either path:
  the service name is the manifest entry's `bundle_id` or the registry record's.
- Launches: `pw-runner-client` once per selected run (`runner_client`),
  `sbpl-check` only for an admitted `xpc_error` reply (`policy_check`), and
  `sandbox-log-observer` unless `--no-log-capture` (`sandbox_log`). Nothing
  else on the run path spawns a process; `plist::plist_key_string` (the one
  PlistBuddy caller), `codesign`, `plutil`, `id` and `launchctl` are reached
  only from `runner_commands` through the `runner` subcommands, which `cli.rs`
  dispatches separately from `run`. `bundle::read_bundle_info` has one caller,
  `runner install`.

The dependencies a run acquires from its environment are named in
`run_flow::RunDependencies` (app root, manifest loader, registry location,
client invocation); the `orchestration` tests in `run_flow.rs` drive the real
`run` with them controlled and count manifest loads and client calls, and
`dossier::tests::builtin_selection_reads_the_manifest_entry_and_no_info_plist`
selects the built-in runner from a synthetic app root that has no `Info.plist`.
Keep this list current when a run-path helper gains a read or a launch.

### Output contract

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 4, response schema 14, controller envelope 7. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

The controller forwards the runner reply without version coercion and
interprets it only when its `schema_version` is the current response schema.
Another integer version is reported as `unsupported_runner_response` and a
missing or noninteger version as `malformed_runner_response`, each with
`result.ok: false`, exit 1, a version diagnostic, the reply retained in
`data.runner_result`, and no runner-derived diagnostics or log capture. A
request-delivery failure takes precedence as `tool_error` and leaves any
captured reply uninterpreted. Optional subprocess objects may be omitted or
null; a null per-step `errno` requires key presence.
Each step carries `comparison` (observation, submitted-scope relations, order
and limitations) and submitted attempt intent; the record relates the two
channels and never says whether they agree.
A `runner_reporting_failed` result makes `result.ok` false and
forwards the host's `reporting_failure` diagnostic unchanged. Retained queries,
attempts and subprocess observations have no per-step comparisons.
`evidence_retained: false` explicitly identifies the minimal reply when
even evidence-preserving serialization failed.
See the [comparison record](../tests/FAILURE-PROPAGATION-CONTRACT.md#comparison-record).


The controller prints one JSON envelope to stdout (`kind="run"`). It contains:

- `build`: the build stamp described under the CLI surface
- `data.runner_result`: the runner's JSON (if parseable)
- `data.runner_client`: argv + stdout/stderr + timing, exact received/retained
  stream byte counts and `capture_limit_bytes` (72 MiB). `stdout_capture_error`
  identifies controller prefix loss; `stdout_parse_error` identifies malformed
  untruncated JSON/UTF-8. Full output is collected first; this is not a streaming
  allocation bound. `request_delivery` records the stdin delivery
  (`bytes_written`, `error`); an accepted write does not prove the client read
  the bytes or that XPC delivered them. Null when the client was not invoked.
- `data.policy_check`: independent `sbpl-check` report, requested only on
  `xpc_error`. `status` is a transport status (`unavailable`, `capture_error`,
  `parse_error`, `tool_error`, `invalid_reply`) or the helper's own
  `normalized_outcome` copied from a supported envelope (`ok`, `compile_error`,
  `setup_error`, `bad_request`, `policy_too_large`); the helper envelope is
  retained whole under `envelope`, `tool_exit_code` is recorded independently,
  and the capture derives no second verdict from the compile record, `result.ok`
  or the exit code. It describes that helper's compilation, not the missing
  worker's progress or the cause of a lost reply. Worker failures use `runner_failed`;
  worker operation/result evidence identifies compilation, setup and application
  independently. The controller retains `runner_subprocess.worker_evidence` and
  `policy_transfer_error` without interpreting their diagnostic codes.
- `data.specimen`: the dossier, present on every run envelope. `request_path`;
  `policy.augmentation` (`status` of `not_requested`, `applied`, `failed` or
  `not_applicable`, applied names, `original_sha256`, `applied_sha256`, `error`)
  and `policy.imports` (the literal import closure of the selected source under
  the `sbpl-check` search paths and bounds: `status`, `closure_sha256`,
  `records`, `cycle`, `exceeded`, `failure`); `host` facts (`macos_version`,
  `macos_build`, `kernel_release`, `arch`); `runner_provenance` (runner identity
  and entitlements metadata); `app_provenance` (`evidence_manifest_path` and the
  optional `evidence_verify` report); and `binaries.{service,worker,validator}`,
  null when the selected binary is the manifest's entry for that role, otherwise
  `path`, `actual_sha256`, `baseline_sha256`, `verification` and `reason`. The
  guide's [dossier section](../docs/PolicyWitness.md#the-specimen-dossier)
  states each field's rule. The `xpc_error` path is the only one that triggers
  a host-side `sbpl-check` compile (to populate `policy_check` and disambiguate
  the failure).
- `data.runner_sandbox_diagnostics`: process disposition and optional denial
  correlation, independent of outcome labels. `process_disposition` is
  `no_worker`, `unconfirmed`, `clean_exit`, `nonzero_exit`, `signaled`,
  `conflicting`, `withheld` or `unrecognized`, projected from the worker
  disposition record the runner carries; `termination_cause` names witnessed
  host cleanup (`host_sentinel_deadline` and its siblings), is null for a clean
  exit and `unknown` otherwise; `stop_reason`, `disposition_integrity` and
  `disposition_issues` carry the projected stop reason and the record's
  validation (`withheld` with `missing_record` when a worker subprocess carries
  no record). `correlation_status` is `not_attempted`, `unavailable`,
  `no_match`, or `pid_match`.
  `permission_failures_without_record` lists the step IDs whose attempt the
  runner classified as a permission-shaped failure and that no captured event
  names as a candidate; it is null unless correlation was `pid_match` or
  `no_match` and the reply carries per-step comparisons. A non-empty list means
  this capture yielded no candidate for denials the attempts themselves
  reported, not that nothing was denied; it makes no claim about what the OS
  log store contains (a record can exist under another path form, such as a
  resolved symlink) and never says why.
- `data.sandbox_log_capture`: optional observer evidence, also captured for
  successful runs; null when disabled or no authoritative worker PID exists.
  `observer` is the observer's own envelope, retained unchanged: its
  `schema_version` is the controller envelope number, the frame every
  controller-family binary prints, and its `data.observer_schema_version`
  identifies the observer's report inside that frame (see
  [docs/CONTRACT.md](../docs/CONTRACT.md)). The report attributes nothing: it
  carries the denial records the log showed, each with its parsed fields and
  `raw_line`, beside the raw `log_stdout`.
  `window` records the scanned interval: the runner client's start and end
  (`started_at_unix_ms`, `ended_at_unix_ms`) and the whole-second UTC `start`
  and `end` strings handed to `log show`, which the observer mirrors back; a
  reply for any other interval is `window_mismatch`, not `captured`. If the
  client's end precedes its start, both strings are null, the raw milliseconds
  are retained, and `invalid_window` records that no observer was invoked.
  For ordered endpoints the bounds are `floor(client start) - 2 s` and
  `ceil(client end) + 2 s`; `window.pad_seconds` records the pad. The raw
  client milliseconds remain unchanged. The pad allows for
  differences between client and archive clocks; supported records in either
  padding region remain eligible candidates. It guarantees neither delivery
  nor exact run membership. Ordered endpoints alone cannot establish clock continuity during the run.
  Structured event timestamps, exact run membership, step ordering and PID-reuse
  protection are not available from this capture; the window carries its bounds
  and nothing that claims them.
  `step_denies` contains event references with candidate step IDs: one candidate
  is `candidate`, repeated matching attempts are `ambiguous`. Matching requires
  worker PID, exact attempt-relevant operation and exact target/path evidence.
  Attempt kind/action come from the request joined by unique step ID, never the
  independent sandbox-check query. `matching_evidence` records each candidate's
  mapped operation, submitted kind/action, matched path and path sources.
  The host's after-orchestration `attempt.path_diagnostics` forms (`realpath_resolved`,
  `parent_realpath_resolved`) are a match source only with a valid compact block,
  `runner_host`/`after_orchestration` provenance and an input equal to both the
  submitted target and reported requested path. They appear in `path_sources`
  under that provenance; a kernel record
  names the resolved path, so a target through a symlink correlates that way.
  Unmatched events remain
  in `deny_events`. Validator queries can themselves generate denial records
  naming the worker PID before attempts begin. Neither a matching path nor a
  candidate association establishes that an attempted operation produced a log
  record. A complete requested interval does not guarantee complete log delivery.
  [Operation mapping and correlation limits](../docs/PolicyWitness.md#denial-log-correlation).
- `data.timeout_ms`: the runner RPC timeout the client was given.

`data.sandbox_log_capture.capture_status` values:

- `captured`: both supervised captures completed, the reply shape and interval
  match, and parsing/correlation stayed within their budgets;
  this does not certify that every denial was logged
- `window_mismatch`: observer returned different or missing bounds, or a trailing
  lookback; its raw reply and parsed denial events survive, but `step_denies` is
  null and correlation is `unavailable`
- `invalid_window`: the client's wall-clock end precedes its start; scan bounds
  are null and no observer runs. Raw timestamps and a diagnostic in `stderr`
  survive; observer/events/associations are null and correlation is `unavailable`
- `blocked`: unified log access blocked (see `blocked_reason`)
- `error`: observer returned an error or non-zero exit
- `parse_error`: observer stdout was not valid JSON
- `timeout`: the shared collection deadline expired
- `overflow`: a stream, event, JSON-structure or candidate budget was exceeded
- `capture_error`: incomplete collection, decoding/read failure or unconfirmed cleanup
- `invalid_reply`: parsed observer JSON fails the required observation, identity,
  metadata or supervision shape
- `requested_unavailable`: observer could not be executed

### Log collection budgets and cleanup

Collection starts immediately before observer launch. The controller passes a
`CLOCK_MONOTONIC` deadline through the observer's internal `--collection-budget`
argument: a JSON object with `timeout_ms`, `timeout_source` (`default` or `cli`),
`started_monotonic_ns` and `deadline_monotonic_ns`. The observer validates the
arithmetic and uses the absolute deadline without restarting it. These are
boot-relative clock readings, not wall-clock query bounds. Startup, `log show`,
reply parsing and candidate association consume this same allowance. Standalone observer
show mode defaults to 10,000 ms. A larger `--log-timeout-ms` changes waiting time
only; it changes neither the query interval nor byte limits and promises no
record. Cleanup has one 1,000 ms grace ending no later than the original deadline
plus that grace. This bounds supervised waits, not OS scheduling or arbitrary
work elsewhere in the controller.

The observer stops its log child 1,000 ms before the shared deadline
(`log_report_reserve`) so it can reap the child and deliver its report before
the controller's own deadline; `reserve_ms` records that withholding (0 at the
observer boundary, 1,000 under `observer.data.collection`). An inner deadline
therefore normally arrives as an intact reply whose `observer.data.collection.cutoff`
is `deadline`, with its retained diagnostics, rather than as a killed observer.
An allowance at or below the reserve leaves no time for the query itself.

The show path counts bytes while reading both pipes: inner stdout 1 MiB, inner
stderr 128 KiB, observer stdout 32 MiB, observer stderr 128 KiB. One additional
byte detects overflow but is not retained. Inner stdout is already filtered by
the OS predicate; counting precedes PW decoding, parsing and PID filtering.
Observer stdout counts the serialized report and its final newline. The observer's bounded serializer
accounts for duplicated raw lines and JSON escaping. Event, JSON-structure and
candidate allocation guards bound derived data; [the limits inventory](../docs/LIMITS.md)
defines their counting rules and controls. These are stream and derived-data
bounds, not a promise about peak process memory. Standalone streaming/follow
mode has a separate contract and is not used by `run`.

The OS query uses `/usr/bin/log show --style syslog --info --debug` with the
recorded UTC `--start` and `--end`. Its `eventMessage MATCHES[c]` predicate has
the regular-expression shape `(?s).*Sandbox:[ \t]+<escaped-name>\(<pid>\)([ \t]+.*)?`:
one or more spaces/tabs after `Sandbox:`, a literal process name and complete
parenthesized PID, then whitespace or end of message. The name is regex-escaped
and the entire pattern is JSON-quoted for the predicate. There is no bare-digit
alternative or emitter-PID test: the emitting process can differ from the
worker named in the message. Parsed worker PID is checked again before association.
The required archive control validates OS selection before parsing; parser and
argument tests alone do not prove query selection. Its fixture and reader
requirements are in [the fixture README](../tests/fixtures/deny_capture/README.md).

`supervision` under `sandbox_log_capture` reports the controller's observer
capture; `observer.data.collection` reports the observer's direct log-child
capture when a reply exists. Each includes the effective budget and source,
elapsed time, boundary, per-stream limit/read/retained counts, EOF/truncation/read
errors, process identity and wait observations, cutoff and cleanup facts.
`processing_cutoff` records controller parsing/correlation limits; its `stream`
identifies the bounded structure. Received byte counts describe actual reads,
not the total output a stopped producer might have emitted.

Read the status together with the recorded cutoff and cleanup facts:

| Cutoff reason | Meaning and capture status |
| --- | --- |
| `deadline` | Shared allowance expired during collection or processing; `timeout`. |
| `output_overflow` | A raw stdout/stderr read exceeded its limit; `overflow`, with stream, limit and observed count. |
| `event_overflow`, `json_structure_overflow`, `correlation_overflow` | A derived-data guard was exceeded; `overflow`, with the affected structure and count/charge. Candidate-byte charges are conservative allocation/encoding allowances, not measured JSON sizes. |
| `launch_error` | Supervised executable could not start; `requested_unavailable`. Failure to resolve the observer before supervision also uses this status, without invented process facts. |
| `process_exit` | Nonzero or signaled exit without an earlier cutoff; `error`. A recognized inner log-access refusal uses `blocked` and retains its reason. |
| `clock_error`, `pipe_setup_error`, `read_error`, `decode_error`, `wait_error`, `pipe_open_after_exit`, `cleanup_unconfirmed` | Collection or cleanup could not be established; `capture_error`. Detailed wait, stream and cleanup observations remain available. |

An earlier cutoff can coexist with a later cleanup failure; `timeout` or
`overflow` alone never certifies successful cleanup. Malformed complete JSON,
invalid reply shape and mismatched windows have their own statuses above.
If the bounded observer serializer cannot produce a report, the observer exits
nonzero with a bounded stderr diagnostic; the controller cannot invent inner
observations from that missing report. The 32 MiB outer allowance accommodates
the bounded inner text, its repeated raw lines, worst-case JSON escaping and
metadata; fixed-corpus and escaping controls verify this relationship.

The controller spawns the observer into a dedicated group with PGID equal to its
PID. The log child inherits it. The controller observes leader exit without
reaping, signals the owned group, then performs bounded reaping and group probes.
It never sends a group signal after releasing the leader's ownership. Only an
`ESRCH` group probe establishes `group_absent`; signal delivery, pipe EOF and
leader exit alone do not. Lost ownership withholds signalling and leaves cleanup
unconfirmed. The observer separately reports its direct child's wait. If no
reply arrives, that child's identity and wait remain unknown even when the
controller confirms group absence.

Any failed or incomplete capture withholds all correlation: `step_denies`,
`permission_failures_without_record` is null and
`correlation_status` is `unavailable`. An intact diagnostic reply and its events
survive failure. Incomplete JSON remains a bounded raw prefix, without fragment
repair or recovered events. Execution result, exit code, native observations and
disposition were completed before collection and remain unchanged.

The default battery tests three separate claims. The committed archive and
independent manifest test real OS query selection before parsing; supplied-text
replay tests exact record/candidate preservation through production parsing,
reception, assembly and consumer recovery; live witnesses test native execution
and the capture facts returned by that invocation. A completed empty live query
or an evidenced budget cutoff with confirmed cleanup is admissible. Missing
equipment, blocked access, malformed complete replies and unexplained process
or cleanup failures still fail those live checks. None of these cases proves
that the OS emitted or delivered every denial. See the
[witness suite](../tests/suites/witness_contract/README.md#deny-capture-covers-the-run).

Optional:

- `PW_VERIFY_EVIDENCE=1` runs a manifest hash verification pass and includes a
  `data.specimen.app_provenance.evidence_verify` report in the output.

### Execution and log-evidence ownership

The execution channel is complete before optional log collection begins.
For fixed runner reply and runner-client capture bytes, changing collector
contents, availability or failure status cannot change execution evidence or
the CLI exit status. A matching event corroborates a candidate; it never
rewrites a comparison, failure attribution or termination cause. Missing
log evidence establishes neither allowance nor a sandbox cause for a
permission-shaped failure.

Ownership is per field, including inside the shared diagnostics object:

| Wire fields | Owner and production writer | Inputs and readers |
| --- | --- | --- |
| `result` and the returned CLI exit status | Execution: `complete_execution` in [run_flow.rs](src/run_flow.rs); early admission/usage failures remain in `cmd_run` and [cli.rs](src/cli.rs). | Runner `normalized_outcome` and `error`, then runner-client capture/parse errors. `cmd_run` prints the completed result and returns its exit status; no log fields are inputs. |
| `data.runner_result`, including predictions, native attempts, comparisons and worker/validator observations | Execution: [runner_client.rs](src/runner_client.rs) parses the runner reply; `ExecutionData` retains it unchanged. | Log processing borrows the reply for worker identity and candidate matching. It has no mutable runner reference. |
| `data.runner_client` (with `request_delivery`), `policy_check`, `specimen` and `timeout_ms` | Execution: runner-client capture, independent fallback compilation and `cmd_run` preparation ([dossier.rs](src/dossier.rs) collects the specimen before invocation). | Client timestamps supply the log query window. Fallback compilation runs only for a supported `xpc_error` reply; collector status does not request it or change its meaning. |
| `data.runner_sandbox_diagnostics.process_disposition`, `termination_cause`, `stop_reason`, `disposition_integrity`, `disposition_issues` | Execution: `execution_diagnostics` and `project_disposition` in [run_flow.rs](src/run_flow.rs). | Authoritative `runner_subprocess.pid`, carried disposition record, its raw supporting facts and reply steps, after the response-version gate. No capture inputs. |
| Entire `data.sandbox_log_capture`, including `window`, `observer`, `observed_deny`, `deny_events`, `step_denies` and transport diagnostics | Logs: `collect_log_evidence` attaches capture or launch-failure diagnostics; [sandbox_log.rs](src/sandbox_log.rs) constructs the window and parses observer output; `finish_sandbox_log_capture` replaces candidate associations. | [sandbox-log-observer.rs](src/bin/sandbox-log-observer.rs) supplies observer/query output and parsed events. Matching uses authoritative worker identity and submitted attempt operation/path evidence. `step_denies` references candidate step IDs; it is never written inside runner steps or comparisons. |
| Diagnostics `correlation_status`, `permission_failures_without_record` | Logs: `log_diagnostics` in [run_flow.rs](src/run_flow.rs). | Capture status, retained events, authoritative worker PID and candidate associations; the missing-record list also reads the runner's per-step `comparison.observation`. |

`complete_execution` constructs a `CompletedExecution` value before
`attach_sandbox_logs` invokes the collector. `collect_log_evidence` returns only
`LogEvidence`: the capture subtree and the two log-owned diagnostics. Separate
execution and log structs flatten into the existing JSON objects when attached;
neither the field paths nor their meanings change. Pre-run augment rejection
retains null capture and diagnostics without invoking collection.

Only a `captured` report with an event array and an authoritative worker PID can
reach `pid_match` or `no_match`. Failed reports may retain matching events as
diagnostics, but cannot supply `step_denies` or
`permission_failures_without_record`. Disabled capture reports a null capture
and `not_attempted`; absent worker identity reports `not_attempted`;
unavailable capture reports its failure status and `unavailable`. A successful
empty event array remains `captured` / `no_match`. Without an authoritative PID,
even supplied matching events cannot gain associations.

`permission_failures_without_record` is null unless correlation reaches
`pid_match` or `no_match` and per-step comparisons are present. When available,
it lists exactly the permission-shaped steps without captured candidates, or
`[]` when none qualify. It makes no claim about what the OS log store contains,
why a record is absent, or whether a sandbox caused the attempted failure.

The permanent Rust control
`collector_states_preserve_the_serialized_execution_half` runs the production
completion/attachment/serialization path with eventful, empty and unrelated
successful captures, every supported collection failure status, and disabled
capture. It compares execution bytes after removing only the log-owned fields
and the envelope generation timestamp, checks CLI status and correlation, and
retains diagnostic events on failed captures. Disposition, withheld-comparison
and absent-worker cases are included. The window
replay control also sends serialized production output through the independent
Python consumer. These controls run in the default `unit/rust.unit` case.

### In-repository consumer audit

The audit covers readers in this checkout, including test-only producers and
their stored fixtures. Consumers outside this checkout were not audited.

| Reader or fixture | Use of the two channels |
| --- | --- |
| [consumer.py](../tests/lib/consumer.py): `validate`, `steps`, `select`, `lifecycle`, `denials` | Gates an envelope on the exact envelope and response versions, validates every step's record against its raw channel fields, and selects steps by field. `denials` copies capture, window, diagnostics and resolved candidate references into a separate answer; log fields never change step validation or selection. |
| [lifecycle_adapter.py](../tests/lib/lifecycle_adapter.py), [lifecycle_contract.py](../tests/lib/lifecycle_contract.py), [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py) | The adapter selects only the execution diagnostic keys enumerated by `DIAGNOSTICS_KEYS`. Contract projections and oracle checks use worker records/raw facts and those execution projections. Constructed oracle envelopes supply disabled log fields; log evidence does not decide a lifecycle claim. |
| [blackbox.py](../tests/lib/blackbox.py), [validate_run.py](../tests/suites/blackbox_e2e/validate_run.py) | Validate runner shape and native steps through `consumer.validate`; expectations read runner step fields, not the optional log channel. |
| [checker_controls.py](../tests/suites/blackbox_e2e/checker_controls.py) | Constructs log captures to verify consumer retention, candidate provenance and distinct availability states. Separately checks comparison records and the shape allowlists: an unknown key at a recorded path and a present key of another type are rejected under the envelope golden and under the reply golden (`tests/fixtures/contract/`). |
| [disposition_controls.py](../tests/suites/blackbox_e2e/disposition_controls.py), [disposition fixtures](../tests/fixtures/disposition/) | Validate execution projections, including rejection of a replaced termination cause. `response14/a1_expected.json` and the preserved `a1_known_loss.json` carry disabled capture; neither supplies log evidence for the worker cause. |
| [check_termination_correlation.py](../tests/suites/witness_contract/check_termination_correlation.py) | Checks native denied writes and self-signal/clean-exit disposition independently; then checks capture state, window, candidates and missing-record diagnostics. |
| [check_deny_capture_window.py](../tests/suites/witness_contract/check_deny_capture_window.py) | Checks native execution, timestamps, padded/mirrored bounds and collection facts. Completed-query records and candidate references are checked conditionally; early/late availability is diagnostic, and independent queries need not return the same records. |
| [check_max_target_reply.py](../tests/suites/witness_contract/check_max_target_reply.py) | Separately checks runner-reply retention and optional observer transport retention. No log-derived native outcome. |
| [log_capture_contract.py](../tests/lib/log_capture_contract.py), [log_capture_controls.py](../tests/suites/witness_contract/log_capture_controls.py) | Shared live acceptance gate and independent supplied observations. Require complete collection or evidenced budget exhaustion with confirmed cleanup; reject unsupported availability claims without changing native expectations. |
| [check_pre_apply_failure.py](../tests/suites/witness_contract/check_pre_apply_failure.py), [check_attempt_in_flight.py](../tests/suites/witness_contract/check_attempt_in_flight.py) | Read execution disposition/cause; pre-apply checks also require disabled capture. Neither uses a deny event to assign worker termination. |
| Rust controls in [run_flow.rs](src/run_flow.rs), [log_replay_tests.rs](src/log_replay_tests.rs), [sandbox_log.rs](src/sandbox_log.rs), [runner_client.rs](src/runner_client.rs), and [observer.py](../tests/fixtures/deny_capture/observer.py) | Exercise projection, status gating, matching, transport retention and window propagation; supplied text crosses the production parser and assembly, while the observer fixture supplies independently timed records. Production log-to-execution writes are excluded by the assembly boundary above. |

### Runner selection (external entitlements)

`run` can target specific runner modes by adding one of the following to the request:

- `runner: { mode, id, service, required_entitlements }` (preferred)
- Top-level fields `runner_id`, `runner_service`, `required_entitlements` and `runner_mode` (accepted beside the `runner` object; the object takes precedence)

Selector objects reject unknown keys and wrong types. Every entitlement entry
must be a string; malformed entries are never dropped. Non-null nested values
take precedence per field, including an empty `required_entitlements` list;
null means absent. Even shadowed aliases are validated. The controller consumes
these fields before XPC delivery; they are not runner-executed request options.

If `required_entitlements` is present, the controller enforces a **superset**
check against the runner’s recorded entitlements before dispatch.

The only built-in mode is `standard` (default). If `runner.mode` is
present and an external runner is selected, it must equal `byoxpc` —
the only supported external runner kind.

### `runner` (external runner manager)

These commands manage external runners signed with user entitlements:

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

Install saves a `pending` registry record before creating the launchd plist.
After bootstrap succeeds (or plist creation with `--skip-bootstrap`), it saves
`installed`. The install envelope includes `data.state` and a separate `loaded`
observation; installation state never substitutes for observed service presence.
Errors after the pending save identify its recovery record on stderr.
The registry lives under `~/Library/Application Support/PolicyWitness/runners.json`;
`PW_RUNNER_REGISTRY` selects an alternate file.

Notes:
- BYOXPC is the only external runner kind. The bundle must be an XPC service
  directory (`CFBundlePackageType=XPC!`); the Mach service name equals the
  bundle's `CFBundleIdentifier`. The executable is derived from
  `<bundle>/Contents/MacOS/<CFBundleExecutable>`.
- `--entitlements` requires either `--identity <id>` or `--allow-adhoc`. Without one of those the supplied entitlements would not be embedded into the binary, so the call is rejected up front.
- A BYOXPC runner copied from the shipped `PWRunner.xpc` inherits its signed-caller check (`PWRunnerRequireSignedCaller`): sign it with a Developer ID whose Team ID matches the caller (`--identity`), or remove those Info.plist keys for an ad-hoc/local runner. An ad-hoc runner that keeps the keys has no Team ID and is rejected at connect time (`xpc_error`). See docs/PolicyWitness.md → "Caller authentication and ad-hoc signing".
- `runner verify` delivers its fixed allow-all verification request on the client's stdin, as a run does; no temporary request file is written. It defaults to a 5-second timeout (override with `--timeout-ms`).
- `runner remove` first atomically moves ownership into `pending_cleanup`. Launchd/plist failures appear in `data.warnings`; `cleanup_retained: true` and `retained_record` identify recovery state. The record is retired only after service and plist absence are verified and retirement is saved; after a bootout it issued, remove re-reads the service every 50 ms for up to 1 s of launchd teardown before judging presence, and the cleanup observation records the reads and the wait. `--skip-bootout` retains recovery while the service is present or unknown.
- `runner status`, `runner verify`, and `runner remove` emit an envelope with the operation's `kind` and `result.normalized_outcome = "not_found"` (exit code 2) when the lookup key is not in the registry, instead of plain-text stderr.
- `runner validate` re-reads each registry entry's on-disk signature and entitlements. It does not reconcile against launchctl or `LaunchAgents/`.

### Registry ownership and recovery

Schema 1 accepts additive fields: `RunnerRecord.state` defaults to `installed`
for older records, `ownership` is optional, and `pending_cleanup` defaults to an
empty collection. Ownership records keep absolute bundle/executable/plist paths,
launchd domain, installer UID and the expected plist hash. Cleanup records retain
that identity plus before/after observations, so recovery does not depend on test
output. Installation checks service, bundle and executable identities against
both collections; conflicts direct callers to `runner remove --service-name`.

Install, remove and validate hold an OS advisory lock beside the selected
registry across the read/modify/write sequence and launchd actions. Competing
modifiers fail with a registry-busy diagnostic. The stable `.lock` file remains
in place; never unlink it while held. Updates write a new temporary file and
atomically rename it, so unlocked list/status/verify/reconcile readers see a
complete old or new registry. Rust 1.89 or newer provides the file lock API.

List exposes both collections. Status and verify report pending installation
state; specimen selection rejects it with `external runner is pending
installation`. Remove accepts either collection through its existing selectors,
including pending installations. It rechecks service executable and plist
ownership before acting. Unknown inspection results preserve recovery; a
permission error is never interpreted as service absence.

`runner reconcile` is report-only. It reports recorded state, observed service
and plist presence, and separate ownership classifications (`owned`, `unowned`,
`ambiguous`, or `unknown` when inspection fails). It scans user LaunchAgents and
readable system LaunchDaemons for `com.policywitness.*` labels or `PWRunner`
executables missing from both collections. A prefix identifies a reporting
candidate; it does not authorize cleanup. Reconcile creates no registry or lock
file and performs no machine changes.

## Why the Rust launcher still shells out

The launcher does not speak NSXPC directly. It drives the Swift client helper embedded in the app bundle:

- `dist/PolicyWitness.app/Contents/MacOS/pw-runner-client`

The Swift client is responsible for `NSXPCConnection` wiring; the Rust launcher owns run orchestration and evidence capture.


`steps[].sandbox_check.pid` is the spawned worker PID, or explicit null when no
worker exists. It never substitutes the host PID. Typed readers must accept
null. Request schema and worker ABI are separate contracts.

The query channel's `native_rc` is authoritative for native returns. A received
diagnostic without a native return retains `result_source="validator"`,
`native_rc=null` and `rc=-1`; this is not a synthetic validator record or a
claimed native failure. Missing replies use synthetic `rc=0`, `outcome="error"`
with a missing reason. `outcome="error"` alone does not identify a native call
failure. The attempt channel carries PolicyWitness attempt status in `rc` and
operation-specific error observations in `errno` and `error`.

See [the query and receiver contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#query-and-receiver-evidence)
for immutable query planning, query association, independent pipe collection,
and exact-byte controller capture semantics.
