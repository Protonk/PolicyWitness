# Requests: declarations and admission

This developer account follows a supplied specimen through controller preparation
and host admission. The examples teach the distinctions; the linked reference
regions hold the complete public statements, authored in the
[contract surface tree](contract/README.md). [RESPONSE](RESPONSE.md) follows the
returned evidence, and [CONTRACT](CONTRACT.md) connects commitments to their
implementation and support. The [user guide](PolicyWitness.md#specimen-format)
provides the user workflow.

A declaration is an instruction. The controller resolves its own selectors and
augments into a held request; the host independently admits the resulting form;
execution then depends on policy application, available resources and native
results. A matching build identity crosses the identity gate, not all those
boundaries. Inspect `build.contract` in the current packaged app's `--version`
envelope before asserting it in an authored request. [Build identification](RESPONSE.md#contract-identity-build)
and [identity derivation](CONTRACT.md#contract-identity-public) explain the
value and its scope.

Three executable publications have different roles:

| Publication | How to use it |
| --- | --- |
| `help` | Selected facts projected from executable interface definitions. Read the [interface inventory](../controller/interface/README.md) for omissions and unenumerated command tails. |
| `example` | A complete build-bound specimen that its build's `run` promises to admit. Emission itself performs no host admission and establishes no attempt result; see the [publication rule](#contract-request-specimen-emit_example) and [extracted example](#contract-request-specimen-example). |
| `test-input read --target PATH` | A build-bound controlled read request with positional target binding. The harness owns target conditions, observations and expectations; the publisher makes no general host-admission promise. See the [read-input rule](#contract-request-specimen-emit_test_input). |

For both specimen publishers, keep stdout only after exit 0; a failed write or
flush can leave complete-looking JSON that must be discarded. Neither supplies
an answer key. The [request corpus](../tests/fixtures/request_contract/examples.json)
separately owns creation inputs and expected refusals for the teaching sequence
below. The [example reading exercise](RESPONSE.md#read-the-published-example)
and [controlled-read exercise](RESPONSE.md#follow-one-saved-read-input) show how
published input relates to independent observations.

Begin with the observable create, then a one-change refusal, then phases,
extensions, actors and the controller/direct-XPC distinction. The
[request references](#request-reference) supply field and rule detail without
interrupting that progression.

## Start with an observable instruction

The `create` example supplies an SBPL policy, one sandbox query, and one file
creation attempt. Supply an absolute path to an absent file. This makes
acceptance observable outside the returned JSON.

From the repository root, using a current signed build:

```sh
PW=dist/PolicyWitness.app/Contents/MacOS/policy-witness
PW_EXAMPLE_DIR=$(mktemp -d /private/tmp/pw-grammar.XXXXXX)
tests/lib/python.sh tests/lib/request_examples.py create --effect "$PW_EXAMPLE_DIR/created" > "$PW_EXAMPLE_DIR/request.json" &&
cat "$PW_EXAMPLE_DIR/request.json" &&
"$PW" run "$PW_EXAMPLE_DIR/request.json" > "$PW_EXAMPLE_DIR/run.json" &&
test -f "$PW_EXAMPLE_DIR/created"
```

The corpus renderer asserts the selected app's identity. Its creation body is
independent test material, not an app-published input. Keep the directory to
inspect the submitted bytes and returned evidence.

Reading that request teaches three boundaries:

1. `contract` asserts the build contract the specimen was written for.
2. `(version 1)` inside `sbpl_source` belongs to SBPL, a nested language.
3. `sandbox_check` and `attempt` describe independent observations. A query
   result cannot establish the attempted operation's effect. The file check
   supplies that observation in this exercise.

The complete [specimen](#contract-request-specimen), [policy](#contract-policy-spec)
and [paired-probe](#contract-probes-step) statements follow the teaching path.
Use [RESPONSE](RESPONSE.md#read-the-run-from-the-outside-in) to distinguish the
returned completion result from this independent file observation.

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
if tests/lib/python.sh tests/lib/request_examples.py capture_typo --effect "$PW_EXAMPLE_DIR/refused" > "$PW_EXAMPLE_DIR/typo.json"; then
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

The [admission rule](#contract-request-specimen-admission) orders the broad
boundaries; [branch-local refusal precedence](RESPONSE.md#contract-refusals-request-compound_order)
describes how the reached branch chooses one failure. Correcting that failure
can expose another. The field reference distinguishes an omitted key, explicit
null, a default and a non-null value; do not generalize one field's convention
to every optional-looking input.

## Divide ordinary actions into phases

Render `phases_create` to use the same paired action inside an explicit phase.
`probe_plan` and `phases` are mutually exclusive non-null forms; supplying both
or neither produces `exclusive_plan_forms`. The simple form has one execution
phase named `main`, so it shares the same barriers and evidence rules.

The corpus's phase controls cover empty/duplicate IDs, unknown phase fields,
missing query or attempt, global duplicate step IDs, and the inclusive phase,
identity and total-action bounds. Refusal paths identify
`phases`, the phase index, `actions` and the action index. Capacity comes before
meaning and no child is launched on either refusal. The [phase declaration](#contract-actors-phase) states the ordering obligations;
[ARCHITECTURE](ARCHITECTURE.md#one-run-in-time) follows the
collection and release mechanism. The guide's [ordered-phase workflow](PolicyWitness.md#ordered-phases) shows a user-facing
sequence in which fresh planning leaves a later query unavailable after an unlink.

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

The [extension grammar and ownership rules](#contract-extensions-operation)
state what these declarations admit. [Extension custody](ARCHITECTURE.md#contract-extensions-custody)
follows bearer bytes and handles across the process boundaries;
[RESPONSE](RESPONSE.md#read-extension-events-and-resources) identifies the records
that can establish a reached native action or host transfer.

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
cannot satisfy it. [The returned gate account](RESPONSE.md#contract-actor_evidence-gate)
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

CLI `--runner-mode` is processed before the request file is read, then enters
the [selector precedence rule](#contract-request-options-precedence). Its
interface association links to the executable definition, but the interface
join does not mechanically compare the spelling in that rule's prose or its
free-text precedence obligation. The [interface account](../controller/interface/README.md#joins)
states the comparison limits.

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

### Test controls are declarations too

A request's `_test_overrides` block supplies two [executable substitutions](#contract-request-overrides)
for observing particular boundaries. The record's other eight controls are not
request data: they travel beside the request in an experimental submission and
are [refused in a request block](#contract-request-overrides-ordinary_refusal).
Admission and applicability still apply; for example, actor equipment
overrides have their own form and path rules.
An echoed override records an admitted value. It does not establish
that the controlled branch was reached or that the requested effect occurred;
read the corresponding [worker and phase observations](RESPONSE.md#read-process-and-publication-evidence).

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

## Checking the examples

Run the examples through the production paths:

```sh
PW_TEST_OUT_DIR=tests/out/runs/request-contract tests/run.sh --case runner_outcome_bad_request/accepted_input_contract --suite runner_unit --suite runner_c_worker_harness
```

Choose a fresh output name for another run. The dispatcher validates the app
and preserves artifacts; use `PW_APP_DIR` for an isolated signed build.

- The Swift tests read the shared corpus, run decoding, capacity and meaning
  checks, and compare exact structured refusals. They do not claim OS effects.
- The live controls render the same cases through both CLI and direct XPC.
  Accepted cases must create a file; refused cases must leave it absent, with
  no worker/validator records and no steps. A valid earlier step in the
  unsupported-attempt example detects accidental partial execution.
- The separate `witness_contract/test_input` case qualifies the selected app's
  read publication with independent target/content observations and a
  harness-authored unknown-field derivative. Its offline controls check the
  preparation boundary and exact correspondence diagnostics.
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

## Request reference

These regions render the complete statements from the surface tree. Field types,
key presence, nullability and subordinate obligations are read together;
[notation and support grades](CONTRACT.md#contract-notation) explain the display.

- [Specimens, publication, selectors and test controls](#contract-request).
- [Policy and augmentation declarations](#contract-policy).
- [Query and attempt operands](#contract-probes).
- [Actors, phase ownership and termination dependencies](#contract-actors).
- [Extension actions and reference ownership](#contract-extensions).
- [Standalone compiler-helper input](#standalone-compiler-helper-input).

<!-- BEGIN GENERATED CONTRACT request -->
<a id="contract-request"></a>
## Saved specimens and runner selection

A saved specimen describes one experiment. The controller reads its file once, resolves controller options and packaged augments, and serializes the held request delivered to the client. Direct XPC callers supply the host form themselves. The standalone compiler helper accepts its own policy input.

<a id="contract-request-specimen"></a>
### Specimen

Record `specimen`: `PWRunnerRunSpec`.

The host request objects have closed field sets. Parameter-map keys and caller labels are data within their own bounds.

- <a id="contract-request-specimen-contract"></a>**`contract`** (string; as defined below): Required non-null string asserting the exact public contract identity. The controller checks it before selector parsing and augmentation; the host checks it before other request fields. Obtain the current value from the packaged version envelope. `unbound` is refused. Uses [Exact admission identity](CONTRACT.md#contract-identity-public-contract).
- <a id="contract-request-specimen-specimen_id"></a>**`specimen_id`** (string; as defined below): Required non-null string caller label, echoed when it fits <!-- span limits.specimen_id.value_unit -->255 UTF-8 bytes<!-- /span -->. It may be empty. Its identity is independent of the worker PID or an actor ID.
- <a id="contract-request-specimen-run_kind"></a>**`run_kind`** (string; as defined below): Optional caller label, bounded by <!-- span limits.request_label.value_unit -->63 UTF-8 bytes<!-- /span -->. Omission and null have the same meaning; it selects no execution mode. Default: `null`.
- <a id="contract-request-specimen-policy"></a>**`policy`** ([Worker policy input](#contract-policy-spec); as defined below): Policy for the ordinary form. With no non-null `actors`, the policy object is required. In the actor form a non-null top-level policy is refused; each actor declares its own sandbox mode and policy.
- <a id="contract-request-specimen-probe_plan"></a>**`probe_plan`** (array of [Paired probe](#contract-probes-step); as defined below): Ordinary paired probes, including an empty array for apply-only execution. Exactly one of this field and `phases` must be non-null in the ordinary form. The host represents this plan as the `main` phase.
- <a id="contract-request-specimen-phases"></a>**`phases`** (array of [Phase declaration](#contract-actors-phase); as defined below): Ordered phase declarations. The ordinary form requires a nonempty array, forbids actor ownership, termination dependencies and extension actions, and uses one worker across its phases. The actor form requires phases and forbids a non-null `probe_plan`.
- <a id="contract-request-specimen-actors"></a>**`actors`** (array of [Actor declaration](#contract-actors-actor); as defined below): A non-null actor array selects the actor form; an empty array is refused. Each declared actor has its own fresh worker and at least one declared visit. Omission or null selects the ordinary form.
- <a id="contract-request-specimen-_test_overrides"></a>**`_test_overrides`** ([Execution overrides](#contract-request-overrides); as defined below): Optional block of two executable substitutions, `worker_executable_path` on the ordinary form and `actor_equipment_executable_paths` on the actor form. Each retains its stated scope and meaning; unknown members are refused, and so is a member that is one of the [eight controls of an experimental submission](#contract-request-overrides-ordinary_refusal). In an [experimental submission](#contract-request-overrides-experimental) the block must be absent, null or empty: the controls travel beside the request.

<a id="contract-request-specimen-hold"></a>
#### Hold and deliver the selected request

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at saved-file processing. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Uses [Specimen](CONTRACT.md#contract-identity-definitions-specimen), [Request](CONTRACT.md#contract-identity-definitions-request). Read and parse the request file once; gate its contract, parse selection, resolve named augments, strip controller selector fields and serialize once for client delivery. Preserve original and selected policy observations in the specimen dossier.

<a id="contract-request-specimen-admission"></a>
#### Admission order and effects

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at request decode and whole-request admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence). Check contract first, decode the selected plan form and closed nested objects, check capacities, then validate policy and plan meaning. On refusal apply the runner request-refusal consequence. A host may already exist to deliver that refusal.

Admission accepts or refuses the complete plan; it preserves declared action counts. Empty ordinary plans still compile and apply the policy.

<a id="contract-request-specimen-nulls"></a>
#### Null and omission

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at request decoding. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Absent field](CONTRACT.md#contract-identity-definitions-absent), [Null value](CONTRACT.md#contract-identity-definitions-null_value), [Extension operation](#contract-extensions-operation). Treat null as absent for each field whose entry says that null and omission are alike; any other null follows its field's stated presence rule. Refuse present null for actor equipment, actor required_entitlements, after_termination and actor_equipment_executable_paths. Retain presence of extension operands so an inapplicable operand is refused even when null.

<a id="contract-request-specimen-capacity"></a>
#### Bounded strings and action counts

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at pre-child admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Preserve complete UTF-8 strings at accepted bounds.

Native C-string inputs also refuse embedded NUL. A paired query and attempt consumes one action; an extension action consumes one action and contributes no query. Phase and actor counts do not multiply the total action capacity.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-request-specimen-capacity-ordinary_source"></a>Ordinary source bytes | Applies when (absent(`specimen.actors`) and present(`specimen.policy`) and present(`specimen.policy.sbpl_source`)). Requires utf8_length(`specimen.policy.sbpl_source`) ≤ `262,143 UTF-8 bytes` (`policy_source`) . |
| <a id="contract-request-specimen-capacity-actor_source"></a>Actor source bytes | Binding `a`: entry in `specimen.actors`. For each `a`. Applies when (present(`specimen.actors`) and present(`specimen.actors[a].sandbox.policy`) and present(`specimen.actors[a].sandbox.policy.sbpl_source`)). Requires utf8_length(`specimen.actors[a].sandbox.policy.sbpl_source`) ≤ `262,143 UTF-8 bytes` (`policy_source`) . |
| <a id="contract-request-specimen-capacity-flat_actions"></a>Flat action count | Applies when (absent(`specimen.actors`) and present(`specimen.probe_plan`)). Requires count(`specimen.probe_plan`) ≤ `256 items` (`probe_steps`) . |
| <a id="contract-request-specimen-capacity-phase_actions"></a>Phased action count | Binding `p`: entry in `specimen.phases`. Applies when present(`specimen.phases`). Requires sum_over(`p`, count(`specimen.phases[p].actions`)) ≤ `256 items` (`probe_steps`) . |
| <a id="contract-request-specimen-capacity-ordinary_phases"></a>Ordinary phase count | Applies when (absent(`specimen.actors`) and present(`specimen.phases`)). Requires count(`specimen.phases`) ≤ `8 items` (`phase_count`) . |
| <a id="contract-request-specimen-capacity-actor_phases"></a>Actor phase count | Applies when (present(`specimen.actors`) and present(`specimen.phases`)). Requires count(`specimen.phases`) ≤ `16 items` (`actor_phases`) . |
| <a id="contract-request-specimen-capacity-failure"></a>Refusal consequence | On failure, perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`). |

<a id="contract-request-specimen-apply_only"></a>
#### Apply-only specimen

This template applies a policy with no probe actions. Replace the assertion with the packaged version's `build.contract` before submission.

```json
{"contract":"<reported-contract>","specimen_id":"apply-only","policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default)"},"probe_plan":[]}
```

<a id="contract-request-specimen-emit_example"></a>
#### Emit the example specimen

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at CLI example dispatch. Entry: cli example. Recipient: cli caller. Reports: example specimen. set_value(`specimen.contract`, [Contract](RESPONSE.md#contract-identity-build-contract)). Uses [Contract](RESPONSE.md#contract-identity-build-contract), [Specimen](CONTRACT.md#contract-identity-definitions-specimen).

`policy-witness example` takes no argument and prints one specimen defined by the emitting build, followed by one newline. The output is a request document, not an envelope. Process exit 0 supplies the complete document. Exit 0 reports that every write and the flush to the process's standard output succeeded. A command launched with standard output closed writes to a discarding descriptor and also exits 0. The build guarantees that its own `run` admits that document; emission performs no admission and observes none. Every failure to emit is process exit 2: an argument, a build whose identity is empty or `unbound`, an example the contract gate refuses, or a failed write or flush. A reason is written to standard error when that stream accepts it; the exit status does not depend on it. On exit 2 discard standard output, even when it holds a complete document. The document's content, layout and labels carry no stability promise between builds. The command reads no file, starts no runner and reports nothing about a caller's document; `run` remains the only admission.

<a id="contract-request-specimen-emit_example-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Emit the example specimen](#contract-request-specimen-emit_example).** Emission parses the constant, inserts the binary's identity, passes the contract gate and uses the held request's serialization before any byte is written. An argument, an empty or unbound identity, a gate refusal and a failed write or flush each return the refusal that the command maps to exit 2. The emitted file reaches the controlled client as emitted, without its framing newline. On the selected app the command exits 0 with one JSON object and one newline carrying the app's identity, repeats it byte for byte, refuses every argument, and exits 2 when stdout has no reader whether or not stderr can be written; launched with stdout closed it exits 0 with an empty stderr; a build without an identity prints nothing. Context: Read the emitter and dispatch, the emitter's unit tests, the controlled orchestration test, the CLI integration tests against the selected app and isolated Cargo builds, and the live round-trip case with its checker. Evidence limit: Check read; no execution is credited. The exact request comparison runs under the test identity and ends at the client callback; on a signed app the live case observes the delivered length only. A gate refusal on a bound build has unit support and no built-app observation. No check observes the process's file reads; the isolated builds emit with no app, manifest or registry beside them. The stdout-closed row observes the exit status and an empty stderr; the discarding descriptor is not observed. Development runs of these checks exist and are disposable; release credit awaits an archived acceptance. [Evidence details](CONTRACT.md#contract-request-specimen-emit_example-support-details).

<a id="contract-request-specimen-emit_test_input"></a>
#### Publish a developer read input

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at CLI test-input dispatch. Entry: cli test input. Recipient: cli caller. Reports: test input specimen. set_value(`specimen.contract`, [Contract](RESPONSE.md#contract-identity-build-contract)). Uses [Contract](RESPONSE.md#contract-identity-build-contract), [Specimen](CONTRACT.md#contract-identity-definitions-specimen).

`policy-witness test-input read --target <absolute-path>` accepts exactly the
read selector followed by one target option. This is a build-bound developer
publisher. The target must be a nonempty absolute UTF-8 path without NUL.
The controller checks the positions it assigns in its embedded body: `contract`
is absent, and the one step holds the `$EFFECT` placeholder at its query and
attempt operands. It then inserts its binary's contract and preserves the
target verbatim at those operands. Other members are published as embedded.
Substitution is positional; literal `$EFFECT` text in caller input is data.
The document's content, layout and labels carry no stability promise between builds.

Process exit 0 establishes complete publication of one pretty JSON object,
one framing newline and a successful flush to the process's standard output;
it establishes neither admission nor execution nor an effect. A command
launched with standard output closed writes to a discarding descriptor and
also exits 0. Ordinary `run` independently admits or refuses the
input. Usage, target, empty or `unbound` identity, rendering, write and flush
failures exit 2. Discard stdout on failure even when it contains complete JSON.
A reason goes to stderr when writable; the exit status does not depend on it.

Emission reads no external file, launches no process, normalizes or inspects
no target and prepares no fixture. It makes no host-capacity or unconditional
admission promise. The harness owns fixture creation, mutation, cleanup,
independently authored expectations and observations.

<a id="contract-request-specimen-emit_test_input-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Publish a developer read input](#contract-request-specimen-emit_test_input).** The fixed read template binds the binary identity and caller target positionally, including literal marker text, quotes, backslashes and non-ASCII characters. A body that is not an object, carries a contract, has no step or a second step, or lacks the placeholder at an assigned operand or a container leading to it refuses before output. A body differing elsewhere is published with the same three assignments. Argument, target and identity refusals write nothing. Short writes complete the document, while partial-write and late-flush failures refuse. Selected-app controls check deterministic publication and exact request content, removed lesson dispatch, status 2 on invalid arguments and unreadable stdout, status independence from stderr closed at launch, and exit 0 with an empty stderr when stdout is closed at launch. Isolated Cargo builds check absent and supplied identities. Context: Read the embedded-template materializer, dispatch, constructed argument/template/writer controls and CLI integration assertions. Evidence limit: Check read; no execution is credited. Publication controls establish neither host admission nor native file effects. No control observes the absence of operating-system reads or process launches; those claims have source support. The closed-stream rows observe exit statuses, and an empty stderr where stdout is closed; the discarding descriptor is not observed. These checks do not promise admission for arbitrary target lengths or environments. [Evidence details](CONTRACT.md#contract-request-specimen-emit_test_input-support-details).

<a id="contract-request-specimen-read_input"></a>
#### Developer read body

This build's identity-free developer body is stated below. Insert the emitting
binary's contract at `contract` and the caller's target at
`probe_plan[0].sandbox_check.filter.value` and `probe_plan[0].attempt.target`.
These are positional assignments, not recursive marker expansion. The harness
compares this authored body with publication separately from native outcomes.

```json
{
  "specimen_id": "test-input",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)\n(allow default)"
  },
  "probe_plan": [
    {
      "step_id": "read-target",
      "sandbox_check": {
        "operation": "file-read-data",
        "filter": {
          "kind": "path",
          "value": "$EFFECT"
        }
      },
      "attempt": {
        "kind": "file",
        "action": "read_fresh",
        "target": "$EFFECT"
      }
    }
  ]
}
```

<a id="contract-request-specimen-read_input-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Developer read body](#contract-request-specimen-read_input).** The selected-app publication assertion independently states the read body's identity, policy, query, attempt and target binding. Context: Read the binding of the embedded body and the independently authored CLI publication expectation. Evidence limit: Check read; no execution or native outcome is credited. This body is build-specific public content, not a compatibility promise for later builds. [Evidence details](CONTRACT.md#contract-request-specimen-read_input-support-details).

<a id="contract-request-specimen-example"></a>
#### Emitted example

Uses [Cause](CONTRACT.md#contract-identity-definitions-cause).

These commands print the example and submit it unchanged:

```sh
policy-witness example > example.json
policy-witness run example.json
```

The printed document carries the emitting build's identity where this rendering shows `<reported-contract>`.

The ordinary phased document keeps one worker across two collection boundaries. `initial-reads` collects the first two queries before releasing their attempts; after that phase completes, `restricted-read` collects the final query before releasing its attempt. When policy application succeeds, both phases use that worker under the same applied policy. The ordinary reply reports observed application; it does not carry an application count.

The policy allows by default and denies data reads of the one file its specific rule names. Each step establishes something different:

- `read-hosts` asks about data reads of one file and opens that file. It supplies a native answer about the path and a witnessed open of it.
- `metadata-propernames-read-connectives` asks about metadata reads of the file the policy names and reads another file through a fresh descriptor. Its answer concerns a file its attempt does not read, so the answer predicts nothing about that read. The read is witnessed separately by its descriptor identity, byte count and bytes.
- `read-propernames` asks about data reads of the file the policy names and opens that file. It supplies a native answer about that path and a witnessed attempt to open it.

Where the three files exist and the caller can read them, the first two answers are `allow` and their attempts succeed; the third answer is `deny` and its open fails with errno 1 (`EPERM`). The run still finishes and its process exits 0: a finished run can hold a failed attempt. The deny answer and the failed open are separate observations. The reply records them side by side and states neither that they agree nor what caused the failure.

These results are observations on the build and machine that produced them, under those conditions. They are not commitments. The paths, labels, step count and order, the policy text with its `(with no-report)` modifier, the errno and every native result can differ between builds. The modifier asks the kernel not to report the refused open in the system log; it promises nothing about what a run logs.

```json
{
  "contract": "<reported-contract>",
  "phases": [
    {
      "actions": [
        {
          "attempt": {
            "action": "open_read",
            "kind": "file",
            "target": "/etc/hosts"
          },
          "sandbox_check": {
            "filter": {
              "kind": "path",
              "value": "/etc/hosts"
            },
            "operation": "file-read-data"
          },
          "step_id": "read-hosts"
        },
        {
          "attempt": {
            "action": "read_fresh",
            "kind": "file",
            "target": "/usr/share/dict/connectives"
          },
          "sandbox_check": {
            "filter": {
              "kind": "path",
              "value": "/usr/share/dict/propernames"
            },
            "operation": "file-read-metadata"
          },
          "step_id": "metadata-propernames-read-connectives"
        }
      ],
      "phase_id": "initial-reads"
    },
    {
      "actions": [
        {
          "attempt": {
            "action": "open_read",
            "kind": "file",
            "target": "/usr/share/dict/propernames"
          },
          "sandbox_check": {
            "filter": {
              "kind": "path",
              "value": "/usr/share/dict/propernames"
            },
            "operation": "file-read-data"
          },
          "step_id": "read-propernames"
        }
      ],
      "phase_id": "restricted-read"
    }
  ],
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default) (deny file-read-data (literal \"/usr/share/dict/propernames\") (with no-report))"
  },
  "specimen_id": "example"
}
```

<a id="contract-request-specimen-example-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Emitted example](#contract-request-specimen-example).** The rendering is the parsed constant, which must be a request object without an identity, test overrides, selection keys or unknown members. An edit to the constant is refused until regeneration and then moves the rendering, the request payload and the build identity. The live case requires the selected app's emitted document without its identity to equal this snapshot and to be an ordinary two-phase read-only workload with two actions then one: a data-read query and open of one target, a metadata query on a second target beside a fresh read of a third, and a data-read query and open of the second. It submits the emitted bytes unchanged and derives flat and single-applied-actor forms with the same actions and policy. Each submission independently requires admission, identity, digest, phase/action ownership and echo relationships; the actor also requires applied-once, selected-equipment and reaped-process observations. A diagnostic summary carries no equality assertion. Under observed target prerequisites it then requires, each as its own assertion, a captured process status of 0, a finished reply, each step's answer, each step's attempt, query-first order, and a fresh read whose descriptor identity, count and bytes equal the case's own observation of that target. Context: Read the constant, the extraction's constructed controls, the disposable-copy generation control and the live case with its checker and rejected controls. Evidence limit: Check read; no executed instance is credited here. Host admission and the native results are observed by the live case on a development build and one machine, under observed target prerequisites, and are not release evidence. The case compares no answer with its attempt and assigns no cause to the failed open. It cannot distinguish the first two steps' allow answers exchanged, samples its targets only before and after the run, and does not establish which object a native query consulted. Deeper request validity is established by execution, not by the extraction. The example's content carries no stability promise between builds. [Evidence details](CONTRACT.md#contract-request-specimen-example-support-details).

<a id="contract-request-specimen-duplicate_keys"></a>
#### Repeated members at each entry

For the paired repeated-member cases, CLI entry keeps the last contract, policy, probe step_id, attempt target, runner selector or runner.mode value, then holds the parsed object’s serialization. Direct host entry keeps the first contract, policy, probe step_id or attempt target value in either tested order. Direct-host runner and runner.mode cases refuse with unknown_field at ["runner"] in either order. These observations concern the listed raw-input pairs, their canonical neighbours and independent file effects on the observed platform.

<a id="contract-request-specimen-duplicate_keys-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Repeated members at each entry](#contract-request-specimen-duplicate_keys).** The controller parses raw JSON before holding its object; the direct-host cases use retained raw request bytes. Context: Static review of the cited producer and assertion branches. Evidence limit: The pinned matrix distinguishes both member orders and canonical neighbours for six fields at CLI and direct host entries. Its selected field/value pairs bound the observation. [Evidence details](CONTRACT.md#contract-request-specimen-duplicate_keys-disposition_support-details).

<a id="contract-request-specimen-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Specimen](#contract-request-specimen) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Context: Source inspection of the current implementation; no execution is credited. Evidence limit: Read the request fixture corpus loop, identity/unknown-field checks and actor parameter-capacity assertions. The apply-only template has source-level support; this owner credits no executed instance of that template. [Evidence details](CONTRACT.md#contract-request-specimen-support-details).

<a id="contract-request-options"></a>
### Controller selection options

Record `options`: `ControllerSelectionOptions`.

These fields extend the saved-file root at the controller entry. The controller strips all five before client delivery. A direct XPC request carrying them reaches the host unknown-field refusal.

- <a id="contract-request-options-runner"></a>**`runner`** ([Nested runner selector](#contract-request-selector) ∪ null): Optional nested selector object. Null means absent. Unknown nested keys are refused.
- <a id="contract-request-options-runner_id"></a>**`runner_id`** (string ∪ null): Legacy registry ID selector. Null means absent; a non-string value refuses even when nested `runner.id` would override it.
- <a id="contract-request-options-runner_service"></a>**`runner_service`** (string ∪ null): Legacy explicit Mach service selector. Null means absent; a non-string value refuses before nested precedence is applied.
- <a id="contract-request-options-required_entitlements"></a>**`required_entitlements`** (array of string ∪ null): Legacy list of selected-worker entitlement keys required to be boolean true. Null means absent. Values must be strings.
- <a id="contract-request-options-runner_mode"></a>**`runner_mode`** (string ∪ null): Legacy runner mode. Null means absent. The accepted values are `standard` and `byoxpc`. Admitted vocabulary: closed; displayed list: exhaustive: `"standard"`, `"byoxpc"`.

<a id="contract-request-options-precedence"></a>
#### Selector precedence

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at runner selector parsing. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Validate every supplied legacy value first, then let each non-null nested value replace its corresponding legacy value. An explicit nested empty entitlement list replaces the legacy list. Refuse with `conflicting_selector`: standard mode with an external selector, or byoxpc mode without an ID or service (at the root path), and a `--runner-mode` value that differs from the file's nested `runner.mode` (at `runner.mode`).

CLI `--runner-mode` is parsed before reading the request and is injected into its selector processing. `machme` is refused. Selection resolution and entitlement checks precede client invocation. A resolved target identifies the requested host service; actor equipment roles remain actor declarations.

<a id="contract-request-options-failure_order"></a>
#### Selection and augmentation failure order

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at request preparation. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Uses [Controller pre-invocation refusal](RESPONSE.md#contract-refusals-controller-consequence). Retain a target-resolution error while resolving augment dossiers. Select the target-resolution error first; otherwise select an augment refusal when present. Apply the controller pre-invocation consequence to the selected failure.

<a id="contract-request-options-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Controller selection options](#contract-request-options) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Context: Source inspection of the current implementation; no execution is credited. Evidence limit: Read parser and precedence controls; full registry selection and installed-equipment evidence belongs to installation and equipment. [Evidence details](CONTRACT.md#contract-request-options-support-details).

<a id="contract-request-selector"></a>
### Nested runner selector

Record `selector`: `ControllerRunnerSelector`.

- <a id="contract-request-selector-id"></a>**`id`** (string ∪ null): Registry ID for an installed external runner.
- <a id="contract-request-selector-service"></a>**`service`** (string ∪ null): Explicit external Mach service name.
- <a id="contract-request-selector-required_entitlements"></a>**`required_entitlements`** (array of string ∪ null): Selected-worker entitlement keys that must read back as boolean true for selection. This demand is separate from each actor's required_entitlements.
- <a id="contract-request-selector-mode"></a>**`mode`** (string ∪ null): Mode constraint applied to selection. With no mode or external selector, selection uses the packaged standard runner. Admitted vocabulary: closed; displayed list: exhaustive: `"standard"`, `"byoxpc"`.

<a id="contract-request-selector-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Nested runner selector](#contract-request-selector) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. [Evidence details](CONTRACT.md#contract-request-selector-support-details).

<a id="contract-request-overrides"></a>
### Execution overrides

Record `overrides`: `PWRunnerTestOverrides`.

This record holds ten controls. Two are request data, admitted in a request's `_test_overrides` block by every host, packaged hosts included: `worker_executable_path` and `actor_equipment_executable_paths`. The other eight are supplied only outside the request, through an [experimental submission](#contract-request-overrides-experimental); an ordinary submission [refuses them](#contract-request-overrides-ordinary_refusal). Their names identify test use; the decoder applies the documented grammar and capacities. Host admission of a positive fixture value can be followed by worker argument refusal before application.

- <a id="contract-request-overrides-worker_executable_path"></a>**`worker_executable_path`** (string?): Ordinary-worker executable override, bounded by <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. Actor-form admission refuses this singular override.
- <a id="contract-request-overrides-worker_timeout_ms"></a>**`worker_timeout_ms`** (integer?): Ordinary worker sentinel budget override in milliseconds. The host floors the supplied allowance at <!-- span limits.worker_timeout_override_floor.value_unit -->50 milliseconds<!-- /span -->; omission uses <!-- span limits.worker_sentinel_wait.value_unit -->120,000 milliseconds<!-- /span -->. Actor scheduling uses its fixed setup allowance and its fixed <!-- span limits.actor_execution_allowance.value_unit -->120,000 milliseconds<!-- /span --> execution allowance even when this field is supplied.
- <a id="contract-request-overrides-actor_equipment_executable_paths"></a>**`actor_equipment_executable_paths`** (object with string keys and string values?): Actor equipment role-to-path map. Present maps must be nonempty and use only `selected` and `unentitled` keys; actor admission requires absolute paths. The ordinary form refuses this map.
- <a id="contract-request-overrides-validator_executable_path"></a>**`validator_executable_path`** (string?): Validator executable override, bounded by <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. The validator remains a separate child and receives query work through its own channel.
- <a id="contract-request-overrides-validator_total_timeout_ms"></a>**`validator_total_timeout_ms`** (integer?): Cumulative validator collection budget override in milliseconds, spanning phases. Both schedulers clamp it to a minimum of <!-- span limits.validator_collection_override_floor.value_unit -->1 millisecond<!-- /span --> and their configured maximum: <!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span --> for the ordinary form and <!-- span limits.actor_collection_allowance.value_unit -->30,000 milliseconds<!-- /span --> for actors. Omission uses that maximum.
- <a id="contract-request-overrides-validator_io_timeout_ms"></a>**`validator_io_timeout_ms`** (integer?): Per-validator I/O timeout override in milliseconds. The host floors the proposed allowance at <!-- span limits.validator_io_override_floor.value_unit -->50 milliseconds<!-- /span -->; omission uses <!-- span limits.validator_io_wait.value_unit -->30,000 milliseconds<!-- /span -->. The remaining aggregate collection allowance can reduce the effective timeout below that floor.
- <a id="contract-request-overrides-worker_post_apply_hang_ms"></a>**`worker_post_apply_hang_ms`** (integer?): Positive fixture delay in milliseconds after all declared visits and actions, before terminal publication. The host forwards positive values; the worker argument parser accepts through <!-- span limits.worker_fixture_delay.value_unit -->60,000 milliseconds<!-- /span -->. A larger forwarded value causes worker argument refusal after launch. Zero and negative values are omitted by the host.
- <a id="contract-request-overrides-worker_post_apply_kill_signal"></a>**`worker_post_apply_kill_signal`** (integer?): Positive fixture signal requested after completed actions and before terminal publication, including an unapplied actor's visits. The host forwards positive values; the worker accepts signal numbers through 31. A larger value causes worker argument refusal after launch. Zero and negative values are omitted. A signal request can return without termination; final process observations decide the ending.
- <a id="contract-request-overrides-worker_pre_ready_hang_ms"></a>**`worker_pre_ready_hang_ms`** (integer?): Positive fixture delay in milliseconds after compilation and optional capture, before an apply worker's readiness byte and policy application. The host forwards positive values; the worker argument parser accepts through <!-- span limits.worker_fixture_delay.value_unit -->60,000 milliseconds<!-- /span -->. A larger value causes worker argument refusal after launch. Zero and negative values are omitted. The unapplied actor branch bypasses this compile/readiness path.
- <a id="contract-request-overrides-worker_kill_before_publish_slot"></a>**`worker_kill_before_publish_slot`** (integer?): Nonnegative zero-based slot in each worker's own plan. After that attempt returns and its result payload is written, the worker raises SIGKILL before publishing completion. Negative values are omitted. The worker argument parser requires an index below <!-- span limits.probe_steps.value_unit -->256 items<!-- /span -->; an index beyond the worker's actual plan has no reached action to trigger it.

<a id="contract-request-overrides-worker_timeout_ms-floor_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [worker_timeout_ms](#contract-request-overrides-worker_timeout_ms).** Calls the production helper to compare its floor to the limits inventory; independent below/equal/above cases retain the minimum and the uncapped larger override. Context: Planning helper and newly authored constructed assertions read. Evidence limit: No test execution is credited; the check establishes the planning value, not elapsed worker time. [Evidence details](CONTRACT.md#contract-request-overrides-worker_timeout_ms-floor_support-details).

<a id="contract-request-overrides-worker_timeout_ms-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [worker_timeout_ms](#contract-request-overrides-worker_timeout_ms).** Actor orchestration constructs the scheduler input with its fixed allowances. Context: Static review of the cited producer and assertion branches. Evidence limit: The paired control uses a 200 ms override and a 500 ms delay, checking an ordinary timeout and actor completion with a later dependent file read. [Evidence details](CONTRACT.md#contract-request-overrides-worker_timeout_ms-disposition_support-details).

<a id="contract-request-overrides-override_authority"></a>
#### Override admission and equipment ordering

Uses [Static worker binding](RESPONSE.md#contract-equipment-binding).

A caller whose connection passes host authorization can supply these controls. Actor equipment preparation checks the packaged inventory and both packaged role bindings before considering fixture override bindings. It retains the packaged and test_override rows with their respective implementation identities.

<a id="contract-request-overrides-experimental"></a>
#### Experimental submission

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at experimental submission decode and admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), [Admission order and effects](#contract-request-specimen-admission).

An experimental submission is a separate host call. It carries the request and, beside it, one JSON object of controls. Which call arrived decides the form; no request field selects it.

The controls object admits eight members: `worker_timeout_ms`, `worker_pre_ready_hang_ms`, `worker_post_apply_hang_ms`, `worker_post_apply_kill_signal`, `worker_kill_before_publish_slot`, `validator_executable_path`, `validator_io_timeout_ms` and `validator_total_timeout_ms`. Each has the type, scope and meaning of the field of the same name in this record.

The host decodes the request first, its contract before any other field. In that request, a `_test_overrides` block holding any member is refused with `inapplicable_field` at `_test_overrides`; a member whose value is null is a member. An absent, null or empty block is admitted. The host then decodes the controls object. An unknown member is refused with `unknown_field`; `worker_executable_path` and `actor_equipment_executable_paths` with `inapplicable_field`; a value of another type, or an integer outside the signed 64-bit range, with `type_mismatch`. Bytes that are not JSON are refused with `invalid_json`, a null with `missing_value` and any other value that is not an object with `type_mismatch`. A member whose value is null is absent. A refused control is located where the controls stand in the host's request: `_test_overrides` followed by the member name, or `_test_overrides` alone for the whole object.

The decoded controls take the block's place, and the request then passes the ordinary capacity and meaning admission. The validator path keeps its <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span --> bound, its embedded-NUL refusal and the withheld echo of a refused string, reported as `_test_overrides.validator_executable_path`. The reply's `test_overrides` mirrors the admitted controls object; with no member supplied it is an empty object, where an ordinary submission without a block has none.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-request-overrides-experimental-failure"></a>Refusal consequence | On failure, perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`). |

<a id="contract-request-overrides-experimental-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Experimental submission](#contract-request-overrides-experimental).** Constructed submissions compare the decoded record with the members given, a null member absent, and the rest of the request with the same request carrying no block; refuse each listed member, type and container fault at its stated code and location; refuse a block with a value, a null member or an unselected member, alone and beside a control; decode the contract and request before the controls; and, through the service, show one admission, the controls in the reply echo, an empty echo for an empty object, a consumed host on each refusal, and the path bound, NUL refusal and withheld echo for the validator control. The client session makes the experimental call once, with the request and controls bytes unchanged, only when controls were given. The selected-app case reads a request block refused through the controller, alone and beside a control, and through the runner client; an admitted empty block; a controls object delivered by the client; and a fractional control refused at the client. Context: Read the two submission calls, the decoder's three inputs, the shared capacity rule, the service unit tests, the client session controls and the selected-app checker. Evidence limit: Check read; no execution is credited. Unit submissions call the service object without XPC and observe orchestration through a substituted closure. The selected-app case submits one type fault through the client; it does not submit an unknown or unselected member, or bytes that are not JSON, there. Development runs of these checks exist and are disposable; release credit awaits an archived acceptance. [Evidence details](CONTRACT.md#contract-request-overrides-experimental-support-details).

<a id="contract-request-overrides-ordinary_refusal"></a>
#### Ordinary refusal of the experimental controls

Uses [Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence).

An ordinary submission carries none of the eight controls. Its `_test_overrides` block holding `worker_timeout_ms`, `worker_pre_ready_hang_ms`, `worker_post_apply_hang_ms`, `worker_post_apply_kill_signal`, `worker_kill_before_publish_slot`, `validator_executable_path`, `validator_io_timeout_ms` and `validator_total_timeout_ms` is refused with `inapplicable_field` at `_test_overrides` followed by that member's name. Presence decides: a member whose value is null, zero, negative or of another type is a member, and the refusal precedes the reading of any member's value. When the block holds several, the refusal names the first in the order just listed. An unknown member of the block is refused first, with `unknown_field`; the contract and the request's other fields are decoded before the block.

The refusal has the request refusal's consequence: no worker or validator starts, and the reply carries no `test_overrides`. `worker_executable_path` and `actor_equipment_executable_paths` remain request data, each on its own request form, and the controller's `run` delivers the block as written.

<a id="contract-request-overrides-ordinary_refusal-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Ordinary refusal of the experimental controls](#contract-request-overrides-ordinary_refusal).** The ordinary decoder refuses each of the eight members at its own name with an acting value, zero, a negative value, null and values of other types; names the first in the declared order when two are present; refuses a control beside the worker substitution and before that member's type fault; reports an unknown member, the contract and an earlier request field first; and still admits the two request-block members, an empty block and no block. Through the service's ordinary call each control, with a value and with null, consumes the host before admission or orchestration and yields a reply with no echo, while the worker substitution alone reaches orchestration. Controlled orchestration shows `run` delivering a block as written and recording no validator selection for it. The selected-app case submits each control in a request block through plain `run`, with an acting and an inert value, and through the runner client's ordinary call, a control beside the worker substitution and beside another control, and one control alone in the block of an actor-form request through plain `run`; each is refused at the stated member with no worker, no echo and an unchanged target, and the actor-form reply holds no actor record. The request corpus submits a fractional control through both entries. Context: Read the decoder's ordinary branch, the declared order, the service unit tests, the controlled orchestration test, the selected-app checker and the corpus loop. Evidence limit: Check read; no execution is credited. Unit submissions call the service object without XPC. The selected-app rows read the reply and an unchanged file; absence of a worker is the reply's own record, not an independent process observation. The actor form's block is submitted once, with one control and through plain `run` only. Development runs of these checks exist and are disposable; release credit awaits an archived acceptance. [Evidence details](CONTRACT.md#contract-request-overrides-ordinary_refusal-support-details).

<a id="contract-request-overrides-test_input_run"></a>
#### Run with test controls

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at CLI test-input run dispatch. Entry: cli test input run. Recipient: caller, report reader. Reports: run envelope. Uses [Hold and deliver the selected request](#contract-request-specimen-hold), [Experimental submission](#contract-request-overrides-experimental), [Controller pre-invocation refusal](RESPONSE.md#contract-refusals-controller-consequence).

`policy-witness test-input run [--timeout-ms N] [--runner-mode KIND] [CONTROL VALUE]... REQUEST` performs the `run` command's preparation, delivery, reply admission and result selection, and prints the same `kind: "run"` envelope with the same exit statuses. Every rule stated for the `cli run` entry applies to it. It differs in two respects.

It makes the experimental submission. The client receives the held request unchanged and a controls object with one member for each control given, and no member when none was given. The controller does not read the request's `_test_overrides` block for this purpose and refuses none: the host owns that refusal.

The dossier's validator record observes the file `--validator-executable-path` names, under the [rules for a selected file](RESPONSE.md#contract-dossier-collection): a value beyond <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span --> is neither echoed nor opened, an empty or relative value is recorded without a hash, and the packaged validator's own path needs no comparison. No command reads a request's validator key.

A control is spelled `--` and its member name with hyphens: `--worker-timeout-ms`, `--worker-pre-ready-hang-ms`, `--worker-post-apply-hang-ms`, `--worker-post-apply-kill-signal`, `--worker-kill-before-publish-slot`, `--validator-executable-path`, `--validator-io-timeout-ms` and `--validator-total-timeout-ms`. An integer control takes one signed 64-bit decimal and is delivered as written. The controller applies no control's range, so a value the host floors or the worker's argument grammar refuses is submitted and judged there. `--validator-executable-path` takes the next argument as UTF-8 text, whatever it is. A control without a value, a value of another form, a repeated control and any other flag are refused before the request is read, with no client invocation. `run` admits none of these flags.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-request-overrides-test_input_run-usage"></a>Refused arguments | On failure, perform([Controller pre-invocation refusal](RESPONSE.md#contract-refusals-controller-consequence), `envelope`). |

<a id="contract-request-overrides-test_input_run-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Run with test controls](#contract-request-overrides-test_input_run).** Each control is admitted only by this command and carries its member name; every signed 64-bit decimal, including values beyond each control's own range, reaches the controls object as written; values of another form, missing values, repeated controls and other flags are refused with the stated diagnostics before the app root is read and with no client call. Controlled orchestration delivers the same held request as `run` with the controls beside it, an empty object when none is given, and a request block as written; the validator record follows the control and not the request key. The case corpus holds the refusals and one admitted submission on the selected app. The selected-app case submits each control, compares the recorded command and delivered request with what it planned, and reads the echo apart from the host's or worker's own observation of the control. Context: Read the definitions, the form dispatch, the argument parser, the controls encoder, the client argument, the dossier selection, their unit tests, the case corpus and the selected-app checker. Evidence limit: Check read; no execution is credited. Controlled orchestration replaces the client with a recording closure. The selected-app case observes one value per control; it does not vary the actor form, external runners or every refusal through a submission. No check observes that usage refusals start no process other than through the envelope's null client capture. Development runs of these checks exist and are disposable; release credit awaits an archived acceptance. [Evidence details](CONTRACT.md#contract-request-overrides-test_input_run-support-details).

<a id="contract-request-overrides-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Execution overrides](#contract-request-overrides).** The actor path retains equipment preparation and fixed scheduler applicability separately. Context: Static review of the cited producer and assertion branches. Evidence limit: Excessive positive fixture values are sent through the selected CLI and checked at the downstream worker argument boundary. [Evidence details](CONTRACT.md#contract-request-overrides-disposition_support-details).

<a id="contract-request-overrides-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Execution overrides](#contract-request-overrides) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. [Evidence details](CONTRACT.md#contract-request-overrides-support-details).
<!-- END GENERATED CONTRACT request -->

<!-- BEGIN GENERATED CONTRACT policy -->
<a id="contract-policy"></a>
## Policy source, parameters and compilation

<a id="contract-policy-spec"></a>
### Worker policy input

Record `spec`: `PWRunnerPolicySpec`.

Each apply actor owns a separate policy. The host bounds the selected source string and parameter map before starting workers or validators.

- <a id="contract-policy-spec-format"></a>**`format`** (string; as defined below): Required non-null string. The accepted policy representation is `sbpl`; another value is refused before worker launch. A value longer than <!-- span limits.request_label.value_unit -->63 UTF-8 bytes<!-- /span --> is a capacity refusal, decided before the vocabulary check. Admitted vocabulary: closed; displayed list: exhaustive: `"sbpl"`.
- <a id="contract-policy-spec-sbpl_source"></a>**`sbpl_source`** (string; as defined below): Required string when applying a policy. An empty string reaches native compilation. The final source after augmentation fits <!-- span limits.policy_source.value_unit -->262,143 UTF-8 bytes<!-- /span -->, and embedded NUL is refused before child launch.
- <a id="contract-policy-spec-params"></a>**`params`** (object with string keys and string values; as defined below): Optional string-to-string compiler parameter map. Omission, null and an empty map produce no native parameter setup. Supplied names remain open data. At most <!-- span limits.policy_parameters.value_unit -->1,024 items<!-- /span --> fit each policy, with keys bounded by <!-- span limits.parameter_key.value_unit -->127 UTF-8 bytes<!-- /span --> and values by <!-- span limits.parameter_value.value_unit -->383 UTF-8 bytes<!-- /span -->; native strings must be NUL-free.
- <a id="contract-policy-spec-capture_compiled_profile"></a>**`capture_compiled_profile`** (boolean; as defined below): When true, request a compiled-profile receipt from the worker before application and require a valid capture_nonce. Omission, null and false leave capture unrequested. Default: `false`.
- <a id="contract-policy-spec-capture_nonce"></a>**`capture_nonce`** (string; as defined below): Required with enabled capture: exactly 32 lowercase hexadecimal characters encoding the caller's nonce. A non-null nonce with capture disabled is an inapplicable-field refusal. The host checks the nonce's form only and keeps no record of earlier nonces; uniqueness across requests is the caller's. Receipt publication and consistency checks belong to the compiled-profile surface. Required when `spec.capture_compiled_profile` = `true`. Present when `spec.capture_compiled_profile` = `true`.
- <a id="contract-policy-spec-augments"></a>**`augments`** (array of string; as defined below): Controller-resolved list of named packaged SBPL fragments. Omission, null and an empty list are no-ops. The controller strips the field before delivery. The host accepts the no-op forms and refuses a nonempty unresolved list.

<a id="contract-policy-spec-parameters"></a>
#### Prepare native compiler input

[Runner host](CONTRACT.md#contract-identity-definitions-host), [Worker](CONTRACT.md#contract-identity-definitions-worker) acts at policy preparation and compilation. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Sort parameter keys, transport their complete strings, create native parameters only for a nonempty map, and pass each key and value through sandbox_set_param before compiling the selected source. Report setup or compile failure at the observed native stage.

A supplied parameter is data for the SBPL compiler. The compiler decides how source expressions use it. Source text, selected parameter values and imported file bytes are distinct inputs.

<a id="contract-policy-spec-parameter_example"></a>
#### Parameter expressions

A source may combine a parameter with a literal suffix:

```scheme
(version 1)
(deny default)
(allow file-read* (literal (string-append (param "ROOT") "/hosts")))
```

`"params":{"ROOT":"/etc"}` supplies the value used by this expression. An unused `OPTIONAL` parameter and a referenced but missing `ROOT` exercise different compiler paths. Inspect the native compile record for the latter's outcome.

<a id="contract-policy-spec-parameter_evidence"></a>
#### Parameter example observations

Native compiler examples concern the helper invocation that produced the verdict. Worker examples use the consumed source and parameter values, then observe application and the requested fresh-file effects on concrete targets. Record the selected binaries, policy and platform with each native observation.

<a id="contract-policy-spec-parameter_evidence-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Parameter example observations](#contract-policy-spec-parameter_evidence).** Helper metadata and native verdict are retained together. Context: Static review of the cited producer and assertion branches. Evidence limit: Helper omitted/null/empty neighbours and worker ROOT twins have distinct oracles; worker target bytes and descriptor identity are checked independently. [Evidence details](CONTRACT.md#contract-policy-spec-parameter_evidence-disposition_support-details).

<a id="contract-policy-spec-compile_classification"></a>
#### Worker and helper compile classification

The worker treats a null compiled-profile pointer as failure and proceeds to capture and application with a non-null profile. The helper requires a profile and no native diagnostic for success, and frees the returned profile, parameters and diagnostic it owns. A simultaneous profile and diagnostic therefore has different classifications at these two boundaries. The helper branch has an injected native-return control; native occurrence of the worker combination remains unobserved.

<a id="contract-policy-spec-compile_classification-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Worker and helper compile classification](#contract-policy-spec-compile_classification).** Worker pointer acceptance and helper diagnostic-sensitive classification are separate producer rules. Context: Static review of the cited producer and assertion branches. Evidence limit: Injected helper returns check verdict and free counts. Worker simultaneous profile/diagnostic occurrence has source support only. [Evidence details](CONTRACT.md#contract-policy-spec-compile_classification-disposition_support-details).

<a id="contract-policy-spec-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Worker policy input](#contract-policy-spec) and its descendants.** The adjacent field meanings and operations follow the named implementation. Evidence limit: Decoder, meaning checks, parameter ordering, worker parameter snapshot/setup and compilation branches read. Native execution is not credited. [Evidence details](CONTRACT.md#contract-policy-spec-support-details).

<a id="contract-policy-augments"></a>
### Augment resolution

Augments select packaged source fragments from `Contents/Resources/Augments/<name>.sb`. Names are nonempty ASCII letters, digits or underscore. The resolver treats the fragment contents as source text.

<a id="contract-policy-augments-resolve"></a>
#### Resolve and append

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at saved-file policy normalization. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. For a nonempty augment list require a string source, validate every name, read the named resources in requested order and append a newline plus each fragment. Replace the policy source only after every requested read succeeds. Remove augments from the held policy before submission.

An empty string source is accepted at this normalization boundary. An unavailable resource produces `augment_unavailable` at the offending list element. Invalid names produce `invalid_value` at the offending list element. A wrong list or element type produces `type_mismatch`. The original file remains unchanged because resolution edits the held JSON value.

<a id="contract-policy-augments-actors"></a>
#### Resolve actor policies in request order

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at actor policy normalization. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Resolve each actor policy object in actor order and stop after the first augment refusal. Retain each visited actor's original and selected source in its dossier. Mode and policy applicability are judged later by host admission.

<a id="contract-policy-augments-exec_baseline"></a>
#### Packaged exec baseline

`exec_baseline` appends these source rules:

```scheme
(allow process-exec*)
(allow process-fork)
(allow file-read*)
```

The `file-read*` allowance is unconditional. Using this augment changes the selected policy's file-read authority and can mask the denial a file-read experiment intended to observe. Its documented derivation used macOS 14.8.3, build 23J220, and the repository's dynamic exec helper.

<a id="contract-policy-augments-augment_semantics"></a>
#### Augment evidence scope

The resolver validates all names before file access, reads fragments in requested order and appends each with a leading newline. Native behavior is scoped to the exact fragment bytes, base policy and macOS build observed. The packaged exec_baseline fragment includes broad file-read allowance; additional prerequisites and SBPL composition on another platform require their own observations.

<a id="contract-policy-augments-augment_semantics-disposition_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Augment evidence scope](#contract-policy-augments-augment_semantics).** Resolver validation, ordered reads and source append define the produced policy text. Evidence limit: Resolver correctness and selected native fragment observations have distinct scopes. [Evidence details](CONTRACT.md#contract-policy-augments-augment_semantics-disposition_support-details).

<a id="contract-policy-augments-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Augment resolution](#contract-policy-augments) and its descendants.** The adjacent field meanings and operations follow the named implementation. Context: Review of the named producer branches. Evidence limit: Read append/no-partial-replacement and actor-order controls. The packaged baseline source was read; its historical derivation is inherited evidence. [Evidence details](CONTRACT.md#contract-policy-augments-support-details).
<!-- END GENERATED CONTRACT policy -->

<!-- BEGIN GENERATED CONTRACT probes -->
<a id="contract-probes"></a>
## Paired probes and attempted operations

<a id="contract-probes-step"></a>
### Paired probe

Record `step`: `PWRunnerProbeStep`.

One paired probe contributes one action and at most one eligible validator query.

- <a id="contract-probes-step-step_id"></a>**`step_id`** (string; as defined below): Required non-null string. Caller label associating a query with its attempt and result. It is unique across all actions and fits <!-- span limits.step_id.value_unit -->63 UTF-8 bytes<!-- /span --> and is NUL-free. Uniqueness is under canonical Unicode equivalence: identifiers that differ only in normalization are duplicates. Actor plans require it to be nonempty; ordinary plans currently accept a unique empty value.
- <a id="contract-probes-step-sandbox_check"></a>**`sandbox_check`** ([Sandbox query](#contract-probes-query); as defined below): Required non-null object. Requested prediction operation and filter. Admission validates this request independently from the attempt.
- <a id="contract-probes-step-attempt"></a>**`attempt`** ([Attempt request](#contract-probes-attempt); as defined below): Required non-null object. Requested native operation.

<a id="contract-probes-step-read_hosts"></a>
#### Read-hosts pair

Uses [Emitted example](#contract-request-specimen-example).

The first step of the emitted example pairs a path query with an open-read attempt. The open-read operation's success establishes its open boundary. A `read_fresh` attempt supplies the separate read-count, content and close observations described by the step-result surface.

```json
{
  "attempt": {
    "action": "open_read",
    "kind": "file",
    "target": "/etc/hosts"
  },
  "sandbox_check": {
    "filter": {
      "kind": "path",
      "value": "/etc/hosts"
    },
    "operation": "file-read-data"
  },
  "step_id": "read-hosts"
}
```

<a id="contract-probes-step-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Paired probe](#contract-probes-step) and its descendants.** The adjacent field meanings and operations follow the named implementation. Evidence limit: Grammar and uniqueness branches read. The read-hosts pair is the first step of the controller's example, extracted from its constant; this owner claims no live result. [Evidence details](CONTRACT.md#contract-probes-step-support-details).

<a id="contract-probes-query"></a>
### Sandbox query

Record `query`: `PWRunnerSandboxCheck`.

- <a id="contract-probes-query-operation"></a>**`operation`** (string; as defined below): Required non-null operation string. It is nonempty after whitespace trimming for admission, bounded by <!-- span limits.query_operation.value_unit -->127 UTF-8 bytes<!-- /span --> and NUL-free, and passes unchanged to prediction planning. Accepted strings remain open to native operation support.
- <a id="contract-probes-query-filter"></a>**`filter`** ([Sandbox filter](#contract-probes-filter); as defined below): Closed filter kind with its applicable optional value.

<a id="contract-probes-query-eligibility"></a>
#### Admission and eligibility

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at query admission and planning. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Excluded prediction pairs](#contract-probes-query-excluded). Check operation trimming first, filter kind next, and value applicability and trimming last; stop at the first refusal. For an admitted query, withhold native prediction when its path fails host realpath planning or its operation/filter pair is excluded; report prediction_unavailable while leaving the attempt eligible.

A path created by the attempt can be unresolved at planning and resolve in later host diagnostics. These observations have separate times and owners.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-probes-query-eligibility-trimmed"></a>Whitespace-trimmed query inputs | The operation is nonempty after trimming whitespace and newlines. For a known non-none filter, its supplied value is also nonempty after that trimming. |
| <a id="contract-probes-query-eligibility-known_filter"></a>Known filter | Requires `query.filter.kind` ∈ [`"none"`, `"path"`, `"global_name"`, `"local_name"`, `"iokit_registry_entry_class"`, `"iokit_user_client_class"`, `"sysctl_name"`]. |
| <a id="contract-probes-query-eligibility-value_presence"></a>Applicable value | Requires (implies(`query.filter.kind` = `"none"`, absent(`query.filter.value`)) and implies(`query.filter.kind` ≠ `"none"`, present(`query.filter.value`))). |
| <a id="contract-probes-query-eligibility-failure"></a>Whole-request refusal | On failure, [perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`)]. |

<a id="contract-probes-query-excluded"></a>
#### Excluded prediction pairs

A query satisfying the condition below is excluded: it is admitted, receives no validator query and reports prediction_unavailable. The condition is not an admission requirement. The exclusion belongs to the pair. Other operations using the same filter follow their own eligibility and native result.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-probes-query-excluded-pairs"></a>Exact excluded pairs | Requires ((`query.operation` = `"iokit-open-service"` and `query.filter.kind` = `"iokit_registry_entry_class"`) or (`query.operation` = `"iokit-open-user-client"` and `query.filter.kind` = `"iokit_user_client_class"`) or (`query.operation` = `"sysctl-read"` and `query.filter.kind` = `"sysctl_name"`) or (`query.operation` = `"mach-lookup"` and `query.filter.kind` = `"local_name"`)). |

<a id="contract-probes-query-exclusion_evidence"></a>
#### Prediction-exclusion evidence scope

The IOKit and sysctl exclusions retain the dated 2026-05-29 exploration of filter IDs 1–200. The local Mach mapping remains conservatively unresolved. Each native filter observation belongs to its recorded operation, target and platform; the finite exploration bounds the basis for the current exclusion table.

<a id="contract-probes-query-exclusion_evidence-disposition_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Prediction-exclusion evidence scope](#contract-probes-query-exclusion_evidence).** The table preserves the dated IOKit/sysctl exploration and conservative local-Mach choice. Evidence limit: This owner reads the recorded basis and current table; it adds no native rerun credit. [Evidence details](CONTRACT.md#contract-probes-query-exclusion_evidence-disposition_support-details).

<a id="contract-probes-query-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Sandbox query](#contract-probes-query) and its descendants.** The adjacent field meanings and operations follow the named implementation. [Evidence details](CONTRACT.md#contract-probes-query-support-details).

<a id="contract-probes-filter"></a>
### Sandbox filter

Record `filter`: `PWRunnerSandboxFilter`.

- <a id="contract-probes-filter-kind"></a>**`kind`** (string; as defined below): Required non-null string. Filter representation admitted by the host. A value longer than <!-- span limits.probe_plan_label.value_unit -->127 UTF-8 bytes<!-- /span --> is a capacity refusal, decided before the vocabulary check. Admitted vocabulary: closed; displayed list: exhaustive: `"none"`, `"path"`, `"global_name"`, `"local_name"`, `"iokit_registry_entry_class"`, `"iokit_user_client_class"`, `"sysctl_name"`.
- <a id="contract-probes-filter-value"></a>**`value`** (string; as defined below): For `none`, require absence or null. Every other kind requires a string nonempty after whitespace trimming, bounded by <!-- span limits.query_filter_value.value_unit -->511 UTF-8 bytes<!-- /span --> and NUL-free. The original string is retained and passed through unchanged.

<a id="contract-probes-filter-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Sandbox filter](#contract-probes-filter) and its descendants.** The adjacent field meanings and operations follow the named implementation. [Evidence details](CONTRACT.md#contract-probes-filter-support-details).

<a id="contract-probes-attempt"></a>
### Attempt request

Record `attempt`: `PWRunnerAttempt`.

- <a id="contract-probes-attempt-kind"></a>**`kind`** (string; as defined below): Required non-null string. Native operation family selected with action. A value longer than <!-- span limits.probe_plan_label.value_unit -->127 UTF-8 bytes<!-- /span --> is a capacity refusal, decided before the vocabulary check. Admitted vocabulary: closed; displayed list: exhaustive: `"file"`, `"mach_lookup"`, `"sysctl"`, `"exec"`.
- <a id="contract-probes-attempt-action"></a>**`action`** (string; as defined below): Required non-null string. Closed action within its family, listed in the operation table below. An unsupported pair refuses the complete request before children. A value longer than <!-- span limits.probe_plan_label.value_unit -->127 UTF-8 bytes<!-- /span --> is a capacity refusal, decided before the vocabulary check.
- <a id="contract-probes-attempt-target"></a>**`target`** (string; as defined below): Required non-null string. Operation target, bounded by <!-- span limits.attempt_target.value_unit -->511 UTF-8 bytes<!-- /span --> and NUL-free. Exec requires an absolute path. Other admitted targets retain their supplied native-operation meaning.
- <a id="contract-probes-attempt-args"></a>**`args`** (array of string; as defined below): Exec-only argument strings appended after target as argv[0]. Omission and null mean an empty list. A supplied array on another kind, including an empty array, is refused. At most <!-- span limits.exec_arguments.value_unit -->15 items<!-- /span --> are admitted, each NUL-free and bounded by <!-- span limits.exec_argument.value_unit -->127 UTF-8 bytes<!-- /span -->. Default: `[]`.

<a id="contract-probes-attempt-operations"></a>
#### Native operations

The worker runs the selected operation after policy application in an apply worker, or after the unapplied actor's setup:

| Kind / action | Native operation and operation-specific consequence |
| --- | --- |
| `file / open_read` | `open(O_RDONLY)`; on an accepted descriptor, request a one-byte read and close. Aggregate success is the successful open; read and close results are discarded. |
| `file / open_write` | `open(O_WRONLY \| O_TRUNC)`; on an accepted descriptor, request a one-byte `x` write and close. Aggregate success is the successful open; write and close results are discarded. |
| `file / create` | `open(O_WRONLY \| O_CREAT, 0600)` then close. Creation mode is subject to umask. An existing file is opened without truncation or exclusive creation. |
| `file / read_fresh` | Fresh `open(O_RDONLY \| O_CLOEXEC)`, `fstat`, one read bounded by <!-- span limits.fresh_read_bytes.value_unit -->64 bytes<!-- /span -->, then close. Record each boundary and read bytes; aggregate failure selects stat, read or close failure after a successful open. |
| `file / write_fresh` | Fresh `open(O_WRONLY \| O_CLOEXEC)` of an existing target, opened `fstat`, `ftruncate(0)`, truncated `fstat`, one-byte `x` write after successful truncation, written `fstat`, then close. Preserve the first failure in the aggregate. |
| `file / create_fresh` | `lstat` before a fresh exclusive `open(O_WRONLY \| O_CLOEXEC \| O_CREAT \| O_EXCL, 0600)`, opened `fstat`, one-byte `x` write, written `fstat`, then close. Pre-open `lstat` is an independent observation. Preserve the first operation failure in the aggregate. |
| `file / unlink` | `unlink(target)` and its return/errno. |
| `file / access` | `access(target, R_OK)` and its return/errno. This is an access-check observation. |
| `mach_lookup / bootstrap_look_up` | Obtain the task bootstrap port and call `bootstrap_look_up` for the supplied name; release the returned service port on success. |
| `sysctl / read` | One `sysctlbyname` call with a <!-- span limits.sysctl_read_bytes.value_unit -->4,096 bytes<!-- /span --> buffer acquired after application. Report the call's result and errno; discard value bytes and the returned length. |
| `exec / spawn` | Prepare per-attempt child resources, call `posix_spawn` for the absolute target with the requested argv, then collect child and cleanup observations. |

A short fresh write records its native count and fails the aggregate while retaining zero native errno when the write returned a short nonnegative count. A fresh file descriptor belongs to that attempt and is closed before its result is published.

<a id="contract-probes-attempt-execute"></a>
#### Execute a declared operation

[Worker](CONTRACT.md#contract-identity-definitions-worker) acts at released action slot. Entry: worker action. Recipient: caller, report reader. Reports: runner reply. Uses [Observation](CONTRACT.md#contract-identity-definitions-observation), [Effect](CONTRACT.md#contract-identity-definitions-effect). Dispatch only the admitted kind/action pair, record the operation's native observations and publish its slot after the attempt. Preserve operation-specific success meaning alongside the aggregate result.

<a id="contract-probes-attempt-execute-disposition_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Execute a declared operation](#contract-probes-attempt-execute).** Native operation details and aggregate return/errno projection have their own report fields. Evidence limit: This owner is source-read. Selected fresh-file, descriptor, sysctl-buffer and exec-cleanup executions need their exact operation owners. [Evidence details](CONTRACT.md#contract-probes-attempt-execute-disposition_support-details).

<a id="contract-probes-attempt-exec"></a>
#### Exec setup and child inputs

[Worker](CONTRACT.md#contract-identity-definitions-worker) acts at released exec action after setup. Entry: worker action. Recipient: caller, report reader. Reports: runner reply. After application or an actor's unapplied declaration, acquire stdout/stderr pipes and spawn actions for this released attempt, release them on setup failure and at completion, and report the failing setup call when spawning was prevented. Spawn with target as argv[0], an empty environment, /dev/null stdin, captured stdout/stderr, close-on-exec descriptor policy and a new process group.

A successful spawn supplies a child PID even if the child later exits nonzero. The child collection, termination request and owned reap remain separate observations. The production per-child collection allowance is <!-- span limits.exec_child_wait.value_unit -->10,000 milliseconds<!-- /span --> after successful spawn, capped by the remaining per-worker active-plan allowance of <!-- span limits.exec_attempt_budget.value_unit -->115,000 milliseconds<!-- /span -->. The active-plan clock starts before worker setup, includes setup and intervening work, and excludes acknowledged release waits and accepted actor parked-activation waits. Both allowances use continuous time, including system sleep. Exhausted allowance can refuse a later spawn or stop collection; clock faults retain their own boundary. Blocking native calls can outlast the allowance.

<a id="contract-probes-attempt-extension_exec"></a>
#### Extension participant restriction

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at actor admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when (present(`request.actors`) and present(`request.phases`)). perform([Exclude exec in participating actors](#contract-extensions-operation-exec), `request`). Uses [Extension operation](#contract-extensions-operation).

<a id="contract-probes-attempt-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Attempt request](#contract-probes-attempt) and its descendants.** The adjacent field meanings and operations follow the named implementation. [Evidence details](CONTRACT.md#contract-probes-attempt-support-details).
<!-- END GENERATED CONTRACT probes -->

<!-- BEGIN GENERATED CONTRACT actors -->
<a id="contract-actors"></a>
## Actors and phases

<a id="contract-actors-actor"></a>
### Actor declaration

Record `actor`: `PWRunnerActor`.

A specimen admits at most <!-- span limits.actors.value_unit -->8 items<!-- /span -->.

- <a id="contract-actors-actor-actor_id"></a>**`actor_id`** (string; as defined below): Required non-null string: a nonempty specimen-local actor identifier, unique across actors and bounded by <!-- span limits.actor_id.value_unit -->63 UTF-8 bytes<!-- /span -->. Native transport also requires NUL-free bytes. Uniqueness, and the match of a phase's or dependency's actor reference, are under canonical Unicode equivalence: identifiers that differ only in normalization are the same actor.
- <a id="contract-actors-actor-sandbox"></a>**`sandbox`** ([Actor sandbox declaration](#contract-actors-sandbox); as defined below): Required non-null object: the actor's explicit apply or unapplied declaration; application assessment is reported separately from this request.
- <a id="contract-actors-actor-equipment"></a>**`equipment`** (string; as defined below): Equipment role: `selected` uses the selected runner worker; `unentitled` uses the packaged unentitled worker. Omission selects `selected`; present null is refused. Default: `"selected"`. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`.
- <a id="contract-actors-actor-required_entitlements"></a>**`required_entitlements`** (array of string; as defined below): Static and live read-back demand for boolean-true entitlement keys on this actor's executable. Omission supplies an empty list; present null is refused. Default: `[]`.

<a id="contract-actors-actor-normalize"></a>
#### Normalize actors before launch

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at actor-plan admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Binding `a`: entry in `request.actors`. Binding `b`: entry in `request.actors`. Binding `p`: entry in `request.phases`. Association restriction for `b`: `request.actors[b].actor_id` = `request.actors[a].actor_id`. Association restriction for `p`: `request.phases[p].actor_id` = `request.actors[a].actor_id`. Applies when (present(`request.actors`) and present(`request.phases`)). Uses [Actor equipment selection](RESPONSE.md#contract-equipment-actor), [Static worker binding](RESPONSE.md#contract-equipment-binding). Resolve the admitted actor and resource references once into the plan indexes used for execution.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actors-actor-normalize-identity"></a>Actor identity | For each `a`. Requires (`request.actors[a].actor_id` ≠ `""` and matches(`b`) = `1` and utf8_length(`request.actors[a].actor_id`) ≤ `63 UTF-8 bytes` (`actor_id`) and not (contains(`request.actors[a].actor_id`, `"\u0000"`))). |
| <a id="contract-actors-actor-normalize-role"></a>Known equipment role | For each `a`. Requires implies(present(`request.actors[a].equipment`), `request.actors[a].equipment` ∈ [`"selected"`, `"unentitled"`]). |
| <a id="contract-actors-actor-normalize-visits"></a>At least one declared visit | For each `a`. Requires matches(`p`) > `0`. |
| <a id="contract-actors-actor-normalize-sandbox"></a>Sandbox declaration | For each `a`. Requires (`request.actors[a].sandbox.mode` ∈ [`"apply"`, `"unapplied"`] and implies(`request.actors[a].sandbox.mode` = `"apply"`, present(`request.actors[a].sandbox.policy`)) and implies(`request.actors[a].sandbox.mode` = `"unapplied"`, absent(`request.actors[a].sandbox.policy`))). |
| <a id="contract-actors-actor-normalize-entitlement_count"></a>Entitlement list capacity | For each `a`. Requires count(`request.actors[a].required_entitlements`) ≤ `64 items` (`actor_required_entitlements`) . |
| <a id="contract-actors-actor-normalize-entitlement_identity"></a>Required entitlement identity | Binding `e`: entry in `request.actors[a].required_entitlements`. Binding `f`: entry in `request.actors[a].required_entitlements`. Association restriction for `f`: `request.actors[a].required_entitlements[f]` = `request.actors[a].required_entitlements[e]`. For each `a`, `e`. Requires (`request.actors[a].required_entitlements[e]` ≠ `""` and matches(`f`) = `1` and utf8_length(`request.actors[a].required_entitlements[e]`) ≤ `255 UTF-8 bytes` (`actor_entitlement_key`) and not (contains(`request.actors[a].required_entitlements[e]`, `"\u0000"`))). |
| <a id="contract-actors-actor-normalize-failure"></a>Refusal consequence | On failure, perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`). |

<a id="contract-actors-actor-fresh"></a>
#### Fresh process and retained policy

[Runner host](CONTRACT.md#contract-identity-definitions-host), [Worker](CONTRACT.md#contract-identity-definitions-worker) acts at actor process lifecycle. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when present(`request.actors`). Uses [Application assessment](RESPONSE.md#contract-actor_evidence-application). Launch one fresh worker for each actor. An apply worker compiles and applies its own declared policy once before its visits; an unapplied worker publishes that declaration and executes under the restrictions already inherited by its process. Keep that worker for its successive visits.

<a id="contract-actors-actor-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Actor declaration](#contract-actors-actor) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Evidence limit: Normalization concerns admitted declarations; worker setup and application observations have separate owners. [Evidence details](CONTRACT.md#contract-actors-actor-support-details).

<a id="contract-actors-sandbox"></a>
### Actor sandbox declaration

Record `sandbox`: `PWRunnerActorSandbox`.

- <a id="contract-actors-sandbox-mode"></a>**`mode`** (string; as defined below): `apply` requires a policy and asks the worker to compile/apply it; `unapplied` requires policy absence or null and records the inherited process restrictions as its starting condition. Admitted vocabulary: closed; displayed list: exhaustive: `"apply"`, `"unapplied"`.
- <a id="contract-actors-sandbox-policy"></a>**`policy`** ([Worker policy input](#contract-policy-spec); as defined below): Required non-null policy for `apply`; a non-null policy is refused for `unapplied`. Each apply policy has its own source, parameters, augmentation and capture request. Required when `sandbox.mode` = `"apply"`. Present when `sandbox.mode` = `"apply"`.

<a id="contract-actors-sandbox-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Actor sandbox declaration](#contract-actors-sandbox) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. [Evidence details](CONTRACT.md#contract-actors-sandbox-support-details).

<a id="contract-actors-phase"></a>
### Phase declaration

Record `phase`: `PWRunnerPhase`.

- <a id="contract-actors-phase-phase_id"></a>**`phase_id`** (string; as defined below): Required non-null string: a nonempty identifier unique across the specimen's phases, under canonical Unicode equivalence, and bounded by <!-- span limits.phase_id.value_unit -->63 UTF-8 bytes<!-- /span --> and NUL-free.
- <a id="contract-actors-phase-actor_id"></a>**`actor_id`** (string; as defined below): Required known actor owner in the actor form. The ordinary form requires absence or null.
- <a id="contract-actors-phase-actions"></a>**`actions`** (array of [Phase action variants](#contract-actors-action); as defined below): Required non-null array of actions in declaration order; it may be empty. Ordinary phases contain paired probes. Actor phases may also contain extension actions. Action identifiers are unique across the whole specimen.
- <a id="contract-actors-phase-after_termination"></a>**`after_termination`** ([Termination dependency](#contract-actors-after_termination); as defined below): Optional owned-termination dependency in the actor form. Absence supplies no dependency; present null is refused. The ordinary form refuses a supplied dependency.

**phase_id.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actors-phase-phase_id-identity"></a>Required phase identity | Requires (`phase.phase_id` ≠ `""` and utf8_length(`phase.phase_id`) ≤ `63 UTF-8 bytes` (`phase_id`) and not (contains(`phase.phase_id`, `"\u0000"`))). |

<a id="contract-actors-phase-order"></a>
#### Collect, release and advance

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at phase scheduler. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Phase](CONTRACT.md#contract-identity-definitions-phase), [Prediction](CONTRACT.md#contract-identity-definitions-prediction). Close the active phase's eligible prediction collection before releasing its actions; run those actions in declaration order. In ordinary execution begin the next phase's collection only after the previous phase completes. In the actor form walk the declared schedule serially while it remains uncancelled and has execution allowance, activating one actor at a time while others remain parked. Skip unavailable actors or visits. After a failed active visit establish that actor's reap before any further activation; unresolved termination cancels the remaining schedule, including after a wait error that leaves the actor unreaped. Once the reap is confirmed, an arrival or completion timeout cancels for exhausted execution allowance and a wait error cancels for lost ownership. A schedule entry that would begin with no execution allowance left cancels the remaining schedule for exhausted allowance with neither collection nor a reap; once the schedule clock can no longer supply a remaining value, a schedule entry, a release or a completion wait counts as having none left, while an arrival wait spends the allowance that remained in bounded sleeps. A failed evaluated termination dependency also cancels the remaining schedule. Other available actors may continue after the failed actor is reaped.

<a id="contract-actors-phase-order-disposition_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Collect, release and advance](#contract-actors-phase-order).** The ordering claim requires a complete chain and a unique matching native prediction for the owned worker. Evidence limit: The source owner describes eligibility and the worker's wait for the release store. No owner in this tree credits integrated collection/release or mutation execution; witness_contract/order_barrier_mutations is the control routed for changes to the wait, release store or eligibility rule. [Evidence details](CONTRACT.md#contract-actors-phase-order-disposition_support-details).

<a id="contract-actors-phase-order-schedule_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Collect, release and advance](#contract-actors-phase-order).** The ordinary driver requires prior phase completion. The actor scheduler skips unavailable visits and gates continuation after a failed active visit on confirmed reap and cancellation conditions; checks distinguish failed setup and death before completion from continuing actors. An injected ECHILD wait error leaves the actor unreaped and cancels as unresolved_termination; an injected wait error of another kind, followed by a reap, cancels as ownership_lost; neither activates the later visit. Context: Read the two driver loops and the failed-setup, active-actor-death and wait-error assertions, including retained absent completion and the next actor's independent process-absence observation. Evidence limit: This check-read account credits assertion scope, not a newly executed trial. The execution-allowance label for a wait or entry whose clock can no longer supply a remaining value is source-read; no test injects a failing clock into a schedule entry or an arrival or completion wait. No owner in this tree credits integrated collection/release or mutation execution; witness_contract/order_barrier_mutations is the control routed for changes to the wait, release store or eligibility rule. [Evidence details](CONTRACT.md#contract-actors-phase-order-schedule_support-details).

<a id="contract-actors-phase-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Phase declaration](#contract-actors-phase) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Evidence limit: Source support here pins decoded grammar and normalized order. Runtime collection/release evidence belongs to the phase and lifecycle producer rules. [Evidence details](CONTRACT.md#contract-actors-phase-support-details).

<a id="contract-actors-after_termination"></a>
### Termination dependency

Record `after_termination`: `PWRunnerAfterTermination`.

The declaration names a source actor, while the gate reports the host's owned observation of its ending.

- <a id="contract-actors-after_termination-actor_id"></a>**`actor_id`** (string; as defined below): Required non-null string naming the known actor whose final declared phase occurs earlier than the dependent phase. It must differ from the dependent phase's actor.

<a id="contract-actors-after_termination-gate"></a>
#### Validate and evaluate the dependency

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at actor admission and phase activation. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when present(`request.actors`). Uses [Termination dependency](RESPONSE.md#contract-actor_evidence-gate). Before activating the dependent actor or collecting its predictions, evaluate the owned natural-reap gate. A failed evaluated gate cancels every remaining scheduled phase.

<a id="contract-actors-after_termination-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Termination dependency](#contract-actors-after_termination) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Evidence limit: Admission source read; the referenced actor-evidence rule owns the runtime gate and global cancellation consequence. [Evidence details](CONTRACT.md#contract-actors-after_termination-support-details).

<a id="contract-actors-after_termination-declaration"></a>
#### Admit the declared dependency

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at actor plan admission before child launch. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.actors`. Binding `q`: entry in `request.phases`. Association restriction for `a`: `request.actors[a].actor_id` = `request.phases[p].after_termination.actor_id`. Association restriction for `q`: `request.phases[q].actor_id` = `request.phases[p].after_termination.actor_id`. For each `p`. Applies when (present(`request.actors`) and present(`request.phases`)).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actors-after_termination-declaration-source"></a>Source actor and visit | Applies when present(`request.phases[p].after_termination`). Requires (matches(`a`) = `1` and `request.phases[p].after_termination.actor_id` ≠ `request.phases[p].actor_id` and matches(`q`) > `0`). |
| <a id="contract-actors-after_termination-declaration-earlier"></a>Every source visit precedes this phase | For each `p`, `q`. Applies when (present(`request.phases[p].after_termination`) and `request.phases[q].actor_id` = `request.phases[p].after_termination.actor_id`). Requires `q` < `p`. |
| <a id="contract-actors-after_termination-declaration-failure"></a>Refusal consequence | On failure, perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`). |

<a id="contract-actors-after_termination-declaration-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Admit the declared dependency](#contract-actors-after_termination-declaration).** The dependency names a different declared actor whose final declared phase precedes the dependent phase. [Evidence details](CONTRACT.md#contract-actors-after_termination-declaration-support-details).

<a id="contract-actors-action"></a>
### Phase action variants

Record `action`: `PWRunnerPhaseAction`.

An action is one JSON object in the phase actions array. The decoder chooses an extension action when the `extension` key is present; otherwise it decodes a paired probe. A present null extension therefore selects extension decoding and fails its required object.

| Alternative | Record |
| --- | --- |
| `probe` | [Paired probe](#contract-probes-step) |
| `extensionAction` | [Extension action](#contract-extensions-action) |

<a id="contract-actors-action-identity"></a>
#### Action identity

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at plan admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Paired probe](#contract-probes-step), [Extension action](#contract-extensions-action).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actors-action-identity-flat"></a>Flat probe identities | Binding `i`: entry in `request.probe_plan`. Binding `j`: entry in `request.probe_plan`. Association restriction for `j`: `request.probe_plan[j].step_id` = `request.probe_plan[i].step_id`. For each `i`. Applies when (absent(`request.actors`) and present(`request.probe_plan`)). Requires matches(`j`) = `1`. |
| <a id="contract-actors-action-identity-probe"></a>Phased probe identities | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: ((is_variant(`request.phases[q].actions[b]`, `"probe"`) and `variant(request.phases[q].actions[b], 'probe').step_id` = `variant(request.phases[p].actions[a], 'probe').step_id`) or (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and `variant(request.phases[q].actions[b], 'extensionAction').step_id` = `variant(request.phases[p].actions[a], 'probe').step_id`)). For each `p`, `a`. Applies when (present(`request.phases`) and is_variant(`request.phases[p].actions[a]`, `"probe"`)). Requires (sum_over(`q`, matches(`b`)) = `1` and implies(present(`request.actors`), `variant(request.phases[p].actions[a], 'probe').step_id` ≠ `""`)). |
| <a id="contract-actors-action-identity-extension"></a>Phased extension identities | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: ((is_variant(`request.phases[q].actions[b]`, `"probe"`) and `variant(request.phases[q].actions[b], 'probe').step_id` = `variant(request.phases[p].actions[a], 'extensionAction').step_id`) or (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and `variant(request.phases[q].actions[b], 'extensionAction').step_id` = `variant(request.phases[p].actions[a], 'extensionAction').step_id`)). For each `p`, `a`. Applies when (present(`request.phases`) and is_variant(`request.phases[p].actions[a]`, `"extensionAction"`)). Requires (sum_over(`q`, matches(`b`)) = `1` and implies(present(`request.actors`), `variant(request.phases[p].actions[a], 'extensionAction').step_id` ≠ `""`)). |
| <a id="contract-actors-action-identity-failure"></a>Refusal consequence | On failure, perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`). |

<a id="contract-actors-action-empty_id"></a>
#### Form-specific action identifiers

Ordinary-form action identifiers may be empty. Actor-form action identifiers must be nonempty so declared actions can be resolved in the actor schedule. UTF-8 capacity, NUL exclusion, uniqueness and membership are separate requirements at their owning admission boundary.

<a id="contract-actors-action-empty_id-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Form-specific action identifiers](#contract-actors-action-empty_id).** Actor normalization rejects an empty action step_id before constructing its slot map; ordinary meaning admission tests uniqueness without a nonempty condition. A signed-CLI ordinary request whose one step_id is empty finishes with its validator record associated and query_first, as its neighbour with a nonempty identifier does, and two empty identifiers are refused as duplicates. An actor-form request with one empty action step_id is refused with empty_step_id at that action's path through the CLI and direct XPC, with no actor launch and no file from its preceding action; its neighbour with a nonempty identifier runs. The reader corpus supports only the reply readers' acceptance of an ordinary empty identifier and refusal of an actor one. Context: Read the cited admission branches, the signed-CLI and direct-XPC controls and the corpus rows. Evidence limit: Check reading; no run is credited. The ordinary pair submits one read of an existing file under an allow-default policy. The corpus emits separate ordinary-empty and actor-empty declaration neighbours through reporting admission; it is constructed reader evidence and establishes nothing about request admission. [Evidence details](CONTRACT.md#contract-actors-action-empty_id-disposition_support-details).

<a id="contract-actors-action-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Phase action variants](#contract-actors-action) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. [Evidence details](CONTRACT.md#contract-actors-action-support-details).
<!-- END GENERATED CONTRACT actors -->

<!-- BEGIN GENERATED CONTRACT extensions -->
<a id="contract-extensions"></a>
## Extension actions and authority custody

The actor form carries explicit issue, transfer, consume and release actions. A reference names a declared resource within this specimen; native results, custody acknowledgements and later file observations each have their own producing boundary.

<a id="contract-extensions-action"></a>
### Extension action

Record `action`: `PWRunnerExtensionAction`.

- <a id="contract-extensions-action-step_id"></a>**`step_id`** (string; as defined below): Required non-null string: a unique nonempty identifier across all specimen actions, bounded by <!-- span limits.step_id.value_unit -->63 UTF-8 bytes<!-- /span -->. Uniqueness is under canonical Unicode equivalence: identifiers that differ only in normalization are duplicates.
- <a id="contract-extensions-action-extension"></a>**`extension`** ([Extension operation](#contract-extensions-operation); as defined below): Closed extension operation for the active actor. Its presence selects extension-action decoding; a null object is refused.

<a id="contract-extensions-action-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Extension action](#contract-extensions-action) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-extensions-action-support-details).

<a id="contract-extensions-operation"></a>
### Extension operation

Record `operation`: `PWRunnerExtensionOperation`.

References are nonempty, NUL-free and bounded by <!-- span limits.extension_reference.value_unit -->63 UTF-8 bytes<!-- /span -->.

- <a id="contract-extensions-operation-operation"></a>**`operation`** (string; as defined below): Required non-null string. Select the operation and its exact applicable operands. Admitted vocabulary: closed; displayed list: exhaustive: `"issue"`, `"transfer"`, `"consume"`, `"release"`.
- <a id="contract-extensions-operation-token_ref"></a>**`token_ref`** (string; as defined below): Required new token reference for issue; required previously assigned token owned by the active actor for transfer. Required when `operation.operation` ∈ [`"issue"`, `"transfer"`]. Present when `operation.operation` ∈ [`"issue"`, `"transfer"`].
- <a id="contract-extensions-operation-handle_ref"></a>**`handle_ref`** (string; as defined below): Required new handle reference for consume; required previously assigned handle owned by the active actor for release. Required when `operation.operation` ∈ [`"consume"`, `"release"`]. Present when `operation.operation` ∈ [`"consume"`, `"release"`].
- <a id="contract-extensions-operation-family"></a>**`family`** (string; as defined below): Required `file` for issue. Required when `operation.operation` = `"issue"`. Present when `operation.operation` = `"issue"`.
- <a id="contract-extensions-operation-target"></a>**`target`** (string; as defined below): Required absolute file or directory path for issue, bounded by <!-- span limits.extension_issue_target.value_unit -->1,023 UTF-8 bytes<!-- /span -->. The exact submitted bytes reach native issuance. Required when `operation.operation` = `"issue"`. Present when `operation.operation` = `"issue"`.
- <a id="contract-extensions-operation-authority"></a>**`authority`** (string; as defined below): Required `read` or `read_write` for issue, selecting `com.apple.app-sandbox.read` or `com.apple.app-sandbox.read-write`. Required when `operation.operation` = `"issue"`. Present when `operation.operation` = `"issue"`.
- <a id="contract-extensions-operation-recipient"></a>**`recipient`** (string; as defined below): Required known actor ID for transfer; may name the active actor itself. Required when `operation.operation` = `"transfer"`. Present when `operation.operation` = `"transfer"`.
- <a id="contract-extensions-operation-delivery_ref"></a>**`delivery_ref`** (string; as defined below): Required new delivery reference for transfer; required previously assigned delivery owned by the active recipient for consume. Required when `operation.operation` ∈ [`"transfer"`, `"consume"`]. Present when `operation.operation` ∈ [`"transfer"`, `"consume"`].

<a id="contract-extensions-operation-grammar"></a>
#### Operation grammar

| Operation | Required operands | Producing actor and consequence |
| --- | --- | --- |
| `issue` | `family`, `target`, `authority`, `token_ref` | Active actor calls native file issuance once with class selected by authority, exact target and flags zero; assigns the declared token resource. |
| `transfer` | `token_ref`, `recipient`, `delivery_ref` | Token-owning actor publishes a host request for one assigned recipient slot; assigns the delivery resource. |
| `consume` | `delivery_ref`, `handle_ref` | Recipient actor calls native consume on its usable delivered token; assigns the handle resource. |
| `release` | `handle_ref` | Consuming actor calls native release for its candidate handle. |

Each other operand must be absent. A required null operand is missing for this grammar; an extraneous null operand is inapplicable.

<a id="contract-extensions-operation-references"></a>
#### Resolve references and ownership

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at whole actor-plan admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when (present(`request.actors`) and present(`request.phases`)). Construct the token, delivery and handle assignments and their execution indexes once from the admitted ordered resource declarations.

The same token may be transferred to multiple recipients or repeatedly to one recipient using distinct delivery references. A delivery may be consumed repeatedly using distinct handle references. Syntactic ordering establishes which resource is requested; the later resource record establishes what was observed.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-operation-references-unique_issue"></a>Unique issue assignment | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and ((`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"issue"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.token_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.token_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.delivery_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.token_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"consume"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.token_ref`))). For each `p`, `a`. Applies when (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"issue"`). Requires sum_over(`q`, matches(`b`)) = `1`. |
| <a id="contract-extensions-operation-references-unique_transfer"></a>Unique transfer assignment | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and ((`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"issue"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.token_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.delivery_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.delivery_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.delivery_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"consume"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.delivery_ref`))). For each `p`, `a`. Applies when (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"transfer"`). Requires sum_over(`q`, matches(`b`)) = `1`. |
| <a id="contract-extensions-operation-references-unique_consume"></a>Unique consume assignment | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and ((`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"issue"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.token_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.delivery_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"consume"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref`))). For each `p`, `a`. Applies when (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"consume"`). Requires sum_over(`q`, matches(`b`)) = `1`. |
| <a id="contract-extensions-operation-references-producer_transfer"></a>Earlier owned producer for transfer | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and `variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"issue"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.token_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.token_ref` and (`q` < `p` or (`q` = `p` and `b` < `a`)) and `request.phases[q].actor_id` = `request.phases[p].actor_id`). For each `p`, `a`. Applies when (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"transfer"`). Requires sum_over(`q`, matches(`b`)) = `1`. |
| <a id="contract-extensions-operation-references-producer_consume"></a>Earlier owned producer for consume | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and `variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.delivery_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.delivery_ref` and (`q` < `p` or (`q` = `p` and `b` < `a`)) and `variant(request.phases[q].actions[b], 'extensionAction').extension.recipient` = `request.phases[p].actor_id`). For each `p`, `a`. Applies when (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"consume"`). Requires sum_over(`q`, matches(`b`)) = `1`. |
| <a id="contract-extensions-operation-references-producer_release"></a>Earlier owned producer for release | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and `variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"consume"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref` and (`q` < `p` or (`q` = `p` and `b` < `a`)) and `request.phases[q].actor_id` = `request.phases[p].actor_id`). For each `p`, `a`. Applies when (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"release"`). Requires sum_over(`q`, matches(`b`)) = `1`. |
| <a id="contract-extensions-operation-references-single_release"></a>At most one handle release | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (is_variant(`request.phases[q].actions[b]`, `"extensionAction"`) and `variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"release"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref`). For each `p`, `a`. Applies when (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"consume"`). Requires sum_over(`q`, matches(`b`)) ≤ `1`. |
| <a id="contract-extensions-operation-references-failure"></a>Refusal consequence | On failure, perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`). |

<a id="contract-extensions-operation-capacity"></a>
#### Bound the declared resource plan

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at pre-child admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Applies when (present(`request.actors`) and present(`request.phases`)). Uses [Specimen](#contract-request-specimen).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-operation-capacity-issue"></a>Issue count | Association restriction for `a`: (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"issue"`). Requires sum_over(`p`, matches(`a`)) ≤ `32 items` (`actor_issues`) . |
| <a id="contract-extensions-operation-capacity-transfer"></a>Transfer count | Association restriction for `a`: (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"transfer"`). Requires sum_over(`p`, matches(`a`)) ≤ `64 items` (`actor_deliveries`) . |
| <a id="contract-extensions-operation-capacity-consume"></a>Consume count | Association restriction for `a`: (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"consume"`). Requires sum_over(`p`, matches(`a`)) ≤ `64 items` (`actor_handles`) . |
| <a id="contract-extensions-operation-capacity-release"></a>Release count | Association restriction for `a`: (is_variant(`request.phases[p].actions[a]`, `"extensionAction"`) and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"release"`). Requires sum_over(`p`, matches(`a`)) ≤ `64 items` (`actor_releases`) . |
| <a id="contract-extensions-operation-capacity-failure"></a>Refusal consequence | On failure, perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`). |

<a id="contract-extensions-operation-exec"></a>
#### Exclude exec in participating actors

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at actor-plan admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Binding `a`: entry in `request.actors`. Binding `p`: entry in `request.phases`. Binding `x`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `y`: entry in `request.phases[q].actions`. Association restriction for `x`: (is_variant(`request.phases[p].actions[x]`, `"extensionAction"`) and (`request.phases[p].actor_id` = `request.actors[a].actor_id` or (`variant(request.phases[p].actions[x], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[p].actions[x], 'extensionAction').extension.recipient` = `request.actors[a].actor_id`))). Association restriction for `y`: (`request.phases[q].actor_id` = `request.actors[a].actor_id` and is_variant(`request.phases[q].actions[y]`, `"probe"`) and `variant(request.phases[q].actions[y], 'probe').attempt.kind` = `"exec"`). Applies when (present(`request.actors`) and present(`request.phases`)). Uses [Attempt request](#contract-probes-attempt).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-operation-exec-participants"></a>Participant exec exclusion | For each `a`. Requires implies(sum_over(`p`, matches(`x`)) > `0`, sum_over(`q`, matches(`y`)) = `0`). |
| <a id="contract-extensions-operation-exec-failure"></a>Refusal consequence | On failure, perform([Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence), `request`). |

<a id="contract-extensions-operation-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Extension operation](#contract-extensions-operation) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-extensions-operation-support-details).

<a id="contract-extensions-examples"></a>
### Extension experiments

These schedules keep declaration, native action, delivered payload and fresh access observations separate.

<a id="contract-extensions-examples-before_during_after"></a>
#### Before, during and after consumption

Declare actors `issuer` and `reader`. Choose the issuer's equipment and sandbox policy to exercise issuance authority, and a reader policy whose baseline denies the chosen path. Use an exact absolute target:

| Phase owner | Actions in declaration order |
| --- | --- |
| `reader` | `read_fresh` before receiving authority |
| `issuer` | issue `token_ref: "t"`, family `file`, authority `read`; transfer `t` to `reader` as `delivery_ref: "d"` |
| `reader` | consume `d` as `handle_ref: "h"`; `read_fresh`; release `h`; `read_fresh` again |

The first read supplies the baseline. The middle read supplies access during this handle's lifetime. The last read supplies a later access observation after the native release call. Compare their actual file identity and content observations. A non-null issue result, delivered bytes, consume result and release result each remain visible even when a read fails.

<a id="contract-extensions-examples-redelegation"></a>
#### Three-actor redelegation

Declare `A`, `B` and `C` with their own sandbox and equipment choices. Read the target freshly in `B` and `C` to establish their baselines. `A` issues a token and transfers it to `B`; `B` consumes that delivery, performs a fresh read, then issues its own token and transfers that token to `C`. `C` consumes its delivery and reads freshly.

The second issuance is `B`'s own native action under its then-current state. Keep the two issue events, two custody/delivery chains, two candidate handles and the readers' file observations distinct. `read_write` may name an absolute directory target; fresh writes or exclusive creation within that directory expose their own file effects.

<a id="contract-extensions-examples-disposition_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Extension experiments](#contract-extensions-examples).** Reply assembly retains extension events, transfer observations and resource accounts by their declared actions. Evidence limit: Native examples require their concrete input and selected-platform observations. [Evidence details](CONTRACT.md#contract-extensions-examples-disposition_support-details).

<a id="contract-extensions-examples-execution_support"></a>
**Support: [executed](CONTRACT.md#contract-support-grades) for [Extension experiments](#contract-extensions-examples).** Concrete before/during/after access, the extracted guide JSON example, credited three-actor redelegation and separate directory authority retain native calls, custody/transfer observations and independently identified file effects. Context: Passed signed-CLI cases with their recorded policies, equipment, paths and macOS 26.7.1/25G241 arm64 environment; inspected native results, principal credit, file observations and owned cleanup. Evidence limit: The before/during/after instance splits reader actions across visits. Redelegation includes B/C control-path reads and the retained policies. Directory writes and exclusive creation form a separate experiment. The extracted guide JSON and the guide's full shell workflows have separate execution scopes. [Evidence details](CONTRACT.md#contract-extensions-examples-execution_support-details).

<a id="contract-extensions-examples-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Extension experiments](#contract-extensions-examples) and its descendants.** Admission supports these resource chains and native operations. Context: Admission and native-operation source for the teaching schedules. Evidence limit: Native examples are scoped to their recorded policies, equipment, targets and platform. Before/during/after access was observed with an unapplied unentitled issuer and an applied selected subject, with reader actions split across visits. Three-actor redelegation was observed with the retained B/C policies and added control-path reads. Directory read-write authority was exercised separately through fresh writes and exclusive creation. Release results and later access observations retain their individual meanings. [Evidence details](CONTRACT.md#contract-extensions-examples-support-details).
<!-- END GENERATED CONTRACT extensions -->

## Standalone compiler-helper input

The compiler helper is a separate entry point. Its policy request does not ask
for a sandboxed worker or a probe plan. The [helper response](RESPONSE.md#read-the-compiler-helper)
records that compiler invocation; it cannot establish specimen execution.

<!-- BEGIN GENERATED CONTRACT helper -->
<a id="contract-policy-helper_request"></a>
### Standalone compiler-helper request

Record `helper_request`: `rust.CheckRequest`.

`sbpl-check --request <path>` reads a policy request file; `--request -` reads stdin. This decoder selects the policy object and ignores other root fields. It accepts input without a public-contract assertion.

- <a id="contract-policy-helper_request-policy"></a>**`policy`** ([Compiler-helper policy](#contract-policy-helper_policy); as defined below): Required compiler-helper policy object.

<a id="contract-policy-helper_request-read"></a>
#### Read helper input

[Compiler helper](CONTRACT.md#contract-identity-definitions-helper) acts at standalone argument, read and JSON boundary. Entry: standalone helper, controller helper stdin. Recipient: caller, report reader. Reports: helper envelope, stderr. Use the helper policy decoder. Usage errors, input-read errors and JSON/decode errors exit 2 and report on stderr. Successfully decoded requests proceed to helper admission and produce an envelope. An envelope, or the usage text that `--help` prints, that cannot be written to standard output and flushed is exit 2 with one line on stderr.

<a id="contract-policy-helper_request-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Standalone compiler-helper request](#contract-policy-helper_request) and its descendants.** The adjacent field meanings and operations follow the named implementation. [Evidence details](CONTRACT.md#contract-policy-helper_request-support-details).

<a id="contract-policy-helper_policy"></a>
### Compiler-helper policy

Record `helper_policy` locations: `helper_request.policy`.

The helper decoder ignores policy members outside this record, including capture and augment requests. Controller fallback supplies the already normalized policy source.

- <a id="contract-policy-helper_policy-format"></a>**`format`** (string; as defined below): Required non-null string; an absent key, null or another type is a decode error, reported on stderr with exit 2 and no envelope. Require `sbpl` at helper admission. Admitted vocabulary: closed; displayed list: exhaustive: `"sbpl"`.
- <a id="contract-policy-helper_policy-sbpl_source"></a>**`sbpl_source`** (string; as defined below): Required at helper admission: omission and null are refused alike as a missing source, and another type is a decode error, reported on stderr with exit 2 and no envelope. Allow an empty string for the native compiler. Bound its UTF-8 bytes by <!-- span limits.helper_source.value_unit -->4,194,304 bytes<!-- /span -->, then require a NUL-free C string.
- <a id="contract-policy-helper_policy-params"></a>**`params`** (object with string keys and string values; as defined below): Optional string map. Null and absence mean no map; an empty map is present for reporting but needs no native parameter object. Reject embedded NUL in each key and value before inventory or native calls.

<a id="contract-policy-helper_policy-admit"></a>
#### Helper admission order

[Compiler helper](CONTRACT.md#contract-identity-definitions-helper) acts at pre-inventory admission. Entry: standalone helper, controller helper stdin. Recipient: caller, report reader. Reports: helper envelope. Binding `k`: entry in `helper_policy.params`. Association restriction for `k`: (contains(`k`, `"\u0000"`) or contains(`helper_policy.params[k]`, `"\u0000"`)). Select the first matching case in the listed order. Stop at the first admission refusal. After format, source-presence and source-extent checks pass, construct the source C string and then parameter key/value C strings in map order; a failed conversion prevents later conversions and retains its diagnostic.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-policy-helper_policy-admit-format"></a>1. Unsupported format | `helper_policy.format` ≠ `"sbpl"` | [set_value(`helper_envelope.result.ok`, `false`), set_value(`helper_envelope.result.exit_code`, `1`), set_value(`helper_envelope.result.normalized_outcome`, `"bad_request"`), set_value(`helper_envelope.data.policy_sha256`, `null`), set_value(`helper_envelope.data.compile`, `null`), set_value(`helper_envelope.data.import_inventory`, `null`)]. |
| <a id="contract-policy-helper_policy-admit-source"></a>2. Missing source | absent(`helper_policy.sbpl_source`) | [set_value(`helper_envelope.result.ok`, `false`), set_value(`helper_envelope.result.exit_code`, `1`), set_value(`helper_envelope.result.normalized_outcome`, `"bad_request"`), set_value(`helper_envelope.data.policy_sha256`, `null`), set_value(`helper_envelope.data.compile`, `null`), set_value(`helper_envelope.data.import_inventory`, `null`)]. |
| <a id="contract-policy-helper_policy-admit-extent"></a>3. Oversized source | (present(`helper_policy.sbpl_source`) and utf8_length(`helper_policy.sbpl_source`) > `4,194,304 bytes` (`helper_source`) ) | [set_value(`helper_envelope.result.ok`, `false`), set_value(`helper_envelope.result.exit_code`, `1`), set_value(`helper_envelope.result.normalized_outcome`, `"policy_too_large"`), set_value(`helper_envelope.data.policy_sha256`, `null`), set_value(`helper_envelope.data.compile`, `null`), set_value(`helper_envelope.data.import_inventory`, `null`)]. |
| <a id="contract-policy-helper_policy-admit-source_nul"></a>4. Source NUL | (present(`helper_policy.sbpl_source`) and contains(`helper_policy.sbpl_source`, `"\u0000"`)) | [set_value(`helper_envelope.result.ok`, `false`), set_value(`helper_envelope.result.exit_code`, `1`), set_value(`helper_envelope.result.normalized_outcome`, `"bad_request"`), set_value(`helper_envelope.data.policy_sha256`, `null`), set_value(`helper_envelope.data.compile`, `null`), set_value(`helper_envelope.data.import_inventory`, `null`)]. |
| <a id="contract-policy-helper_policy-admit-parameter_nul"></a>5. Parameter NUL | (present(`helper_policy.params`) and matches(`k`) > `0`) | [set_value(`helper_envelope.result.ok`, `false`), set_value(`helper_envelope.result.exit_code`, `1`), set_value(`helper_envelope.result.normalized_outcome`, `"bad_request"`), set_value(`helper_envelope.data.policy_sha256`, `null`), set_value(`helper_envelope.data.compile`, `null`), set_value(`helper_envelope.data.import_inventory`, `null`)]. |

<a id="contract-policy-helper_policy-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Compiler-helper policy](#contract-policy-helper_policy) and its descendants.** The adjacent field meanings and operations follow the named implementation. [Evidence details](CONTRACT.md#contract-policy-helper_policy-support-details).
<!-- END GENERATED CONTRACT helper -->
