# Architecture doc buildout plan

This plan builds `docs/ARCHITECTURE.md`. It is committed so the work can span
sessions, and it is deleted at closeout. Nothing permanent links here: not the
README, not an AGENTS router, not the architecture doc itself. When the plan is
gone, the repository reads as though it never existed.

Started 2026-10-03 at v0.2.5.

## Status

- [x] Step 0: survey the repository (2026-10-03)
- [x] Step 1: triage conversation over the strain register (2026-10-05)
- [x] Step 2: carry out the eliminations chosen in step 1 (2026-10-05; gate: default battery under `tests/out/runs/arch-step2-gate`, dispatcher rerun under `arch-step2-gate-dispatcher` after an unrelated Makefile fix)
- [ ] Step 3a: the manifest, generator, figures and drift case, from source
- [ ] Step 3b: the prose and the ASCII timeline, from source
- [ ] Step 4: review the draft with a human
- [ ] Step 5: integrate, verify, close out

## The document being built

`docs/ARCHITECTURE.md` is a tour of PolicyWitness internals at a meso level.
It does not ship: `build.sh` stages only the user guide. It does not supplant
the [user guide](PolicyWitness.md), and it does not replace the developer
documentation in [controller/README.md](../controller/README.md) and
[runner/README.md](../runner/README.md) or the contracts in
[CONTRACT.md](CONTRACT.md) and the
[failure evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md).

The existing documents sit at three altitudes. The README is the macro account:
one Flow paragraph and a list of what ships. The guide, FAQ and limits inventory
are user-facing: field semantics and operating guidance. The directory READMEs,
source comments and the ABI header are micro accounts, and the two contract
documents are normative. What is missing is the account of how one run unfolds
in time and of the boundaries a run crosses. That is the meso level, and it is
the subject of the new document.

Audience: a developer or agent who has read the README and is about to open a
directory. The document is not a field reference, not a contract, not a module
list, not a test map and not a build guide; each of those exists and is linked
instead.

Writing the account is also expected to make interdependencies visible that are
hard to describe parsimoniously. Those are collected once, in the strain
register below, and settled with a human before drafting begins (step 1). Some
become footnotes the document carries; others are chased down and removed from
the repository first, so that the document describes a simpler system.

## What no single document states today

The survey assembled each of the following from three or more places. The
document's job is to state each in one place.

1. **The life of one run in time.** Spawn, policy written on a pipe, ready
   byte, compile, optional capture, apply, applied sentinel, host fires the
   validator hook, validator batch, collection closes, proceed stored, worker
   acknowledges, attempts, done, exit requested, grace, kill, final snapshot.
   The pieces are in the host driver's comments in
   [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift), the C
   worker's `main` in
   [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c),
   the ordering tables in the failure evidence contract, and one sentence in
   the README.
2. **The process topology.** Seven distinct executables; the host and its two
   helpers live inside the XPC bundle, and the validator also has a diagnostic
   copy at the app's top level. Which are sandboxed, which call native sandbox
   APIs, who spawns whom, over what channel, with what lifetime. Spread over
   the README's "What ships", the controller README's reads-and-launches list,
   the runner README's key files, and comments in `build.sh`.
3. **The native API trust map.** The invariance rule says the XPC host never
   links, loads or calls libsandbox. The full statement is that exactly three
   processes call native sandbox APIs: the worker (compile and apply), the
   validator (`sandbox_check`, resolved through libSystem) and `sbpl-check`
   (compile only, diagnostic). The controller, the client, the host and the
   observer do not.
4. **The data flow.** Request JSON; controller admission (version, selector,
   augments); held bytes on the client's stdin; XPC `Data`; Codable decode with
   closed keys; capacity admission; meaning validation; shared memory plus a
   policy pipe; worker slots; host output; disposition record; step results and
   comparison; encode with degradation; client stdout; controller admission;
   envelope with dossier, projections and log capture.
5. **The boundary inventory.** CONTRACT.md covers three version numbers plus
   the worker identity. The survey counted nine guarded boundaries:

   | Boundary | Defined in | Guarded by (as read, not yet run) |
   | --- | --- | --- |
   | request schema | `docs/contract.json` | generator check; exact-version decoders in controller and host |
   | response schema | `docs/contract.json` | generator check; reply shape golden |
   | controller envelope | `docs/contract.json` | generator check; envelope shape golden |
   | worker ABI identity | `docs/generate_worker_identity.py` | build check; abi layout golden; worker exit 4 on mismatch |
   | validator NDJSON wire | `tests/suites/validator_batch_mode/` | suite only; no version field; outside the identity scope |
   | observer report schema | `controller/src/bin/sandbox-log-observer.rs` | Rust unit tests; envelope golden subtree |
   | sbpl-check helper envelope | shares the controller envelope frame | consumer admission by `kind` and version |
   | evidence manifest | `controller/src/evidence.rs`, `tests/build-evidence.py` | preflight |
   | runner registry | `controller/src/runner_manager.rs` | additive-field loader; retired kind aliases retained for recovery |

