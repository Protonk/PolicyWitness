# Interface and example tracing review

Source inspection on 2026-11-15 at starting commit
`2fcf9dbc9f08b1643426b4cf9b9b32e3782c86cc`. This record supplies the bounded
investigation for exercises 1 and 2. It credits no new mutation, test execution,
signed build or native observation. The mutation outcomes below are historical
records in [mutations.json](../../controller/interface/mutations.json), read
against the current owners. Final document destinations and acceptance are
the integrating executor's responsibility.

## 1. Interface vocabulary and result projection

The two entry points expose different review questions. Renaming a command-line
option changes what callers can supply. Changing a result row can change what
callers conclude and the process status they receive. A support identifier
rename can leave both behaviors unchanged.

### Option spelling and selector precedence

`run.option.runner_mode` identifies `RunOption::RunnerMode` in
[run_args.rs](../../controller/src/interface/run_args.rs). Its `def` supplies
`--runner-mode` and the `run_option` runner-kind reader; `classify` and
`run_flow::parse_arguments` consume those definitions. The
[inventory](../../controller/interface/inventory.json) records that spelling,
reader, command relationship and run-card association.

The reverse link already exists: `request.options.precedence` cites that
identifier and the two admitted runner-kind words. Its complete obligation is
to parse CLI mode before reading the request, inject it into selector
processing, validate all supplied legacy values before replacement, replace
each with its corresponding non-null nested value, preserve an explicitly
empty nested entitlement list, and refuse the standard/external-selector and
byoxpc/no-selector conflicts. Selection and entitlement checks precede client
invocation. `machme` is refused. Its controller/CLI/run-envelope applicability
must travel with the free effect and prose.

The existing connection is useful navigation, but it is **not a spelling
comparison**. [interface_join.py](../../docs/contract/interface_join.py) resolves
the entry; the node supplies no `values` fact for the option spelling, and the
join does not compare its prose or `free.effect`. Thus a matching identifier
does not establish agreement about `--runner-mode` or selector precedence.
The node's subtree support names selector parsing and independently authored
precedence controls; those controls do not claim to verify the option spelling.
The interface corpus and `run_flow` argument/injection tests supply separate
behavioral expectations.

Historical `rename_option` changes `--runner-mode` to `--runner-kind`: the first
build refuses stale inventory, the regenerated card changes, the contract
check stays unchanged, and the literal corpus plus argument/injection tests
fail. Card/execution agreement remains successful because both follow the new
definition. This is evidence of the distinction between internal projection
agreement and preservation of the public spelling; it is not a new execution
in this work.

### Admitted completion and process status

`result.admitted_finished` comes from `Row::AdmittedFinished` in
[result.rs](../../controller/src/interface/result.rs). The first-match relation
requires class `Admitted` and host label exactly `finished`, retains that label,
sets `ok` true and selects exit 0. `run_result::run_result` constructs the
serialized result from this selection; `run_flow::envelope` also obtains the
process exit from it. `complete_execution` computes diagnostic findings
independently and passes their count into the disposition; the relation does
not use the count to select another result.

The public path is `envelope.data.select` and its `finished` case, beside
`envelope.data.success_findings`. The rule applies after reply checks, to a
present host reply **whose client capture and host reply admission succeeded**.
Under that applicability, exact `finished` means true/0 with the host report
retained. Failed attempts and controller integrity findings can coexist with
that result. A received but unadmitted `finished` record does not qualify.
The first-match fallback retains another admitted host label and selects
false/1. These conditions prevent reading a literal label as sufficient proof
of successful admission or successful attempts.

The join compares the finished case's literal `ok` and `exit_code` assignments,
its host-label condition and retained host-label assignment. It also checks
the relative first-match order of cited cases. It leaves the admission class
uncompared because no structured contract operand binds that class; the whole
applicability expression, inherited `free.when`, diagnostic independence and
record-retention effects are not established by those literal comparisons.
The report must retain those distinctions after routing.

[cards.rs](../../controller/interface/cards.rs) renders each fixed disposition
through `select`, `run_result` and JSON serialization. The build compares its
generated inventory with the committed inventory. The offline interface check
validates the inventory and token provenance, but does not independently run
the Rust definitions. `each_result_class_agrees_in_fields_process_status_and_card`
in [run_flow.rs](../../controller/src/run_flow.rs) independently spells result
expectations for controlled captures, including failed attempts and integrity
findings beside finished success. The CLI corpus is a separate set of literal
expectations. `help_cards_agree_with_execution` in
[cli_contract.rs](../../controller/integration/cli_contract.rs) compares the
selected binary's displayed facts with what that binary does; it is not an
independent stability specification.

| Historical change | Recorded result | Review consequence |
| --- | --- | --- |
| `acceptance_connected_exit`: finished exit 0 → 9 | Inventory stale at build; connected card changes; contract join rejects exit mismatch; runtime cases not run | A public result/exit promise is implicated. Updating a projection does not authorize that change. |
| `acceptance_numeric_copy`: renderer privately fixes exit at the current 0 | Build and checks pass; card unchanged; runtime cases not run | Agreement with current output cannot detect this latent independent copy. |
| `acceptance_numeric_copy_then_exit`: definition changes to 9 while the copy remains 0 | Inventory stale; card token provenance and contract exit comparison both fail; runtime cases not run | The renderer is stale, and the governing result differs from the public statement; these are separate findings. |
| `rename_identifier`: row identity and its contract support reference change together | Inventory stale initially; card, contract and cases unchanged after the recorded update | A support identity changed without a public result change. `interface` metadata is outside canonical public meaning. |

The three acceptance mutations are recorded as unsigned Cargo checks of a copied
controller, based on `78abff08` with source hashes. They establish no live host
behavior. Their mechanisms remain intelligible from the current direct
renderer, relation and join; no fresh credit for them is asserted here.

