# I3 actor fallback association preparation

Prepared against base `ea64218be2549fd034096f53ac23d79afac711ae`, following `implementation/COMMON.md`, investigation E3 in `investigations/evidence-report.md` and I3 in [the outflow plan](../../../READER-OUTFLOW-PLAN.md). Source editing and read-only inspection only: **no builds, tests, native trials, formatters, compiler checks, generators or dispatcher invocations ran**. Runtime and formatting acceptance remain pending the user's sleep checkpoint and explicit resume.

## Source and contract judgment

[run_flow.rs](../../../controller/src/run_flow.rs) already resolves each actor's policy, collects policy objects in request order, and keeps each actor ID beside its independent helper capture. Fallback eligibility is admission of a client capture with terminal `xpc_error`, not proof that the host admitted the request or launched/applied a worker. No implementation defect was found or repaired. No wire field, reader rule, version, golden or generated artifact changes are needed. No new memory, malformed-input, or fallback behavior is introduced.

The existing orchestration dependencies did not expose the compiler invocation. The minimal seam adds `RunDependencies.policy_check`, with production still bound to `run_policy_check`, and passes the closure into `actor_fallback_checks`. Both existing dependency initializers (`production`, `orchestration::observe_client`) preserve the real helper binding. Both `run` branches pass it to the singular fallback closure and to the two actor-fallback call sites. The added test has its own initializer. All callers and initializers are in the assigned file; no external API changes were needed. Production trigger, order, request serialization and unavailable-error conversion remain unchanged.

The implementation reference currently enumerates four controllable dependencies under [what a run reads and launches](../../../controller/README.md#what-a-run-reads-and-launches). Its next documentation edit should include the fallback compiler invocation in that list; this report does not edit outside the assigned scope.

## Prepared assertions

`run_flow::tests::orchestration::actor_fallback_preserves_resolved_inputs_order_and_transport_evidence` drives the real controller `run` with synthetic app evidence and controlled invocation boundaries. Its six bounded scenarios cover eligible terminal failure, an unavailable actor helper, successful host reply, host body naming `xpc_error`, missing client capture and request-delivery failure.

- Distinct apply actors `zeta` and `alpha` surround a valid unapplied actor. Their declaration order differs from lexical order, detecting reordering and label/index shifts when a policy-free actor is skipped. Each actor owns an empty phase, preserving valid actor-form inputs.
- `zeta` resolves a real fixture augment. Expected full policy objects are literal independent values, including the exact inserted newline, absent `augments` field and `alpha` parameters. No expected value comes from the production resolver or captured output.
- The client receives the independently expected request with the controller selector stripped. The client closure then replaces the source file. The singular helper must receive byte-for-byte the client-held string, followed by exactly `{policy: zeta}` and `{policy: alpha}`; neither a reread nor a different actor policy can pass.
- Distinct helper success, compile-error and unavailable captures must appear under the exact actor labels and in declaration order. Full capture equality preserves helper envelopes, exit values and diagnostics. A failed singular check does not suppress the later actor checks.
- The client is invoked exactly once. Its full capture and optional runner result survive unchanged. Eligible failures retain null runner result and diagnostics, terminal `xpc_error`, the original client error and exit 1, regardless of helper outcomes. This establishes no host admission, compilation by native code or worker execution.
- All four ineligible scenarios invoke neither singular nor actor helpers; singular capture remains null and the optional actor list is absent. A host body merely naming `xpc_error` does not enable fallback.

The helper captures are constructed fixtures. This tests association/orchestration, not native compiler semantics or transport admission's full malformed-input space. Helper failure continuation is bounded to the selected slots. The existing generic fallback controls remain in place.

## Deferred validation

Run from repository root after resume, using a fresh output name and without concurrent checkout execution:

```sh
PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-i3-unit-01 tests/run.sh --case unit/rust.unit --case unit/rust.fmt
```

Canonical behavioral selector: `unit/rust.unit`; formatting selector: `unit/rust.fmt`. The named test is part of the ordinary Rust binary unit batch and needs no new catalog registration. The catalog requires Cargo; the case compiles the controller/helper binaries and requires their usual toolchain/dependencies. This selection needs no signed app, XPC, live sandbox or external runner. Compilation, formatting and assertions are unverified until this command runs. Existing broad acceptance can be combined by the coordinator under the serialized dispatcher, retaining a fresh run directory and unset `PYTHONOPTIMIZE`.
