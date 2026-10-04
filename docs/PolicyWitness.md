# PolicyWitness User Guide

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

PolicyWitness runs sandbox specimens and prints a single JSON envelope to stdout. Each specimen is an SBPL policy plus a probe plan. For shorter answers to common questions see [Questions](#questions).

Reading paths: try it via [Quick start](#quick-start), write a specimen via [Specimen format](#specimen-format), or interpret output via [Output envelope](#output-envelope).

## Contents

- [Quick start](#quick-start)
- [Questions](#questions)
- [Specimen format](#specimen-format)
- [Limits](#limits)
- [Output envelope](#output-envelope)
- [What PolicyWitness understands](#what-policywitness-understands)
- [Operating](#operating)
- [External runners (BYOXPC)](#external-runners-byoxpc)

## Quick start

Quick start uses the built-in standard runner. If you need entitlements the standard runner doesn't ship — debug-attach, DYLD env, custom dylib loading, JIT — see [External runners (BYOXPC)](#external-runners-byoxpc) below.

Set a convenience variable, adjusting the path to wherever `PolicyWitness.app` is installed:

```sh
PW="/Applications/PolicyWitness.app/Contents/MacOS/policy-witness"
```

Create a specimen:

```sh
cat > /tmp/pw_specimen_file_read_deny.json <<'JSON'
{
  "schema_version": 4,
  "specimen_id": "file_read_deny",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default) (deny file-read-data)"
  },
  "probe_plan": [
    {
      "step_id": "fr1",
      "sandbox_check": {
        "operation": "file-read-data",
        "filter": { "kind": "path", "value": "/etc/hosts" }
      },
      "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" }
    }
  ]
}
JSON
```

Run it:

```sh
$PW run /tmp/pw_specimen_file_read_deny.json > /tmp/pw_result.json
```

For an experiment that checks a file effect and then deliberately triggers a
request refusal, see [Try an accepted request and a refusal](#try-an-accepted-request-and-a-refusal).

## Questions

<!-- BEGIN COPIED QUESTIONS -->

### When should I use PolicyWitness?

Use PolicyWitness when you need to determine whether an observed result follows from the sandbox policy under test or from some unrelated part of the execution environment.

### Who needs to use PolicyWitness?

Almost no one. Folks authoring SBPL profiles can call `sandbox_check` and `sandbox-exec` directly and Apple's entitlements model plus their app's actual runtime behavior cover practical sandbox questions. A small wrapper script around `sandbox_check` plus `sandbox-exec` can obtain a prediction and an attempt result in the common case. 

### Can PolicyWitness attribute a failed attempt to sandbox denial?

No. PolicyWitness records the failed attempt and the evidence available around it, but a failure alone does not establish that the sandbox caused it.

### What does PolicyWitness's attempt channel record?

The sandboxed worker supports four built-in attempt kinds: `file` (open/read/write/create/unlink/access), `mach_lookup` (`bootstrap_look_up`), `sysctl` (`sysctlbyname` read), and `exec` (`posix_spawn`). Completed results carry operation-specific status and error observations in a uniform per-step envelope; those status fields are PolicyWitness attempt status, not raw syscall returns. Result provenance and missing reasons distinguish completed observations from missing or incomplete reports.

### Can PolicyWitness probe operations it doesn't natively support?

Yes — via the `exec` attempt kind plus the named-augment interface. Callers ship their own helper binary and, where needed, opt into `exec_baseline`, a shipped SBPL fragment supplying baseline allows for spawning under `(deny default)`. PolicyWitness records spawn observations, child disposition and bounded stdout/stderr in the same envelope shape as the built-in attempt kinds. The helper must supply evidence about its internal operation; PW does not turn that evidence into a record for that operation, and a successful spawn can coexist with a failed exec result. The per-operation authoring burden lives with the caller — PolicyWitness intentionally doesn't carry an atlas of every sandboxable operation, and the augment system is the documented extension point for callers who need to test surfaces (network, iokit, ipc, signals, user_preference, etc.) PolicyWitness has no built-in attempt kind for.

### What does a comparison record contain?

Each step's `comparison` has six fields: what the attempt channel observed (`observation`: `succeeded`, `permission_failure`, `other_failure` or `unavailable`) and the raw fields that observation rests on (`observation_basis`); whether the query named the same operation as the attempt (`operation_relation`) and the same submitted target (`target_relation`); whether an eligible query is known to precede the attempt batch (`order`); and a short list of `limitations` that name a planning exclusion or the attempt's lifecycle state. The query's own answer stays in `sandbox_check`. See the guide's [reading rules](#reading-a-comparison-record).

### Does PolicyWitness decide whether `sandbox_check` and enforcement disagree?

No. The envelope carries no evidence that a target's state was stable between the query and the attempt, or that a path named the same object both times, and a permission-shaped failure does not identify the sandbox as its cause. A deny prediction beside a successful attempt is therefore reported as those two facts with their relations and order, and nothing more. Readers who want an opinion form it from the record and the raw channels, under limits the record states.

### Can PolicyWitness run every profile that `libsandbox` accepts?

No. PolicyWitness has its own limits, documented in [the limits inventory](#limits).

### What versions of SBPL are supported?

PolicyWitness passes the submitted SBPL source to the host's `libsandbox` compiler and supports whatever profile versions that compiler accepts. `(version 1)` is the documented profile version; some Apple-shipped profiles use higher version numbers.

### How do I use imports with PolicyWitness?

PolicyWitness supports imports the same way `sandbox-exec` does — `(import "name.sb")` statements are resolved by libsandbox against the system search path (`/System/Library/Sandbox/Profiles/` first, then `/usr/share/sandbox/`).

### Can PolicyWitness test sandbox-extension behavior?

No. PolicyWitness does not issue, consume, release, or otherwise track sandbox extensions, and it does not model changes in access caused by extension state. Policies containing extension predicates may compile and run, but PolicyWitness does not provide first-class probes or comparison semantics for extension lifecycle behavior.

### Which happens first, the prediction or the attempt?

A `query_first` comparison identifies an eligible native prediction collected before the worker acknowledged host release, which precedes every attempt. Missing or unusable predictions and death before acknowledgement remain `unestablished`. Query collection closes even when validator cleanup is unconfirmed; a surviving validator cannot add later records. The interval is not a common state snapshot, and earlier attempts can change what later attempts encounter.

### How do I read the denial log?

As optional, possibly incomplete evidence. The kernel's sandbox log intermittently omits denial lines for any sandboxed process, so a missing record never establishes that an operation was allowed. The validator queries `sandbox_check` with `SANDBOX_CHECK_NO_REPORT`, so a denial record naming the worker PID comes from an attempt, never from a prediction. A candidate association (`sandbox_log_capture.step_denies`) says that a record's PID, operation and path match a submitted attempt; it does not say the attempt produced that record, and it changes no comparison field.

### How long does a run take?

One runner client span plus, by default, one unified-log scan, plus the controller's own startup and output. Your reply records the first two: the runner's work is `data.runner_client.ended_at_unix_ms` minus `started_at_unix_ms`, and the scan is `data.sandbox_log_capture.supervision.elapsed_ms`.

### Can I evaluate specimens in parallel?

Yes and no. Each specimen is evaluated in its own runner and worker processes, but PolicyWitness does not guarantee relative scheduling between concurrent runs or complete denial-log evidence. If an experiment depends on timing or log availability, run the specimens separately. N.B. Runs through one installed [external runner](#external-runners-byoxpc) queue behind launchd's respawn throttle.

<!-- END COPIED QUESTIONS -->

## Specimen format

### Top-level shape

Top-level fields:

- `schema_version`: integer-valued number equal to the current request schema
- `specimen_id`: string
- `run_kind`: string (optional)
- `policy`: object
- `probe_plan`: array of steps
- `runner`: object (optional; select runner mode and external runners)

Minimal skeleton (copy/paste):

```json
{
  "schema_version": 4,
  "specimen_id": "skeleton",
  "runner": { "mode": "standard" },
  "policy": { "format": "sbpl", "sbpl_source": "(version 1) (allow default)" },
  "probe_plan": []
}
```
Notes:
- The [accepted input contract](CONTRACT.md#accepted-input-contract) rejects
  unsupported request versions, unknown fields and wrong types explicitly.
  Optional nulls mean absence; parameter names inside `policy.params` remain
  caller-defined. Runtime capacity limits are checked separately.
- All path rules live inside `policy.sbpl_source`; there is no `path_membership` field.
- `probe_plan` may be empty when you only want to exercise sandbox
  apply (the validator child is only spawned when there are probes
  to query).

### Try an accepted request and a refusal

This specimen asks a sandbox query and attempts to create an empty file. Use a
fresh directory so you can observe whether the file was created. Adjust `PW`
to your installed app; the commands need no repository files or extra tools.

```sh
PW="/Applications/PolicyWitness.app/Contents/MacOS/policy-witness"
PW_EXAMPLE_DIR=$(mktemp -d /private/tmp/pw-input.XXXXXX)
cat > "$PW_EXAMPLE_DIR/request.json" <<JSON
{
  "schema_version": 4,
  "specimen_id": "request-grammar",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default)"
  },
  "probe_plan": [
    {
      "step_id": "create",
      "sandbox_check": {
        "operation": "file-write-create",
        "filter": { "kind": "path", "value": "$PW_EXAMPLE_DIR/created" }
      },
      "attempt": { "kind": "file", "action": "create", "target": "$PW_EXAMPLE_DIR/created" }
    }
  ]
}
JSON
"$PW" run "$PW_EXAMPLE_DIR/request.json" --no-log-capture > "$PW_EXAMPLE_DIR/run.json"
test -f "$PW_EXAMPLE_DIR/created"
```

The run should exit 0, and `test -f` should succeed. The newly created file is
an observation outside the JSON reply. A query answer alone cannot establish
that effect. In particular, a query about an absent path can report
`prediction_unavailable` while the creation attempt succeeds.

Now make a copy with a new target and the deliberately misspelled field
`capture_applied_profiel`. The new target lets you check that refusal prevents
an otherwise valid create from running:

```sh
sed -e 's|/created"|/refused"|g' \
    -e 's|"format": "sbpl",|"format": "sbpl", "capture_applied_profiel": true,|' \
    "$PW_EXAMPLE_DIR/request.json" > "$PW_EXAMPLE_DIR/typo.json"
PW_REFUSAL_RC=0
"$PW" run "$PW_EXAMPLE_DIR/typo.json" --no-log-capture > "$PW_EXAMPLE_DIR/refusal.json" || PW_REFUSAL_RC=$?
test "$PW_REFUSAL_RC" -eq 1
test ! -e "$PW_EXAMPLE_DIR/refused"
```

Both `test` commands should succeed: PW exited 1 and the file is absent.
In `refusal.json`, `result.normalized_outcome` is `bad_request`, and
`data.request_failure` contains:

```json
{
  "code": "unknown_field",
  "path": ["policy", "capture_applied_profiel"]
}
```

No worker or validator is created for this refusal; the XPC host may have
launched to inspect the request. Keep the directory to inspect the submitted
requests and both envelopes. Removing the misspelled field restores the
original instruction. Enabling capture instead requires both the correctly
spelled field and its [nonce](#compiled-object-receipt-opt-in).

### What acceptance establishes

An accepted-input grammar describes which input shapes are allowed. PW also
checks their meaning and the build's capacity. Execution supplies a separate
observation:

| Distinction | Example | What it tells you |
| --- | --- | --- |
| Syntax and structure | Broken JSON, an unknown field, or a string where `args` requires an array of strings. | Correct the request's spelling or shape. Optional nulls mean absence; names inside `policy.params` are caller data, but their values must be strings. |
| Meaning | `args: []` on a file attempt, or duplicate step IDs. | The fields decode, but the submitted instruction is invalid. Correct their relationship or choose a supported operation. |
| Capacity | A plan contains more steps than this build admits. | Inspect `admission_failure` for the field, actual count and maximum, and find the field in the Specimen admission table under [Limits](#limits). Revise the experiment or use a build with sufficient capacity; PW never truncates the plan. |
| Observed effects | A valid create encounters a permission failure, or succeeds and produces a file. | Read the attempt evidence and inspect the target. Acceptance establishes neither an allowed operation nor its effect. |

Unknown attempt combinations and filter names refuse the whole specimen before
worker or validator creation. Recognized queries with unavailable predictions
still permit supported attempts. A request can therefore be useful even when
the query channel cannot answer. For capacities and units, see [Limits](#limits).

### Correcting a refused request

Use `data.request_failure.code` to classify the refusal and `path` to locate
the field. Human-readable `result.error` supplies context; programs should not
parse that prose. Path components are exact keys and decimal array positions:
`["probe_plan", "1", "attempt", "args"]` identifies the second step's arguments.
`[]` names the root; `null` means the location was withheld. An absent
`request_failure` does not establish success. Capacity refusals also retain
counts and positions in `data.runner_result.admission_failure`.

Three field relationships commonly matter:

| Field | When it applies |
| --- | --- |
| `attempt.args` | A non-null array, including `[]`, is accepted only for `exec/spawn`. |
| `sandbox_check.filter.value` | `none` accepts only absence or null. Other recognized kinds require a nonempty string. |
| `policy.capture_nonce` | Requires `capture_applied_profile: true`; enabled capture requires a fresh nonce of 32 lowercase hexadecimal characters. |

A refusal identifies one problem. Correct it and rerun; another problem may
then be reported. `bad_request` exits 1 and executes no probe steps. Missing or
unreadable files and unavailable runners are separate failures; correcting a
request's grammar cannot make an unavailable runner launch.

The request's `schema_version` names its accepted shapes and meanings. It is
separate from `(version 1)` in the SBPL source and from the app's build number.
Removing a field, requiring a new one, or changing an action's meaning requires
a revised contract and corresponding request changes. Review those changes
before replacing an unsupported marker with the current one.

An implementation correction that honors the documented instruction can keep
the marker and the same request, even when observations change. Additions can
also preserve the marker: existing requests remain valid, while older builds
can refuse newly added fields or actions. Equal markers do not promise equal
capacity or identical observations across builds and macOS versions.

### Policy

SBPL source:

```json
"policy": {
  "format": "sbpl",
  "sbpl_source": "(version 1) (allow default) (deny file-read-data)",
  "params": { "DENY_DIR": "/tmp/deny" }
}
```

`(import "...")` statements compile transparently — `sandbox_compile_string`
resolves them against the system profile search path. `(param "NAME")`
substitution uses values from `policy.params`. `string-append` of param
references is supported by the compiler.

### Compiled-object receipt (opt-in)

An SBPL policy may set `capture_applied_profile: true` and a fresh per-application
`capture_nonce` (32 lowercase hexadecimal characters). The runner adds
`data.runner_result.applied_profile`, with its own `schema_version: 1`. A
`status: "captured"` receipt contains `worker_pid`, `request_nonce`, `profile_type`,
`bytecode_length`, `bytecode_b64`, `bytecode_sha256`, `source_length`,
`source_sha256`, `parameter_count` and `params_sha256`. These are sensitive outputs:
the caller must arrange restricted receipt storage before opting in.
A non-null nonce without enabled capture is a `bad_request`.

The C worker copies the bytecode from the same compiler-result pointer it passes
to `sandbox_apply`, before applying. The host requires successful apply,
complete worker exit, matching PID/nonce, lengths, input identities and payload
checksum before publication. Missing capture, failed apply, worker death or
capture corruption is unavailable; no expected digest is accepted as an output.
An unavailable nested receipt has a reason and no bytecode, or is absent if no
worker result was obtained. Capture identifies the supplied compiled object, not
kernel readback.

Source identity hashes the UTF-8 C string consumed by compilation. Parameter
identity is SHA-256 of the little-endian 32-bit pair count followed by sorted
32-byte pair digests. Each pair digest hashes LE32 key-byte count, key UTF-8 bytes,
LE32 value-byte count, then value UTF-8 bytes. The worker hashes its private copy
of the strings passed to `sandbox_set_param`; the host independently recomputes
the identity. Pair ordering is irrelevant, consumed values are not. Embedded NUL
inputs cannot qualify as matching complete requested inputs. Consumers must join
the nonce and worker identity to their own request and compare actual decoded
bytecode with any independently retained expected object. A source hash alone
does not establish that equality.

### SBPL check (`sbpl-check`)

`sbpl-check` is a host-side SBPL compiler. The C worker exercises the
policy itself; its worker failure record identifies the failed operation and
available native result, summarized as `runner_failed`. The controller runs
`sbpl-check` only after `xpc_error`, retaining its independent result under
`data.policy_check`. That fallback says nothing about how far a missing worker
progressed or why its reply was lost. You can also run the tool directly for the
diagnostics below.

The verdict is the native compiler's. The helper does not scan the source for
`(param "...")` references and reports no missing or unused names: a parameter
the source needs and the request does not supply is whatever libsandbox makes
of it, usually a compile error whose diagnostic the helper copies unchanged.
Supplied `policy.params` entries reach the compiler through
`sandbox_set_param`.

The helper works in a fixed order: decode the request; validate the format,
the presence of `sbpl_source`, the source byte cap (`helper_source` under
[Limits](#limits)) and the absence of NUL in the source and in every parameter
key and value; inventory the literal import closure; set up parameters and
compile; state the verdict. An input refusal performs no import walk and no
libsandbox call.

| Condition | `result.normalized_outcome` | Exit / `result.ok` | `data.compile` |
| --- | --- | --- | --- |
| Unsupported `policy.format`, missing `sbpl_source`, or NUL in the source or in a parameter key or value | `bad_request` | 1 / false | null |
| Source over the byte cap | `policy_too_large` | 1 / false | null |
| `sandbox_create_params` returned NULL | `setup_error` | 1 / false | stage `params_create`, `ok: false` |
| `sandbox_set_param` returned nonzero | `setup_error` | 1 / false | stage `param_set`, `ok: false` |
| The compiler returned an error buffer, or no profile | `compile_error` | 1 / false | stage `compile`, `ok: false` |
| The compiler returned a profile and no error buffer | `ok` | 0 / true | stage `compile`, `ok: true` |

`data.compile` is null on an input refusal and otherwise `{stage, ok, error}`:
the last native stage attempted, not a history of calls. An absent or empty
`policy.params` map makes no setup call, so the record goes straight to
`compile`. Read `compile.error` beside `result.error`:

- An input refusal puts the helper's validation text in `result.error`;
  `data.compile` is null.
- A setup failure puts the helper's text naming the failed call in both
  fields. A failed `sandbox_set_param` names the parameter and its return
  code; the value is never echoed.
- A compiler error buffer is copied unchanged into both fields: no prefix,
  trimming or hint. An empty native string stays an empty string, distinct
  from null.
- A NULL profile without an error buffer is a completed compiler call with no
  diagnostic: `compile.error` is null and `result.error` is the helper summary
  `sandbox_compile_string returned NULL without a diagnostic`.
- A profile returned beside an error buffer remains a failure with the native
  text. On success both fields are null.

A diagnostic in `compile.error` does not by itself show that a missing
parameter caused the failure; read its text. For example, without a supplied
`OPTIONAL` parameter, `(version 1) (allow default) (define unused (param
"OPTIONAL"))` compiles and the helper reports `ok`, while `(allow file-read*
(subpath (param "ROOT")))` without `ROOT` fails with the compiler's own type
diagnostic.

Invalid arguments, an unreadable request path and malformed request JSON exit 2
with a message on stderr and no JSON envelope.

The remaining `data` fields are input and host facts:

- `policy_format`: the request's `policy.format`.
- `policy_sha256`: sha256 of `policy.sbpl_source` only; null on an input
  refusal.
- `params_present`: whether the request carried a `policy.params` map at
  all. An empty map is present; a missing or null map is not.
- `params_count`: the number of entries in that map, counted even when the
  check refuses the input.
- `macos_build_version`: the `kern.osversion` sysctl of the host that ran
  `sbpl-check`. Import contents change between OS builds; this lets a
  downstream auditor decide whether a closure hash is verifiable on their
  machine.

In the controller's fallback capture, `data.policy_check.status` is either a
transport status or the helper's `normalized_outcome` copied exactly from a
supported envelope (the helper kind, the current controller envelope version
and a nonempty outcome string). The transport statuses, in precedence order,
are `unavailable` (the helper could not be launched or the request was not
delivered), `capture_error` (truncated stdout, never parsed), `parse_error`
(untruncated stdout that is not UTF-8 JSON), `tool_error` (no parsed output)
and `invalid_reply` (parsed output that is not a supported helper envelope,
retained unchanged). The capture carries the helper envelope whole under
`data.policy_check.envelope` and derives no second verdict from the compile
record, `result.ok` or the process exit, which `tool_exit_code` records
independently.

In the run flow, a policy that fails to compile reaches the C
worker and surfaces as `runner_failed` with an operation=5 compilation record,
NULL-result evidence and any published compiler diagnostic. Parameter setup
and application failures have their own operation/result records.
In a run, a missing `sbpl_source` or non-`sbpl` `format` is a structured
`bad_request` before children. The controller runs `sbpl-check` only on the
`xpc_error` path.

The sbpl-check envelope also records the imports closure under
`data.import_inventory`: null on an input refusal, otherwise present even when
setup or compilation fails. Resolution errors, truncation and cycles stay in
the inventory; they never veto or replace native compilation.

- `records`: each entry is `{name, resolved_path, sha256, size_bytes,
  mtime_unix, error}`. The resolver walks `(import "...")` statements
  recursively, trying
  `/System/Library/Sandbox/Profiles/<name>` first and then
  `/usr/share/sandbox/<name>`. Names must include the `.sb` extension;
  libsandbox does not auto-append. Absolute paths starting with `/` are
  accepted as-is. A performed walk over a source with no imports is an empty
  list, distinct from the null of a refusal.
- `truncated`: true when either the count cap or the
  depth cap was hit during resolution. Records still include the
  partial result up to the cap.
- `cycle`: when a back-edge to an in-progress import is detected
  during resolution, the chain of import names that closed the cycle,
  `[outer, ..., inner, repeated_name]`. Null when no cycle is present. The
  field is single-valued: only the first cycle observed in a given walk is
  reported. (Diamond imports, the same file reached via two distinct paths
  with no cycle, are deduplicated silently and do not populate this field.)
- `policy_closure_sha256`: sha256 of the source plus the sorted
  `resolved_path + " " + sha256` of every successfully resolved import.
  This hash is reproducible iff every resolved file is content-identical
  on the verifying host. Unresolved imports are excluded; check
  `records[].error` to see which ones failed.

### Augments

`policy.augments` is an optional array of named SBPL fragments shipped
inside the signed app bundle under
`Contents/Resources/Augments/<name>.sb`. The controller resolves each
name **before the runner runs**, appends the augment's contents to
`policy.sbpl_source`, computes both the original-source and
applied-source sha256, and strips the `augments` field from the
request forwarded to the runner. The runner therefore compiles the
spliced bytes (as does `sbpl-check` if the `xpc_error` path runs
it), and the runner has no augment-aware code path.

```json
"policy": {
  "format": "sbpl",
  "sbpl_source": "(version 1)\n(deny default)\n",
  "augments": ["exec_baseline"]
}
```

Resolution rules:

- Augment names must match `^[A-Za-z0-9_]+$`. Anything else (including
  `..`, path separators, or empty strings) is rejected with
  `normalized_outcome = "bad_request"` before the runner is invoked.
- A name that doesn't resolve to
  `<app>/Contents/Resources/Augments/<name>.sb` is rejected with
  `bad_request` and `error = "unknown augment '<name>'"`.
- The `augments` field being absent, `null`, or `[]` is treated as
  "no augments." In the empty/null cases the field is still stripped
  from the request before forwarding so the runner sees no
  augment-aware shape.

Splicing semantics:

- Augments are **append-only and allow-only.** Each shipped augment
  contains only `(allow ...)` rules; the author commits not to emit
  `(deny ...)`.
- SBPL is last-match-wins, so an augment's `(allow process-exec)`
  overrides a caller's earlier `(deny process-exec)` for the
  operations the augment covers. A caller opting into an augment
  consents to this override; the controller does not warn about
  overlap.

Envelope reporting:

- `data.specimen.policy.augmentation` is present on every run envelope.
  Shape after a successful splice:

  ```json
  "augmentation": {
    "status": "applied",
    "applied": ["exec_baseline"],
    "original_sha256": "<sha256 of policy.sbpl_source as submitted>",
    "applied_sha256":  "<sha256 of source after augments appended>",
    "error": null
  }
  ```

  `status` is `not_requested` (no augments; both hashes name the same
  submitted source), `applied`, `failed` (resolution refused; `applied` is
  empty, `applied_sha256` is null and `error` carries the diagnostic) or
  `not_applicable` (no string source to hash). `data.runner_result.policy_sha256`
  (the hash the runner computed over the bytes it actually compiled)
  equals `applied_sha256` on a completed run. A consumer that wants "what the
  caller submitted" reads `original_sha256` instead. See
  [The specimen dossier](#the-specimen-dossier).

Shipped augments:

- **`exec_baseline`** — three `(allow ...)` rules that let a
  libSystem-dynamic helper `posix_spawn` under `(deny default)`:
  `(allow process-exec*)`, `(allow process-fork)`, and an
  **unconditional** `(allow file-read*)`. Empirically derived
  with the project's exec helper fixture
  on macOS 14.8.3 (build 23J220, Darwin 23.6.0).

  **This is a pragmatic baseline, not a narrow minimum.**
  `(allow file-read*)` is unconditional because the kernel reads
  the target binary's bytes before exec and the augment can't
  predict the caller's chosen helper path. Because augments are
  appended after the caller's source and SBPL is last-match-wins,
  this allow overrides any caller-authored `(deny file-read* ...)`.
  Specimens that probe file-read denial cannot be composed with
  `exec_baseline`.

### Probe plan steps

Each step has:

- `step_id`
- `sandbox_check`: `{ operation, filter }`
- `attempt`: `{ kind, action, target }`

Step IDs, query strings, filter/attempt labels, attempt targets and the
top-level strings have separate admission limits (see [Limits](#limits)).
Valid Unicode and control characters survive JSON transport. Embedded NUL is
refused in native C-string fields; host-only metadata and labels may contain it.

Example:

```json
{
  "step_id": "read_etc_hosts",
  "sandbox_check": {
    "operation": "file-read-data",
    "filter": { "kind": "path", "value": "/etc/hosts" }
  },
  "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" }
}
```

## Limits

<!-- BEGIN COPIED LIMITS -->

A specimen that `libsandbox` would compile can still be refused here, or run
with less evidence than it produced. This section lists every such limit with
its value, what it counts and what happens at the boundary.

Capacity refusals carry `data.runner_result.admission_failure`, which names the
`field`, the `actual` count, the `maximum` and the `unit`, with location details
where available and `origin: "runner_host"`. Find that field in the "Refusal
names" column of the Specimen admission table; the row says what was measured
and which location fields are reported. To check a specimen before submitting
it, compare it with the same rows.

Request files must be UTF-8 JSON. A file containing invalid UTF-8 yields exit
code 2 and `result.normalized_outcome: "tool_error"`, with an error beginning
`failed to read request.json` and `data.runner_result: null`. It has no
`admission_failure` to look up.

### How to read the tables

- Capacities are inclusive maxima unless the row says otherwise: a 63-byte
  step ID fits, a 64-byte one exceeds its limit. UTF-8 counts measure decoded
  strings rather than JSON escapes or characters. Rows labeled `bytes` specify
  whether they count raw output, bytecode or a calculated allowance. String
  capacities exclude any terminating NUL.
- Time rows distinguish defaults, elapsed monotonic deadlines, nominal waits
  and unenforced allowances. Monotonic deadlines are unaffected by wall-clock
  adjustments. Nominal waits can take longer than their listed duration; each
  row describes what expiry does.
- The Control column describes `policy-witness` flags using four words.
  "Fixed" means no flag changes the value in this build. "Flag" names the flag
  that does. "Derived" means the value follows from another row.
  "Not enforced" means the number is informative.
- Specimen admission answers whether a specimen fits this build's capacities
  and why one did not. A capacity refusal names one field, has empty `steps`
  and carries no worker or validator subprocess record. PolicyWitness never
  truncates a plan to fit.
- Execution budgets describe waits and deadlines within a run. Some expiries
  lead to cleanup or missing results; the readiness hint can expire while the
  run continues. The nominal release margin has no expiry of its own.
- Queries and transport describe query sizes and received output. The rows
  identify rejected queries, truncated output and unavailable parsing or
  correlation. Truncated JSON is not parsed as a complete reply.
- Evidence capture bounds optional evidence: deny-log records, child output and
  compiled-object receipts. Excess can retain a prefix with a truncation marker
  or make capture or correlation unavailable, as the row describes. Attempt
  status and `sandbox_check` verdicts are unchanged by these evidence limits.
- Diagnostic helpers lists the limits of `sbpl-check`, which runs only after an
  XPC error, and of the log observer's streaming mode. Neither is the normal
  admission path, and the helper's import inventory does not control how
  `libsandbox` resolves or compiles imports.

<!-- BEGIN GENERATED LIMITS -->

### Specimen admission

| Limit | Value | Refusal names | Counting and consequence | Control |
| --- | --- | --- | --- | --- |
| Policy source (`policy_source`) | 262,143 UTF-8 bytes | `policy.sbpl_source` | Final SBPL source after augments. Imported file contents are not added to this count. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Probe steps (`probe_steps`) | 256 items | `probe_plan` | Entries in `probe_plan`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Policy parameters (`policy_parameters`) | 1,024 items | `policy.params` | Entries in `policy.params`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Step ID (`step_id`) | 63 UTF-8 bytes | `step_id`, with `step_index` | Each `step_id`. A refused ID is identified by `step_index` and is never echoed. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Attempt target (`attempt_target`) | 511 UTF-8 bytes | `target`, with `step_id` and `step_index` | Each attempt target (path, service or sysctl name). For exec, this is also argument zero. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Supplied exec arguments (`exec_arguments`) | 15 items | `args` with unit `items`, with `step_id` and `step_index` | Arguments supplied in `attempt.args`; the exec target is the additional argument zero. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Each supplied exec argument (`exec_argument`) | 127 UTF-8 bytes | `args` with unit `utf8_bytes`, with `index`, `step_id` and `step_index` | Each supplied exec argument; the target has its own larger limit. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Parameter key (`parameter_key`) | 127 UTF-8 bytes | `key` | Each parameter key. A refused key is identified by field and byte count and is never echoed. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Parameter value (`parameter_value`) | 383 UTF-8 bytes | `value`, with `parameter_key` | Each parameter value. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Query operation (`query_operation`) | 127 UTF-8 bytes | `sandbox_check.operation`, with `step_id` and `step_index` | Each `sandbox_check.operation`, also echoed per step in the reply. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Query filter value (`query_filter_value`) | 511 UTF-8 bytes | `sandbox_check.filter.value`, with `step_id` and `step_index` | Each `sandbox_check.filter.value` when present, including for `none` and unrecognized filter kinds. The query value and attempt target are counted separately, even when they name different paths. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Probe filter and attempt labels (`probe_plan_label`) | 127 UTF-8 bytes | `sandbox_check.filter.kind`, `attempt.kind` or `attempt.action`, with `step_id` and `step_index` | Each `sandbox_check.filter.kind`, `attempt.kind` and `attempt.action`. Unknown labels within the capacity still receive a meaning refusal. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Specimen ID (`specimen_id`) | 255 UTF-8 bytes | `specimen_id` | The `specimen_id` string. Echoed once per reply; a refused ID is replaced by `<admission_refused>`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Request labels (`request_label`) | 63 UTF-8 bytes | `run_kind` or `policy.format` | Each of `run_kind` and `policy.format`. A refused `run_kind` is omitted and a refused format reads `unknown`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Test-seam executable paths (`test_override_path`) | 1,023 UTF-8 bytes | `_test_overrides.worker_executable_path` or `_test_overrides.validator_executable_path` | Each of `_test_overrides.worker_executable_path` and `_test_overrides.validator_executable_path`. Every path that fails byte or NUL admission is omitted from a refusal's `test_overrides`, even when another field is refused first. Excess returns `bad_request` with `admission_failure`. | Fixed. |

### Execution budgets

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Worker readiness hint wait (`worker_ready_wait`) | 1,000 milliseconds | Nominal wait for the worker readiness hint. Expiry can leave `runner_subprocess.ready_byte_received: false` while the run continues. | Fixed. |
| Worker publication wait (`worker_sentinel_wait`) | 120,000 milliseconds | Nominal wait for worker results after the readiness-hint wait. Validator collection is outside this allowance; the listed duration is not a total runtime limit. Expiry can yield `runner_timeout` with partial evidence and reported cleanup results. | Fixed. |
| Worker exit grace (`worker_exit_grace`) | 1,000 milliseconds | Nominal wait for worker exit after an exit request. Expiry requests `SIGKILL`. Termination and reap failures remain reported. | Fixed. |
| Worker release wait (`worker_proceed_wait`) | 60,000 milliseconds | Elapsed monotonic deadline for worker release after successful policy application. Expiry or clock failure records a proceed failure with no attempts. | Fixed. |
| Nominal release margin (`validator_release_margin`) | 5,000 milliseconds | Informative allowance between the validator budgets and worker release wait. No separate timeout or refusal occurs at this value. | Not enforced; no flag. |
| Validator I/O test override floor (`validator_io_override_floor`) | 50 milliseconds | Minimum effective `_test_overrides.validator_io_timeout_ms`. Smaller supplied values use 50 ms; there is no ceiling. The reply mirrors the supplied value. This changes only the validator I/O deadline; a longer value can outlast `worker_proceed_wait` without restoring expired attempts. | Fixed. |
| Validator I/O deadline (`validator_io_wait`) | 30,000 milliseconds | Default elapsed monotonic deadline for validator query delivery and verdict collection. Received verdicts survive an I/O timeout; cleanup results remain reported. | Fixed. |
| Validator exit grace (`validator_exit_grace`) | 1,000 milliseconds | Nominal wait for validator exit after collection closes. Expiry requests `SIGKILL`. Termination and reap failures remain reported. | Fixed. |
| Exec child deadline (`exec_child_wait`) | 10,000 milliseconds | Elapsed monotonic deadline after successful spawn, limited by the remaining `exec_attempt_budget`. Expiry fails the attempt while preserving any observed natural exit code. Cleanup results remain reported; an observed leader exit does not establish that every descendant stopped. | Fixed. |
| Exec attempt budget (`exec_attempt_budget`) | 115,000 milliseconds | Elapsed monotonic budget shared by exec steps, including worker setup and intervening work but excluding the worker release wait. Exhaustion refuses a later spawn with `exec_failed` and `ETIMEDOUT`, no `child_pid` and no sandbox attribution. A clock failure refuses spawn or leaves an observation error after spawn. Blocking spawn and non-exec operations may outlast this allowance. | Fixed. |
| Exec child reap grace (`exec_reap_grace`) | 1,000 milliseconds | Elapsed monotonic allowance to confirm an exec child's exit after observation ends. Expiry, clock failure or a wait error leaves reaping unconfirmed and supplies no invented exit status. Failed group termination leaves only an immediate exit check. This is not a total cleanup runtime limit. | Fixed. |
| Runner RPC wait (`client_rpc_wait`) | 240,000 milliseconds | Default wait for the runner reply. The reply records the actual span as `data.runner_client.started_at_unix_ms` and `ended_at_unix_ms`. An expired wait yields `xpc_timeout`; it does not expand the inner worker or validator budgets. | Flag `--timeout-ms`, floored at 1 ms; values above this default are permitted. |
| Runner removal teardown wait (`runner_remove_teardown_wait`) | 1,000 milliseconds | Nominal wait for a removed BYOXPC service to disappear from launchd. The cleanup observation records the service checks and the wait. A service still listed at expiry retains its cleanup record with a warning; a later `runner remove` or `runner reconcile` continues recovery. | Fixed. No wait when the removal issued no bootout. |

### Queries and transport

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Validator query payload (`validator_query_payload`) | 65,534 bytes | Serialized JSON bytes for one validator probe, excluding the final LF. JSON escapes count toward this size. An overlong line produces one `parse_error` without a step ID; later lines remain usable. Admitted specimens stay below this limit. | Fixed. |
| Informative reply size bound (`runner_reply_maximum`) | 24,825,335 bytes | Upper bound on the encoded size of one runner JSON reply for this build. No reply is refused at this size; retained output is bounded by `controller_output`. | Not enforced; it sizes `controller_output`. |
| Runner client output (`controller_output`) | 75,497,472 bytes | Captured bytes per stdout or stderr stream from the runner client, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Derived: three times `runner_reply_maximum`, rounded up to a whole 4 MiB; no flag. |
| Log observer stdout (`log_observer_output`) | 33,554,432 bytes | Raw observer stdout bytes, including the JSON report and final newline. Stderr has a separate cap. Overflow retains a bounded raw prefix, with unavailable parsing and correlation. | Fixed. |
| Log show stdout (`log_show_stdout`) | 1,048,576 bytes | Raw bytes from `log show` stdout, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Log show stderr (`log_show_stderr`) | 131,072 bytes | Raw bytes from `log show` stderr, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Log observer stderr (`log_observer_stderr`) | 131,072 bytes | Raw bytes from observer stderr, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Observer JSON structure (`log_reply_structure`) | 262,144 items | Opening object/array delimiters, commas and colons outside quoted strings in the observer reply. Excess retains bounded raw diagnostic text with unavailable parsing and correlation. | Fixed. |
| Observer echoed metadata (`log_observer_metadata`) | 4,096 UTF-8 bytes | Each echoed show argument: predicate, process name, start, end, last, plan, row and correlation ID. Oversized arguments are rejected; oversized reply metadata leaves correlation unavailable. | Fixed. |
| Policy helper output (`policy_helper_output`) | 8,388,608 bytes | Captured bytes per stdout or stderr stream from `sbpl-check`, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Fixed. |
| Rejected validator frame context (`validator_fault_context`) | 256 bytes | Retained prefix of the first rejected validator frame, measured before base64 encoding. `frame_bytes`, `retained_bytes` and `context_truncated` describe how much context was retained. | Fixed. |

### Evidence capture

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Deny-log scan padding per endpoint (`log_window_pad`) | 2 seconds | Padding at each end of the runner client's span after rounding outward to whole seconds. The scan covers `floor(start) - 2 seconds` through `ceil(end) + 2 seconds`, including both pads. Raw client timestamps are unchanged; reversed endpoints prevent collection. | Fixed; `window.pad_seconds` records it. |
| Default log collection timeout (`log_collection_timeout`) | 10,000 milliseconds | Default elapsed monotonic allowance for log collection, including startup and processing. Actual costs appear in `data.sandbox_log_capture.supervision.elapsed_ms` and `observer.data.collection.elapsed_ms`. Expiry stops collection and starts the fixed cleanup grace; available diagnostics survive without associations. Standalone `show` uses the same default. | Flag `--log-timeout-ms`: a positive integer of milliseconds that fits a monotonic deadline plus the cleanup grace, validated before the runner starts even with `--no-log-capture`. |
| Log cleanup grace (`log_cleanup_grace`) | 1,000 milliseconds | Elapsed monotonic allowance for observing log-process cleanup after collection stops. Early failures start the grace immediately. The allowance expires no later than the original collection deadline plus this grace. Unconfirmed reaping or group absence is reported; retries never restart the allowance. | Fixed. |
| Log report reserve (`log_report_reserve`) | 1,000 milliseconds | Allowance withheld from the log query within `log_collection_timeout`. The observer's report can arrive after the query times out. Collection allowances at or below this reserve leave no query time. The reserve does not guarantee an intact report; interruption leaves bounded transport diagnostics. | Fixed; `supervision.reserve_ms` records 0 at the observer boundary and this value under `observer.data.collection`. |
| Parsed deny events (`log_deny_events`) | 8,192 records | Parsed deny events in show output and the derived controller array. An additional event makes capture incomplete and correlation unavailable; bounded raw output and available diagnostic events survive. | Fixed. |
| Candidate associations (`log_candidate_count`) | 4,096 items | Total event-to-step candidates, including ambiguous matches. Excess discards the whole derived association result and withholds correlation; retained events remain diagnostic. | Fixed. |
| Candidate allocation allowance (`log_candidate_bytes`) | 8,388,608 bytes | Total candidate charge: six times the sum of twice the step-ID byte length plus the path, operation, kind and action byte lengths, plus 1,024 bytes per candidate. Excess reports the `association_bytes` cutoff, discards associations and withholds correlation. | Fixed. |
| Steps admitted to correlation (`log_correlation_steps`) | 256 items | Each of the submitted plan and returned step arrays. Excess withholds log correlation; execution evidence is unchanged. | Fixed. |
| Exec child output per stream (`exec_stream`) | 1,023 bytes | Retained stdout or stderr bytes for each exec child. An overflow marker occupies part of this allowance. Excess output is not retained. | Fixed. |
| Primary worker diagnostic (`worker_diagnostic`) | 4,095 bytes | Retained primary diagnostic bytes. The reply reports retained length and truncation state; this is not a complete transcript. | Fixed. |
| Optional compiled-object capture (`applied_profile`) | 1,048,576 bytes | Raw bytecode bytes in an optional compiled-object receipt, before base64 encoding. Oversized or unsupported objects leave capture unavailable without preventing policy application. | Fixed. |
| Worker observed path (`observed_path`) | 1,023 bytes | Retained bytes in each worker-observed path. Path observation can be absent or bounded; a host-side path diagnostic is a separate observation. | Fixed. |
| Worker attempt error text (`attempt_error`) | 255 bytes | Retained bytes in each worker attempt error message. Error text is bounded; structured result and status fields remain separate. | Fixed. |

### Diagnostic helpers

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| sbpl-check source admission (`helper_source`) | 4,194,304 bytes | Top-level source bytes read by the diagnostic helper; not the runner policy cap. policy_too_large with null compile and import_inventory groups; no compile verdict. | Fixed. |
| sbpl-check import inventory depth (`helper_import_depth`) | 8 levels | Import depth in the helper inventory, starting at 0. Depth 8 is the first depth replaced by a depth-limit diagnostic. The affected branch stops and `import_inventory.truncated` is set. This does not limit compilation of imports. | Fixed. |
| sbpl-check import inventory count (`helper_import_count`) | 64 records | Import-inventory records, including unresolved and error records. Repeated files or names are listed once. Further inventory stops and `import_inventory.truncated` is set. This does not limit compilation of imports. | Fixed. |
| Log observer stream text (`observer_stream_text`) | 1,048,576 bytes | Streaming helper mode only (`--duration` or `--follow`): retained nonempty log lines after the prelude, with one LF per line. Only whole lines that fit are retained. The first overflowing line sets `log_truncated` and ends text retention. Deny-event arrays and JSONL emission continue. The normal CLI log-show path does not use this cap. | Fixed. `--no-log-capture` disables the CLI's log collection, not this helper mode. |

<!-- END GENERATED LIMITS -->

### Interactions that matter

- Budgets nest, and one flag changes one of them. `--timeout-ms` sets
  `client_rpc_wait`, which bounds only the client's wait. The worker polling
  window `worker_sentinel_wait`, the validator deadline `validator_io_wait`,
  the release wait `worker_proceed_wait` and the exec budgets keep their own
  values, so no number here is an end-to-end runtime. The reply records the
  client span in `data.runner_client.started_at_unix_ms` and
  `ended_at_unix_ms`; an expired client wait yields `xpc_timeout`.
- Output budgets mark, they never silently cut. Each receiver reports the
  budget it applied in `capture_limit_bytes` (`controller_output`,
  `policy_helper_output`). Output beyond it is marked truncated, and a
  truncated JSON stream is not parsed as a reply.
- Log limits change evidence only. The byte caps on `log show` and the
  observer (`log_show_stdout`, `log_show_stderr`, `log_observer_output`,
  `log_observer_stderr`) and the event and candidate counts (`log_deny_events`,
  `log_candidate_count`, `log_candidate_bytes`) are fixed; when one is
  exceeded, the capture keeps a bounded prefix and withholds correlation.
  `--log-timeout-ms` changes only the time allowance, `log_collection_timeout`.
  Attempt results and `sandbox_check` verdicts never change because of a log
  limit, and the plan's step count does not bound how much the OS log holds.
- One refusal names the first failing field. When a specimen exceeds several
  admission limits, the order is: top-level metadata (`specimen_id`,
  `request_label`) and `test_override_path` executable overrides, then plan
  and parameter counts (`probe_steps`, `policy_parameters`), then worker strings
  (`policy_source`, `step_id`, `attempt_target`, exec arguments, parameter keys
  and values), then host query
  fields (`query_operation`, `query_filter_value`, `probe_plan_label`). A
  refused value is never echoed shortened: an oversized `specimen_id` is
  replaced by `<admission_refused>`, an oversized `run_kind` is omitted and an
  oversized `policy.format` reads `unknown`.
- The `policy_source`, `parameter_key`, `parameter_value`, `step_id`,
  `attempt_target`, `exec_argument`, `query_operation`, `query_filter_value`
  and `test_override_path` limits also reject embedded NUL. For a string within
  its byte capacity, that refusal reports unit `nul_bytes`, maximum 0 and the
  same field. Metadata and labels (`specimen_id`, `request_label`,
  `probe_plan_label`) permit escaped NUL at this gate; their
  normal meaning rules still apply. Within the capacities above, other control
  characters and valid Unicode survive request transport unchanged.
- Exec steps share a budget and each child has a deadline. `exec_attempt_budget`
  bounds all exec steps of a plan together and `exec_child_wait` bounds each
  child; neither has a flag. A step the exhausted budget refuses reports
  `exec_failed` with `ETIMEDOUT`, no `child_pid` and no sandbox attribution. A
  child cut by its deadline fails the attempt but keeps any exit code that was
  observed. A worker that dies first leaves the step's exec details
  unpublished, which establishes neither that no child spawned nor that cleanup
  succeeded.
- What the deny-log capture covers. The requested window is the runner
  client's own span, rounded outward to whole seconds and padded by
  `log_window_pad` at each end; `window.start`, `window.end` and
  `window.pad_seconds` record it, and reversed wall-clock endpoints prevent the
  scan. Captured records name the worker's process name and PID. Denials inside
  exec children and prediction queries contribute no captured records. A
  missing record never establishes that an operation was allowed.

<!-- END COPIED LIMITS -->

## Output envelope

Every envelope carries a top-level `build` object naming the code that produced
it: `version` (nearest `v*` git tag), `number` (commit count), `describe` and
`commit`. The same values are stamped into the app's Info.plist. This is a
coordinate for correlating evidence with source, not a compatibility signal; the
contract versions below are.

### Shape and schema_version

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 4, response schema 14, controller envelope 7. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

Two documents carry these numbers. The runner reply is the JSON that
`pw-runner-client` prints: its `schema_version` is the response schema, and it
holds `normalized_outcome`, `steps`, `runner_subprocess`, `validator_subprocess`
and the policy identity (`specimen_id`, `policy_format`, `policy_sha256`). It is
readable on its own. The controller envelope is what `policy-witness run`
prints: its `schema_version` is the controller envelope, `result` summarizes
the run, and `data` carries the reply unchanged as `runner_result` beside the
specimen dossier (`specimen`), the client transport (`runner_client`), the
fallback compilation (`policy_check`), the controller's projections
(`runner_sandbox_diagnostics`), the optional log capture
(`sandbox_log_capture`) and `timeout_ms`. Readers that interpret either
document accept exactly the current numbers; another version is reported as
unsupported, with the bytes retained (see [CONTRACT.md](CONTRACT.md)).

The XPC host stays unsandboxed and spawns a sandboxed attempt worker plus a
batch validator. Worker identity for
correlation comes only from `runner_subprocess.pid`; top-level `pid` may name
the host or client when no worker metadata exists.

`runner_subprocess` retains PID, exit/signal and partial-step status, plus
`ready_byte_received`, `done_observed`, `poll_stop_reason`, `exit_requested`,
`termination_request`, `reaped`, and `wait_errors`. Polling reasons are `done`,
`child_reaped`, `sentinel_deadline`, or `wait_error`. Termination requests record
signal, syscall return and errno only on failure. Exit/signal values require a
successful reap; both are absent/null when disposition is unconfirmed. Wait
errors retain their phase and native return/errno, including recovered EINTR.
Application remains independently reported by `sandboxed_after_apply`.

`runner_subprocess` also records three host facts where the host acts:
`cleanup_trigger` (why exit was requested: `deadline_expiry`, `completion`,
`child_reaped`, `poll_wait_error` or `policy_transfer_error`), `grace_end` (how
the exit-grace wait ended: `not_entered`, `reaped_during_grace`, `exhausted` or
`wait_error`) and `collection_basis` (whether the final shared-memory reads
followed a confirmed reap: `after_confirmed_reap`, `execution_may_continue` or
`unavailable`). `runner_subprocess.disposition` is the worker disposition
record: one account of the worker's lifecycle, present whenever a worker
subprocess is reported. It answers seven run questions (`final_status`,
`stop_reason`, `cleanup_trigger`, `grace_end`, `kill_request_and_result`,
`collection_basis`, `progress_association`) and three per-step questions
(`step_boundary_reached`, `step_result_published`,
`step_requested_operation_applicability`). Each answer is `supported` with a
`basis` naming the raw fields that witness it, `unresolved` or `inapplicable`
with a reason, or `conflicting` with an entry in `issues`. The raw fields stay
authoritative; the record references them, and every lifecycle conclusion in
the envelope, including `attempt.lifecycle` and the controller's
`termination_cause`, is a projection of it.

The controller projects the record into `data.runner_sandbox_diagnostics`:
`process_disposition` (`no_worker`, `unconfirmed`, `clean_exit`, `nonzero_exit`,
`signaled`, `conflicting`, `withheld` or `unrecognized`), `termination_cause`,
`stop_reason`, `disposition_integrity` and `disposition_issues`.
`termination_cause` names host cleanup the record witnesses end to end
(`host_sentinel_deadline`, `host_exit_grace_exhausted`,
`host_cleanup_after_wait_error`, `host_cleanup_after_transfer_error`); it is
null for a confirmed clean exit and `unknown` for every other termination,
including a self-signal and an unresolved or conflicting status. It never names
the sandbox. `stop_reason` projects why polling stopped (a deadline can coexist
with a clean exit), and `disposition_integrity` with `disposition_issues` says
whether the carried record agreed with the raw facts it cites (`valid`, or
`invalid` with claims withheld). These fields do not change `normalized_outcome`.

A host reply-construction failure reports `runner_reporting_failed`, `rc: 1`
and `reporting_failure` with the diagnostic and original execution summary.
When `reporting_failure.evidence_retained` is true, queries, attempts and child
observations survive, but every `comparison` is omitted. Retained ordering
observations are diagnostic; this reply certifies no per-step order. If serialization also fails for that degraded reply,
`evidence_retained` is false and steps and subprocess evidence are absent.

Optional subprocess objects may be omitted or null. A null `errno` on a step
requires key presence. Outcome mappings below use execution evidence without
assigning a sandbox termination cause from a signal or log match.

The `exec` attempt kind adds five optional per-step fields under
`steps[].attempt` — `child_pid`, `child_exit_code`,
`child_term_signal`, `stdout`, `stderr` — populated only for
`("exec", "spawn")` attempts. These are optional fields;
consumers that branch on `attempt.outcome == "exec_failed"` see the
three child fields exactly when an exec attempt's slot was filled, and
`stdout`/`stderr` only when that stream produced bytes. A non-exec
attempt's envelope omits the keys entirely so a sysctl /
file / mach result envelope does not grow five null fields it has
no use for.

### Top-level fields

Reply fields beyond `pid` / `runner_subprocess`:

- `validator_subprocess` — optional validator child observations, including
  `pid`, `reaped`, exit/signal status and the [receiver evidence](#receiver-evidence).

  | Observed validator disposition | Current status fields |
  | --- | --- |
  | Confirmed normal termination | `exit_code` present, including nonzero codes; no `term_signal` |
  | Confirmed signal termination | `term_signal` present; no `exit_code` |
  | Final status unconfirmed | Neither status field supplies a value; the current encoder omits both |

  Readers tolerate absent or null optional values. `reaped` records whether
  final status was confirmed; termination requests and wait errors are
  independent evidence. Any observed terminating signal can be recorded,
  and its number alone does not identify the sender. An absent or null
  subprocess object does not by itself establish why validator observation
  is missing.
- `validator_spawn_failure` — optional host launch evidence with `origin`,
  `operation`, `executable_path`, `return_code` and `diagnostic`. For a failed
  validator launch, these are `runner_host`, `posix_spawn`, the executable path,
  the direct native return code and native descriptive text. The code is not
  ambient errno. Unfamiliar nonzero codes remain failures; wording is not a
  classification rule. The record survives a higher-priority worker failure
  and evidence-preserving reply degradation.
- `steps[].comparison.order` — `query_first` for eligible native records with the full release/acknowledgement chain; `unestablished` otherwise. Query order establishes an interval before the entire attempt batch, not state stability or runtime identity.
- `runner_subprocess.ordering` — host collection/release observations, worker acknowledgement, worker lifetime evidence, validator disposition and protocol violations. Collection closure releases attempts even after validator failure or unconfirmed cleanup; no later record enters predictions. Missing predictions remain unestablished. Death before acknowledgement prevents a query-first claim; later death preserves it. `validator_disposition` is `not_invoked`, `not_needed` (empty query plan), `not_spawned`, `reaped` or `unconfirmed`.
- `steps[].comparison` — six fields that relate the two channels without
  judging them. `observation` classifies the attempt channel (`succeeded`,
  `permission_failure`, `other_failure` or `unavailable`) and
  `observation_basis` names the fields it rests on (`completed_worker_status`,
  `permission_errno`, `bootstrap_permission_result`, `spawned_child` or
  `no_completed_worker_result`). `operation_relation` (`matched`, `different`
  or `unresolved`) says whether the submitted query operation is the attempt's
  mapped operation: file `open_read`/`access` map to `file-read-data`,
  `open_write` to `file-write-data`, `unlink` to `file-write-unlink`, exec
  `spawn` to `process-exec*`, mach lookup to `mach-lookup` and sysctl read to
  `sysctl-read`. `target_relation` (`same_submitted`, `different_submitted` or
  `unresolved`) compares the submitted filter value with the submitted attempt
  target under the attempt's mapped filter kind: `path` for file and exec,
  `global_name` for mach lookup, `sysctl_name` for sysctl. `order` is described
  above. `limitations` lists the planner's exclusion
  (`query_plan:path_unresolved_at_planning`,
  `query_plan:prediction_unavailable_pair`,
  `query_plan:unrecognized_filter_kind`) or the attempt's lifecycle state
  (`attempt:lifecycle_unresolved`, `attempt:lifecycle_conflicting`,
  `attempt:unsupported`, `attempt:not_reached`,
  `attempt:started_without_result`), and is empty otherwise. The prediction
  itself stays in `sandbox_check`; the record never says whether the channels
  agree. [Reading a comparison record](#reading-a-comparison-record) gives the
  rules for using it.
- `steps[].attempt.requested_kind` / `requested_action` — submitted intent,
  alongside the `requested_path` target; these do not prove execution.
  A `file`/`create` attempt and an unsupported attempt have no single mapped
  operation, so their `operation_relation` is `unresolved`. For exec/spawn, a
  `process-exec*` query predicts admission of the submitted executable target
  only; fork, interpreter and other spawn prerequisites are outside it, so an
  allow answer does not promise a successful spawn. Native failure and
  missing-result evidence survive.

The authoritative child object also includes `worker_evidence` when a child was
spawned. Its `abi_identity` identifies the host-selected protocol sources, not proof that
the child reached ABI validation. It contains the latest atomic `progress`, an
independently published `failure` (operation, diagnostic code, native result
kind/value, meaningful errno and optional parameter index), the worker's
readiness-write result, and a bounded `diagnostic`. Compilation returning NULL
is distinct from parameter setup or application returning an integer failure.
Numeric operation/code values are open: unfamiliar values remain available.
Missing/incomplete publication exposes no payload. Diagnostic text can be absent,
complete, empty, truncated or incomplete; its availability does not determine
failure classification. Its length counts stored bytes, and invalid UTF-8 is
decoded with replacement characters. Early stderr and
unpublished text are not recovered by this channel.

`done_observed` and completed slots reflect the final acquire snapshot after
cleanup. `poll_stop_reason` retains an earlier deadline even if the worker
finishes during grace. On a failed policy write, `policy_transfer_error` records
the host's errno and written/expected UTF-8 byte counts, while worker evidence
and process status remain available. Written bytes do not prove child receipt.

Both step channels carry `result_source` and, when no result exists,
`missing_reason`; the query channel also carries `native_rc`. A missing
requested prediction retains `rc=0` with source `synthetic`, `native_rc:null` and a
`missing_reason` of `validator_not_invoked` (no validator process),
or `validator_no_verdict` (the process ran without this verdict). Planner-excluded
queries use `prediction_unavailable`, `rc=-1` and `query_not_requested` with
the same synthetic source and null native return. Received predictions
use source `validator`; `native_rc` is retained only for native-call result records.

For supported attempts, completed worker slots use
`attempt.result_source: "worker"`, including completed failed operations.
Absent or incomplete publications use `"synthetic"` with `missing_reason: "slot_absent"` or
`"slot_incomplete"`, respectively. Their `not_run_worker_died` outcome means
no completed result, not proof that the operation never started. The separate
`attempt.lifecycle` evidence addresses that question: its `summary` is
`completed`, `started_without_result`, `not_reached`, `unsupported`, `unresolved`
or `conflicting`, and its `boundary` and `result` claims carry the supporting
observations or the reason the
question is unresolved, projected from
[the worker disposition record](#shape-and-schema_version). A completed
attempt's rc is PW attempt status, not a raw syscall return, and the attempt
channel carries no native return.

### Receiver evidence

`validator_subprocess` retains accepted `records` (including null-ID diagnostics)
and their `raw_line`, expected IDs, association issues, received stdout byte
count, probe write counts, independent I/O/decode faults, termination-call
observations and actual reap status. Duplicate IDs supply no unique per-step
prediction. Decode context is not an accepted verdict. Unfamiliar structurally
valid diagnostic outcomes remain visible even when their per-step summary is
`error`.

`data.runner_client` reports the client's `argv`, start and end milliseconds,
`exit_code`, exact received/retained stdout and stderr byte counts and
`capture_limit_bytes`. `stdout_capture_error` means the controller truncated
its own retained reply; `stdout_parse_error` means the untruncated bytes could
not be decoded as JSON. Records inside a lost envelope are unavailable. The
independent fallback helper's admission refusal remains `policy_too_large`;
successful helper compilation cannot explain a missing worker reply.

The controller delivers the request to the client on stdin (`--request -`)
and records that delivery in `runner_client.request_delivery`:
`bytes_written` and `error`. This is a controller observation: an accepted
pipe write and a closed writer do not prove that the client read the bytes or
that XPC delivered them. A delivery error makes the run a controller
`tool_error` (exit 2) that takes precedence over any captured reply; the reply
stays unchanged in `data.runner_result`. `runner_client` is null when the
client was not invoked.

`steps[].sandbox_check.pid` is the spawned worker PID, or explicit null when no
worker exists. It never substitutes the host PID.

The query channel's `native_rc` is authoritative for native returns. A
received diagnostic without a native return retains `result_source="validator"`,
`native_rc=null` and `rc=-1`; this is not a synthetic validator record or a
claimed native failure. Missing replies use synthetic `rc=0`, `outcome="error"`
with a missing reason. `outcome="error"` alone does not identify a native call
failure.

### The specimen dossier

`data.specimen` is present on every `kind: "run"` envelope, including
refusals and pre-execution tool errors. It records what the controller knew
about the request before invoking the runner. Nothing in it embeds policy
source or parameter values.

- `request_path`: the path given to `run`, or null when no path was given.
- `policy.augmentation`: always present; see [Augments](#augments). `status`
  is `not_requested`, `applied`, `failed` or `not_applicable`; `applied` lists
  the spliced augment names; `original_sha256` hashes the submitted string
  source and `applied_sha256` the string selected for invocation (the same
  hash when nothing was applied); `error` carries the refusal diagnostic. The
  hashes name string bytes that existed; they do not cover parameters or prove
  worker compilation.
- `policy.imports`: the literal `(import "...")` closure of the selected
  source, scanned before invocation under the search paths and bounds shared
  with `sbpl-check` (`/System/Library/Sandbox/Profiles/`, then
  `/usr/share/sandbox/`, and absolute paths; the `helper_import_depth`,
  `helper_import_count` and `helper_source` rows under [Limits](#limits)).
  `status` is `complete` (the closure was exhausted with no unresolved name,
  cycle, nonliteral import form, decoding error or exceeded bound),
  `incomplete` (collected records are kept; `exceeded` names the first bound
  hit, `depth` or `count`, or `cycle` names the cycle), `failed` (the collector
  could not start; `failure` says why) or `not_applicable` (no post-resolution
  source; `failure` is `augmentation_failed` after a refused augment and null
  otherwise). For an incomplete scan, `failure` identifies the first problem
  encountered; a complete scan has `failure: null`. `closure_sha256` hashes the source plus every successfully
  hashed import whenever the scan ran. Each record carries `name`,
  `resolved_path`, `sha256`, `size_bytes`, `mtime_unix` and `error`. Each
  unique resolved import is opened once and checked to be a regular file
  before the same bytes are hashed and lexed. The scan describes files the
  controller could read; macro evaluation and the files the worker's compiler
  actually read are outside it. `data.policy_check`, when the fallback
  compilation ran, carries `sbpl-check`'s own inventory verbatim; the two are
  not reconciled.
- `host`: `macos_version`, `macos_build`, `kernel_release` and `arch`, read
  from `kern.osproductversion`, `kern.osversion`, `kern.osrelease` and
  `hw.machine`; null when a read fails. These are environment context. They do
  not identify the sandbox libraries the worker or the validator loaded.
- `runner_provenance`: the selected runner's `runner_kind`, bundle identity
  and path, service name, executable path, entitlements and signature
  metadata, and `runner_registry_id` for an installed BYOXPC runner.
- `app_provenance`: `evidence_manifest_path`, the app evidence manifest the
  built-in runner and the binary baselines were selected from, and
  `evidence_verify`, the verification report when `PW_VERIFY_EVIDENCE`
  requested one (null otherwise). The object is null when the manifest could
  not be parsed.
- `binaries.service`, `binaries.worker` and `binaries.validator`: null when
  the selected binary is the manifest's entry for that role, so the manifest's
  hash already describes it. Otherwise (a `_test_overrides` executable path or
  a BYOXPC copy) an object with `path`, `actual_sha256`, `baseline_sha256`
  (the manifest entry's hash), `verification` (`match`, `mismatch` or
  `unavailable`) and `reason` (null only for `match`). The hash is taken
  before invocation and does not prove which bytes were launched. Neither
  `mismatch` nor `unavailable` changes the run outcome.

Collection failures are recorded in these statuses and do not change whether
the request is admitted or the runner is invoked. For a controller refusal, the
dossier holds what was collected before the refusal: unavailable scalars are
null, lists are empty, and the imports status says why no scan ran.

To check that a result came from the bytes you think it did:

```sh
jq '.data.specimen | {request_path, policy: {augmentation: .policy.augmentation.status,
  applied_sha256: .policy.augmentation.applied_sha256, imports: .policy.imports.status,
  closure_sha256: .policy.imports.closure_sha256}, host, runner: .runner_provenance.runner_kind,
  binaries}' run.json
jq '[.data.specimen.policy.augmentation.applied_sha256, .data.runner_result.policy_sha256]' run.json
```

### Per-step shape

The runner echoes step results with additional context:

- `steps[].sandbox_check`: `{ rc, outcome, pid, operation, filter_kind, filter_value, filter_type_id, errno, error, result_source, native_rc, missing_reason?, path_diagnostics? }`
- `steps[].attempt`: `{ rc, errno, outcome, error, result_source, missing_reason?, requested_kind, requested_action, requested_path, observed_path, lifecycle, path_diagnostics?, child_pid?, child_exit_code?, child_term_signal?, stdout?, stderr? }`
- `steps[].comparison`: `{ observation, observation_basis, operation_relation, target_relation, order, limitations }` — see [Top-level fields](#top-level-fields) and [Reading a comparison record](#reading-a-comparison-record).

Notes:
- `requested_path` echoes the attempt target for every attempt kind
  (path, Mach service name, sysctl name, etc.). `observed_path` is the
  worker's own `F_GETPATH` observation of a successful open, explicit `null`
  otherwise. `path_diagnostics` is the host's later resolution of a file or
  exec attempt target (see [attempt.path_diagnostics](#attemptpath_diagnostics));
  other attempt kinds omit it.
- `filter_value` is the exact string the runner passes to `sandbox_check`,
  except when `outcome == "prediction_unavailable"` — in that case no
  `sandbox_check` call is made; `filter_value` is echoed back from the
  request unchanged for cross-referencing with the specimen.
- `filter_type_id`: `1` (path), `2` (mach-lookup global), `17`
  (mach-lookup local). The global-name ID was verified against kernel
  enforcement (deny on the policy's denied value and allow on a sibling
  un-denied value); ID `12` passes the same check, so `2` is the selected
  working ID, not the uniquely correct one. The local-name ID has not been
  verified by the same method. For filter kinds in the
  prediction_unavailable set, no `filter_type_id` is emitted (see
  [Filter kinds where prediction is unavailable](#filter-kinds-where-prediction-is-unavailable)).
- `outcome`: `allow`, `deny`, `error`, `unsupported_operation`, or
  `prediction_unavailable`.
    - `allow` / `deny`: `sandbox_check` returned a clean verdict.
    - `error`: no usable prediction. This includes native call errors,
      validator diagnostics and synthetic missing replies. Consult
      `result_source`, `native_rc`, `missing_reason` and run-level records;
      the outcome alone does not establish that a native call ran.
      Diagnostic text need not be `strerror(errno)`.
    - `unsupported_operation`: `sandbox_check` returned `rc=-1` +
      `errno=22` (EINVAL), which most commonly means the operation
      name is one libsandbox doesn't recognize. SBPL family
      operations must be passed to `sandbox_check` in their
      wildcard form — e.g. `process-exec*`, not the bare
      `process-exec`. `error` is always populated with a message
      naming the rejected operation and the wildcard hint. The step
      still runs the attempt channel for the observation. The
      prediction channel yields no answer, so `comparison.order` is
      `unestablished`, and `operation_relation` compares the
      submitted spelling with the attempt's mapped operation
      (`different` for bare `process-exec` beside a spawn).
    - `prediction_unavailable`: emitted when the runner deliberately
      skips `sandbox_check` for a step where the userland predicate
      is structurally suspect. Two public triggers, each named by a
      `query_plan:*` entry in `comparison.limitations` when the comparison
      is available (degraded replies can omit it):
        - **op+filter pair** in the set under
          [Filter kinds where prediction is unavailable](#filter-kinds-where-prediction-is-unavailable)
          (`query_plan:prediction_unavailable_pair`).
        - **per-step host condition**: a `path` filter whose
          `filter_value` doesn't resolve via `realpath` on the host
          at planning time. PW excludes that query and records
          `sandbox_check.error` naming the unresolved path, plus
          `query_plan:path_unresolved_at_planning` when the comparison
          is available. The later [path diagnostics](#path_diagnostics)
          describe a separate observation after orchestration; they can
          resolve a target created by the attempt.
      The `attempt` result remains the reliable evidence
      for these probes; the prediction is honestly absent rather
      than wrong.
  When `outcome == "prediction_unavailable"`, `rc` is the sentinel
  `-1` (not `0`) and `errno`/`filter_type_id` are `null` — consumers
  that key on `rc == 0` for "allow" must check `outcome` first so the
  sentinel is not misread.

For supported attempts, a completed slot has `attempt.result_source: "worker"`
whether the operation succeeded or failed. Missing or incomplete publications
have source `"synthetic"` with `missing_reason: "slot_absent"` or
`"slot_incomplete"`; lifecycle evidence separately describes progress.

`steps[].attempt.outcome` values:

- `ok` — the attempt's syscall returned success (allow).
- `open_failed` — file `open()` (for `open_read` / `open_write` /
  `create`) returned non-zero; errno in `attempt.errno`. EPERM /
  EACCES are ambiguous between sandbox and DAC (see
  [Reading a comparison record](#reading-a-comparison-record)).
- `unlink_failed` — file `unlink()` returned non-zero; errno in
  `attempt.errno`.
- `access_failed` — file `access(R_OK)` returned non-zero; errno in
  `attempt.errno`.
- `lookup_failed` — `bootstrap_look_up` returned a non-success
  Mach kernel return code; the `kr` is preserved in
  `attempt.error` as `"bootstrap_look_up: kr=<N>"`. `kr=1100`
  (`BOOTSTRAP_NOT_PRIVILEGED`) is the permission-shaped result the
  comparison classifies as `permission_failure` with basis
  `bootstrap_permission_result`; it does not identify the sandbox as
  the cause. `kr=1102` (`BOOTSTRAP_UNKNOWN_SERVICE`) means the
  service simply isn't registered and is not a permission result.
- `sysctl_failed` — `sysctlbyname()` returned non-zero; errno in
  `attempt.errno`. EPERM / EACCES are ambiguous; ENOENT / ENOMEM
  are non-policy failures.
- `exec_failed` — `posix_spawn` was blocked, the target was
  missing, the helper exited non-zero, the helper was signaled,
  the per-exec deadline fired, or the worker's exec attempt budget
  was exhausted before spawn (`child_pid` 0, errno 60), or observation/cleanup
  failed after spawn. A leader exit of zero can coexist with a failed attempt
  when descendants retain pipes beyond the deadline. See
  [Attempt kinds the runner implements](#attempt-kinds-the-runner-implements)
  → `("exec", "spawn")` for the `child_pid` sentinel rules that
  distinguish a spawn that produced no child from a helper that
  simply exited non-zero.
- `unsupported` — defensive output for an unimplemented attempt combination;
  public admission refuses such combinations before children. See the
  [developer construction rule](REQUEST-GRAMMAR.md#what-the-implementation-promises).
- `not_run_worker_died` — no completed attempt result. Missing or incomplete
  publication does not prove the operation never started; `attempt.lifecycle`
  says which, and the comparison's limitation repeats its summary
  (`attempt:started_without_result`, `attempt:not_reached`,
  `attempt:lifecycle_unresolved` or `attempt:lifecycle_conflicting`) beside
  `observation: unavailable`. Errno is null when no result supports it.

### Reading a comparison record

The record relates the two channels; it does not say whether they agree.
Read it with these rules, in order:

<!-- BEGIN COPIED READING RULES -->

1. The query channel's answer is `sandbox_check.outcome` when `result_source`
   is `validator` and the outcome is `allow` or `deny`; otherwise no prediction
   was available and `sandbox_check.missing_reason` says why.
2. `attempt.missing_reason` explains an unavailable attempt channel.
3. A `permission_failure` or `other_failure` observation, or an exec attempt
   whose spawned child exited nonzero, does not attribute the failure to the
   sandbox; attribution needs a captured denial record, and
   `permission_failures_without_record` lists the steps that have none.
4. A `path` query, or an attempt whose mapped filter is `path`, never
   establishes that both channels resolved the same object at runtime.
5. No record establishes that the state the query saw is the state the
   attempt met; nothing in a reply discharges this.
6. When a query has `filter_kind: path`, a nonnull `filter_value` and no
   `query_plan:*` limitation, and any step's attempt is a worker `unlink` of
   that same submitted path with `outcome: ok` and `rc: 0`, the target was
   removed during the run; `order` says whether the removal followed the
   query, and the unlink attempt's step is the step that removed it.
7. A `process-exec*` query predicts target admission only, not every spawn
   prerequisite; the child's result is in `attempt.rc` and
   `attempt.child_exit_code`.
8. A `file`/`create` attempt has no single query operation, so
   `operation_relation` is `unresolved`.
9. A query operation containing `*`, other than `process-exec*`, resolves to
   no single attempt operation.
10. `target_relation: unresolved` means the attempt's mapped filter kind
    differs from the query's `filter_kind`, or `filter_value` or
    `requested_path` is absent; those fields show which.
11. `sandbox_check.path_diagnostics.realpath_resolved` null on a query the
    planner did not exclude means the host could not resolve the submitted
    path after the run.
12. An attempt the worker does not support has `attempt.outcome` and
    `missing_reason` saying so, and both relations `unresolved`.

<!-- END COPIED READING RULES -->

Select steps by explicit field combinations. A deny
answer beside a successful attempt, with the relations and order that qualify
it:

```sh
jq '.data.runner_result.steps[]
    | select(.sandbox_check.outcome == "deny" and .comparison.observation == "succeeded")
    | {step_id, operation_relation: .comparison.operation_relation,
       target_relation: .comparison.target_relation, order: .comparison.order,
       limitations: .comparison.limitations}' run.json
```

Steps with no usable prediction, and why:

```sh
jq '.data.runner_result.steps[]
    | select(.sandbox_check.result_source != "validator"
             or (.sandbox_check.outcome | IN("allow", "deny") | not))
    | {step_id, outcome: .sandbox_check.outcome, missing_reason: .sandbox_check.missing_reason,
       limitations: .comparison.limitations}' run.json
```

Permission-shaped failures that no captured denial record names:

```sh
jq '.data.runner_sandbox_diagnostics.permission_failures_without_record' run.json
```

### path_diagnostics

`path_diagnostics` is emitted on every path-filter `sandbox_check`
result with a nonempty submitted path. It carries later host-resolved path forms
for diagnostic inspection; it cannot identify which form an earlier native check
used. Fields: `{ observer, phase, input, same_as_input, realpath_resolved?,
firmlink_resolved? }`. The runner still passes the raw `filter_value` to
`sandbox_check` — this block is observation only.

Producer: `path_diagnostics` is computed by the unsandboxed runner
host (`PWRunnerService.enrichPathDiagnostics`) after orchestration returns,
which need not establish that every child was reaped. `observer="runner_host"`
and `phase="after_orchestration"` identify that provenance. The host's resolution
is independent of the worker's sandbox and can see a path changed by an attempt.
Neither a resolved path nor null establishes what the validator saw earlier.

Each form is in exactly one of three states, so a reader never guesses:

- listed by name in `same_as_input` and its key omitted: the host derived
  the form with exactly the same UTF-8 bytes as `input`, so the path is carried once;
- present as a string: the host derived a different form;
- present as an explicit `null`: the host could not derive the form.

`same_as_input` is required and contains unique names drawn
from `realpath_resolved` and `firmlink_resolved`. A form both listed and
present, or neither listed nor present, is malformed. A carried string
must differ from `input` in UTF-8 bytes. Canonically equivalent Unicode
spellings with different bytes remain separate strings.

In the [file-create exercise](#try-an-accepted-request-and-a-refusal), an absent
target can be excluded at query planning, then created successfully by the
attempt and resolved by this later host pass. If the resolved bytes equal
`input`, `same_as_input` lists `realpath_resolved` and that key is omitted;
otherwise the diagnostic can carry a different resolved string. The earlier
`prediction_unavailable` outcome does not require a later null path form.

- `realpath_resolved`: `realpath(3)` of `input`, or null on failure.
  Computed in the unsandboxed host; under normal conditions this is
  populated whenever the file exists. Null only when the host's own
  `realpath` fails (path doesn't exist, permission denied at the
  host level, etc.). The other form below remains computable in that
  case.
- `firmlink_resolved`: the realpath result rewritten through
  `/usr/share/firmlinks`. When realpath returned null, the host
  falls back to a pure-string substitution of the standard userspace
  symlinks (`/etc`, `/tmp`, `/var` → `/private/{etc,tmp,var}`)
  before applying firmlinks, so `/etc/hosts` still lands at
  `/System/Volumes/Data/private/etc/hosts` in the rare case the
  host's `realpath` fails. The firmlinks map is loaded eagerly and
  has a built-in fallback mirroring the standard mappings on
  Catalina+.

### attempt.path_diagnostics

Every file or exec attempt with a nonempty target carries
`attempt.path_diagnostics`: `{ observer, phase, input, same_as_input,
realpath_resolved?, parent_realpath_resolved? }`, produced by the same
unsandboxed host pass after orchestration (`observer="runner_host"`,
`phase="after_orchestration"`) and always in the compact three-state form
above. `realpath_resolved` is `realpath(3)` of the target with the leaf
followed. `parent_realpath_resolved` is `realpath(3)` of the parent directory
with the literal leaf appended: the path the kernel names for a created or
unlinked entry, or for a symlink acted on itself. Either is null when the host
cannot derive it (a missing leaf has no leaf-followed form; a relative path has
no parent form). Neither establishes what the worker's own syscall resolved,
and neither changes the attempt or its comparison. Deny-log
correlation admits these forms as candidate evidence under their provenance;
see [Denial-log correlation](#denial-log-correlation).

Capture the sandbox_check argument quickly:

```sh
jq '.data.runner_result.steps[].sandbox_check | {filter_value, filter_type_id, outcome, path_diagnostics}' run.json
```

### normalized_outcome catalog

`data.runner_result.normalized_outcome` values the runner can produce
(for the standalone helper's `bad_request`, `policy_too_large`,
`setup_error`, `compile_error` and `ok` outcomes, see
[SBPL check](#sbpl-check-sbpl-check)):

- `ok` — worker completion and clean disposition are confirmed. Any invoked
  validator also has confirmed clean disposition, valid received records for
  every requested step ID, and no transport, decoding, or association failure.
  Uniquely associated per-step diagnostics retain their per-step semantics.
- `runner_timeout` — the host observed exhaustion of its sentinel polling
  budget. This remains a timeout if the child voluntarily exits during grace;
  a cleanup termination request alone does not establish a deadline.
- `runner_failed` — execution/reporting failure, including inconsistent
  publication, a published worker operation failure, an incomplete
  report, abnormal or unconfirmed disposition, or a host wait/cleanup failure.
  The cause may be unknown; this label does not prove a host defect. A completed
  report survives an abnormal exit, but cannot establish clean run completion.
- `runner_reporting_failed` — the host could not encode its assembled result.
  `reporting_failure` preserves the original summary separately; this outcome
  attributes no failure to the worker, validator or specimen policy.
- `worker_spawn_failed` — host could not `posix_spawn` the worker
  (filesystem/codesign/quota error). Worker never ran.
- `validator_spawn_failed` — host could not `posix_spawn` the
  validator child. `result.ok=false`; attempts are still surfaced
  in `steps[*].attempt` as degraded evidence.
- `validator_no_reply` — host encountered validator probe-write or verdict-read
  I/O failure. Independently completed verdicts and attempts remain available.
- `validator_decode_failure` — the host rejected a validator reply frame at the
  UTF-8, JSON syntax, or record-structure boundary. Earlier valid records survive.
- `validator_unavailable` — requested IDs lack unique replies, unassociated or
  unexpected records arrived, or validator disposition/cleanup is abnormal or
  unconfirmed. A sufficient record count alone cannot establish success.
  Partial verdicts and attempts survive. Missing supported-query verdicts use
  the `outcome="error"`, `rc=0` shape with `result_source="synthetic"`,
  `native_rc:null`, and a missing reason.
- `bad_request` — request rejected before any worker spawn. Causes
  include: JSON decode failure, empty `sandbox_check.operation`, an unknown field (e.g.
  `instrumentation`), duplicate `step_id`, or a capacity refusal: the worker's
  shared-memory bounds, the host-only query strings and filter/attempt labels,
  or the top-level and test-seam strings. Admission runs after decoding, before
  semantic validation. Native C-string fields also reject embedded NUL.
  Capacity refusals carry host-owned `admission_failure` with field, actual and
  maximum, `utf8_bytes`, `items` or `nul_bytes`, and applicable `step_id`, `step_index`,
  `parameter_key` and `index`. Every `bad_request` reply has `steps: []`:
  nothing ran, so the refused probe plan is omitted. A capacity refusal never repeats
  the string it refused: a refused step ID or parameter key is identified by
  position or by field, and a refused `specimen_id`, `run_kind`, `policy.format`
  or seam path is replaced by `<admission_refused>`, omitted, `unknown` or
  dropped from the mirrored `test_overrides` respectively. Every echoed field
  is checked independently, including when several fields are invalid.
  Unknown filter kinds, unsupported attempt combinations and non-null fields
  that cannot take effect are also refused. `request_failure` supplies the
  structured code and field path; the controller mirrors it at
  `data.request_failure`. See [request refusals](CONTRACT.md#structured-request-refusals).
- `already_ran` — the XPC service instance only accepts one
  `runSpecimen` call. A second call returns this error.

`xpc_error`, `xpc_timeout`, `xpc_proxy_type_mismatch`, and
`xpc_no_reply` are synthesized by `pw-runner-client` for an XPC error,
RPC wait expiry, a proxy type mismatch, or completion without a reply or error,
respectively. A host reply can be delayed or lost.

For ordinary, successfully captured client output, the two timeout layers map
to these fields:

| Event | `result.normalized_outcome` | `data.runner_result.normalized_outcome` | Result origin and distinguishing evidence |
| --- | --- | --- | --- |
| Client RPC wait expires | `xpc_timeout` | `xpc_timeout` | Client synthesizes a present result with empty steps and no host subprocess report. Client exit code is 1. |
| Host sentinel budget expires and its reply arrives | `runner_timeout` | `runner_timeout` | Host result includes `runner_subprocess.poll_stop_reason: "sentinel_deadline"` and available disposition evidence. Client exit code is 0 because it delivered the reply. |

The client exit code is `data.runner_client.exit_code`. The controller
`policy-witness` exits 1 in both cases. RPC expiry means no reply was received
before the client's deadline. It does not prove the host never ran, was
unreachable or crashed, and does not establish cancellation of host work.

If client stdout supplies no parsed reply, `data.runner_result` is null and
the controller can report `runner_output_not_json`; inspect the
[capture evidence](#receiver-evidence) for empty, undecodable or truncated output.
Client launch or request-delivery failures are `tool_error` paths. These differ
from a captured, client-synthesized RPC timeout and from a parsed reply retained
but refused as `unsupported_runner_response` or `malformed_runner_response`.

The controller's own outcomes (`tool_error`, `runner_output_not_json`,
`unsupported_runner_response` and `malformed_runner_response`) appear in
`result.normalized_outcome` and are documented in the
[controller README](../controller/README.md#output-contract).

## What PolicyWitness understands

### Filter kinds the runner predicts

The runner predicts (asks `sandbox_check` about) these filter kinds:
`none`, `path`, `global_name`, `local_name`,
`iokit_registry_entry_class`, `iokit_user_client_class`,
`sysctl_name`. Unknown filter kinds refuse the specimen before any attempts.
Known kinds other than `none` require a nonempty value. A `none` filter accepts
only an absent or null value.

### Filter kinds where prediction is unavailable

Even within the predicted set, some `(operation, filter_kind)` pairs
have no usable userland prediction: on the system where they were
checked, no `sandbox_check` filter ID in 1..200 produced an answer
that matched what the kernel enforced for the policy under test.
For these, the runner accepts the filter in specimens (so policies
can be authored), compiles and applies the policy normally, but
skips `sandbox_check` entirely and emits
`prediction_unavailable`, with
`query_plan:prediction_unavailable_pair` in the step's
`comparison.limitations`. The attempt still runs and provides the
real evidence.

The contract is keyed on the `(operation, filter_kind)` pair, not on
the filter kind alone — a filter kind with no usable prediction for
one operation may have one for another, and the check is
op+filter-specific. A specimen pairing one of these filter kinds with
a DIFFERENT operation gets a normal `sandbox_check` call; that
answer is reported as received, because the runner excludes only the
pairs it has checked.

Currently in this category:

- `(iokit-open-service, iokit_registry_entry_class)` — verified
  2026-05-29 unreliable across all candidate filter IDs in 1..200
  against `IOSurfaceRoot`. The runner short-circuits
  `sandbox_check.outcome` to `prediction_unavailable` (`rc=-1`); the
  C-worker orchestrator omits the probe from the validator batch.
- `(iokit-open-user-client, iokit_user_client_class)` — verified
  2026-05-29 with policy filter `IOSurfaceRootUserClient` and probe
  target `IOSurfaceRoot`. `iokit-open-user-client` is the SBPL
  operation `iokit-user-client-class` matches against (see Apple's
  `/System/Library/Sandbox/Profiles/application.sb` for canonical
  usage); `iokit-open-service` is a sibling operation that fires for
  the IOService class itself.
- `(sysctl-read, sysctl_name)` — verified 2026-05-29 unreliable
  across all candidate filter IDs in 1..200 against `kern.osrelease`.
  The same result outside the iokit family.

### Attempt kinds the runner implements

The C worker implements these `(attempt.kind, attempt.action)`
combinations:

- `("file", "open_read" | "open_write" | "create" | "unlink" | "access")` — exercise file ops on `target`.
- `("mach_lookup", "bootstrap_look_up")` — `bootstrap_look_up` on `target`.
- `("sysctl", "read")` — `sysctlbyname(target, ...)` read of a sysctl name such as `kern.osrelease`.
- `("exec", "spawn")` — `posix_spawn(target, argv, ...)` of a helper
  binary. `target` is the absolute path to the helper (becomes
  argv[0]). Optional `args: ["…", …]` supplies argv[1..N].
  The worker creates each child's stdout/stderr pipes and spawn handles
  inside the attempt, after the sandbox applies, and releases them before
  the step completes. None of that setup is a sandbox operation, so under
  an unaugmented `(deny default)` the denied call is `posix_spawn` itself
  (see [Augments](#augments) → `exec_baseline` for the policy that lets a
  spawn succeed). It bounds each child by the deadlines under
  [Execution budgets](#execution-budgets), drains both streams while the
  child runs, reaps it, and surfaces these fields under `attempt`:

  | field | populated when | sentinel when not | semantics |
  | --- | --- | --- | --- |
  | `child_pid` | spawn produced a child (helper ran, success or non-zero exit) | `0` — spawn blocked / target missing / setup failed | No child establishes spawn failure, not its cause. With `child_pid==0`, EPERM/EACCES are permission-shaped failures (`observation: permission_failure`) whose cause the record does not assign. A helper non-zero exit with `child_pid>0` still establishes successful spawning (`observation: succeeded`, basis `spawned_child`); the child's own result is in `rc` and `child_exit_code`. |
  | `child_exit_code` | child clean-exited | `-1` — signaled, no child ran, or final status unconfirmed | |
  | `child_term_signal` | child killed by a signal | `0` — clean-exited, no child ran, or final status unconfirmed | |
  | `stdout` / `stderr` | stream produced bytes | key omitted (no stream output) | |
  | `rc` | always populated | (n/a) | Helper's exit code after successful observation; `-1` on spawn, deadline, observation or cleanup failure. Consult `child_exit_code` for the leader's independently observed exit. |
  | `outcome` | always populated | (n/a) | `"ok"` when spawn and observation completed successfully and the leader exited 0; `"exec_failed"` also covers deadline and cleanup errors. Neither a successful leader reap nor pipe EOF proves descendant cleanup. |

  A minimal `(deny default)` policy will block `posix_spawn` itself.
  Callers who want exec attempts to succeed under a deny-by-default
  policy opt into `policy.augments: ["exec_baseline"]` (see
  [Augments](#augments)) — three `(allow ...)` rules are sufficient
  to let a libSystem-dynamic helper spawn, load dyld, and reach
  `main`. Callers who need to allow more (network, IOKit, specific
  filesystem subpaths) compose their own additional allows on top
  of the augment.

  The helper is spawned with `POSIX_SPAWN_CLOEXEC_DEFAULT` (so it inherits only
  the runner's stdin=/dev/null + stdout/stderr pipes — no shm fd,
  no policy fd, no other exec slots' pipes) and an empty
  environment.

  Exec children have their own PIDs; deny-log correlation covers the worker
  PID only (see [Denial-log correlation](#denial-log-correlation)).

Other attempt combinations refuse the whole specimen before worker or validator
creation. A non-null `args` field is accepted only for `exec/spawn`, including
when the array is empty. Query and attempt scopes can differ; recognized queries with
unavailable predictions still permit supported attempts.

## Operating

### Common flags

- `--timeout-ms <n>`: runner RPC timeout
- `--log-timeout-ms <n>`: log collection allowance, default 10,000 ms. Positive
  integer milliseconds only; no unlimited value. Invalid values fail before
  running the specimen, including with `--no-log-capture`. A larger value buys
  waiting time only: the specimen, the scan interval and the byte budgets are
  unchanged, and no record is promised.
- `--no-log-capture`: skip the unified-log (`log show`) deny scan. Archive access
  has been observed to cost seconds even for short spans. Pass this when you
  don't consume `data.sandbox_log_capture`; it is then `null` and
  `correlation_status` is `not_attempted`.
- `--runner-mode <standard|byoxpc>`: inject `runner.mode` into the request
- `--version`: print a `kind="version"` envelope with the build stamp and the
  wire contract versions this build speaks

Log collection is bounded in time and size. Observer startup, `log show` and
result processing share one monotonic deadline, followed by a fixed 1,000 ms
cleanup grace; the `log show` child itself stops 1,000 ms before that deadline
so the observer can deliver its report. Byte limits are listed under
[Evidence capture](#evidence-capture); a small specimen can still exceed one
because admission does not bound OS log volume. `sandbox_log_capture.supervision`
records the controller's observer wait and owned-group cleanup, and
`observer.data.collection` records the observer's own log child; both report
the effective timeout and its source, elapsed time, per-stream byte counts and
limits, and a `cutoff` reason. `deadline` reports as `capture_status: "timeout"`;
`output_overflow`, `event_overflow`, `json_structure_overflow` and
`correlation_overflow` as `overflow`; `launch_error` as `requested_unavailable`;
`process_exit` as `error` (or `blocked` for a recognized log-access refusal);
and `clock_error`, `pipe_setup_error`, `read_error`, `decode_error`,
`wait_error`, `pipe_open_after_exit` and `cleanup_unconfirmed` as `capture_error`.
`processing_cutoff` names a controller-side parsing or correlation limit.
`group_absent` requires an observed absent group after cleanup; a timeout or
overflow status alone does not establish that cleanup succeeded.

Any incomplete capture withholds correlation: `step_denies` and
`permission_failures_without_record` are null and `correlation_status` is
`unavailable`, while bounded diagnostics and any intact observer reply survive.
A successful complete empty query remains distinct. Neither case changes native
attempts, predictions, execution result or process disposition.

For a slower machine, select a larger finite allowance per run:

```sh
$PW run request.json --log-timeout-ms 30000
```

Each invocation is a separate observation; a later result does not replace an
earlier failure or show what an earlier query could have returned.

### Denial-log correlation

`sandbox_log_capture.window` separates raw client milliseconds
(`started_at_unix_ms`, `ended_at_unix_ms`) from the UTC query bounds (`start`,
`end`): `floor(client start) - 2 s` through `ceil(client end) + 2 s`, with
`pad_seconds` recording the pad. The observer mirrors the interval it scanned;
a reply for any other interval is `window_mismatch` rather than `captured`: its
parsed events remain inspectable, but `step_denies` is null and correlation is
`unavailable`. If the client's wall-clock end precedes its
start, capture is `invalid_window`: raw milliseconds survive, `start`/`end` are
null and the observer is not invoked. The pad allows for client/archive clock
differences, and supported records in either padding region remain eligible
candidates. It promises neither complete delivery nor exact run membership.
Structured event timestamps, step ordering and PID-reuse protection remain
unavailable; array position is not proof of execution order. Ordered endpoints
do not prove clock continuity during execution.

The controller invokes the observer only with a confirmed `runner_subprocess.pid`.
It never substitutes a host/client PID. `sandbox_log_capture.capture_status`
says how the capture ended; `runner_sandbox_diagnostics` reports
`correlation_status` (`not_attempted`, `unavailable`, `no_match`, `pid_match`)
beside the process disposition fields described under
[Shape and schema_version](#shape-and-schema_version).
`permission_failures_without_record` lists the step IDs whose attempt the
runner classified as a permission-shaped failure and that no captured event
names as a candidate (null unless correlation reached `pid_match` or `no_match`
and the reply carries per-step comparisons). A non-empty list means this
capture yielded no candidate for denials the attempts themselves reported; it
does not mean nothing was denied, it makes no claim about what the OS log store
contains (a record can exist under another path form, such as a resolved
symlink), and it does not say why.

Step associations under
`sandbox_log_capture.step_denies` contain `{event_index, candidate_step_ids,
association, matching_evidence}`. Array order is not time order, and a match
is not a cause of death. Events remain in `deny_events`, including unmatched events;
associations do not copy them. A single candidate uses `association="candidate"`;
multiple candidates use `"ambiguous"`. Neither establishes a unique occurrence.

Step matching requires a positive worker PID matching the event, an exact
operation relevant to the submitted attempt joined by unique step ID, and an
exact target/path match. Query operations and filter values are independent and
are never used as attempt provenance. Targets come from the submitted attempt,
its requested and worker-observed paths, and the host's after-orchestration
`attempt.path_diagnostics` forms; each admitted source is named in
`matching_evidence.path_sources`, the host forms as
`runner_host.after_orchestration.<form>`. A kernel record names the resolved
path, so a target reached through a symlink (such as `/etc/hosts`) correlates
through `realpath_resolved`, and a created or unlinked entry through
`parent_realpath_resolved`. Host forms require a valid compact block with that
exact observer and phase, and an input equal to both the submitted target and
the reported requested path. Invalid blocks contribute no host path matches;
independent submitted, requested and observed paths remain eligible.
Supported operations are:

| Attempt | Relevant event operations |
| --- | --- |
| file open_read/access | file-read-data |
| file open_write | file-write-data |
| file create | file-write-create or file-write-data |
| file unlink | file-write-unlink |
| mach_lookup bootstrap_look_up | mach-lookup |
| sysctl read | sysctl-read |
| exec spawn | process-exec, worker PID only |

There are no wildcard or prefix aliases. Missing/unknown operations or ambiguous
step-ID joins stay unmatched. Create can create a new file or open an existing
one for writing. A missing completed attempt does not prevent a candidate
association: a denial can precede interrupted publication.

Validator `sandbox_check` queries can generate denial records naming the worker
PID before any attempt begins. A matching target is therefore not proof that a
record came from its paired attempt, and a PID match can reflect an ordinary
denied probe followed by an unrelated self-signal or crash. Some denied attempts
have no available log record; requesting the full interval does not guarantee
complete delivery.

### Running specimens in parallel

Each run is its own controller, XPC host, worker and validator. Four processes
per run, plus any exec children, count against the per-user process table, and
a failed spawn is reported as `worker_spawn_failed` or `validator_spawn_failed`
with the native return code (see the
[outcome catalog](#normalized_outcome-catalog)). Resource delays can exhaust
the separate budgets in the [limits inventory](#limits): client RPC expiry
produces `xpc_timeout`, while a delivered host sentinel-timeout reply reports
`runner_timeout`. Worker or validator limits can also leave incomplete
observations; read the available lifecycle evidence. Denial records are
matched to the worker by PID inside the padded window with no protection
against PID reuse: heavy process churn makes a reused PID inside that window
more plausible, so read candidate associations under
[Denial-log correlation](#denial-log-correlation) with that in mind. The
denial log's shared channel is described in the
[Questions](#can-i-evaluate-specimens-in-parallel), and the pacing of one
installed external runner under [External runners](#external-runners-byoxpc).

### Troubleshooting

- Service not found: run `policy-witness runner list` and confirm the service name.
- System scope install fails: use `--scope user` or run with admin privileges.
- Verify fails with no reply: check launchd state and the service plist.
- BYOXPC crashes at launch: confirm `XPC_SERVICE_PATH` is set and the bundle is a valid XPC service (`CFBundlePackageType=XPC!`).
- `normalized_outcome` is `runner_failed`: inspect the published-state diagnostic
  and independent `runner_subprocess` observations. A signal or missing report
  may leave the underlying cause unknown. Completed predictions, attempts and
  captured denial events remain usable for their own claims.
- `data.runner_sandbox_diagnostics` separates process disposition from capture
  status and correlation. Capture can be disabled, unavailable, or captured
  without a match; none proves policy played no role. Successful runs also
  retain capture. See [Denial-log correlation](#denial-log-correlation).
- `normalized_outcome` is `worker_spawn_failed`: the host could not
  `posix_spawn` the worker. Verify the bundle is signed and on a writable
  filesystem; `pgrep -fl PWRunner` should show no stragglers.
- If you are running inside a sandboxed automation harness, XPC lookup can be blocked;
  run from a normal Terminal to confirm behavior.

Common decode errors (quick fixes)
- `missing field 'policy'`: add a top-level `policy` object with `format` and `sbpl_source`.
- `keyNotFound(... "specimen_id" ...)`: add a top-level `specimen_id` string.
- `unknown field 'path_membership'`: path rules belong in `policy.sbpl_source` as SBPL, not as JSON fields.
- `runner.mode=debuggable` or top-level `instrumentation` field rejected:
  these are not supported. Install a BYOXPC runner with the entitlements
  you need and select it via `runner.id` or `runner.service`.

## External runners (BYOXPC)

Use this when you need entitlements that are not in the built-in runner.
BYOXPC is the only external runner kind.

### What you need

- A runner `.xpc` bundle to sign (typically a copy of `PWRunner.xpc`).
- A signing identity: a **Developer ID Application whose Team ID matches the app**
  (see [Caller authentication and ad-hoc signing](#caller-authentication-and-ad-hoc-signing)).
- An entitlements plist.
- A logged-in GUI session (launchd bootstrap is not available from non-GUI shells).

### Install a BYOXPC runner

This sequence is the one the project's own tests exercise and is the
recommended starting point. Adjust `APP` to wherever `PolicyWitness.app` is
installed.

```sh
APP="/Applications/PolicyWitness.app"
PW="$APP/Contents/MacOS/policy-witness"
IDENTITY="Developer ID Application: Your Name (TEAMID)"
ENT="$PWD/path/to/your-byoxpc-entitlements.plist"
BYO="$PWD/runtime/byosig/instances/PWRunner.byoxpc.xpc"

mkdir -p "$(dirname "$BYO")"
rm -rf "$BYO"
cp -R "$APP/Contents/XPCServices/PWRunner.xpc" "$BYO"

$PW runner install --kind byoxpc \
  --bundle "$BYO" \
  --identity "$IDENTITY" \
  --entitlements "$ENT" \
  --scope user

$PW runner verify --service-name com.yourteam.policy-witness.PWRunner --timeout-ms 2000
```

Notes:
- Use `--allow-adhoc` only for a local runner whose caller-auth keys have been
  removed; see [Caller authentication and ad-hoc signing](#caller-authentication-and-ad-hoc-signing).
- Use `--scope system` if you want a system-wide service (requires admin).
- Use `--skip-bootstrap` if you will run `launchctl` manually.
- Use `--env KEY=VALUE` to set launchd `EnvironmentVariables` (for `DYLD_*`).
- BYOXPC service name must match the bundle's `CFBundleIdentifier` (no override).
- The bundle must be a valid XPC service (`CFBundlePackageType=XPC!`); plain
  binaries are rejected at install time. The executable is derived from
  `<bundle>/Contents/MacOS/<CFBundleExecutable>`.
- `--entitlements` requires either `--identity <id>` or `--allow-adhoc` so the
  supplied entitlements are actually re-embedded into the binary. Passing
  `--entitlements` without one of those is rejected — the registry would
  otherwise record entitlements that the kernel will not enforce.

The install command saves a `pending` registry record before writing its launchd
plist, then bootstraps and marks the record `installed`. With `--skip-bootstrap`,
plist creation completes installation; loaded state is reported separately.
Errors after the pending save retain ownership for recovery. Pending runners
can be listed, inspected and removed, but cannot be selected for specimens. The registry's `entitlements` field always
reflects what's embedded in the binary (read back via `codesign -d --entitlements`),
not what was supplied on the command line.

### Caller authentication and ad-hoc signing

The shipped `PWRunner.xpc` has caller authentication enabled in its Info.plist
(`PWRunnerRequireSignedCaller`), and the runner authenticates the caller by
comparing the caller's **Team ID** to its own. A BYOXPC runner made by copying
that template inherits the check, which constrains how you may sign it:

- **Signed runner (default, recommended):** sign the copy with a **Developer ID
  whose Team ID matches the app** (so the runner's team equals `pw-runner-client`'s).
  `runner verify` returns `ok`.
- **Ad-hoc / local runner:** ad-hoc signatures have **no Team ID**, so a runner
  that keeps the caller-auth keys rejects every connection with
  `NSXPCConnectionInvalid` (reported as `normalized_outcome: xpc_error`). To run
  ad-hoc, first remove `PWRunnerRequireSignedCaller` and
  `PWRunnerAllowedIdentifiers` from the copied bundle's Info.plist, then
  `--allow-adhoc`. Such a runner accepts any local caller — appropriate for local
  testing, not for a trust boundary.

Symptom cheat-sheet: `xpc_error` right after install usually means an ad-hoc (or
wrong-team) runner failing the signed-caller check; `xpc_timeout` means the host
reply was not received before the deadline. A launch crash is one possible
cause; the timeout alone does not establish it.

### Verify the runner

```sh
$PW runner verify --service-name <service-name>
```

`runner verify` sends a fixed allow-all specimen with no probe steps to the
runner on the client's stdin, as a run does, and reports the runner's PID and
outcome. It defaults to a 5-second timeout; pass `--timeout-ms <n>` for slow
cold-spawn cases.

### Use the runner in a specimen

Consecutive runs through one installed runner are paced by launchd: the runner
exits after each specimen, and launchd spawns a job at most once every 10
seconds by default, so a run requested sooner waits for the remainder.

Preferred: include a `runner` object:

```json
"runner": {
  "id": "runner-<id-from-install>",
  "mode": "byoxpc",
  "required_entitlements": [
    "com.apple.security.cs.disable-library-validation"
  ]
}
```

Alternative: select by service name:

```json
"runner": {
  "service": "com.yourteam.policy-witness.PWRunner",
  "mode": "byoxpc"
}
```

`runner.mode` is optional; when present it must equal `byoxpc` for external
runners. Valid modes: `standard`, `byoxpc`. `required_entitlements` enforces
a superset check before dispatch.

Quick smoke request (save as `/tmp/pw_byoxpc_smoke.json`):

```json
{
  "schema_version": 4,
  "specimen_id": "byoxpc_smoke",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (deny default)"
  },
  "probe_plan": [],
  "runner": {
    "service": "com.yourteam.policy-witness.PWRunner",
    "mode": "byoxpc"
  }
}
```

Then run:

```sh
$PW run /tmp/pw_byoxpc_smoke.json --timeout-ms 20000
```

### List, validate, or remove runners

```sh
$PW runner list
$PW runner validate
$PW runner reconcile
$PW runner remove --id runner-<id>
```

External runners install a launchd background item. `runner remove` first moves
the record from `runners` to durable `pending_cleanup`, then checks ownership
before bootout or plist removal. It retires recovery only after verifying both
service and plist absence, waiting up to a second for launchd to finish tearing
the job down after a bootout. Failed or uncertain cleanup reports `data.warnings`
and `data.cleanup_retained: true`, with the retained record. Retrying the same
remove command continues recovery, including when the plist has already gone.
`--skip-bootout` keeps recovery until service absence is observed.

`runner list` includes both collections. `runner reconcile` reports recorded
state, observed service/plist presence and ownership, and scans LaunchAgents and
readable LaunchDaemons for unregistered candidates. A label prefix is evidence
for reporting only. Inspection failures remain unknown. Reconcile never removes
anything. Use the recorded `bundle_path` to find a test runner's staging directory
and durable `session.json`, even after its original test output is deleted.
Test bundles remain staged until cleanup verifies service/plist absence and
registry retirement; retry the session cleanup using its durable state path if
bundle deletion was interrupted.

Modifying commands use a stable advisory lock beside the registry and atomic
JSON replacement. One registry admits one modifier at a time; read-only commands
remain available. Never remove the lock file while a command might hold it.

`runner validate` re-reads each registry entry's on-disk signature and
entitlements (registry-internal only — it does not reconcile against launchctl
or `LaunchAgents/`).

`runner status`, `runner verify`, and `runner remove` emit an envelope with
`result.normalized_outcome = "not_found"` and exit code 2 when the lookup key
isn't present in the registry; the envelope `kind` still matches the operation
so consumers can dispatch by `kind` and then branch on `normalized_outcome`.

For an unregistered candidate, inspect `runner reconcile` and verify its exact
service, executable, scope and plist ownership before any manual cleanup:

User scope:

```sh
launchctl bootout "gui/$(id -u)/<service-name>"
rm -f "$HOME/Library/LaunchAgents/<service-name>.plist"
```

System scope:

```sh
sudo launchctl bootout "system/<service-name>"
sudo rm -f "/Library/LaunchDaemons/<service-name>.plist"
```

Registry location:

```
~/Library/Application Support/PolicyWitness/runners.json
```
