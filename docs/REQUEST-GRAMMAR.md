# Teaching the accepted request contract

This is a developer lesson. The [contract rules](CONTRACT.md#accepted-input-contract)
define the promise; the [specimen reference](PolicyWitness.md#specimen-format)
describes authoring. The examples here are executable inputs from
[tests/fixtures/request_contract/examples.json](../tests/fixtures/request_contract/examples.json).
Their expected refusals are independent data, checked by both the Swift unit
tests and live CLI/direct-XPC controls.

The [user guide exercise](PolicyWitness.md#try-an-accepted-request-and-a-refusal)
presents `create` and `capture_typo` as standalone commands. Keep its requests
aligned with those corpus cases so readers can repeat the same experiment
using the shipped app.

## Start with an observable instruction

The `create` example supplies an SBPL policy, one sandbox query, and one file
creation attempt. Its `$EFFECT` placeholder is replaced by an absolute path to
an absent file. This makes acceptance observable outside the returned JSON.

From the repository root, using a current signed build:

```sh
PW=dist/PolicyWitness.app/Contents/MacOS/policy-witness
PW_EXAMPLE_DIR=$(mktemp -d /private/tmp/pw-grammar.XXXXXX)
python3 tests/lib/request_examples.py create --effect "$PW_EXAMPLE_DIR/created" > "$PW_EXAMPLE_DIR/request.json"
cat "$PW_EXAMPLE_DIR/request.json"
"$PW" run "$PW_EXAMPLE_DIR/request.json" --no-log-capture > "$PW_EXAMPLE_DIR/run.json"
test -f "$PW_EXAMPLE_DIR/created"
```

The renderer prints the complete request and does no execution. It generates
a fresh nonce for examples that request capture. Keep the directory to inspect
both submitted bytes and returned evidence.

Reading that request teaches three boundaries:

1. `schema_version` identifies PW's accepted request contract.
2. `(version 1)` inside `sbpl_source` belongs to SBPL, a nested language.
3. `sandbox_check` and `attempt` describe independent observations. A query
   result cannot establish the attempted operation's effect. The file check
   supplies that observation in this exercise.

## Change one thing and predict the result

An input grammar describes the allowed shapes. A contract also gives those
shapes meaning, specifies refusals, and distinguishes execution from admission.
Use these corpus IDs with the same renderer:

| Example | Lesson | Expected behavior |
| --- | --- | --- |
| `malformed_json` | JSON syntax | `invalid_json` at the root. |
| `capture_typo` | Closed field names | `unknown_field` at `policy.capture_applied_profiel`. |
| `wrong_args_type` | Field types | `type_mismatch` at the attempt's `args`. |
| `parameter_value` | Open dictionaries | Parameter names are caller data, but their values must be strings. |
| `optional_nulls` | Defaults | Optional nulls have the same meaning as absence; creation succeeds. |
| `duplicate_ids` | Meaning across steps | `duplicate_step_id` at the second step. |
| `file_args` | Meaning across fields | Even an empty non-null `args` array is inapplicable to a file attempt. |
| `unused_nonce` | Meaning across fields | A nonce without enabled capture is refused. |
| `unused_filter_value` | Meaning across fields | A `none` filter cannot consume a non-null value. |
| `unknown_filter` | Supported vocabulary | An unknown filter name refuses the specimen. |
| `unknown_attempt` | Supported vocabulary | An unsupported second attempt prevents the first valid create from running. |
| `over_capacity` | Admission | 257 distinct steps decode, then exceed the current <!-- span limits.probe_steps.value -->256<!-- /span -->-step capacity. |
| `old_marker` | Version boundary | Another request contract is refused before its fields are interpreted. |
| `exec_args` | Effective arguments | `exec/spawn` of `touch` consumes its argument and creates the named file. |
| `capture` | Effective capture | Enabled capture returns a receipt with the submitted nonce. |
| `known_unavailable_prediction` | Witness limits | A recognized excluded query reports `prediction_unavailable`; the independent create still runs. |

Try the typo with a new, absent effect path:

```sh
python3 tests/lib/request_examples.py capture_typo --effect "$PW_EXAMPLE_DIR/refused" > "$PW_EXAMPLE_DIR/typo.json"
"$PW" run "$PW_EXAMPLE_DIR/typo.json" --no-log-capture > "$PW_EXAMPLE_DIR/refusal.json"
PW_EXAMPLE_RC=$?
test "$PW_EXAMPLE_RC" = 1
test ! -e "$PW_EXAMPLE_DIR/refused"
```

Inspect `data.request_failure` in that envelope:

```json
{
  "code": "unknown_field",
  "path": ["policy", "capture_applied_profiel"]
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

## The entry point matters

The controller accepts an authored specimen and resolves controller-owned
instructions before XPC delivery. The runner accepts the resulting specimen.
Both independently enforce the request marker.

| Example | Through the controller | Direct XPC |
| --- | --- | --- |
| `selector` | Resolves and records runner selection; creates the file. | Rejects `runner` as an unknown field. |
| `selector_typo` | Identifies the non-string entitlement at its array position. | Rejects the controller-only `runner` field. |
| `augment` | Resolves the named fragment, records policy provenance, and creates the file. | Refuses unresolved `policy.augments`. |

Consistent diagnostics do not imply identical accepted fields at different
boundaries. The corpus records an expectation for each boundary explicitly.
Selection precedence is also meaning: a nested empty entitlement list overrides
the top-level list; a nested null is absent and permits fallback. Malformed
shadowed aliases are still refused. The selector unit tests pin that rule.

## What the implementation promises

[PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) owns
the request types. `CodingKeys` lists the allowed fields; explicit decoding
rejects unknown names, missing required fields and wrong types. Parameter
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
[`buildStepResults`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift),
an unsupported attempt uses `attempt.result_source: "synthetic"` with
`missing_reason: "attempt_not_supported"`, even when handed a completed worker
slot. This is not a public input acceptance rule; the defensive comparison
case is covered in
[ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift).

A successful decode establishes neither valid SBPL nor a successful sandbox
application or operation. A passing request contract cannot certify the host's
filesystem state, permissions, available services, or kernel behavior.

## Deciding whether the contract changes

| Change | Caller impact | Contract treatment |
| --- | --- | --- |
| Rename a field, require a field, reject an accepted combination, or reinterpret an action | Existing requests need revision or a different meaning must be selected explicitly. | New request contract; refuse other markers. |
| Add an optional field or a supported action while preserving existing meanings | Existing callers remain valid; users of the addition need a capable build. | The request marker can stay stable. |
| Correct parameter transfer to honor its documented meaning | The request stays valid; observations may change. | Keep the marker and identify the implementation through build provenance. |
| Raise a capacity limit | More specimens can execute. | Document and test the capacity separately. |
| Lower a capacity limit | Previously runnable specimens may be refused. | An operational compatibility change even if the grammar is unchanged. |

Compatibility has a direction: a newer build can preserve existing requests
while an older build refuses a newly introduced field or action. The marker
does not enumerate every build's capabilities. A capacity refusal never
truncates a plan; automatically splitting one would also change its fresh-process
experiment. The caller decides whether to revise it or use another build.

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
