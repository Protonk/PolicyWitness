# Working in `controller/`

Read [README.md](README.md) for the module map, CLI, run lifecycle, log capture
and external-runner registry. These rules supplement the [root guidance](../AGENTS.md).

## Find the relevant contract

- Use the [wire contract](../docs/CONTRACT.md) for versioning and shape ownership,
  the [request grammar](../docs/REQUEST-GRAMMAR.md) for admission, and the
  [user guide](../docs/PolicyWitness.md) for public field meanings.
- For native helpers under `tools/`, runner behavior or test seams, also read
  [runner/AGENTS.md](../runner/AGENTS.md) and the [runner reference](../runner/README.md).
- For test selection, evidence and cleanup, follow [tests/AGENTS.md](../tests/AGENTS.md).
  Build through the [signed pipeline](../docs/BUILD.md) when verification needs
  a current app. Rust-only tests do not require that app.
- Before installing or cleaning up an external runner, follow the
  [external-runner workflow](../AGENTS.md#external-runner-workflow-agents) and
  [BYOXPC guide](../docs/PolicyWitness.md#external-runners-byoxpc).

## Preserve the controller boundaries

Admit the request version before interpreting controller options or augments.
Validate selectors, including shadowed aliases, resolve policy changes in
memory, and remove controller-owned fields before delivery. Keep one held
serialization for the client and fallback compiler; never reread or mutate the
user's file to prepare either invocation. Keep dossier hashes and import records
tied to the selected source. If a helper gains an environmental read or process
launch, update [the run inventory](README.md#what-a-run-reads-and-launches) and
its orchestration controls.

Gate replies before interpreting versioned fields. Preserve rejected parsed
payloads and transport diagnostics without coercing versions or recovering
semantic claims from unsupported bodies. Keep request-delivery failures ahead
of reply interpretation. A successful write is not proof of receipt; an
independent fallback compile is not evidence of worker progress.

Complete execution before attaching optional log evidence. Preserve
[field ownership](README.md#execution-and-log-evidence-ownership): collector
failures, matching events and missing events must not change CLI status, native
observations, comparisons or disposition. Match against submitted attempts,
not independent query targets. Keep ambiguous candidates and unmatched events;
do not turn PID/path matching into causal attribution or absence into allowance.

Preserve the shared monotonic collection deadline and separate wall-clock query
window. Keep streaming and derived-data limits, bounded diagnostics and cleanup
observations at both process boundaries. Do not repair truncated JSON into
evidence or report cleanup from EOF or leader exit alone. Keep group signalling
within proven ownership and distinguish group absence from a child's observed
wait. Review [the collection contract](README.md#log-collection-budgets-and-cleanup)
when changing supervision, parsing or correlation.

For registry changes, preserve lock ownership across mutations and launchd
actions, atomic publication, pending installation and durable cleanup records.
Never unlink a registry lock to bypass a holder. Require observed absence to
retire cleanup; unknown inspection is not absence, and a label prefix does not
authorize removal. Keep reconcile report-only and entitlement requirements tied
to the selected worker's read-back.

## Change producers and readers together

For request or evidence changes, trace affected admission, transport, assembly,
independent consumers, fixtures, shape goldens and documentation. Use the
[contract evolution rules](../docs/CONTRACT.md#when-a-number-moves) to decide
version changes. Update owning inputs and regenerate through the
[generator contracts](../tests/suites/source_drift/README.md#generator-contracts);
do not hand-edit generated versions, limits, layouts or worker identity.
Native source additions/moves also require the owning Meson target.

Keep the README's CLI block synchronized with [cli.rs](src/cli.rs).
Put public field definitions in the user guide, implementation responsibilities
in this README, and detailed assertions beside their suites. Preserve inbound
anchors when condensing documentation, or update their callers together.

## Verify the changed boundary

Use `tests/run.sh` from the repository root with a fresh `PW_TEST_OUT_DIR` as
described in [test guidance](../tests/AGENTS.md#choose-and-run-verification).
Select the cases that establish the change:

| Change | Relevant verification |
| --- | --- |
| Rust helpers, orchestration or formatting | [unit](../tests/suites/unit/README.md): binary unit tests, controlled dependencies and rustfmt. |
| Public CLI arguments and envelope behavior | [integration](../tests/suites/integration/README.md); use live suites when the behavior needs XPC or the kernel. |
| Request/reply admission or evidence interpretation | [failure_boundaries](../tests/suites/failure_boundaries/README.md), [blackbox_e2e](../tests/suites/blackbox_e2e/README.md) consumer controls and affected [witness_contract](../tests/suites/witness_contract/README.md) cases; follow the coordinated runner checks in test guidance. |
| Log parsing, transport or correlation | Rust supplied-text replay and execution-preservation controls; [archive selection](../tests/suites/witness_contract/README.md#archive-query-selection) for OS predicates; [live capture](../tests/suites/witness_contract/README.md#deny-capture-covers-the-run) for native execution and collection facts. Each establishes a different claim. |
| Selection, signing, registry or recovery | Rust selection/registry controls and applicable [runner_byoxpc](../tests/suites/runner_byoxpc/README.md) cases, including change-specific controls in the [opt-in registry](../tests/OPT_IN_TESTS.md). |
| Documentation or generated contracts | [source_drift](../tests/suites/source_drift/README.md), plus behavioral checks when meanings change. |

Use [sandboxed-harness diagnostics](../tests/AGENTS.md#sandboxed-automation-harnesses)
when XPC, logs, signing or compiler discovery are refused. Retain failed-run
evidence and external-runner ownership through the shared
[cleanup procedure](../tests/AGENTS.md#preserve-and-clean-up-output).
