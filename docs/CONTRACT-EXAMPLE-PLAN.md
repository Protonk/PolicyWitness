# Contract example plan

This plan gives PolicyWitness one specimen that it defines in its own controller source, prints through its own CLI and admits through `run`, with a test that follows that passage on the signed app. The contract renders the example from the same source. The work follows the completed four-stage contract effort, whose remaining release inputs are in [RELEASE-INPUTS.md](../records/contract/RELEASE-INPUTS.md), and targets the 0.3.8 candidate without making the tag or publication an outcome.

The plan is written for an executor who knows the repository but not the planning conversation. Section 2 holds the principles the maintainer settled; a design choice that conflicts with one of them is wrong even if the rest of the plan seems to allow it.

## 1. Intended result

```sh
PW=/Applications/PolicyWitness.app/Contents/MacOS/policy-witness
$PW example > /tmp/example.json
$PW run /tmp/example.json > /tmp/result.json
```

- One definition of the example exists, in controller source.
- `example` prints that definition with the binary's own identity, in the serialization the controller itself holds and delivers.
- `run` admits the printed document and delivers its bytes without the single trailing framing newline.
- The contract's rendering of the example is extracted from that source.
- A default-battery case follows the passage on the signed app. It supplies no specimen of its own.

For this release the audience is the project: PolicyWitness is tested against its own expression at release. This is a public command currently intended for project verification. The user guide lists it in its command table and presents no workflow; a purpose-built help and example interface is later work with its own plan. It is the first step toward examples that keep statements of what PolicyWitness accepts out of the user guide.

## 2. Principles

The maintainer settled these on 2026-11-12.

**There is one way to hold PolicyWitness.** A specimen is submitted with `run`, and `run` is the only way to ask whether PolicyWitness accepts a shape. The answer comes from the same admission that precedes execution. This plan adds no admission query, validation mode, dry run or second submission path, and none is on its route. `example` takes no input and answers no question about a caller's document; it hands the caller an input for `run`. Every refusal the test demands is obtained through `run`.

**The app is the authority for the example.** The example is what the shipped code defines. Nothing outside that code holds a second copy that must be kept equal by hand: the contract extracts its rendering, and the test obtains the document from the built app.

**Fixtures author no specimen.** A fixture intervenes in three places and nowhere else:

- *before*, by changing the produced bytes in one place and demanding refusal at a stated boundary;
- *beside*, by observing the machine itself: the target file, the process exit status;
- *after*, by reading the envelope with the independently written consumer and requiring the controller's own assessment to be clean.

A fixture does not restate the app's interpretive rules. Those belong to the host, controller and test consumer; a missing consumer check is added there with its controls. This plan does not add a fourth interpreter. The live case still has independent expectations: the document must contain at least one paired, read-only probe, and the native results must satisfy the expectations pinned to the present example. These expectations state the test's purpose without copying its specimen, policy, target or labels.

**Make a narrow public promise.** Successful emission gives a document that the same build admits through `run`. Content, layout and labels carry no stability promise between builds. The exit and output rules are public behavior, even while the command's intended audience is the project.

## 3. Starting state

Observed on `main` on 2026-11-12. Re-check any that the work depends on.

**The checkout is prepared for `v0.3.8` and has no `v0.3.8` tag.** The stamp tables and [contract/public.json](contract/public.json) claim the release, so `generate_contract_stamps.py --check` exits 1 with `release history unavailable; restore annotated release tags: v0.3.8`, and [build.sh](../build.sh), which runs that check, refuses. Ordinary generation refuses too; generation with `--release v0.3.8` works. Earlier pre-tag work alternated between the two states: `d18d4925` returned the stamps to `unreleased`, and `6f65612b` prepared them again.

**Identity.** [build_contract.py](build_contract.py) derives `release:vX.Y.Z` for a clean checkout at one annotated release tag whose selected bytes equal the tag's blobs, and `development:<sha256>` otherwise. The digest covers every `.rs` file under `controller/src`. [json_contract.rs](../controller/src/json_contract.rs) embeds the value as `BUILD_CONTRACT`; a plain Cargo build is `unbound`.

**Admission and the held request.** [`validate_contract`](../controller/src/request_patch.rs) requires `contract` to equal the binary's identity and refuses an empty or `unbound` identity; a refusal is exit 1, `bad_request`, with `data.request_failure`. The controller owns that gate, selectors and augments. The request grammar belongs to the Swift host. [run_flow.rs](../controller/src/run_flow.rs) parses the file once, resolves augments, removes controller selection fields, and holds one `serde_json::to_string_pretty` serialization that it delivers to the client without a trailing newline. A retained smoke run reports `request_delivery.bytes_written` of 576, matching the length computed from the submitted specimen; this is a length observation, not proof of byte identity. The existing controlled orchestration tests capture the exact string passed to `RunDependencies.client`, which can establish the example's byte-preservation property through the actual preparation path.

**The controller already originates one specimen.** [`verify_request()`](../controller/src/runner_commands.rs) builds an apply-only request with the binary's identity and sends it on `runner verify`. The contract's `request.specimen.apply_only` example is a separate hand-typed document.

**CLI.** [cli.rs](../controller/src/cli.rs) dispatches `run`, `runner` and `--version`. Every current output is an envelope. `run` reads a file path; there is no standard-input form.

**Contract tree.** Example nodes carry prose and support and no kind-specific facts. A node's facts enter the canonical public payload, so they move the surface stamp. Strict loading requires each rule and example to have graded support or an explicit evidence gap. The tree already takes shapes from code: [record_definitions.py](contract/record_definitions.py) imports field declarations, and [runtime.py](contract/runtime.py) reads selector constants out of `runner_select.rs`. Generation refuses growth in `free.*` relationship counts.

