# Narrow assembled-guide account corrections

Private only while root's focused test selection holds the shared source.
`before/docs/PolicyWitness.md` is the assembled guide
`aa24c71c67019804cf2d6b34655d23cc4271939797b94788b8110aff0558b01f`.
The patch changes seven authored guide statements and the single field-comment
input in `docs/porcelain.json`. Every fenced block is byte-identical. No public
field, wire tag, type, codec rule, product behavior or test assertion changes.
No generator, build, test or guide command was run.

1. `execution_form`: the ordinary producer omits this field; actor assembly
   assigns `actors`. `PWRunnerRunResult` declares an optional at
   `runner/Sources/PWRunnerCore/PWRunnerReply.swift:183`; its initializer at
   196–240 leaves it nil. `CWorkerOrchestrator.swift:211–229` returns ordinary
   output without assigning it. `ProbeRunner.swift:132–138` and
   `CWorkerRequestPlanning.swift:272–293` likewise construct refusal reports
   without it. The only production assignments are actor assembly and actor
   preparation refusal at `ActorOrchestration.swift:513` and `:538`.
   `PWPorcelain.swift:51–53` omits a nil optional on the binary wire;
   `controller/src/porcelain_records.rs:3420` emits JSON only for Some.
   This agrees with `docs/contract/30-reply.surface.md:135–138`.
2. The misleading Swift comment is generated from
   `docs/porcelain.json:3584`. Only that authored `doc` string changes, to
   “Actor assembly emits `actors`; the ordinary producer omits this field.”
   Generated Swift is intentionally untouched. Root will run the porcelain
   and worker-identity owners and their dependent generated/staging checks.
3. The adjacent `actors[].applied` row said null for an unapplied actor.
   `ActorOrchestration.swift:437` supplies nil for unapplied and the collected
   applied flag only for apply mode with output. The Rust actor projection at
   `porcelain_records.rs:1234` emits the key only for Some. The guide now calls
   it an optional collected observation for an apply actor, matching
   `docs/contract/33-actor_evidence.surface.md:62–64`. This describes current
   production rather than importing reader tolerance for carried nulls.
4. The adjacent `ordering` row depended on whether a worker “exists.”
   `CWorkerOrchestrator.swift:176–178` maps collected worker output to phase
   ordering; `ActorOrchestration.swift:336–340` additionally requires the
   corresponding visit index in that output. The guide now states those
   collection conditions. Current process existence is a different observation.
5. The re-delegation example uses unapplied unentitled A and applied B/C.
   Its first issue is A's `a_issue`; B's `b_issue` occurs under B's policy after
   consumption. The introduction now offers an applied actor as the choice
   for observing issuance under its policy. The exact heredoc includes four
   target fresh reads: b_read_before, c_read_before, b_read_after, c_read_after.
   “Compare each fresh read … with its actor's policy” replaces “three.”
   `tests/suites/witness_contract/check_extension_redelegation.py:146` names
   the same four target readings; additional control-path reads in that native
   scenario retain their separate scope. The shell block is unchanged.
6. The receipt sentence is positive: it is read under the contract of the
   reply that carries it. No receipt field or interpretation rule changes.

The adjacent top-level inventory was also read against actor assembly and
preparation records, `ActorSetupStatus` at `ActorScheduler.swift:45–56`, phase
assembly, and the typed JSON projections. The follow-up below adds the child
evidence qualification. This is a bounded source review,
not a new native observation or an exhaustive re-audit of every downstream
comparison rule.


## Worker evidence follow-up

The original accepted package and report remain intact at
`/private/tmp/pw-contract-stage-four-account-corrections`, patch SHA256
`b4439552096b786042e424a76107687b2d782c2c9bbb3a5543333f68cb4f31c9`.
This successor adds one guide sentence correction: `worker_evidence` belongs to
the subprocess record when collected shared memory has the expected worker
identity. The following `abi_identity` explanation still names host-selected
protocol sources.

Independent source read confirms the condition. `CWorkerDisposition.swift:18–33`
copies optional `out.workerEvidence`; `ActorSession.swift:727–747` fills that
optional using `decodeWorkerEvidence(rawBase)` during output collection.
`CWorker.swift:584–592` checks the shared header's ABI magic and complete identity
bytes before decoding; its successful path returns the record at `:645–647`,
with `PWShmLayout.abiIdentity`. The controller projection at
`controller/src/porcelain_records.rs:3844` serializes only Some. A launched child
alone does not supply the decoder's input condition. No producer, schema, wire
rule or test assertion changes.

All paths above are under `runner/Sources/PWRunnerCore/` except the explicit
controller path. No shared files or generated outputs were changed and no tests,
app commands or builds were run. Every guide fence remains byte-identical.