6. **Verification as mechanisms.** Goldens, generators with marker regions,
   the source-drift rules, the consumer, the test seam, the C harness, the
   lifecycle oracle, the dispatcher's app integrity check. The
   [tests README](../tests/README.md) has a suite table; nothing names the
   mechanisms.
7. **The document graph.** Three generators write marked regions into several
   documents and source files. The sandboxed-harness note is carried in three
   places with a drift check. The FAQ and the shared limits text are copied
   into the guide. Nobody has drawn this.

## Sequence

### Step 0: survey (done)

Read: the run flow, host driver, orchestrator, service, C worker `main`, ABI
header and client in full; the validator driver and the two helper binaries in
part; every top-level and directory document; the failure evidence contract's
introduction and comparison section; the test README's suite table; the
generators and the source-drift checkers. Nothing was executed. Line counts in
this plan come from `wc -l` and, for Rust files, note where inline `mod tests`
begins.

### Step 1: triage conversation

A conversation between an agent and a human over the strain register below.
The agent presents each row with its evidence and the two available
dispositions. The human decides. The agent may recommend, and should say when
it thinks a row is not a strain at all.

Dispositions:

- **footnote**: the document states the fact as it is, in one or two sentences.
  Write the sentence into the register.
- **eliminate**: change the repository so the document need not mention it.
  Write a one-sentence scope into the register; the work happens in step 2.
- **not a strain**: strike the row with a reason.

Rules: no code changes during the conversation; new rows may be added; the
register in this file is the record of the decisions. Step 1 ends when every
row has a disposition.

### Step 2: eliminations

Carry out each "eliminate" row as its own change, with the gates its files
require: the maintenance checklist in [AGENTS.md](../AGENTS.md), the
`source_drift` suite, and the owning suites of any behavior touched. Do not
begin step 3 until these land, because the document describes current behavior
and nothing else.

### Step 3: draft from source

Write the document from the code, not from the existing documents. For every
claim, name the symbol that implements it and the test that pins it. Keep a
drafting log (the section at the end of this file). A claim that needs a
footnote, or has no pin, goes into the register as a new row marked "found
while drafting". After the draft is complete, diff it against the existing
documents for contradictions and record those in the log as well.

Step 3a builds the manifest, the generator, the three figures and the
`source_drift` case; every node and edge cites its source symbol and its
check, and the generator refuses a citation it cannot find. Step 3b writes the
prose around the generated regions and the ASCII timeline.

The proposed shape is below. Use it unless the draft shows a better one.

### Step 4: human review

Review the draft with a human. Settle any rows added in step 3 the same way as
in step 1. A row settled as "eliminate" at this point goes back through step 2
before the document is finished.

### Step 5: integrate and close out

- Add a router row in [AGENTS.md](../AGENTS.md) for the document, the
  manifest and the generator, a maintenance-checklist line (a change to who
  spawns whom, a channel or a boundary guard updates `docs/architecture.json`
  and regenerates), and a line under "Implementation details" in the
  [README](../README.md).
- Run `python3 docs/generate_limits.py --check` and
  `tests/run.sh --suite source_drift`. The source-drift link check globs every
  `docs/*.md`, so the new document's relative links are checked without
  registration; anchors are not checked and must be verified by hand.
- Confirm the document contains no change-history notes, no contract version
  numbers in prose, no enumerated bundle paths that duplicate the README's
  "What ships", and no link to `records/`.
- Delete this plan in the same change, or the next one. The architecture doc
  must not cite it.

## Strain register

Each row is a place where a parsimonious account needed a footnote during the
survey. The Disposition column is empty until step 1. Evidence is what the
survey saw; verify it before deciding.

