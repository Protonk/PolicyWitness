# Teaching the accepted request contract

This is a developer lesson. The [contract rules](CONTRACT.md#contract-request)
define the promise; the [specimen reference](PolicyWitness.md#specimen-format)
describes authoring. The `create` and `capture_typo` inputs are embedded in the
app from [controller-owned templates](../controller/src/lessons/README.md).
The [test corpus](../tests/fixtures/request_contract/examples.json) references
those inputs and owns the other examples. Expected refusals remain independent
data, checked by both Swift unit tests and live CLI/direct-XPC controls.

The [user guide exercise](PolicyWitness.md#try-an-accepted-request-and-a-refusal)
presents the same app-owned pair as standalone commands, with saved requests
and independent effect observations.

## Start with an observable instruction

The `create` example supplies an SBPL policy, one sandbox query, and one file
creation attempt. Supply an absolute path to an absent file. This makes
acceptance observable outside the returned JSON.

From the repository root, using a current signed build:

```sh
PW=dist/PolicyWitness.app/Contents/MacOS/policy-witness
PW_EXAMPLE_DIR=$(mktemp -d /private/tmp/pw-grammar.XXXXXX)
"$PW" lesson create --target "$PW_EXAMPLE_DIR/created" > "$PW_EXAMPLE_DIR/request.json" &&
cat "$PW_EXAMPLE_DIR/request.json" &&
"$PW" run "$PW_EXAMPLE_DIR/request.json" > "$PW_EXAMPLE_DIR/run.json" &&
test -f "$PW_EXAMPLE_DIR/created"
```

`lesson` prints a complete request with the emitting binary's contract and does
no execution or filesystem inspection. Exit 0 establishes publication; on exit 2
discard its output. The typo lesson deliberately produces a request that `run`
refuses. Neither lesson supplies a nonce. Keep the directory to inspect submitted
bytes and returned evidence.

Reading that request teaches three boundaries:

1. `contract` asserts the build contract the specimen was written for.
2. `(version 1)` inside `sbpl_source` belongs to SBPL, a nested language.
3. `sandbox_check` and `attempt` describe independent observations. A query
   result cannot establish the attempted operation's effect. The file check
   supplies that observation in this exercise.

## Change one thing and predict the result

An input grammar describes the allowed shapes. A contract also gives those
shapes meaning, specifies refusals, and distinguishes execution from admission.
Use the repository renderer for the broader corpus, for example
`tests/lib/python.sh tests/lib/request_examples.py capture --effect "$PW_EXAMPLE_DIR/captured"`.
It asserts the selected app's identity and generates a nonce for inputs that
request one. Expected behavior remains separately authored:

| Example | Lesson | Expected behavior |
| --- | --- | --- |
| `malformed_json` | JSON syntax | `invalid_json` at the root. |
| `retired_capture_spelling` | Retired field names | `unknown_field` at `policy.capture_applied_profile`. |
| `previous_request_version` | Previous contract | `unsupported_contract` before execution. |
| `capture_typo` | Closed field names | `unknown_field` at `policy.capture_compiled_profiel`. |
| `wrong_args_type` | Field types | `type_mismatch` at the attempt's `args`. |
| `parameter_value` | Open dictionaries | Parameter names are caller data, but their values must be strings. |
| `optional_nulls` | Defaults | The optional fields shown in this example treat null as absent; creation succeeds. Actor equipment, requirement and termination-dependency fields reject explicit null. |
| `duplicate_ids` | Meaning across steps | `duplicate_step_id` at the second step. |
| `file_args` | Meaning across fields | Even an empty non-null `args` array is inapplicable to a file attempt. |
| `unused_nonce` | Meaning across fields | A nonce without enabled capture is refused. |
| `unused_filter_value` | Meaning across fields | A `none` filter cannot consume a non-null value. |
| `unknown_filter` | Supported vocabulary | An unknown filter name refuses the specimen. |
| `unknown_attempt` | Supported vocabulary | An unsupported second attempt prevents the first valid create from running. |
| `over_capacity` | Admission | 257 distinct steps decode, then exceed the current <!-- span limits.probe_steps.value -->256<!-- /span -->-step capacity. |
| `foreign_contract` | Contract boundary | Another request contract is refused before its fields are interpreted. |
| `exec_args` | Effective arguments | `exec/spawn` of `touch` consumes its argument and creates the named file. |
| `capture` | Effective capture | Enabled capture returns a receipt with the submitted nonce. |
| `known_unavailable_prediction` | Witness limits | A recognized excluded query reports `prediction_unavailable`; the independent create still runs. |

Try the typo with a new, absent effect path:

```sh
if "$PW" lesson capture_typo --target "$PW_EXAMPLE_DIR/refused" > "$PW_EXAMPLE_DIR/typo.json"; then
  "$PW" run "$PW_EXAMPLE_DIR/typo.json" > "$PW_EXAMPLE_DIR/refusal.json"
  PW_EXAMPLE_RC=$?
  test "$PW_EXAMPLE_RC" = 1
  test ! -e "$PW_EXAMPLE_DIR/refused"
fi
```

Inspect `data.request_failure` in that envelope:

```json
{
  "code": "unknown_field",
  "path": ["policy", "capture_compiled_profiel"]
}
```

The runner's `request_failure` carries the same record when the runner made
the refusal. `error` remains human-readable; programs select the stable code
and path instead of parsing that prose. A path is an array of exact field
names and decimal array positions. The root is `[]`; `null` means the location
was withheld because it exceeds the diagnostic bounds. A path never presents
a shortened input key as its real name.

No worker or validator is created for these request refusals. The XPC host
may have launched to decode and refuse a request. File I/O, runner availability
and transport failures remain separate tool/execution failures.

## Divide ordinary actions into phases

Render `phases_create` to use the same paired action inside an explicit phase.
`probe_plan` and `phases` are mutually exclusive non-null forms; supplying both
or neither produces `exclusive_plan_forms`. The simple form has one execution
phase named `main`, so it shares the same barriers and evidence rules.

The corpus's phase controls cover empty/duplicate IDs, unknown phase fields,
missing query or attempt, global duplicate step IDs, and the inclusive phase,
identity and total-action bounds. Refusal paths identify
`phases`, the phase index, `actions` and the action index. Capacity comes before
meaning and no child is launched on either refusal. The guide's
[ordered-phase example](PolicyWitness.md#ordered-phases) describes the sequence
and how fresh planning can leave a later query unavailable after an unlink.

## Declare authority separately from lifecycle placement

Extension specimens use actors and explicit `issue`, `transfer`, `consume` and
`release` operations. The [sandbox-extension example](PolicyWitness.md#sandbox-extensions)
starts with an unapplied, unentitled issuer and an applied, selected subject.
Issuance happens inside the named actor at its scheduled action, using the exact
submitted absolute target. Native events do not have validator queries.

The top-level `extensions` field is refused even when null or empty. The retired
`issuer_executable_path` override is also refused by key presence. These are
current-schema field refusals, distinct from unsupported-version rejection.
`consume` takes `delivery_ref` and a new `handle_ref`; its removed `token_ref`
operand is refused even when null. Unknown fields remain closed at actor,
phase, action and operation objects. Raw class names and token bytes are not
request inputs. `write_fresh` and `create_fresh` remain ordinary file actions
with fixed one-byte writes, separate from `open_write` and `create`.

| Corpus family | Meaning or refusal |
| --- | --- |
| `removed_extensions_null`, `removed_extensions_empty_array`, `removed_extensions_array` | The declaration field is refused in the current schema. |
| `removed_issuer_override_null`, `removed_issuer_override_path` | The removed helper override is refused, including null. |
| `consume_removed_operand_null`, `consume_removed_operand` | Actor consumption names its delivery, without declaration operands. |
| `actor_issue_authority_null`, `actor_issue_authority_unknown`, `actor_issue_authority_empty`, `actor_issue_authority_boolean`, `actor_issue_authority_number` | Issue authority is a required closed string choice, not a nullable default. |
| `actor_issue_raw_token`, `actor_issue_raw_extension_class` | Bearer bytes and native class strings are not accepted. |
| Reference and target exact/over cases | UTF-8 byte capacities apply to ASCII and multibyte strings. |

The compact `repeat_phase_actions` recipe repeats an ordinary action and
partitions the requested total into phases. Swift admission and the Python
CLI/XPC materializer implement the same recipe; expected refusals remain
independent corpus data. Admission is separate from native availability and
from the observed effects of an admitted action.

## Give each actor its own sandbox

The actor form replaces the singular `policy` with `actors`: each actor has an
`actor_id` and a `sandbox` whose `mode` is `apply` (with its own `policy`
object) or `unapplied` (no specimen policy application; inherited restrictions
remain). Every phase names its `actor_id`, every declared actor owns at least
one phase; `probe_plan` and singular `policy` are absent. The `extensions`
field is refused in every request form. The
corpus's `actors_redelegation` is the principal specimen: an unapplied `A`
issues a file token and transfers it to `B`; `B` consumes it, reads, issues
under the consumed extension and transfers to `C`; `C` consumes and reads;
both handles are released; a final phase has `A` create the corpus's effect
file, the independent witness that the request executed. The guide's
[sandbox-extension section](PolicyWitness.md#sandbox-extensions) walks the
same model, beginning with the simpler issuer/subject lifecycle.

Each actor independently selects `equipment: "selected"` (the default) or
`"unentitled"`; `required_entitlements` defaults to an empty list. Explicit null
for either field is refused. Required keys must be unique nonempty C-string
keys, at most 64 keys of 255 UTF-8 bytes each. The host checks boolean `true`
in the actor's static and live signing readbacks; equipment labels do not prove
effective authority. The controller's selected-runner requirement remains separate.

A phase may add `after_termination: {"actor_id": "issuer"}` when the source's
final scheduled visit precedes that phase. Unknown, self or non-prior source
dependencies return `invalid_termination_dependency` at the dependency's
`actor_id`. Null and unknown keys are refused. A satisfied dependency requires
an owned natural reap after source final activation; phase completion alone
cannot satisfy it. [The wire account](CONTRACT.md#contract-actor_evidence-gate)
describes retained reap, activation and reference-only gate observations.

Extension actions name their operands by reference. `issue` takes `family`
(`file`), `authority` (`read` or `read_write`), an absolute `target` and a new
`token_ref`; `transfer` takes an existing `token_ref`, a `recipient` actor and a
new `delivery_ref`; `consume` takes a `delivery_ref` the acting actor received
and a new `handle_ref`; `release` takes that `handle_ref`. References are
assigned once across tokens, deliveries and handles, used after their producer
in global action order, and owned: only the issuing actor transfers its token,
only the recipient consumes a delivery, only the consuming actor releases its
handle. An actor that issues, sends, receives, consumes or releases cannot also
`exec`; another actor may. Each capacity is a specimen-wide count.

| Corpus family | Meaning or refusal |
| --- | --- |
| `actors_with_policy`, `actors_with_probe_plan`, `actors_with_legacy_extensions`, `actors_without_phases`, `actors_empty_phases`, `actors_empty` | The actor form is one closed shape: actors with explicit phases and nothing from the singular form. |
| `actor_empty_id`, `actor_duplicate_id`, `actor_unknown_mode`, `actor_unapplied_with_policy`, `actor_apply_without_policy`, `actor_policy_format`, `actor_unknown_sandbox_field` | Actor identity and sandbox objects are closed and complete. |
| `actor_policy_augments_direct` | Named augments resolve in the controller per actor; direct XPC refuses them at the actor's own path. |
| `phase_without_actor`, `phase_unknown_actor`, `actor_without_phases`, `transfer_unknown_recipient` | Phases and transfers name declared actors, and every declared actor owns at least one phase. |
| `issue_unknown_family`, `issue_raw_class`, `issue_relative_target`, `issue_with_handle`, `transfer_without_delivery`, `consume_legacy_spelling` | Each operation takes exactly its operands; raw classes and relative targets are refused. |
| `transfer_unknown_token`, `transfer_before_issue`, `transfer_wrong_owner`, `consume_wrong_owner`, `consume_unknown_delivery`, `release_wrong_owner`, `release_repeated`, `issue_duplicate_reference`, `handle_duplicates_delivery`, `transfer_empty_token`, `actor_duplicate_step` | References follow their producers, keep their owners and are assigned once. |
| `exec_in_extension_actor`, `exec_in_other_actor` | The exec exclusion is per participating actor, not specimen-wide. |
| `self_transfer`, `repeated_consume` | A delivery to the sending actor and repeated consumption of one delivery are admitted with distinct references. |
| Actor, phase, issue, delivery, handle, release, action, identifier and target exact/over cases | The actor-form capacities and byte bounds apply inclusively. |

## The entry point matters

The controller accepts an authored specimen and resolves controller-owned
instructions before XPC delivery. The runner accepts the resulting specimen.
Both independently enforce the request marker.

| Example | Through the controller | Direct XPC |
| --- | --- | --- |
| `selector` | Resolves and records runner selection; creates the file. | Rejects `runner` as an unknown field. |
| `selector_typo` | Identifies the non-string entitlement at its array position. | Rejects the controller-only `runner` field. |
| `augment` | Resolves the named fragment, records policy provenance, and creates the file. | Refuses unresolved `policy.augments`. |
| `actor_policy_augments_direct` | Resolves each actor's named fragment and records a dossier per actor. | Refuses unresolved `actors[].sandbox.policy.augments`. |

Consistent diagnostics do not imply identical accepted fields at different
boundaries. The corpus records an expectation for each boundary explicitly.
Selection precedence is also meaning: a nested empty entitlement list overrides
the top-level list; a nested null is absent and permits fallback. Malformed
shadowed aliases are still refused. The selector unit tests pin that rule.

## What the implementation promises

[PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift) owns
the ordinary request types;
[PWRunnerExtension.swift](../runner/Sources/PWRunnerCore/PWRunnerExtension.swift)
owns shared actor intervention types; [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift)
owns actor inputs and [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift)
resolves actor operations and resource ownership. `CodingKeys` lists the allowed
fields; explicit decoding rejects unknown names, missing required fields and wrong types. Parameter
names remain open. No additional schema language participates in parsing.

[ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift) checks
meaning: applicable fields, supported attempt pairs and filter names, required
filter values, capture prerequisites, absolute exec targets and distinct step
IDs. The service and direct orchestrator both use this check before children.
Capacity checks run first so later diagnostics cannot echo unbounded input.

The operation string passed to `sandbox_check` remains an OS query. The
validator can return `unsupported_operation`; PW records that observation.
Known operation/filter pairs for which prediction is unavailable likewise
retain their explicit observation. Query and attempt targets need not match.
These are useful witness requests, even when one channel cannot answer.

By contrast, unknown attempt/filter names and non-null fields that cannot be
consumed refuse the whole specimen. PW does not run the recognized subset of
a misspelled plan. Internal classifiers retain defensive unsupported-result
handling for constructed or inconsistent inputs. In
[`buildStepResults`](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift),
an unsupported attempt uses `attempt.result_source: "synthetic"` with
`missing_reason: "attempt_not_supported"`, even when handed a completed worker
slot. This is not a public input acceptance rule; the defensive comparison
case is covered in
[ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift).

A successful decode establishes neither valid SBPL nor a successful sandbox
application or operation. A passing request contract cannot certify the host's
filesystem state, permissions, available services, or kernel behavior.

## Deciding whether the contract changes

A shipped-source edit changes the development identity, including an optional
addition or an implementation fix. A clean annotated release asserts the
release identity. Public admission always requires the exact value; the tool
does not infer compatibility from the shape or from the direction of a change.

For a syntax or meaning change, revise the definition and its verified example,
and review the shape golden. The derived surface table then identifies the
release in which that surface changed. A specimen author uses those rows to
review saved intent before asserting another build's contract.

Capacity changes still need independent documentation and evidence. A capacity
refusal never truncates a plan; automatically splitting one would change which
actions share a process. The caller decides whether to revise the plan or use
another build.

## Keeping the lesson honest

Run the examples through the production paths:

```sh
PW_TEST_OUT_DIR=tests/out/runs/request-lesson tests/run.sh --suite runner_outcome_bad_request --suite runner_unit --suite runner_c_worker_harness
```

Choose a fresh output name for another run. The dispatcher validates the app
and preserves artifacts; use `PW_APP_DIR` for an isolated signed build.

- The Swift tests read the shared corpus, run decoding, capacity and meaning
  checks, and compare exact structured refusals. They do not claim OS effects.
- The live controls render the same cases through both CLI and direct XPC.
  Accepted cases must create a file; refused cases must leave it absent, with
  no worker/validator records and no steps. A valid earlier step in the
  unsupported-attempt example detects accidental partial execution.
- The live controls retain the corpus, rendered requests, replies and effect
  observations. They verify that submitted files were not rewritten.
- Dedicated unit controls still cover every object depth, bounded diagnostics,
  selector precedence, nulls, and the exact capacity boundary. The teaching
  corpus selects instructive examples rather than replacing all coverage.

Maintenance is the existing types and validators, their described meanings,
and evidence-backed examples. Adding another schema representation would still
leave semantic validation and external effects to these tests. Add a teaching
case when a distinction becomes awkward to explain; a case that cannot state
its expected refusal or observation exposes an unresolved contract decision.
