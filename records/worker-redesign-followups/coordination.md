# Follow-up investigation coordination

Status: descriptor-lifetime, exec-supervision and sysctl-read investigations are
complete and reviewed; execution configuration has a reviewed source inventory.
No follow-up application refactor has been selected. The source
baseline is `503156f0693dd8a22acf633efccdc93e300f2ebc`, following accepted terminal
exit and its shared-token lifetime documentation correction.

This record belongs to the [worker redesign plan](../../WORKER-REDESIGN-PLAN.md).
The daughter plans link their individual reports and experiment equipment.
Application changes follow a separate design decision; copied-source prototypes
are investigation equipment.

## Coordination and decision boundaries

The three initial investigations ran concurrently, with shared-checkout builds
and process experiments scheduled one at a time. The final native experiments
recorded successful cleanup accounts. The existing worker-death
baseline lacked a durable final fixture-cleanup receipt; the exec investigation
retains a later read-only absence observation without upgrading that earlier
assertion. The inspected signed app is unchanged.

Descriptor ownership is the first decision checkpoint. Exec supervision may use
its findings, but must preserve post-apply spawning and establish its promised
cleanup boundary before selecting new processes or channels. The worker's own
terminal lifetime remains settled; descendants are a separate lifetime.

Execution configuration inventoried existing request, resolution and
observation facts after the sysctl investigator finished. Shared reporting decisions
follow the exec result so the two investigations do not invent competing
completion/intervention fields. Environment work follows that distinction and
starts with existing provenance and one useful interpretation case. There is no
authorization to reset consent, provision a machine or alter system settings.

## Fresh baseline observations

The coordinator ran:

```sh
PW_TEST_OUT_DIR=tests/out/runs/worker-followup-baseline-20261018 tests/run.sh \
  --suite runner_exec_lifecycle --suite exec_fixture \
  --case runner_unit/host_setup_controls
```

Run `20261018T192430Z_884b74f5` passed all seven selected cases, with no skips,
unrun cases or harness errors. Its [run summary](../../tests/out/runs/worker-followup-baseline-20261018/run.json)
records the command, configuration, per-case results and valid/unchanged app
inventory. Raw output is gitignored and local to this checkout. This run and
the sysctl compatibility run `20261018T192613Z_fe6fb31d` (two of two passed)
are pinned in the retention index. [Provenance](provenance.json) and
[baseline receipts](baseline-receipts/) preserve exact run summaries, commands,
consoles and app inventories durably. The source baseline identifies unchanged
production/test sources; it is not asserted as the app's original build commit.

The cases distinguish timeout cleanup, stream closure, leader exit, worker
death and a same-group survivor after ordinary completion. The survivor case
observes the child answering with its original identity and group after the CLI
finishes and the following file effect occurs. Fixture cleanup then observes
exit. This establishes that ordinary completion can leave that child alive; it
does not establish arbitrary descendant containment. The setup controls retain
their narrower meaning: matching descriptor metadata is not proof that two
shared-memory mappings refer to the same object.

## Reviewed outcomes and next decisions

The coordinator reviewed the agents' source traces, equipment, native receipts
and recommendation limits. The parent and daughter plans carry their reports;
none of the following is implementation acceptance.

- **Descriptor lifetime:** fourteen constructed-core scenarios and six rejected
  checker controls support closing the host descriptor immediately after worker
  spawn while keeping its mapping. Independent writes/readback distinguish the
  true object from a byte-identical writable decoy with identical stat fields.
  The deliberate naive close demonstrates why deferred ownership must also be
  invalidated: it closes an unrelated descriptor that reuses the number. The
  self-dup no-clear case loses fd 3 at the first observer entry, before its extra
  exec, supporting retention of the current pre-spawn clear in this scope.
  Recommend this narrow ownership refactor first; collisions and worker aliases
  remain separate.
- **Exec supervision:** current behavior allows same-group background work to
  outlive ordinary completion. Before choosing a supervisor, decide whether
  ending that work is intended. A worker-side group request before normal leader
  reap is a small extension; cleanup after worker loss needs a surviving owner.
  The external-anchor probe preserves post-apply spawn and stops observed peers
  after worker death before child-PID publication. Its escaped-child negative
  remains alive until fixture release. Both signal-zero probes return `EPERM`
  with the anchor unreaped: no group-absence conclusion follows. Additional
  authority, per-attempt group ownership and changed child-visible group/session
  behavior are material costs. Keep completion facts separate from cleanup
  effort and independently established exits under every choice.
- **Sysctl:** eleven native calls and three rejected interpretation controls
  support preserving the single non-null 4096-byte read. Name and disclose that
  bound; optional capacity/raw post-call `oldlen` evidence is a separate choice.
  A failed read changed 3,888 sentinel bytes while returning length zero. That
  count establishes some writes, not exact bytes copied; native length is not
  required size or a causal diagnosis. No dependency on exec was found.
- **Configuration:** the source inventory distinguishes all ten submitted
  controls, resolved allowances and actual observations, including inert and
  unreached values. Existing retained request/envelope/provenance can support
  qualified observation records now. Missing dynamic validator allowances,
  intervention observations and the default-validator fallback's selected-path
  discrepancy are independent gaps, not grounds for a generic mode flag.

Keep environment investigation staged and defer shared lifecycle fields until
the exec choice. The documentation prototype can proceed from existing evidence
without requiring a new application configuration or environment schema.

## Retained documentation workstream: source findings

These are coordinator source-review findings, not a selected documentation
schema or completed repair of WA-02/05/06/09.

The current worker graph contains 83 nodes and 54 edges. Each item carries a
flat facts dictionary plus row-wide source/check lists. The generator's
`_citations` requires a test or rule through `require_test`; citation
validation establishes symbol/definition availability. It does not establish
which particular fact the cited assertion supports. The existing caption
accurately describes that mechanical guarantee.

Several concrete examples motivate a small fact-support prototype:

- Host temporary-array row `n6` cites the direct C harness's bare-deny case.
  That harness does not execute the host's Swift allocation/population path.
  Source support can state what this row actually has without adding an
  unrelated case to satisfy a required cell.
- Token rows `s12b` and `s22` have distinct framing and accepted-channel
  lifetimes. Their new erasure controls support specific capacity and ordering
  facts, while early mapping/header refusals still depend on independent host
  cleanup. A row-wide check list cannot express this division by itself.
- Process-group row `s36b` combines acquisition placement, source semantics and
  an old audit-execution note in its `Sandbox-gated` cell. The fresh lifecycle
  results apply to identified configurations and assertions; they should not be
  promoted into a universal policy-gating claim.
- Source ownership for edges `W24`, `W30` and `W55` deserves correction after
  tracing actual duplication, worker borrowing and controller log association.
  This is separable from changing the resource model or role taxonomy.

The next documentation experiment should express a few of these rows with
fact-specific source/assertion support and an identifiable observation record.
Acquisition placement, policy-specific observation and resource purpose should
remain distinct. An observation record needs its command/configuration,
source/artifact identity, actual predicate and applicability review; a matching
worker identity alone cannot explain whether an observation exercised the fact.

Keep current resource IDs stable while testing that representation. Delay
broader holder/object and multi-purpose graph changes until descriptor and exec
ownership decisions settle. Configuration findings should inform how the record
identifies requested controls and observed interventions, without requiring a
new application-wide environment schema first.
