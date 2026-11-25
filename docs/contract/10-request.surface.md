# Saved specimens and runner selection {request: surface}

```contract
syntax: 1
artifact: "Saved specimens and runner selection"
goldens: ["tests/fixtures/contract/surfaces/request.json", "tests/fixtures/request_contract/examples.json"]
checks: ["failure_boundaries"]
```


A saved specimen describes one experiment. The controller reads its file once, resolves controller options and packaged augments, and serializes the held request delivered to the client. Direct XPC callers supply the host form themselves. The standalone compiler helper accepts its own policy input.

## Specimen {specimen: subject}

```contract
record: "PWRunnerRunSpec"
as: "specimen"
```

The host request objects have closed field sets. Parameter-map keys and caller labels are data within their own bounds.

### contract {contract: field}

```contract
uses: ["identity.public.contract"]
```

Required non-null string asserting the exact public contract identity. The controller checks it before selector parsing and augmentation; the host checks it before other request fields. Obtain the current value from the packaged version envelope. `unbound` is refused.

### specimen_id {specimen_id: field}

Required non-null string caller label, echoed when it fits <!-- span limits.specimen_id.value_unit -->255 UTF-8 bytes<!-- /span -->. It may be empty. Its identity is independent of the worker PID or an actor ID.

### run_kind {run_kind: field}

```contract
default: null
```

Optional caller label, bounded by <!-- span limits.request_label.value_unit -->63 UTF-8 bytes<!-- /span -->. Omission and null have the same meaning; it selects no execution mode.

### policy {policy: field}

Policy for the ordinary form. With no non-null `actors`, the policy object is required. In the actor form a non-null top-level policy is refused; each actor declares its own sandbox mode and policy.

### probe_plan {probe_plan: field}

Ordinary paired probes, including an empty array for apply-only execution. Exactly one of this field and `phases` must be non-null in the ordinary form. The host represents this plan as the `main` phase.

### phases {phases: field}

Ordered phase declarations. The ordinary form requires a nonempty array, forbids actor ownership, termination dependencies and extension actions, and uses one worker across its phases. The actor form requires phases and forbids a non-null `probe_plan`.

### actors {actors: field}

A non-null actor array selects the actor form; an empty array is refused. Each declared actor has its own fresh worker and at least one declared visit. Omission or null selects the ordinary form.

### _test_overrides {_test_overrides: field}