**Readers and harness.** [consumer.py](../tests/lib/consumer.py) validates an envelope against the shape goldens and record rules, including `order` against its supporting chain, without consulting specimen policy or production classifiers. It does not currently bind the envelope's `result.normalized_outcome`, `result.ok` and `result.exit_code` to the admitted reply's outcome. This plan adds that relationship to the consumer with its own controls. The controller reports its assessment of the runner reply under `data.runner_sandbox_diagnostics` (`disposition_integrity`, `disposition_issues`); that assessment does not validate the outer result assembled afterward. [run_capture.py](../tests/lib/run_capture.py) re-serializes a specimen, so it cannot submit bytes unchanged. Release acceptance runs the default battery with no selectors ([SIGNING.md](SIGNING.md#release-procedure)). The opt-in `preflight/build_refusal_controls` rehearsal runs that battery against a disposable fixture reporting `release:v1.0.0`.

## 4. Design

### 4.1 The example in controller source

A new module, `controller/src/example.rs`, holds the example as one raw string constant, [`EXAMPLE_DOCUMENT`](../controller/src/example.rs): a JSON object without a `contract` member. This plan does not repeat it; the [contract's rendering](CONTRACT.md#contract-request-specimen-example) is extracted from the constant.

The scenario is one read-only paired probe under an allow-default policy. It writes nothing and needs no fixture, and it gives each of the three fixture interventions something to act on; an apply-only document would leave two of them empty.

The command builds its output from that constant with the functions `run` already uses:

1. `parse_request` reads the constant.
2. The binary's `BUILD_CONTRACT` is inserted as `contract`.
3. `validate_request_contract` gates the result.
4. `serde_json::to_string_pretty` serializes it, the call that produces `run`'s held request.

The emitter cannot print a document its own controller gate refuses; host admission is established by the live `run`. For this example, the emitted JSON document without its one trailing framing newline must be a fixed point of `run`'s preparation. The example carries neither selection fields nor augments. A controlled orchestration test submits the emitted file through `run` and compares the exact string captured at `RunDependencies.client` with that document, including all JSON encoding choices. It exercises the real preparation path rather than reproducing serialization in Python. The live case separately observes the delivery length and the returned evidence; those observations alone do not prove byte identity.

The exact comparison uses the test-compiled controller's `test:policy-witness` identity and ends at the client callback. It establishes request preparation for that build, not exact delivery by the signed development or release binary. On the signed app, `bytes_written` records bytes accepted by the client's stdin pipe; it does not record their contents or prove receipt by the host. Keep these scopes explicit in support and evaluation records. This plan adds no production capture or transport field to close that gap.

The file is hand-written Rust under `controller/src`. It is a build-identity input with no change to `build_contract.py`, no generated source and no build step. `build.sh` does not change.

The module's constant is the example's only definition. `verify_request()` stays as it is; section 11 describes optional sharing of storage or extraction without unifying its apply-only behavior with this paired probe.

### 4.2 The command

```text
policy-witness example
```

It takes no argument. Naming and selecting examples wait until a second example exists and its design is settled.

| Invocation | stdout | stderr | Exit |
| --- | --- | --- | --- |
| `example` on a bound build | The document and one trailing newline, nothing else | empty | 0 |
| `example` with any argument | empty | Usage | 2 |
| `example` when the binary's identity is empty or `unbound` | empty | One line stating that this build has no public identity | 2 |
| `example` when the constant does not parse or the gate refuses on a bound build | empty | One line with the request-failure code | 2 |
| Writing or flushing stdout fails | Whatever the system accepted, possibly an incomplete document | One line, if stderr is writable | 2 |

The command reads no file, resolves no app root, loads no manifest or registry and launches nothing. The whole document, including its framing newline, is rendered in memory and gated before any byte is written. Use `write_all` and an explicit flush; either failure maps to exit 2 without a panic. A short successful `write` is not completion, and a flush error must not be lost during writer destruction. Exit 0 supplies the complete document. On exit 2 callers must discard stdout, even if the bytes they received happen to form a complete document. The stderr line is for a person and is not a classification interface.

The fourth row cannot occur in a build from the signed pipeline: the contract generator's check, which `build.sh` runs before compiling, refuses a constant that is not an admissible-looking object (section 4.3), and JSON encoding of the identity round-trips exactly. Parse or gate failure occurs before output and therefore prints no document; a later write failure has the separate behavior in the fifth row. The fourth row has source and unit-test support and no built-app observation.

The output is the specimen itself, not an envelope. The document carries the identity in `contract`, where the contract says a specimen carries it, and redirecting stdout yields a file `run` accepts with no extraction step.

`print_usage` lists the command, and the controller README's CLI block follows `cli.rs` as the drift suite requires. The user guide lists it as one row of its command table, stating the two commands, the exit rule and its present use for project verification.

### 4.3 The contract's account

**One rule.** Under `request.specimen`, add `emit_example {emit_example: reports}`: the controller, at entry `cli_example`, reports a specimen with `set_value(specimen.contract, ref("identity.build.contract"))`. Its prose states that successful emission gives a document the same build's `run` admits, the two exit statuses and the requirement to discard stdout on exit 2, and that content, layout and labels carry no stability promise between builds. Author it without `free.*` facts. If one proves unavoidable, stop and raise it; do not raise the baseline. No new subject or record is needed, so no shape golden changes.

**One example node, rendered from code.** Add `request.specimen.example {example: example}` with one new example fact, a citation in the shared `path` and `symbol` vocabulary:

````markdown
### Emitted example {example: example}

```contract
document: {"path": "controller/src/example.rs", "symbol": "EXAMPLE_DOCUMENT"}
```
````

The tree reader extracts the constant with a strict reader that refuses anything but exactly one definition of that symbol as a raw string. It then requires a JSON object that has no `contract` member, no `_test_overrides`, none of the controller selection keys already read from `runner_select.rs`, and only members that are fields of the imported `PWRunnerRunSpec`. Deeper validity belongs to the host and is established by execution.

The renderer prints the document with `contract` shown as `<reported-contract>`, and the command that emits it. The parsed document enters the node's public payload, so a change to the example moves the `request` surface stamp. The cited source file becomes a declared generator input, as `runner_select.rs` already is.

The `apply_only` example stays as it is. By the maintainer's decision of 2026-11-12 the probes surface's `read_hosts` example takes its step from the same constant: its `document` fact adds a `member` path selecting the first step, checked against the step record's fields and rendered without the identity placeholder.

### 4.4 Identities and stale artifacts

| Concern | Mechanism |
| --- | --- |
| Development build | `contract` is `development:<sha256>`; the digest includes `example.rs`. |
| Release build | `contract` is `release:vX.Y.Z`; the release form requires `example.rs` to equal the tag's blob. |
| Example edited, contract not regenerated | `--check` refuses the stale [CONTRACT.md](CONTRACT.md) and snapshot before compilation and in `source_drift`. |
| Example malformed or carrying a forbidden member | The same check refuses, naming the source. |
| Source edited during a build | The existing pre-sign identity recomputation refuses. |
| Example changed between releases | The `request` stamp becomes `unreleased`; release preflight refuses remaining `unreleased` rows. |
| Specimen saved from another build | `run` refuses it with `unsupported_contract` and names the expected identity. |

No path runs from documentation into shipped code. Editing contract prose leaves the development digest unchanged. Release-form identity additionally requires a clean checkout at an eligible annotated release tag, so prose-only edits can change the next computed identity from release form to development form. An already-built app retains its embedded identity.

### 4.5 The round-trip case

**`witness_contract/example_round_trip`** (default; requires the app). A shell case in the style of the smoke case runs the selected app directly and retains raw stdout, stderr and exit status for every invocation: `--version`, two emissions, the `run` of the emitted bytes, and each perturbed `run`. A Python checker reads the retained files before submission and after execution. The emitted bytes are submitted unchanged; the case does not route them through `RunCapture`. The case contains no specimen document.

The emitted document is `S` and the run envelope for `S` is `E`. Every assertion has a stable identifier and belongs to one group.

Before submitting or perturbing `S`, the case checks the emission requirements and the bounds on what it will run below, using the same checker. A failed command cannot supply the specimen even when its stdout parses. A failure at this stage is `consistency`; retain the captures and report dependent run assertions as not evaluated, without invoking `run` or inventing an `execution_unavailable` failure for a run never attempted.

**Consistency.** These hold whatever the native results. A non-`finished` admitted reply can satisfy them. When no admitted reply exists, only the passage and controller-side assertions are evaluated.

| Group | Demand | Intervention |
| --- | --- | --- |
| Emission | `--version` and both `example` invocations exit 0; both emissions have empty stderr and each stdout is one JSON object followed by exactly one LF | before |
| Passage | `S.contract` equals `--version`'s `build.contract` and `data.contract` and the `PWContract` the case reads from the app's property list; it has a packaged `release:` or `development:` form; two emissions are byte-identical | after |
| Passage | `E`'s `request_delivery.bytes_written` equals `S`'s byte length after removing exactly its one framing newline. This is a delivery-length check; exact bytes at the client boundary are checked through controlled `run` orchestration | after |
| Passage | `S` without `contract` equals the contract's rendered example, read from the snapshot | after |
| What the case will run | `S` is the ordinary form with a nonempty `probe_plan` containing at least one step with both a `sandbox_check` and a read-only file attempt; every attempt is a read-only file action; no `_test_overrides`, selection fields, augments or entitlement requirement. The case refuses to run a document outside these bounds | before |
| Admission | No `request_failure` and no `bad_request` outcome; the dossier's `policy.augmentation.original_sha256` and the reply's `policy_sha256` equal the SHA-256 of `S`'s policy source | after |
| Identity | `E.build.contract`, `data.runner_client.transport.contract` and `runner_result.producer.contract` each equal `S.contract` | after |
| Echo | `runner_result.specimen_id` equals `S.specimen_id`; the reply's step identifiers are `S`'s, in order; each query echoes its submitted operation and filter; each attempt echoes its submitted kind, action and target | after |
| Reported against observed | The CLI exit status the case captured equals `result.exit_code` | beside |
| Existing readers | `consumer.validate` reports no error; the controller's `disposition_integrity` is `valid` with no `disposition_issues` | after |

Identity, digest and echo expectations are derived from `S` or another output of the same app. The case also states its purpose independently: there must be a paired probe, and its native results must meet the pinned expectations below. It does not copy the specimen, policy text, target or labels.

The comparison with the snapshot is a comparison, never a substitution: a mismatch means the app and the tree disagree, which a stale app produces. Ordering, comparison vocabulary and outcome mapping are not restated here. The consumer owns them, including the missing envelope-result relationship added under section 4.8, and its rejected controls belong to `blackbox_e2e/checker_controls`.

**Native expectations.** These depend on the machine. The case takes its targets from `S` and observes its prerequisites itself: each attempt target resolves to a regular file the test user can open and read. The expectations are pinned to the present example and change with it.

| Observation | Expectation under the prerequisites |
| --- | --- |
| Completion | `runner_result.normalized_outcome` is `finished` |
| Prediction | `result_source` is `validator`, `outcome` is `allow`, `native_rc` is 0 |
| Order | Given that prediction, `order` is `query_first` |
| Attempt | `outcome` is `ok`, `rc` is 0 |
| Target observation | Each target's digest, length and selected metadata are unchanged between the case's before and after observations |

The case records each resolved target path, a SHA-256 digest and the length of its bytes, and `st_dev`, `st_ino`, `st_mode`, `st_uid`, `st_gid`, `st_size`, `st_mtime_ns` and `st_ctime_ns` before and after execution. Access time is excluded because the observations themselves read the file. A changed target is a `native_observation` failure, not a contradiction in the app's report or evidence that PolicyWitness caused the change. These observations establish equality or difference at the sampled boundaries, not the absence of intervening changes. Section 4.6 governs its disposition.

Nothing in either group states that prediction and enforcement agree.

**Refusals.** Each starts from `S`, makes exactly one change and goes through `run`. The unmodified `S` passes in the same case, so each refusal is attributable to its change.

| Control | Change | Required result |
| --- | --- | --- |
| Other development build | One hexadecimal digit of a `development:` identity changed, or a well-formed `development:` identity substituted when the app is a release build | Exit 1, `bad_request`, `request_failure` with code `unsupported_contract`, path `["contract"]` and `expected_contract` equal to the app's identity; no client capture and no runner reply |
| Other release | `contract` set to `release:v0.0.0` | The same |
| Unbound | `contract` set to `unbound` | The same |
| Absent identity | `contract` removed | Code `missing_field`, the same path and expected identity |
| Truncated document | Closing `}` immediately before the framing LF removed; LF retained | Exit 1, `bad_request`, code `invalid_json`, path `[]`; no client capture or runner reply |
| Unknown member | One unknown top-level member added, identity intact | Exit 1, `bad_request` from the host with code `unknown_field` and a path naming the member; no step results |

The first five stop at the controller. The last shows that a correct identity does not carry an invalid document past the host. Together they show that `run` distinguishes the example from its neighbors, which the app's acceptance of its own example cannot show.

### 4.6 Status, classification and earlier runs

**Status and classification.** The case has two statuses, pass and fail. It declares no skip, and the dispatcher's equipment check does not cover these prerequisites, so no row below is an unrun case. The report's classification carries the distinction the status cannot.

| Situation | Consistency | Native expectations | Status | Classification |
| --- | --- | --- | --- | --- |
| Everything holds | Evaluated, passing | Evaluated, passing | pass | none |
| A consistency assertion fails, at emission, admission or in the reply | Evaluated, failing | Evaluated when an admitted reply and their prerequisites are available | fail | `consistency` |
| The run yields no admitted reply (service unreachable, tool error) | Passage and controller-side assertions only; nothing is credited or faulted from the missing reply | Not evaluated | fail | `execution_unavailable` |
| A target prerequisite is not observed | Evaluated; they do not depend on it | Not evaluated | fail | `prerequisite_unestablished` |
| Prerequisites hold and a native expectation fails | Evaluated, passing | Evaluated, failing | fail | `native_observation` |

More than one classification can apply, and the report lists each.

**Release consequence.** Every failing row fails the default battery and therefore release acceptance; that attempt produces no archive. The classification says where the remedy lies, not whether the release may proceed:

- `consistency` is a defect in the product, the contract's account or the checker. Fix it where it lives; a product or example fix is new shipped source and a new build.
- `execution_unavailable` locates missing execution evidence without assigning a cause. For an observed automation-sandbox refusal, follow the repository's sandboxed-harness guidance: rerun the same command once outside it with the artifact unchanged. A passing rerun supports that explanation and is the run that gets credited.
- `prerequisite_unestablished` is not a PolicyWitness result. The machine cannot run this example's native check, and acceptance belongs on one that can.
- `native_observation` is an observation about this machine or build. Retain the evidence without assigning a cause; the rules below determine whether acceptance needs a correction or a fresh qualifying run.

In no row is the case removed from the default battery, given a skip, or handed another document to obtain a pass.

**Earlier runs and variation.** A failed run remains failed. The following rules determine which earlier failures a fresh qualifying run can supersede and which remain objections to acceptance. They do not change the case's assertions or statuses, add automatic retries, or replace the complete passing default battery required by section 8. Review every failed assertion separately: an interruption does not excuse an independent identity or echo defect.

| Earlier observation | Required disposition |
| --- | --- |
| One reply reports `query_first` and another `unestablished`, each accepted by the consumer | The difference needs no explanation for consistency. The latter run still fails the native order expectation; apply the remaining rows to that failure. |
| A target prerequisite was not observed, the dispatcher recorded system sleep overlapping the failure, or an automation-sandbox refusal was confirmed by the prescribed unchanged-artifact rerun | Record that exclusion and credit a fresh run that establishes the prerequisites and completes without it. Explaining why the target was unavailable, the machine slept or the harness imposed the restriction is unnecessary. Use the existing dispatcher sleep record and sandboxed-harness procedure. |
| The validator produced no answer, with a valid recorded spawn failure or timeout and honest `unestablished` ordering | A complete passing run can supersede this trial without explaining the underlying scheduling or OS cause. The earlier run supplies no successful native-observation credit. Its available evidence must satisfy the consistency assertions; a generic error without evidence locating the failure does not establish this disposition. |
| The validator answered `deny`, or the worker failed `open_read`, while the stated prerequisites were observed | Resolve the challenge to the native expectation through a justified correction to its applicability, a checker correction or a product fix. Later successes alone do not settle it. |
| A target's digest, length or selected metadata changed between observations | Report `native_observation` without assigning a writer. Review target applicability and the observation code, and record the evidence supporting any environmental exclusion or correction. A later unchanged sample alone does not explain the earlier difference; an unsupported disposition leaves evaluation pending. |
| An identity, policy digest, echo or reported-against-observed assertion is wrong, or an existing reader reports an error | Resolve the product, checker or contract discrepancy before acceptance. These must hold even when native execution fails. |

The example must demonstrate successful execution. This work does not require an explanation of every correctly reported inability to execute. A failure without a disposition supported by this table leaves evaluation pending, including a native discrepancy that the table does not cover. Do not infer an exclusion from a later pass or classify every `execution_unavailable` result as environmental.

For failures requiring a correction, the evidence needed to close the issue is bounded:

- **Checker defect:** replay the retained failing input through the corrected checker and show that the affected assertion's rejected control still works. Reproducing the original live event is unnecessary.
- **Product defect:** identify the faulty behavior and establish its correction with a focused control and the applicable verification. Explaining precisely why it occurred intermittently is unnecessary. Changes to section 5's not-touched components remain separate work.
- **Incorrect prerequisite or expectation:** identify the concrete condition that changes applicability and how the case observes it. Passing after a reboot alone does not establish that condition.

Record the failed assertion, the relevant retained observation and its disposition in the evaluation record, with any correction and replacement run. Continue that record through section 9's untagged candidate verification, including dispositions that need no product correction. A new build identity or ten later passes is not itself a disposition; name the relevant change. Preserve original results under the repository's evidence-retention rules rather than rewriting a failed historical run as passing.

### 4.7 Checker controls

**`witness_contract/example_round_trip_controls`** (default; offline). Every assertion that can fail the live case has a stable identifier in the checker. Each failure reports that identifier, its classification and a human-readable explanation. Controls match the identifier and classification; the explanation's wording can change. All of the checker's inputs are retained files, so every assertion can be handed a constructed input that violates it. Build the inputs from the existing constructed-envelope helpers in [blackbox.py](../tests/lib/blackbox.py) and the reply fixtures under `tests/fixtures/contract/`; the case generates no replacement fixtures. A constructed document stands in for `S` here because this case tests the checker, not the app.

The checker and control case establish coverage as follows:

- Start with an input that passes with no failure diagnostics. Each rejected control introduces one logical fault and names its target assertions and the exact expected set of `(assertion identifier, classification)` pairs, authored independently of the checker's output. If the fault necessarily triggers another assertion of this checker, include that consequence explicitly. Missing or unexpected diagnostics fail the control, with only the shared-consumer allowance below.
- A control earns coverage for its target assertions only after the actual diagnostic set matches the expected set under that allowance and includes their failures. Registering or executing a control earns no coverage. For example, changing the producer contract must produce the identity assertion's diagnostic with `consistency`; a generic consumer error alone cannot satisfy that control. Check producer identity before semantic reading; the consumer's version rejection still prevents assertions about the unsupported reply's semantics.
- Report all `consumer.validate` errors under one aggregate assertion, `consumer_validation`, classified as `consistency`, and retain every underlying message. Its dedicated propagation control requires that diagnostic exactly. Other rejected controls permit that one diagnostic in addition to their exact expected set; its presence there earns no coverage. Consumer errors still fail the live case and the passing baseline. The allowance applies only when matching negative-control diagnostics and does not suppress consumer output or permit another unexpected assertion.
- A combined-fault input must retain the diagnostics of its independent faults. Check unevaluated groups explicitly: a missing prerequisite requires `prerequisite_unestablished` and native expectations not evaluated; a missing admitted reply requires `execution_unavailable` and no credit or fault from the absent reply. A rejection alone does not establish these results.
- The completeness assertion compares the checker's full assertion table with the identifiers whose targeted controls actually matched, plus the documented exceptions resting on other evidence below. An assertion without verified coverage or a documented exception fails the case. The control results retain expected and actual diagnostic sets and the identifiers that earned coverage.

| Group | Rejected controls required |
| --- | --- |
| Emission | A nonzero version exit; either emission exits 2 with otherwise valid stdout; nonempty emission stderr; malformed or non-object JSON; a missing or extra framing LF. Each prevents submission and leaves dependent run assertions unevaluated |
| Passage | The version identity differs; the property-list identity differs; the identity is not in a packaged form; two emissions differ; `bytes_written` differs from the document's length without its framing newline; a member differs from the contract's rendered example |
| What the case will run | An empty plan; a plan without a paired probe; a write action; an exec action; test overrides; a runner selector; augments; a required entitlement; phases in place of the plan |
| Admission | A `request_failure` or `bad_request` outcome; each policy digest differing |
| Identity | Each of the three identities differing, separately |
| Echo | The echoed `specimen_id` differs; an extra, missing or renamed step; the query echo differs; the attempt echo differs |
| Reported against observed | The captured exit differs from `result.exit_code` |
| Existing readers | The dedicated consumer propagation control; `disposition_integrity` not `valid`; a nonempty `disposition_issues` |
| Native | A coherent `validator_spawn_failed` reply with a missing prediction and honest `unestablished` ordering; a prediction other than `allow`; an attempt that failed; a changed target digest, length or selected metadata with the envelope unchanged. With prerequisites held, each must produce `native_observation` with consistency still passing. An unobserved prerequisite must produce `prerequisite_unestablished` with native expectations not evaluated |
| Refusals | For each refusal control: an accepted run in its place; the wrong code or path; a missing or wrong expected identity where section 4.5 requires one; a client capture on a controller-side refusal |
| Classification | A combined-fault input reports every fault; an attempted run with no admitted reply is `execution_unavailable` and credits or faults nothing from the reply |

The coherent `validator_spawn_failed` control has matching reported and captured exits of 1 and a clean consumer reading. It fails the native completion and prediction expectations without failing consistency. A second control changes only its captured exit to 0 and must add the reported-against-observed diagnostic under `consistency` while retaining the native diagnostics. This establishes that a nonzero exit alone is not a consistency fault.

Two things rest on other evidence, and the suite account says so:

- Shape and record validity, including ordering and the envelope-result relationship added in section 4.8, come from `consumer.validate`, whose rejected controls belong to `blackbox_e2e/checker_controls`. This case's propagation control requires `(consumer_validation, consistency)` and establishes that a consumer error fails the case; incidental consumer diagnostics in other controls do not cover it.
- That the app is validly signed and unchanged comes from the dispatcher's inspection and inventory, controlled in the `dispatcher` suite.

### 4.8 Other controls

**Consumer result consistency.** Extend `consumer.validate` for admitted runner replies: `result.normalized_outcome` equals the reply's outcome, `result.ok` is true exactly for `finished`, and `result.exit_code` is 0 for `finished` and 1 otherwise. Apply this behind the existing version and reply-admission boundaries; a body retained after admission failed cannot supply the mapping, and controller failures without an admitted reply keep their own result rules. Add controls to `blackbox_e2e/checker_controls` for valid finished and non-finished admitted replies, each envelope result field changed independently, and combined faults alongside existing record errors. Keep the refusal and unsupported-body controls passing. These are consumer assertions; the example checker only propagates the consumer's result and compares the reported exit with the process exit it observed.

This rule checks the present outcome-to-result mapping. It does not decide whether controller integrity findings should change command success. Preserve that open question, currently `envelope.data.select.success_findings`, in the evaluation and handoff; stronger verification of current behavior does not resolve it or authorize a product change.

Determine applicability from the version, transport and reply-admission evidence independently of the result fields being checked. Changing only `result.normalized_outcome` to `tool_error` or a refusal spelling must not disable the relationship. Require all three result fields with their proper JSON types; controls remove them, set them to null and substitute booleans for integers or integers for booleans. Distinguish admission failures from later record errors: a retained reply rejected for its compiled-profile context supplies no outcome mapping, while an admitted reply with an unrelated record error must still expose an independent result mismatch. Preserve both diagnostics in that combined control. Controls also cover absent replies and rejected client captures without deriving outcomes from their retained bytes.

The new rule reaches every existing reader of an envelope, not only this plan's cases: 35 tracked test files call the consumer's readers. Constructed envelopes need attention first. [`envelope_skeleton`](../tests/lib/blackbox.py) sets `result.ok` and `result.exit_code` from an `ok` argument that defaults to true whatever the reply's outcome, and it has five call sites, three of which pass `ok` explicitly. Derive the skeleton's result from the reply's outcome, or correct each caller, so that a constructed envelope states a coherent result unless its control is about that incoherence. Correct accidental fixture mismatches and state the correction; preserve deliberate result faults and require their diagnostics. Do not normalize the result in `consumer.validate` or repair a control after its deliberate mutation. A fixture correction is not a reason to narrow the rule.

Summarize fixture corrections in section 6's evaluation record. For each correction, name the affected helper and cases, the original incoherence, what changed, the intended assertion and the deliberate faults whose rejection remains verified. Cite their control identifiers, expected diagnostics and results. Corrections sharing one helper fix and cause can share an entry with all affected cases named. This summary lets a later reviewer distinguish repaired incidental envelope fields from a weakened control without reconstructing the entire diff.

**Cross-build controls** extend [cli_contract.rs](../controller/integration/cli_contract.rs), which already builds isolated non-test controllers with supplied and absent stamps. The unbound build's `example` exits 2 with empty stdout. The build given another identity emits that identity, and the signed app's `run` refuses the resulting document with `unsupported_contract` and its own expected identity. The same file takes the usage rows of section 4.2 against the signed app.

**Generation controls** go in the existing `source_drift` cases, over disposable source copies:

- The example constant edited without regeneration is refused by `--check`, which names the stale outputs and writes nothing.
- After regeneration, the rendered contract, the `request` surface payload and `build_contract.identity` all differ.
- The extraction refuses, naming the source: a missing symbol; two definitions; a constant that is not a raw string; a value that is not a JSON object; a `contract` member; `_test_overrides`; a selection key; an unknown top-level member.

**Unit tests** in the controller cover the renderer under test, development and release identities and one that needs escaping; the gate's typed refusals for an unbound identity and an unparsable constant; and dispatch. Writer controls cover short writes that eventually complete, a failure after partial output, and a flush failure after all bytes have been accepted; only complete output with a successful flush exits 0. The gate takes the document and the expected identity as parameters, so the tests match the returned reason and not a message. Extend the existing controlled orchestration tests in `run_flow.rs` to write the emitted example as the input file, call the actual `run` path, and capture the exact request at `RunDependencies.client`. It must equal the emitted bytes after removing exactly one trailing newline. This checks the chosen example through real augmentation resolution and selector removal under `test:policy-witness`; rendering other identity spellings does not extend that orchestration evidence to signed builds. It neither constructs another specimen nor reimplements the Rust serialization in another language; the app root, manifest and client remain controlled as in the existing tests.

**One implementation challenge before evaluation.** In a disposable worktree, change only the emitter's serialization from `serde_json::to_string_pretty` to `serde_json::to_string`, leaving `run`, the example constant and the tests unchanged. Run `tests/run.sh --case unit/rust.unit` on the baseline, mutation and restoration, with a fresh output directory for each. The baseline and restoration must pass; the mutated run must reach and fail the exact emitted-document/client-request equality assertion. An earlier refusal, build failure or unrelated assertion failure alone earns no credit. Retain the source snapshots, minimal patch, commands, logs and named comparison failure in the evaluation evidence. This is one experiment using the existing case, with no new specimen, production instrumentation or mutation harness. Its evidence remains scoped to preparation under the test identity.

### 4.9 Test boundary

| Stage | What is checked | Equipment | Home |
| --- | --- | --- | --- |
| Generation | Extraction and its refusals, stale rendering, stamp and identity sensitivity | Python | `source_drift` (existing cases) |
| Compilation | Rendering, exact request bytes at the controlled client boundary through `run` under the test identity and sensitivity to the serialization mutation, gate, write and flush behavior, dispatch | Cargo | `unit/rust.unit`, `unit/rust.fmt` |
| Packaging | No new layout or build step. Existing gates: generator check before compilation, identity recomputation before signing | Build toolchain and identity | `make build`; `preflight/build_refusal_controls` at candidate entry |
| Signed-app inspection | Usage rows, cross-build controls | Signed app; Cargo for the isolated builds; no XPC | `integration/cli.integration` |
| Checker | Matched rejected controls and completeness | Python | `witness_contract/example_round_trip_controls` |
| Shared consumer | Admitted reply-to-envelope result mapping, independent and combined faults, preserved refusal boundaries | Python | `blackbox_e2e/checker_controls` |
| Actual execution | Passage, admission, identity, echo, existing readers, native expectations, refusals through `run` | Signed app and XPC | `witness_contract/example_round_trip` |

Only the last row observes native execution, and only its native group depends on the machine. Both new cases are default members: they are read-only, need no signing identity, GUI session or network, and add a handful of CLI invocations. Default membership places the live case in release acceptance with no further wiring.

## 5. Affected components

| Area | Files | Change |
| --- | --- | --- |
| Controller | `controller/src/example.rs` (new), `main.rs`, `cli.rs`, controlled tests in `run_flow.rs`, `controller/README.md` | The constant, the command, unit tests including exact client-boundary capture, usage and CLI block |
| Contract authoring | `docs/contract/10-request.surface.md` | The rule and the example node, with support |
| Contract model | `docs/contract/tree.py`, `README.md`, `AGENTS.md`; `docs/generate_contract_stamps.py` | The `document` fact, its extraction, validation and rendering; the cited source as a declared input; authoring reference |
| Generated | `docs/CONTRACT.md`, `docs/contract/public.json` | Regenerated, never hand-edited |
| Tests | `tests/catalog.json`; `tests/suites/witness_contract/` (two case scripts, one checker, README); `tests/lib/consumer.py`; `tests/lib/blackbox.py` and the constructed controls that call `envelope_skeleton`; `tests/suites/blackbox_e2e/checker_controls.py` and README; `controller/integration/cli_contract.rs`; `tests/suites/source_drift/` (`contract_tree_controls.py`, `generators.py`, `build_contracts.py`); `tests/README.md`, `tests/COVERAGE.md` where applicable | Cases, shared outcome-consistency checks and controls, registry and suite accounts |
| Guide | `docs/PolicyWitness.md` | One row in the command table |
| Possibly | `docs/architecture.json` | Only if its account enumerates CLI entries; check and regenerate if so |

Not touched: `build.sh`, `meson.build`, `build_contract.py`, the bundle layout, the evidence manifest, the wire schema, the host, the worker, the validator, the dispatcher and `runner verify`. A need to change any of these is a signal to stop and reconsider, not a routine extension.

## 6. Order of implementation

**Step 0. Return the stamps to `unreleased`.** Follow the `d18d4925` precedent so the tree can be generated, built and tested. Done when `generate_contract_stamps.py --check --require-history` passes and the three stamp artifacts are the only difference from the starting commit.

**Step 1. The example and its account, together.** Add the module and command with their unit tests, including exact request capture through the existing controlled `run` path, usage text and README block; extend the tree with the `document` fact; author the rule and the example node, with an explicit evidence gap until the checks exist; regenerate; add the generation controls. The command does not land without the contract's statement of it. Done when `--tree-check` and `--check --require-history` pass and `tests/run.sh --suite unit --suite source_drift` passes outside the automation sandbox.

**Step 2. Signed build and CLI checks.** Build through the signed pipeline, then add the usage rows and cross-build controls. Done when `tests/run.sh --suite integration` passes against that build.

**Step 3. The round trip.** Add the missing envelope-result relationship to the shared consumer and its controls, then write the example checker, its offline controls and the live case; register both new cases; update the suite accounts. Done when `blackbox_e2e/checker_controls` and both new cases pass by `--case` against the step 2 build with a fresh `PW_TEST_OUT_DIR`, and the control case's completeness assertion accounts for every assertion identifier through matched expected diagnostics or documented other evidence under section 4.7. Because the consumer is shared, also run a complete default battery against that build before the evaluation point; a case that newly fails on the result relationship is reviewed as section 4.8 describes.

**Evaluation point.** Stop here and present the first complete result before anything else is built on it: the emitted document, the version envelope, the run envelope, the refusal inputs and outputs, and the checker's report with its groups. Before presenting, run the live case ten times against the same build, each with a fresh output directory, and report every assertion's result and each failure's disposition under section 4.6. This is a bounded evaluation sample; do not restart it to obtain ten consecutive passes. Record subsequent corrective or replacement runs separately, including changes to their inputs, build or operating conditions.

**One independent evaluation review.** Before sharing the authors' interpretation or acceptance recommendation, give a reviewer in a fresh context the settled constraints, confirmed commitments and declared evidence scopes, implementation and tests, source/build identities, and raw captures and checker/control results, including failed trials and the serialization challenge. Withhold the authors' diagnoses, proposed failure dispositions and prior review conclusions until the reviewer records an initial assessment: which promises the evidence establishes, which remain unsupported, and what observation would change that assessment. Preserve that initial response before sharing the withheld material, then record the authors' response and the disposition of consequential disagreements in the existing evaluation record. The maintainer makes the evaluation decision below; this review adds no separate approval checkpoint or set of investigation records.

Passing tests are necessary here and not sufficient. Failures awaiting a disposition under section 4.6 leave evaluation pending and prevent step 4. The maintainer decides, on these criteria.

*Accept, and go on to step 4, when all of these hold:*

- The two commands in section 1 work from the usage text alone.
- The passage is direct: the command's output comes from the one constant through the functions `run` uses, with no intermediate copy, generated source or build step. The exact string captured at the controlled client boundary equals the emitted document without its framing newline; the live delivery-length observation is credited separately.
- The serialization mutation fails that exact comparison, with passing baseline and restoration, and the independent review's consequential findings have recorded dispositions within the stated evidence scopes.
- The fixtures author no specimen. The live case contains no document and independently requires a nonempty plan with a paired, read-only probe, in addition to the execution bounds and native expectations pinned to the present example.
- The checker restates no interpretive rule owned by the consumer or controller. The shared consumer's outcome-consistency controls establish the newly assigned relationship.
- Nothing answers whether PolicyWitness accepts a shape except `run`.
- The final build has a complete passing live case, and every earlier failed assertion has a disposition supported by section 4.6. Different values supported by each reply's evidence do not themselves fail evaluation.
- A deliberately faulted input produces a diagnostic that names the assertion and the classification without a reader opening the checker.
- Nothing in section 5's not-touched list changed, the free-text baseline did not grow, and no harness machinery was added.

*Revise, keeping the design, when:*

- An assertion compares the envelope only with itself, or duplicates a consumer rule.
- The usage text, exit statuses or printed form are awkward in use.
- The report blurs consistency and native observations, or a failure is hard to attribute from the report.
- The byte comparison fails because the chosen example contains a preparation input such as an augment, or because the assertion mishandles framing or encoding. Correct the constant or assertion and rerun the actual preparation path; do not infer a defect in `run` from the mismatch alone.
- Evidence establishes a checker defect or a concrete condition requiring correction to a native expectation's applicability. Make and verify that correction under section 4.6; variation alone does not establish incomplete prerequisites.
- The work needed an evidence gap or a deviation from this plan that the maintainer has not seen.

*Stop, and reconsider the design, when:*

- A not-touched component had to change.
- After accounting for the example's restrictions and its framing newline, exact request capture establishes an unexpected transformation in `run`'s preparation. Investigate that behavior separately before changing the production path. `run`'s intended augmentation and selector handling are not defects merely because they transform other requests.
- The case could pass only by carrying a specimen of its own or by re-running a production classifier.
- The work called for a second way to ask what `run` answers.
- The rule cannot be authored without free-text growth and the maintainer does not want the baseline raised.

**Recording the decision.** In the commit that completes step 3, the executor adds an "Evaluation record" section to this plan: the build identity and commit, the run identifiers with their availability (development evidence, disposable), the control case's verified coverage, the serialization challenge, the independent review's initial assessment and the subsequent responses and dispositions, the ten-run comparison, each failed assertion with its relevant observation and disposition, any correction and replacement run, and every deviation from the plan. The maintainer's decision goes into that section in its own commit, in the maintainer's words: accept, revise with the changes listed, or stop with the reason. Step 4 does not begin before that commit exists.

Continue the same record through section 9. For each later disposition, append the verification stage, case and failed assertion, failed and replacement run identifiers, applicable build identities, supporting observation and disposition. Commit the evidence update even when no product correction was needed. Later entries preserve the step 3 decision and make subsequent verification available for candidate review.

End the evaluation record with a short, current handoff statement: the final supported source commit and the commits completing implementation and support, the selected app's source snapshot (commit and worktree state) and embedded identity, the applicable verification, completed support work, and unresolved decisions or failure dispositions (explicitly none when there are none). Record later evidence-only commits separately. Distinguish matters that block dependent investigation from release work that may remain pending. Update the statement after step 4 and whenever later work changes readiness; it summarizes the existing decisions and evidence and adds no approval checkpoint. An unchanged development digest does not establish that verification remains applicable: account for changed consumers, fixtures and tests when carrying evidence forward.

**Step 4. Support and accounts.** Replace the evidence gap with owners that cite the constant, the emitter and the checks, with their limits stated; regenerate. Owner metadata is outside the public payload, and these support edits do not change the development digest inputs. Confirm that the `development:<sha256>` identity is unchanged from the step 3 build, and update the handoff statement with the completed support work and its commit.

At that point, when relevant decisions and failure dispositions are settled, the controller investigation can begin against the recorded baseline; step 5's candidate rehearsal may remain outstanding. Coordinate its evidence review while the disposable artifacts are available, within the existing retention rules. Record later source, contract, consumer, fixture or test changes affecting that baseline and reassess evidence applicability before carrying credit forward. The unresolved product question about integrity findings and success remains distinct from a failure to verify today's mapping.

**Step 5. Candidate verification** (section 9).

## 7. Anticipated failure modes

| Failure | Sign | Response |
| --- | --- | --- |
| The automation sandbox refuses XPC lookup, signing or native-builder queries | `xpc_error`, an empty keychain listing, refused `sysctl` reads | Follow the repository's sandboxed-harness guidance: rerun the same command once outside the sandbox, unchanged. Do not weaken the case |
| The app predates an example edit | The live case reports that the emitted document differs from the contract's rendering | Rebuild. This is the intended stale-app refusal |
| The strict extraction is defeated by ordinary Rust formatting | Generation refuses a valid constant | Keep the constant in the one form the reader accepts and say so beside it; do not widen the reader into a Rust parser |
| The rule needs a `free.*` fact | Generation refuses free-text growth | Restructure the rule; otherwise stop and raise it |
| The host refuses the example | The live case fails at admission with a `request_failure` | The example is invalid for this build. Fix the constant; do not relax admission |
| A target is unreadable or absent | The case fails as `prerequisite_unestablished` | Section 4.6's release consequence. Do not hand the case another document |
| A target's digest, length or selected metadata differ after the run | The case fails as `native_observation` while a consistent envelope still passes its readers | Record the sampled change and follow section 4.6 without attributing a writer or treating it as a false app report |
| The prediction is unavailable with a valid recorded spawn failure or timeout | The case fails as `native_observation` while consistency passes | Apply section 4.6's earlier-run rules: a complete passing run can supersede the trial without diagnosing the underlying OS cause |
| The prediction is `deny` or `open_read` fails with prerequisites established | The case fails as `native_observation` while consistency passes | Resolve the challenge to the native expectation under section 4.6; later successes alone do not settle it |
| A passing checker that checks nothing or rejects for the wrong reason | The offline controls accept a faulted input or its diagnostics differ from the expected set | Match each control's intended diagnostics and classification before crediting coverage; preserve independent combined faults and check unevaluated groups |
| The case passes against a release-form identity only by string luck | The identity-form assertions never see a `release:` value | Covered at candidate entry by the nested acceptance, whose fixture reports a release identity |
| The consumer's new result rule fails cases outside this plan | Constructed controls or live cases elsewhere in the battery report a result that disagrees with the reply's outcome | First establish that the reply was admitted and the reader applied the rule correctly. Correct accidental fixture mismatches and preserve deliberate faults under section 4.8. A confirmed mismatch in a live admitted reply is a product finding about result assembly and comes before this plan |
| The checker grows back into a second specification | New assertions about ordering, vocabulary or outcome mapping appear in it | They belong to the consumer. Add them there with its controls, or not at all |
| The dispatcher's inventory differs after the case | Artifact-integrity failure | The command wrote into the app; it must not. Fix the command |

## 8. Acceptance criteria

1. In the `unreleased` stamp state, `generate_contract_stamps.py --check --require-history` passes, and a second generation writes nothing.
2. A signed development build of the final source prints, for `example`, a document whose `contract` equals `--version`'s `build.contract` and the app's `PWContract`. The live case requires at least one paired, read-only probe. `run` on the emitted file is admitted, reports delivery of the document's byte length without its framing newline, and exits 0 with `finished`. Separately, the controlled orchestration test establishes exact equality between the emitted document without that newline and the string passed to the client through the actual `run` preparation path.
3. `witness_contract/example_round_trip` and `example_round_trip_controls` pass inside a complete default battery with no skips, unrun cases or harness errors, and with the app inventory unchanged. The live case's artifacts hold the emitted bytes, the version envelope, the run envelope, every refusal input and output, the target-file observations, and a report giving each assertion's result and each failure's identifier and classification, consistency apart from native observations. The offline case retains expected and actual diagnostic sets and verified coverage under section 4.7.
4. Each refusal control in section 4.5 produces its stated code, path and expected identity through `run`, and the controller-side controls show no client capture.
5. The cross-build controls pass: the unbound build emits nothing and exits 2; the signed app refuses a document emitted under another identity.
6. The generation controls pass: an example edit is refused until regeneration and then moves the rendering, the stamp and the build identity.
7. The contract's rendered example equals the app's emitted document without its identity.
8. Every component in section 5's not-touched list, and the worker identity, are unchanged from the starting commit.
9. The repository contains one definition of the example. No test, fixture or document holds a copy that is not extracted from it.
10. `blackbox_e2e/checker_controls` establishes the shared consumer's admitted reply-to-envelope result mapping, including independent and combined faults, without interpreting retained inadmissible bodies. The example checker propagates that reader's errors and contains no duplicate mapping.
11. The evaluation record retains the serialization challenge's passing baseline, targeted failure and passing restoration, and the independent review's original assessment and subsequent dispositions. The handoff after step 4 identifies the supported baseline and preserves the distinction between current conformance and unresolved product decisions.

## 9. Entering the 0.3.8 candidate

Earlier pre-tag evidence does not carry over. This work changes the CLI, the build-identity inputs, the contract tree and its generator, so the rehearsals recorded for `8435e5d3` describe a different build. The following are required on the final source, in the `unreleased` state, before the work is treated as part of the candidate:

1. A signed development build, and a complete default battery against it (about half an hour on this machine as of 2026-11-11).
2. The complete `preflight/build_refusal_controls` rehearsal (about two and a quarter hours), because the generator and its inputs changed. Its nested extracted-ZIP acceptance runs the default battery, including the new live case, against a fixture that reports a `release:` identity. That run is this plan's evidence for the release form; record the identity the case saw.
3. A reviewed applicability statement for `witness_contract/order_barrier_mutations`: it is not required if the worker wait, release store and eligibility rule are untouched, which criterion 8 and an unchanged worker identity support. State this as a judgment, not as a mechanical fact.
4. Confirm that the evaluation record includes the candidate battery and rehearsal results and all later dispositions, with their replacement runs. Commit any outstanding evidence update, including when no product correction was needed. Then prepare again: `generate_contract_stamps.py --release v0.3.8 --require-history`, changing only the two stamp tables and the snapshot history; confirm that the ordinary check gives exactly the expected missing-tag refusal; run the same prepared-commit checks as before (baselines against `v0.3.7`, footprint attribution).
5. Revise the prepared notes in [RELEASE-NOTES-v0.3.8.md](../records/contract/RELEASE-NOTES-v0.3.8.md): the `request` row gains an additive command, and the verification paragraph cites the new runs with their scopes.

The plan ends at that prepared, untagged state with the maintainer's review pending. Its disposition-recording procedure covers this untagged candidate work; it does not alter the [tagged-release checkpoint rules](../records/contract/RELEASE-INPUTS.md#checkpoint-rules-the-release-procedure-does-not-state), including restrictions on working-tree writes and the correcting-commit procedure. Tagging, the tagged rehearsal, notarization and publication are separate decisions and are not steps here. If the maintainer prefers to tag 0.3.8 without this work, steps 0 to 4 can equally sit on a branch of the `unreleased` state; nothing in the design depends on the release number.

## 10. Commitments

**Settled with the maintainer on 2026-11-12.**

| Commitment | What it means in practice |
| --- | --- |
| One way to hold PolicyWitness | No admission query or second submission path, here or later on this route. `example` answers nothing about a caller's document |
| The app is the authority for the example | One definition in controller source; the contract extracts it; tests obtain it from the built app |
| A narrow public guarantee | Successful emission gives a document the same build admits through `run`. Content, layout and labels carry no stability promise between builds. The command is public and currently intended for project verification |
| Every failure to emit is exit 2 and requires discarding stdout | Usage errors, an unbound build, a failed gate and a failed write share one status; the reason is stderr text. A write failure does not establish exactly which bytes reached the caller |

**Confirmed by the maintainer on 2026-11-12, before step 1.** Each creates behavior a caller can see.

| Distinction | Why it matters | Commitment |
| --- | --- | --- |
| The command prints a bare specimen, in the controller's held serialization, not an envelope | It is the first controller output that is not an envelope, and its key order is the serializer's, not an author's | `example` output is a request document with one trailing framing newline; `run`'s held request omits that newline. Envelopes remain the form of every report |
| The command is listed in usage, stated in the contract and listed in the user guide's command table | A reader of the guide learns that the command exists and what its exit statuses mean, while the guide's worked examples still use hand-substituted identities | The entrance is disclosed in each place and its target remains project testing; presentation as a workflow waits for the purpose-built help and example interface |
| Native expectations fail the case when their prerequisites hold | A machine where `sandbox_check` gives no answer for this read fails the default battery and release acceptance, subject to section 4.6's dispositions | The battery asserts the native result only under observed prerequisites, and reports it apart from consistency |

## 11. Where this stops, and the route onward

Out of scope: more than one example, selection by name, external runner examples, expected-refusal examples, response fixtures, any documentation interface, and any query other than `run`.

Possible later steps keep the same direction, from code to presentation; they are not prerequisites or promised follow-up work:

- **The guide and README.** Their hand-substituted `BUILD_CONTRACT` examples can shrink to the two commands in section 1 when the purpose-built help and example interface is planned. That is the point at which the promise in section 10 is reconsidered.
- **The verify request.** `verify_request()` and the contract's `apply_only` example may share storage or extraction later if that removes useful duplication. Verification's apply-only request serves a different purpose from the paired example, and its behavior need not be unified with this command. No such refactor is required by this plan.
- **A second example.** It needs a way to select among examples and, with that, a statement of what a selection denotes across releases. Neither is designed here.
- **Refusal examples.** A document the app prints so that `run` refuses it would let refusal guidance come from the app as well. Its expected outcome is obtained by running it, in keeping with section 2.
- **Support grade.** After an archived release acceptance includes the live case, the example's owner can move from `check_read` to release credit naming that release and case.

## 12. Evaluation record

Recorded by the executor on 2026-11-12 at the evaluation point. Every run named here is development evidence under `tests/out/runs/` or in the challenge worktree: it is disposable under the retention policy and is not retained release evidence.

### Source and build

| Item | Value |
| --- | --- |
| Final supported source | `23440049`, clean working tree |
| Implementation commits | `89f9d121` (step 0), `de17cef7` (step 1), `7f1fcb8b` (step 2), `6c9f11da` (step 3), `c188ffb4` and `23440049` (corrections after review) |
| Selected app | `dist/PolicyWitness.app`, built by the signed pipeline from `23440049` with a clean tree; `PWBuildDescribe` is `v0.3.7-34-g23440049` |
| Embedded identity | `development:6a333cf6f19aea6939fa843655b6ce2a90ec05837fb4bb6b8b9288b0ccc572f0`, equal to what `docs/build_contract.py` derives from the source |
| Earlier builds | `de17cef7` gave `development:06501fd5…8923`; `c188ffb4` gave `development:8627b82f…e504`. Evidence from them is not carried to the final build |

### Runs

| Output directory | Run | Selection | Source and build | Result |
| --- | --- | --- | --- | --- |
| `example-step1-a` | `20261113T002356Z_28ce9ecf` | `unit`, `source_drift` | Working tree later committed as `de17cef7` | Failed, 13 of 14; disposition below |
| `example-step1-b` | `20261113T003211Z_06171dc8` | The same | Working tree later committed as `de17cef7` | Pass, 14 of 14 |
| `example-step2-a` | `20261113T004110Z_7995238e` | `integration` | Build of `de17cef7` | Pass |
| `example-step3-a` | `20261113T005552Z_7b966617` | `blackbox_e2e/checker_controls` and both example cases | Working tree later committed as `6c9f11da`; build of `de17cef7` | Pass, 3 of 3 |
| `example-step3-battery-1` | `20261113T005633Z_a4410175` | Default battery | `6c9f11da`; build of `de17cef7` | Pass, 231 case results |
| `example-eval-01` to `-10` | `…998977e8` to `…ae06eac7` | Live case, ten times | `6c9f11da`; build of `de17cef7` | Pass, 10 of 10 |
| `example-fix-unit-drift` | `20261113T014053Z_edb14980` | `unit`, `source_drift` | Working tree later committed as `c188ffb4` | Pass, 14 of 14 |
| `example-fix-cases` | `20261113T014824Z_cfd718de` | `integration` and the three cases | `c188ffb4` and its build | Failed, 3 of 4; disposition below |
| `example-fix2-unit-drift` | `20261113T014921Z_6172d5cb` | `unit`, `source_drift` | Working tree later committed as `23440049` | Pass, 14 of 14 |
| `example-fix2-cases` | `20261113T015638Z_e8188171` | `integration` and the three cases | `23440049` and its build | Pass, 4 of 4 |
| `example-final-battery-1` | `20261113T015713Z_2e6b9fd5` | Default battery | `23440049` and its build | Pass, 231 case results, no skip, unrun case or harness error, inventory unchanged, no system sleep recorded |
| `example-final-eval-01` to `-10` | `…9aeeaa60` to `…a52e9e15` | Live case, ten times | `23440049` and its build | Pass, 10 of 10 |

Runs marked "working tree later committed" started before their commit existed; no run record states a source snapshot, and their applicability rests on the tree having been committed unchanged. The final battery, `example-fix2-cases` and the final ten runs ran on the clean tree at `23440049`.

### Control coverage

In the final battery `witness_contract/example_round_trip_controls` matched 190 of 190 rejected controls and covered 67 of 67 assertions, with passing baselines under a development and a release-form identity and seven controls of the checker's prepare step. Its artifact `example-round-trip-controls.json` holds each control's expected and actual sets and the coverage it earned. The case spells every expected classification itself and fails if the checker's table differs. Each native assertion, the prerequisite assertion and the execution assertion has at least one matched control that the consumer reads without error. Six assertions can only be violated together with a consumer diagnostic, which the allowance of section 4.7 permits: the three identity assertions, the step-identifier and query echoes, and the consumer's own aggregate, whose propagation control requires it exactly.

`blackbox_e2e/checker_controls` ran 134 result-consistency controls for the shared consumer. Shape and record validity rest on that case; that the app is validly signed and unchanged rests on the dispatcher's inspection.

### Serialization challenge

The disposable worktree `PolicyWitness-example-challenge`, beside this checkout, holds the runs; the directory `PolicyWitness-example-challenge.evidence` beside it holds the patch, source hashes, commands, console logs and the named failure. The challenge was run at `6c9f11da` and repeated at `23440049`, with the same outcome.

| Step at `23440049` | Run | Result |
| --- | --- | --- |
| Baseline | `20261113T022155Z_0dd7c933` | `unit/rust.unit` passes |
| One line of the emitter changed from the pretty serializer to the compact one | `20261113T022159Z_39f2cd98` | 241 tests pass and one fails: the controlled orchestration test for the emitted example, at its comparison of the client's request with the emitted document |
| Restoration, with source hashes equal to the baseline's | `20261113T022201Z_89d8e260` | `unit/rust.unit` passes |

This evidence concerns request preparation under the test identity and ends at the client callback. It does not establish exact delivery by a signed binary.

### Ten-run comparison

The bounded sample ran on the build of `de17cef7`: ten of ten runs passed, with all 67 assertions holding in each, every prediction a validator `allow`, every order `query_first` and every attempt `ok`. After the corrections a second sample of ten ran on the final build with the same results; it is recorded as replacement evidence for the changed build, not as a restart of the first. Neither sample contains a failed or unevaluated assertion, so no disposition under section 4.6 was needed. Both samples ran back to back within about half a minute each on one machine under one operating condition. They give no information about variation such as an `unestablished` order.

### Failed runs and their dispositions

| Run | Failure | Disposition |
| --- | --- | --- |
| `example-step1-a` | `source_drift/generator_contract` reported three unlisted citation pairs, all in this plan | A defect in this document's prose, unrelated to the command. The text is present at the starting commit, from which the executor infers the case was already failing there; it was not run at that commit. `3bb0955f` rewrote the three mentions as symbol links; `example-step1-b` is the replacement run |
| `example-fix-cases` | The new integration test required exit 2 for a stdout closed at launch; the app exited 0 | An incorrect expectation written by the executor. On that build the write to descriptor 1 succeeded, so the launch condition behaves as a redirect to the null device and exit 0 supplies what the system accepted. `23440049` removed the expectation and the direct descriptor write that accompanied it; `example-fix2-cases` is the replacement run |

Local runs of the two control scripts outside the dispatcher failed several times on mistakes in the controls while they were being written. They are not retained and earn no credit. One direct `cargo test` during step 1 ran outside the checkout lock helper; it was local debugging and earns no credit.

### Independent review: initial assessment

A reviewer in a fresh context received this plan, the diff from `c6345219` to `6c9f11da`, the source and build identities, the raw runs and the serialization challenge evidence. The authors' diagnoses, failure dispositions and acceptance view were withheld. The assessment below is preserved as received on 2026-11-12, before any of that was shared and before any correction was made.

```text
Initial assessment: `policy-witness example` at 6c9f11da, plan evaluation point (section 6)

All evidence runs but `example-step1-a` passed, including 12 live round trips with 67 of 67 assertions each. I found one product behaviour that contradicts a confirmed commitment (exit 101 instead of 2) and several places where the controls prove less than the plan and suite README say.

What I did: read the plan, the full diff `c6345219..6c9f11da`, the checker, both control files, the consumer changes, and the raw artifacts of every listed run. I ran only read-only commands:
- `example`, `--version` and `example x` on the dist app, including with closed pipes;
- `generate_contract_stamps.py --check --require-history` and `--tree-check`, and `build_contract.py`;
- `codesign --verify`;
- the checker on copies of a retained capture in my scratch directory.

One command of mine was refused by the permission system before it executed. It would have copied the controller binary to scratch and invoked `example` and, wrongly, `run` on the copy. Nothing ran, and I did not retry.

## Identity and applicability (verified)

- **Identity:** the app's `PWContract`, `--version` `build.contract` and `data.contract`, and `docs/build_contract.py` at HEAD all give `development:06501fd5…8923`.
- **Source since the build:** no `controller/src` or `runner` file changed after de17cef7. Later commits touch only `controller/integration/cli_contract.rs`, tests and READMEs.
- **Build:** the app was built at 16:40:27 from de17cef7 (`PWBuildDescribe v0.3.7-29-gde17cef7`, no dirty marker). `codesign --verify --deep --strict` passes.
- **Runs on an uncommitted tree:** `example-step1-a`, `step1-b`, `step2-a` and `step3-a` started before their commits existed. Every file in the diff has an mtime earlier than the run that credits it, and the tree is clean now. I infer those runs saw the committed bytes; no run record states a source snapshot.
- **Runs after the final commit:** `example-step3-battery-1` (16:56:33) and the ten eval runs.
- **Limit:** the app is a build of de17cef7, not of the final commit; only its contract-identity inputs are equal. Criterion 8.2's "build of the final source" holds in that sense only.

## 1. Established

- **Section 1 commands on the signed development app.**
  - Twelve live runs (`example-step3-a`, the battery, `example-eval-01`…`10`) each report 67 of 67 assertions passing.
  - Recomputed from raw captures:
    - emission is 555 bytes, byte-identical across both emissions and all runs;
    - `bytes_written` is 554;
    - envelope, client-capture and reply-producer identities equal the document's;
    - both policy digests equal SHA-256 of the policy source;
    - the prediction is validator/allow/0, order is `query_first`, the attempt is ok/0, and the result is `finished`, ok, exit 0, with integrity valid;
    - target observations are equal before and after.
  - Replaying `example-eval-05`'s capture in a scratch copy reproduced its `report.json` exactly.
  - Scope: one machine, one development identity; the ten eval runs fall within 27 seconds, back to back.
- **Exact preparation fixed point, test identity only.** `emitted_example_reaches_the_client_as_the_emitted_document` (`controller/src/run_flow.rs` ~2806–2828) passes in step1-a, step1-b, the battery and the challenge baseline and restoration. It ends at the `RunDependencies.client` callback under `test:policy-witness`, as section 4.1 declares.
- **Serialization challenge.** In `/Users/raccoon/Desktop/Security/PolicyWitness-example-challenge.evidence/`:
  - the patch is one line;
  - baseline and restoration hashes of `example.rs` and `run_flow.rs` equal main's;
  - the mutated run fails only that test (241 passed, 1 failed) at `run_flow.rs:2824:13`, the request/document `assert_eq!`, pretty on the left and compact on the right.
- **One definition, direct passage (by reading).** `EXAMPLE_DOCUMENT` → `parse_request` → insert `BUILD_CONTRACT` → `validate_contract` → `serde_json::to_string_pretty`. There is no generated source or build step, and `build.sh` is unchanged.
- **Contract account.**
  - Both generator checks exit 0 at HEAD.
  - The `emit_example` rule carries no `free.*` fact, and no baseline file changed.
  - The snapshot's `document` equals the emitted document without `contract`, checked independently of the checker.
  - Both new nodes carry explicit evidence gaps, as step 1 prescribes.
- **Refusals through `run` (criterion 8.4).** A diff of each retained `input.json` against the emitted bytes shows exactly the stated single change. The outputs:
  - other development, other release, unbound → `unsupported_contract`, path `["contract"]`, the app's `expected_contract`, no client or reply;
  - absent identity → `missing_field`, same path and expected identity;
  - truncated → `invalid_json`, path `[]`;
  - unknown member → host `unknown_field`, path naming the member, client and reply present.
- **Cross-build and usage controls (8.5).** Battery artifacts under `…/integration/cli.integration/artifacts/direct-cargo-contract/`:
  - `absent` and `empty` builds: empty stdout and one stderr line (exit 2 is asserted by the test);
  - `foreign` and `release_form` builds emit their own identity, and the app refuses each with its own expected identity and null client and reply.
- **Generation controls (8.6).** Present in `contract_tree_controls.py` and `generators.py`, passing in step1-b and the battery. They assert the request payload moves, not the stamp cell itself.
- **Consumer result rule (8.10).** `result-consistency-controls.json` holds 133 records, identical in step3-a and the battery. They cover coherent finished and three non-finished baselines, each field changed, removed, nulled and retyped alone, all three together, a record error beside a result fault, refused profile contexts, absent replies, rejected captures and a projection differing from the bytes. On a live-format capture copy, flipping only `result.ok` produced exactly the consumer diagnostic.
- **Battery (8.3).** 231 selected, 231 completed, 0 skip, 0 unrun, no harness errors, `system_sleep_ms` 0 throughout, inventory unchanged.
- **Not-touched list (8.8).** No file under `runner/`, and none of `build.sh`, `meson.build`, `docs/build_contract.py`, `runner_commands.rs` or the dispatcher is in the diff.
- **Offline controls.** 178 of 178 matched, 67 of 67 identifiers covered, both baselines clean, results identical across two runs. Section 3 qualifies what "matched" proves.
- **Checker restates no consumer or controller rule (by reading).** Its own assertions compare against the emitted document, the process exit, its target observations or the pinned native expectations.

## 2. Unsupported or weakly supported

- **"Every failure to emit is exit 2" (section 10, 4.2, the contract rule).** False in one case I reproduced; see 3.1. The write-failure row has no built-app test: the unit test drives `emit` with a mock writer, and nothing exercises `cmd_example`'s mapping. I observed exit 2 with the stderr line when only stdout was a closed pipe.
- **"Reads no file, resolves no app root."** Supported by code reading only (`cli.rs` dispatch → `example::cmd_example`).
- **Classification matching (4.7).** Only identifiers are independently matched; see 3.2.
- **Native controls "with consistency still passing" (4.7 native row).** Shown for the spawn-failure and target-change controls only; see 3.3.
- **"Each [emission fault] prevents submission."** Controls call `checker.evaluate` only. Nothing executes `prepare()` or the shell's no-run branch with a failing emission; that rests on reading `example_round_trip.sh` and `prepare()` (`check_example_round_trip.py` ~733–737).
- **`refusal.*.one_change`.** It compares the retained input with `refusal_inputs(emitted)`, the function that wrote it (line ~518). It shows the file was not altered after preparation, not that the change is single. For real serde bytes that property rests on my diff above and on reading; `perturbation_controls` uses Python-serialized documents.
- **Release-form identity on the live case.** Not expected yet (section 9). Present evidence is the offline `release:v9.9.9` baseline and the Cargo `release_form` build.
- **Step 4 support, candidate rehearsal, criterion 8.11.** Later steps; not counted as failures.
- **Ten-run sample.** All ten ran back to back in 27 seconds under one condition. It gives no information on variation, such as `unestablished` ordering.
- **Criterion 8.1 "a second generation writes nothing."** I could not run generation. `--check` passing and the disposable-copy control support it indirectly.

## 3. Defects and risks, most consequential first

1. **`example` exits 101 when stderr is unwritable.**
   - Reproduction: `{ sleep 0.4; policy-witness example 2>&1; } | true` exits 101; `example x` under the same pipe also exits 101.
   - Cause: `cmd_example` reports through `eprintln!` and `cli::print_usage` (`controller/src/example.rs` ~66–86, `cli.rs:14`), which panic on a failed stderr write.
   - It contradicts 4.2 ("exit 2 without a panic", "one line, if stderr is writable") and the public rule text in `docs/contract/10-request.surface.md`.
   - A caller is not misled into accepting output, since 101 is not 0.
   - Separately, `example >&-` exits 0: the write succeeds with nobody receiving it.
2. **Expected classifications come from the checker's own table.** `pairs()` in `example_round_trip_controls.py:47–48` reads `checker.CLASSIFICATION`. `consistency_holds`, `native` and the rendered-report check use the same table. A misclassified assertion cannot fail any control. Section 4.7 requires the pairs "authored independently", and the suite README says the same.
3. **Six native controls also trip the consumer.** `native_prediction_deny`, `_source`, `_rc_boolean`, `native_order_unestablished`, `native_attempt_failed` and `native_attempt_rc` each produce `consumer_validation [consistency]` as well, because the constructed replies are incoherent. They earn coverage under the allowance. No control shows a coherent deny or failed-read reply classified as `native_observation` alone.
4. **The consumer's result rule is switched off by one controller-authored field.**
   - `admitted_reply` in `tests/lib/consumer.py` (~1013–1036) returns None unless `data.runner_sandbox_diagnostics` is an object.
   - The `assessment_absent` control asserts zero errors for a finished admitted reply with result `{tool_error, false, 7}`.
   - On a live capture copy, nulling the assessment and setting the result to `tool_error`, ok false, exit_code 0 gave only `execution.admitted_reply [execution_unavailable]` and no consistency failure. The case still fails, but with the classification whose remedy text points away from the product.
   - `envelope_skeleton` sets the assessment to null, so skeleton-built envelopes are never subject to the rule. The commit's "five call sites already coherent" is true but immaterial.
5. **No evaluation record exists.** Section 6 places it in the commit that completes step 3. Missing with it are the fixture-correction summary from 4.8 (even "none needed") and a recorded disposition for `example-step1-a`.
6. **Criterion 8.9 is not literally met.** `docs/CONTRACT-EXAMPLE-PLAN.md:66` holds the constant verbatim. The pre-existing hand-typed `read_hosts` step in `docs/contract/12-probes.surface.md:39` is byte-equal to the example's step; the plan keeps it, but it is an unextracted near-copy.
7. **The live case stores the machine's `/etc/hosts` bytes** (base64 in `targets-before.json` and `targets-after.json`), as 4.5 requires. Release-acceptance evidence will carry the acceptance machine's hosts file.
8. **`RUNNER_SELECTION_KEYS` in the checker (line 48) is a hand-held copy** of `SELECTOR_FIELDS` in `runner_select.rs`. It is correct today and would go stale silently if a selector is added. The generator's refusal of selection keys in the constant partly covers this.

## `example-step1-a`

`source_drift/generator_contract` failed in `test_prose_baseline_is_consistent_and_growth_is_explicit` on three unlisted `citation_pair` sites, all in `docs/CONTRACT-EXAMPLE-PLAN.md`. The other 13 cases passed, including `unit/rust.unit`. That text is present at c6345219, so I infer the case was already red at the starting commit; I did not run it there. 3bb0955f rewrote the three mentions as symbol links. By mtime, only the plan, `docs/contract/AGENTS.md`, `docs/contract/README.md` and the source_drift README changed between runs a and b. This is not evidence about the command, and it has no recorded disposition.

## 4. What would change this assessment

- **Fixed point:** a `run_flow` test or challenge run where the mutated emitter still passes, or evidence that `observe` does not reach the production preparation path.
- **Signed-app passage:** a host-received request differing from the emitted bytes at equal length. Present evidence cannot exclude it, and the plan declares that.
- **Live results:** any eval or battery `report.json` with a failing or unevaluated assertion, a nonzero `system_sleep_ms`, or evidence of live-case runs that were not retained (I found none).
- **Applicability:** an identity-input or runner file differing between de17cef7 and HEAD, or a test file edited after its crediting run.
- **3.1:** `example` exiting 2 under `2>&1 | true` on a rebuilt app, or the maintainer limiting the rule to a writable stderr.
- **3.2 and 3.3:** literal classifications per control, and coherent deny and failed-read controls with `clean=True`.
- **3.4:** a consumer or controller check that an envelope with admitted host bytes always carries the assessment.
- **Release form:** the section 9 nested acceptance showing a `release:` identity through the live case.

## 5. Deviations from the plan

- The step 3 commit has no "Evaluation record" section.
- Step 0 (89f9d121) rewrote the stamp cells and snapshot history by hand. The commit says so, and `--check --require-history` passes on the result.
- `docs/contract/runtime.py` changed (selector-key reading moved into `tree.py`) and `tests/suites/integration/README.md` changed; section 5 lists neither. `build_contracts.py` and `tests/COVERAGE.md` are listed and unchanged.
- The offline controls build from `tests/fixtures/blackbox_e2e/checker/current/constructed_run.json`, not `tests/fixtures/contract/` as 4.7 names. The fixture is existing and unmodified.
- There is no unit test of CLI dispatch to `example`; it is covered by the integration case and by `emit`'s argument refusals.
- The renderer uses `validate_contract(value, identity)` where 4.1 names `validate_request_contract`. It is the same gate with the identity as a parameter, which 4.8 asks for.
- 3bb0955f bundles the maintainer-confirmation record with the prose fix for the step1-a failure.
```

### Authors' response and dispositions

The reviewer has not seen the corrections below, and they have not been independently reviewed again.

| Finding | Response | Disposition |
| --- | --- | --- |
| 3.1 `example` exits 101 when stderr is unwritable | Confirmed as a product defect against the confirmed exit commitment | Corrected in `c188ffb4`: the reason and the usage text are written without panicking. The integration test `example_write_failures_exit_2_without_a_panic` checks unwritable pipes on the signed app, and the reviewer's reproduction exits 2 on the final build |
| 3.1, stdout closed at launch exits 0 | Not a defect; see the failed-run table | No product change. The contract rule does not claim this case fails |
| 3.2 Expected classifications came from the checker's table | Accepted | Corrected in `c188ffb4`: the control case spells each classification and checks the checker's table against it |
| 3.3 Six native controls also tripped the consumer | Accepted | Corrected in `c188ffb4`: coherent deny, failed-read, combined and unestablished-order replies are read cleanly by the consumer and fail only native expectations. The incoherent inputs remain as further controls under the allowance |
| 3.4 One controller-authored field switched the consumer's result rule off | Accepted | Corrected in `c188ffb4`: admission comes from the capture's host bytes and the producer and profile gates alone. Controls show the relationship in force without the assessment, and the example checker reports an admitted reply without the assessment as a consistency failure. Remaining limit: the consumer does not restate the controller's collection-capacity gate, so a reply refused for capacity alone would be reported as inconsistent; the final battery contains no such envelope |
| 3.5 No evaluation record | The record follows the review by the order of section 6 | This section |
| 3.6 The plan repeated the constant | Accepted | Section 4.1 now links to the constant. The hand-typed step in the probes surface's `read_hosts` example stays, as section 4.3 states; it is listed under open matters |
| 3.7 The live case stores the target file's bytes | The plan requires it in section 4.5 | No change; listed under open matters |
| 3.8 The checker held its own list of selection keys | Accepted | Corrected in `c188ffb4`: the checker reads the keys from the request shape golden, and the control case fails if the set changes |
| Section 2, no built-app test of the write-failure row | Accepted | Covered by the integration test named above |
| Section 2, nothing executed the prepare step on a failing emission | Accepted | Seven prepare controls: a failed emission or bound writes a report and leaves no target observation or refusal input |
| Section 2, `one_change` compared an input with the function that wrote it | Accepted | The checker now judges each input against the emitted bytes and the stated change |
| Section 2, "reads no file" rests on reading | Partly answered | The isolated Cargo builds in the integration case emit from a bare target directory with no app, manifest or registry beside them. No control observes the process's file reads |
| Section 2, the ten-run sample shows one condition | Agreed | Stated as a limit in the comparison above |

No consequential disagreement remains open between the reviewer's assessment and this response.

### Fixture corrections under section 4.8

No fixture needed correcting. `envelope_skeleton` in `tests/lib/blackbox.py` now derives its default result from the reply's outcome. Its five call sites already stated coherent results: two rely on the default with a `finished` reply (`runner_filter_sysctl_name/checker_controls`, `blackbox_e2e` extension controls) and three pass an explicit failure with a `bad_request` or `xpc_error` reply (`blackbox_e2e` policy-check and client-capture controls, `source_drift/porcelain_codec`). No control's expectation changed. Controls that deliberately fault a result or a reply outcome, such as the `retired_run_outcome` and `failed_runner` controls, still require their own diagnostics, and the cases holding them pass in the final battery. With admission decided by the capture and gates alone, skeleton-built envelopes are subject to the new rule; none failed it.

### Deviations from the plan

- The user guide gained one command-table row, by the maintainer's decision of 2026-11-12.
- Step 0 rewrote the stamp cells and snapshot history directly, because generation refuses while the tables claim an absent tag; the generator then wrote nothing further.
- `3bb0955f` also fixed the pre-existing prose-scan failure in this plan.
- Files outside section 5's table changed: `docs/contract/runtime.py` (selector-key reading moved into the tree reader, which the extraction needs), `tests/lib/runner_client_capture.py` (the independent admission of host bytes), and the `integration` and `source_drift` suite READMEs. `build_contracts.py` and `tests/COVERAGE.md` are listed there and did not change.
- The offline controls are a separate script beside the one checker, and build their passing input from the authored run under `tests/fixtures/blackbox_e2e`, because no coherent single-read reply exists under `tests/fixtures/contract`. No fixture was generated.
- No unit test covers CLI dispatch to `example`; the integration case covers it on the signed app.
- The renderer calls the contract gate with the identity as a parameter, which section 4.8 asks for, where section 4.1 names its wrapper.
- The contract's example node states its two commands in authored prose and the renderer appends the extracted document. The node's public payload holds the parsed document in place of its citation.
- The shared consumer's admission uses the capture and the producer and profile gates, and not the controller's assessment, with the capacity limit stated above.
- Step 3 spans `6c9f11da`, `c188ffb4` and `23440049`, and needed two further signed builds after the review.

### Open matters

1. **Integrity findings and command success.** The consumer verifies today's mapping from reply outcome to result. Whether controller integrity findings should change command success, `envelope.data.select.success_findings`, remains undecided and is not authorized by this work.
2. **Release form.** No live run has seen a `release:` identity; section 9's nested acceptance supplies it.
3. **Review of later changes.** The corrections after the independent review, the two revisions and the step 4 support have not been independently reviewed.

### Maintainer's decision

Given on 2026-11-12, in the maintainer's words.

On the evaluation:

> I accept (this may be treated as "accept with revisions" based on the below).

On the target bytes in evidence, after hearing that the plan states no reason for storing them:

> digest-and-length is good.

On the `read_hosts` example, choosing extraction of the step from the constant over a link to the emitted example:

> I agree, you can do A. Proceed.

The decision is accept, with two revisions: the live case records a digest and length of each target in place of its bytes, and the probes surface's `read_hosts` step is extracted from the example constant.

### After the decision

| Stage | Change | Run | Result |
| --- | --- | --- | --- |
| Revisions, `d3c2a72a` | The live case records a digest and length of each target in place of its bytes. The probes surface's `read_hosts` step is extracted from the constant through a member path | `example-rev-a`, `20261113T024020Z_f14a2562`: `source_drift`, `unit`, both example cases and `blackbox_e2e/checker_controls` | Pass, 17 of 17. The offline case matched 192 controls and covered 67 of 67 assertions. The retained target record holds a digest and length and no bytes |
| Step 4, the commit that adds this row | Support owners replace the evidence gaps on the rule and the example node, graded check read with their limits stated | `example-step4-a`, `20261113T024826Z_da2f4033`: `source_drift` and both example cases | Pass, 12 of 12 |

Both stages changed tests, the contract tree and generated documents. Controller source did not change, so the identity derived from the source stays `development:6a333cf6f19aea6939fa843655b6ce2a90ec05837fb4bb6b8b9288b0ccc572f0`, equal to the selected app's.

Evidence carried forward to this state, as a reviewed judgment and not a mechanical fact: the final default battery ran before `d3c2a72a`. The consumer, the dispatcher and every case outside the two example cases and the contract generator's controls are unchanged since that battery; the two example cases, the consumer controls and `source_drift` were rerun after each change. Earlier development runs under `tests/out/runs/` retain this machine's target bytes from before the first revision and remain disposable.

### Handoff statement

- **Supported source:** the commit that adds this statement. Implementation is `23440049` with the revisions of `d3c2a72a`; support for the rule and the example node is complete at check-read grade, and the evidence gaps are gone.
- **Selected app:** built from `23440049` with a clean tree, identity `development:6a333cf6f19aea6939fa843655b6ce2a90ec05837fb4bb6b8b9288b0ccc572f0`. Controller source is unchanged since that build.
- **Applicable verification:** the final default battery and the challenge at `23440049`, and the reruns listed under "After the decision". The final ten runs of the live case predate the digest revision and stand as the sample for that build.
- **Unresolved decisions and dispositions:** no failed assertion awaits a disposition. The open matters above are the unresolved decisions.
- **Blocks dependent investigation:** nothing recorded here. The controller investigation can use this baseline; reassess applicability if source, contract, consumer, fixtures or tests change.
- **May remain pending:** section 9's candidate verification on the final source, and an independent review of the later changes.