| # | Strain | Where it shows | Evidence | Disposition | Footnote text or elimination scope |
| --- | --- | --- | --- | --- | --- |
| 1 | The reply's normative semantics live under `tests/` in a file whose title no longer fits | [tests/FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md) | Its sections are Worker disposition record, Admission and receiver contract, Query and receiver evidence, Comparison record with the reading rules. It is linked from the guide, CONTRACT.md, both directory READMEs and AGENTS.md. | footnote | The normative reply semantics live in [the failure evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md); the document links that file by title wherever it needs a rule and never restates one. |
| 2 | The controller README carries cross-cutting contract text beside its module list | [controller/README.md](../controller/README.md) | "Execution and log-evidence ownership", "In-repository consumer audit" and "Log collection budgets and cleanup" are not about what lives in `controller/`. The runner README's "Run result highlights" overlaps the guide. `source_drift` checks the CLI surface block in the controller README, so that block stays where it is. | not a strain | Log capture and envelope assembly are controller work; those sections describe the controller's own behavior and the document links them. |
| 3 | Two paragraphs are duplicated verbatim with no drift check | End of [controller/README.md](../controller/README.md) and [runner/README.md](../runner/README.md) | The paragraph on the query PID (`sandbox_check.pid` names the worker, never the host) and the paragraph on `native_rc` appear identically in both files. The repository's shared-text pattern has a drift check; this pair has none. | eliminate | Keep the runner README's copy under Evidence contract pointers; replace the controller README's copy with a link. |
| 4 | Three outcome labels that no producer emits | `NormalizedOutcome` in [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [tests/COVERAGE.md](../tests/COVERAGE.md) | `sandbox_apply_failed` and `runner_sandbox_denied` are "recognized constants that no producer emits"; `bad_policy` is reachable only defensively because public admission refuses the same inputs earlier as `bad_request`. The witness case `pre_apply_failure_reports_no_policy_verdict` asserts their absence. The question is whether negative pins need constants. | eliminate; footnote for `bad_policy` | Remove `sandbox_apply_failed` and `runner_sandbox_denied` from `NormalizedOutcome`, their coverage rows and the prose that explains their non-emission; negative pins keep string literals. Footnote: `bad_policy` is the host's defensive pre-spawn structural check; admission refuses the same inputs earlier as `bad_request`, so the label is reachable only through a defect in that check. |
| 5 | Disposition validation and projection sit inside the orchestration module | [controller/src/run_flow.rs](../controller/src/run_flow.rs) | Production code ends near line 1,800 where `mod tests` begins. The `DISPOSITION_*` constants, `validate_disposition`, `project_disposition` and `execution_diagnostics` occupy roughly lines 900 to 1,700, about 800 of those production lines. The document would describe "the controller's disposition projection" and point at a unit that is not a module. | eliminate | Move the `DISPOSITION_*` constants, `validate_disposition`, `project_disposition`, `execution_diagnostics` and their unit tests into `controller/src/disposition.rs`, with the shared reply fixtures in a test-only module; no behavior change. |
| 6 | The validator has a diagnostic copy at the app's top level; the worker does not | `build.sh`; README "What ships"; `EXECUTABLES` in [tests/lib/artifact.py](../tests/lib/artifact.py) | AGENTS.md already lists this under "Two conventions are not obvious". `tests/suites/validator_batch_mode/` and the witness harness invoke the top-level copy directly. Every inventory must footnote the asymmetry. | eliminate | Drop the app-level validator copy from `build.sh`, the `EXECUTABLES` list, the evidence helper list, the dispatcher fixture layout and the README inventory; repoint the three suites and two Swift test files that used it to the bundle-local copy. |
| 7 | The `sbpl-check` fallback compiles only when no worker saw the policy | `fallback_policy_check` in [run_flow.rs](../controller/src/run_flow.rs) | The controller runs it only for an admitted `xpc_error` reply, to separate "runner unreachable" from "policy would not compile" in a nested sandbox. It is a side branch with its own 8 MiB capture budget and its own nested envelope. | not a strain | A feature with one trigger (an admitted `xpc_error` reply) and a unit-test pin; the document gives it one paragraph beside the sandboxed-harness note. |
| 8 | BYOXPC management is a large share of the controller | [runner_manager.rs](../controller/src/runner_manager.rs), [runner_commands.rs](../controller/src/runner_commands.rs), `bundle.rs`, `plist.rs`, part of `runner_select.rs` | Production lines: `runner_manager.rs` about 1,050 (tests begin at 1,054), `runner_commands.rs` 986, `bundle.rs` 29, `plist.rs` 32; the nine Swift files under `runner/Sources/PWRunnerCore/` total 5,829, of which `PWRunnerAPI.swift` is 1,994. Registry schema, advisory lock, `pending` and `pending_cleanup` states, and report-only `reconcile`. The survey's spoken comparison overstated this; these are the numbers. The question is proportion, not correctness. | not a strain | Proportion is not the document's subject; section 8 describes BYOXPC as a variation on launch and selection and stays short. |
| 9 | The "controller family frame" exists but is never named | [CONTRACT.md](CONTRACT.md); `json_contract.rs` shared by `#[path]` into both helper binaries | The same envelope number frames the controller's output, the observer report and the helper envelope, and CONTRACT.md describes it in a sentence each time. Naming the concept once would shorten several paragraphs. | eliminate | Name the shared outer object the envelope frame in CONTRACT.md's prose, in the controller README's observer paragraph and in the module doc of `json_contract.rs`; the document uses that name. |
| 10 | Records may be linked only from plan files, and until this plan there were none | [records/AGENTS.md](../records/AGENTS.md) | `git ls-files` showed no `*-PLAN.md` before 2026-10-03, so the records there were unreachable by policy. This plan is not associated with that record and does not link it. Not a matter for the architecture doc; a matter for the records convention. | not a strain | Struck: a records-convention question, not the document's. |
| 11 | The validator wire has no version marker and sits outside the worker identity | [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c); `ValidatorClient.swift` | The identity digest covers `controller/tools/pw_probe_runner/` and `runner/Sources/`, not the validator source. The NDJSON contract is pinned by the `validator_batch_mode` suite and by co-shipping in one bundle. Every other boundary in the inventory carries a number or a digest. | footnote | The validator wire carries no version because the host and the validator are built, signed and shipped inside one XPC bundle, so no cross-version pairing can occur; the `validator_batch_mode` suite pins the NDJSON shape. |
| 12 | The design principles live in AGENTS.md as operating instructions | "Core ideas" in [AGENTS.md](../AGENTS.md) | The architecture doc will restate the same six ideas as constraints paired with the mechanism that enforces each. Two copies of the principles would then exist. | not a strain | AGENTS.md keeps the six headlines as operating instructions; the document pairs each with its mechanism, and the step 5 router row links the two. |

## Proposed shape of the document

Spine: one run, phase by phase. Ordering is the architecture here. "Predictions
precede attempts" is a temporal claim, and each other principle appears as a
constraint on a particular phase. Each phase carries the same sidebar: what
crosses the boundary, who owns the bytes, what guards them.

Sections in order:

1. Why these processes exist: `sandbox_check` needs a live PID and application
   is one-way, so each specimen needs a fresh process and the reply path must
   stay outside the policy under test.
2. Process inventory (table below).
3. One run in time, with an ASCII sequence diagram. The repository has no
   diagram anywhere; the release-barrier timeline is the single highest-value
   artifact the document can add. Diagram decision (2026-10-05): dot is
   preferred. Figures are generated from `docs/architecture.json` by
   `docs/generate_architecture.py`, so a node or edge is chased by its id to a
   manifest row and from there to the symbol and the check that pin it. The
   SVGs are rendered by the installed Graphviz and stamped with the hash of
   their dot text; a `source_drift` case checks every copy without needing
   Graphviz. ASCII is used only where dot cannot express the figure, which is
   this timeline. Three dot graphs: process topology (section 2), boundaries
   (section 5) and the document graph (section 7).
4. Evidence channels and a field-group ownership map: prediction, attempt,
   comparison, disposition, dossier, log capture; who writes each; the rule that
   log evidence never changes execution evidence.
5. Boundary inventory (the table above, verified).
6. Principles as enforced constraints: each core idea paired with its
   mechanism. For example, host invariance is enforced by the source rule in
   `source_drift` plus the `nm -u` artifact inspection; predictions-precede-attempts
   by the `proceed` and `proceed_observed` sentinels plus the opt-in
   order-barrier mutation control.
7. How the system verifies itself: mechanisms, not suites.
8. BYOXPC as a variation on launch and selection, kept short.

Size target: 300 to 500 lines. Current behavior only.

### Process inventory (draft, verify in step 3)

| Executable | Language | Where | Started by | Under the specimen sandbox | Native sandbox API | Lifetime | Channels |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `policy-witness` | Rust | app top level | the user | no | none | one run | argv in; one JSON envelope on stdout; spawns the client, the observer and (fallback only) `sbpl-check` |
| `pw-runner-client` | Swift | app top level | controller | no | none | one run | request on stdin, read to EOF before connecting; `NSXPCConnection`; reply or synthetic `xpc_*` reply on stdout |
| `PWRunner` (host) | Swift | inside the XPC bundle | launchd: XPC service lookup, or a LaunchAgent Mach service for BYOXPC | no | none, by the invariance rule | one specimen; exits 50 ms after replying | XPC in and out; shared memory plus two pipes to the worker; two pipes to the validator |
| `pw-probe-runner` | C | inside the XPC bundle | host, `posix_spawn` | yes; applies the policy to itself | `sandbox_compile_string`, params, `sandbox_apply` | until the host requests exit; spins after `done` | fd 0 policy pipe, fd 3 shared memory, fd 4 ready pipe |
| exec helper children | caller-supplied | caller's path | worker, `posix_spawn` | inherit the worker's sandbox | none of PW's | bounded by the exec deadlines and budget | stdout and stderr pipes into bounded slot buffers |
| `sb_api_validator` | C | inside the XPC bundle; diagnostic copy at app top level | host, after `applied` | no | `sandbox_check` | one batch | NDJSON probes on stdin, verdicts on stdout |
| `sandbox-log-observer` | Rust | app top level | controller, after execution completes, in its own process group | no | none | one scan | budget on argv; JSON report on stdout; spawns `log show` |
| `log show` | OS | `/usr/bin/log` | observer | no | none | one query | text on stdout, bounded by the observer |
| `sbpl-check` | Rust | app top level | controller, only for an admitted `xpc_error` reply | no | `sandbox_compile_string` and params; never applies | one compile | held request bytes in; helper envelope on stdout |

### One run in time (draft phase list, verify each against source)

1. Controller: parse arguments; collect host facts; load the evidence manifest
   once; read the request; request version gate; optional runner-mode
   injection; selector parse; runner selection from the manifest entry or the
   registry; augment resolution; dossier; strip selector fields; serialize once
   into the held bytes.
2. Controller to client: held bytes on stdin; the client reads to EOF before
   connecting; `runSpecimen(Data)` over `NSXPCConnection`.
3. Host admission: caller authorization by Team ID and optional allowlist;
   decode with closed keys; capacity admission; meaning validation; policy hash.
4. Host to worker: create and zero the shared region; write magic, identity,
   counts, slots, params, capture nonce; pre-touch every page; `prepared`;
   pipes with `FD_CLOEXEC` and `F_SETNOSIGPIPE`; `posix_spawn` with fds 0, 3
   and 4; write the policy bytes; read the ready byte within its window.
5. Worker before apply: map the region; refuse on magic or identity mismatch
   (exit 4) or unprepared header (exit 5); bound counts; NUL-terminate strings;
   read the policy (size cap, embedded NUL refusal); params; compile; optional
   capture; ready byte; `sandbox_apply`; `applied`.
6. Host on `applied` with `apply_rc` zero and identity match: premature
   publication check; fire the hook; validator spawned as `--batch <pid>`,
   probes written and verdicts read under `poll()` with an I/O deadline;
   the hook returns; collection is closed; `proceed` stored.
7. Worker: `wait_for_proceed` within its budget (failure code 8 on expiry);
   `proceed_observed`; attempts in plan order (an exec attempt creates its
   pipes and spawn handles here and releases them before its slot completes);
   each slot's outputs then `completed` with release ordering; `done`; spin
   until `exit_requested`.
8. Host: poll for `done`, a reaped child, the sentinel deadline or a wait
   error; `exit_requested`; grace; terminate; final acquire snapshot; decode
   worker evidence; build output.
9. Host assembly: disposition record; classify; ordering; per-step results
   (query from the verdict or synthesized unavailable, attempt from the slot,
   comparison); subprocess objects; host-side path diagnostics; encode with
   degradation; reply; exit.
10. Client prints the reply. Controller: capture within its budget; admit by
    version; `sbpl-check` only for `xpc_error`; complete execution, including
    the disposition projections; then log capture with the observer in its own
    process group over the padded client span, correlation, and the envelope.

### Rules the document follows

- Describe current behavior. No change-history notes; `git log` is the history
  ([AGENTS.md](../AGENTS.md) "Documentation").
- Do not repeat contract version numbers in prose. Either carry the generated
  region by adding the file to `TARGETS` in `docs/generate_contract.py`, or
  link [CONTRACT.md](CONTRACT.md) and say nothing numeric. Prefer the latter.
- Do not enumerate bundle paths. The layout is already a contract in three
  places (README "What ships", `EXECUTABLES`, `build.sh`); the inventory names
  locations at the granularity of "app top level" and "inside the XPC bundle"
  and links the README for exact paths.
- Link the sandboxed-harness note; do not add a fourth copy.
- Do not link `records/`.
- Every relative link must resolve from `docs/`; the `source_drift` link check
  reads every `docs/*.md`.
- Prefer links to copies. If the document must state a fact another document
  also states, the two should either share text under a checked marker region
  or one should link the other.

## Drafting log

Entries are added during step 3. Each names the claim, where it was pinned or
why it could not be, and any contradiction found with an existing document.