Optional block of two executable substitutions, `worker_executable_path` on the ordinary form and `actor_equipment_executable_paths` on the actor form. Each retains its stated scope and meaning; unknown members are refused, and so is a member that is one of the [eight controls of an experimental submission](#contract-request-overrides-ordinary_refusal). In an [experimental submission](#contract-request-overrides-experimental) the block must be absent, null or empty: the controls travel beside the request.

### Hold and deliver the selected request {hold: acts}

```contract
who: ["identity.definitions.controller"]
where: "saved-file processing"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Read and parse the request file once; gate its contract, parse selection, resolve named augments, strip controller selector fields and serialize once for client delivery. Preserve original and selected policy observations in the specimen dossier.
uses: ["identity.definitions.specimen", "identity.definitions.request"]
retained_free: {"effect":{"kind":"native_protocol","reason":"The read-once, in-memory augmentation and one-serialization guarantee concerns ownership of intermediate request bytes."}}
```



### Admission order and effects {admission: acts}

```contract
uses: ["refusals.request.consequence"]
who: ["identity.definitions.host"]
where: "request decode and whole-request admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Check contract first, decode the selected plan form and closed nested objects, check capacities, then validate policy and plan meaning. On refusal apply the runner request-refusal consequence. A host may already exist to deliver that refusal.
retained_free: {"effect": {"kind": "raw_admission", "reason": "Contract-first decoding and branch traversal consume raw objects before a complete typed request is available."}}
```

Admission accepts or refuses the complete plan; it preserves declared action counts. Empty ordinary plans still compile and apply the policy.

### Null and omission {nulls: acts}

```contract
who: ["identity.definitions.host"]
where: "request decoding"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
free.effect: Treat null as absent for each field whose entry says that null and omission are alike; any other null follows its field's stated presence rule. Refuse present null for actor equipment, actor required_entitlements, after_termination and actor_equipment_executable_paths. Retain presence of extension operands so an inapplicable operand is refused even when null.
uses: ["identity.definitions.absent", "identity.definitions.null_value", "extensions.operation"]
retained_free: {"effect":{"kind":"raw_admission","reason":"Key presence, explicit null and failed decoding are distinguished before optional admitted values erase those distinctions."}}
```



### Bounded strings and action counts {capacity: acts}

```contract
free.effect: Preserve complete UTF-8 strings at accepted bounds.
who: ["identity.definitions.host"]
where: "pre-child admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
retained_free: {"effect":{"kind":"serialized_grammar","reason":"Complete string transport and C-string admission describe the original encoded inputs, separate from the structured count requirements."}}
```

Native C-string inputs also refuse embedded NUL. A paired query and attempt consumes one action; an extension action consumes one action and contributes no query. Phase and actor counts do not multiply the total action capacity.

#### Ordinary source bytes {ordinary_source: condition}

```contract
when: absent(specimen.actors) and present(specimen.policy) and present(specimen.policy.sbpl_source)
test: utf8_length(specimen.policy.sbpl_source) <= limit("policy_source")
```

#### Actor source bytes {actor_source: condition}

```contract
bind.a: specimen.actors
each: ["a"]
when: present(specimen.actors) and present(specimen.actors[a].sandbox.policy) and present(specimen.actors[a].sandbox.policy.sbpl_source)
test: utf8_length(specimen.actors[a].sandbox.policy.sbpl_source) <= limit("policy_source")
```

#### Flat action count {flat_actions: condition}

```contract
when: absent(specimen.actors) and present(specimen.probe_plan)
test: count(specimen.probe_plan) <= limit("probe_steps")
```

#### Phased action count {phase_actions: condition}

```contract
when: present(specimen.phases)
bind.p: specimen.phases
test: sum_over(p, count(specimen.phases[p].actions)) <= limit("probe_steps")
```

#### Ordinary phase count {ordinary_phases: condition}

```contract
when: absent(specimen.actors) and present(specimen.phases)
test: count(specimen.phases) <= limit("phase_count")
```

#### Actor phase count {actor_phases: condition}

```contract
when: present(specimen.actors) and present(specimen.phases)
test: count(specimen.phases) <= limit("actor_phases")
```

#### Refusal consequence {failure: effect}

```contract
on: "failure"
effects: perform(ref("refusals.request.consequence"), request)
```

### Apply-only specimen {apply_only: example}

This template applies a policy with no probe actions. Replace the assertion with the packaged version's `build.contract` before submission.

```json
{"contract":"<reported-contract>","specimen_id":"apply-only","policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default)"},"probe_plan":[]}
```

### Emit the example specimen {emit_example: reports}

```contract
interface: ["command.example", "tail.example", "example.name.extension", "example.document", "example.document.extension"]
who: ["identity.definitions.controller"]
where: "CLI example dispatch"
entry: ["cli_example"]
recipient: ["cli_caller"]
report: ["example_specimen"]
uses: ["identity.build.contract", "identity.definitions.specimen"]
effects: set_value(specimen.contract, ref("identity.build.contract"))
```

`policy-witness example` prints the ordinary phased specimen. `policy-witness example extension` prints the actor specimen for a file-read grant. Each form prints one specimen defined by the emitting build, followed by one newline. The output is a request document, not an envelope. Process exit 0 supplies the complete document. Exit 0 reports that every write and the flush to the process's standard output succeeded. A command launched with standard output closed writes to a discarding descriptor and also exits 0. The build guarantees that its own `run` admits that document; emission performs no admission and observes none. Every failure to emit is process exit 2: an unknown name, an extra argument, a build whose identity is empty or `unbound`, an example the contract gate refuses, or a failed write or flush. A reason is written to standard error when that stream accepts it; the exit status does not depend on it. On exit 2 discard standard output, even when it holds a complete document. The document's content, layout and labels carry no stability promise between builds. The command reads no file, starts no runner and reports nothing about a caller's document; `run` remains the only admission.

#### Emission support {support: owner}

```contract
grade: "check_read"
source: [{"path": "controller/src/example.rs", "symbol": "pub fn render"}, {"path": "controller/src/example.rs", "symbol": "fn emit"}, {"path": "controller/src/example.rs", "symbol": "pub fn cmd_example"}, {"path": "controller/src/cli.rs", "symbol": "pub fn run"}]
check: [{"path": "controller/src/example.rs", "symbol": "rendered_document_is_the_constant_with_the_given_identity", "form": "test"}, {"path": "controller/src/example.rs", "symbol": "refusals_are_typed_and_write_nothing", "form": "test"}, {"path": "controller/src/example.rs", "symbol": "only_complete_output_with_a_successful_flush_succeeds", "form": "test"}, {"path": "controller/src/run_flow.rs", "symbol": "emitted_example_reaches_the_client_as_the_emitted_document", "form": "test"}, {"path": "controller/integration/cli_contract.rs", "symbol": "example_publishes_both_forms_and_refuses_unknown_tails", "form": "test"}, {"path": "controller/integration/cli_contract.rs", "symbol": "example_write_failures_exit_2_without_a_panic", "form": "test"}, {"path": "controller/integration/cli_contract.rs", "symbol": "supplied_direct_cargo_identity_is_embedded_without_release_provenance", "form": "test"}, {"path": "tests/suites/witness_contract/example_round_trip.sh", "symbol": "example_round_trip", "form": "test"}]
pins: "Emission parses the selected constant, inserts the binary's identity, passes the contract gate and uses the held request's serialization before any byte is written. An unknown name or extra operand, an empty or unbound identity, a gate refusal and a failed write or flush each return the refusal that the command maps to exit 2. The emitted file reaches the controlled client as emitted, without its framing newline. On the selected app the command exits 0 with one JSON object and one newline carrying the app's identity, repeats it byte for byte, refuses unknown names and extra operands, and exits 2 when stdout has no reader whether or not stderr can be written; launched with stdout closed it exits 0 with an empty stderr; a build without an identity prints nothing."
context: "Read the emitter and dispatch, the emitter's unit tests, the controlled orchestration test, the CLI integration tests against the selected app and isolated Cargo builds, and the live round-trip case with its checker."
limits: "Check read; no execution is credited. The exact request comparison runs under the test identity and ends at the client callback; on a signed app the live case observes the delivered length only. A gate refusal on a bound build has unit support and no built-app observation. No check observes the process's file reads; the isolated builds emit with no app, manifest or registry beside them. The stdout-closed row observes the exit status and an empty stderr; the discarding descriptor is not observed. Development runs of these checks exist and are disposable; release credit awaits an archived acceptance."
```

### Publish a developer read input {emit_test_input: reports}

```contract
who: ["identity.definitions.controller"]
where: "CLI test-input dispatch"
entry: ["cli_test_input"]
recipient: ["cli_caller"]
report: ["test_input_specimen"]
uses: ["identity.build.contract", "identity.definitions.specimen"]
effects: set_value(specimen.contract, ref("identity.build.contract"))
```

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

#### Publication support {support: owner}

```contract
grade: "check_read"
source: [{"path": "controller/src/test_input.rs", "symbol": "fn render_template"}, {"path": "controller/src/test_input.rs", "symbol": "fn emit_template"}, {"path": "controller/src/test_input.rs", "symbol": "pub fn cmd_test_input"}, {"path": "controller/src/cli.rs", "symbol": "pub fn run"}]
check: [{"path": "controller/src/test_input.rs", "symbol": "read_input_preserves_target_identity_and_fixed_workload", "form": "test"}, {"path": "controller/src/test_input.rs", "symbol": "malformed_templates_refuse_before_output", "form": "test"}, {"path": "controller/src/test_input.rs", "symbol": "members_outside_the_assigned_positions_are_published_as_embedded", "form": "test"}, {"path": "controller/src/test_input.rs", "symbol": "argument_target_and_identity_refusals_write_nothing", "form": "test"}, {"path": "controller/src/test_input.rs", "symbol": "complete_publication_requires_all_writes_and_flush", "form": "test"}, {"path": "controller/integration/cli_contract.rs", "symbol": "test_input_publishes_read_from_the_installed_binary", "form": "test"}, {"path": "controller/integration/cli_contract.rs", "symbol": "test_input_cli_refusals_and_write_failures_exit_2_safely", "form": "test"}, {"path": "controller/integration/cli_contract.rs", "symbol": "supplied_direct_cargo_identity_is_embedded_without_release_provenance", "form": "test"}]
pins: "The fixed read template binds the binary identity and caller target positionally, including literal marker text, quotes, backslashes and non-ASCII characters. A body that is not an object, carries a contract, has no step or a second step, or lacks the placeholder at an assigned operand or a container leading to it refuses before output. A body differing elsewhere is published with the same three assignments. Argument, target and identity refusals write nothing. Short writes complete the document, while partial-write and late-flush failures refuse. Selected-app controls check deterministic publication and exact request content, removed lesson dispatch, status 2 on invalid arguments and unreadable stdout, status independence from stderr closed at launch, and exit 0 with an empty stderr when stdout is closed at launch. Isolated Cargo builds check absent and supplied identities."
context: "Read the embedded-template materializer, dispatch, constructed argument/template/writer controls and CLI integration assertions."
limits: "Check read; no execution is credited. Publication controls establish neither host admission nor native file effects. No control observes the absence of operating-system reads or process launches; those claims have source support. The closed-stream rows observe exit statuses, and an empty stderr where stdout is closed; the discarding descriptor is not observed. These checks do not promise admission for arbitrary target lengths or environments."
```

### Developer read body {read_input: example}

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

#### Body support {support: owner}

```contract
grade: "check_read"
source: [{"path": "controller/src/test_input.rs", "symbol": "fn render_template"}]
check: [{"path": "controller/integration/cli_contract.rs", "symbol": "test_input_publishes_read_from_the_installed_binary", "form": "test"}]
pins: "The selected-app publication assertion independently states the read body's identity, policy, query, attempt and target binding."
context: "Read the binding of the embedded body and the independently authored CLI publication expectation."
limits: "Check read; no execution or native outcome is credited. This body is build-specific public content, not a compatibility promise for later builds."
```

### Emitted example {example: example}

```contract
document: {"path": "controller/src/example_document.rs", "symbol": "EXAMPLE_DOCUMENT"}
uses: ["identity.definitions.cause"]
```

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

#### Example support {support: owner}

```contract
grade: "check_read"
source: [{"path": "controller/src/example_document.rs", "symbol": "EXAMPLE_DOCUMENT"}]
check: [{"path": "tests/suites/source_drift/contract_tree_controls.py", "symbol": "test_example_document_is_extracted_from_its_cited_constant", "form": "test"}, {"path": "tests/suites/source_drift/contract_tree_controls.py", "symbol": "test_example_document_refusals_name_the_source", "form": "test"}, {"path": "tests/suites/source_drift/generators.py", "symbol": "test_example_source_edit_is_stale_until_regeneration_and_moves_content_and_identity", "form": "test"}, {"path": "tests/suites/witness_contract/example_round_trip.sh", "symbol": "example_round_trip", "form": "test"}, {"path": "tests/suites/witness_contract/check_example_round_trip.py", "symbol": "evaluate", "form": "test"}, {"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
pins: "The rendering is the parsed constant, which must be a request object without an identity, test overrides or selection keys, and without a member at any depth that the imported request records do not declare. The runner's decoder and admission gate accept the snapshot's document under the test identity. An edit to the constant is refused until regeneration and then moves the rendering, the request payload and the build identity. The live case requires the selected app's emitted document without its identity to equal this snapshot and to be an ordinary two-phase read-only workload with two actions then one: a data-read query and open of one target, a metadata query on a second target beside a fresh read of a third, and a data-read query and open of the second. It submits the emitted bytes unchanged and derives flat and single-applied-actor forms with the same actions and policy. Each submission independently requires admission, identity, digest, phase/action ownership and echo relationships; the actor also requires applied-once, selected-equipment and reaped-process observations. A diagnostic summary carries no equality assertion. Under observed target prerequisites it then requires, each as its own assertion, a captured process status of 0, a finished reply, each step's answer, each step's attempt, query-first order, and a fresh read whose descriptor identity, count and bytes equal the case's own observation of that target."
context: "Read the constant, the extraction's constructed controls, the disposable-copy generation control, the runner's admission test and the live case with its checker and rejected controls."
limits: "Check read; no executed instance is credited here. Host admission and the native results are observed by the live case on a development build and one machine, under observed target prerequisites, and are not release evidence. The case compares no answer with its attempt and assigns no cause to the failed open. It cannot distinguish the first two steps' allow answers exchanged, samples its targets only before and after the run, and does not establish which object a native query consulted. The extraction reads member names and the admission test stops before policy compilation, equipment inspection and any launch; those and every native result are established by execution. The example's content carries no stability promise between builds."
```

### Emitted extension example {extension_example: example}

```contract
document: {"path": "controller/src/example_document.rs", "symbol": "EXTENSION_DOCUMENT"}
```

`policy-witness example extension` prints this document with the emitting build's identity. The issuer transfers a file-read extension to Alice. Both Alice and Bob try a fresh open before issuance and again after Alice consumes the token. The transfer records delivery. Each successful fresh read records the opened object's identity and sampled bytes.

#### Extension example support {support: owner}

```contract
grade: "check_read"
source: [{"path": "controller/src/example_document.rs", "symbol": "EXTENSION_DOCUMENT"}]
check: [{"path": "tests/suites/witness_contract/example_round_trip.sh", "symbol": "example_round_trip", "form": "test"}, {"path": "tests/suites/witness_contract/check_extension_example.py", "symbol": "round_trip", "form": "test"}, {"path": "tests/suites/witness_contract/check_extensions.py", "symbol": "run_targets", "form": "test"}, {"path": "tests/suites/source_drift/contract_tree_controls.py", "symbol": "test_example_document_refusals_name_the_source", "form": "test"}, {"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
pins: "The round trip takes each named invocation from the selected app's example help card and submits that stdout unchanged to ordinary run. For this document it requires the two readers to be declared alike, matches the request digest, and requires that Alice's read after consumption is the only read that opened the independently sampled file. The extension controls retarget the emitted document to a case-owned file. With the delivery, consumption and release moved to Bob, Bob's later read is the only one that opens it. In three further schedules issuance, delivery, consumption and release still succeed and the same access claim is false: Alice can read before consuming, Bob's policy has no extension rule, and the grant names another file. The extraction refuses a member at any depth that the imported request records do not declare. The runner's decoder and admission gate accept the snapshot's document under the test identity."
context: "Read the published document, the round trip, the separate extension controls, the extraction's constructed controls and the runner's admission test."
limits: "Check read. The outside descriptor samples the target before and after execution. These trials cover the selected file and equipment. Release acceptance supplies separate execution evidence."
```

### Field names in a specimen {duplicate_keys: definition}

```contract
defines: "value"
```

Supply each field name at most once within a JSON object, both in a saved specimen and in a direct host request. For a repeated name, acceptance and the choice of value are unspecified. This applies to field names within one object. The separately declared uniqueness rules for step and actor identifiers apply across the plan.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"controller/src/request_patch.rs","symbol":"parse_request"}
pins: "For a request with one value per field, the CLI and direct-host controls bind the admitted step, policy digest and created file to the caller's input. A foreign contract is refused at each receiving boundary."
context: "The capture repair and identity-before-selector cases submit independently written requests and inspect the effect path."
check: [{"path":"tests/suites/runner_outcome_bad_request/contract.py","symbol":"refusal_workflows","form":"test"}]
limits: "These checks exercise unambiguous inputs. They establish no rejection or precedence rule for a repeated field name."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerRunSpec"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "admissionFailure"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "admitSpecimen"}, {"path": "controller/src/run_flow.rs", "symbol": "validate_request_contract"}, {"path": "controller/src/request_patch.rs", "symbol": "pub fn validate_request_contract"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "requestAdmissionFailure"}, {"path": "runner/Sources/PWRunnerCore/ActorPlan.swift", "symbol": "actorAdmissionFailure"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
context: "Source inspection of the current implementation; no execution is credited."
limits: "Read the request fixture corpus loop, identity/unknown-field checks and actor parameter-capacity assertions. The apply-only template has source-level support; this owner credits no executed instance of that template."
check: [{"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}]
```



## Controller selection options {options: subject}

```contract
record: "ControllerSelectionOptions"
as: "options"
```

These fields extend the saved-file root at the controller entry. The controller strips all five before client delivery. A direct XPC request carrying them reaches the host unknown-field refusal.

### runner {runner: field}

```contract
type: "ControllerRunnerSelector"
optional: true
json_null: true
```

Optional nested selector object. Null means absent. Unknown nested keys are refused.

### runner_id {runner_id: field}

```contract
type: "String"
optional: true
json_null: true
```

Legacy registry ID selector. Null means absent; a non-string value refuses even when nested `runner.id` would override it.

### runner_service {runner_service: field}

```contract
type: "String"
optional: true
json_null: true
```

Legacy explicit Mach service selector. Null means absent; a non-string value refuses before nested precedence is applied.

### required_entitlements {required_entitlements: field}

```contract
type: "[String]"
optional: true
json_null: true
```

Legacy list of selected-worker entitlement keys required to be boolean true. Null means absent. Values must be strings.

### runner_mode {runner_mode: field}

```contract
type: "String"
optional: true
json_null: true
vocabulary: "closed"
listed: "exhaustive"
values: ["standard", "byoxpc"]
```

Legacy runner mode. Null means absent. The accepted values are `standard` and `byoxpc`.

### Selector precedence {precedence: acts}

```contract
interface: ["run.option.runner_mode", "runner_kind.standard@run_option", "runner_kind.byoxpc@run_option"]
who: ["identity.definitions.controller"]
where: "runner selector parsing"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Validate every supplied legacy value first, then let each non-null nested value replace its corresponding legacy value. An explicit nested empty entitlement list replaces the legacy list. Refuse with `conflicting_selector`: standard mode with an external selector, or byoxpc mode without an ID or service (at the root path), and a `--runner-mode` value that differs from the file's nested `runner.mode` (at `runner.mode`).
retained_free: {"effect": {"kind": "raw_admission", "reason": "CLI mode injection and per-field precedence construct the effective selector from supplied candidates. Malformed raw values are checked before replacement; an explicit nested empty entitlement list replaces the legacy list."}}
```

CLI `--runner-mode` is parsed before reading the request and is injected into its selector processing. `machme` is refused. Selection resolution and entitlement checks precede client invocation. A resolved target identifies the requested host service; actor equipment roles remain actor declarations.

### Selection and augmentation failure order {failure_order: acts}

```contract
uses: ["refusals.controller.consequence"]
who: ["identity.definitions.controller"]
where: "request preparation"
entry: ["cli_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
free.effect: Retain a target-resolution error while resolving augment dossiers. Select the target-resolution error first; otherwise select an augment refusal when present. Apply the controller pre-invocation consequence to the selected failure.
retained_free: {"effect": {"kind": "native_protocol", "reason": "Target resolution and augmentation return separate intermediate results. Their priority determines which refusal procedure applies."}}
```



### Support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/runner_select.rs", "symbol": "parse_runner_selector_value"}, {"path": "controller/src/run_flow.rs", "symbol": "strip_runner_selector"}, {"path": "controller/src/runner_select.rs", "symbol": "pub fn strip_runner_selector"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
context: "Source inspection of the current implementation; no execution is credited."
limits: "Read parser and precedence controls; full registry selection and installed-equipment evidence belongs to installation and equipment."
check: [{"path": "controller/src/runner_select.rs", "symbol": "nested_runner_takes_precedence_over_legacy_top_level", "form": "test"}, {"path": "controller/src/runner_select.rs", "symbol": "malformed_selection_never_falls_back_or_discards_entitlements", "form": "test"}, {"path": "controller/src/runner_select.rs", "symbol": "optional_nulls_and_explicit_nested_empty_entitlements_have_defined_meanings", "form": "test"}]
```



## Nested runner selector {selector: subject}

```contract
record: "ControllerRunnerSelector"
as: "selector"
```



### id {id: field}

```contract
type: "String"
optional: true
json_null: true
```

Registry ID for an installed external runner.

### service {service: field}

```contract
type: "String"
optional: true
json_null: true
```

Explicit external Mach service name.

### required_entitlements {required_entitlements: field}

```contract
type: "[String]"
optional: true
json_null: true
```

Selected-worker entitlement keys that must read back as boolean true for selection. This demand is separate from each actor's required_entitlements.

### mode {mode: field}

```contract
type: "String"
optional: true
json_null: true
vocabulary: "closed"
listed: "exhaustive"
values: ["standard", "byoxpc"]
```

Mode constraint applied to selection. With no mode or external selector, selection uses the packaged standard runner.

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/runner_select.rs", "symbol": "RunnerSelector"}, {"path": "controller/src/runner_select.rs", "symbol": "parse_runner_selector_value"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
```



## Execution overrides {overrides: subject}

```contract
record: "PWRunnerTestOverrides"
as: "overrides"
```

This record holds ten controls. Two are request data, admitted in a request's `_test_overrides` block by every host, packaged hosts included: `worker_executable_path` and `actor_equipment_executable_paths`. The other eight are supplied only outside the request, through an [experimental submission](#contract-request-overrides-experimental); an ordinary submission [refuses them](#contract-request-overrides-ordinary_refusal). Their names identify test use; the decoder applies the documented grammar and capacities. Host admission of a positive fixture value can be followed by worker argument refusal before application.

### worker_executable_path {worker_executable_path: field}

Ordinary-worker executable override, bounded by <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. Actor-form admission refuses this singular override.

### worker_timeout_ms {worker_timeout_ms: field}

Ordinary worker sentinel budget override in milliseconds. The host floors the supplied allowance at <!-- span limits.worker_timeout_override_floor.value_unit -->50 milliseconds<!-- /span -->; omission uses <!-- span limits.worker_sentinel_wait.value_unit -->120,000 milliseconds<!-- /span -->. Actor scheduling uses its fixed setup allowance and its fixed <!-- span limits.actor_execution_allowance.value_unit -->120,000 milliseconds<!-- /span --> execution allowance even when this field is supplied.

#### Floor support {floor_support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift","symbol":"timeoutMsForCWorker"}
check: {"path":"runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift","symbol":"runLimitsContractTests","form":"test"}
pins: "Calls the production helper to compare its floor to the limits inventory; independent below/equal/above cases retain the minimum and the uncapped larger override."
context: "Planning helper and newly authored constructed assertions read."
limits: "No test execution is credited; the check establishes the planning value, not elapsed worker time."
```

#### Actor applicability support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorOrchestration.swift","symbol":"runActors"}
pins: "Actor orchestration constructs the scheduler input with its fixed allowances."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/witness_contract/check_actor_compositions.py","symbol":"assert_timeout_applicability","form":"test"}]
limits: "The paired control uses a 200 ms override and a 500 ms delay, checking an ordinary timeout and actor completion with a later dependent file read."
```

### actor_equipment_executable_paths {actor_equipment_executable_paths: field}

Actor equipment role-to-path map. Present maps must be nonempty and use only `selected` and `unentitled` keys; actor admission requires absolute paths. The ordinary form refuses this map.

### validator_executable_path {validator_executable_path: field}

Validator executable override, bounded by <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. The validator remains a separate child and receives query work through its own channel.

### validator_total_timeout_ms {validator_total_timeout_ms: field}

Cumulative validator collection budget override in milliseconds, spanning phases. Both schedulers clamp it to a minimum of <!-- span limits.validator_collection_override_floor.value_unit -->1 millisecond<!-- /span --> and their configured maximum: <!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span --> for the ordinary form and <!-- span limits.actor_collection_allowance.value_unit -->30,000 milliseconds<!-- /span --> for actors. Omission uses that maximum.

### validator_io_timeout_ms {validator_io_timeout_ms: field}

Per-validator I/O timeout override in milliseconds. The host floors the proposed allowance at <!-- span limits.validator_io_override_floor.value_unit -->50 milliseconds<!-- /span -->; omission uses <!-- span limits.validator_io_wait.value_unit -->30,000 milliseconds<!-- /span -->. The remaining aggregate collection allowance can reduce the effective timeout below that floor.

### worker_post_apply_hang_ms {worker_post_apply_hang_ms: field}

Positive fixture delay in milliseconds after all declared visits and actions, before terminal publication. The host forwards positive values; the worker argument parser accepts through <!-- span limits.worker_fixture_delay.value_unit -->60,000 milliseconds<!-- /span -->. A larger forwarded value causes worker argument refusal after launch. Zero and negative values are omitted by the host.

### worker_post_apply_kill_signal {worker_post_apply_kill_signal: field}

Positive fixture signal requested after completed actions and before terminal publication, including an unapplied actor's visits. The host forwards positive values; the worker accepts signal numbers through 31. A larger value causes worker argument refusal after launch. Zero and negative values are omitted. A signal request can return without termination; final process observations decide the ending.

### worker_pre_ready_hang_ms {worker_pre_ready_hang_ms: field}

Positive fixture delay in milliseconds after compilation and optional capture, before an apply worker's readiness byte and policy application. The host forwards positive values; the worker argument parser accepts through <!-- span limits.worker_fixture_delay.value_unit -->60,000 milliseconds<!-- /span -->. A larger value causes worker argument refusal after launch. Zero and negative values are omitted. The unapplied actor branch bypasses this compile/readiness path.

### worker_kill_before_publish_slot {worker_kill_before_publish_slot: field}

Nonnegative zero-based slot in each worker's own plan. After that attempt returns and its result payload is written, the worker raises SIGKILL before publishing completion. Negative values are omitted. The worker argument parser requires an index below <!-- span limits.probe_steps.value_unit -->256 items<!-- /span -->; an index beyond the worker's actual plan has no reached action to trigger it.

### Override admission and equipment ordering {override_authority: definition}

```contract
defines: "condition"
uses: ["equipment.binding"]
```

A caller whose connection passes host authorization can supply these controls. Actor equipment preparation checks the packaged inventory and both packaged role bindings before considering fixture override bindings. It retains the packaged and test_override rows with their respective implementation identities.

### Experimental submission {experimental: acts}

```contract
uses: ["refusals.request.consequence", "request.specimen.admission"]
who: ["identity.definitions.host"]
where: "experimental submission decode and admission"
entry: ["xpc_execute"]
recipient: ["caller", "report_reader"]
report: ["runner_reply"]
```

An experimental submission is a separate host call. It carries the request and, beside it, one JSON object of controls. Which call arrived decides the form; no request field selects it.

The controls object admits eight members: `worker_timeout_ms`, `worker_pre_ready_hang_ms`, `worker_post_apply_hang_ms`, `worker_post_apply_kill_signal`, `worker_kill_before_publish_slot`, `validator_executable_path`, `validator_io_timeout_ms` and `validator_total_timeout_ms`. Each has the type, scope and meaning of the field of the same name in this record.

The host decodes the request first, its contract before any other field. In that request, a `_test_overrides` block holding any member is refused with `inapplicable_field` at `_test_overrides`; a member whose value is null is a member. An absent, null or empty block is admitted. The host then decodes the controls object. An unknown member is refused with `unknown_field`; `worker_executable_path` and `actor_equipment_executable_paths` with `inapplicable_field`; a value of another type, or an integer outside the signed 64-bit range, with `type_mismatch`. Bytes that are not JSON are refused with `invalid_json`, a null with `missing_value` and any other value that is not an object with `type_mismatch`. A member whose value is null is absent. A refused control is located where the controls stand in the host's request: `_test_overrides` followed by the member name, or `_test_overrides` alone for the whole object.

The decoded controls take the block's place, and the request then passes the ordinary capacity and meaning admission. The validator path keeps its <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span --> bound, its embedded-NUL refusal and the withheld echo of a refused string, reported as `_test_overrides.validator_executable_path`. The reply's `test_overrides` mirrors the admitted controls object; with no member supplied it is an empty object, where an ordinary submission without a block has none.

#### Refusal consequence {failure: effect}

```contract
on: "failure"
effects: perform(ref("refusals.request.consequence"), request)
```

#### Experimental admission support {support: owner}

```contract
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerAPI.swift", "symbol": "runReservedExperiment"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerService.swift", "symbol": "decodeExperimentalSubmission"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerService.swift", "symbol": "runSubmission"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerOverrideSource"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "overridePathAdmissions"}, {"path": "runner/Clients/PWRunnerClient/PWRunnerClientSession.swift", "symbol": "submitExperiment"}]
check: [{"path": "runner/Tests/PWRunnerCoreTests/ExperimentalSubmissionTests.swift", "symbol": "runExperimentalSubmissionTests", "form": "test"}, {"path": "runner/Tests/PWRunnerClientSessionTests/main.swift", "symbol": "runClientSessionControls", "form": "test"}, {"path": "tests/suites/witness_contract/check_test_input_seam.py", "symbol": "evaluate", "form": "test"}]
pins: "Constructed submissions compare the decoded record with the members given, a null member absent, and the rest of the request with the same request carrying no block; refuse each listed member, type and container fault at its stated code and location; refuse a block with a value, a null member or an unselected member, alone and beside a control; decode the contract and request before the controls; and, through the service, show one admission, the controls in the reply echo, an empty echo for an empty object, a consumed host on each refusal, and the path bound, NUL refusal and withheld echo for the validator control. The client session makes the experimental call once, with the request and controls bytes unchanged, only when controls were given. The selected-app case reads a request block refused through the controller, alone and beside a control, and through the runner client; an admitted empty block; a controls object delivered by the client; and a fractional control refused at the client."
context: "Read the two submission calls, the decoder's three inputs, the shared capacity rule, the service unit tests, the client session controls and the selected-app checker."
limits: "Check read; no execution is credited. Unit submissions call the service object without XPC and observe orchestration through a substituted closure. The selected-app case submits one type fault through the client; it does not submit an unknown or unselected member, or bytes that are not JSON, there. Development runs of these checks exist and are disposable; release credit awaits an archived acceptance."
```

### Ordinary refusal of the experimental controls {ordinary_refusal: definition}

```contract
defines: "condition"
uses: ["refusals.request.consequence"]
```

An ordinary submission carries none of the eight controls. Its `_test_overrides` block holding `worker_timeout_ms`, `worker_pre_ready_hang_ms`, `worker_post_apply_hang_ms`, `worker_post_apply_kill_signal`, `worker_kill_before_publish_slot`, `validator_executable_path`, `validator_io_timeout_ms` and `validator_total_timeout_ms` is refused with `inapplicable_field` at `_test_overrides` followed by that member's name. Presence decides: a member whose value is null, zero, negative or of another type is a member, and the refusal precedes the reading of any member's value. When the block holds several, the refusal names the first in the order just listed. An unknown member of the block is refused first, with `unknown_field`; the contract and the request's other fields are decoded before the block.

The refusal has the request refusal's consequence: no worker or validator starts, and the reply carries no `test_overrides`. `worker_executable_path` and `actor_equipment_executable_paths` remain request data, each on its own request form, and the controller's `run` delivers the block as written.

#### Ordinary refusal support {support: owner}

```contract
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "experimentalControls"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerOverrideSource"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerService.swift", "symbol": "runSubmission"}, {"path": "controller/src/dossier.rs", "symbol": "pub fn observe("}]
check: [{"path": "runner/Tests/PWRunnerCoreTests/ExperimentalSubmissionTests.swift", "symbol": "runExperimentalSubmissionTests", "form": "test"}, {"path": "runner/Tests/PWRunnerCoreTests/RequestContractTests.swift", "symbol": "runRequestContractTests", "form": "test"}, {"path": "controller/src/run_flow.rs", "symbol": "test_input_run_delivers_the_held_request_unchanged_and_the_controls_beside_it", "form": "test"}, {"path": "tests/suites/witness_contract/check_test_input_seam.py", "symbol": "evaluate", "form": "test"}, {"path": "tests/suites/runner_outcome_bad_request/contract.py", "symbol": "main", "form": "test"}]
pins: "The ordinary decoder refuses each of the eight members at its own name with an acting value, zero, a negative value, null and values of other types; names the first in the declared order when two are present; refuses a control beside the worker substitution and before that member's type fault; reports an unknown member, the contract and an earlier request field first; and still admits the two request-block members, an empty block and no block. Through the service's ordinary call each control, with a value and with null, consumes the host before admission or orchestration and yields a reply with no echo, while the worker substitution alone reaches orchestration. Controlled orchestration shows `run` delivering a block as written and recording no validator selection for it. The selected-app case submits each control in a request block through plain `run`, with an acting and an inert value, and through the runner client's ordinary call, a control beside the worker substitution and beside another control, and one control alone in the block of an actor-form request through plain `run`; each is refused at the stated member with no worker, no echo and an unchanged target, and the actor-form reply holds no actor record. The request corpus submits a fractional control through both entries."
context: "Read the decoder's ordinary branch, the declared order, the service unit tests, the controlled orchestration test, the selected-app checker and the corpus loop."
limits: "Check read; no execution is credited. Unit submissions call the service object without XPC. The selected-app rows read the reply and an unchanged file; absence of a worker is the reply's own record, not an independent process observation. The actor form's block is submitted once, with one control and through plain `run` only. Development runs of these checks exist and are disposable; release credit awaits an archived acceptance."
```

### Run with test controls {test_input_run: acts}

```contract
interface: ["command.test_input", "test_input.form.run", "run.control.worker_timeout_ms", "run.control.worker_pre_ready_hang_ms", "run.control.worker_post_apply_hang_ms", "run.control.worker_post_apply_kill_signal", "run.control.worker_kill_before_publish_slot", "run.control.validator_executable_path", "run.control.validator_io_timeout_ms", "run.control.validator_total_timeout_ms"]
uses: ["request.specimen.hold", "request.overrides.experimental", "refusals.controller.consequence"]
who: ["identity.definitions.controller"]
where: "CLI test-input run dispatch"
entry: ["cli_test_input_run"]
recipient: ["caller", "report_reader"]
report: ["run_envelope"]
```

`policy-witness test-input run [--timeout-ms N] [--runner-mode KIND] [CONTROL VALUE]... REQUEST` performs the `run` command's preparation, delivery, reply admission and result selection, and prints the same `kind: "run"` envelope with the same exit statuses. Every rule stated for the `cli run` entry applies to it. It differs in two respects.

It makes the experimental submission. The client receives the held request unchanged and a controls object with one member for each control given, and no member when none was given. The controller does not read the request's `_test_overrides` block for this purpose and refuses none: the host owns that refusal.

The dossier's validator record observes the file `--validator-executable-path` names, under the [rules for a selected file](#contract-dossier-collection): a value beyond <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span --> is neither echoed nor opened, an empty or relative value is recorded without a hash, and the packaged validator's own path needs no comparison. No command reads a request's validator key.

A control is spelled `--` and its member name with hyphens: `--worker-timeout-ms`, `--worker-pre-ready-hang-ms`, `--worker-post-apply-hang-ms`, `--worker-post-apply-kill-signal`, `--worker-kill-before-publish-slot`, `--validator-executable-path`, `--validator-io-timeout-ms` and `--validator-total-timeout-ms`. An integer control takes one signed 64-bit decimal and is delivered as written. The controller applies no control's range, so a value the host floors or the worker's argument grammar refuses is submitted and judged there. `--validator-executable-path` takes the next argument as UTF-8 text, whatever it is. A control without a value, a value of another form, a repeated control and any other flag are refused before the request is read, with no client invocation. `run` admits none of these flags.

#### Refused arguments {usage: effect}

```contract
on: "failure"
effects: perform(ref("refusals.controller.consequence"), envelope)
```

#### Command support {support: owner}

```contract
grade: "check_read"
source: [{"path": "controller/src/interface/run_args.rs", "symbol": "pub fn classify"}, {"path": "controller/src/interface/commands.rs", "symbol": "pub fn select_form"}, {"path": "controller/src/test_input.rs", "symbol": "pub fn cmd_test_input"}, {"path": "controller/src/run_flow.rs", "symbol": "fn parse_arguments"}, {"path": "controller/src/run_flow.rs", "symbol": "fn controls_object"}, {"path": "controller/src/runner_client.rs", "symbol": "fn submission_arguments"}, {"path": "controller/src/dossier.rs", "symbol": "pub fn observe_with_validator_control"}]
check: [{"path": "controller/src/run_flow.rs", "symbol": "control_spellings_are_their_keys_and_only_test_input_run_admits_them", "form": "test"}, {"path": "controller/src/run_flow.rs", "symbol": "integer_controls_pass_every_signed_64_bit_decimal_through_unchanged", "form": "test"}, {"path": "controller/src/run_flow.rs", "symbol": "malformed_control_syntax_is_refused_before_any_run_work", "form": "test"}, {"path": "controller/src/run_flow.rs", "symbol": "test_input_run_delivers_the_held_request_unchanged_and_the_controls_beside_it", "form": "test"}, {"path": "controller/src/run_flow.rs", "symbol": "test_input_run_usage_refusals_invoke_no_client_and_read_no_app_root", "form": "test"}, {"path": "controller/src/runner_client.rs", "symbol": "only_an_experimental_submission_names_a_controls_object", "form": "test"}, {"path": "controller/src/dossier.rs", "symbol": "validator_control_follows_the_worker_key_rules_and_names_the_flag", "form": "test"}, {"path": "controller/integration/cli_contract.rs", "symbol": "interface_cases_hold_on_the_signed_controller", "form": "test"}, {"path": "tests/suites/witness_contract/check_test_input_seam.py", "symbol": "evaluate", "form": "test"}]
pins: "Each control is admitted only by this command and carries its member name; every signed 64-bit decimal, including values beyond each control's own range, reaches the controls object as written; values of another form, missing values, repeated controls and other flags are refused with the stated diagnostics before the app root is read and with no client call. Controlled orchestration delivers the same held request as `run` with the controls beside it, an empty object when none is given, and a request block as written; the validator record follows the control and not the request key. The case corpus holds the refusals and one admitted submission on the selected app. The selected-app case submits each control, compares the recorded command and delivered request with what it planned, and reads the echo apart from the host's or worker's own observation of the control."
context: "Read the definitions, the form dispatch, the argument parser, the controls encoder, the client argument, the dossier selection, their unit tests, the case corpus and the selected-app checker."
limits: "Check read; no execution is credited. Controlled orchestration replaces the client with a recording closure. The selected-app case observes one value per control; it does not vary the actor form, external runners or every refusal through a submission. No check observes that usage refusals start no process other than through the envelope's null client capture. Development runs of these checks exist and are disposable; release credit awaits an archived acceptance."
```

### Fixture-value support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorOrchestration.swift","symbol":"runActors"}
pins: "The actor path retains equipment preparation and fixed scheduler applicability separately."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/witness_contract/check_pre_apply_failure.py","symbol":"main","form":"test"}]
limits: "Excessive positive fixture values are sent through the selected CLI and checked at the downstream worker argument boundary."
```

### Support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWRunnerRequest.swift", "symbol": "PWRunnerTestOverrides"}, {"path": "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift", "symbol": "timeoutMsForCWorker"}, {"path": "runner/Sources/PWRunnerCore/ProbeRunner.swift", "symbol": "admitSpecimen"}, {"path": "runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift", "symbol": "collectionRemainingNs"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "collectionRemainingNs"}, {"path": "runner/Sources/PWRunnerCore/ActorSession.swift", "symbol": "postApplyHangMs"}, {"path": "runner/Sources/PWRunnerCore/ActorEquipment.swift", "symbol": "private func prepare"}, {"path": "controller/tools/pw_probe_runner/pw_probe_runner.c", "symbol": "kill_before_publish_slot"}]
pins: "The adjacent field meanings and obligations follow the named producer and admission branches."
```
