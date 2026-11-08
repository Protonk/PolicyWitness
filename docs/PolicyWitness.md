# PolicyWitness User Guide

PolicyWitness records `sandbox_check` queries and attempted operations under
macOS sandbox policies. When prediction is available, the validator queries
the worker's PID; the worker attempts its operation after applying the policy
and receiving release from the host. Each step records available results, missing
observations, submitted-scope relations and ordering. The controller adds
request identity, source hashes, imports, runner and app provenance, host
facts and hashes of selected binaries outside the app manifest. Retain the
specimen alongside the envelope for the full input. The
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
  "schema_version": 6,
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

For an exercise that checks a file effect and then deliberately triggers a
request refusal, see [Try an accepted request and a refusal](#try-an-accepted-request-and-a-refusal).

## Questions

<!-- BEGIN COPIED QUESTIONS -->

### When should I use PolicyWitness?

Use PolicyWitness when you need to determine whether an observed result follows from the sandbox policy under test or from some unrelated part of the execution environment.

### Who needs to use PolicyWitness?

Almost no one. Folks authoring SBPL profiles can call `sandbox_check` and `sandbox-exec` directly and Apple's entitlements model plus their app's actual runtime behavior cover practical sandbox questions. A small wrapper script around `sandbox_check` plus `sandbox-exec` can obtain a prediction and an attempt result in the common case. 

### What systems can run PolicyWitness?

PolicyWitness requires macOS 26 on Apple Silicon. Its shipped executables are arm64-only; Intel Macs are not supported.

### Can PolicyWitness attribute a failed attempt to sandbox denial?

No. PolicyWitness records the failed attempt and the evidence available around it, but a failure alone does not establish that the sandbox caused it.

### What does PolicyWitness's attempt channel record?

The sandboxed worker supports four built-in attempt kinds: `file` (open/read/write/create/unlink/access), `mach_lookup` (`bootstrap_look_up`), `sysctl` (`sysctlbyname` read), and `exec` (`posix_spawn`). Completed results carry operation-specific status and error observations in a uniform per-step envelope; those status fields are PolicyWitness attempt status, not raw syscall returns. Result provenance and missing reasons distinguish completed observations from missing or incomplete reports.

### How does a worker report observations under `(deny default)`?

The host prepares and pre-touches a shared-memory region before spawning the worker. The worker publishes observations there after applying its policy, and the unsandboxed host reads them to assemble the response.

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

Yes. Use an unapplied, unentitled actor to issue and transfer a token to an applied, selected actor, then compare fresh access before consumption, during use and after release. Add actors to test re-delegation. Unapplied does not mean unrestricted; signing observations do not establish effective authority. See [EXTENSIONS.md](#sandbox-extensions) for operations and evidence limits.

### Which happens first, the prediction or the attempt?

A `query_first` comparison identifies an eligible native prediction collected before the worker acknowledged that phase's host release, which precedes its actions. Missing or unusable predictions and death before acknowledgement remain `unestablished`. Query collection closes even when validator cleanup is unconfirmed; a surviving validator cannot add later records. Earlier actions in the phase, including consumption or release, can change what a later attempt encounters. Use another phase for a new query collection; neither interval is a common state snapshot.

### Can PolicyWitness collect sandbox-denial logs?

No. Earlier versions included a best-effort unified-log observer. The observer
and its former PolicyWitness integration are archived at
[Protonk/Observer](https://github.com/Protonk/Observer). The archive is
unmaintained.

### How long does a run take?

A run includes the runner client span plus the controller's startup,
preparation and output. `data.runner_client.ended_at_unix_ms` minus
`started_at_unix_ms` records the client's wall-clock span; clock adjustments
can affect that difference.

### Can I evaluate specimens in parallel?

Yes and no. Each specimen is evaluated in its own runner and worker processes, but PolicyWitness does not guarantee relative scheduling between concurrent runs. Run specimens separately when you need to avoid timing interference between them. N.B. Runs through one installed [external runner](#external-runners-byoxpc) are serial and queue behind launchd's configured respawn throttle.

### Are old versions of the app supported?

In general, no. Using old releases of PolicyWitness, including and especially correlating output across schema versions, is a research problem for the user. The development repo carries release binaries and test evidence, but backwards compatibility is not a goal.

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

Minimal skeleton (copy/paste):

```json
{
  "schema_version": 6,
  "specimen_id": "skeleton",
  "runner": { "mode": "standard" },
  "policy": { "format": "sbpl", "sbpl_source": "(version 1) (allow default)" },
  "probe_plan": []
}
```
Notes:
- The [accepted input contract](CONTRACT.md#accepted-input-contract) rejects
  unsupported request versions, unknown fields and wrong types explicitly.
  Optional nulls generally mean absence; actor equipment/requirements, termination dependencies and the actor equipment override map reject null. Parameter names inside `policy.params` remain
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
  "schema_version": 6,
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

Extension specimens use actors. Start with an unapplied issuer using `unentitled` equipment and a subject using `selected` equipment under its submitted policy. Equipment selects the signed worker copy; sandbox mode selects whether that process applies an SBPL policy. An unapplied actor may still inherit restrictions. A worker's signing readback does not establish its effective authority.

This two-actor specimen reads an owned file before consumption, issues and transfers a token, consumes it, reads again, releases the native handle, then makes another fresh read. Each read opens a new descriptor. The last read records the result after release without assuming revocation.

```sh
PW=/Applications/PolicyWitness.app/Contents/MacOS/policy-witness
PW_EXTENSION_DIR=$(mktemp -d /private/tmp/pw-extension.XXXXXX)
printf 'extension witness\n' > "$PW_EXTENSION_DIR/target"
cat > "$PW_EXTENSION_DIR/request.json" <<JSON
{
  "schema_version": 6,
  "specimen_id": "extension_lifecycle",
  "actors": [
    {"actor_id": "issuer", "equipment": "unentitled", "sandbox": {"mode": "unapplied"}},
    {"actor_id": "subject", "equipment": "selected", "sandbox": {"mode": "apply", "policy": {
      "format": "sbpl", "sbpl_source": "(version 1) (allow default) (deny file-read-data) (deny file-write*) (allow file-read-data (extension \"com.apple.app-sandbox.read\"))"}}}
  ],
  "phases": [
    {"phase_id": "before", "actor_id": "subject", "actions": [{"step_id": "read_before", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "$PW_EXTENSION_DIR/target"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "$PW_EXTENSION_DIR/target"}}]},
    {"phase_id": "supply", "actor_id": "issuer", "actions": [
      {"step_id": "issue", "extension": {"operation": "issue", "family": "file", "authority": "read", "target": "$PW_EXTENSION_DIR/target", "token_ref": "token"}},
      {"step_id": "deliver", "extension": {"operation": "transfer", "token_ref": "token", "recipient": "subject", "delivery_ref": "delivery"}}]},
    {"phase_id": "consume", "actor_id": "subject", "actions": [
      {"step_id": "consume_token", "extension": {"operation": "consume", "delivery_ref": "delivery", "handle_ref": "handle"}}]},
    {"phase_id": "during", "actor_id": "subject", "actions": [
      {"step_id": "read_during", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "$PW_EXTENSION_DIR/target"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "$PW_EXTENSION_DIR/target"}},
      {"step_id": "release", "extension": {"operation": "release", "handle_ref": "handle"}}]},
    {"phase_id": "after", "actor_id": "subject", "actions": [{"step_id": "read_after", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "$PW_EXTENSION_DIR/target"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "$PW_EXTENSION_DIR/target"}}]}
  ]
}
JSON
"$PW" run "$PW_EXTENSION_DIR/request.json" > "$PW_EXTENSION_DIR/run.json"
```

`read_write` selects the native read-write class and can name a directory. Issue passes the submitted absolute path unchanged with flags zero. Raw token bytes never appear in retained output. A published native result does not by itself establish file access or revocation: use the separate fresh reads and the actor's baseline.

Omitting `equipment` selects `selected`; explicit null is rejected. Optional actor `required_entitlements` is a list of unique entitlement keys that must each have boolean value `true` in that actor's bound and observed live code. Its default is an empty list; explicit null is rejected. This is independent of the controller's `runner.required_entitlements`, which preflights only the selected runner worker. The host verifies both production equipment artifacts against its sealed service-local inventory before launching any actor and inspects each usable actor's owned live code before any scheduled activation. Missing or mismatched equipment never substitutes the other role.

For a specimen that needs the issuer gone before consumption, add `"after_termination": {"actor_id": "issuer"}` to the `consume` phase. The source actor's last scheduled visit must precede the gated phase. The host waits for natural terminal completion and confirmed reaping before activation and query collection; it does not kill the source to satisfy the gate. The normal example has no such dependency.

Actor setup automatically reports bounded apparatus operations and their publication. Required apparatus failures stop before compilation/application; missing private extension symbols instead make their actions unavailable. A missing terminal setup publication does not prove application never happened. Read application observations, setup decisions and process disposition separately.

#### Actors: issue inside the sandbox and re-delegate

The actor form puts issuance inside a sandboxed process. Replace `policy` with
`actors`, give every phase an `actor_id`, and place `issue`, `transfer`,
`consume` and `release` actions in the phases of the actor that performs them.
An `unapplied` actor skips policy application and can request issuance under its actual inherited conditions; an `apply` actor applies its own policy once. Actors are
fresh processes that stay alive across their visits; one is active per phase
and the others are parked. The request below is the shared corpus's principal
specimen: `A` issues a read token for a file and transfers it to `B`; `B`,
whose policy denies ordinary reads and allows issuance only under a consumed
read extension, consumes it, reads, issues a second token and transfers it to
`C`; `C`, who can read only under a consumed extension, consumes and reads;
both handles are released.

```sh
PW=/Applications/PolicyWitness.app/Contents/MacOS/policy-witness
PW_ACTOR_DIR=$(mktemp -d /private/tmp/pw-actors.XXXXXX)
printf 'actor witness\n' > "$PW_ACTOR_DIR/target"
T="$PW_ACTOR_DIR/target"
READ='"sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "'"$T"'"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "'"$T"'"}'
cat > "$PW_ACTOR_DIR/request.json" <<JSON
{
  "schema_version": 6,
  "specimen_id": "extension_redelegation",
  "actors": [
    {"actor_id": "A", "equipment": "unentitled", "sandbox": {"mode": "unapplied"}},
    {"actor_id": "B", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source":
      "(version 1) (allow default) (deny file-read-data) (deny file-write*) (deny file-issue-extension) (allow file-read-data (extension \"com.apple.app-sandbox.read\")) (allow file-issue-extension (require-all (extension-class \"com.apple.app-sandbox.read\") (extension \"com.apple.app-sandbox.read\")))"}}},
    {"actor_id": "C", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source":
      "(version 1) (allow default) (deny file-read-data) (deny file-write*) (allow file-read-data (extension \"com.apple.app-sandbox.read\"))"}}}
  ],
  "phases": [
    {"phase_id": "b_before", "actor_id": "B", "actions": [{"step_id": "b_read_before", $READ}]},
    {"phase_id": "c_before", "actor_id": "C", "actions": [{"step_id": "c_read_before", $READ}]},
    {"phase_id": "initial_supply", "actor_id": "A", "actions": [
      {"step_id": "a_issue", "extension": {"operation": "issue", "family": "file", "authority": "read", "target": "$T", "token_ref": "ta"}},
      {"step_id": "a_to_b", "extension": {"operation": "transfer", "token_ref": "ta", "recipient": "B", "delivery_ref": "db"}}]},
    {"phase_id": "b_consume", "actor_id": "B", "actions": [{"step_id": "b_consume_first", "extension": {"operation": "consume", "delivery_ref": "db", "handle_ref": "hb"}}]},
    {"phase_id": "b_redelegate", "actor_id": "B", "actions": [
      {"step_id": "b_read_after", $READ},
      {"step_id": "b_issue", "extension": {"operation": "issue", "family": "file", "authority": "read", "target": "$T", "token_ref": "tb"}},
      {"step_id": "b_to_c", "extension": {"operation": "transfer", "token_ref": "tb", "recipient": "C", "delivery_ref": "dc"}}]},
    {"phase_id": "c_consume", "actor_id": "C", "actions": [{"step_id": "c_consume_second", "extension": {"operation": "consume", "delivery_ref": "dc", "handle_ref": "hc"}}]},
    {"phase_id": "c_effect", "actor_id": "C", "actions": [{"step_id": "c_read_after", $READ}, {"step_id": "c_release", "extension": {"operation": "release", "handle_ref": "hc"}}]},
    {"phase_id": "b_cleanup", "actor_id": "B", "actions": [{"step_id": "b_release", "extension": {"operation": "release", "handle_ref": "hb"}}]}
  ]
}
JSON
"$PW" run "$PW_ACTOR_DIR/request.json" > "$PW_ACTOR_DIR/run.json"
```

Read `actors`, `phases`, `steps`, `extension_events`, `transfers` and
`resources` under `data.runner_result`. Each actor's record names its process,
its setup and both policy hashes; each phase names the actor it activated and
that actor's visit number; each step and event names its actor. Compare the
three fresh reads of the target with their actors' policies, and credit
re-delegation only when the whole chain published: A's nonnull issue, custody,
delivery to B, B's consume, B's nonnull issue, delivery to C and C's consume,
with C's later read succeeding where its earlier read failed. A published NULL,
a failed consume or a denied read is a legitimate result of the run; a
missing publication is not a refusal. The shared coverage below says what each
record establishes.

<!-- BEGIN COPIED EXTENSION COVERAGE -->

File sandbox extensions carry read or read-write authority for a path from an
issuing process to a consuming process. PolicyWitness records their lifecycle
alongside probes of file access.

Extension specimens use actors: one fresh worker per named process, with explicit `issue`, `transfer`, `consume` and `release` actions. Start with an unapplied, unentitled issuer and an applied, selected subject. Add a third actor when testing whether a subject that consumed a token can issue a new one and transfer it onward. Every actor owns at least one phase; issuance takes place inside that actor after its own setup.

Each actor chooses `equipment: "selected"` (the default) or `"unentitled"`, independently of `sandbox.mode`. Both are signed copies of the same compiled worker. The selected copy carries the runner's supplied entitlements; the unentitled copy has an empty entitlement dictionary. Neither name establishes effective authority: an unapplied actor can inherit restrictions, and signing entitlements are associated code metadata. Optional actor `required_entitlements` require boolean `true` in that actor's selected equipment and live signing readback. The controller's `runner.required_entitlements` remains a separate preflight on the selected runner worker.

The service validates its own seal, its sealed `Contents/Resources/worker-equipment.json`, and both production worker artifacts before launching any actor. The inventory binds roles to relative paths, signed hashes, CDHashes, identifiers, teams, entitlements and the compiled worker ABI/build identity. There is no fallback between roles. After usable setup and before any activation or query collection, the host inspects the owned live process and matches its associated code to the binding. An inspection failure cancels scheduled activations while preserving any application already observed. Setup-failed or unlaunched actors remain unavailable without turning their missing inspection into a failure of healthy actors.

Actor setup automatically records bounded apparatus observations before policy compilation/application: core-limit handling, authority mapping and framing, descriptor closure and each extension-symbol lookup. Missing extension symbols make the corresponding actions unavailable; required apparatus failure prevents application. Setup publication, application observation and final process disposition remain separate. Missing terminal publication leaves application uncertain rather than proving it did not happen.

A phase may specify `after_termination: {"actor_id": "issuer"}` when that actor's last scheduled visit precedes the phase. The gate requires an owned natural reap after the source's final activation, including a nonzero exit or signal, before dependent activation and query collection. It does not require final phase completion. It does not kill an actor to satisfy the dependency. Expiry or an unusable dependency withholds that phase; cleanup and previously published facts retain their own meanings. The reply retains `actors[].owned_reap` and phase `activation_observation`; the gate references the source reap by `capture_ordinal`. Missing clock timestamps retain facts without establishing gate order.

#### Request forms

| Form | Available operations |
| --- | --- |
| Actor specimen | Ordinary probes and explicit issue, transfer, consume and release actions. Equipment and policy application are selected per actor. |
| Ordinary single-worker specimen | Ordinary probes and phases without extension actions. |

#### Supported families and native calls

| Family | `authority` | Native class | Issue | Consume | Release |
| --- | --- | --- | --- | --- | --- |
| `file` | `read` | `com.apple.app-sandbox.read` | `sandbox_extension_issue_file(class, path, 0)` | `sandbox_extension_consume(token)` | `sandbox_extension_release(handle)` |
| `file` | `read_write` | `com.apple.app-sandbox.read-write` | the same call with the read-write class | the same | the same |

Issuance uses flags zero and passes the submitted absolute path unchanged.

#### Operations and references

| Operation | Who | Operands | Produces |
| --- | --- | --- | --- |
| `issue` | an actor | `family`, `authority`, absolute `target`, new `token_ref` | a token the host takes into custody when the native call returns one |
| `transfer` | the actor that issued the token | `token_ref`, `recipient` actor, new `delivery_ref` | a delivery the recipient accepts while parked or during its own wait |
| `consume` | the recipient of a delivery | `delivery_ref`, new `handle_ref` | a candidate handle when the native call returns one |
| `release` | the actor that consumed | `handle_ref` | the native release result |

References are specimen-local names. Each `token_ref`, `delivery_ref` and
`handle_ref` is assigned once, used only after its producer in action order,
and stays with its owner: only the issuer transfers its token, only the
recipient consumes a delivery, only the consumer releases its handle. A
delivery may be consumed more than once with distinct handles, a token may be
transferred to several recipients or back to its issuer, and each handle is
released at most once.

#### `exec` limitation

An actor that issues, transfers, receives, consumes or releases cannot also
run an `exec` attempt; another actor in the same specimen can. The capacities
are in the [limits](#limits).

#### How authority moves

Each actor has its own evidence region and its own authority region; neither
is visible to another actor or to a validator. Each admitted issue has its own
outbound slot, and each transfer has its own request and answer cell. An issued
token is published once; its bytes remain immutable until the host copies or
rejects them and erases that slot. A timeout cannot reuse the slot or consume
another action's answer. A transfer is a request the
host answers: it copies the custody bytes into the recipient's assigned inbound
slot, waits for the recipient to validate framing and its preassigned source,
action and delivery references and acknowledge them, compares the
two copies, settles the delivery as usable or withdrawn, and reports the outcome
to the sender. Consumption requires the host's usable settlement, so a
self-transfer cannot consume or erase bytes while the host compares them.

The recipient accepts a delivery while parked between its visits; it consumes
only in a later visit of its own, after that phase's queries were collected and
the host released it. The host erases private custody at the token's last
declared transfer and at teardown. The worker erases settled inbound slots at
last use and ordinary exit; the host clears remaining shared slots after
confirmed process exit. If worker termination remains unresolved, the host
records that uncertainty and avoids erasing shared bytes that may still be in
use. Tokens never enter the request, the reply, logs or diagnostics.

Every actor's worker is launched with an empty environment, a policy pipe on
stdin, and stdout and stderr opened on the null device. Its other inherited
endpoints are its evidence region, readiness pipe and, when needed, authority
region. Other host descriptors are closed at exec. The host disables core dumps before any token
can arrive, and so does each worker before mapping its region.

#### What each observation establishes

| Observation | Establishes | Does not establish |
| --- | --- | --- |
| `extension_events[]` with operation `issue`, `status: returned`, `native_nonnull: true` | That actor's process made the native issue call for the recorded class and path and received a nonnull result of the recorded length. | That the token is usable by anyone, or why it was granted. |
| `issue` with `native_nonnull: false` | The native call returned NULL; `errno` is the value saved immediately after it. | A sandbox cause for the refusal. |
| `resources.tokens[].status: issued` | The host accepted the published bytes into custody. | Delivery or consumption. |
| `transfers[].status: delivered` with `equality: equal` | The recipient acknowledged a framed delivery whose bytes equalled the host's custody copy. | Consumption or access. |
| `transfers[]` with any other status | Where the exchange stopped: custody absent, recipient refusal, timeout, mismatch. No native result belongs to a transfer. | A native refusal. |
| `consume` with `status: returned` and `native_result` other than the failure sentinel | That actor received a candidate handle for the delivery it named. | Effective permission for any operation. |
| `release` with `status: returned` | The native release call returned the recorded value. | Revocation of access or undoing of earlier effects. |
| `status: unavailable` with an `unavailable_reason` | The named operation was not called for the recorded reason (no delivery, no handle, missing native symbol, no authority channel, repeated action). | A native result of any kind. |
| Resource status `not_reached` | Terminal lifecycle evidence establishes that the producing action was not reached. | Absence of a result alone is insufficient; interrupted or unknown producers remain `unresolved`. |
| `status: unresolved` | The action's result was never published: the actor died, was stopped or never reached it. | That the call did not happen. |
| A fresh read that succeeds after a consume | That process could open and read the file at that moment. | That the consumed extension caused it; compare with the actor's baseline read and its policy. |

Native results, host custody facts, recipient acknowledgements and the
validator's predictions are separate records with separate writers. A source
acknowledgement requires the source action's published matching answer; a
pending request alone does not establish that the source observed an answer. The
`sandbox_check` query cannot represent an extension class beside a path, so
`file-issue-extension` queries cannot express that full issuance predicate and
extension events stay outside the query/attempt comparison.

#### What can go wrong, and how it reads

| Situation | Reading |
| --- | --- |
| Required authority-region or custody setup fails | Host preparation refuses launch, or automatic worker setup records a terminal apparatus failure before policy compilation/application. This is distinct from missing native symbols or a native refusal. |
| An actor's policy does not compile or apply | That actor's `setup_status` is `setup_failed`; its visits are `actor_unavailable`; other actors' evidence stands. The run is `runner_failed`. |
| An application is published during cleanup after setup expires | Setup stays `setup_timeout` and its visits remain unavailable; `applied` and `application_count` retain the later observed application. |
| An actor dies during a visit | The visit records how it ended; the scheduler establishes the actor is reaped before activating anyone else; later visits of that actor are unavailable. |
| The shared lifetime cutoff expires | A worker that reaches a checked wait publishes a timing failure and exits. A blocked native call may prevent that check; host cleanup and missing publication remain separate observations. |
| The issuing actor publishes a token the host rejects | `resources.tokens[].status` is `issued_uncustodied` and `transfers[]` of that token read `custody_unavailable`. |
| A recipient rejects or does not acknowledge a delivery | The transfer reads `recipient_rejected`, `recipient_timeout` or `recipient_unavailable`; the recipient's later consume is `unavailable` for want of a delivery. |
| Native symbols are missing in the worker | The affected operations are `unavailable` with `native_api_unavailable`; unrelated reads still run. |

<!-- END COPIED EXTENSION COVERAGE -->

### Try an accepted request and a refusal

This specimen asks a sandbox query and attempts to create an empty file. Use a
fresh directory so you can observe whether the file was created. Adjust `PW`
to your installed app; the commands need no repository files or extra tools.

```sh
PW="/Applications/PolicyWitness.app/Contents/MacOS/policy-witness"
PW_EXAMPLE_DIR=$(mktemp -d /private/tmp/pw-input.XXXXXX)
cat > "$PW_EXAMPLE_DIR/request.json" <<JSON
{
  "schema_version": 6,
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
"$PW" run "$PW_EXAMPLE_DIR/request.json" > "$PW_EXAMPLE_DIR/run.json"
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
"$PW" run "$PW_EXAMPLE_DIR/typo.json" > "$PW_EXAMPLE_DIR/refusal.json" || PW_REFUSAL_RC=$?
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
| Capacity | A plan contains more steps than this build admits. | Inspect `admission_failure` for the field, actual count and maximum, and find the field in the Specimen admission table under [Limits](#limits). Revise the specimen or use a build with sufficient capacity; PW never truncates the plan. |
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
with less evidence than it produced. This is the inventory of numeric capacities,
budgets and evidence-retention bounds: what each counts and what happens at its
boundary. Fitting these bounds does not establish that a request is meaningful
or that evidence will be available. Request grammar, extension ownership and
action order, receipt prerequisites and prediction eligibility still apply.
A fitting query or complete record may supply no usable prediction.

Numeric capacity refusals carry `data.runner_result.admission_failure`, which names the
`field`, the `actual` count, the `maximum` and the `unit`, with location details
where available and `origin: "runner_host"`. Find that field in the "Refusal
names" column of the Specimen admission table; the row says what was measured
and which location fields are reported. To check a specimen before submitting
it, compare it with the same rows. Meaning refusals such as `repeated_consume`
use `request_failure`; not every refusal supplies numeric counts. Its path is
retained whole or withheld as null under the diagnostic bounds below.

Request files must be UTF-8 JSON. A file containing invalid UTF-8 yields exit
code 2 and `result.normalized_outcome: "tool_error"`, with an error beginning
`failed to read request.json` and `data.runner_result: null`. It has no
`admission_failure` to look up.

### How to read the tables

The Refusal names column gives literal `admission_failure.field` values, except
where it explicitly names a `request_failure` code and path instead. In indexed
patterns, replace `{actor}`, `{phase}` and `{action}` with the
zero-based decimal position in that request array; an action position is local
to its phase. Braces are notation, not emitted text: for example,
`actors.{actor}.sandbox.policy.sbpl_source` can emit
`actors.0.sandbox.policy.sbpl_source`. Dots in field values are literal.
A `request_failure.path` is a separate array of string components, subject to
the diagnostic retention bounds; it is not the `admission_failure.field`.
For numeric refusals, names following “with” identify separate admission-record fields.

An ordinary request has one worker and no extension actions. Extension
specimens use the actor form, with
up to <!-- span limits.actors.value -->8<!-- /span --> workers and <!-- span limits.actor_phases.value -->16<!-- /span --> phases globally,
and aggregate issue/transfer/consume/release counts. The `extensions` field is
refused, including null. Source and parameter limits apply separately to each policy;
the total action limit applies once to the whole specimen. Authority participation,
including being a transfer recipient, excludes exec in that actor; a separate
actor may exec.

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
  Even elapsed deadlines do not preempt blocked native calls or guarantee final cleanup time.
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
  identify rejected queries, truncated output and unavailable parsing. Truncated JSON is not parsed as a complete reply.
- Evidence capture bounds optional evidence: child output and
  compiled-object receipts. Excess can retain a prefix with a truncation marker
  or make capture unavailable, as the row describes. Attempt
  status and `sandbox_check` verdicts are unchanged by these evidence limits.
- Diagnostic helpers lists the limits of fallback `sbpl-check` calls after an
  eligible terminal XPC error. These independent compile diagnostics can run
  before host admission; they do not establish application. Actor fallback
  associates each selected policy with its actor label when present. Malformed
  requests can supply more policies than the admitted actor limit. Each helper's
  retention cap therefore bounds neither their cumulative envelope nor process
  memory. Its import inventory does not control compiler import resolution.

<!-- BEGIN GENERATED LIMITS -->

### Specimen admission

| Limit | Value | Refusal names | Counting and consequence | Control |
| --- | --- | --- | --- | --- |
| Policy source (`policy_source`) | 262,143 UTF-8 bytes | `policy.sbpl_source` or `actors.{actor}.sandbox.policy.sbpl_source` | Final SBPL source after augments, separately for each supplied policy, including each actor policy. Imported file contents are not added to this count. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Total actions and queries (`probe_steps`) | 256 items | `probe_plan` or `phases.actions` | Total ordinary pairs and extension lifecycle actions across the complete specimen, including all actor phases. A pair counts once; a lifecycle action occupies one slot but supplies no query. Neither phases nor actors multiply this cap. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Policy parameters (`policy_parameters`) | 1,024 items | `policy.params` or `actors.{actor}.sandbox.policy.params` | Entries per policy, separately for each actor policy; not an aggregate across actors. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Step ID (`step_id`) | 63 UTF-8 bytes | `step_id`, with `step_index`; extension actions: `phases.{phase}.actions.{action}.step_id` | Each `step_id`. A refused ordinary probe ID is identified by `step_index`; a refused extension-action ID is identified by its indexed field. The refused ID is never echoed. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Attempt target (`attempt_target`) | 511 UTF-8 bytes | `target`, with `step_id` and `step_index` | Each attempt target (path, service or sysctl name). For exec, this is also argument zero. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Supplied exec arguments (`exec_arguments`) | 15 items | `args` with unit `items`, with `step_id` and `step_index` | Arguments supplied in `attempt.args`; the exec target is the additional argument zero. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Each supplied exec argument (`exec_argument`) | 127 UTF-8 bytes | `args` with unit `utf8_bytes`, with `index`, `step_id` and `step_index` | Each supplied exec argument; the target has its own larger limit. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Parameter key (`parameter_key`) | 127 UTF-8 bytes | `key` | Each parameter key. A refused key is identified by field and byte count and is never echoed. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Parameter value (`parameter_value`) | 383 UTF-8 bytes | `value` or `actors.{actor}.sandbox.policy.value`, with `parameter_key` | Each parameter value. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Query operation (`query_operation`) | 127 UTF-8 bytes | `sandbox_check.operation`, with `step_id` and `step_index` | Each `sandbox_check.operation`, also echoed per step in the reply. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Query filter value (`query_filter_value`) | 511 UTF-8 bytes | `sandbox_check.filter.value`, with `step_id` and `step_index` | Each `sandbox_check.filter.value` when present, including for `none` and unrecognized filter kinds. The query value and attempt target are counted separately, even when they name different paths. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Probe filter and attempt labels (`probe_plan_label`) | 127 UTF-8 bytes | `sandbox_check.filter.kind`, `attempt.kind` or `attempt.action`, with `step_id` and `step_index` | Each `sandbox_check.filter.kind`, `attempt.kind` and `attempt.action`. Unknown labels within the capacity still receive a meaning refusal. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Specimen ID (`specimen_id`) | 255 UTF-8 bytes | `specimen_id` | The `specimen_id` string. Echoed once per reply; a refused ID is replaced by `<admission_refused>`. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Request labels (`request_label`) | 63 UTF-8 bytes | `run_kind`, `policy.format`, `actors.{actor}.sandbox.mode`, `actors.{actor}.sandbox.policy.format`, `phases.{phase}.actions.{action}.extension.operation`, `phases.{phase}.actions.{action}.extension.family` or `phases.{phase}.actions.{action}.extension.authority` | Each run_kind, policy.format, actors[].sandbox.mode, actors[].sandbox.policy.format and extension-action operation, family or authority label. A refused run_kind is omitted; a refused legacy format reads unknown. Actor metadata is not echoed in a capacity refusal. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Test-seam executable paths (`test_override_path`) | 1,023 UTF-8 bytes | `_test_overrides.worker_executable_path`, `_test_overrides.validator_executable_path` or `_test_overrides.actor_equipment_executable_paths.{role}` | Each executable override path. Every path that fails byte or NUL admission is omitted from a refusal echo, even when another field is refused first. Actor equipment overrides are keyed by selected or unentitled role. Excess returns `bad_request` with `admission_failure`. | Fixed. |
| Ordinary phases (`phase_count`) | 8 items | `phases` | Explicit phases in an ordinary request; probe_plan normalizes to one phase. Actor requests use actor_phases. Excess returns admission_failure before any child. | Fixed. |
| Phase identity (`phase_id`) | 63 UTF-8 bytes | `phase_id`, with `index` | UTF-8 payload bytes in each phase_id. NUL is refused independently. Excess returns admission_failure without echoing the refused identity. | Fixed. |
| Extension references and recipients (`extension_reference`) | 63 UTF-8 bytes | `phases.{phase}.actions.{action}.extension.token_ref`, `.handle_ref`, `.delivery_ref` or `.recipient` | Each token, handle or delivery reference and each extension transfer recipient identifier; nonempty, no embedded NUL. Excess returns `admission_refused`; references must also satisfy actor resource ownership and action order. | Fixed. |
| Specimen actors (`actors`) | 8 items | `actors` | Actor objects in one actor-form request; every phase names one of them. Excess returns `admission_refused` before any child. | Fixed. |
| Actor-form phases (`actor_phases`) | 16 items | `phases` | All explicit phases across the complete actor-form request, including empty visits; each visits one actor. Not a per-actor allowance. Excess returns `admission_refused` before any child. | Fixed. |
| Extension issues (`actor_issues`) | 32 items | `extension.issue` | Issue actions across the complete actor-form specimen; each assigns one token reference. Excess returns `admission_refused` before any child. | Fixed. |
| Extension transfers (`actor_deliveries`) | 64 items | `extension.transfer` | Transfer actions across the complete actor-form specimen; each assigns one delivery reference. Excess returns `admission_refused` before any child. | Fixed. |
| Extension consumes (`actor_handles`) | 64 items | `extension.consume` | Consume actions across the complete actor-form specimen; each assigns one handle reference. Excess returns `admission_refused` before any child. | Fixed. |
| Extension releases (`actor_releases`) | 64 items | `extension.release` | Release actions across the complete actor-form specimen; at most one per handle. Excess returns `admission_refused` before any child. | Fixed. |
| Actor identifier (`actor_id`) | 63 UTF-8 bytes | `actors.{actor}.actor_id` or `phases.{phase}.actor_id` | Each actor declaration identifier and phase actor reference; nonempty, no NUL. Extension transfer recipient identifiers use the extension_reference row. Excess returns `admission_refused`; empty or duplicate identifiers are request refusals. | Fixed. |
| Issue target (`extension_issue_target`) | 1,023 UTF-8 bytes | `phases.{phase}.actions.{action}.extension.target` | Absolute path an issue action submits; passed to the native call unchanged. Excess returns `admission_refused`; a relative target is a request refusal. | Fixed. |
| Actor entitlement requirements (`actor_required_entitlements`) | 64 items | `actors.{actor}.required_entitlements` | Unique nonempty required boolean entitlement keys per actor. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |
| Actor entitlement requirement key (`actor_entitlement_key`) | 255 UTF-8 bytes | `actors.{actor}.required_entitlements.{key}` | Each actor requirement key, excluding NUL. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |

### Execution budgets

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Host reply flush delay (`host_exit_delay`) | 50 milliseconds | Delay scheduled once by the terminal execution or abandoned-reservation owner. The unsandboxed host schedules exit after the delay. An occupied host grants no further reservation; client acquisition can reconnect before submission. | Fixed. |
| Runner verification wait (`runner_verify_wait`) | 5,000 milliseconds | Default allowance for the fixed runner verify specimen, shared by reservation acquisition and the execution reply wait. Overall expiry reports xpc_timeout with the captured submission state. Acquisition may stop earlier at its attempt bound. Expiry after invocation does not establish nonexecution or cancel host work; worker/validator budgets remain separate. | Flag `--timeout-ms` on `runner verify`. |
| Worker policy delivery (`worker_policy_transfer`) | 5,000 milliseconds | One absolute monotonic deadline per policy delivery starting immediately after spawn; partial writes and interrupted calls do not restart it. Actor delivery is also capped by the remaining aggregate setup allowance. Expiry closes the input pipe and enters host cleanup with policy_transfer_timeout and policy_transfer_deadline; no write errno is invented. The worker, reaching EOF, publishes the count it read beside the host's expected length and refuses a different length before compiling; an observed refusal takes worker-failure precedence. | Fixed; internal driver controls may shorten it. |
| Worker readiness hint wait (`worker_ready_wait`) | 1,000 milliseconds | Elapsed monotonic wait after successful policy delivery and readiness-pipe setup, capped for an actor by remaining setup allowance. Expiry can leave `runner_subprocess.ready_byte_received: false` while the run continues. | Fixed. |
| Worker publication wait (`worker_sentinel_wait`) | 120,000 milliseconds | Elapsed monotonic publication wait for ordinary execution, starting after the readiness wait and excluding synchronous validator collection. Actor execution uses actor_execution_allowance instead. Expiry can yield `runner_timeout` with partial evidence and reported cleanup results. | Fixed; `_test_overrides.worker_timeout_ms` replaces the ordinary default with a floor of 50 ms and no ceiling. It does not change the actor schedule allowance. |
| Actor setup allowance (`actor_setup_allowance`) | 10,000 milliseconds | One aggregate elapsed monotonic allowance starting before authority-region preparation and ending at setup disposition, including launches, policy delivery and readiness. Remaining setup caps each subwait. An actor whose setup is unresolved at expiry is stopped and reported `setup_timeout`; independent actors keep their own dispositions. | Fixed. |
| Actor schedule allowance (`actor_execution_allowance`) | 120,000 milliseconds | One elapsed monotonic allowance for the complete serial actor schedule after setup, excluding synchronous validator collection; not one allowance per actor. Expiry ends the current visit (`arrival_timeout` or `completion_timeout`) and cancels the remaining schedule; every earlier publication is retained. | Fixed. |
| Actor collection allowance (`actor_collection_allowance`) | 30,000 milliseconds | One aggregate allowance for validator planning and synchronous collection across all actor phases. This is the actor counterpart of phase_collection_wait, not an additional pool. Exhaustion marks later phases `budget_exhausted`; earlier collections are retained. | Fixed; `_test_overrides.validator_total_timeout_ms` can reduce it to at least 1 millisecond. |
| Actor release wait (`actor_release_wait`) | 60,000 milliseconds | The worker's wait from a visit's arrival to the host's release of that visit's ordinal. Expiry refuses the visit with a published timing failure, as the single-worker release wait does. | Fixed. |
| Authority exchange allowance (`actor_exchange_allowance`) | 5,000 milliseconds | Each worker custody-acknowledgement or transfer-answer wait uses sampled continuous time; each host recipient-acknowledgement wait uses elapsed monotonic time, also capped by remaining schedule allowance. Expiry is a transport observation (`timeout` custody or a `host_timeout`/`recipient_timeout` transfer status), never a native result. | Fixed. |
| Actor lifetime cutoff (`actor_lifetime_cutoff`) | 180,000 milliseconds | One absolute continuous-clock cutoff shared by all actors, calculated before setup. Parked waits, collection and system sleep advance this clock. An already-past cutoff refuses before policy reading; a worker that observes expiry at a checked activation, release or exchange wait reports a timing failure. Native calls and final cleanup can outlast it. | Fixed. |
| Worker exit grace (`worker_exit_grace`) | 1,000 milliseconds | Elapsed monotonic wait for an unreaped worker after the host stores an exit request. Expiry requests `SIGKILL`. Termination and reap failures remain reported. | Fixed. |
| Worker release wait (`worker_proceed_wait`) | 60,000 milliseconds | Sampled continuous time for each phase release after the worker arrives, converted once before application to a ceiling tick allowance. Continuous time includes system sleep. Expiry records the phase index and milliseconds and prevents its actions. An unusable sample, an earlier rejected sample or an unrepresentable plan exclusion records a local timing refusal with its reason instead; neither invents a native result or errno. Earlier published phase evidence remains. | Fixed. |
| Nominal release margin (`validator_release_margin`) | 5,000 milliseconds | Informative allowance between the validator budgets and worker release wait. No separate timeout or refusal occurs at this value. | Not enforced; no flag. |
| Validator I/O test override floor (`validator_io_override_floor`) | 50 milliseconds | Minimum proposed `_test_overrides.validator_io_timeout_ms`. Smaller supplied values propose 50 ms; the reply mirrors the supplied value. The remaining aggregate collection allowance caps the effective deadline, including below this floor. | Fixed. |
| Validator I/O deadline (`validator_io_wait`) | 30,000 milliseconds | Default elapsed monotonic deadline for one phase’s query delivery and verdict collection, capped by the remaining aggregate collection allowance. Received verdicts survive an I/O timeout; cleanup results remain reported. | Fixed; `_test_overrides.validator_io_timeout_ms` changes the proposed deadline, floored at 50 ms without a ceiling. The aggregate remainder can cap the effective deadline below that floor. |
| Validator exit grace (`validator_exit_grace`) | 1,000 milliseconds | Elapsed monotonic wait for validator exit after collection closes. Subsequent termination and final reap can overrun it. Expiry requests `SIGKILL`. Termination and reap failures remain reported. | Fixed. |
| Exec child deadline (`exec_child_wait`) | 10,000 milliseconds | Continuous time after successful spawn, limited by the remaining `exec_attempt_budget`. Expiry fails the attempt while preserving any observed natural exit code. An unusable sample or unrepresentable child deadline ends observation as a local timing fault with no errno. Cleanup results remain reported; an observed leader exit does not establish that every descendant stopped. | Fixed. |
| Exec attempt budget (`exec_attempt_budget`) | 115,000 milliseconds | Continuous time from each worker origin before setup, shared by that worker's exec steps. Includes setup and intervening work; excludes acknowledged release waits and, for actors, accepted parked activation waits. This per-worker budget is separate from the global actor schedule allowance. Exhaustion refuses a later spawn with `exec_failed` and `ETIMEDOUT`, no `child_pid` and no sandbox attribution. An unusable sample refuses spawn with no errno, or after spawn records a local timing fault beside any native error; after a rejected sample, later spawns are refused. Blocking spawn and non-exec operations may outlast this allowance. | Fixed. |
| Exec child reap grace (`exec_reap_grace`) | 1,000 milliseconds | Continuous-time allowance to confirm an exec child's exit after observation ends. Expiry, an unusable sample or a wait error leaves reaping unconfirmed and supplies no invented exit status; an unusable clock still permits the immediate exit check. Failed group termination leaves only an immediate exit check. This is not a total cleanup runtime limit. | Fixed. |
| Runner RPC wait (`client_rpc_wait`) | 240,000 milliseconds | One absolute client allowance, including helper launch/stdin delivery, reservation acquisition and the execution reply wait. Direct helper invocation starts after reading input. Overall expiry reports xpc_timeout with the captured submission state. Acquisition may stop earlier at its attempt bound. Expiry after invocation does not establish nonexecution or cancel host work; worker/validator budgets remain separate. | Flag `--timeout-ms`, floored at 1 ms; values above this default are permitted. |
| Runner removal teardown wait (`runner_remove_teardown_wait`) | 1,000 milliseconds | Nominal wait for a removed BYOXPC service to disappear from launchd. The cleanup observation records the service checks and the wait. A service still listed at expiry retains its cleanup record with a warning; a later `runner remove` or `runner reconcile` continues recovery. | Fixed. No wait when the removal issued no bootout. |
| External runner respawn throttle (`byoxpc_throttle_interval`) | 1 second | `ThrottleInterval` in every launchd plist that `runner install` generates. The host exits after each specimen and launchd starts the job at most once per interval; the wait is counted from the previous launch, not from the previous exit. The setting controls launch pacing, not a guaranteed request-delivery time. Without the key launchd uses its ten-second default. Acquisition reaching an occupied or retiring host can retry without sending the specimen. | Fixed in the generated plist. An installed plist can be edited by hand after `runner remove` and a fresh install; the registry's plist hash then differs and removal reports the ownership disagreement. |
| Aggregate phase collection allowance (`phase_collection_wait`) | 30,000 milliseconds | Cumulative monotonic planning and collection time across ordinary phases. Actor form uses the single actor_collection_allowance pool. Remaining allowance caps each validator I/O deadline; cleanup and scheduling can overrun it. After exhaustion, subsequent predictions are unavailable; the worker can still execute released attempts. | Fixed; `_test_overrides.validator_total_timeout_ms` can reduce it to at least 1 millisecond. |
| Sysctl value-read destination (`sysctl_read_bytes`) | 4,096 bytes | Destination for one post-apply sysctlbyname value read with a non-null buffer; no sizing call or retry. Larger values can fail within this bound. Returned value bytes and post-call length are discarded; a failed call does not diagnose whether capacity was insufficient. | Fixed. |
| Reservation lease (`reservation_lease`) | 5,000 milliseconds | Requested unused lease, capped by the host; the client requests no more than its remaining allowance. Expiry or owner disconnect retires the unused host. Submission checks expiry atomically and an old timer cannot terminate execution. | Fixed. No renewal. |
| Reservation RPC wait (`reservation_rpc_wait`) | 5,000 milliseconds | Maximum wait for one reserve reply, also bounded by the original overall client deadline. Expiry abandons and invalidates that connection; acquisition may continue without submitting a specimen. | Fixed per-attempt ceiling. |
| Reservation acquisition attempts (`reservation_attempts`) | 256 items | Every opened acquisition attempt, including transport failures and occupied replies. Exhaustion ends acquisition explicitly at attempt_limit with no submission; it can precede the overall timeout. Every attempted acquisition stays in the capture. | Fixed. |
| Reservation retry delay (`reservation_retry_delay`) | 100 milliseconds | Minimum delay between a failed/occupied attempt and another connection, within the remaining allowance. No delay after a successful grant. Scheduling may take longer; neither waiting nor progress renews the deadline. | Fixed minimum. |
| Actor termination dependency wait (`actor_termination_wait`) | 5,000 milliseconds | Maximum wait before a dependent phase, additionally capped by remaining execution and lifetime allowances. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |

### Queries and transport

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Validator query payload (`validator_query_payload`) | 65,534 bytes | Serialized JSON bytes for one validator probe, excluding the final LF. JSON escapes count toward this size. An overlong line produces one `parse_error` without a step ID; later lines remain usable. Admitted specimens stay below this limit. | Fixed. |
| Runner client output (`controller_output`) | 285,212,672 bytes | Captured bytes per stdout or stderr stream from the runner client. Stdout carries a binary capture with opaque host bytes. Excess is marked truncated; a truncated capture establishes neither submission nor host evidence. Excess is marked truncated. Truncated client capture is not parsed, so submission remains unknown and no host evidence is inferred. | Fixed per-stream retention allowance; no flag. |
| Policy helper output (`policy_helper_output`) | 8,388,608 bytes | Captured bytes per stdout or stderr stream from each sbpl-check invocation, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Fixed. |
| Rejected validator frame context (`validator_fault_context`) | 256 bytes | Retained prefix of the first rejected validator frame, measured before base64 encoding. `frame_bytes`, `retained_bytes` and `context_truncated` describe how much context was retained. | Fixed. |
| Validator reply frame (`validator_reply_frame`) | 8,192 bytes | UTF-8 bytes in one NDJSON frame, before parsing. An overlong frame is rejected with bounded context; earlier complete records remain. | Fixed. |
| Validator records per query (`validator_records_per_query`) | 2 items | Retained-record allowance is twice the number of queries submitted to that phase collector, sized before writes; at most 512 records across a production run. The first excess record produces a decode fault; no excess record enters association. | Fixed. |
| Validator reply storage per query (`validator_reply_bytes_per_query`) | 16,384 bytes | Twice the frame bound per query submitted to the phase collector, sized before writes; at most 4,194,304 retained stdout bytes across a production run. The first read crossing the cap closes collection with byte_limit; its cutoff fragment is never decoded as a complete frame. | Fixed. |
| Validator step_id string (`validator_reply_step_id`) | 63 UTF-8 bytes | Bytes in a decoded validator step_id string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator operation string (`validator_reply_operation`) | 127 UTF-8 bytes | Bytes in a decoded validator operation string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator filter_type string (`validator_reply_filter_type`) | 63 UTF-8 bytes | Bytes in a decoded validator filter_type string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator filter_value string (`validator_reply_filter_value`) | 1,023 UTF-8 bytes | Bytes in a decoded validator filter_value string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator outcome string (`validator_reply_outcome`) | 63 UTF-8 bytes | Bytes in a decoded validator outcome string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Validator error string (`validator_reply_error`) | 511 UTF-8 bytes | Bytes in a decoded validator error string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated. | Fixed. |
| Transient token storage (`extension_token_storage`) | 16,384 bytes | Fixed token array including its terminating NUL; never part of a retained reply. Empty, oversized or malformed publications cannot supply a consumed token. | Fixed. |
| Maximum token payload (`extension_token_payload`) | 16,383 bytes | Nonempty token bytes excluding the required trailing NUL. Larger native results report `token_oversized`; malformed delivery is unavailable. | Fixed. |
| Reservation control bytes (`reservation_control_bytes`) | 65,536 bytes | Encoded reservation request or control reply, before JSON decoding. Excess is a protocol failure. No oversized control can grant execution. | Fixed. |
| Client error message (`client_error_message`) | 1,024 UTF-8 bytes | Retained error prose at a Unicode boundary. Excess is truncated with message_truncated; error stage, domain and native code remain separate observations. | Fixed. |
| Client error domain (`client_error_domain`) | 128 UTF-8 bytes | Retained native error domain at a Unicode boundary. Excess is truncated with domain_truncated. No arbitrary userInfo dictionary is retained. | Fixed. |
| Client host reply retention (`client_reply_retention`) | 96,468,992 bytes | Host result bytes retained before base64 encoding in the client capture. Excess is explicitly truncated and cannot be admitted as a complete host result; received and retained byte counts remain distinct. | Fixed; must cover the informative maximal reply. |
| Authority setup encoded reserve (`authority_setup_reply`) | 524,288 bytes | Conservative JSON allowance for host run, eight regions, thirty-two custody slots and eight workers; at most 388 operation cells. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |
| Typed response frame (`porcelain_frame_bytes`) | 134,217,728 bytes | One complete binary client capture or host reply, including its frame header. Larger frames are refused before typed record interpretation. | Fixed. |
| Typed decoded storage (`porcelain_decoded_storage_bytes`) | 134,217,728 bytes | One reader frame charges string bytes, opaque bytes and typed collection slots to a shared logical-storage budget. A charge exceeding the remaining budget refuses decoding before allocation; fixed record storage and allocator overhead are not physical peak-memory claims. | Fixed. |
| Typed response nesting (`porcelain_nesting`) | 32 levels | Reader cursor nesting within one binary frame; the schema generator separately refuses deeper record graphs. Deeper input is refused before reading another nested value. | Fixed. |

### Evidence capture

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Exec child output per stream (`exec_stream`) | 1,023 bytes | Retained stdout or stderr bytes for each exec child. An overflow marker occupies part of this allowance. Excess output is not retained. | Fixed. |
| Primary worker diagnostic (`worker_diagnostic`) | 4,095 bytes | Retained primary diagnostic bytes per worker, hence separately per actor. The reply reports retained length and truncation state; this is not a complete transcript. | Fixed. |
| Optional compiled-object capture (`compiled_profile`) | 1,048,576 bytes | Raw bytecode bytes per optional compiled-object receipt before base64 encoding, separately for each opted-in apply actor. Oversized or unsupported objects leave capture unavailable without preventing policy application. | Fixed. |
| Worker observed path (`observed_path`) | 1,023 bytes | Retained bytes in each worker-observed path. Path observation can be absent or bounded; a host-side path diagnostic is a separate observation. | Fixed. |
| Worker attempt error text (`attempt_error`) | 255 bytes | Retained bytes in each worker attempt error message. Error text is bounded; structured result and status fields remain separate. | Fixed. |
| Phase records per worker region (`phase_records`) | 16 items | Fixed phase records in each worker shared header. Ordinary requests admit eight phases; public actor requests admit sixteen phases globally, so one actor can use all sixteen records. A worker refuses a header naming more phases than its records before application. | Fixed. |
| Authority slot storage (`authority_slot_bytes`) | 16,448 bytes | One token publication slot in an actor's authority region: a fixed header and the token buffer. A region holds one outbound slot per admitted issue and one inbound slot per admitted delivery to that actor, with distinct bounded transfer answer cells; nothing in it enters the reply. | Fixed. |
| Phase publication storage (`phase_publications`) | 512 bytes | Sixteen fixed 32-byte phase records within each shared header, one per visit an actor can be activated in; the legacy form uses the first eight. The legacy and actor-form phase caps prevent excess publication storage. | Fixed. |
| Fresh file-read prefix (`fresh_read_bytes`) | 64 bytes | At most one read from a freshly opened descriptor; content_hex encodes only the returned prefix. Reads of longer files remain supported; the bounded result does not claim complete file contents. | Fixed. |
| Request-failure path depth (`request_failure_path_components`) | 8 items | Components in a retained request_failure.path, including object keys and array positions. Excess withholds the entire path as null; no shortened location is substituted. | Fixed. |
| Request-failure path component (`request_failure_path_component`) | 63 UTF-8 bytes | Each component in a retained request_failure.path. The separate parameter_key admission-record echo has its own larger bound. Excess withholds the entire path as null; no shortened location is substituted. | Fixed. |
| Worker authority setup trailer (`authority_setup_trailer`) | 832 bytes | 64-byte header plus sixteen 48-byte independently published operation cells. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |
| Worker authority setup operation cells (`authority_setup_cells`) | 16 items | Fixed operation slots per worker trailer, including separate cleanup facts. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |
| Equipment entitlement readback (`equipment_entitlement_bytes`) | 65,536 UTF-8 bytes | UTF-8 XML payload in each entitlement readback row. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |
| Equipment static binding records (`equipment_static_bindings`) | 4 items | Two required packaged roles and at most two explicit role overrides. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |
| Equipment live inspections (`equipment_live_inspections`) | 8 items | One inspection per usable actor, before any schedule activation. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |
| Equipment entitlement records (`equipment_entitlement_records`) | 12 items | Four static and eight live readbacks at the maximum actor and override population. Excess request input is refused before launch; evidence storage and output never silently truncate native observations. | Fixed. |
| Sealed worker equipment inventory (`equipment_inventory_bytes`) | 1,048,576 bytes | Complete service-local inventory bytes read before actor preparation. A larger input is refused without selecting equipment. An observation exceeding this bound cannot establish eligible actor equipment. | Fixed. |
| Equipment diagnostic (`equipment_diagnostic_bytes`) | 1,024 UTF-8 bytes | Each equipment diagnostic is bounded before it enters a reply; longer observations retain a bounded diagnostic. An observation exceeding this bound cannot establish eligible actor equipment. | Fixed. |
| Equipment metadata record (`equipment_metadata_bytes`) | 32,768 bytes | Sum of UTF-8 bytes in the declared text fields of one static binding or live execution record, including binding error text or live native-operation names. Fixed scalar fields and the separately bounded entitlement plist do not count. An observation exceeding this bound cannot establish eligible actor equipment. | Fixed. |

### Diagnostic helpers

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| sbpl-check source admission (`helper_source`) | 4,194,304 bytes | Source bytes in each diagnostic helper input, including independent actor-policy fallback inputs; not the runner policy cap or total fallback size. policy_too_large with null compile and import_inventory groups; no compile verdict. | Fixed. |
| sbpl-check import inventory depth (`helper_import_depth`) | 8 levels | Import depth in the helper inventory, starting at 0. Depth 8 is the first depth replaced by a depth-limit diagnostic. The affected branch stops and `import_inventory.truncated` is set. This does not limit compilation of imports. | Fixed. |
| sbpl-check import inventory count (`helper_import_count`) | 64 records | Import-inventory records, including unresolved and error records. Repeated files or names are listed once. Further inventory stops and `import_inventory.truncated` is set. This does not limit compilation of imports. | Fixed. |

<!-- END GENERATED LIMITS -->

### Interactions that matter

- Budgets nest, and one flag changes one of them. `--timeout-ms` sets
  `client_rpc_wait`, which also bounds external host re-acquisition. The worker polling
  window `worker_sentinel_wait`, the validator deadline `validator_io_wait`,
  the release wait `worker_proceed_wait` and the per-worker exec budgets keep their own
  values. Actor form instead uses one setup allowance and one schedule allowance
  shared by all actors. No number here is an end-to-end runtime. The reply records the
  client span in `data.runner_client.started_at_unix_ms` and
  `ended_at_unix_ms`; an expired client wait yields `xpc_timeout`.
- Actor setup and signed-code inspection precede schedule activation and share
  `actor_setup_allowance`. A termination dependency waits at most <!-- span limits.actor_termination_wait.value_unit -->5,000 milliseconds<!-- /span -->
  within the remaining schedule and lifetime allowances. Cleanup can outlast a
  wait; a later cleanup reap never turns a timed-out dependency into permission
  to activate its phase.
- Phases share one total action/query capacity and a cumulative collection
  allowance of <!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span -->.
  In actor form this is `actor_collection_allowance`, not a second pool.
  The total-collection test override can reduce either form's pool.
  Each eligible phase gets a fresh validator; its I/O deadline is capped by the
  remaining allowance. Planning and cleanup consume this allowance, but cleanup
  and scheduling can overrun it. Exhaustion leaves later predictions unavailable
  while attempts may still run. Each worker arrival starts its
  own <!-- span limits.worker_proceed_wait.value_unit -->60,000 milliseconds<!-- /span -->
  release wait; stale releases cannot satisfy it. The host's sentinel polling
  excludes every synchronous collection, and the worker's exec budget excludes
  every acknowledged release wait and each accepted actor activation wait.
  Actor setup includes preparation before the first launch; its schedule allowance
  excludes synchronous collection. The shared continuous lifetime cutoff is
  sampled at checked waits, so blocked native calls and final cleanup can outlast
  it. Client timeout still cancels none of this work.
- Validator storage scales with the query list submitted to each phase collector
  before writes, not the count of successfully written query lines or phase
  capacity multiplied by action capacity. Expected and written bytes remain
  separate observations. Frame and string rejection retain
  earlier complete records and bounded fault context; the stdout byte cutoff
  closes collection with `byte_limit` and discards any incomplete cutoff frame.
- Output budgets mark, they never silently cut. Each receiver reports the
  budget it applied in `capture_limit_bytes` (`controller_output`,
  `policy_helper_output`). Output beyond it is marked truncated, and a
  truncated JSON stream is not parsed as a reply.
- Capacity checking selects the first failing field after decoding. Common
  checks visit top-level metadata, actor identity and sandbox labels, phase
  actor and termination-dependency identities/lifecycle strings, then executable
  overrides. Ordinary checks then visit phase/action counts, phase
  identities, parameter count, worker strings and query fields. Actor checks
  instead visit actor/phase/action counts, phase identities, aggregate lifecycle
  counts, each policy's source/parameters, ordinary worker strings and query
  fields. Meaning validation follows capacity checking; decoding can refuse
  malformed shapes earlier. A refused identity is never shortened into another:
  an oversized `specimen_id` becomes `<admission_refused>`, an oversized
  `run_kind` is omitted and an oversized legacy `policy.format` reads `unknown`.
- The `policy_source`, `parameter_key`, `parameter_value`, `step_id`,
  `attempt_target`, `exec_argument`, `query_operation`, `query_filter_value`,
  `phase_id`, `extension_reference`, `extension_issue_target` and `test_override_path`
  limits also reject embedded NUL, as do lifecycle-action identities and operation
  labels. For a string within
  its byte capacity, that refusal reports unit `nul_bytes`, maximum 0 and the
  same field. Metadata and labels (`specimen_id`, `request_label`,
  `probe_plan_label`) permit escaped NUL at this gate; their
  normal meaning rules still apply. Within the capacities above, other control
  characters and valid Unicode survive request transport unchanged.
- Exec steps in each worker share a budget and each child has a deadline.
  `exec_attempt_budget` bounds that worker's exec steps together and `exec_child_wait` bounds each
  child; neither has a flag. A step the exhausted budget refuses reports
  `exec_failed` with `ETIMEDOUT`, no `child_pid` and no sandbox attribution. A
  child cut by its deadline fails the attempt but keeps any exit code that was
  observed. A worker that dies first leaves the step's exec details
  unpublished, which establishes neither that no child spawned nor that cleanup
  succeeded.
- Compiled-object receipts are bounded per opted-in policy, separately in each
  apply actor's record. Capture requires a 32-character lowercase hexadecimal nonce, successful
  application, completion, clean exit and matching identity/checksum. Capacity
  alone does not make a receipt available; an unapplied actor has none.

<!-- END COPIED LIMITS -->

## Output envelope

Every envelope carries a top-level `build` object naming the code that produced
it: `version` (nearest `v*` git tag), `number` (commit count), `describe` and
`commit`. The same values are stamped into the app's Info.plist. This is a
coordinate for correlating evidence with source. The contract versions below
identify compatibility.

### Shape and schema_version

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 6, response schema 29, controller envelope 13, runner protocol 4. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

The runner reply's JSON projection carries the response `schema_version` and
holds `normalized_outcome`, `steps`, `runner_subprocess`, `phases`
and the policy identity (`specimen_id`, `policy_format`, `policy_sha256`). It is
readable on its own. The controller envelope is what `policy-witness run`
prints: its `schema_version` is the controller envelope, `result` summarizes
the run, and `data` carries the reply unchanged as `runner_result` beside the
specimen dossier (`specimen`), the client transport (`runner_client`), the
fallback compilation (`policy_check`), the controller's projections
(`runner_sandbox_diagnostics`) and `timeout_ms`. Readers that interpret either
document accept exactly the current numbers; another version is reported as
unsupported, with the bytes retained (see [CONTRACT.md](CONTRACT.md)).
`pw-runner-client` emits a binary `runner_client_capture` at the current
runner protocol. It carries acquisition and submission observations and the
received host bytes, rather than manufacturing host results for client errors.

The XPC host stays unsandboxed and spawns a sandboxed attempt worker plus a
fresh batch validator for each eligible phase. Worker identity for
correlation comes only from `runner_subprocess.pid`; the host reply's top-level
`pid` names the host. The separate capture's `client_pid` names the helper.

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

- `execution_form` — `single_worker` or `actors`. An actor-form reply has no
  `runner_subprocess`, `policy_sha256`, `sandboxed_after_apply` or
  `extensions`; each actor carries its own.
- `actors[]` — one record per actor in request order: `actor_id`, `index`,
  `mode`, `setup_status` (`applied`, `unapplied_declared`, `setup_failed`,
  `exited_before_setup`, `setup_timeout`, `launch_refused`,
  `transfer_failed` or `not_launched`), `applied` (null for an unapplied
  actor), `application_count`, the host's `policy_sha256` and the worker's
  `policy_received_sha256`, the `launch` context (`pid`, `parent_pid`,
  `environment`, `standard_streams`, `inherited_descriptors`), the actor's own
  `subprocess` with its disposition record, an optional `compiled_profile`
  and `visits` (the phase ordinals it was activated in).
- `transfers[]` and `resources` — the host's record of each explicit exchange
  and the token, delivery and handle tables; see
  [extension output](#extension-and-fresh-read-output).

- `phases[]` — ordered records with `phase_id`, one-based `ordinal`, ordered
  `action_ids`, `arrival_observed`, `completion_observed` and `collection_status`.
  Status is `not_reached`, `not_needed`, `collected`, `budget_exhausted` or
  `clock_unavailable`; `collected` includes failed or partial collection.
  `ordering` is present when a worker exists. Each `steps[].phase_id` identifies
  the phase owning its query, attempt and comparison. Phase completion and
  individual action completion remain separate observations. In the actor
  form each phase and step also names its `actor_id`, and a phase carries the
  actor's one-based `actor_visit`; a later phase of another actor may arrive
  after an unfinished phase, and the missing completion stays on the earlier
  phase.

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
  `open_write`/`write_fresh` to `file-write-data`, `unlink` to `file-write-unlink`, exec
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
not be decoded as a supported binary capture. Records inside a lost envelope are unavailable. The
independent fallback helper's admission refusal remains `policy_too_large`.

The parsed client frame is retained in `transport`. `transport_admission`
is `accepted`, `missing`, `unsupported`, `malformed` or `delivery_failed`;
`transport_error`
explains rejection. The controller's `submission` projection is `invoked`,
`not_invoked` or `unknown`. It is known only from an admitted capture.
`runner_reply_error` reports truncated host bytes or a host body that is not
a complete supported typed record; the retained bytes remain available inside the capture.

The admitted frame records `clock: "mach_continuous_time_ns"`,
`clock_available`, available absolute start/deadline/end readings, `timeout_ms`,
`attempts`, `acquisition_stop`, `submission` and `terminal`. The overall deadline
includes controller-side launch and stdin delivery. Attempt start/end and
invocation elapsed milliseconds use the helper's continuous-clock start.
Clock failure preserves earlier readings and invocation state, then stops with
`local_error`; absent readings never establish elapsed time.

Each acquisition attempt records an ordinal, attempt UUID, elapsed times,
outcome and any control observation or error. Control observations retain byte
count and SHA-256 plus admitted peer-reported status, host PID/instance and
lease/reason fields; they omit the credential. Transport errors retain stage,
reason and bounded message, with paired native domain/code when observed and
explicit message/domain truncation flags. The message retains the native debug
description when available, otherwise its localized description; arbitrary
native error metadata is not copied. A successful grant does not by itself
establish invocation or execution.

`runner_reply` contains the exact retained host bytes as base64, received and
retained byte counts, and a truncation flag. Only a reply accepted before the
deadline can populate it. The capture retains a prefix up to the documented
limit; an incomplete body cannot become `runner_result`. A complete typed host
body is projected as `runner_result` and independently admitted under the
response schema before its meaning is used. Client transport failures do not
create synthetic host results. The helper writes this versioned binary capture to
stdout, including when no host reply arrived. The controller presents its retained
byte fields as base64 in public JSON. Rejected client frames retain bounded exact
bytes with `format: "porcelain"`; they establish no submission state.

The controller delivers the request to the client on stdin (`--request -`)
and records that delivery in `runner_client.request_delivery`:
`bytes_written` and `error`. This is a controller observation: an accepted
pipe write and a closed writer do not prove that the client read the bytes or
that XPC delivered them. A delivery error makes the run a controller
`tool_error` (exit 2) that takes precedence over any captured reply; the client
bytes remain retained without host interpretation. `runner_client` is null when the
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
  installed BYOXPC runner, and the host's, selected worker's, unentitled worker's and validator's
  signature metadata and entitlements read back separately
  (`runner_signature`/`runner_entitlements`, `runner_worker_signature`/
  `runner_worker_entitlements`, `runner_validator_signature`/
  `runner_validator_entitlements`, `runner_unentitled_worker_signature`/
  `runner_unentitled_worker_entitlements`). Each entitlement object lists `keys` and
  `granted`, the keys whose value is `true`. The built-in runner's helpers are
  described from the evidence manifest and carry no signature metadata.
- `app_provenance`: `evidence_manifest_path`, the app evidence manifest the
  built-in runner and the binary baselines were selected from, and
  `evidence_verify`, the verification report when `PW_VERIFY_EVIDENCE`
  requested one (null otherwise). The object is null when the manifest could
  not be parsed.
- `binaries.service`, `binaries.worker`, `binaries.validator` and `binaries.unentitled_worker`: null when
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
| `extension_events[]` | `phase_id`, `step_id`, operation and references, `call_boundary_observed`, `result_published`, status, optional `native_result`, errno, unavailability reason and lifecycle claims. Events carry `actor_id`, `family`, `delivery_ref`, and for an issue the submitted `target`, `extension_class`, `flags`, `native_nonnull` and `token_length`; a transfer event's status is the host's acknowledgement and it carries no native result. |
| `transfers[]` | `phase_id`, `step_id`, source and recipient actors, `token_ref`, `delivery_ref`, `request_published`, `custody_status`, `copy_status`, `equality`, `recipient_acknowledged`, `source_acknowledged`, `status` and the sender's lifecycle claims. |
| `resources` | `tokens[]` (reference, issuing actor and step, family, status, token length, last declared use), `deliveries[]` (reference, token, source and recipient actors, step, status, delivered length, equality, last declared use) and `handles[]` (reference, delivery, consuming actor and step, status, raw native handle, other handles with the same raw value, release step and whether release was attempted). |
| `steps[].attempt.fresh_read` | `open_rc` / `open_errno`, `stat_rc` / `stat_errno`, optional descriptor identity, `read_rc` / `read_errno`, `close_rc` / `close_errno` and `content_hex`. Each errno belongs to its failed syscall; successful read count determines the hex length. |
| `steps[].attempt.fresh_write` | Separate `open_rc` / `open_errno`, optional `truncate_rc` / `truncate_errno`, `write_rc` / `write_errno`, `close_rc` / `close_errno`, and metadata observations described below. Unattempted calls are absent. |

A published nonnull issue becomes usable only after host custody accepts it. Transfer, recipient acknowledgement and consume remain separate observations. Consumption has its own record in `extension_events`.

<!-- BEGIN COPIED EXTENSION STATUSES -->

Host custody and explicit transfer have their own statuses.
A custody status describes the host's acceptance of the bytes an actor
published after a nonnull native issue; a transfer status describes the host's
answer to the sending actor and is never a native result.

| Custody status | Host observation and supported meaning |
| --- | --- |
| `issued` | The native issue returned nonnull and the host accepted the published bytes into custody after framing checks. |
| `issued_uncustodied` | The native issue returned nonnull but the host rejected, timed out on or never saw the publication; the token's transfers read `custody_unavailable`. |
| `null` | The native issue returned NULL with its errno. No custody exists. |
| `unavailable` | The issue was not called; the event's `unavailable_reason` says why. |
| `not_reached` | Independent progress and slot evidence supports that the issue action's boundary was not reached. |
| `unresolved` | No eligible complete result establishes the issue state; absence of publication alone does not prove the action was never called. |

| Transfer status | Host observation and supported meaning |
| --- | --- |
| `delivered` | The recipient acknowledged a framed delivery and its bytes equalled the host's custody copy (`equality: equal`). This is not consumption. |
| `custody_unavailable` | The named token had no accepted custody when the transfer ran. |
| `recipient_rejected` | The recipient's framing check refused the delivery. |
| `recipient_timeout` | The recipient did not acknowledge within the exchange allowance; the delivery was withdrawn. |
| `recipient_unavailable` | The recipient had no usable process or region when the transfer ran. |
| `request_invalid` | The request named no admitted transfer of this actor. |
| `host_timeout`, `clock_fault` | The sending worker's own wait for the host's answer expired or lost its clock; the host's record may still carry an answer. |
| `copy_mismatch` | The recipient acknowledged bytes that no longer equalled custody; the delivery was withdrawn. |

An event can report `authority_channel_unavailable` when its worker cannot use the
assigned authority region, or `delivery_unavailable` when the named delivery
was not accepted. Individually unavailable issue, consume and release symbols
produce operation-specific `native_api_unavailable` decisions; supported
unrelated operations remain observable. These are no-call decisions, not
native denial results.

<!-- END COPIED EXTENSION STATUSES -->

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
bounded prefix. Actor equipment, native actions and fresh access retain their separate observations. The [native evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence)
defines producer and reader validation.

For `write_fresh` and `create_fresh`, `fresh_write` retains each actual syscall
result. Its metadata objects `preopen_stat`, `opened_stat`, `truncated_stat` and
`written_stat` contain `rc`, failure `errno`, and successful `identity` plus
signed `size`. The pre-open path observation belongs only to exclusive creation;
the other observations use the opened descriptor. Truncation and its metadata
belong only to `write_fresh`. A failed truncation omits the write, but its later
metadata and close observations remain. A failed open has no descriptor
metadata, truncation, write or close evidence.

The aggregate outcome is `write_failed` for the first failed open, descriptor stat,
truncation, write or close in call order, or for a short transfer. A short write
has no invented errno. Pre-open metadata is diagnostic and does not determine
the aggregate outcome. Missing publication supplies no `fresh_write` object.
The returned byte count and metadata do not substitute for independently read
contents or establish crash durability.

### Per-step shape

The runner echoes step results with additional context:

- `steps[].sandbox_check`: `{ rc, outcome, pid, operation, filter_kind, filter_value, filter_type_id, errno, error, result_source, native_rc, missing_reason?, path_diagnostics? }`
- `steps[].attempt`: `{ rc, errno, outcome, error, result_source, missing_reason?, requested_kind, requested_action, requested_path, observed_path, lifecycle, fresh_read?, fresh_write?, path_diagnostics?, child_pid?, child_exit_code?, child_term_signal?, stdout?, stderr?, exec_observation? }`
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
- `write_failed` — a fresh write or exclusive creation encountered a failed open, descriptor stat, truncation, write or close, or a short transfer; inspect `fresh_write` for separate observations.
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
   sandbox. The envelope does not establish that sandbox enforcement caused a
   particular attempt's failure.
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
and neither changes the attempt or its comparison.

Capture the sandbox_check argument quickly:

```sh
jq '.data.runner_result.steps[].sandbox_check | {filter_value, filter_type_id, outcome, path_diagnostics}' run.json
```

### normalized_outcome catalog

`data.runner_result.normalized_outcome` values the runner can produce
(for the standalone helper's `bad_request`, `policy_too_large`,
`setup_error`, `compile_error` and `ok` outcomes, see
[SBPL check](#sbpl-check-sbpl-check)):

- `finished` — worker completion and clean disposition are confirmed. Any invoked
  validator also has confirmed clean disposition, valid received records for
  every requested step ID, and no transport, decoding, or association failure.
  Uniquely associated per-step diagnostics retain their per-step semantics.
  Attempted operations can succeed or fail in a finished run; inspect each
  step's `attempt` and `comparison` records for those observations. The controller
  reports `result.normalized_outcome: "finished"`, `result.ok: true` and exit 0
  for this execution status. None of these establishes that an attempt succeeded.
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

Client failures are separately attributed in `runner_client.transport` and the
controller's result: `xpc_error` is a captured transport error and `xpc_timeout`
is expiry of the overall client allowance. `xpc_acquisition_failed` means the
client exhausted its bounded reservation attempts; `xpc_submission_refused`
means the execution method returned a reservation refusal. Protocol/local
failures retain their stage and diagnostic. Missing, malformed or unsupported
client capture leaves submission unknown. These paths have no host RunResult.
A host reply can be delayed or lost; an invoked execution is never replayed.

For ordinary, successfully captured client output, the two timeout layers map
to these fields:

| Event | `result.normalized_outcome` | `data.runner_result.normalized_outcome` | Result origin and distinguishing evidence |
| --- | --- | --- | --- |
| Client allowance expires | `xpc_timeout` | null | Client capture retains whether execution was invoked. After invocation, execution is unknown; before invocation, it was not submitted. |
| Host sentinel budget expires and its reply arrives | `runner_timeout` | `runner_timeout` | Host result includes `runner_subprocess.poll_stop_reason: "sentinel_deadline"` and available disposition evidence. Client exit code is 0 because it delivered the reply. |

The client exit code is `data.runner_client.exit_code`. The controller
`policy-witness` exits 1 in both cases. RPC expiry means no reply was received
before the client's deadline. It does not prove the host never ran, was
unreachable or crashed, and does not establish cancellation of host work.

If client stdout supplies no admitted capture, `data.runner_result` is null and
the controller reports a missing, malformed or unsupported client capture; inspect the
[capture evidence](#receiver-evidence) for empty, undecodable or truncated output.
Client launch or request-delivery failures are `tool_error` paths. These differ
from a captured client RPC timeout and from a parsed host reply retained
but refused as `unsupported_runner_response` or `malformed_runner_response`.

The controller's own outcomes (`tool_error`, client capture refusals,
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

- `("file", "open_read" | "read_fresh" | "open_write" | "write_fresh" | "create" | "create_fresh" | "unlink" | "access")` — exercise file ops on `target`.
  `open_read` opens read-only, attempts a one-byte read and close, and discards
  those latter returns; its status reports the open result. `open_write` opens
  with `O_WRONLY | O_TRUNC`, then attempts to write `x` and close, discarding
  those returns; success reports the truncating open, not an observed byte
  transfer. `create` uses `O_WRONLY | O_CREAT` with mode argument `0600`, subject
  to umask: an existing file is opened without truncation, and an absent target
  can be created. `read_fresh` instead retains separate native open, stat, read
  and close observations and bounded content, as described in
  [fresh-read output](#extension-and-fresh-read-output).
  `write_fresh` explicitly truncates an existing file then writes `x`;
  `create_fresh` uses an exclusive create then writes `x`. Both retain the
  separate native results and metadata in `fresh_write`, described alongside
  that output. The exclusive create fails if the target already exists.
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

  Exec children have their own PIDs and separate subprocess observations.

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
- `--runner-mode <standard|byoxpc>`: inject `runner.mode` into the request
- `--version`: print a `kind="version"` envelope with the build stamp and the
  wire contract versions this build speaks

### Running specimens in parallel

A run uses a controller and a separate `pw-runner-client` to acquire a fresh
XPC host. After admission, an ordinary specimen uses one fresh
worker; an actor specimen uses one fresh worker per actor, retained across
that actor's phases. Each eligible phase gets a fresh validator; a phase with
no eligible queries creates none. Exec attempts can create children, and a
terminal XPC error can trigger independent `sbpl-check` helpers. These processes
have different lifetimes, so there is no fixed process count per run. Concurrent
runs add to per-user process-table pressure. A failed worker or validator spawn
is reported as `worker_spawn_failed` or `validator_spawn_failed` with the native
return code (see the
[outcome catalog](#normalized_outcome-catalog)). Resource delays can exhaust
the separate budgets in the [limits inventory](#limits): client RPC expiry
produces `xpc_timeout`, while a delivered host sentinel-timeout reply reports
`runner_timeout`. Worker or validator limits can also leave incomplete
observations; read the available lifecycle evidence. See
[External runners](#external-runners-byoxpc) for the pacing of one installed
external runner.

### Troubleshooting

- Service not found: run `policy-witness runner list` and confirm the service name.
- System scope install fails: use `--scope user` or run with admin privileges.
- Verify fails with no reply: check launchd state and the service plist.
- BYOXPC crashes at launch: confirm `XPC_SERVICE_PATH` is set and the bundle is a valid XPC service (`CFBundlePackageType=XPC!`).
- `normalized_outcome` is `runner_failed`: inspect the published-state diagnostic
  and independent `runner_subprocess` observations. A signal or missing report
  may leave the underlying cause unknown. Completed predictions and attempts
  remain usable for their own claims.
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

For `run` and `runner verify`, one client acquires a reservation before sending
the specimen for execution. Acquisition messages contain no specimen bytes.
An occupied host or a connection lost during acquisition can lead to another
connection within the original deadline and acquisition limits. A grant is
single-use and bound to that connection. An abandoned or expired reservation
retires its host without executing a specimen.

The client marks submission `invoked` immediately before calling execution on
the reserved connection. No later error, refusal or timeout causes replay.
In particular, XPC error 4097 can accompany completed work and cannot establish
nonexecution. A grant alone also does not establish invocation: the overall
deadline can expire after the grant but before submission.

`data.runner_client.transport` records acquisition attempts, their control
observations, the acquisition stop reason, submission state, terminal event
and host reply bytes accepted before the deadline. Host PID/instance values in a grant are
peer-reported identities, not kernel-generation receipts. Reservation credentials
are omitted. The controller admits the capture's protocol and state invariants
before reading the host result. Missing or inadmissible capture means submission
unknown, never known nonexecution. `runner_result` is null without a parsed
host reply, and no client error is represented as a host execution observation.

External runners must advertise the current runner protocol in their signed
bundle and participate in its reservation RPC. Install rejects missing or
unsupported advertisements; run and verify independently check the actual
protocol response. Old registry records remain available for list, reconcile
and removal, but cannot be selected for execution. Remove and reinstall an
updated runner to use it; there is no automatic legacy execution fallback.


Use this when you need entitlements that are not in the built-in runner.
BYOXPC is the only external runner kind.

### What you need

- A runner `.xpc` bundle to sign (typically a copy of `PWRunner.xpc`).
- A signing identity: a **Developer ID Application whose Team ID matches the app**
  (see [Caller authentication and ad-hoc signing](#caller-authentication-and-ad-hoc-signing)).
- An entitlements plist.
- A logged-in GUI session (launchd bootstrap is not available from non-GUI shells).

### Install a BYOXPC runner

Installation verifies the source bundle's existing seal and complete service-local worker inventory before changing bytes. Start from an intact built service. If you change `CFBundleIdentifier` or caller-authentication keys in its `Info.plist`, reseal that source service with your signing identity before installation, for example `codesign --force --options runtime --sign "$IDENTITY" "$BYO"`. Preserve the nested workers and inventory; the installer separately signs the selected worker with your requested entitlements and regenerates signing observations before its final seal. A modified source with a stale or invalid seal is refused.

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
  its validator (`Contents/MacOS/sb_api_validator`) and unentitled worker
  (`Contents/MacOS/pw-probe-runner-unentitled`) with the identity alone,
  refreshes the sealed worker equipment inventory, and then signs the enclosing bundle with both. The worker is the process the
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

The registry reads each binary back separately using `codesign`: `signature` and `entitlements` describe the host, `worker_signature` and `worker_entitlements` the selected worker, `unentitled_worker_signature` and `unentitled_worker_entitlements` the unentitled worker, and `validator_signature` and `validator_entitlements` the validator. Each entitlement object lists all `keys` and the `granted` keys whose values are boolean `true`. Current and source worker equipment inventory snapshots retain installation provenance; execution verifies the service-local sealed inventory against current bytes.

Historical registry records remain available for list, reconcile and removal even when their protocol or inventory is unsupported for execution. Unknown historical observations remain unknown; they do not authorize substitution or bypass current equipment validation. `runner validate` checks the current copy and reports failures; `runner reconcile` reports installation state. Reinstall a current service to refresh its provenance.

### Caller authentication and ad-hoc signing

The shipped `PWRunner.xpc` has caller authentication enabled in its Info.plist
(`PWRunnerRequireSignedCaller`), and the runner authenticates the caller by
comparing the caller's **Team ID** to its own. A BYOXPC runner made by copying
that template inherits the check, which constrains how you may sign it:

- **Signed runner (default, recommended):** sign the copy with a **Developer ID
  whose Team ID matches the app** (so the runner's team equals `pw-runner-client`'s).
  `runner verify` returns `finished`.
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
previous launch. Acquisition that reaches the verified host while it is still
retiring, or a fresh host another connection reserved first, may reconnect
without submitting a specimen. Execution remains a single invocation after
the grant, as described above.

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
  "schema_version": 6,
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

`runner validate` verifies each registry entry's bundle recursively and the host, both current worker variants and validator individually. It also verifies the sealed equipment inventory against the current role artifacts. Historical issuer observations remain inspectable for legacy recovery. The command retains signature and entitlement readbacks and reports failed records in `invalid` and per-binary or `equipment_inventory` failure rows. A valid signature alone does not excuse a stale inventory. Use `runner reconcile` to compare installation state with launchctl and `LaunchAgents/`.

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
