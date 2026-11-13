# PolicyWitness User Guide

PolicyWitness runs a saved sandbox-policy specimen and records what happened.
A specimen supplies sandbox queries and attempted operations, with an SBPL
policy for each process it asks to apply one. The runner arranges one fresh
worker for an ordinary specimen or one per actor, collects eligible
`sandbox_check` answers, then releases each phase's worker to perform its actions. The report keeps predictions,
native observations, ordering and process cleanup separately so you can decide
which facts support your experiment.

The **controller** is the `policy-witness` command you invoke. It prepares the
request, selects a runner and prints the result envelope. The **runner host**
manages fresh workers and validators and returns their observations. A
**worker** performs its actions after policy application or its actor's explicit
unapplied declaration; a **validator** asks `sandbox_check` about that worker. Actor specimens name several workers and
schedule their visits explicitly.

This guide is staged with the app it describes. Keep the app's `build.contract`,
your submitted JSON, its result envelope and independent observations together.
They are the starting point for comparing runs.

## Contents

- [Quick start](#quick-start)
- [Questions](#questions)
- [Specimen format](#specimen-format)
- [Limits](#limits)
- [Output envelope](#output-envelope)
- [What PolicyWitness understands](#what-policywitness-understands)
- [Operating](#operating)
- [External runners (BYOXPC)](#external-runners-byoxpc)
- [Public contract surfaces](#public-contract-surfaces)

## Quick start

The shipped app requires macOS 26 or later on Apple silicon (arm64).
Use the built-in standard runner for your first specimen. These commands use
macOS tools and a new private work directory outside privacy-mediated folders.
Run them in one shell, keeping the printed directory for later examples. Set
`APP` to your installed app.

```sh
APP="/Applications/PolicyWitness.app"
PW="$APP/Contents/MacOS/policy-witness"
umask 077
PW_WORK=$(mktemp -d /private/tmp/pw-guide.XXXXXX)
printf 'Work directory: %s\n' "$PW_WORK"
"$PW" --version > "$PW_WORK/version.json"
PW_CONTRACT=$(/usr/bin/plutil -extract build.contract raw -o - "$PW_WORK/version.json")
printf 'Contract: %s\n' "$PW_CONTRACT"
```

Check that the version command succeeded and the contract string is nonempty
before continuing. The string identifies the exact input/report contract; the
remaining examples marked `BUILD_CONTRACT` need that value before submission.
A release uses `release:vX.Y.Z`; a development build uses `development:<digest>`.

Obtain this build's create lesson, which opens a new, empty file under an
allow-all policy. `lesson` prints a request with the emitting app's contract;
it does not execute it. Exit 0 supplies the complete request. On exit 2 discard
its output. The target is inserted verbatim without checking the filesystem.

```sh
"$PW" lesson create --target "$PW_WORK/created" > "$PW_WORK/create.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/created"; then
  "$PW" run "$PW_WORK/create.json" > "$PW_WORK/create-result.json" 2> "$PW_WORK/create-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/create-exit.txt"
  cat "$PW_WORK/create-result.json"
  test -f "$PW_WORK/created"
  /usr/bin/stat -f 'size=%z mode=%Sp inode=%i' "$PW_WORK/created" > "$PW_WORK/create-observation.txt"
  cat "$PW_WORK/create-observation.txt"
else
  printf '%s\n' 'Request emission failed or target exists; discard failed output and prepare a fresh work directory.' >&2
fi
```

The guard requires successful emission and refuses to reuse an existing target.
On a completed create, the run command exits 0 and the target is an empty file. The saved
exit status and envelope describe execution; `test` and `stat` independently
observe the file effect. `create` opens an existing file without truncating it,
which is why the initial absence matters.

The query about the initially absent path can be `prediction_unavailable`
while the attempt succeeds. Read [Reading a result](#reading-a-result) for the
relationship between run status, evidence findings and individual effects. Then
try [an accepted request and a refusal](#try-an-accepted-request-and-a-refusal)
using the same saved request and work directory.

Preserve this directory until you have reviewed the results. If you later stage
an external runner inside it, retain the directory through the runner's
[removal and recovery](#list-validate-or-remove-runners).

## Questions

<!-- BEGIN COPIED QUESTIONS -->

### When should I use PolicyWitness?

Use it for a repeatable experiment about a sandbox policy: prepare a saved request, collect a prediction where available, perform the requested actions and retain the observations. Start with the [quick start](#quick-start), then read the [result account](#reading-a-result) before comparing runs.

### Who needs to use PolicyWitness?

Developers investigating sandbox policy, native API behavior and process authority can use the same specimen and report to state exactly what they observed. A useful experiment identifies its target, its expected observation and an independent way to inspect the effect.

### What systems can run PolicyWitness?

The shipped app requires macOS 26 or later on Apple silicon (arm64).

### Can PolicyWitness attribute a failed attempt to sandbox denial?

A permission-shaped failure records a native result such as `EPERM`, `EACCES` or a bootstrap permission result. The report preserves that observation and the separately collected query answer. Establishing the cause requires evidence that distinguishes sandbox enforcement from the other reasons the native operation can fail. [What a permission failure establishes](#what-a-permission-failure-establishes) lists what the classification rests on and gives examples of evidence an attribution can use.

### What does PolicyWitness's attempt channel record?

It records the requested operation's published result and the evidence that supports it. A completed failed operation is a result. A missing or incomplete publication stays unavailable, with lifecycle evidence showing whether the action boundary was reached. File, Mach lookup, sysctl and exec operations have [different observations](#attempt-kinds-the-runner-implements).

### How does a worker report observations under `(deny default)`?

The host prepares shared evidence memory before the worker applies the policy. The worker publishes bounded observations there, and the host collects them after execution and cleanup. The host's reply path remains in its own unsandboxed process. Publication, collection and final process status each have their own records.

### Can PolicyWitness probe operations it doesn't natively support?

An `exec/spawn` attempt can run your helper and retain its bounded stdout, stderr and child-process observations. Arrange for the helper to report the native result and supporting effect you need. The [exec augment](#augments) adds process permissions and an unconditional file-read allow; choose it only when those added permissions fit the experiment.

### What does a comparison record contain?

It records the attempt observation and its basis, the relationship between submitted operations and targets, query order and limitations. The prediction stays in `sandbox_check`. [Reading a comparison](#reading-a-comparison-record) explains the six fields together. Reporting-failure replies omit comparisons while retaining the observations their fallback form can carry.

### Does PolicyWitness decide whether `sandbox_check` and enforcement disagree?

No. The report supplies the query answer, attempt observation and the relationships it can establish. `query_first` establishes collection before the phase's actions; `same_submitted` compares submitted target bytes. Runtime object identity and changes between query and action require additional observations for an agreement or disagreement claim. [When the answer and the attempt differ](#when-the-answer-and-the-attempt-differ) gives the fields to check first.

### Can PolicyWitness run every profile that `libsandbox` accepts?

PolicyWitness admits requests within its grammar, action relationships and [limits](#limits). The worker then uses the host OS's native compiler and applies the resulting profile. Compilation, application and completion are separate observations, each with its own failure record.

### What versions of SBPL are supported?

SBPL is interpreted by the installed OS's `libsandbox`. Keep the recorded macOS build, selected source and parameters with the result when comparing compiler behavior. The [compiler helper](#sbpl-check-sbpl-check) gives an independent host-side compilation diagnostic.

### How do I use imports with PolicyWitness?

Write native `(import "name.sb")` expressions in the policy. The controller separately inventories literal imports: absolute names are read as supplied; relative names are searched under `/System/Library/Sandbox/Profiles/` and then `/usr/share/sandbox/`. Preserve each inventory's errors, hashes and truncation status alongside the native compiler result. The [dossier](#the-specimen-dossier) describes that inspection and the source selected for invocation.

### Can PolicyWitness test sandbox-extension behavior?

Use [actors and sandbox extensions](#sandbox-extensions). Each actor selects equipment and either applies a policy or declares an unapplied path. Explicit issue, transfer, consume and release actions record native calls and host custody separately. Fresh file attempts before and after those actions observe access at those moments.

### Which happens first, the prediction or the attempt?

The host closes a phase's query collection before releasing its action batch. A qualifying native answer has `comparison.order: query_first` when the report carries the supporting release and acknowledgement chain. Actions run in declaration order; an earlier action can change the state a later action encounters. Use [ordered phases](#ordered-phases) to collect again after earlier actions. [When `order` is `unestablished`](#when-order-is-unestablished) names each requirement behind `query_first` and the fields that show it.

### Can PolicyWitness collect sandbox-denial logs?

The result records query, worker, transport and process-lifecycle evidence. If you collect unified logs separately, retain their collection conditions and correlate them with the saved run; a log entry's availability and attribution require their own evidence.

### How long does a run take?

The saved client start/end wall-clock milliseconds describe its observed span;
wall-clock adjustments can affect their difference. Client acquisition/reply allowance, host collection and cleanup, worker waits and exec observation have separate clocks and [budgets](#execution-budgets). A client deadline can expire after execution was invoked. Inspect [submission state](#receiver-evidence) before deciding whether a retry could repeat an effect.

### Can I evaluate specimens in parallel?

Each run acquires a fresh host and fresh specimen workers. Concurrent runs share machine resources and an installed service's launch pacing; acquisition can encounter an occupied host. Use independent request, result and target paths, retain each run's submission state and inspect its outcome. The [operating guidance](#running-specimens-in-parallel) describes the separate process lifetimes.

### Are old versions of the app supported?

Use the guide shipped with the app and retain its exact `build.contract`. Each release preserves its contract and shape history for interpreting that release's reports. Review the [surface table](#public-contract-surfaces) before updating an existing request for another build.

<!-- END COPIED QUESTIONS -->

## Specimen format

### Top-level shape

Top-level fields:

- `contract`: string exactly equal to the current build contract
- `specimen_id`: string
- `run_kind`: string (optional)
- `policy`: object, the ordinary form's single policy. The
  [actor form](#actors-issue-inside-the-sandbox-and-re-delegate) supplies
  `actors` (array) instead and carries neither `policy` nor `probe_plan`.
- Exactly one non-null plan form: `probe_plan` (array of paired steps) or
  `phases` (ordered array of phase objects)
- `runner`: object (optional; select runner mode and external runners)

Minimal skeleton (copy/paste):

```json
{
  "contract": "BUILD_CONTRACT",
  "specimen_id": "skeleton",
  "runner": { "mode": "standard" },
  "policy": { "format": "sbpl", "sbpl_source": "(version 1) (allow default)" },
  "probe_plan": []
}
```
Notes:
- Save the request as UTF-8 JSON. Request objects have declared keys: an
  unknown field or a value of the wrong type produces a request refusal.
  Optional nulls generally mean absence; actor equipment/requirements,
  termination dependencies and the actor equipment override map reject null.
  Parameter names inside `policy.params` are caller data and their values
  must be strings. [Acceptance](#what-acceptance-establishes) distinguishes
  shape, meaning, capacity and execution.
- All path rules live inside `policy.sbpl_source`.
- `probe_plan` may be empty when you want to exercise policy application.
  Each phase with an eligible query plan gets a fresh validator; a phase with
  no eligible queries creates none.
- Ordinary step IDs are unique strings, including an empty string when used
  once. Actor action IDs and phase/actor IDs are nonempty. Give useful unique
  labels to correlate the request, phases and returned steps.


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
  "contract": "BUILD_CONTRACT",
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

The ordinary form accepts at most <!-- span limits.phase_count.value -->8<!-- /span --> phases; the actor form accepts at most <!-- span limits.actor_phases.value -->16<!-- /span --> phases across all actors. Both forms accept at most <!-- span limits.probe_steps.value -->256<!-- /span --> total actions; phases do not multiply the action or query allowance. The
[limits](#limits) describe cumulative collection and per-phase wait bounds.


### Sandbox extensions

Extension specimens use actors. Start with an unapplied issuer using `unentitled` equipment and a subject using `selected` equipment under its submitted policy. Equipment selects the signed worker copy; sandbox mode selects whether that process applies an SBPL policy. An unapplied actor may still inherit restrictions. A worker's signing readback does not establish its effective authority.

This two-actor specimen reads an owned file before consumption, issues and transfers a token, consumes it, reads again, releases the native handle, then makes another fresh read. Each read opens a new descriptor. The last read records the result after release without assuming revocation.

```sh
# Continue with PW and PW_CONTRACT from the quick start.
PW_EXTENSION_DIR=$(mktemp -d /private/tmp/pw-extension.XXXXXX)
printf 'extension witness\n' > "$PW_EXTENSION_DIR/target"
/usr/bin/stat -f 'size=%z inode=%i' "$PW_EXTENSION_DIR/target" > "$PW_EXTENSION_DIR/target-before.txt"
/usr/bin/shasum -a 256 "$PW_EXTENSION_DIR/target" >> "$PW_EXTENSION_DIR/target-before.txt"
cat > "$PW_EXTENSION_DIR/request.json" <<JSON
{
  "contract": "BUILD_CONTRACT",
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
sed "s/BUILD_CONTRACT/$PW_CONTRACT/" "$PW_EXTENSION_DIR/request.json" > "$PW_EXTENSION_DIR/submitted.json"
"$PW" run "$PW_EXTENSION_DIR/submitted.json" > "$PW_EXTENSION_DIR/run.json" 2> "$PW_EXTENSION_DIR/stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_EXTENSION_DIR/exit.txt"
/usr/bin/stat -f 'size=%z inode=%i' "$PW_EXTENSION_DIR/target" > "$PW_EXTENSION_DIR/target-after.txt"
/usr/bin/shasum -a 256 "$PW_EXTENSION_DIR/target" >> "$PW_EXTENSION_DIR/target-after.txt"
```

`read_write` selects the native read-write class and can name a directory. Issue passes the submitted absolute path unchanged with flags zero. Raw token bytes never appear in retained output. A published native result does not by itself establish file access or revocation: use the separate fresh reads and the actor's baseline.

Omitting `equipment` selects `selected`; explicit null is rejected. Optional actor `required_entitlements` is a list of unique entitlement keys that must each have boolean value `true` in that actor's bound and observed live code. Its default is an empty list; explicit null is rejected. This is independent of the controller's `runner.required_entitlements`, which preflights only the selected runner worker. The host verifies both production equipment artifacts against its sealed service-local inventory before launching any actor and inspects each usable actor's owned live code before any scheduled activation. Missing or mismatched equipment never substitutes the other role.

For a specimen that needs the issuer gone before consumption, add `"after_termination": {"actor_id": "issuer"}` to the `consume` phase. The source actor's last scheduled visit must precede the gated phase. The host evaluates the source's owned natural reap after its final activation
before activating the dependent phase or collecting its queries. A nonzero exit
or signal can qualify; final phase completion is separate. A failed evaluated
gate cancels the remaining schedule, including unrelated later visits, while
collection and cleanup continue. This example leaves that dependency absent.

Actor setup automatically reports bounded apparatus operations and their publication. Required apparatus failures stop before policy setup or the unapplied declaration; missing private extension symbols instead make their actions unavailable. A missing terminal setup publication does not prove application never happened. Read application observations, setup decisions and process disposition separately.

#### Actors: issue inside the sandbox and re-delegate

Use an applied actor to observe issuance under its policy. Replace `policy` with
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
# Continue with PW and PW_CONTRACT from the quick start.
PW_ACTOR_DIR=$(mktemp -d /private/tmp/pw-actors.XXXXXX)
printf 'actor witness\n' > "$PW_ACTOR_DIR/target"
T="$PW_ACTOR_DIR/target"
READ='"sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "'"$T"'"}}, "attempt": {"kind": "file", "action": "read_fresh", "target": "'"$T"'"}'
/usr/bin/stat -f 'size=%z inode=%i' "$PW_ACTOR_DIR/target" > "$PW_ACTOR_DIR/target-before.txt"
/usr/bin/shasum -a 256 "$PW_ACTOR_DIR/target" >> "$PW_ACTOR_DIR/target-before.txt"
cat > "$PW_ACTOR_DIR/request.json" <<JSON
{
  "contract": "BUILD_CONTRACT",
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
sed "s/BUILD_CONTRACT/$PW_CONTRACT/" "$PW_ACTOR_DIR/request.json" > "$PW_ACTOR_DIR/submitted.json"
"$PW" run "$PW_ACTOR_DIR/submitted.json" > "$PW_ACTOR_DIR/run.json" 2> "$PW_ACTOR_DIR/stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_ACTOR_DIR/exit.txt"
/usr/bin/stat -f 'size=%z inode=%i' "$PW_ACTOR_DIR/target" > "$PW_ACTOR_DIR/target-after.txt"
/usr/bin/shasum -a 256 "$PW_ACTOR_DIR/target" >> "$PW_ACTOR_DIR/target-after.txt"
```

Read `actors`, `phases`, `steps`, `extension_events`, `transfers` and
`resources` under `data.runner_result`. Each actor's record names its process,
its setup and both policy hashes; each phase names the actor it activated and
that actor's visit number; each step and event names its actor. Compare each
fresh read of the target with its actor's policy, and credit
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

Actor setup automatically records bounded apparatus observations before policy
compilation/application or the unapplied declaration: core-limit handling, authority mapping and framing, descriptor closure and each extension-symbol lookup. Missing extension symbols make the corresponding actions unavailable; required apparatus failure prevents application. Setup publication, application observation and final process disposition remain separate. Missing terminal publication leaves application uncertain rather than proving it did not happen.

A phase may specify `after_termination: {"actor_id": "issuer"}` when that actor's last scheduled visit precedes the phase. The gate requires an owned natural reap after the source's final activation, including a nonzero exit or signal, before dependent activation and query collection. It does not require final phase completion. It does not kill an actor to satisfy the dependency. A failed evaluated gate cancels the remaining schedule, including later unrelated
actors' visits, while final collection and cleanup continue. A gate that was
never evaluated because its dependent actor was unavailable retains that distinct
status; it does not itself impose that cancellation. Earlier published facts
retain their own meanings. The reply retains `actors[].owned_reap` and phase `activation_observation`; the gate references the source reap by `capture_ordinal`. Missing clock timestamps retain facts without establishing gate order.

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

Each actor has its own evidence region. A plan containing token or delivery
resources also receives a host custody session and one authority region per
actor. Those regions are private to their owning host/worker endpoints. Each admitted issue has its own
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
region. Other host descriptors are closed at exec. When creating a custody session, the host disables core dumps before creating
its actor regions. Every actor worker resolves extension symbols and attempts
its core-limit setup. A required authority region is mapped before policy setup;
a plan with no authority resources records mapping as `not_required`. Applied
actors then enter policy setup, and unapplied actors publish their declaration.

#### What each observation establishes

| Observation | Supported reading | Read separately |
| --- | --- | --- |
| `extension_events[]` with operation `issue`, `status: returned`, `native_nonnull: true` | That actor's process made the native issue call for the recorded class and path and received a nonnull result of the recorded length. | Host custody, recipient delivery, consumption and fresh access observations. |
| `issue` with `native_nonnull: false` | The native call returned NULL; `errno` is the value saved immediately after it. | Evidence distinguishing the cause of the native refusal. |
| `resources.tokens[].status: issued` | The host accepted the published bytes into custody. | The delivery and consume records. |
| `transfers[].status: delivered` with `equality: equal` | The recipient acknowledged a framed delivery whose bytes equalled the host's custody copy. | The consume result and later fresh access observations. |
| `transfers[]` with any other status | Where the exchange stopped: custody absent, recipient refusal, timeout, mismatch. No native result belongs to a transfer. | Native issue/consume/release calls belong to their separate event records. |
| `consume` with `status: returned` and `native_result` other than the failure sentinel | That actor received a candidate handle for the delivery it named. | Fresh attempts in that process after the consume. |
| `release` with `status: returned` | The native release call returned the recorded value. | Later fresh attempts and independently observed earlier effects. |
| `status: unavailable` with an `unavailable_reason` | The named operation was not called for the recorded reason (no delivery, no handle, missing native symbol, no authority channel, repeated action). | The exact no-call reason. |
| Resource status `not_reached` | Terminal lifecycle evidence establishes that the producing action was not reached. | Interrupted or unknown producers remain `unresolved`. |
| `status: unresolved` | The action's result was never published: the actor died, was stopped or never reached it. | Published progress and final lifecycle evidence about whether the boundary was reached. |
| A fresh read that succeeds after a consume | That process could open and read the file at that moment. | That actor's baseline read, policy and other authority when investigating the cause. |

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
| Required authority-region or custody setup fails | Host preparation refuses launch, or automatic worker setup records a terminal apparatus failure before policy setup or the unapplied declaration. Missing native symbols instead make the corresponding actions unavailable. |
| An actor's policy does not compile or apply | That actor's `setup_status` is `setup_failed`; its visits are `actor_unavailable`; other actors' evidence stands. The run is `runner_failed`. |
| An application is published during cleanup after setup expires | Setup stays `setup_timeout` and its visits remain unavailable; `applied` and `application_count` retain the later observed application. |
| An actor dies during a visit | The visit records how it ended; the scheduler establishes the actor is reaped before activating anyone else; later visits of that actor are unavailable. |
| The shared lifetime cutoff expires | A worker that reaches a checked wait publishes a timing failure and exits. A blocked native call may prevent that check; host cleanup and missing publication remain separate observations. |
| The issuing actor publishes a token the host rejects | `resources.tokens[].status` is `issued_uncustodied` and `transfers[]` of that token read `custody_unavailable`. |
| A recipient rejects or does not acknowledge a delivery | The transfer reads `recipient_rejected`, `recipient_timeout` or `recipient_unavailable`; the recipient's later consume is `unavailable` for want of a delivery. |
| Native symbols are missing in the worker | The affected operations are `unavailable` with `native_api_unavailable`; unrelated reads still run. |

<!-- END COPIED EXTENSION COVERAGE -->


### Try an accepted request and a refusal

The [quick start](#quick-start) retained `create.json`, its envelope and an
independent file observation in `$PW_WORK`. Use a different target for this
refusal exercise, so an earlier successful run cannot explain its presence.

Obtain the paired lesson containing a deliberately unknown policy field.
Successful publication by `lesson` does not mean `run` will admit this input:

```sh
"$PW" lesson capture_typo --target "$PW_WORK/capture-target" > "$PW_WORK/capture-typo.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/capture-target"; then
  "$PW" run "$PW_WORK/capture-typo.json" > "$PW_WORK/capture-typo-result.json" 2> "$PW_WORK/capture-typo-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/capture-typo-exit.txt"
  test "$PW_EXIT" -eq 1
  test ! -e "$PW_WORK/capture-target"
else
  printf '%s\n' 'Request emission failed or target exists; preserve earlier records and prepare a fresh target.' >&2
fi
```

The envelope reports `bad_request`; `data.request_failure` identifies
`code: "unknown_field"` and
`path: ["policy", "capture_compiled_profiel"]`. The host inspected the request
and refused it before creating a worker or validator. The absent target checks
the intended file effect independently.

Correct the spelling in a copy, preserving the refused input:

```sh
/usr/bin/plutil -remove policy.capture_compiled_profiel \
  -o "$PW_WORK/capture-no-nonce.json" "$PW_WORK/capture-typo.json" &&
/usr/bin/plutil -insert policy.capture_compiled_profile -bool YES "$PW_WORK/capture-no-nonce.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/capture-target"; then
  "$PW" run "$PW_WORK/capture-no-nonce.json" > "$PW_WORK/capture-no-nonce-result.json" 2> "$PW_WORK/capture-no-nonce-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/capture-no-nonce-exit.txt"
  test "$PW_EXIT" -eq 1
  test ! -e "$PW_WORK/capture-target"
else
  printf '%s\n' 'Request repair failed or target exists; preserve earlier records before continuing.' >&2
fi
```

Enabled capture requires a nonce. This second refusal reports
`invalid_capture_nonce` at `["policy", "capture_nonce"]`. To enable capture,
first keep receipt files restricted as in the quick start, then supply a fresh
32-character lowercase hexadecimal nonce. On macOS installations with
`/usr/bin/openssl`, this produces one and saves a third request:

```sh
PW_NONCE=$(/usr/bin/openssl rand -hex 16)
printf '%s\n' "$PW_NONCE"
```

Continue after that command succeeds and prints 32 lowercase hexadecimal
characters. Preserve the corrected request and its result:

```sh
/usr/bin/plutil -insert policy.capture_nonce -string "$PW_NONCE" \
  -o "$PW_WORK/capture.json" "$PW_WORK/capture-no-nonce.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/capture-target"; then
  "$PW" run "$PW_WORK/capture.json" > "$PW_WORK/capture-result.json" 2> "$PW_WORK/capture-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/capture-exit.txt"
  cat "$PW_WORK/capture-result.json"
  test -f "$PW_WORK/capture-target"
else
  printf '%s\n' 'Request repair failed or capture target exists; preserve its records before continuing.' >&2
fi
```

On a completed run the file exists; inspect the separate
[compiled-object receipt](#compiled-object-receipt-opt-in) for its capture
status, nonce and worker identity. Capture can be unavailable even when policy
application was observed. Retain all three request/result pairs so the corrected
field and the next prerequisite remain visible.

For a different experiment, the following policy denies reading one existing
file while leaving the rest allowed:

```json
"policy": {
  "format": "sbpl",
  "sbpl_source": "(version 1) (allow default) (deny file-read-data (literal \"/etc/hosts\"))"
}
```

Pair it with the `read_etc_hosts` step in [Probe plan steps](#probe-plan-steps).
A completed run can contain a permission-shaped open failure. Read the native
observation and query separately; the run's success reports execution completion.

### What acceptance establishes

The controller first parses its command arguments and reads the request. It
checks `contract`, runner selection and policy augmentation before invocation.
The host then admits the delivered request before spawning children. Compilation,
application and attempted operations supply later observations.

| Boundary | Example | Next action |
| --- | --- | --- |
| CLI or request file | Unknown flag, missing file, invalid UTF-8 or malformed JSON. | Read stderr and any printed envelope; save the corrected command or UTF-8 JSON. |
| Request shape | Unknown field or a string where `args` requires an array. | Correct the exact code/path in `request_failure`; keep the refused input. |
| Request meaning | `args: []` on a file attempt, duplicate step IDs or a reference used before its producer. | Correct the field relationship or declared action order. |
| Capacity | Source bytes or total actions exceed a bound. | Read `admission_failure.field`, `actual`, `maximum` and `unit` beside the [limits](#limits); revise the whole specimen. |
| Compilation and application | Native compilation or apply fails after admission. | Read the worker failure operation and native result, then review the selected source and parameters. |
| Attempted effect | A create succeeds or an open returns a permission-shaped failure. | Read that attempt's publication/native evidence and observe the target independently. |

Unknown attempt combinations and filter names refuse the specimen before worker
or validator creation. A recognized query with an unavailable prediction still
permits its supported attempt. The request is preserved as a whole; exceeding a
capacity refuses it instead of shortening the plan.

### Correcting a refused request

Start with `result.normalized_outcome`. For `bad_request`, use
`data.request_failure.code` and `path`; human-readable `result.error` adds
context. Path components are exact keys and decimal array positions:
`["probe_plan", "1", "attempt", "args"]` names the second step's arguments.
`[]` names the root and `null` means the location was withheld. Numeric capacity
refusals also retain `data.runner_result.admission_failure` with counts and
applicable positions.

| Field | Accepted relationship |
| --- | --- |
| `attempt.args` | A non-null array, including `[]`, belongs to `exec/spawn`. |
| `sandbox_check.filter.value` | `none` uses absence or null; other recognized kinds require a nonempty string. |
| `policy.capture_nonce` | Enabled capture requires a fresh nonce of 32 lowercase hexadecimal characters; a supplied nonce requires enabled capture. |

Correct one refused input in a new file and retain the new output. Another
failure may then become visible, as the capture example shows. This retry is
appropriate for a known pre-execution refusal. For a transport failure, first
read [submission state](#receiver-evidence): an invoked or unknown request may
have produced effects already.

The request's `contract` is an exact identity assertion. Compare it with the
saved `--version` output and the [public surface table](#public-contract-surfaces)
before updating an existing specimen. Missing, malformed and foreign assertions
are refused before selection, augmentation or helper/worker invocation.
Keep OS and input observations when comparing matching-contract runs: native
sandbox results also depend on the machine and the state each action encounters.

### Policy

SBPL source:

```json
"policy": {
  "format": "sbpl",
  "sbpl_source": "(version 1) (allow default) (deny file-read-data (subpath (param \"DENY_DIR\")))",
  "params": { "DENY_DIR": "/tmp/deny" }
}
```

`policy.params` is an optional object with caller-chosen names and string
values. Missing or null means absence; an empty object supplies no parameters.
The worker and compiler helper pass nonempty maps through `sandbox_set_param`
before compilation. The native compiler resolves `(param "NAME")` references,
including references inside `string-append`, and determines how missing or
unused parameters affect compilation. `sandbox_compile_string` resolves
`(import "...")` statements against the system profile search path.


### Compiled-object receipt (opt-in)

An SBPL policy may set `capture_compiled_profile: true` and a fresh per-application
`capture_nonce` (32 lowercase hexadecimal characters). Ordinary output places
its receipt at `data.runner_result.compiled_profile`; actor output places each
worker's receipt at `data.runner_result.actors[].compiled_profile`. Each selected
policy opts in independently. The receipt is read under the contract of the
reply that carries it. A `status: "captured"` receipt requires
`producer: "worker"` and `capture_stage: "before_apply"`. It contains `worker_pid`, `request_nonce`, `profile_type`,
`bytecode_length`, `bytecode_b64`, `bytecode_sha256`, `source_length`,
`source_sha256`, `parameter_count` and `params_sha256`. These are sensitive outputs:
the caller must arrange restricted receipt storage before opting in.
A non-null nonce without enabled capture is a `bad_request`.

The C worker copies the bytecode from the same compiler-result pointer it passes
to `sandbox_apply`, before applying. The host qualifies the captured bytes using successful apply,
completed worker publication and clean owned exit, matching PID/nonce, lengths,
input identities and payload checksum before publication. Missing capture, failed apply, worker death or
capture corruption is unavailable.
An unavailable nested receipt has a reason and no bytecode, producer or capture
stage, or is absent if no worker result was obtained. An opt-in request alone
does not establish that capture ran. The controller requires the exact producer/stage labels for a captured receipt
and classifies a reply without them as `malformed_runner_response`. This label
admission and the host's byte/input checks are separate boundaries.

Application is reported separately by the ordinary `sandboxed_after_apply` and
`runner_subprocess.worker_evidence`, or the actor's application account and
`subprocess.worker_evidence`. An unavailable capture does not
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
diagnostics below. For the ordinary request saved in the quick start:

```sh
"$APP/Contents/MacOS/sbpl-check" --request "$PW_WORK/create.json" > "$PW_WORK/compile-result.json" 2> "$PW_WORK/compile-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/compile-exit.txt"
cat "$PW_WORK/compile-result.json"
```

The helper also accepts `--request -` for stdin. It compiles the `policy`
object and reports a diagnostic; application and file effects belong to the
worker run. Its accepted request subset and input checks differ from `run`.

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
supported envelope (the helper kind, the current helper producer contract
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
`bad_request` before children. The controller runs fallback checks only after an eligible terminal XPC error.
It uses the held, resolved request already prepared for invocation. For actor
requests, `actor_policy_checks` associates independent checks with each carried
policy object and the available actor label, including policies whose actor
mode or label would later fail host admission.

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

The controller appends the named fragments in the submitted order. The shipped
`exec_baseline` contains allow rules. Review those actual additions against the
experiment: its unconditional `(allow file-read*)` broadens file access as well
as permitting executable loading. Choose explicit policy rules when you need a
more limited experiment.

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

Shipped augment:

- **`exec_baseline`** appends `(allow process-exec*)`, `(allow process-fork)` and
  an unconditional `(allow file-read*)`. The project's libSystem-dynamic helper
  exercised that fragment on macOS 14.8.3 (build 23J220, Darwin 23.6.0). Other
  helpers and OS environments can require different permissions. Because the
  fragment changes file-read authority, keep it separate from an experiment
  intended to observe file-read denial under the unaugmented source.

### Probe plan steps

Each step has:

- `step_id`
- `sandbox_check`: `{ operation, filter }`
- `attempt`: `{ kind, action, target }`, with optional `args` for `exec/spawn`

The query and attempt are independent instructions: their operation, filter and
target can intentionally differ. The comparison records those relationships.
Choose the pair that asks your question rather than assuming one implies the other.

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

This inventory identifies the capacities, execution budgets and evidence-retention
bounds a request encounters. Each row states what is counted, where the bound
applies and what happens there. Prepare the request using its grammar and action
relationships, then compare its measured quantities with these rows. After a run,
use the reported refusal or collection state to locate the relevant boundary.

Numeric capacity refusals carry `data.runner_result.admission_failure`, which names the
`field`, the `actual` count, the `maximum` and the `unit`, with location details
where available and `origin: "runner_host"`. Find that field in the "Refusal
names" column of the Specimen admission table; the row says what was measured
and which location fields are reported. To check a specimen before submitting
it, compare it with the same rows. Meaning refusals such as `duplicate_step_id`
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
  A blocked native call can outlast a checked deadline; final cleanup has its own
  observations and may remain unconfirmed.
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
  identify rejected queries, truncated output and unavailable parsing. Truncated output is not read as a complete capture or reply.
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
| Actor entitlement requirements (`actor_required_entitlements`) | 64 items | `actors.{actor}.required_entitlements` | Unique nonempty required boolean entitlement keys per actor. A count above the maximum refuses the request before any worker or validator starts; admission_failure reports unit items. | Fixed. |
| Actor entitlement requirement key (`actor_entitlement_key`) | 255 UTF-8 bytes | `actors.{actor}.required_entitlements.{key}` | Each actor requirement key, excluding NUL. An overlong key or embedded NUL refuses the request before any worker or validator starts; admission_failure reports utf8_bytes or nul_bytes. | Fixed. |

### Execution budgets

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Host reply flush delay (`host_exit_delay`) | 50 milliseconds | Delay scheduled once by the terminal execution or abandoned-reservation owner. The unsandboxed host schedules exit after the delay. An occupied host grants no further reservation; client acquisition can reconnect before submission. | Fixed. |
| Runner verification wait (`runner_verify_wait`) | 5,000 milliseconds | Default allowance for the fixed runner verify specimen, shared by reservation acquisition and the execution reply wait. Overall expiry reports xpc_timeout with the captured submission state. Acquisition may stop earlier at its attempt bound. Expiry after invocation does not establish nonexecution or cancel host work; worker/validator budgets remain separate. | Flag `--timeout-ms` on `runner verify`. |
| Worker policy delivery (`worker_policy_transfer`) | 5,000 milliseconds | One absolute monotonic deadline per policy delivery starting immediately after spawn; partial writes and interrupted calls do not restart it. Actor delivery is also capped by the remaining aggregate setup allowance. Expiry closes the input pipe and enters host cleanup with policy_transfer_timeout and policy_transfer_deadline; no write errno is invented. The worker, reaching EOF, publishes the count it read beside the host's expected length and refuses a different length before compiling; an observed refusal takes worker-failure precedence. | Fixed; internal driver controls may shorten it. |
| Worker readiness hint wait (`worker_ready_wait`) | 1,000 milliseconds | Elapsed monotonic wait after successful policy delivery and readiness-pipe setup, capped for an actor by remaining setup allowance. Expiry can leave `runner_subprocess.ready_byte_received: false` while the run continues. | Fixed. |
| Worker publication wait (`worker_sentinel_wait`) | 120,000 milliseconds | Elapsed monotonic publication wait for ordinary execution, starting after the readiness wait and excluding synchronous validator collection. Actor execution uses actor_execution_allowance instead. Expiry can yield `runner_timeout` with partial evidence and reported cleanup results. | Fixed; `_test_overrides.worker_timeout_ms` replaces the ordinary default with a floor of 50 ms and no ceiling. It does not change the actor schedule allowance. |
| Ordinary worker timeout override floor (`worker_timeout_override_floor`) | 50 milliseconds | Minimum ordinary worker publication-wait allowance selected by `_test_overrides.worker_timeout_ms`; zero and negative overrides select this floor. An override below this value is clamped before the ordinary worker input is built. Actor scheduling uses its own fixed allowance. | Fixed; a larger supplied override is used without a ceiling. |
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
| Runner removal observation interval (`runner_remove_poll_interval`) | 50 milliseconds | Requested delay between service observations after this removal call successfully boots out a service that remains present. Each delay is charged to the nominal teardown allowance; absence, an unknown observation or budget exhaustion ends polling. | Fixed. |
| External runner respawn throttle (`byoxpc_throttle_interval`) | 1 second | `ThrottleInterval` in every launchd plist that `runner install` generates. The host exits after each specimen and launchd starts the job at most once per interval; the wait is counted from the previous launch, not from the previous exit. The setting controls launch pacing, not a guaranteed request-delivery time. Without the key launchd uses its ten-second default. Acquisition reaching an occupied or retiring host can retry without sending the specimen. | Fixed in the generated plist. An installed plist can be edited by hand after `runner remove` and a fresh install; the registry's plist hash then differs and removal reports the ownership disagreement. |
| Aggregate phase collection allowance (`phase_collection_wait`) | 30,000 milliseconds | Cumulative monotonic planning and collection time across ordinary phases. Actor form uses the single actor_collection_allowance pool. Remaining allowance caps each validator I/O deadline; cleanup and scheduling can overrun it. After exhaustion, subsequent predictions are unavailable; the worker can still execute released attempts. | Fixed; `_test_overrides.validator_total_timeout_ms` can reduce it to at least 1 millisecond. |
| Sysctl value-read destination (`sysctl_read_bytes`) | 4,096 bytes | Destination for one post-apply sysctlbyname value read with a non-null buffer; no sizing call or retry. Larger values can fail within this bound. Returned value bytes and post-call length are discarded; a failed call does not diagnose whether capacity was insufficient. | Fixed. |
| Reservation lease (`reservation_lease`) | 5,000 milliseconds | Requested unused lease, capped by the host; the client requests no more than its remaining allowance. Expiry or owner disconnect retires the unused host. Submission checks expiry atomically and an old timer cannot terminate execution. | Fixed. No renewal. |
| Reservation RPC wait (`reservation_rpc_wait`) | 5,000 milliseconds | Maximum wait for one reserve reply, also bounded by the original overall client deadline. Expiry abandons and invalidates that connection; acquisition may continue without submitting a specimen. | Fixed per-attempt ceiling. |
| Reservation acquisition attempts (`reservation_attempts`) | 256 items | Every opened acquisition attempt, including transport failures and occupied replies. Exhaustion ends acquisition explicitly at attempt_limit with no submission; it can precede the overall timeout. Every attempted acquisition stays in the capture. | Fixed. |
| Reservation retry delay (`reservation_retry_delay`) | 100 milliseconds | Minimum delay between a failed/occupied attempt and another connection, within the remaining allowance. No delay after a successful grant. Scheduling may take longer; neither waiting nor progress renews the deadline. | Fixed minimum. |
| Actor termination dependency wait (`actor_termination_wait`) | 5,000 milliseconds | Maximum wait before a dependent phase, additionally capped by the remaining execution allowance. Expiry leaves the dependent phase unactivated and cancels the remaining schedule. A later cleanup reap does not satisfy the expired gate. | Fixed. |
| Worker fixture delay ceiling (`worker_fixture_delay`) | 60,000 milliseconds | Each --pre-ready-hang-ms or --post-apply-hang-ms worker argument forwarded from a positive request override. The worker argument parser refuses a larger forwarded value before worker setup; zero disables that fixture delay. | Fixed. |
| Aggregate validator collection override floor (`validator_collection_override_floor`) | 1 millisecond | Minimum aggregate collection allowance for either execution form. Zero and negative validator_total_timeout_ms overrides select this floor before phase planning. The remaining aggregate allowance still controls whether a validator is invoked. | Fixed; larger overrides are capped at the owning execution form's aggregate collection allowance. |

### Queries and transport

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Validator query payload (`validator_query_payload`) | 65,534 bytes | Serialized JSON bytes for one validator probe, excluding the final LF. JSON escapes count toward this size. An overlong line produces one `parse_error` without a step ID; later lines remain usable. Admitted specimens stay below this limit. | Fixed. |
| Runner client output (`controller_output`) | 285,212,672 bytes | Captured bytes per stdout or stderr stream from the runner client. Stdout carries a binary capture with opaque host bytes. Excess is marked truncated; a truncated capture establishes neither submission nor host evidence. Excess is marked truncated. Truncated client capture is not parsed, so submission remains unknown and no host evidence is inferred. | Fixed per-stream retention allowance; no flag. |
| Policy helper output (`policy_helper_output`) | 8,388,608 bytes | Captured bytes per stdout or stderr stream from each sbpl-check invocation, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply. | Fixed. |
| Rejected validator frame context (`validator_fault_context`) | 256 bytes | Retained prefix bytes of the first rejected validator frame; public JSON spells them as base64 in `context_b64`. `frame_bytes`, `retained_bytes` and `context_truncated` describe how much context was retained. | Fixed. |
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
| Client host reply retention (`client_reply_retention`) | 96,468,992 bytes | Binary host result bytes retained in the client capture; base64 is added only in public JSON presentation. Excess is explicitly truncated and cannot be admitted as a complete host result; received and retained byte counts remain distinct. | Fixed. |
| Typed response frame (`porcelain_frame_bytes`) | 134,217,728 bytes | One complete binary client capture or host reply, including its frame header. Larger frames are refused before typed record interpretation. | Fixed. |
| Typed decoded storage (`porcelain_decoded_storage_bytes`) | 134,217,728 bytes | One reader frame charges string bytes, opaque bytes and typed collection slots to a shared logical-storage budget. A charge exceeding the remaining budget refuses decoding before allocation; fixed record storage and allocator overhead are not physical peak-memory claims. | Fixed. |
| Typed response nesting (`porcelain_nesting`) | 32 levels | Reader cursor nesting within one binary frame; the schema generator separately refuses deeper record graphs. Deeper input is refused before reading another nested value. | Fixed. |

### Evidence capture

| Limit | Value | Counting and consequence | Control |
| --- | --- | --- | --- |
| Exec child output per stream (`exec_stream`) | 1,023 bytes | Retained stdout or stderr bytes for each exec child. An overflow marker occupies part of this allowance. Excess output is not retained. | Fixed. |
| Primary worker diagnostic (`worker_diagnostic`) | 4,095 bytes | Retained primary diagnostic bytes per worker, hence separately per actor. The reply reports retained length and truncation state; this is not a complete transcript. | Fixed. |
| Optional compiled-object capture (`compiled_profile`) | 1,048,576 bytes | Raw bytecode bytes per optional compiled-object receipt, separately for each opted-in apply actor; public JSON spells them as base64 in `bytecode_b64`. Oversized or unsupported objects leave capture unavailable without preventing policy application. | Fixed. |
| Worker observed path (`observed_path`) | 1,023 bytes | Retained bytes in each worker-observed path. Path observation can be absent or bounded; a host-side path diagnostic is a separate observation. | Fixed. |
| Worker attempt error text (`attempt_error`) | 255 bytes | Retained bytes in each worker attempt error message. Error text is bounded; structured result and status fields remain separate. | Fixed. |
| Phase records per worker region (`phase_records`) | 16 items | Fixed phase records in each worker shared header. Ordinary requests admit eight phases; public actor requests admit sixteen phases globally, so one actor can use all sixteen records. A worker refuses a header naming more phases than its records before application. | Fixed. |
| Authority slot storage (`authority_slot_bytes`) | 16,448 bytes | One token publication slot in an actor's authority region: a fixed header and the token buffer. A region holds one outbound slot per admitted issue and one inbound slot per admitted delivery to that actor, with distinct bounded transfer answer cells; nothing in it enters the reply. | Fixed. |
| Phase publication storage (`phase_publications`) | 512 bytes | Sixteen fixed 32-byte phase records within each shared header, one per visit an actor can be activated in; the legacy form uses the first eight. The legacy and actor-form phase caps prevent excess publication storage. | Fixed. |
| Fresh file-read prefix (`fresh_read_bytes`) | 64 bytes | At most one read from a freshly opened descriptor; `content_hex` spells only the returned prefix bytes, in lowercase hexadecimal. Reads of longer files remain supported; the bounded result does not claim complete file contents. | Fixed. |
| Request-failure path depth (`request_failure_path_components`) | 8 items | Components in a retained request_failure.path, including object keys and array positions. Excess withholds the entire path as null; no shortened location is substituted. | Fixed. |
| Request-failure path component (`request_failure_path_component`) | 63 UTF-8 bytes | Each component in a retained request_failure.path. The separate parameter_key admission-record echo has its own larger bound. Excess withholds the entire path as null; no shortened location is substituted. | Fixed. |
| Worker authority setup trailer (`authority_setup_trailer`) | 832 bytes | 64-byte header plus sixteen 48-byte independently published operation cells. The host retains eligible published setup and cleanup cells independently of the final setup decision; malformed publications are reported as integrity errors. | Fixed. |
| Worker authority setup operation cells (`authority_setup_cells`) | 16 items | Fixed operation slots per worker trailer, including separate cleanup facts. Each fixed slot publishes at most once. Unpublished cells supply no native result; invalid published cells are omitted and reported as integrity errors. | Fixed. |
| Equipment entitlement readback (`equipment_entitlement_bytes`) | 65,536 UTF-8 bytes | UTF-8 XML payload in each entitlement readback row. Overlong entitlement XML fails inventory decoding or signing readback. Static failure refuses actor preparation; live failure cancels scheduled activation. No XML prefix is reported. | Fixed. |
| Equipment static binding records (`equipment_static_bindings`) | 4 items | Two required packaged roles and at most two explicit role overrides. Preparation retains packaged and explicit override bindings, including refused rows. A failed binding prevents actor launch; the controller refuses replies above this table capacity. | Fixed. |
| Equipment live inspections (`equipment_live_inspections`) | 8 items | One inspection per usable actor, before any schedule activation. Actor admission bounds this population. A failed live inspection cancels scheduled activation and retains existing setup and application observations. | Fixed. |
| Equipment entitlement records (`equipment_entitlement_records`) | 12 items | Four static and eight live readbacks at the maximum actor and override population. Static and live readbacks share this table. Each reported readback is observed XML or a failure with an error; the controller refuses replies above this table capacity. | Fixed. |
| Sealed worker equipment inventory (`equipment_inventory_bytes`) | 1,048,576 bytes | Complete service-local inventory bytes read before actor preparation. A larger input is refused without selecting equipment. An observation exceeding this bound cannot establish eligible actor equipment. | Fixed. |
| Equipment diagnostic (`equipment_diagnostic_bytes`) | 1,024 UTF-8 bytes | Each equipment diagnostic is bounded before it enters a reply; longer observations retain a bounded diagnostic. An observation exceeding this bound cannot establish eligible actor equipment. | Fixed. |
| Equipment metadata record (`equipment_metadata_bytes`) | 32,768 bytes | Sum of UTF-8 bytes in the declared text fields of one static binding or live execution record, including binding error text or live native-operation names. Fixed scalar fields and the separately bounded entitlement plist do not count. An observation exceeding this bound cannot establish eligible actor equipment. | Fixed. |
| Equipment signing identifier or team (`equipment_signing_text`) | 255 UTF-8 bytes | Each nonempty signing identifier or team string in the equipment inventory and reported static/live equipment identity. Oversized inventory strings refuse inventory decoding; the equipment reader identifies oversized reported strings as invalid. | Fixed. |
| Equipment observed path (`equipment_path`) | 1,023 UTF-8 bytes | Each absolute inventory, binding or live execution path in the equipment report. The equipment reader reports an integrity finding for an overlong path; native signing-information decoding also refuses an overlong executable path. | Fixed. |
| Equipment native error domain (`equipment_error_domain`) | 128 UTF-8 bytes | Retained native NSError domain text in an equipment diagnostic, preserving complete Swift Characters. The producer retains the prefix that fits; the equipment reader reports an integrity finding for an overlong carried domain. | Fixed. |
| Authority cleanup object name (`authority_cleanup_name`) | 31 UTF-8 bytes | The absolute POSIX shared-memory name in a retained authority cleanup reference. The authority setup reader reports authority_cleanup_reference for an overlong carried name. | Fixed. |

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
  within the remaining execution allowance. Cleanup can outlast a
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
  `policy_helper_output`). Output beyond it is marked truncated, and
  truncated output is never read as a complete capture or reply.
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
`commit`, plus `contract`, the exact producer identity used for admission.
The same values are stamped into the app’s Info.plist. The descriptive build
coordinates correlate evidence with source; readers admit by `contract`.

### Reading a result

`policy-witness run` prints one envelope. Read it in this order: whether a host
report was admitted, what execution status was selected, which evidence checks
passed, and what each attempted operation actually observed.

| Part | Supplied by | Reading |
| --- | --- | --- |
| `data.runner_client` | Controller and runner client | Request delivery, capture retention, acquisition, submission state and received host bytes. |
| `data.runner_result` | Runner host | The retained decoded report: host outcome, steps, phases and worker observations. |
| `data.runner_sandbox_diagnostics` | Controller | Checks of the admitted report's evidence and the supported worker-ending projections. |
| `result` and command exit status | Controller | Whole-run classification, with the result/error selected at the boundary reached. |
| `data.specimen` | Controller | The saved request path, selected source/import inventory and runner/app provenance known before invocation. |

Admission proceeds through client capture, complete host decoding and the host's
producer/context checks. A decoded host report can remain in `runner_result`
when admission is refused; `runner_sandbox_diagnostics` is then null. Raw bytes,
decoded records and admitted evidence have different status. The
[receiver account](#receiver-evidence) identifies which is available.

#### What success means

For `run`, `result.ok: true` and exit 0 mean the controller admitted a host report
whose `normalized_outcome` is `finished`. The host reports completed, collected
execution and confirmed clean disposition. Any invoked validator has confirmed
clean disposition and complete, uniquely associated requested records without
transport/decode/association failure. Per-step diagnostics still have their own
meanings.

A finished run can contain failed attempts. For example, a completed open that
returns a permission-shaped failure remains a useful observation in a finished
run. Read the step's `attempt`, its native observations and `comparison` to
learn what happened to that operation.

The controller also checks evidence consistency. Those findings are reported
beside the completion result; they leave the host report and outer outcome
unchanged. An envelope can therefore contain `finished`, `result.ok: true` and
an `invalid` integrity finding with a withheld disposition. A consumer needing
consistent evidence checks the applicable integrity and issue records as well
as the outer result.

#### How the controller's findings qualify the report

For an ordinary worker, the diagnostics record its `process_disposition`,
`termination_cause`, `stop_reason`, `disposition_integrity` and
`disposition_issues`. The disposition is `no_worker`, `unconfirmed`, `clean_exit`,
`nonzero_exit`, `signaled`, `conflicting`, `unrecognized` or `withheld`.

| Scope | Consequence of a finding |
| --- | --- |
| Worker lifecycle | That worker's projection becomes `withheld`, with integrity `invalid` and cause `unknown`. Its raw observations remain in the host report. |
| Actor aggregate | Top-level `per_actor` directs the reader to `diagnostics.actors[]`. Any invalid actor projection makes aggregate integrity invalid; other actor entries retain their own results. |
| Reply-wide relationship | Top-level projection becomes `withheld`/`invalid`/`unknown`. Already computed actor projections of the carried rows remain available; identity, launch-association and action-membership findings still qualify their attribution to the requested actors. |
| Validated host conflict | The controller can report `conflicting` with integrity `valid` and copied host issues: it validated the evidence supporting that conflict. |

Here `diagnostics` abbreviates `data.runner_sandbox_diagnostics`. Null integrity
means there was no worker projection to validate. A nonempty issue list can
contain validated host conflicts as well as controller findings; read each
issue's kind and scope.

For owned-reap, phase-activation and termination-gate findings, an optional
`subject_path` locates the inspected assertion relative to
`data.runner_result`. Components are object keys and zero-based array positions:
`["phases", "2", "termination_gate"]` points to the third phase's carried gate,
even if labels are duplicated. A present null target is still addressable.
The path identifies the assertion; the producing check determines the projection
scope. Other findings can omit the path.

A supported termination cause names the complete host-cleanup chain:
`host_sentinel_deadline`, `host_exit_grace_exhausted`,
`host_cleanup_after_wait_error`, `host_cleanup_after_transfer_error` or
`host_cleanup_after_transfer_timeout`. A confirmed clean exit has null cause;
other endings remain `unknown` until their supporting chain establishes one of
these causes. Actor causes live in their actor entries. `stop_reason` records
why polling stopped, so an earlier deadline can coexist with a later clean exit.

#### What a reporting failure preserves

If host validation or encoding of the assembled result fails, the host attempts
to publish a replacement report. When the controller admits that fallback, its
outcome is `runner_reporting_failed`, with `rc: 1`, an error and
`reporting_failure` containing the diagnostic and original execution summary;
the command exits 1. If both the rich and minimal fallback writers fail, the
host returns empty bytes, which the controller cannot decode; follow
[When no host report was admitted](#when-no-host-report-was-admitted).

- `evidence_retained: true` retains the assembled observations while removing
  every comparison. Retained ordering fields are diagnostic; this form supplies
  no per-step `query_first` claim.
- `evidence_retained: false` identifies the minimal fallback with no steps or
  subprocess evidence.

The controller checks the degradation's outcome, diagnostic and permitted retained
form. Worker lifecycle projections still run, with the comparison-limitation
requirement waived for the removed comparison. Ordinary phase, native-operation
and actor-relationship check families apply to the nondegraded branch. Read the
remaining observations at the boundary where they were published.

#### When no host report was admitted

Use the nearby [outcome catalog](#normalized_outcome-catalog) to identify the
boundary. A missing or rejected client capture leaves submission unknown. A host
reply truncated or undecodable as a complete typed body leaves `runner_result`
null. A decoded but refused producer/context can remain there beside null
diagnostics. Request-delivery failure takes precedence as `tool_error`, even
when client bytes were retained.

Before retrying, distinguish a known request refusal from `invoked` or `unknown`
submission. Retain the request, output, stderr and independent target observations;
execution after invocation is never automatically replayed by the client.

### normalized_outcome catalog

`data.runner_result.normalized_outcome` values the runner can produce
(for the standalone helper's `bad_request`, `policy_too_large`,
`setup_error`, `compile_error` and `ok` outcomes, see
[SBPL check](#sbpl-check-sbpl-check)):

- `finished` — the host reports completed, collected execution. See
  [What success means](#what-success-means) for the distinction between that
  status, individual effects and integrity findings.
- `runner_timeout` — a host execution allowance expired, including sentinel
  polling or policy transfer. The retained timeout and disposition records
  identify the boundary. A later voluntary exit can coexist with the timeout;
  a published worker failure can take priority as `runner_failed`.
- `runner_failed` — execution/reporting failure, including inconsistent
  publication, a published worker operation failure, an incomplete
  report, abnormal or unconfirmed disposition, or a host wait/cleanup failure.
  The cause may be unknown. A completed report survives an abnormal exit as
  partial execution evidence.
- `runner_reporting_failed` — a fallback report after host validation or encoding
  of the assembled result failed. See
  [What a reporting failure preserves](#what-a-reporting-failure-preserves)
  for retained evidence and fallback limits.
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
  `data.request_failure`. See [Correcting a refused request](#correcting-a-refused-request).

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
from a captured client RPC timeout and from a received host reply retained
but refused as `unsupported_runner_response` or `malformed_runner_response`.

Controller-owned outcomes appear in `result.normalized_outcome`:

| Outcome | Boundary and recovery | Exit |
| --- | --- | --- |
| `tool_error` | Command/request-file handling, runner selection, client launch or request delivery failed. Read the error and retained delivery evidence before retrying. | 2 |
| `missing_runner_client` | No client capture arrived; submission is unknown. | 1 |
| `unsupported_runner_client` | The retained capture has another schema/contract; use matching app components. | 1 |
| `malformed_runner_client` | The capture is incomplete or fails decoding/state admission; inspect retained bytes and capture counts. | 1 |
| `runner_reply_truncated` | The accepted capture retained only a prefix of the host reply; its body supplies no decoded result. | 1 |
| `unsupported_runner_response` | The host frame or producer differs from the expected schema/contract; update the selected runner to match the app. | 1 |
| `malformed_runner_response` | Host framing, typed body or producer/context admission failed. A decoded body can remain beside the refusal. | 1 |
| `xpc_error` | The admitted client capture records a terminal transport error. Inspect submission state; an independent fallback compiler result may also be present. | 1 |
| `xpc_timeout` | The client allowance expired. Use submission state to distinguish a known unsubmitted request from possible execution. | 1 |
| `xpc_acquisition_failed` | Reservation acquisition exhausted its attempt bound; inspect the attempts and observed service state. | 1 |
| `xpc_submission_refused` | The execution method returned a reservation refusal; retain its reason and submission observation. | 1 |
| `xpc_protocol_error` | Reservation/transport control failed its protocol checks. | 1 |
| `runner_client_error` | The client recorded a local terminal failure; inspect its stage and native diagnostic. | 1 |

An admitted result with any host outcome other than `finished` exits 1. A
recognized client failure has its own record instead of a synthesized host
execution result. A reply can be delayed or lost after invocation; inspect
[Receiver evidence](#receiver-evidence) before repeating an effect.

<a id="shape-and-producer-contract"></a>

### Worker and host records

The XPC host stays unsandboxed and spawns an attempt worker for each declared
process, plus a fresh batch validator for each eligible phase. In a
single-worker reply, `runner_subprocess.pid` names the worker; top-level `pid`
copies that PID when worker output exists and otherwise names the host. In an
actor-form reply, top-level `pid` names the host, and each actor's `launch.pid`
and `subprocess.pid` identify its worker when present. The separate capture's
`client_pid` names the helper.

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
is unavailable, and leaves cleanup, EOF and reap unavailable at that boundary. See [Structured exec observations](#structured-exec-observations).


### Top-level fields

Reply fields beyond `pid` / `runner_subprocess`:

- `execution_form` — actor assembly emits `actors`; the ordinary producer
  omits the field. An actor-form reply has no `runner_subprocess`,
  `policy_sha256` or `sandboxed_after_apply`; each actor carries its own
  subprocess record, policy hashes and application account.
- `actors[]` — one record per actor in request order: `actor_id`, `index`,
  `mode`, `setup_status` (`applied`, `unapplied_declared`, `setup_failed`,
  `exited_before_setup`, `setup_timeout`, `launch_refused`,
  `transfer_failed`, `authority_setup_failed` or `not_launched`), an optional
  `applied` observation collected from an `apply` actor, `application_count`,
  the host's `policy_sha256` and the worker's `policy_received_sha256`, the
  `launch` context (`pid`, `parent_pid`,
  `environment`, `standard_streams`, `inherited_descriptors`), the actor's own
  `subprocess` with its disposition record, an optional `compiled_profile`
  and `visits` (its declared phase ordinals). The corresponding phase records
  separately state whether activation and subsequent progress were observed.
- `schedule` — actor setup/execution waits and aggregate budgets, plus the
  cancellation reason when traversal stopped. Read individual phases to see
  which activations and results were actually observed.
- `equipment_inventory`, `equipment_bindings`, `equipment_entitlements` and
  `actors[].equipment` — service/worker selection, signing and entitlement
  observations, followed by the actor's owned live-code observation.
  `preparation_failure` identifies a host preparation refusal before the planned
  actor schedule. Keep that refusal beside any setup/cleanup observations.
- `actors[].application` — the classified setup/application account, read with
  the worker's raw publication. The reply's top-level `authority_setup` records
  host scopes and actor-indexed worker apparatus decisions. Selected equipment
  and live inspection have their own records. An unapplied
  declaration, a failed apply and missing publication describe different states.
- `actors[].owned_reap` — the host's observed final status of its owned worker,
  with an optional capture ordinal and timing observations. A termination request
  remains separate from this observation.
- `phases[].activation_observation` and `termination_gate` — whether the phase
  was activated and, when declared, whether the source actor's natural ending
  satisfied the dependency. Read the gate outcome and source reap/activation
  references together. The [extension workflow](#sandbox-extensions) describes
  failed evaluated gates and later schedule cancellation.
- `transfers[]` and `resources` — the host's record of each explicit exchange
  and the token, delivery and handle tables; see
  [extension output](#extension-and-fresh-read-output).

- `phases[]` — ordered records with `phase_id`, one-based `ordinal`, ordered
  `action_ids`, `arrival_observed`, `completion_observed` and `collection_status`.
  Status is `not_reached`, `not_needed`, `collected`, `budget_exhausted` or
  `clock_unavailable`; `collected` includes failed or partial collection.
  Ordinary orchestration includes `ordering` with collected worker output;
  actor assembly also needs the corresponding visit in that output.
  Each `steps[].phase_id` identifies the phase owning its query, attempt and
  comparison. Phase completion and
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
  | Final status unconfirmed | Neither status field supplies a value; the current projection omits both |

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
- `steps[].comparison.order` — `query_first` when the step has a native allow or deny answer, its phase's complete collection, release and acknowledgement chain, established setup and one exact validator record; `unestablished` otherwise. Query order establishes an interval before that phase’s entire action batch. [When `order` is `unestablished`](#when-order-is-unestablished) names the fields behind each requirement.
- `phases[].ordering` — host collection/release observations, worker acknowledgement, worker lifetime evidence, validator disposition and protocol violations. After collection closure, release still requires the expected live worker phase. Validator failure or unconfirmed cleanup does not itself prevent release; no later record enters a closed collection. Missing predictions remain unestablished. Death before acknowledgement prevents a query-first claim; later death preserves it. `validator_disposition` is `not_invoked`, `not_needed` (empty query plan), `not_spawned`, `reaped` or `unconfirmed`.
- `steps[].comparison` — six fields that relate the two channels. `observation`
  classifies the attempt channel (`succeeded`,
  `permission_failure`, `other_failure` or `unavailable`) and
  `observation_basis` names the fields it rests on (`completed_worker_status`,
  `permission_errno`, `bootstrap_permission_result`, `spawned_child` or
  `no_completed_worker_result`);
  [What a permission failure establishes](#what-a-permission-failure-establishes)
  gives the fields behind each basis. `operation_relation` (`matched`, `different`
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

The subprocess record carries `worker_evidence` when the collected shared
memory has the expected worker identity. Its `abi_identity` identifies the
host-selected protocol sources.
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
[the worker disposition record](#worker-and-host-records). A completed
attempt's `rc` is PW attempt status. For `read_fresh`, the separate
`attempt.fresh_read` fields retain native open, fstat, read and close returns.


### Receiver evidence

Read `data.runner_client.submission` before recovering from a transport failure:

| State | Established boundary | Recovery |
| --- | --- | --- |
| `not_invoked` | An admitted capture records that execution was never submitted. | Correct the acquisition/selection problem, then prepare a new run. |
| `invoked` | The client called execution on its reserved connection. | Inspect retained reply and independent effects before any repeat. |
| `unknown` | A complete current capture was unavailable or refused. | Preserve available bytes/diagnostics and investigate service and target state. |

The client can reconnect during reservation acquisition, within its original
allowance. Once it invokes execution, a later error or timeout ends that attempt;
it performs no replay. The client allowance, host/worker execution budgets and
output-retention bounds are separate.

`data.runner_client` reports the client's `argv`, start and end milliseconds,
`exit_code`, exact received/retained stdout and stderr byte counts and
`capture_limit_bytes`. `stdout_capture_error` means the controller truncated
its own retained reply; `stdout_parse_error` means the untruncated bytes could
not be decoded as a supported binary capture. Records inside a lost envelope are unavailable. The
independent fallback helper's admission refusal remains `policy_too_large`.

An admitted client frame is projected in `transport`; a rejected one is
retained there as raw bytes. `transport_admission`
is `accepted`, `missing`, `unsupported`, `malformed` or `delivery_failed`;
`transport_error`
explains rejection. The controller's `submission` projection is `invoked`,
`not_invoked` or `unknown`. It is known only from an admitted capture.
`runner_reply_error` reports truncated host bytes, a host frame written under
another typed schema, or a host body that is not a complete typed record; the
retained bytes remain available inside the capture. A host from another build,
such as an external runner installed before an app update, can produce the
second case after it has executed the specimen.

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
producer contract before its meaning is used. Client transport failures do not
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

`phases[].validator_subprocess` names the phase it served (`phase_id` and `ordinal`,
which readers require to match the containing phase, with expected IDs equal to
that phase's eligible query plan) and retains accepted `records` (including null-ID diagnostics)
and their `raw_line`, expected IDs, association issues, received stdout byte
count, probe write counts, independent I/O/decode faults, termination-call
observations and actual reap status. Duplicate IDs supply no unique per-step
prediction. Rejected-frame context remains diagnostic evidence. Unfamiliar
structurally valid diagnostic outcomes remain visible even when their per-step summary is
`error`.


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
- `actors[]`: per-actor source augmentation and import inventories in request
  order, with the actor label when available. Compare each selected source with
  that actor's reported `policy_sha256`; the ordinary `policy` dossier describes
  the ordinary form. Both record source selection independently from what the
  compiler later reads from imported files.
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

If you have `jq` installed, this optional view selects the ordinary source
hashes and binary provenance from the quick-start result. The complete saved JSON
is usable without `jq`:

```sh
jq '.data.specimen | {request_path, policy: {augmentation: .policy.augmentation.status,
  applied_sha256: .policy.augmentation.applied_sha256, imports: .policy.imports.status,
  closure_sha256: .policy.imports.closure_sha256}, host, runner: .runner_provenance.runner_kind,
  binaries}' "$PW_WORK/create-result.json"
jq '[.data.specimen.policy.augmentation.applied_sha256, .data.runner_result.policy_sha256]' "$PW_WORK/create-result.json"
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
unrelated operations remain observable. These decisions record why the corresponding native call was not made.

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
bounded prefix. Actor equipment, native actions and fresh access retain their separate observations. Read the native event, custody/transfer status and later fresh access result
in that order; each supplies the observation in its own row.

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
- `filter_type_id` records the validator's selected numeric filter ID when
  available: `none` uses 0, `path` uses 1 and `global_name` uses 2. The global-name
  mapping was checked against native observations in the documented calibration;
  the alternative ID 12 also matched that control. The `mach-lookup/local_name`
  pair is excluded, while another operation with `local_name` reaches the
  validator's candidate ID 3. A query skipped by the planner or rejected by the
  validator has no native filter-ID observation. Read the particular
  [excluded pair](#filter-kinds-where-prediction-is-unavailable), provenance and
  native return together.
- `outcome`: `allow`, `deny`, `error`, `unsupported_operation`, or
  `prediction_unavailable`.
    - `allow` / `deny`: `sandbox_check` returned a clean verdict.
    - `error`: no usable prediction. This includes native call errors,
      validator diagnostics and synthetic missing replies. Consult
      `result_source`, `native_rc`, `missing_reason` and run-level records;
      diagnostic text can come from the validator or host as well as the native call.
    - `unsupported_operation`: `sandbox_check` returned `rc=-1` +
      `errno=22` (EINVAL), which most commonly means the operation
      name was rejected by the native call. `error` retains the validator's
      diagnostic naming the operation and its hint that SBPL family operations
      are typically queried in wildcard form, such as `process-exec*`. Keep that
      hint beside the recorded return rather than treating it as a compiler rule. The step
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

- `ok` — the attempt reports successful aggregate status; its operation-specific
  observations describe the effect.
- `read_failed` — a fresh-descriptor open, stat, read or close failed; inspect `fresh_read` for the separate syscall observations.
- `write_failed` — a fresh write or exclusive creation encountered a failed open, descriptor stat, truncation, write or close, or a short transfer; inspect `fresh_write` for separate observations.
- `open_failed` — file `open()` (for `open_read` / `open_write` /
  `create`) returned a negative file descriptor; errno in `attempt.errno`. EPERM /
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
  identify the native failure reported. Establishing its cause requires
  additional evidence about the target and execution conditions.
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
  [supported attempts](#attempt-kinds-the-runner-implements).
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

`steps[].comparison` relates a step's two channels: the query answer in
`sandbox_check` and the native result in `attempt`. It classifies the attempt,
compares what the specimen submitted to each channel and states whether the
host established that the answer preceded the phase's actions. No field in the
record, or elsewhere in the reply, says that the prediction and the attempt
agree or disagree. That conclusion is yours to draw, and it needs the
observations described here.

The next three subsections each start from a step you are looking at.
[The complete rules](#the-complete-rules) cover every field and case.

#### When the answer and the attempt differ

Take a step whose `sandbox_check.outcome` is `deny` and whose
`comparison.observation` is `succeeded`. The same reading applies to an `allow`
beside a failure. Check these fields before setting one channel against the
other:

| Field | Value that permits the comparison | Any other value |
| --- | --- | --- |
| `sandbox_check.result_source` and `outcome` | `validator` with `allow` or `deny` | The step has no query answer. Read `error`, `native_rc` and `missing_reason`. |
| `comparison.operation_relation` | `matched` | `different`: the query named another operation than the one the attempt maps to. `unresolved`: a `file`/`create` or `create_fresh` attempt, an unsupported attempt, or a wildcard query other than `process-exec*`, has no single operation to match. |
| `comparison.target_relation` | `same_submitted` | `different_submitted`: the query and the attempt submitted different strings, which can still resolve to one object. `unresolved`: the query's filter kind differs from the attempt's, or one of the two values is absent. |
| `comparison.order` | `query_first` | `unestablished`: the host did not establish that the answer preceded the attempt. See [When `order` is `unestablished`](#when-order-is-unestablished). |
| `comparison.limitations` | empty | Each entry names a planner exclusion or an attempt whose lifecycle is not `completed`. |

When every field has the value in the middle column, the record establishes
this much: the validator asked `sandbox_check` about this worker, using the
operation PolicyWitness maps the attempt to and the same submitted target
string; the host collected that answer before releasing the phase's actions;
and the worker's attempt then completed as recorded. For exec, a matched
`process-exec*` query concerns admission of the target only. A claim that
prediction and enforcement agree or disagree needs more:

- **The same runtime object.** `same_submitted` compares submitted strings.
  One spelling can resolve to different objects for the query and the attempt.
  `observed_path` and a fresh descriptor's `identity` come from the worker's
  attempt; `path_diagnostics` comes from the host after the run. None of them
  shows which object the query consulted.
- **Unchanged state across the interval.** `query_first` places the answer
  before the phase's whole action batch. An earlier action in the same phase
  can change the target or the worker's own sandbox state, for example by
  consuming or releasing an extension, and a process outside the run can
  change the target. Give the action its own [phase](#ordered-phases) to
  collect nearer to it, and observe the state independently.
- **The attempt's effect.** `succeeded` rests on the worker's reported status
  or, for exec, on a spawned child. Read the operation's own observations, such
  as fresh-read bytes or the child's exit status, and confirm the effect
  outside the run.
- **A failure's cause**, when the attempt failed. See
  [What a permission failure establishes](#what-a-permission-failure-establishes).

#### When `order` is `unestablished`

The host sets `comparison.order` to `query_first` only when four requirements
hold for the step. `unestablished` means at least one did not; it does not mean
the attempt came first. These fields show which:

| Requirement | Fields to read | Why it can be unmet |
| --- | --- | --- |
| A native answer | `sandbox_check.result_source` is `validator`, and `outcome` is `allow` with `native_rc: 0` or `deny` with `native_rc: 1` and `errno: 0` | The planner excluded the query (`prediction_unavailable`, with a `query_plan:` entry in `limitations`). The native call returned `EINVAL` (`unsupported_operation`), most commonly for a rejected operation name. The validator returned a diagnostic or no record (`error`, `missing_reason`). |
| The phase's collection chain | In the `phases[]` entry with the step's `phase_id`: `ordering.collection_closed_before_proceed`, `proceed_set`, `proceed_observed` and `worker_lifetime_established` are all true and `protocol_violations` is empty | The worker exited or stalled before acknowledging release, or its release wait expired. With no worker there is no `ordering` object. |
| Established setup | Ordinary form: `sandboxed_after_apply` is true. Actor form: the step's actor has `setup_status` `applied` or `unapplied_declared` | Compilation or application failed, or application was not observed. |
| One exact validator record | The phase's `validator_subprocess.records` has exactly one record with this `step_id`; its operation, filter, outcome, `rc` and `errno` equal the step's `sandbox_check`; and `sandbox_check.pid` is the worker's PID | The validator's output was partial, or a record was missing, duplicated or different from the planned query. |

Use the table to find the unmet requirement. The host decides `order` from its
own observations, so matching fields in a reply that says `unestablished`, or
in a `runner_reporting_failed` reply without comparisons, do not establish
`query_first`.

An unestablished step still supplies its attempt result and classification,
the two submitted relations and its limitations. A retained `allow` or `deny`
remains the native call's return. Without `query_first` it does not establish
that the query met the live worker under its established setup, so it is not a
prediction about the specimen. Each step is assessed separately: another query's failure in the
same phase leaves an eligible answer its `query_first`.

`query_first` does not depend on the attempt. A step can carry it beside an
`unavailable` observation when the worker stopped after acknowledging release.

#### What a permission failure establishes

`observation` classifies the shape of the attempt's native result, and
`observation_basis` names what that classification rests on. The host takes the
first row that fits:

| `observation` | `observation_basis` | Rests on |
| --- | --- | --- |
| `succeeded` | `spawned_child` | A completed exec attempt with a positive `child_pid`, whatever the child's later exit. |
| `succeeded` | `completed_worker_status` | A completed result with `outcome: ok` and `rc: 0`. |
| `permission_failure` | `permission_errno` | A completed, failed open, read, write, unlink, access, sysctl or exec result whose `attempt.errno` is 1 (`EPERM`) or 13 (`EACCES`). |
| `permission_failure` | `bootstrap_permission_result` | A failed Mach lookup whose `attempt.error` is `bootstrap_look_up: kr=1100`. |
| `other_failure` | `completed_worker_status` | Any other completed result with a nonzero `rc`. |
| `unavailable` | `no_completed_worker_result` | No completed worker result. Read `attempt.missing_reason` and `attempt.lifecycle`. |

`permission_failure` says that the native call returned a permission-shaped
result. Sandbox enforcement is one cause of such a result. File mode and
ownership, access-control lists, file flags and other system policy are
others. The classification does not say which applied, and a `deny` answer
beside it does not either: the answer is a separate query-channel record, and
a prediction collected before the actions only when `order` is `query_first`.

To attribute the failure, add evidence that separates the causes. For example:

- perform the same operation outside PolicyWitness before the run, to learn
  whether it fails with no specimen policy applied; that process differs from
  the worker in more than the policy, so a success there does not single out
  the policy;
- run a control specimen whose policy differs only in the rule in question,
  and compare the two attempts;
- record the target's existence, mode and ownership independently.

Keep those observations with the result. The attribution they support is your
conclusion; the report does not state it.

#### Recorded scenarios

These rows come from the scenario fixture that PolicyWitness's tests check
against the app. Its specimen's policy allows by default and denies reading the
file named `denied`. `readable` is an ordinary file, `locked` has mode 0000,
`absent` does not exist and `helper_true` is a program that exits 0. Query is
the answer in `sandbox_check`, or `unavailable` when the step has none. The
other columns are the comparison fields. The last column is the fixture's
control note: the independent observations the test makes, such as direct open
and spawn results and file bytes before and after the run, and for some rows
the policy text or native behavior the row relies on.

<!-- BEGIN COPIED COMPARISON SCENARIOS -->

| Row | Scenario | Query | Observation | Basis | Operation | Target | Order | Limitations | Independent control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S02 | deny, read EPERM | `deny` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | policy denies file-read-data on this literal path; denied bytes unchanged; the failure is read under reading rule 3 (the envelope does not attribute it to the sandbox) |
| S03 | allow, mode-000 file EACCES | `allow` | `permission_failure` | `permission_errno` | `matched` | `same_submitted` | `query_first` | — | direct open of locked outside PW fails with EACCES before the run; mode 0000 is a DAC condition, not policy |
| S05 | query denied path, attempt other path | `deny` | `succeeded` | `completed_worker_status` | `matched` | `different_submitted` | `query_first` | — | readable and denied bytes unchanged |
| S06 | query write, attempt read | `allow` | `succeeded` | `completed_worker_status` | `different` | `same_submitted` | `query_first` | — | readable bytes unchanged |
| S07 | absent path, both channels | `unavailable` | `other_failure` | `completed_worker_status` | `matched` | `same_submitted` | `unestablished` | `query_plan:path_unresolved_at_planning` | absent does not exist before or after the run |
| S11 | bare process-exec query, spawn ok | `unavailable` | `succeeded` | `spawned_child` | `different` | `same_submitted` | `unestablished` | — | direct spawn of helper_true exits 0; the native API rejects the bare spelling |

<!-- END COPIED COMPARISON SCENARIOS -->

- S02 and S03 carry identical comparison fields. S03's control shows an
  equivalent open failing without the specimen policy. S02's policy contains a
  matching deny rule; its row still does not attribute the failure to the
  sandbox.
- S05 has a `deny` beside a success, and `target_relation` is
  `different_submitted`: the query named the denied file and the attempt
  opened another for reading. In S06 `operation_relation` is `different`: the
  query asked about writing and the attempt opened the file for reading.
- S07 and S11 have no query answer, so their order is `unestablished`. S07's
  planner exclusion appears in `limitations`. S11's `unsupported_operation`
  outcome appears in `sandbox_check` and not in `limitations`.

#### The complete rules

Read the channels' results, relations and order with these rules:

<!-- BEGIN COPIED READING RULES -->

1. The raw query answer is `sandbox_check.outcome` when `result_source`
   is `validator` and the outcome is `allow` or `deny`. For another outcome,
   read `result_source`, `native_rc`, `error` and the optional `missing_reason`
   together: a received diagnostic and a synthetic missing answer are distinct.
   An otherwise
   eligible answer qualifies as a prediction about a live specimen only with
   its phase's collection/release/acknowledgement chain, reflected by
   `comparison.order: query_first`. Neither successful attempts nor a successful
   run are required. Without that chain, retained native answers do not establish
   whether the target was live during any particular query. A degraded
   `runner_reporting_failed` reply certifies no per-step order, even when raw
   ordering observations survive; every comparison is omitted.
2. `attempt.result_source` distinguishes a completed worker publication from
   a synthetic unavailable result. `attempt.missing_reason` and `attempt.lifecycle`
   describe the missing publication and the supported action boundary.
3. Read a `permission_failure`, `other_failure` or nonzero child exit as the
   recorded observation. Attributing it to sandbox enforcement requires evidence
   that distinguishes that cause from the other causes of the native result.
4. `same_submitted` compares the submitted path bytes. Runtime object identity
   requires its own observations across the query and attempt.
5. `query_first` establishes an order; state may change during that interval.
   Keep independent state observations when a comparison depends on continuity.
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

#### Selecting steps with jq

With optional `jq`, select steps by explicit field combinations from a saved
result. For these commands, set `PW_RESULT` to that result's absolute path:

```sh
PW_RESULT="$PW_WORK/create-result.json"
```

A deny
answer beside a successful attempt, with the relations and order that qualify
it:

```sh
jq '.data.runner_result.steps[]
    | select(.sandbox_check.outcome == "deny" and .comparison.observation == "succeeded")
    | {step_id, operation_relation: .comparison.operation_relation,
       target_relation: .comparison.target_relation, order: .comparison.order,
       limitations: .comparison.limitations}' "$PW_RESULT"
```

Steps with no usable prediction, and why:

```sh
jq '.data.runner_result.steps[]
    | select(.sandbox_check.result_source != "validator"
             or (.sandbox_check.outcome | IN("allow", "deny") | not))
    | {step_id, outcome: .sandbox_check.outcome, result_source: .sandbox_check.result_source, native_rc: .sandbox_check.native_rc,
       error: .sandbox_check.error, missing_reason: .sandbox_check.missing_reason,
       limitations: .comparison.limitations}' "$PW_RESULT"
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
with the literal leaf appended. That later host spelling keeps the submitted
leaf instead of following it, which is useful for inspecting create, unlink and
symlink experiments. Either is null when the host
cannot derive it (a missing leaf has no leaf-followed form; a relative path has
no parent form). Neither establishes what the worker's own syscall resolved,
and neither changes the attempt or its comparison.

With optional `jq`, inspect the submitted query and its later host diagnostics:

```sh
jq '.data.runner_result.steps[].sandbox_check | {filter_value, filter_type_id, outcome, path_diagnostics}' "$PW_WORK/create-result.json"
```


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
one of these filter kinds with a different operation goes through ordinary
query planning. If eligible, it reaches validator processing, which can return
its own filter/operation diagnostic or a native answer. Read `result_source`,
`outcome` and `native_rc` to distinguish those results. The exclusions are
specific to the listed pairs.

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
  inside the attempt, after policy application or an actor's unapplied declaration,
  and releases them before the step completes. The bare-deny control observes successful setup followed
  by a permission-shaped failure at `posix_spawn` for its tested inputs and
  environment. Setup can fail at an earlier call; its recorded boundary and
  native error do not establish a sandbox cause. Actor attempts begin after usable applied setup or the explicit unapplied
  declaration; their recorded native results identify the boundary reached. The worker bounds each child
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

  The optional [exec augment](#augments) supplies the shipped process and file-read
  allow rules. It broadens the source selected for compilation; inspect the helper's
  actual native observations to establish how far it progressed in your environment.

  The helper is spawned with `POSIX_SPAWN_CLOEXEC_DEFAULT`, inheriting only
  stdin=/dev/null and its stdout/stderr pipes, and an empty environment,
  whatever `EnvironmentVariables` an external runner's launchd plist gave the
  host. Actor workers themselves use an empty environment, recorded in their
  launch context; the ordinary worker inherits its host environment without a
  corresponding full environment snapshot. The helper's own failure is
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

| Command option | Effect |
| --- | --- |
| `run FILE --timeout-ms N` | Sets the client acquisition/reply allowance. Host, validator and worker budgets keep their own values. |
| `run FILE --runner-mode standard` or `byoxpc` | Supplies the runner-mode selection; external selection still requires its registered ID or service. |
| `--version` | Prints a version envelope with `build.contract` and descriptive build coordinates. Save it with the specimen. |
| `example` | Prints one specimen that this build defines, carrying the build's own contract identity, for the same build's `run`: `example > FILE`, then `run FILE`. It takes no argument and prints a request, not an envelope. Exit 0 supplies the complete document; on exit 2 discard the output. The document can differ between builds. The project uses it to test a build against its own example. |

### Running specimens in parallel

Each invocation uses a controller and client to acquire a fresh host. An ordinary
request uses one fresh worker; actors each receive a fresh worker retained across
that actor's visits. Each phase with eligible queries receives a fresh validator.
Exec attempts can launch children, and a terminal XPC error can trigger independent
compiler helpers. These lifetimes overlap, so concurrency increases process and
resource pressure.

Use separate work directories, request/result files and effect targets per run.
An occupied host can refuse reservation; acquisition can reconnect within its
original attempt/deadline limits. An installed external service also has launchd
pacing. Inspect the outcome and [submission state](#receiver-evidence) of each
run; scheduling delays and cleanup can outlast an earlier observation or deadline.

### Troubleshooting

| Observation | Inspect and recover |
| --- | --- |
| `bad_request` | Read the structured code/path or capacity record and follow [request correction](#correcting-a-refused-request). |
| Unknown or pending external runner | Save `runner list` and `runner reconcile`; use the recorded service/ID and finish installation or cleanup before ordinary selection. |
| `unsupported_runner_response` or foreign registry contract | Compare the selected runner's contract with saved `--version`; prepare and reinstall a current intact service. Preserve old reports with their original app identity. |
| `worker_spawn_failed` / `validator_spawn_failed` | Read the failed executable, direct native return and diagnostic. Inspect that exact artifact's availability, signatures and inventory before changing it. |
| `runner_failed` | Read worker failure publication, final status and cleanup independently; a signal or missing publication can leave the underlying cause unknown. |
| `xpc_timeout`, missing reply or capture refusal | Read submission state and inspect possible effects before repeating the request. Use the retained acquisition/transport diagnostics and observed service state. |
| User-scope bootstrap unavailable | Use a logged-in GUI session for that user. System scope requires its administrative authorization and has separate service ownership. |
| Signing or XPC lookup fails inside restricted automation | Preserve the artifact and diagnostic. Repeat a read-only signature/status check from a normal Terminal. Repeat execution only after its prior submission/effects are understood. |

For old request fields such as `instrumentation` or runner mode `debuggable`,
prepare a current request and select a BYOXPC worker with the needed entitlements.
Keep path restrictions in SBPL. Ordinary requests need `policy`; actor requests
put each policy under that actor's `sandbox` object.

## External runners (BYOXPC)

Choose the built-in `standard` runner when its worker equipment fits the
experiment. Use an external BYOXPC service when the selected worker needs
specific signing entitlements. Each run still gets a fresh host and fresh
specimen workers. The installer records the host, selected worker, unentitled
worker and validator separately; a worker entitlement is read from that worker's
metadata.

Before preparing another service, retain the current registry and observations:

```sh
"$PW" runner list > "$PW_WORK/runners-before.json" 2> "$PW_WORK/runners-before-stderr.txt"
"$PW" runner reconcile > "$PW_WORK/reconcile-before.json" 2> "$PW_WORK/reconcile-before-stderr.txt"
```

Inspect `runners`, `pending_cleanup` and reconcile's observed service/plist state.
Resolve ownership of an existing service before reusing its label or bundle path.
A label prefix is a discovery hint; the durable record supplies cleanup ownership.

### What you need

- An intact current `PWRunner.xpc` copied from the selected app, including its
  nested workers, validator and sealed equipment inventory.
- A Developer ID Application identity whose Team ID matches the app's caller.
- An actual entitlements plist for the selected worker.
- A logged-in GUI session for user scope, or administrative authorization for
  system scope.
- A fresh staging directory you own, retained while the registry refers to it.

The external service must advertise the app's exact `PWContract`. Installation
checks the signed bundle; run and verify check the live peer. After changing
build identity, prepare a matching service before selecting it. Older records
remain available for inspection and removal.

### Install a BYOXPC runner

Continue from the quick start, using a new unique bundle path and service name.
Replace the signing identity and entitlement path with your own values. Keep
`$PW_WORK` until recovery is complete.

```sh
IDENTITY="Developer ID Application: Your Name (TEAMID)"
ENT="/absolute/path/to/your-entitlements.plist"
PW_RUNNER_STAGE=$(mktemp -d "$PW_WORK/runner.XXXXXX")
BYO="$PW_RUNNER_STAGE/PWRunner.guide.xpc"
SERVICE="com.policywitness.guide.$(id -u).$(basename "$PW_RUNNER_STAGE")"
cp -R "$APP/Contents/XPCServices/PWRunner.xpc" "$BYO"
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $SERVICE" "$BYO/Contents/Info.plist"
/usr/bin/codesign --force --options runtime --sign "$IDENTITY" "$BYO"
```

Continue after the copy, metadata edit and signing all succeed. Keep any failure
diagnostic with this staging directory. Then install the prepared service:

```sh
"$PW" runner install --bundle "$BYO" --identity "$IDENTITY" \
  --entitlements "$ENT" --scope user \
  > "$PW_WORK/install.json" 2> "$PW_WORK/install-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/install-exit.txt"
cat "$PW_WORK/install.json"
cat "$PW_WORK/install-stderr.txt"
"$PW" runner list > "$PW_WORK/runners-after-install.json"
"$PW" runner reconcile > "$PW_WORK/reconcile-after-install.json"
```

Changing `Info.plist` requires resealing the enclosing source service first. The installer verifies
that source seal and its complete worker inventory before changing signatures.
It then signs the selected worker with your entitlements, signs the validator
and unentitled worker with the identity alone, refreshes the inventory and seals
the service. Preserve the nested code while preparing the source copy.

On successful installation, save `data.runner.id`, `service_name`, `scope`,
`bundle_path` from `data.runner`, and `data.plist_path`. The durable ownership
record also keeps its verified plist path and launchd domain. The service name equals
`CFBundleIdentifier`; the executable comes from the bundle's
`CFBundleExecutable`, and its package type is `XPC!`.

Installation saves a `pending` registry record before publishing the launchd
plist and marks it `installed` after the installation step. A later failure can
therefore leave a record owning recovery, even when the command emitted only
stderr. Inspect list/reconcile after a failure and preserve the staging bundle.
A pending record remains available to status, explicit verify and removal;
ordinary `run` selection refuses it.

`--scope system` selects the system launchd domain. `--skip-bootstrap` finishes
installation after plist creation and leaves loaded state to a later explicit
bootstrap. `--env KEY=VALUE` configures launchd's host environment. Actor workers
and exec children retain their separately defined empty environments.

Keep effect targets under a directory you own, such as `/private/tmp`. Privacy
mediation for Desktop or Documents can introduce consent or blocking behavior;
record that boundary separately from the sandbox observation.

### Caller authentication and ad-hoc signing

The shipped service authenticates its caller using the signed caller's Team ID.
The signed workflow above preserves that check, so the runner and the app's
`pw-runner-client` need matching teams. Inspect the actual native diagnostic if
connection admission fails; a particular XPC error number alone does not identify
an authentication failure or prove that execution never occurred.

The installer also accepts `--allow-adhoc` for a coherent ad-hoc source service.
Its existing seal and equipment inventory must already match all role artifacts,
including their team observations. An ad-hoc service has no Team ID; using it for
local testing requires caller authentication to be deliberately disabled in its
source configuration and the complete service prepared and sealed consistently.
That configuration accepts local callers without the shipped team check. Removing
authentication keys or resealing only the host while leaving differently signed
workers produces an inconsistent source inventory, which installation refuses.

### Verify the runner

Inspect the installed record, then send the fixed diagnostic request:

```sh
"$PW" runner status --service-name "$SERVICE" > "$PW_WORK/status.json" 2> "$PW_WORK/status-stderr.txt"
"$PW" runner verify --service-name "$SERVICE" --timeout-ms 20000 \
  > "$PW_WORK/verify.json" 2> "$PW_WORK/verify-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/verify-exit.txt"
cat "$PW_WORK/verify.json"
```

Verify uses an allow-all policy and empty probe plan. An admitted `finished`
reply and exit 0 establish that diagnostic request's completed application/run;
inspect the retained client and host records. `runner_pid` is projected only from
an admitted reply. A refused response keeps the available records and its refusal
outcome with `runner_pid: null`; verify has no run diagnostics object.

The default verify allowance is <!-- span limits.runner_verify_wait.value_unit -->5,000 milliseconds<!-- /span -->;
`--timeout-ms` adjusts acquisition/reply waiting. Verification consumes one host.
The next request acquires a fresh host; the installed plist uses
`ThrottleInterval` of <!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span -->.
Observed startup and completion also depend on scheduling and cleanup.

### Use the runner in a specimen

Select the saved registry ID or exact service name in the request. For example:

```json
"runner": {
  "id": "runner-<id-from-install>",
  "mode": "byoxpc",
  "required_entitlements": ["com.apple.security.cs.disable-library-validation"]
}
```

Choose only entitlements the experiment requires. Each named key must have
boolean value `true` in the selected worker's readback (`worker_entitlements.granted`).
A missing or differently valued key refuses selection before contacting a host.
Actor `required_entitlements` adds that actor's own equipment/live-readback
requirement. Host entitlement metadata belongs to the host.

For a service-selected file-effect check, derive another request from the saved
quick-start input and use a new target:

```sh
/usr/bin/plutil -replace specimen_id -string guide-byoxpc-create \
  -o "$PW_WORK/byoxpc-create.json" "$PW_WORK/create.json" &&
/usr/bin/plutil -insert runner -dictionary "$PW_WORK/byoxpc-create.json" &&
/usr/bin/plutil -insert runner.service -string "$SERVICE" "$PW_WORK/byoxpc-create.json" &&
/usr/bin/plutil -insert runner.mode -string byoxpc "$PW_WORK/byoxpc-create.json" &&
/usr/bin/plutil -replace probe_plan.0.sandbox_check.filter.value -string "$PW_WORK/byoxpc-created" "$PW_WORK/byoxpc-create.json" &&
/usr/bin/plutil -replace probe_plan.0.attempt.target -string "$PW_WORK/byoxpc-created" "$PW_WORK/byoxpc-create.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/byoxpc-created"; then
  "$PW" run "$PW_WORK/byoxpc-create.json" --timeout-ms 20000 \
    > "$PW_WORK/byoxpc-create-result.json" 2> "$PW_WORK/byoxpc-create-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/byoxpc-create-exit.txt"
  cat "$PW_WORK/byoxpc-create-result.json"
  test -f "$PW_WORK/byoxpc-created"
  /usr/bin/stat -f 'size=%z mode=%Sp inode=%i' "$PW_WORK/byoxpc-created" > "$PW_WORK/byoxpc-observation.txt"
  cat "$PW_WORK/byoxpc-observation.txt"
else
  printf '%s\n' 'Request preparation failed or target exists; preserve its records and prepare a new effect target.' >&2
fi
```

The client reserves a host before submitting the specimen; acquisition messages
contain no specimen bytes. A grant is single-use and bound to its connection.
Occupied/lost acquisition connections can lead to another attempt within the
original limits. `submission: invoked` is recorded immediately before execution
is called. A later refusal, timeout or lost reply causes no replay. Read
[Receiver evidence](#receiver-evidence) before repeating a request whose effects
are uncertain.

### List, validate, or remove runners

Save inspection and cleanup results under the same owned work directory:

```sh
"$PW" runner validate > "$PW_WORK/validate.json" 2> "$PW_WORK/validate-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/validate-exit.txt"
"$PW" runner remove --service-name "$SERVICE" > "$PW_WORK/remove.json" 2> "$PW_WORK/remove-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/remove-exit.txt"
"$PW" runner list > "$PW_WORK/runners-after-remove.json"
"$PW" runner reconcile > "$PW_WORK/reconcile-after-remove.json"
```

Read the bodies as well as the exits. `runner validate` can exit 0 while reporting
`missing`, `invalid` or per-binary/inventory failures. It verifies the stored
bundle and refreshes observations; reconcile separately compares recorded state
with observed services/plists.

Removal first moves the runner into durable `pending_cleanup`, then checks
ownership before bootout and plist removal. Exit 0 means the remove command
completed its attempt; inspect `data.warnings`, `cleanup_retained` and the retained
record. Recovery is retired only after service and plist absence are verified.
An unknown inspection keeps recovery pending. Retrying the same remove command
continues that recovery, including after the plist has gone. `--skip-bootout`
keeps recovery until absence is observed.

Keep the bundle and saved install/remove records while either registry collection
owns recovery. After list/reconcile confirm retirement and service/plist absence,
the staging bundle can be removed and the experiment records retained wherever you
keep run evidence. The registry is normally
`~/Library/Application Support/PolicyWitness/runners.json`. Modifying commands
serialize through its stable advisory lock; retain the lock file while any
command may hold it.

For an unregistered candidate reported by reconcile, establish its exact service,
executable, bundle, scope and plist ownership before administrative cleanup. An
owned user service can be booted out with
`launchctl bootout "gui/$(id -u)/<recorded-service-name>"`; an owned system service
uses `sudo launchctl bootout "system/<recorded-service-name>"`. Inspect the command
result and actual service absence before removing the verified owned plist.
Preserve the observations if absence or ownership remains uncertain. A test
harness's durable cleanup session belongs to that harness; ordinary installed
services recover through their recorded registry ownership.

`runner status`, `runner verify` and `runner remove` report `not_found` with exit 2
when the lookup key is absent. The envelope `kind` still identifies the command.
Install and other command setup errors can instead emit stderr without JSON;
retain both streams and consult list/reconcile for any surviving ownership.

## Public contract surfaces

The release is the public contract unit. Review rows changed since the release
your specimen asserts before changing its `contract`. Stamps guide review;
admission compares the complete build contract exactly. The release's
[developer contract](https://github.com/Protonk/PolicyWitness/blob/v0.3.8/docs/CONTRACT.md)
defines the fields, applicability and obligations behind these surfaces. Use the
matching release's source when reading older reports.

<!-- BEGIN GENERATED CONTRACT STAMPS -->
| Surface | User artifact | Last changed |
| --- | --- | --- |
| `actor_evidence` | Actor and phase evidence | unreleased |
| `actors` | Actors and phases | unreleased |
| `diagnostics` | Controller findings and assessments | unreleased |
| `dossier` | Specimen dossier | unreleased |
| `envelope` | The controller envelope | unreleased |
| `equipment` | Equipment and authority setup | unreleased |
| `extensions` | Extension actions and authority custody | unreleased |
| `identity` | The contract identity | unreleased |
| `installation` | Managing runners | unreleased |
| `lifecycle` | Process and operation observations | unreleased |
| `policy` | Policy source, parameters and compilation | unreleased |
| `probes` | Paired probes and attempted operations | unreleased |
| `profile` | Compiled-profile receipts | unreleased |
| `refusals` | Request refusals and retained evidence | unreleased |
| `reply` | The host report | unreleased |
| `request` | Saved specimens and runner selection | unreleased |
| `steps` | Predictions, attempts and comparison | unreleased |
| `transport` | Reservation, invocation and client capture | unreleased |
| `wire` | Binary response primitives and validator record transport | unreleased |
<!-- END GENERATED CONTRACT STAMPS -->