**Reading-path recommendation.** REQUEST should expose
`request.options.precedence`, including the distinction between CLI mode and
request selectors. RESPONSE should lead from the outer result to
`envelope.data.select` and `success_findings`, then to the admission and retained
evidence boundaries. CONTROLLER's result-selection section should list those
commitments. CONTRACT's changed-item index can derive both directions from the
existing `interface` facts, inventory and support records. No new association
is needed for these two entries. Explicitly expose the option spelling as a
human comparison and the result class as an uncompared binding; do not present
either as fully machine-verified.

## 2. Example composition and admission

The changed item is `EXAMPLE_DOCUMENT` in
[example_document.rs](../../controller/src/example_document.rs). The constant
owns the build-specific specimen content. It is consumed by the emitter, the
contract's `request.specimen.example` extraction and the example help-card
projection. `request.specimen.emit_example` owns the distinct publication and
build admission promise.

The full publication statement is: `example` takes no argument; a bound build
prints its specimen with that binary's contract identity and one newline;
exit 0 means the complete document was written and flushed. That build's own
`run` admits the document, but emission itself performs no host admission and
observes none. Usage, missing/unbound identity, gate, write and flush failures
exit 2; discard stdout on failure even if it is complete JSON. Publication
reads no file, launches no runner and says nothing about a caller's document.
Content, layout and labels have no cross-build stability promise.

[example.rs](../../controller/src/example.rs) implements rendering through
`parse_request`, identity insertion and `validate_contract`, then whole-document
serialization before `write_all` and flush. Its refusal and short-write/flush
unit controls distinguish complete-looking bytes from successful publication.
`emitted_example_reaches_the_client_as_the_emitted_document` checks the held
serialization at a controlled client callback, under the test identity. This
is preparation evidence, not host grammar admission.

[tree.py](../../docs/contract/tree.py)'s `_example_document` requires the cited
single raw-string JSON object, known top-level `PWRunnerRunSpec` members, and no
`contract`, `_test_overrides` or controller selector fields. It is deliberately
not the deeper request decoder. The extracted content enters the canonical
snapshot; its citation does not. `test_example_source_edit_is_stale_until_regeneration_and_moves_content_and_identity`
checks that the source edit changes the rendered content, public payload and
build identity after regeneration. A generated example can pass extraction
and still fail host grammar or meaning checks.

The actual host path is
[PWRunnerService.runReservedSpecimen](../../runner/Sources/PWRunnerCore/PWRunnerService.swift)
→ `pwRunnerDecodeJSON(PWRunnerRunSpec.self, ...)` →
[PWRunnerRunSpec.init(from:)](../../runner/Sources/PWRunnerCore/PWRunnerRequest.swift)
→ [admitSpecimen](../../runner/Sources/PWRunnerCore/ProbeRunner.swift).
Decode validates identity before unknown keys, typed members and exclusive plan
forms. Admission then checks capacity before ordinary meaning or actor-plan
normalization. Ordinary meaning checks include policy validity, phase and step
IDs, query validity, attempt support and inapplicable actor/extension fields.
The controller's contract gate is an earlier, narrower boundary.

[RequestContractTests.swift](../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift)
loads the independently authored request corpus, decodes and calls
`admitSpecimen`, and compares expected refusal codes and paths. That corpus
does **not** load `EXAMPLE_DOCUMENT`. Its general grammar checks cannot be
credited as an execution of the app's exact publication. The direct exact-example
admission support is the live
[example_round_trip](../../tests/suites/witness_contract/example_round_trip.sh)
case and its
[checker](../../tests/suites/witness_contract/check_example_round_trip.py).
No instance was run during this review.

The checker submits the selected app's emitted bytes unchanged. It separately
compares identity with version and plist records, content without `contract`
with the canonical example, delivered byte length, admission/refusal evidence,
policy digests, operand echoes and the shared consumer's validation. Its
independently authored `WORKLOAD` requires the two-plus-one phase partition and
three roles: query/read A; metadata query B beside fresh read C; data query/open
B. It pins native results separately under observed file prerequisites. In
particular, the third attempt is expected to fail with `EPERM` while the run
finishes; admission never promises that all three attempts succeed. The second
query predicts nothing about the read of a different file.

Every emitted, flat and actor submission has its own before/after file samples,
process capture and evidence rows. The flat and actor derivatives are harness
constructions, not documents published by `example`. The independent samples
support comparisons of descriptor identity and bounded read bytes; they do not
establish continuous target stability, a native query's resolved object, or the
cause of a permission-shaped failure. The
[constructed actor fixture](../../tests/fixtures/example_round_trip/README.md)
is authored hypothetical evidence for checker controls, never a captured run.

Historical `example_field` changes only the first attempt target from
`/etc/hosts` to `/etc/services`. It initially refuses stale inventory; the example
card changes, the contract check rejects stale rendered content and public
snapshot, and literal help cases fail. Card/execution agreement stays successful.
The record does not contain an example round-trip execution. The changed target
therefore proves neither admitted nor refused host input. It changes composition
and the public snapshot, and it breaks the independent workload's equality
between the first query and attempt targets. It does not by itself revise the
build's general admission promise.

**Reading-path recommendation.** REQUEST should connect the publication rule
to the extracted example and the ordinary phased grammar, with an explicit
transition from emission to host admission. RESPONSE's compact exercise should
start with the emitted form and distinguish publication, admission, process
completion, each query, each attempt and independent samples. Link to the
maintained checker and its row descriptions instead of authoring a synthetic
success transcript. CONTRACT should show the constant's extraction and interface
projection separately from its support links to publication and the live
admission check. Existing relationships suffice; no blanket association between
all example fields and all admission checks is justified.
