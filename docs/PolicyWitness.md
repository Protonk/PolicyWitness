# PolicyWitness User Guide

PolicyWitness records `sandbox_check` queries and attempted operations under
macOS sandbox policies. When prediction is available, the validator queries
the worker's PID; the worker attempts its operation after applying the policy
and receiving release from the host. Each step records available results, missing
observations, submitted-scope relations and ordering. The controller adds
request identity, source hashes, imports, runner and app provenance, host
facts and hashes of selected binaries outside the app manifest. Retain the
specimen alongside the envelope for the full input. Optional log capture adds
kernel denial records with candidate associations. The
[comparison reading rules](#reading-a-comparison-record) explain how to interpret
the channels together.

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

PolicyWitness requires macOS 26 on Apple Silicon: every executable it ships is arm64-only macOS code, so an Intel Mac cannot run it. Quick start uses the built-in standard runner. If you need entitlements the standard runner doesn't ship — debug-attach, DYLD env, custom dylib loading, JIT — see [External runners (BYOXPC)](#external-runners-byoxpc) below.

Set a convenience variable, adjusting the path to wherever `PolicyWitness.app` is installed:

```sh
PW="/Applications/PolicyWitness.app/Contents/MacOS/policy-witness"
```

Create a specimen:

```sh
cat > /tmp/pw_specimen_file_read_deny.json <<'JSON'
{
  "schema_version": 5,
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

Yes, for a bounded file-read experiment. A fresh issuer outside the specimen sandbox prepares one `com.apple.app-sandbox.read` token under its ordinary authority. Explicit phases can consume it once and release the returned handle once in the same worker under one fixed policy. Issuance, delivery, native lifecycle results, predictions and fresh-descriptor reads remain separate observations. A successful consume or release does not establish effective permission or revocation. Raw tokens never enter the request or reply. See [sandbox extensions](#sandbox-extensions).

### Which happens first, the prediction or the attempt?

A `query_first` comparison identifies an eligible native prediction collected before the worker acknowledged that phase's host release, which precedes its actions. Missing or unusable predictions and death before acknowledgement remain `unestablished`. Query collection closes even when validator cleanup is unconfirmed; a surviving validator cannot add later records. Earlier actions in the phase, including consumption or release, can change what a later attempt encounters. Use another phase for a new query collection; neither interval is a common state snapshot.

### How do I read the denial log?

As optional, possibly incomplete evidence. The kernel's sandbox log intermittently omits denial lines for any sandboxed process, so a missing record never establishes that an operation was allowed. The validator queries `sandbox_check` with `SANDBOX_CHECK_NO_REPORT`, so a denial record naming the worker PID comes from an attempt, never from a prediction. A candidate association (`sandbox_log_capture.step_denies`) says that a record's PID, operation and path match a submitted attempt; it does not say the attempt produced that record, and it changes no comparison field.

### How long does a run take?

One runner client span plus, by default, one unified-log scan, plus the controller's own startup and output. Your reply records the first two: the runner's work is `data.runner_client.ended_at_unix_ms` minus `started_at_unix_ms`, and the scan is `data.sandbox_log_capture.supervision.elapsed_ms`.

### Can I evaluate specimens in parallel?

Yes and no. Each specimen is evaluated in its own runner and worker processes, but PolicyWitness does not guarantee relative scheduling between concurrent runs or complete denial-log evidence. If an experiment depends on timing or log availability, run the specimens separately. N.B. Runs through one installed [external runner](#external-runners-byoxpc) are serial and queue behind launchd's respawn throttle, which the generated plist sets to one second.

<!-- END COPIED QUESTIONS -->

## Specimen format

### Top-level shape

Top-level fields:

- `schema_version`: integer-valued number equal to the current request schema
- `specimen_id`: string
- `run_kind`: string (optional)
- `policy`: object
- Exactly one non-null plan form: `probe_plan` (array of paired steps) or
  `phases` (ordered array of phase objects)
- `runner`: object (optional; select runner mode and external runners)
- `extensions`: array (optional; file-extension declaration, requires `phases`)

Minimal skeleton (copy/paste):

```json
{
  "schema_version": 5,
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
- All path rules live inside `policy.sbpl_source`.
- `probe_plan` may be empty when you only want to exercise sandbox
  apply (the validator child is only spawned when there are probes
  to query).

### Ordered phases

Use `probe_plan` for one query collection followed by its attempts. It becomes
one reply phase named `main`, including when the plan is empty. To collect again
after earlier actions, supply `phases` instead. Each phase has a nonempty unique
`phase_id` and an `actions` array. Each ordinary action has the same shape as a
probe-plan step: `step_id`, `sandbox_check` and `attempt` are all required.
Step IDs are unique across the entire specimen. Empty action arrays are allowed;
the phase array itself must be nonempty.

```json
{
  "schema_version": 5,
  "specimen_id": "two_reads",
  "policy": { "format": "sbpl", "sbpl_source": "(version 1) (allow default)" },
  "phases": [
    { "phase_id": "first", "actions": [
      { "step_id": "read1",
        "sandbox_check": { "operation": "file-read-data", "filter": { "kind": "path", "value": "/etc/hosts" } },
        "attempt": { "kind": "file", "action": "access", "target": "/etc/hosts" } }
    ] },
    { "phase_id": "second", "actions": [
      { "step_id": "read2",
        "sandbox_check": { "operation": "file-read-data", "filter": { "kind": "path", "value": "/etc/hosts" } },
        "attempt": { "kind": "file", "action": "access", "target": "/etc/hosts" } }
    ] }
  ]
}
```

Query collection closes before any actions in that phase begin, even if some
predictions are unavailable. Actions then
run in declaration order, and the next collection begins after phase completion.
The worker and its once-applied policy remain the same. File identity and
permissions can change during a phase's interval.

Path-query eligibility is checked afresh at each boundary. If an earlier action
unlinks a target, a later path query can be unavailable while its paired attempt
still runs and reports its own result. Such a pair has `order: unestablished`;
phase completion and arrival still describe the observed progression. Validator
failure or exhausted collection allowance can likewise leave predictions missing.
Worker loss or an expired worker release wait stops further progression.

At most <!-- span limits.phase_count.value -->8<!-- /span --> phases and <!-- span limits.probe_steps.value -->256<!-- /span --> total actions fit one specimen; phases do not multiply the action or query allowance. The
[limits](#limits) describe cumulative collection and per-phase wait bounds.

### Sandbox extensions

An extension specimen declares a local token reference and a target path, then
places native consume/release actions in explicit phases. The issuer prepares
one `com.apple.app-sandbox.read` token outside the specimen sandbox under ordinary
authority. The worker applies the submitted policy once and keeps that policy
through every phase. Record native issuance, consumption and release alongside
fresh-descriptor reads to observe access at each stage.

| Input | Meaning |
| --- | --- |
| `extensions: [{"token_ref": "token", "target": "/absolute/path"}]` | A local reference and issuance target; raw token bytes and caller-selected classes are not accepted. |
| `{"step_id": "consume", "extension": {"operation": "consume", "token_ref": "token", "handle_ref": "handle"}}` | Consume the declared token and associate an observed native handle with a distinct local reference. |
| `{"step_id": "release", "extension": {"operation": "release", "handle_ref": "handle"}}` | Release the earlier consume result if it supplied a handle. No token reference belongs on release. |

The limits are <!-- span limits.extension_declarations.value -->1<!-- /span -->
declaration, <!-- span limits.extension_consumes.value -->1<!-- /span --> consume
and <!-- span limits.extension_releases.value -->1<!-- /span --> release across
the entire specimen. References are nonempty and at most <!-- span limits.extension_reference.value -->63<!-- /span --> UTF-8 bytes.
Declaration targets have their own <!-- span limits.extension_target.value -->1,023<!-- /span -->-byte cap, distinct
from ordinary attempt targets. References and paths cannot contain NUL.
Unknown references, duplicate token/handle names, release before consume,
repeated actions, unknown fields and mixing an extension declaration with exec
are refused before execution. Additional declarations are refused even when
placed in separate phases. The lifecycle actions share the total action cap.

Omitting consumption or release is allowed. Issuance/delivery without consumption,
consumption without release, and phases containing only lifecycle actions retain
those distinctions. An action is either an ordinary query/attempt pair or a
lifecycle action. Lifecycle actions carry available native results and
publication evidence. Query collection closes before any of that phase's actions,
including when collection fails. A read after a consume in the same phase has
any received prediction from before the consume. Place the read in a later phase
to collect again.

Use an investigator-owned file in a temporary directory for a repeatable example:

```sh
PW=/Applications/PolicyWitness.app/Contents/MacOS/policy-witness
PW_EXTENSION_DIR=$(mktemp -d /private/tmp/pw-extension.XXXXXX)
printf 'extension witness\n' > "$PW_EXTENSION_DIR/target"
cat > "$PW_EXTENSION_DIR/request.json" <<JSON
{
  "schema_version": 5,
  "specimen_id": "extension_lifecycle",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)(allow default)(deny file-read-data)(allow file-read-data (extension \"com.apple.app-sandbox.read\"))"
  },
  "extensions": [{"token_ref": "token", "target": "$PW_EXTENSION_DIR/target"}],
  "phases": [
    {"phase_id": "before", "actions": [
      {"step_id": "read_before",
       "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "$PW_EXTENSION_DIR/target"}},
       "attempt": {"kind": "file", "action": "read_fresh", "target": "$PW_EXTENSION_DIR/target"}},
      {"step_id": "consume", "extension": {"operation": "consume", "token_ref": "token", "handle_ref": "handle"}}
    ]},
    {"phase_id": "consumed", "actions": [
      {"step_id": "read_consumed",
       "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "$PW_EXTENSION_DIR/target"}},
       "attempt": {"kind": "file", "action": "read_fresh", "target": "$PW_EXTENSION_DIR/target"}},
      {"step_id": "release", "extension": {"operation": "release", "handle_ref": "handle"}}
    ]},
    {"phase_id": "released", "actions": [
      {"step_id": "read_released",
       "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "$PW_EXTENSION_DIR/target"}},
       "attempt": {"kind": "file", "action": "read_fresh", "target": "$PW_EXTENSION_DIR/target"}}
    ]}
  ]
}
JSON
"$PW" run "$PW_EXTENSION_DIR/request.json" --no-log-capture > "$PW_EXTENSION_DIR/run.json"
```

Inspect `extensions`, `extension_events`, `phases` and `steps` under
`data.runner_result`. Compare successful `fresh_read.content_hex` with the file's
known bytes, and retain failed reads and the native release result independently.
The example's phase names describe action placement. Keep the request, file
and envelope together when investigating the result.

Target preparation records the submitted path, `realpath` result and metadata
before issuance. Admission accepts targets regardless of owner or file type,
including symlinks. Resolution/metadata failure is retained as preparation
evidence. A symlink can resolve successfully, and replacement after preparation
can make later access
reach another object. Ordinary query and attempt targets stay as submitted.
`read_fresh` opens in the worker after application, records descriptor metadata,
reads at most <!-- span limits.fresh_read_bytes.value -->64<!-- /span --> bytes
once, and closes it. The returned bytes are a bounded prefix.

A current runner bundle without the issuer returns `bad_request` with
`extension_issuer_unavailable`; an issuer without the native issuance API returns
`extension_api_unavailable`. Native refusal,
issuer death, timeout, malformed publication and unconfirmed cleanup retain their
own issuance evidence and withhold delivery. Worker-side API absence is an
unavailable lifecycle action. An issued token and a delivered token remain
separate observations. Raw token bytes travel only through a bounded transient
channel, never the request, argv, environment, reply or ordinary diagnostics.
A worker delivery failure is `channel_rejected` or `local_setup_failed`, and
its `delivery_failure` account names the failing stage with the native return
and saved errno when a native call supplied them; a cleanup failure after the
first failure is recorded separately and never changes the status.
The host clears its own mapping before replying. Copies held inside native
libraries are outside that observation. BYOXPC uses its own bundle-local issuer,
[signed without the worker's entitlements](#install-a-byoxpc-runner).

### Try an accepted request and a refusal

This specimen asks a sandbox query and attempts to create an empty file. Use a
fresh directory so you can observe whether the file was created. Adjust `PW`
to your installed app; the commands need no repository files or extra tools.

```sh
PW="/Applications/PolicyWitness.app/Contents/MacOS/policy-witness"
PW_EXAMPLE_DIR=$(mktemp -d /private/tmp/pw-input.XXXXXX)
cat > "$PW_EXAMPLE_DIR/request.json" <<JSON
{
  "schema_version": 5,
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
an independent observation of the file effect. A query about an absent path
can report
`prediction_unavailable` while the creation attempt succeeds.

Now make a copy with a new target and the deliberately misspelled field
`capture_compiled_profiel`. The new target lets you check that refusal prevents
an otherwise valid create from running:

```sh
sed -e 's|/created"|/refused"|g' \
    -e 's|"format": "sbpl",|"format": "sbpl", "capture_compiled_profiel": true,|' \
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
  "path": ["policy", "capture_compiled_profiel"]
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
| Observed effects | A valid create encounters a permission failure, or succeeds and produces a file. | Read the attempt evidence and inspect the target to establish what happened during execution. |

Unknown attempt combinations and filter names refuse the whole specimen before
worker or validator creation. Recognized queries with unavailable predictions
still permit supported attempts. A request can therefore be useful even when
the query channel cannot answer. For capacities and units, see [Limits](#limits).

### Correcting a refused request

Use `data.request_failure.code` to classify the refusal and `path` to locate
the field. Human-readable `result.error` supplies context; programs should not
parse that prose. Path components are exact keys and decimal array positions:
`["probe_plan", "1", "attempt", "args"]` identifies the second step's arguments.
`[]` names the root; `null` means the location was withheld. Read the run's
outcome in `result.normalized_outcome`. Capacity refusals also retain
counts and positions in `data.runner_result.admission_failure`.

Three field relationships commonly matter:

| Field | When it applies |
| --- | --- |
| `attempt.args` | A non-null array, including `[]`, is accepted only for `exec/spawn`. |
| `sandbox_check.filter.value` | `none` accepts only absence or null. Other recognized kinds require a nonempty string. |
| `policy.capture_nonce` | Requires `capture_compiled_profile: true`; enabled capture requires a fresh nonce of 32 lowercase hexadecimal characters. |

A refusal identifies one problem. Correct it and rerun; another problem may
then be reported. `bad_request` exits 1 and executes no probe steps. Missing or
unreadable files and unavailable runners have their own failure outcomes.

The request's `schema_version` names its accepted shapes and meanings. It is
separate from `(version 1)` in the SBPL source and from the app's build number.
Removing a field, requiring a new one, or changing an action's meaning requires
a revised contract and corresponding request changes. Review those changes
before replacing an unsupported marker with the current one.

An implementation correction that honors the documented instruction can keep
the marker and the same request, even when observations change. Additions can
also preserve the marker: existing requests remain valid, while older builds
can refuse newly added fields or actions. Capacity and observations can vary
across builds and macOS versions sharing a marker.

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

An SBPL policy may set `capture_compiled_profile: true` and a fresh per-application
`capture_nonce` (32 lowercase hexadecimal characters). The runner adds
`data.runner_result.compiled_profile`, with its own `schema_version: 2`. A
`status: "captured"` receipt requires `producer: "worker"` and
`capture_stage: "before_apply"`. It contains `worker_pid`, `request_nonce`, `profile_type`,
`bytecode_length`, `bytecode_b64`, `bytecode_sha256`, `source_length`,
`source_sha256`, `parameter_count` and `params_sha256`. These are sensitive outputs:
the caller must arrange restricted receipt storage before opting in.
A non-null nonce without enabled capture is a `bad_request`.

The C worker copies the bytecode from the same compiler-result pointer it passes
to `sandbox_apply`, before applying. The host requires successful apply,
complete worker exit, matching PID/nonce, lengths, input identities and payload
checksum before publication. Missing capture, failed apply, worker death or
capture corruption is unavailable.
An unavailable nested receipt has a reason and no bytecode, producer or capture
stage, or is absent if no worker result was obtained. An opt-in request alone
does not establish that capture ran. Readers require the nested receipt version
and the exact producer/stage values for a captured receipt.

Application is reported separately by `sandboxed_after_apply` and any published
`runner_subprocess.worker_evidence.failure`. An unavailable capture does not
establish application failure. The receipt identifies compiler output; successful
application and subsequent access observations supply different evidence. None
is a readback of the kernel's effective policy.

Source identity hashes the UTF-8 C string consumed by compilation. Parameter
identity is SHA-256 of the little-endian 32-bit pair count followed by sorted
32-byte pair digests. Each pair digest hashes LE32 key-byte count, key UTF-8 bytes,
LE32 value-byte count, then value UTF-8 bytes. The worker hashes its private copy
of the strings passed to `sandbox_set_param`; the host independently recomputes
the identity. Consumed values determine the identity independently of pair
ordering. Embedded NUL inputs cannot qualify as matching complete requested inputs. Consumers must join
the nonce and worker identity to their own request and compare actual decoded
bytecode with any independently retained expected object.

### SBPL check (`sbpl-check`)

`sbpl-check` is a host-side SBPL compiler. The C worker exercises the
policy itself; its worker failure record identifies the failed operation and
available native result, summarized as `runner_failed`. The controller runs
`sbpl-check` only after `xpc_error`, retaining its independent result under
`data.policy_check`. That fallback says nothing about how far a missing worker
progressed or why its reply was lost. You can also run the tool directly for the
diagnostics below.

The native compiler determines the verdict and handles missing or unused
parameters. The helper copies its diagnostic unchanged. Supplied `policy.params`
entries reach the compiler through `sandbox_set_param`.

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
the last native stage attempted. An absent or empty
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

Read `compile.error` for the compiler's diagnosis. For example, without a supplied
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
`data.policy_check.envelope`; `tool_exit_code` records the process exit
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
the inventory while native compilation proceeds independently.

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
spliced bytes (as does `sbpl-check` if the `xpc_error` path runs it).

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
  "no augments." The field is stripped before forwarding.

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

  **This baseline adds an unconditional file-read allow.**
  The kernel reads the target binary's bytes before exec; `(allow file-read*)`
  covers any caller-selected helper path. Because augments are
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

- Capacities are inclusive maxima unless the row says otherwise: a step ID
  of <!-- span limits.step_id.value -->63<!-- /span --> UTF-8 bytes fits, and any longer step ID exceeds its limit. UTF-8 counts measure decoded
  strings rather than JSON escapes or characters. Rows labeled `bytes` specify
  whether they count raw output, bytecode or a calculated allowance. String
  capacities exclude any terminating NUL.
- Time rows distinguish defaults, elapsed monotonic deadlines, nominal waits
  and unenforced allowances. Monotonic deadlines are unaffected by wall-clock
  adjustments. The C worker's release wait and exec allowances count continuous
  Mach time, which includes system sleep; host, validator and controller waits
  keep their own clocks, and no worker time is compared with them. Nominal waits
  can take longer than their listed duration; each row describes what expiry does.
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
| Total actions and queries (`probe_steps`) | 256 items | `probe_plan` or `phases.actions` | Total ordinary pairs and extension lifecycle actions across the complete plan. Lifecycle actions occupy slots but supply no query; phases do not multiply this cap. Excess returns `bad_request` with `admission_failure`. | Fixed. |
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
| Test-seam executable paths (`test_override_path`) | 1,023 UTF-8 bytes | `_test_overrides.worker_executable_path`, `validator_executable_path` or `issuer_executable_path` | Each executable override path. Every path that fails byte or NUL admission is omitted from a refusal echo, even when another field is refused first. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Specimen phases (`phase_count`) | 8 items | `phases` | Explicit phases in one request; probe_plan normalizes to one phase. Excess returns admission_failure before any child. | Fixed. |
| Phase identity (`phase_id`) | 63 UTF-8 bytes | `phase_id` | UTF-8 payload bytes in each phase_id. NUL is refused independently. Excess returns admission_failure without echoing the refused identity. | Fixed. |
| Extension declarations (`extension_declarations`) | 1 item | `extensions` | Across the complete specimen, including separate phases. Omitted actions are legal. Additional declarations return `admission_refused`. | Fixed. |
| Consume actions (`extension_consumes`) | 1 item | `phases.actions.extension` | Across the complete specimen, including separate phases. Omitted actions are legal. A repeated consume returns `repeated_consume`. | Fixed. |
| Release actions (`extension_releases`) | 1 item | `phases.actions.extension` | Across the complete specimen, including separate phases. Omitted actions are legal. A repeated release returns `repeated_release`. | Fixed. |
| Token and handle references (`extension_reference`) | 63 UTF-8 bytes | `extensions.token_ref` or `phases.actions.extension.token_ref` / `handle_ref` | Each nonempty local token or handle reference; embedded NUL is refused. Excess returns `admission_refused`; references must also satisfy declaration and action order. | Fixed. |
| Issuance target path (`extension_target`) | 1,023 UTF-8 bytes | `extensions.target` | Submitted target path, before host realpath preparation; excludes terminating NUL. This is separate from an ordinary attempt target. Excess or embedded NUL returns `admission_refused`. Resolution and metadata failures remain preparation evidence. | Fixed. |

### Execution budgets

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Host reply flush delay (`host_exit_delay`) | 50 milliseconds | Delay scheduled by the terminal request owner after replying. The unsandboxed host exits when the delay elapses. A second connection reaching the retiring host meets the terminal claim. | Fixed. |
| Runner verification wait (`runner_verify_wait`) | 5,000 milliseconds | Default allowance for the fixed runner verify specimen, shared across host re-acquisition and client waits. An expired client RPC returns its timeout outcome; acquisition deadline exhaustion returns the last qualifying already_ran refusal. An admitted verification consumes its single-use host. | Flag `--timeout-ms` on `runner verify`. |
| Worker policy delivery (`worker_policy_transfer`) | 5,000 milliseconds | One absolute monotonic deadline starting immediately after spawn; partial writes and interrupted calls do not restart it. Expiry closes the input pipe and enters host cleanup with policy_transfer_timeout and policy_transfer_deadline; no write errno is invented. The worker, reaching EOF, publishes the count it read beside the host's expected length and refuses a different length before compiling; an observed refusal takes worker-failure precedence. | Fixed; internal driver controls may shorten it. |
| Worker readiness hint wait (`worker_ready_wait`) | 1,000 milliseconds | Nominal wait for the worker readiness hint. Expiry can leave `runner_subprocess.ready_byte_received: false` while the run continues. | Fixed. |
| Worker publication wait (`worker_sentinel_wait`) | 120,000 milliseconds | Nominal wait for worker results after the readiness-hint wait. Validator collection is outside this allowance; the listed duration is not a total runtime limit. Expiry can yield `runner_timeout` with partial evidence and reported cleanup results. | Fixed. |
| Worker exit grace (`worker_exit_grace`) | 1,000 milliseconds | Elapsed monotonic wait for an unreaped worker after the host stores an exit request. Expiry requests `SIGKILL`. Termination and reap failures remain reported. | Fixed. |
| Worker release wait (`worker_proceed_wait`) | 60,000 milliseconds | Sampled continuous time for each phase release after the worker arrives, converted once before application to a ceiling tick allowance. Continuous time includes system sleep. Expiry records the phase index and milliseconds and prevents its actions. An unusable sample, an earlier rejected sample or an unrepresentable plan exclusion records a local timing refusal with its reason instead; neither invents a native result or errno. Earlier published phase evidence remains. | Fixed. |
| Nominal release margin (`validator_release_margin`) | 5,000 milliseconds | Informative allowance between the validator budgets and worker release wait. No separate timeout or refusal occurs at this value. | Not enforced; no flag. |
| Validator I/O test override floor (`validator_io_override_floor`) | 50 milliseconds | Minimum proposed `_test_overrides.validator_io_timeout_ms`. Smaller supplied values propose 50 ms; the reply mirrors the supplied value. The remaining aggregate collection allowance caps the effective deadline, including below this floor. | Fixed. |
| Validator I/O deadline (`validator_io_wait`) | 30,000 milliseconds | Default elapsed monotonic deadline for one phase’s query delivery and verdict collection, capped by the remaining aggregate collection allowance. Received verdicts survive an I/O timeout; cleanup results remain reported. | Fixed. |
| Validator exit grace (`validator_exit_grace`) | 1,000 milliseconds | Nominal wait for validator exit after collection closes. Expiry requests `SIGKILL`. Termination and reap failures remain reported. | Fixed. |
| Exec child deadline (`exec_child_wait`) | 10,000 milliseconds | Continuous time after successful spawn, limited by the remaining `exec_attempt_budget`. Expiry fails the attempt while preserving any observed natural exit code. An unusable sample or unrepresentable child deadline ends observation as a local timing fault with no errno. Cleanup results remain reported; an observed leader exit does not establish that every descendant stopped. | Fixed. |
| Exec attempt budget (`exec_attempt_budget`) | 115,000 milliseconds | Continuous time from the worker origin before setup, shared by exec steps, including worker setup and intervening work but excluding each acknowledged release wait. Continuous time includes system sleep. Exhaustion refuses a later spawn with `exec_failed` and `ETIMEDOUT`, no `child_pid` and no sandbox attribution. An unusable sample refuses spawn with no errno, or after spawn records a local timing fault beside any native error; after a rejected sample, later spawns are refused. Blocking spawn and non-exec operations may outlast this allowance. | Fixed. |
| Exec child reap grace (`exec_reap_grace`) | 1,000 milliseconds | Continuous-time allowance to confirm an exec child's exit after observation ends. Expiry, an unusable sample or a wait error leaves reaping unconfirmed and supplies no invented exit status; an unusable clock still permits the immediate exit check. Failed group termination leaves only an immediate exit check. This is not a total cleanup runtime limit. | Fixed. |
| Runner RPC wait (`client_rpc_wait`) | 240,000 milliseconds | Default reply allowance; external runner acquisition shares it across refused attempts, retirement waits and the final client. Each client capture records its own wall-clock span. An expired client RPC yields `xpc_timeout`. Exhaustion while waiting after a qualifying external `already_ran` returns the last refusal. Inner worker and validator budgets do not expand. | Flag `--timeout-ms`, floored at 1 ms; values above this default are permitted. |
| Runner removal teardown wait (`runner_remove_teardown_wait`) | 1,000 milliseconds | Nominal wait for a removed BYOXPC service to disappear from launchd. The cleanup observation records the service checks and the wait. A service still listed at expiry retains its cleanup record with a warning; a later `runner remove` or `runner reconcile` continues recovery. | Fixed. No wait when the removal issued no bootout. |
| External runner respawn throttle (`byoxpc_throttle_interval`) | 1 second | `ThrottleInterval` in every launchd plist that `runner install` generates. The host exits after each specimen and launchd starts the job at most once per interval; the wait is counted from the previous launch, not from the previous exit. A request to an installed external runner that arrives within the interval of the previous launch waits for the remainder before a host serves it. Without the key launchd applies its ten-second default. A request that reaches a host which is still retiring after its reply meets that host's `already_ran`; the interval does not change that. | Fixed in the generated plist. An installed plist can be edited by hand after `runner remove` and a fresh install; the registry's plist hash then differs and removal reports the ownership disagreement. |
| Aggregate phase collection allowance (`phase_collection_wait`) | 30,000 milliseconds | Cumulative monotonic time spent planning and collecting across all phases. The remaining allowance caps each validator I/O deadline. Cleanup and scheduling can overrun that deadline. After exhaustion, subsequent predictions are unavailable; the worker can still execute released attempts. | Fixed; `_test_overrides.validator_total_timeout_ms` can reduce it to at least 1 millisecond. |
| Issuer collection wait (`extension_issuer_wait`) | 5,000 milliseconds | Monotonic host wait starting after successful issuer spawn, before worker creation. Target preparation and spawn precede this clock; phase collection and worker waits have not started. Expiry requests termination, records native publication and cleanup independently, and withholds delivery. Termination/reaping and scheduling can overrun this wait. | Fixed. |
| Sysctl value-read destination (`sysctl_read_bytes`) | 4,096 bytes | Destination for one post-apply sysctlbyname value read with a non-null buffer; no sizing call or retry. Larger values can fail within this bound. Returned value bytes and post-call length are discarded; a failed call does not diagnose whether capacity was insufficient. | Fixed. |

### Queries and transport

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Validator query payload (`validator_query_payload`) | 65,534 bytes | Serialized JSON bytes for one validator probe, excluding the final LF. JSON escapes count toward this size. An overlong line produces one `parse_error` without a step ID; later lines remain usable. Admitted specimens stay below this limit. | Fixed. |
| Informative reply size bound (`runner_reply_maximum`) | 52,595,368 bytes | Upper bound on the encoded size of one runner JSON reply for this build. No reply is refused at this size; retained output is bounded by `controller_output`. | Not enforced; it sizes `controller_output`. |
| Runner client output (`controller_output`) | 159,383,552 bytes | Captured bytes per stdout or stderr stream from the runner client, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Derived: three times `runner_reply_maximum`, rounded up to a whole 4 MiB; no flag. |
| Log observer stdout (`log_observer_output`) | 33,554,432 bytes | Raw observer stdout bytes, including the JSON report and final newline. Stderr has a separate cap. Overflow retains a bounded raw prefix, with unavailable parsing and correlation. | Fixed. |
| Log show stdout (`log_show_stdout`) | 1,048,576 bytes | Raw bytes from `log show` stdout, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Log show stderr (`log_show_stderr`) | 131,072 bytes | Raw bytes from `log show` stderr, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Log observer stderr (`log_observer_stderr`) | 131,072 bytes | Raw bytes from observer stderr, before text decoding. Overflow stops collection, retains a bounded prefix and withholds correlation. Cleanup results remain reported. | Fixed. |
| Observer JSON structure (`log_reply_structure`) | 262,144 items | Opening object/array delimiters, commas and colons outside quoted strings in the observer reply. Excess retains bounded raw diagnostic text with unavailable parsing and correlation. | Fixed. |
| Observer echoed metadata (`log_observer_metadata`) | 4,096 UTF-8 bytes | Each echoed show argument: predicate, process name, start, end, last, plan, row and correlation ID. Oversized arguments are rejected; oversized reply metadata leaves correlation unavailable. | Fixed. |
| Policy helper output (`policy_helper_output`) | 8,388,608 bytes | Captured bytes per stdout or stderr stream from `sbpl-check`, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Fixed. |
| Rejected validator frame context (`validator_fault_context`) | 256 bytes | Retained prefix of the first rejected validator frame, measured before base64 encoding. `frame_bytes`, `retained_bytes` and `context_truncated` describe how much context was retained. | Fixed. |
| Validator reply frame (`validator_reply_frame`) | 8,192 bytes | UTF-8 bytes in one NDJSON frame, before parsing. An overlong frame is rejected with bounded context; earlier complete records remain. | Fixed. |
| Validator records per query (`validator_records_per_query`) | 2 items | Retained-record allowance is twice the number of queries actually sent in that phase; at most 512 records across a production run. The first excess record produces a decode fault; no excess record enters association. | Fixed. |
| Validator reply storage per query (`validator_reply_bytes_per_query`) | 16,384 bytes | Twice the frame bound per actual query; at most 4,194,304 retained stdout bytes across a production run. The first read crossing the cap closes collection with byte_limit; its cutoff fragment is never decoded as a complete frame. | Fixed. |
| Validator step_id string (`validator_reply_step_id`) | 63 UTF-8 bytes | Bytes in a decoded validator step_id string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator operation string (`validator_reply_operation`) | 127 UTF-8 bytes | Bytes in a decoded validator operation string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator filter_type string (`validator_reply_filter_type`) | 63 UTF-8 bytes | Bytes in a decoded validator filter_type string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator filter_value string (`validator_reply_filter_value`) | 1,023 UTF-8 bytes | Bytes in a decoded validator filter_value string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator outcome string (`validator_reply_outcome`) | 63 UTF-8 bytes | Bytes in a decoded validator outcome string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator error string (`validator_reply_error`) | 511 UTF-8 bytes | Bytes in a decoded validator error string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Transient token storage (`extension_token_storage`) | 16,384 bytes | Fixed token array including its terminating NUL; never part of a retained reply. Empty, oversized or malformed publications cannot supply a consumed token. | Fixed. |
| Maximum token payload (`extension_token_payload`) | 16,383 bytes | Nonempty token bytes excluding the required trailing NUL. Larger native results report `token_oversized`; malformed delivery is unavailable. | Fixed. |
| Transient extension channel (`extension_channel`) | 17,472 bytes | Logical mapped channel with header, resolved path and token array. The OS backing object may round its storage up. Insufficient backing size or invalid channel geometry cannot supply a token. | Fixed. |

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
| Optional compiled-object capture (`compiled_profile`) | 1,048,576 bytes | Raw bytecode bytes in an optional compiled-object receipt, before base64 encoding. Oversized or unsupported objects leave capture unavailable without preventing policy application. | Fixed. |
| Worker observed path (`observed_path`) | 1,023 bytes | Retained bytes in each worker-observed path. Path observation can be absent or bounded; a host-side path diagnostic is a separate observation. | Fixed. |
| Worker attempt error text (`attempt_error`) | 255 bytes | Retained bytes in each worker attempt error message. Error text is bounded; structured result and status fields remain separate. | Fixed. |
| Phase publication storage (`phase_publications`) | 256 bytes | Eight fixed 32-byte phase records within the shared header. The phase cap prevents excess publication storage. | Fixed. |
| Fresh file-read prefix (`fresh_read_bytes`) | 64 bytes | At most one read from a freshly opened descriptor; content_hex encodes only the returned prefix. Longer files remain readable experiments; the bounded result does not claim complete file contents. | Fixed. |

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
  `client_rpc_wait`, which also bounds external host re-acquisition. The worker polling
  window `worker_sentinel_wait`, the validator deadline `validator_io_wait`,
  the release wait `worker_proceed_wait` and the exec budgets keep their own
  values, so no number here is an end-to-end runtime. The reply records the
  client span in `data.runner_client.started_at_unix_ms` and
  `ended_at_unix_ms`; an expired client wait yields `xpc_timeout`.
- Extension issuance precedes worker creation.
  Its <!-- span limits.extension_issuer_wait.value_unit -->5,000 milliseconds<!-- /span -->
  wait starts after the issuer spawns; target preparation and the spawn call
  precede that clock. Issuer cleanup can overrun the wait. This work consumes
  the client's reply window but none of the later worker or phase collection
  budgets. A client timeout does not cancel issuance or its cleanup.
- Phases share one total action/query capacity and a cumulative collection
  allowance of <!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span -->.
  Each eligible phase gets a fresh validator; its I/O deadline is capped by the
  remaining allowance. Planning and cleanup consume this allowance, but cleanup
  and scheduling can overrun it. Exhaustion leaves later predictions unavailable
  while attempts may still run. Each worker arrival starts its
  own <!-- span limits.worker_proceed_wait.value_unit -->60,000 milliseconds<!-- /span -->
  release wait; stale releases cannot satisfy it. The host's sentinel polling
  excludes every synchronous collection, and the worker's exec budget excludes
  every measured release wait. Client timeout still cancels none of this work.
- Validator storage scales with queries actually sent, never with the phase
  capacity multiplied by the action capacity. Frame and string rejection retain
  earlier complete records and bounded fault context; the stdout byte cutoff
  closes collection with `byte_limit` and discards any incomplete cutoff frame.
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
  `request_label`), extension declaration count and declaration strings, then
  lifecycle-action strings and `test_override_path` executable overrides,
  then phase count, total action count, phase identities
  and parameter counts (`phase_count`, `probe_steps`, `phase_id`, `policy_parameters`), then worker strings
  (`policy_source`, `step_id`, `attempt_target`, exec arguments, parameter keys
  and values), then host query
  fields (`query_operation`, `query_filter_value`, `probe_plan_label`). A
  refused value is never echoed shortened: an oversized `specimen_id` is
  replaced by `<admission_refused>`, an oversized `run_kind` is omitted and an
  oversized `policy.format` reads `unknown`.
- The `policy_source`, `parameter_key`, `parameter_value`, `step_id`,
  `attempt_target`, `exec_argument`, `query_operation`, `query_filter_value`,
  `phase_id`, `extension_reference`, `extension_target` and `test_override_path`
  limits also reject embedded NUL, as do lifecycle-action identities and operation
  labels. For a string within
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
coordinate for correlating evidence with source. The contract versions below
identify compatibility.

### Shape and schema_version

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 5, response schema 23, controller envelope 7. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

Two documents carry these numbers. The runner reply is the JSON that
`pw-runner-client` prints: its `schema_version` is the response schema, and it
holds `normalized_outcome`, `steps`, `runner_subprocess`, `phases`
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
fresh batch validator for each eligible phase. Worker identity for
correlation comes only from `runner_subprocess.pid`; top-level `pid` may name
the host or client when no worker metadata exists.

`runner_subprocess` retains PID, exit/signal and partial-step status, plus
`ready_byte_received`, `done_observed`, `poll_stop_reason`, `exit_requested`,
`termination_request`, `reaped`, and `wait_errors`. Polling reasons are `done`,
`child_reaped`, `sentinel_deadline`, `wait_error`, `policy_write_error`, or
`policy_transfer_deadline`. The host's readiness, publication and exit-grace
waits are elapsed monotonic allowances, each reported as `ready_wait`,
`sentinel_wait` and `exit_grace_wait` with its budget, the elapsed time when it
stopped, why it stopped, the collection time the sentinel allowance excludes
and whether the clock failed; each phase's `validator_subprocess` reports its
`exit_grace_wait` the same way. Expiry starts the documented stop and cleanup
path; it promises neither an exact total response time nor instantaneous
process termination. Termination requests record
signal, syscall return and errno only on failure. Exit/signal values require a
successful reap; both are absent/null when disposition is unconfirmed. Wait
errors retain their stage and native return/errno, including recovered EINTR.
Application remains independently reported by `sandboxed_after_apply`.

`runner_subprocess` also records three host facts where the host acts:
`cleanup_trigger` (why exit was requested: `deadline_expiry`, `completion`,
`child_reaped`, `poll_wait_error`, `policy_transfer_error` or `policy_transfer_timeout`), `grace_end` (how
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
including a self-signal and an unresolved or conflicting status. `stop_reason`
projects why polling stopped (a deadline can coexist
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
requires key presence. Outcome mappings below use execution evidence.

The `exec` attempt kind adds optional per-step fields under
`steps[].attempt` — `child_pid`, `child_exit_code`,
`child_term_signal`, `stdout`, `stderr`, `exec_observation` — populated only for
`("exec", "spawn")` attempts. These are optional fields;
consumers that branch on `attempt.outcome == "exec_failed"` see the
three child fields exactly when an exec attempt's slot was filled, and
`stdout`/`stderr` only when that stream produced bytes. Other attempt kinds omit
these keys. `exec_observation` is available only for a completed worker result
whose spawn produced a child. Its absence or null means structured exec evidence
is unavailable, including valid replies from producers without this field; it
establishes no cleanup, EOF or reap fact. See [Structured exec observations](#structured-exec-observations).

### Top-level fields

Reply fields beyond `pid` / `runner_subprocess`:

- `phases[]` — ordered records with `phase_id`, one-based `ordinal`, ordered
  `action_ids`, `arrival_observed`, `completion_observed` and `collection_status`.
  Status is `not_reached`, `not_needed`, `collected`, `budget_exhausted` or
  `clock_unavailable`; `collected` includes failed or partial collection.
  `ordering` is present when a worker exists. Each `steps[].phase_id` identifies
  the phase owning its query, attempt and comparison. Phase completion and
  individual action completion remain separate observations.

- `phases[].validator_subprocess` — optional validator child observations, including
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

  Readers require the block to name the phase it served (`phase_id` and
  `ordinal` matching the containing phase) and its `expected_step_ids` to equal
  that phase's eligible query plan; a block, plan or record set copied from
  another phase is an ownership problem, as
  [Receiver evidence](#receiver-evidence) describes. The exact step/query join
  prevents a prediction from being borrowed for another phase's differently
  named action. A valid disposition establishes the reported process status
  only. Unexpected, duplicate and null-ID records are retained as diagnostic
  evidence; numeric PID uniqueness across phases is not a reader invariant, so
  a reused PID alone is not an ownership problem.
- `phases[].validator_spawn_failure` — optional host launch evidence with `origin`,
  `operation`, `executable_path`, `return_code` and `diagnostic`. For a failed
  validator launch, these are `runner_host`, `posix_spawn`, the executable path,
  the direct native return code and native descriptive text. The code is not
  ambient errno. Unfamiliar nonzero codes remain failures; wording is not a
  classification rule. The record survives a higher-priority worker failure
  and evidence-preserving reply degradation.
- `steps[].comparison.order` — `query_first` for eligible native records with the full release/acknowledgement chain; `unestablished` otherwise. Query order establishes an interval before that phase’s entire action batch.
- `phases[].ordering` — host collection/release observations, worker acknowledgement, worker lifetime evidence, validator disposition and protocol violations. After collection closure, release still requires the expected live worker phase. Validator failure or unconfirmed cleanup does not itself prevent release; no later record enters a closed collection. Missing predictions remain unestablished. Death before acknowledgement prevents a query-first claim; later death preserves it. `validator_disposition` is `not_invoked`, `not_needed` (empty query plan), `not_spawned`, `reaped` or `unconfirmed`.
- `steps[].comparison` — six fields that relate the two channels. `observation`
  classifies the attempt channel (`succeeded`,
  `permission_failure`, `other_failure` or `unavailable`) and
  `observation_basis` names the fields it rests on (`completed_worker_status`,
  `permission_errno`, `bootstrap_permission_result`, `spawned_child` or
  `no_completed_worker_result`). `operation_relation` (`matched`, `different`
  or `unresolved`) says whether the submitted query operation is the attempt's
  mapped operation: file `open_read`/`read_fresh`/`access` map to `file-read-data`,
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
  itself stays in `sandbox_check`.
  [Reading a comparison record](#reading-a-comparison-record) gives the rules
  for using it.
- `steps[].attempt.requested_kind` / `requested_action` — submitted intent,
  alongside the `requested_path` target. Execution is recorded in the attempt's
  result and lifecycle fields.
  A `file`/`create` attempt and an unsupported attempt have no single mapped
  operation, so their `operation_relation` is `unresolved`. For exec/spawn, a
  `process-exec*` query predicts admission of the submitted executable target
  only. Spawning also depends on fork, interpreter and other prerequisites.
  Native failure and missing-result evidence survive.

The authoritative child object also includes `worker_evidence` when a child was
spawned. Its `abi_identity` identifies the host-selected protocol sources.
Its latest atomic `progress` records the child's published stage, beside an
independently published `failure` (operation, diagnostic code, native result
kind/value, meaningful errno and optional parameter index), the worker's
readiness-write result, a bounded `diagnostic` and, when the worker published
it, `policy_read`: its EOF receipt for the policy pipe, with `bytes_expected`
(the submitted byte count the host wrote into the shared header before spawn)
and `bytes_received` (what the worker read at EOF). The worker refuses a
delivery whose length differs from the expectation before compiling (operation
2, code 13, detail the received count), so equal counts establish length
agreement with the submission only, not content identity, compilation,
application or kernel effect; absence establishes nothing about delivery.
Unequal counts can survive termination before a refusal is published, but cannot
accompany observations of compilation or later worker execution in an ordinary
reply. An evidence-preserving reporting failure retains contradictions as
diagnostics and omits every comparison.
Compilation returning NULL
is distinct from parameter setup or application returning an integer failure.
Before reading the policy, the worker queries the Mach timebase and converts its
release wait and exec allowances to continuous-clock ticks; a failure there is
operation 12 (clock setup) with the native Mach return, or code 14 with a reason
in `detail`, and the worker exits 12 before any policy byte or application. A
phase's release wait (operation 11) reports expiry as code 8 with the budget in
milliseconds, and a local timing refusal as code 14 with a reason, never
milliseconds: reason 3 means a clock sample went backwards and reason 6 that an
earlier sample, named in the diagnostic, already invalidated the clock. Neither
carries a native result or errno, and neither is a sandbox cause. An exec
attempt's timing fault appears in that step's error text and contributes no
errno; an accompanying native observation or cleanup failure retains its errno.
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
and process status remain available. Written bytes are host writes, not child
receipt; `worker_evidence.policy_read` is the worker's own account of what it read.
Policy delivery has an absolute monotonic deadline of <!-- span limits.worker_policy_transfer.value_unit -->5,000 milliseconds<!-- /span --> starting after worker spawn. Expiry records `policy_transfer_timeout` with `budget_ms`,
`elapsed_ms`, `bytes_written` and `bytes_expected`.
The host closes input and enters cleanup without starting readiness/sentinel
polling. A worker that reaches EOF refuses a short delivery before compiling;
termination can prevent it from publishing or exiting on its own. A transfer
timeout ordinarily yields
`runner_timeout`; that refusal, when the host observes it, is a published
worker failure and takes precedence as `runner_failed`, while the timeout
record and the cleanup/status observations remain independent. The deadline
does not bound final reap or cancel a client timeout.

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
`"slot_incomplete"`, respectively, and the outcome `no_completed_result`, which
names the missing result and does not say whether the operation ran. The
`attempt.lifecycle` evidence addresses that question: its `summary` is
`completed`, `started_without_result`, `not_reached`, `unsupported`, `unresolved`
or `conflicting`, and its `boundary` and `result` claims carry the supporting
observations or the reason the
question is unresolved, projected from
[the worker disposition record](#shape-and-schema_version). A completed
attempt's `rc` is PW attempt status. For `read_fresh`, the separate
`attempt.fresh_read` fields retain native open, fstat, read and close returns.

### Receiver evidence

`phases[].validator_subprocess` names the phase it served (`phase_id` and `ordinal`,
which readers require to match the containing phase, with expected IDs equal to
that phase's eligible query plan) and retains accepted `records` (including null-ID diagnostics)
and their `raw_line`, expected IDs, association issues, received stdout byte
count, probe write counts, independent I/O/decode faults, termination-call
observations and actual reap status. Duplicate IDs supply no unique per-step
prediction. Rejected-frame context remains diagnostic evidence. Unfamiliar
structurally valid diagnostic outcomes remain visible even when their per-step summary is
`error`.

`data.runner_client` reports the client's `argv`, start and end milliseconds,
`exit_code`, exact received/retained stdout and stderr byte counts and
`capture_limit_bytes`. `stdout_capture_error` means the controller truncated
its own retained reply; `stdout_parse_error` means the untruncated bytes could
not be decoded as JSON. Records inside a lost envelope are unavailable. The
independent fallback helper's admission refusal remains `policy_too_large`.

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
`native_rc=null` and `rc=-1`. Missing replies use synthetic `rc=0`, `outcome="error"`
with a missing reason. Use `result_source` and `native_rc` to distinguish a
received diagnostic, a native failure and a missing reply.

### The specimen dossier

`data.specimen` is present on every `kind: "run"` envelope, including
refusals and pre-execution tool errors. It records what the controller knew
about the request before invoking the runner. Policy source and parameter values
remain in the caller's specimen.

- `request_path`: the path given to `run`, or null when no path was given.
- `policy.augmentation`: always present; see [Augments](#augments). `status`
  is `not_requested`, `applied`, `failed` or `not_applicable`; `applied` lists
  the spliced augment names; `original_sha256` hashes the submitted string
  source and `applied_sha256` the string selected for invocation (the same
  hash when nothing was applied); `error` carries the refusal diagnostic. The
  hashes identify source string bytes before invocation. The worker's compilation
  evidence is in `data.runner_result`.
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
  `hw.machine`; null when a read fails. These describe the host environment.
- `runner_provenance`: the selected runner's `runner_kind`, bundle identity
  and path, service name, executable path, `runner_registry_id` for an
  installed BYOXPC runner, and the host's, worker's, validator's and issuer's
  signature metadata and entitlements read back separately
  (`runner_signature`/`runner_entitlements`, `runner_worker_signature`/
  `runner_worker_entitlements`, `runner_validator_signature`/
  `runner_validator_entitlements`, `runner_issuer_signature`/
  `runner_issuer_entitlements`). Each entitlement object lists `keys` and
  `granted`, the keys whose value is `true`. The built-in runner's helpers are
  described from the evidence manifest and carry no signature metadata.
- `app_provenance`: `evidence_manifest_path`, the app evidence manifest the
  built-in runner and the binary baselines were selected from, and
  `evidence_verify`, the verification report when `PW_VERIFY_EVIDENCE`
  requested one (null otherwise). The object is null when the manifest could
  not be parsed.
- `binaries.service`, `binaries.worker`, `binaries.validator` and `binaries.issuer`: null when
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

To inspect the selected source hashes and observed binary provenance:

```sh
jq '.data.specimen | {request_path, policy: {augmentation: .policy.augmentation.status,
  applied_sha256: .policy.augmentation.applied_sha256, imports: .policy.imports.status,
  closure_sha256: .policy.imports.closure_sha256}, host, runner: .runner_provenance.runner_kind,
  binaries}' run.json
jq '[.data.specimen.policy.augmentation.applied_sha256, .data.runner_result.policy_sha256]' run.json
```

### Extension and fresh-read output

The lifecycle [example](#sandbox-extensions) returns these records under
`data.runner_result`, separately from ordinary `steps`:

| Record | Fields and supported reading |
| --- | --- |
| `extensions[]` | `token_ref`, `extension_class`, `submitted_target`, optional `resolved_target` and `identity`, preparation status/errno, `issuance_status`, optional `issuer`, `delivery_status`, optional `delivered_bytes`, and `host_buffer_erased`. Target identity includes device, inode, mode, UID and GID at preparation time. |
| `extensions[].issuer` | Selected executable, PID and UID/EUID/GID/EGID, call marker and result publication, pointer nonnullness, errno and token length, plus independent spawn, termination, wait and reap observations. No token or pointer value is exposed. |
| `extension_events[]` | `phase_id`, `step_id`, operation and references, `call_boundary_observed`, `result_published`, status, optional `native_result`, errno, unavailability reason and lifecycle claims. |
| `steps[].attempt.fresh_read` | `open_rc` / `open_errno`, `stat_rc` / `stat_errno`, optional descriptor identity, `read_rc` / `read_errno`, `close_rc` / `close_errno` and `content_hex`. Each errno belongs to its failed syscall; successful read count determines the hex length. |

`issuance_status: issued` requires published bounded token evidence and a clean,
confirmed issuer exit. `issuer_abnormal_exit` retains that publication alongside
an observed nonzero exit or signal and withholds delivery. An interrupted worker
can leave `delivery_status: not_observed` despite completed issuance. Consumption
has its own record in `extension_events`.

<!-- BEGIN COPIED EXTENSION STATUSES -->

Issuance and delivery are separate observations. Only `issued` makes the token
channel eligible for worker delivery. Other issuance statuses withhold it;
none establishes consumption, effective permission or revocation. Read spawn,
termination, wait and reap fields independently: a status does not substitute
for cleanup evidence.

| Issuance status | Publication and supported meaning |
| --- | --- |
| `not_started` | Issuance did not start, including when target preparation failed. No issuer result is supplied. |
| `issuer_unavailable` | The selected issuer executable was unavailable. Preparation and issuance did not start; capability refusal prevents a worker run. |
| `channel_setup_failed` | Host setup of the transient channel or its descriptor failed before issuer launch. No issuer result is supplied. |
| `spawn_failed` | Spawn setup or `posix_spawn` failed. The issuer record retains the spawn failure; no child PID or native result is inferred. |
| `issuer_timeout` | The issuer wait expired without a more specific publication status. Publication may be present; termination requests and final reap observations remain separate. |
| `issuer_wait_error` | The issuer wait failed without a more specific publication status. Publication may be present; the wait error does not establish child exit. |
| `issuer_result_missing` | The issuer was reaped without result publication. `result_published` is false, with no native result, errno, token length or published authority IDs. A pre-call marker and exit/signal observation may remain. |
| `issuer_abnormal_exit` | A bounded token result was published, but the issuer was reaped with a nonzero exit or signal. Publication is retained and delivery withheld. |
| `native_api_unavailable` | The issuer published that at least one required extension API (issue, consume or release) was unavailable, without a native call. Capability refusal prevents a worker run; cleanup remains independently recorded. |
| `native_refusal` | The issuer published a null native return and its errno. This observation does not establish why issuance was refused or whether cleanup was clean. |
| `token_oversized` | A nonnull native return supplied an empty token or no terminator within the token buffer bound. The issuer published that rejection; no deliverable token length is supplied. |
| `invalid_transport` | Publication was observed, but its header, state/marker relationship or token length failed host validation. Fields from an invalid header are not treated as native results. |
| `issued` | The issuer published a nonnull native result with a bounded token length and was cleanly reaped. The worker still must validate the channel and publish its own delivery observation. |

Published API unavailability, native refusal, token rejection or invalid transport
has its own issuance status even if the host wait also timed out or failed.
For a valid bounded token result, a wait timeout or error withholds delivery and
keeps that wait status; clean and abnormal reaps distinguish `issued` from
`issuer_abnormal_exit`.

| Delivery status | Worker observation and supported meaning |
| --- | --- |
| `not_observed` | No worker delivery publication was collected. This includes no worker or interruption before publication; it does not negate completed issuance. |
| `delivered` | The worker published successful channel validation; `delivered_bytes` matches the issued token length. This does not establish a consume call or result. |
| `token_unavailable` | The worker published that no token descriptor was supplied. No delivered byte count is supplied. |
| `channel_rejected` | The worker inspected the channel and rejected it. `delivery_failure.stage` is `channel_size` (a successful `fstat` reported an object smaller than the channel; `native_rc` 0 and no errno), `channel_header` (magic, completion or status) or `channel_token` (length, terminator or embedded NUL). Format rejections carry no native result. No delivered byte count is supplied. |
| `local_setup_failed` | A local native call before channel validation failed. `delivery_failure.stage` is `core_limit` (`setrlimit`), `descriptor_metadata` (`fstat`), `mapping` (`mmap`) or `descriptor_close` (`close`), with that call's `native_rc` and the errno saved immediately after it. The channel contents were not judged. No delivered byte count is supplied. |
| `native_api_unavailable` | The worker published that consume or release API support was unavailable. No delivered byte count is supplied. |

<!-- END COPIED EXTENSION STATUSES -->

When native API support is unavailable, an optional `delivery_cleanup_failure`
records a failed descriptor close independently of that primary status. It has
`stage: "descriptor_close"` and the saved native `errno`. Its absence means no
cleanup failure was reported, not proof that cleanup succeeded. For
`channel_rejected` and `local_setup_failed`, cleanup observations remain in
`delivery_failure.cleanup_stage` and `cleanup_errno`.

An event status of `returned` requires native result publication; consumption's
signed handle value of -1 supplies no handle. Release's native result stays
separate from later file access. `unavailable` records a published no-call
decision (`token_unavailable`, `handle_unavailable`, `native_api_unavailable` or
defensive `repeated_action`). `unresolved` has no published result, even if a
pre-call marker survived. An omitted action has no event. Completed disposition
slots can therefore describe unavailable actions without implying a native call.

A failed fresh open has no stat/read/close evidence. A completed fresh read keeps
the first failure in syscall order as the aggregate `read_failed` outcome;
missing action publication supplies no fresh-read payload. Returned bytes are a
bounded prefix. Issuer and worker identities describe their observed authority
separately. The [native evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence)
defines producer and reader validation.

### Per-step shape

The runner echoes step results with additional context:

- `steps[].sandbox_check`: `{ rc, outcome, pid, operation, filter_kind, filter_value, filter_type_id, errno, error, result_source, native_rc, missing_reason?, path_diagnostics? }`
- `steps[].attempt`: `{ rc, errno, outcome, error, result_source, missing_reason?, requested_kind, requested_action, requested_path, observed_path, lifecycle, fresh_read?, path_diagnostics?, child_pid?, child_exit_code?, child_term_signal?, stdout?, stderr?, exec_observation? }`
- `steps[].comparison`: `{ observation, observation_basis, operation_relation, target_relation, order, limitations }` — see [Top-level fields](#top-level-fields) and [Reading a comparison record](#reading-a-comparison-record).

Notes:
- `requested_path` echoes the attempt target for every attempt kind
  (path, Mach service name, sysctl name, etc.). `observed_path` is the
  worker's own `F_GETPATH` observation for successful `open_read`, `open_write`
  or `create`, explicit `null` otherwise. A `read_fresh` action instead retains
  descriptor metadata under `fresh_read.identity`. `path_diagnostics` is the host's later resolution of a file or
  exec attempt target (see [attempt.path_diagnostics](#attemptpath_diagnostics));
  other attempt kinds omit it.
- `filter_value` is the exact string the runner passes to `sandbox_check`,
  except when `outcome == "prediction_unavailable"` — in that case no
  `sandbox_check` call is made; `filter_value` is echoed back from the
  request unchanged for cross-referencing with the specimen.
- `filter_type_id`: `1` (path) or `2` (mach-lookup global). The global-name
  ID was verified against kernel enforcement (deny on the policy's denied
  value and allow on a sibling un-denied value); ID `12` passes the same
  check, so `2` is the selected working ID. No ID is emitted for
  `local_name`: PW excludes this pair conservatively because the investigation
  has not established a matched native lookup with which to calibrate a
  filter ID. The empirical mapping question remains open. For filter kinds
  in the prediction_unavailable set, no
  `filter_type_id` is emitted (see
  [Filter kinds where prediction is unavailable](#filter-kinds-where-prediction-is-unavailable)).
- `outcome`: `allow`, `deny`, `error`, `unsupported_operation`, or
  `prediction_unavailable`.
    - `allow` / `deny`: `sandbox_check` returned a clean verdict.
    - `error`: no usable prediction. This includes native call errors,
      validator diagnostics and synthetic missing replies. Consult
      `result_source`, `native_rc`, `missing_reason` and run-level records;
      diagnostic text can come from the validator or host as well as the native call.
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
      The `attempt` result records what happened when these probes ran.
  When `outcome == "prediction_unavailable"`, `rc` is the sentinel
  `-1` and `errno`/`filter_type_id` are `null`. Consumers must check `outcome`
  before interpreting `rc`.

For supported attempts, a completed slot has `attempt.result_source: "worker"`
whether the operation succeeded or failed. Missing or incomplete publications
have source `"synthetic"` with `missing_reason: "slot_absent"` or
`"slot_incomplete"`; lifecycle evidence separately describes progress.

`steps[].attempt.outcome` values:

- `ok` — the attempt's syscall returned success (allow).
- `read_failed` — a fresh-descriptor open, stat, read or close failed; inspect `fresh_read` for the separate syscall observations.
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
  `bootstrap_permission_result`, subject to the
  [comparison reading rules](#reading-a-comparison-record).
  `kr=1102` (`BOOTSTRAP_UNKNOWN_SERVICE`) reports an unregistered service.
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
- `no_completed_result` — no completed attempt result. The name makes no claim
  about whether the operation ran: a worker can die before an attempt, while
  the native call is in flight, or after the call returned but before the slot
  published, and the reply withholds the unpublished result in every case.
  `attempt.lifecycle`
  describes observed progress, and the comparison's limitation repeats its summary
  (`attempt:started_without_result`, `attempt:not_reached`,
  `attempt:lifecycle_unresolved` or `attempt:lifecycle_conflicting`) beside
  `observation: unavailable`. Errno is null when no result supports it.

### Reading a comparison record

Read the channels' results, relations and order with these rules:

<!-- BEGIN COPIED READING RULES -->

1. The raw query answer is `sandbox_check.outcome` when `result_source`
   is `validator` and the outcome is `allow` or `deny`; otherwise
   `sandbox_check.missing_reason` explains the unavailable answer. An otherwise
   eligible answer qualifies as a prediction about a live specimen only with
   its phase's collection/release/acknowledgement chain, reflected by
   `comparison.order: query_first`. Neither successful attempts nor a successful
   run are required. Without that chain, retained native answers do not establish
   whether the target was live during any particular query. A degraded
   `runner_reporting_failed` reply certifies no per-step order, even when raw
   ordering observations survive; every comparison is omitted.
2. `attempt.missing_reason` explains an unavailable attempt channel.
3. A `permission_failure` or `other_failure` observation, or an exec attempt
   whose spawned child exited nonzero, does not attribute the failure to the
   sandbox; attribution needs a captured denial record, and
   `permission_failures_without_record` lists the steps that have none.
4. A `path` query, or an attempt whose mapped filter is `path`, never
   establishes that both channels resolved the same object at runtime.
5. No record establishes that the state the query saw is the state the
   attempt met; nothing in a reply discharges this.
6. A worker `unlink` of a submitted path with `outcome: ok` and `rc: 0`
   records removal at that action. For a path query of that same submitted
   spelling in the same phase, `order: query_first` establishes that the query
   preceded the unlink. `order: unestablished` supplies no ordering inference.
   For actions in different phases, use the corresponding completion and arrival
   publications to establish sequencing; the query's `order` applies only to
   its own phase. A later same-path query can follow an earlier unlink and
   recreation. None of these fields establishes stable object identity.
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
13. Extension issuance, delivery, consumption and release are independent
    observations. A pre-call marker without result publication supplies no
    native result. A successful consume/release does not establish effective
    access or revocation; read later fresh-descriptor attempts separately.
14. A lifecycle action has no ordinary comparison. `query_first` on an ordinary
    action refers to its phase's collection, including when an earlier consume
    or release in that phase changed what the attempt later encountered.

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
for diagnostic inspection. Fields:
`{ observer, stage, input, same_as_input, realpath_resolved?,
firmlink_resolved? }`. The runner still passes the raw `filter_value` to
`sandbox_check` — this block is observation only.

Producer: `path_diagnostics` is computed by the unsandboxed runner
host (`PWRunnerService.enrichPathDiagnostics`) after orchestration returns,
with child cleanup status recorded separately. `observer="runner_host"`
and `stage="after_orchestration"` identify that provenance. The host's resolution
is independent of the worker's sandbox and can see a path changed by an attempt.
Neither a resolved path nor null establishes what the validator saw earlier.

Each form is in exactly one of three states:

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
otherwise the diagnostic can carry a different resolved string.

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
`attempt.path_diagnostics`: `{ observer, stage, input, same_as_input,
realpath_resolved?, parent_realpath_resolved? }`, produced by the same
unsandboxed host pass after orchestration (`observer="runner_host"`,
`stage="after_orchestration"`) and always in the compact three-state form
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
  The cause may be unknown. A completed report survives an abnormal exit as
  partial execution evidence.
- `runner_reporting_failed` — the host could not encode its assembled result.
  `reporting_failure` preserves the original execution summary separately.
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
  unconfirmed.
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
attempt evidence.

The contract is keyed on the `(operation, filter_kind)` pair. A specimen pairing
one of these filter kinds with a different operation gets a normal
`sandbox_check` call; that answer is reported as received, because the runner
excludes only the
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
- `(mach-lookup, local_name)` — a conservative capability exclusion. The
  investigation has not established a native lookup governed by a `local-name`
  rule against which to calibrate a filter ID. ID `3` is a query candidate;
  matching it to local-name enforcement remains an open empirical question.
  PW reports the prediction as unavailable, and attempts still run.

### Attempt kinds the runner implements

The C worker implements these `(attempt.kind, attempt.action)`
combinations:

- `("file", "open_read" | "read_fresh" | "open_write" | "create" | "unlink" | "access")` — exercise file ops on `target`.
  `open_read` opens read-only, attempts a one-byte read and close, and discards
  those latter returns; its status reports the open result. `open_write` opens
  with `O_WRONLY | O_TRUNC`, then attempts to write `x` and close, discarding
  those returns; success reports the truncating open, not an observed byte
  transfer. `create` uses `O_WRONLY | O_CREAT` with mode argument `0600`, subject
  to umask: an existing file is opened without truncation, and an absent target
  can be created. `read_fresh` instead retains separate native open, stat, read
  and close observations and bounded content, as described in
  [fresh-read output](#extension-and-fresh-read-output).
- `("mach_lookup", "bootstrap_look_up")` — `bootstrap_look_up` on `target`.
- `("sysctl", "read")` — one post-apply `sysctlbyname` value read of
  `target`, such as `kern.osrelease`, into a
  non-null <!-- span limits.sysctl_read_bytes.value -->4,096<!-- /span -->-byte
  stack buffer. There is no preliminary sizing call or retry. The worker
  discards the returned value bytes and post-call length; the attempt
  retains the existing PW status and errno. This bounded read does not
  promise retrieval of an arbitrarily sized value, and failure does not
  diagnose whether the destination was too small.
- `("exec", "spawn")` — `posix_spawn(target, argv, ...)` of a helper
  binary. `target` is the absolute path to the helper (becomes
  argv[0]). Optional `args: ["…", …]` supplies argv[1..N].
  The worker creates each child's stdout/stderr pipes and spawn handles
  inside the attempt, after the sandbox applies, and releases them before
  the step completes. The bare-deny control observes successful setup followed
  by a permission-shaped failure at `posix_spawn` for its tested inputs and
  environment. Setup can fail at an earlier call; its recorded boundary and
  native error do not establish a sandbox cause. The
  [worker tour](WORKER.md#acquisitions-inside-attempts) distinguishes these
  observations from source-established placement. The worker bounds each child
  by the deadlines under
  [Execution budgets](#execution-budgets), drains both streams while the
  child runs, reaps it, and surfaces these fields under `attempt`:

  | field | populated when | sentinel when not | semantics |
  | --- | --- | --- | --- |
  | `child_pid` | spawn produced a child; user-code entry is not established | `0` — spawn blocked / target missing / setup failed | No child establishes spawn failure, not its cause. With `child_pid==0`, EPERM/EACCES are permission-shaped failures (`observation: permission_failure`) whose cause the record does not assign. A helper non-zero exit with `child_pid>0` still establishes successful spawning (`observation: succeeded`, basis `spawned_child`); leader status is in `child_exit_code`/`child_term_signal`, while `rc` retains aggregate attempt status. |
  | `child_exit_code` | confirmed reap reported natural leader exit | `-1` — signaled, no child ran, or final status unconfirmed | |
  | `child_term_signal` | confirmed reap reported a signal | `0` — clean-exited, no child ran, or final status unconfirmed | |
  | `stdout` / `stderr` | stream produced bytes | key omitted (no stream output) | |
  | `rc` | always populated | (n/a) | Helper's exit code after successful observation; `-1` on spawn, deadline, observation or cleanup failure. Consult `child_exit_code` for the leader's independently observed exit. |
  | `outcome` | always populated | (n/a) | `"ok"` when spawn and observation completed successfully and the leader exited 0; `"exec_failed"` also covers deadline and cleanup errors. Neither a successful leader reap nor pipe EOF proves descendant cleanup. |

  Callers who want exec attempts to succeed under a deny-by-default
  policy opt into `policy.augments: ["exec_baseline"]` (see
  [Augments](#augments)) — three `(allow ...)` rules are sufficient
  to let a libSystem-dynamic helper spawn, load dyld, and reach
  `main`. Callers who need to allow more (network, IOKit, specific
  filesystem subpaths) compose their own additional allows on top
  of the augment.

  The helper is spawned with `POSIX_SPAWN_CLOEXEC_DEFAULT`, inheriting only
  stdin=/dev/null and its stdout/stderr pipes, and an empty environment,
  whatever `EnvironmentVariables` an external runner's launchd plist gave the
  host. The worker's own environment is unrecorded. The helper's own failure is
  the attempt's record
  (`child_exit_code` and its bounded output); it does not change the run's
  `normalized_outcome`.

  Exec children have their own PIDs; deny-log correlation covers the worker
  PID only (see [Denial-log correlation](#denial-log-correlation)).

Other attempt combinations refuse the whole specimen before worker or validator
creation. A non-null `args` field is accepted only for `exec/spawn`, including
when the array is empty. Query and attempt scopes can differ; recognized queries with
unavailable predictions still permit supported attempts.

### Structured exec observations

`steps[].attempt.exec_observation` separates the worker's collection snapshot,
termination requests and final leader wait. Slot publication and
`lifecycle.summary: completed` mean the result became immutable, including a
failed result. They do not mean that processes or descendants finished.
The added object does not change `rc`, `errno`, `outcome`, the run disposition,
or the comparison's `spawned_child` meaning.

The object is optional. A present object requires all three sections below.
Pre-spawn failures, synthetic results and non-exec attempts omit it. A worker
that dies before slot publication supplies none of it, even if it wrote a PID
or payload bytes. Missing or null metadata remains unknown.

| Section | Fields and meanings |
| --- | --- |
| `collection` | `stop_reason` is `leader_exit_and_eof`, `deadline`, `observation_error` or `clock_fault`. `leader_exit_observed` records `waitid(... WNOWAIT)` observing the leader. Required `stdout.eof` and `stderr.eof` record reads returning zero. This snapshot precedes all cleanup and final reap; later observations cannot revise it. |
| Collection details | A deadline has `deadline_kind: child` or `plan`. Optional `waitid_errno`, `poll_errno`, and each stream's `read_errno` retain terminal native errors; recovered interruptions are excluded. Each stream's optional `poll_revents` retains the actual error flag mask, rather than a fabricated native errno. Optional `clock_fault` is a nonzero numeric worker time-reason code, not errno. Both streams' failures can coexist. |
| `cleanup` | `state` is `not_requested`, `ownership_unconfirmed` or `requested`. Only `requested` has `group_request: {target, signal, rc, errno?}`. The target is the actual negative process-group ID. A failed group request other than `ESRCH` has a separate `leader_fallback` with the actual positive leader target and independent return. Successful calls omit errno. `ESRCH` remains a failed native request, distinct from return zero. |
| `reap` | `stop_reason` is `reaped`, `wait_error`, `ownership_unconfirmed`, `group_request_failed`, `clock_fault` or `deadline`. Required `last_wait` retains the final `waitpid(... WNOHANG)` return: leader PID, zero or -1; errno is present only for -1. Raw `status` is present only when that call returned the leader. Optional `clock_fault` can coexist with a successful reap or native error. |

The existing child exit/signal fields decode that same confirmed raw status.
Pending or failed waits have no status. A local reap-grace expiry has no native
wait errno unless the last call itself failed; a native `ETIMEDOUT` is instead a
`wait_error`. A final `EINTR` can coexist with a subsequent local stop. Clock
reason codes are bounded nonzero integers; an unfamiliar code remains a raw
reason without an inferred interpretation.

A successful signal is a termination request, not an observed exit. Neither
signal return, `ESRCH`, leader status, stream EOF nor an omitted fallback proves
group absence or complete descendant cleanup. The cleanup section covers
process-termination calls only; it is not an account of descriptor closes or
spawn-handle destruction. Observed leader signal status does not identify its
sender. A missing fallback in a present record means this path made no fallback
call; absent metadata makes no such negative claim.

Ordinary collection ends at leader exit plus both EOFs and requests no
termination. Same-group descendants can remain alive after closing their
streams, including during later steps and after worker exit. Worker death can
also leave descendants alive. Exceptional cleanup targets the owned group;
descendants that leave it are not contained. The host supervises the worker,
not the exec descendants.

## Operating

### Common flags

- `--timeout-ms <n>`: runner RPC timeout
- `--log-timeout-ms <n>`: log collection allowance, default <!-- span limits.log_collection_timeout.value_unit -->10,000 milliseconds<!-- /span -->. Positive
  integer milliseconds only; no unlimited value. Invalid values fail before
  running the specimen, including with `--no-log-capture`. A larger value buys
  waiting time only: the specimen, the scan interval and the byte budgets are
  unchanged. Log availability remains dependent on the OS.
- `--no-log-capture`: skip the unified-log (`log show`) deny scan. Archive access
  has been observed to cost seconds even for short spans. Pass this when you
  don't consume `data.sandbox_log_capture`; it is then `null` and
  `correlation_status` is `not_attempted`.
- `--runner-mode <standard|byoxpc>`: inject `runner.mode` into the request
- `--version`: print a `kind="version"` envelope with the build stamp and the
  wire contract versions this build speaks

Log collection is bounded in time and size. Observer startup, `log show` and
result processing share one monotonic deadline, followed by a fixed <!-- span limits.log_cleanup_grace.value_unit -->1,000 milliseconds<!-- /span -->
cleanup grace; the `log show` child itself stops <!-- span limits.log_report_reserve.value_unit -->1,000 milliseconds<!-- /span --> before that deadline
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

Retain each invocation as a separate observation, including earlier failures.

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
candidates.
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
capture yielded no candidate for the reported permission-shaped failures.
A record can exist in the OS log store under another path form, such as a
resolved symlink; the list describes this capture's matching result.

Step associations under
`sandbox_log_capture.step_denies` contain `{event_index, candidate_step_ids,
association, matching_evidence}`. Events, including unmatched ones, remain in
`deny_events`; associations refer to them by index. A single candidate uses `association="candidate"`;
multiple candidates use `"ambiguous"`.

Step matching requires a positive worker PID matching the event, an exact
operation relevant to the submitted attempt joined by unique step ID, and an
exact target/path match. Targets come from the submitted attempt,
its requested and worker-observed paths, and the host's after-orchestration
`attempt.path_diagnostics` forms; each admitted source is named in
`matching_evidence.path_sources`, the host forms as
`runner_host.after_orchestration.<form>`. A kernel record names the resolved
path, so a target reached through a symlink (such as `/etc/hosts`) correlates
through `realpath_resolved`, and a created or unlinked entry through
`parent_realpath_resolved`. Host forms require a valid compact block with that
exact observer and stage, and an input equal to both the submitted target and
the reported requested path. Invalid blocks contribute no host path matches;
independent submitted, requested and observed paths remain eligible.
Supported operations are:

| Attempt | Relevant event operations |
| --- | --- |
| file open_read/read_fresh/access | file-read-data |
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

Validator `sandbox_check` queries use `SANDBOX_CHECK_NO_REPORT` and produce no
denial records. A matching target still does not prove that a record came from
its paired attempt: repeated attempts and PID reuse prevent unique attribution,
and a PID match can reflect an ordinary denied probe followed by an unrelated
self-signal or crash. Some denied attempts have no available log record;
requesting the full interval does not guarantee complete delivery.

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
  without a match. Successful runs also retain capture. See [Denial-log correlation](#denial-log-correlation).
- `normalized_outcome` is `worker_spawn_failed`: the host could not
  `posix_spawn` the worker. Verify the bundle is signed and on a writable
  filesystem; `pgrep -fl PWRunner` should show no stragglers.
- If you are running inside a sandboxed automation harness, XPC lookup can be blocked;
  run from a normal Terminal to confirm behavior.

Common decode errors (quick fixes)
- `missing field 'policy'`: add a top-level `policy` object with `format` and `sbpl_source`.
- `keyNotFound(... "specimen_id" ...)`: add a top-level `specimen_id` string.
- `unknown field 'path_membership'`: put path rules in `policy.sbpl_source` as SBPL.
- `runner.mode=debuggable` or top-level `instrumentation` field rejected:
  install a BYOXPC runner with the entitlements
  you need and select it via `runner.id` or `runner.service`.

## External runners (BYOXPC)

For `run` and `runner verify`, a qualifying `already_ran` refusal triggers
re-acquisition within the existing request timeout. The reply must pass current
response admission, carry empty steps and no worker, and name a live host whose
executable matches the selected registry record. The controller captures its
kernel start time and waits for that generation to disappear (ESRCH or a changed
start time) before starting another client. The host remains single-use.

The last refusal is returned when the deadline expires. A refusal can reach the
caller earlier if it does not qualify or a process observation fails before
retirement is established. Hosts that cannot be observed, including system-scope
hosts under restricted access, keep that refusal behavior.

Other outcomes, including XPC connection errors, do not trigger re-acquisition.
A connection racing a host's exit can fail before delivering a refusal; that
error does not establish that the request was refused before admission.

`data.runner_acquisition` is an array of qualifying refused attempts (empty when
none qualified). Each contains `runner_client`, the unchanged refusal in
`runner_result`, and `generation` with `pid`, `start_sec`, `start_usec` and
`executable_path`. `wait_outcome` is `retired`, `deadline` or
`observation_failed`; `observation_error` retains a failed observation diagnostic.
`observed_exit` is null without established retirement, otherwise it records
`basis` (`esrch` or `pid_reused`), `observed_at_unix_ms`, and the replacement
identity for PID reuse. The replacement's executable is uncollected. These
records identify the refusing host, not the client holding its claim.
Only the final attempt supplies the ordinary runner result, client capture,
deny-log interval and downstream observations. On deadline exhaustion that
final result is the last refusal, also retained in the acquisition array.


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

$PW runner verify --service-name com.policywitness.policy-witness.PWRunner --timeout-ms 2000
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
  supplied entitlements are re-embedded into the binary.
- The installer signs the copy's embedded worker
  (`Contents/MacOS/pw-probe-runner`) with the identity and the supplied plist,
  its validator (`Contents/MacOS/sb_api_validator`) and issuer
  (`Contents/MacOS/pw-extension-issuer`) with the identity alone,
  and then the enclosing bundle with both. The worker is the process the
  specimen policy is applied to, so the plist you supply is what the kernel
  consults for that policy's `require-entitlement` rules. A copy missing
  a required helper is refused.
- Installation verifies the sealed bundle recursively
  (`codesign --verify --deep --strict`): a copy whose embedded code changed
  after sealing is refused.
- Point specimen attempts at files you own under a temporary directory (for
  example under `/private/tmp`). Attempts against targets under
  privacy-mediated folders such as Desktop or Documents can stall on consent
  mediation, and such a stall is not a sandbox verdict.

The install command saves a `pending` registry record before writing its launchd
plist, then bootstraps and marks the record `installed`. With `--skip-bootstrap`,
plist creation completes installation; loaded state is reported separately.
Errors after the pending save retain ownership for recovery. Pending runners
can be listed, inspected and removed, but cannot be selected for specimens.

The registry record reads each binary back separately (`codesign -d
--entitlements` and `codesign -dv`): `signature`
and `entitlements` describe the host executable, `worker_signature` and
`worker_entitlements` the worker, `validator_signature` and
`validator_entitlements` the validator, and `issuer_signature` /
`issuer_entitlements` the issuer. Each entitlement object lists `keys`
(every key the plist names) and `granted` (the keys whose value is `true`).
A record written by an earlier policy-witness carries no worker read-back: it
can be listed, validated and removed, and it serves specimens that require no
entitlements, but a specimen with `required_entitlements` is refused until the
runner is reinstalled. Older records without issuer read-back similarly retain
unknown issuer provenance and remain manageable. Selecting a current runner copy
whose issuer file is missing refuses extension specimens with
`extension_issuer_unavailable`; its ordinary specimens remain supported. An
older runner binary can refuse the request version or fields before reaching
this capability check. `runner validate` checks any recorded helper
against the current copy and reports missing or invalid code; `runner reconcile`
reports installation state. Reinstall to refresh recorded provenance.

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
  testing with trusted local callers.

Symptom cheat-sheet: `xpc_error` right after install usually means an ad-hoc (or
wrong-team) runner failing the signed-caller check; `xpc_timeout` means the host
reply was not received before the deadline. A launch crash is one possible
cause; the timeout alone does not establish it.

### Verify the runner

```sh
$PW runner verify --service-name <service-name>
```

`runner verify` sends a fixed allow-all specimen with no probe steps to the
runner on the client's stdin, as a run does, and reports the outcome and the
PID the reply names as `runner_pid`: the worker that served the request, or
the host when the host refused it (the reply's `pid` rule). It defaults to
a <!-- span limits.runner_verify_wait.value_unit -->5,000 milliseconds<!-- /span --> timeout; pass `--timeout-ms <n>` for slow cold-spawn cases.

Verification consumes the host it reaches: every host serves one request and
exits. The next request starts a fresh host once launchd allows a launch,
which the installed plist's `ThrottleInterval` bounds at <!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span --> after the
previous launch. A request that reaches the verified host while it is still
retiring, or a fresh host that another connection reached first, is refused
with `normalized_outcome: already_ran`. The controller re-acquires after this
pre-worker refusal only when it can identify the selected host's generation
and observe its retirement, as described above.

### Use the runner in a specimen

Consecutive runs through one installed runner are serial and paced by launchd:
the runner exits after each specimen, and the generated plist sets
`ThrottleInterval` to <!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span -->, so a run requested sooner than a second after
the previous host's launch waits for the remainder (launchd's default without
the key is ten seconds). Three serial runs with a short pause between them
took about four seconds of wall time in the project's measurement.

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
  "service": "com.policywitness.policy-witness.PWRunner",
  "mode": "byoxpc"
}
```

`runner.mode` is optional; when present it must equal `byoxpc` for external
runners. Valid modes: `standard`, `byoxpc`. `required_entitlements` is
satisfied only by keys the selected runner's worker holds with the value
`true`, as recorded in the registry's `worker_entitlements.granted` (for the
built-in runner, its worker's evidence-manifest entry). A key that is absent,
or present with any other value, refuses the run before any host is reached,
and the refusal names the worker and the key. The host's entitlements are
recorded separately.

Quick smoke request (save as `/tmp/pw_byoxpc_smoke.json`):

```json
{
  "schema_version": 5,
  "specimen_id": "byoxpc_smoke",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (deny default)"
  },
  "probe_plan": [],
  "runner": {
    "service": "com.policywitness.policy-witness.PWRunner",
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

`runner validate` verifies each registry entry's bundle recursively, then the
host, worker and validator individually. It also checks the issuer when the file
is present or the registry already records issuer evidence. It re-reads those
signatures and entitlement sets, and reports `invalid` (records with a failure)
and `failures` rows naming the record and binary (`bundle`, `host`, `worker`,
`validator` or `issuer`). An older record and bundle with no issuer retain unknown
issuer evidence; a recorded issuer that disappears fails validation.
The host's recorded `signature.valid` follows the recursive
check; each helper's follows its own. Use `runner reconcile` to compare
installation state with launchctl and `LaunchAgents/`.

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
