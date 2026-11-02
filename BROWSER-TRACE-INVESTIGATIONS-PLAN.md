# Browser trace investigations: starting points for sandbox-extension experiments

This plan investigates under what restrictions an already sandboxed issuer can
delegate usable file authority to another sandboxed process. Q1 and its bounded
query companion Q2 are the only active questions. The first investigation uses
an independent native fixture and ends in a durable report for maintainer review,
whether issuance, consumption or access succeeds or fails.

The plan is linked to a source packet at
[records/browser-sandbox-sources](records/browser-sandbox-sources/README.md). 
The packet persists in `records/` while this plan lives.

## Boundary

Every experiment under this plan respects these limits.

- **Independent process roles.** Production PolicyWitness applies one policy
  once to one disposable worker. This pilot instead uses a fresh supervisor,
  issuer and recipient per trial. The issuer and recipient each apply their own
  policy once, except for the explicitly unsandboxed issuer baseline.
- **Sources nor browsers.** Reports may identify Chromium, Firefox, WebKit and
  Ladybird as motivating sources. Runtime findings describe the fixture and its
  recorded environment, not an installed browser.
- **Token confinement.** Raw tokens never enter a request, reply, report
  or retained artifact. The erasure discipline in
  [supplied extension authority](docs/WORKER.md#supplied-extension-authority)
  applies to any new issuer, channel or consumer the experiments introduce.
- **Keep the observations distinct.** A nonnull issue result, accepted transfer,
  consume return and fresh read establish different facts. Known bytes read
  through a newly opened descriptor establish that access in that process at
  that boundary. Their controlled contrast can support a bounded delegation
  finding; they do not reveal private kernel state or establish general
  permissions, revocation or the cause of a permission-shaped failure.

## Where PolicyWitness stands

Read current behavior from these sources rather than from this summary.

| Topic | Where |
| --- | --- |
| Request shape, two classes, one declaration, one consume, one release | [Sandbox extensions](docs/PolicyWitness.md#sandbox-extensions); [extension output](docs/PolicyWitness.md#extension-and-fresh-read-output); [QUESTIONS.md](docs/QUESTIONS.md#can-policywitness-test-sandbox-extension-behavior) |
| Issuer, channel, worker preparation, lifecycle calls, erasure, known gap | [Supplied extension authority](docs/WORKER.md#supplied-extension-authority); [known gaps](docs/WORKER.md#known-gaps) |
| Limits and the issue-before-spawn ordering | [Specimen admission](docs/LIMITS.md#specimen-admission) rows `extension_*`; [interactions that matter](docs/LIMITS.md#interactions-that-matter) |
| Issuer implementation | [`pw_extension_issuer.c`](controller/tools/pw_probe_runner/pw_extension_issuer.c): `dlopen` of libsandbox, `sandbox_extension_issue_file` with flags `0`, class chosen by the `authority` field; [`pw_extension_channel.h`](controller/tools/pw_probe_runner/pw_extension_channel.h) |
| Worker side | [`prepare_extension`](controller/tools/pw_probe_runner/pw_probe_runner.c) resolves consume/release symbols before apply and validates the channel before apply; [`attempt_extension`](controller/tools/pw_probe_runner/pw_probe_runner.c) treats only `-1` as a failed consume and keeps one static handle |
| Host session | [`ExtensionIssuer.swift`](runner/Sources/PWRunnerCore/ExtensionIssuer.swift): `realpath` and `fstatat` before issuance, issuer spawned and reaped before the worker exists |
| Query side | [`sb_api_validator.c`](controller/tools/sb_api_validator/sb_api_validator.c): query arguments, no-report flag and result classification; `NONE` or one filter value, with no class-plus-path representation |
| Native fixture and its controls | [suite README](tests/suites/sandbox_extensions_native/README.md); [fixture README](tests/fixtures/sandbox_extensions/README.md); host, issuer and worker as three processes; file and directory scenarios |
| Production extension controls | [native extension boundaries](tests/suites/witness_contract/README.md#native-extension-boundaries) and the `check_extension*.py` checkers beside it |
| Evidence contract | [native extension evidence](tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence); [native sandbox extensions](tests/CHANGE-VERIFICATION.md#native-sandbox-extensions) |
| Process topology and architecture account | [process topology](docs/ARCHITECTURE.md#process-topology); [docs/architecture.json](docs/architecture.json) and its generator |

Production PW has no post-apply issuance action. Query operation
strings remain OS queries under [request admission](docs/REQUEST-GRAMMAR.md);
accepting a string does not establish a useful native prediction for it.

## Traces and the packet

[TRACES.md](records/browser-trace-investigations/TRACES.md) holds the seven
source traces T1–T7, the questions Q1–Q18 they raise, and the description of
the source packet at
[records/browser-sandbox-sources](records/browser-sandbox-sources/README.md).
Each trace names a source, states what it shows, states what PolicyWitness does
at the same point, and names the questions it raises.

## What we want to learn

The questions are stated once, in
[TRACES.md](records/browser-trace-investigations/TRACES.md#questions), each with
its observable, what it needs beyond this investigation's apparatus, and what an
answer does not establish. This plan refers to them by number only. Q1 and Q2
are the active questions; Q3–Q18 remain an unordered inventory for later review,
not commitments or automatic follow-ups to an unexpected result.

## First investigation: Q1 and Q2

Use an investigation-local adaptation of
[`tests/fixtures/sandbox_extensions/native.c`](tests/fixtures/sandbox_extensions/native.c).
Its existing host/issuer/worker split, separate token storage and explicit
descriptor passing are useful equipment. Its unsandboxed issuer and pre-policy
worker read change for this pilot.
Retain the adapted source with the investigation; do not edit production code,
the registered fixture, suite checkers or test catalog to conduct it.

### Records and retention

The first step, before any build, is to add a `.gitignore` rule for
`records/browser-trace-investigations/local/` and commit it. Everything else under
`records/browser-trace-investigations/` is committed for the life of this plan
and is disposed of or dispersed at retirement together with the ignore rule.

Commit the pilot source, driver and reader beside `REPORT.md`, with the text
evidence specified below. A committed record larger than a few megabytes needs
a stated reason in the report.

Build directly in `local/<apparatus-revision>/`: executables, objects, debug
symbols and other regenerable build products stay there. Do not use `.tmp/`
for this pilot. The committed hashes and read-backs identify the local products.
The report must be readable without `local/`; where it cites an item there, it
says the item is gitignored and available only in the local checkout, per
[records guidance](records/AGENTS.md). Core dumps are disabled, and tokens,
token hashes and token-bearing diagnostics are never written to either location.

### Equipment setup

Use an investigation-local driver at `records/browser-trace-investigations/run.sh`.
From the repository root, outside any automation sandbox, invoke it through:

```sh
tests/lib/checkout_lock.sh -- /bin/sh records/browser-trace-investigations/run.sh
```

The driver owns build/signing commands, block execution, cleanup accounting and
evidence finalization under that lock. Separate block invocations use the same
wrapper. Honor a busy-lock refusal; never unlink `tests/.checkout.lock`. Preserve
the inherited lock descriptors through intermediate launchers as required by
the [lock contract](tests/README.md#retention-ownership-and-execution-locking).

Adapt the native fixture's [build command](tests/fixtures/sandbox_extensions/build.sh)
to the pilot source and the revision's `local/` output directory. Select
`pilot_identity` from `PW_BYOXPC_IDENTITY`, falling back to `IDENTITY`; require
an explicit `Developer ID Application: ...` identity. Set `pilot_binary` to the
new executable and run the fixture's signing and read-back sequence:

```sh
/usr/bin/codesign --force --options runtime --timestamp -s "$pilot_identity" "$pilot_binary"
/usr/bin/codesign --verify --strict --verbose=4 "$pilot_binary"
/usr/bin/codesign -dvvv "$pilot_binary"
/usr/bin/codesign -d --entitlements :- "$pilot_binary"
```

Require successful verification, the selected authority and runtime flag in the
signature read-back, and absent or empty entitlements. Do not seek another
signing context on failure. All three roles exec this same signed binary; child
environments are `PATH=/usr/bin:/bin` and `LC_ALL=C`.

Retain one equipment record per apparatus revision: source commit/status and
source hashes; build/signing/read-back command arguments, results and output;
executable path and post-signing hash; selected identity and entitlement result;
macOS build, Darwin release, architecture, SDK and compiler facts. Trial records
reference that record rather than duplicating it.

### Preparation and application boundary

The first result concerns issuance after application with a prepared native
runtime. It does not claim issuance before any initialization, or reproduce
Chromium's framework startup. [T7](records/browser-trace-investigations/TRACES.md#t7-context-only-traces)
explains why the boundary must be explicit.

| Stage | Operations and evidence |
| --- | --- |
| Supervisor before child launch | Create owned regular files A and B with known bytes in the driver's fresh trial directory. Resolve their canonical absolute paths, record metadata and ordinary fresh-read baselines, and close target descriptors. Prepare exact policies and separate evidence/token channels; the token channels start empty. Pass strings and apparatus descriptors, never a target descriptor or pre-issued token. |
| Each child before apply | Map the explicit channels, close their mapping descriptors, disable core dumps, resolve the needed libsandbox entry points, initialize fixed reporting storage, and compile the row's policy. No target open, target `stat`/`realpath`, extension issue/consume/release, or extension warm-up occurs in either child before apply. |
| Application | Each sandboxed child applies its policy once and publishes the native result before advancing, with C0's omission specified in the matrix. Failure withholds dependent actions and remains evidence. Source order and supervisor gates associate the application and later call publications with the same owned process. |
| After apply | The recipient opens, reads, identifies and closes A before token consumption. The supervisor completes Q2 against the waiting issuer, then releases its first issuance call. Native path processing within that call therefore occurs under the issuer's policy. The recipient validates the subsequent transfer, optionally consumes, and makes another fresh open/read/identity/close attempt. Record unavailable stages explicitly when issuance or transfer fails. |

Use the minimal C/libsystem/libsandbox setup of the existing native fixture;
do not add application frameworks or optional allocation instrumentation. Symbol
resolution before apply avoids confusing a loader failure with issuance refusal.
The supervisor's path preparation supplies names and metadata, not open-file
authority to the children.

Inspect the retained source and linked/loaded-image inventory for pre-apply
acquisitions. Collect descriptor snapshots at the exact boundaries specified in
the [trial record](#trial-record-and-reader-checks). A target descriptor already
present invalidates a fresh-acquisition inference. The recorded preparation and
order are not a complete census of transient resources, Mach rights or private
library initialization. A comparison of pre- versus post-apply framework loading
is later work.

### Fixed contrasts and positive controls

Use one signed executable with empty entitlements for all roles, identical
credentials, environment, path preparation and flags `0`. Every native issue call
requests `com.apple.app-sandbox.read` for A. B is another existing owned regular
file used only as the nonmatching policy path. Keep the issuer's ordinary data
and metadata read rules permissive in this first investigation; whether issuance
can exceed the issuer's own read access is not answered by these contrasts.
All sandboxed issuer policies use this exact common prefix, in this order:

```scheme
(version 1)
(allow default)
(deny file-write*)
(deny file-issue-extension)
```

The file-write restriction guards against unintended issuer writes; it is fixed
equipment policy, not a variable in the issuance-filter contrasts. Independent
target observations, rather than that rule's presence, establish preserved bytes.

C1 appends `(allow file-issue-extension)` to the prefix. C2 appends:

```scheme
(allow file-issue-extension
  (require-all
    (extension-class "com.apple.app-sandbox.read")
    (literal "<canonical A>")))
```

C3 appends nothing. C4 changes only C2's predicate string to
`com.apple.app-sandbox.read-write`; C5 changes only its literal to canonical B.
C6/C7 use C2's issuer policy. Substitute the actual escaped canonical paths for
the placeholders before compilation. C1 and C2 share the issuance denial and
differ only in the allow clause's filter.

Keep this clause order fixed. Failure of an intended exception is an observation,
not a reason to rearrange clauses during the pilot or infer a general precedence
rule from these compositions.

The recipient's fixed prefix is `(version 1) (allow default)
(deny file-read-data)`, followed by
`(allow file-read-data (extension "com.apple.app-sandbox.read"))` except in C7.
The intended exception is access through that predicate; runtime observations
establish whether it operates in these trials.
No descriptor spans the two access attempts. The supervisor independently checks
target identity and bytes before and after the trial. A pre-consume successful
read is retained but prevents claiming that the later read demonstrates newly
delegated access. Neither child spawns the other; the supervisor execs fresh
siblings so that the recipient does not inherit an issuer's applied policy.

| Row | Issuer arrangement | Recipient intervention | Purpose |
| --- | --- | --- | --- |
| C0 | C1's preparation, including compilation of its policy; omit only application | Consume if delivery permits | Ordinary-authority baseline for this binary, class, target, OS and recipient path |
| C1 | Common prefix plus unfiltered issuance allow | Consume if delivery permits | Candidate matched positive control for restricting issuance by class and path |
| C2 | Common prefix plus allow filtered by read class and literal A | Consume if delivery permits | Matching restricted delegation |
| C3 | Common prefix only, retaining its issuance denial | Consume if delivery permits | Absence of the issuance allowance |
| C4 | Same as C2, but allow predicate names the read-write string | Consume if delivery permits | Different class string from the native call's read class; runtime discrimination remains to be observed |
| C5 | Same as C2, but allow predicate names literal B | Consume if delivery permits | Path mismatch with the native call still targeting A |
| C6 | Same as C2 | Accept transfer but omit consumption | Separate delivered bytes from consumed authority |
| C7 | Same as C2 | Consume if delivery permits; omit recipient extension predicate | Separate consumption from access allowed through that predicate |

No read-write issue call, symlink, directory, flag variant, process-bound token,
self-consumption or release comparison is part of this matrix. After the final
read, erase owned token buffers and reap the children; omission of release is
fixed across rows and supports no claim about exit-time revocation.

Nonnull issuance alone is only a positive control for token production; a usable
delegation control additionally needs accepted transfer, a consume result and
known bytes from a fresh recipient read beside its before-consume observation.

The host-level prior for C0 is already pinned. The 0.3.4 release acceptance in
`tests/RETAINED.json` ran at the commit `v0.3.4` resolves to, and its battery
passed the four production extension cases in `witness_contract` (`extensions`,
`extension_boundaries`, `extension_combinations`, `extension_directory`): the
app's signed issuer under ordinary authority, the app's signed worker consuming
after apply, and fresh reads through the predicate. The opt-in native suite did
not run in that acceptance; the retained run `workset-native-crossed-01` is its
nearest evidence, from an ancestor of the tag with fixture and suite sources
identical to the tag's, and its `lifecycle` row has C0's shape. Cite both as
context for this host, OS and identity. Neither replaces C0: the inference from
C0 to C1 needs the pilot's own binary, signing read-back, credentials, path
preparation, policies and recipient. A C0 failure makes differences from that
working apparatus and recorded host context the first diagnostic focus; the
prior alone does not establish the cause of a new failure. Referenced evidence
keeps its managed ownership and is not copied into these records.

For the pilot's bookkeeping, the consume sentinel is the signed 64-bit value
`-1`, following the native fixture's convention. Other values, including zero,
are candidate handles rather than proof of success. Always retain the raw value
and attempt the second fresh read, including after `-1` or omitted consumption.
This convention does not settle the wrapper disagreement in Q5; access evidence
is necessary for every delegation inference below.

Read the matrix through the following table. Each row names the Q1 part it
serves (see the question's parts (a)–(e)), a condition on valid observations
from one apparatus revision, what that condition supports, and what it
withholds. "Nonnull" and "null" are the raw issue return; "accepted" is the
recipient's transfer acceptance; "fails" for a fresh read means no known bytes
with matching identity. A row's withheld column applies even when its
supported column is empty. No control's success is required for closeout.

| Part | Condition | Supports | Withholds |
| --- | --- | --- | --- |
| (a) | C0 nonnull, C1 null | The difference concerns applying the entire C1 profile, including the fixed write denial and the combined issuance rules | Isolating a class/path restriction; that sandbox application alone prevents issuance |
| (a) | C1 nonnull, C2 null | With the prefix shared, the filtered allow clause or its runtime interpretation is at issue | Any claim about the prefix itself |
| (a), (e) | C2 nonnull; C3, C4 or C5 null | A finding scoped to that row's single changed rule and the recorded environment | An errno-based claim about kernel cause |
| (a) | C0 and C1 both fail at one stage | Preservation of the results; neither designated baseline establishes feasibility at that stage | Restriction-specific negative conclusions that need a working baseline |
| (b)–(d) | Issuance nonnull; delivery, consumption or fresh access fails | Each stage's own observation, reported separately | Collapsing the later stages into issuance refusal |
| (d), (e) | C2 and C6 both accepted; both pre-consume reads fail; C2 reads known bytes after a consume return other than `-1`; C6's second read fails | Consumption-dependent delegation in this setup; delivery alone produced no access in C6 | A general consumption claim beyond this apparatus |
| (d), (e) | C2 and C7 both accepted; both pre-consume reads fail; both consume returns other than `-1`; C2 reads known bytes; C7's second read fails | A role for the recipient's extension predicate; the consume return alone does not establish access | A general predicate claim beyond this apparatus |
| (d), (e) | Delivery or consumption fails in C2, C6 or C7 | The stage observations | Every contrast that requires the failed stage |
| (d), (e) | Pre-consume access in any row; access in C6 or C7 despite the omission; or no access gain in C2 | Those observations and their limits, without another trial | The proposed consumption/predicate separation |
| any | A usable restricted result while another control is unavailable | The result as evidence, with the inconsistency explicit | Any contrast that needs the unavailable control |

### Ordering and query protocol

Both children publish their preparation and application state before issuance.
The recipient's first fresh access precedes consumption, and its second follows
the consume result or recorded omission/unavailability. Keep issuance return,
bounded token publication, transfer readiness, recipient acceptance, consume
return and read results as separate publications. Preserve partial evidence when
a process dies between a native call and publication; never invent its return.
Transfer evidence includes framing/length validation and a transient equality
check between issued and received bytes. Retain only the check result, never
tokens, token hashes, token-bearing diagnostics or core files.

For Q2, the supervisor calls `sandbox_check` directly from the signed pilot
executable. Make exactly the `NONE` and `PATH(A)` queries for
`file-issue-extension` against the live issuer paused before issuance in each row.
Use filter IDs `NONE=0` and `PATH=1`, OR'd with the no-report value. Resolve
`sandbox_check` and `SANDBOX_CHECK_NO_REPORT` through `dlsym` in the supervisor,
and dereference the exported flag as an `int`. If either symbol is unavailable,
mark Q2 unavailable and continue Q1; do not substitute a literal flag or an
unflagged call.

Any derived allow/deny labels use the convention in the
[validator's batch classifier](controller/tools/sb_api_validator/sb_api_validator.c):
`rc == 0` maps to allow and `rc == 1 && errno == 0` maps to deny.
This is an interpretation convention, not a calibrated native contract for
`file-issue-extension`. Negative returns are query errors; other unexpected
return/errno combinations remain unclassified. Retain `EINVAL` as a diagnostic,
not a denial. Expect a trivial allow answer in C0, but preserve any other result
without making that expectation a continuation requirement. A query answer does
not establish usable issuance.

Missing query capability or a native query failure does not prevent Q1. The
recipient is not the query target. Do not add filter-ID searches, alternate query
APIs or recipient before/after query experiments from Q18.

Record availability and observed patterns separately from representational
adequacy. The pilot's ordering evidence is not PW's `comparison.order=query_first`.

Unified-log collection is outside this pilot: query and issuance denials can be
attributed to the same issuer PID. Request suppression, but do not claim to have
verified it or verdict invariance, or treat incidental log lines as issuance
evidence. No flagged/unflagged comparison is added.

### Trial record and reader checks

Retain one token-free record for every planned position and diagnostic rerun.
The following is the complete observation checklist; shared equipment and
block-schedule records may be referenced by identity. For every operation,
distinguish attempted with a published result, omitted by design, unavailable
with a reason, and interrupted without a published result. Clear errno before
native calls and save it immediately afterward; it is diagnostic alongside the
call's raw return, not an independent failure on a successful call.

| Record group | Required contents |
| --- | --- |
| Trial and equipment | Arrangement C0–C7; block, position within block and chronological position; chosen sequence and scheduling-rationale reference; apparatus revision and equipment-record reference. For a diagnostic rerun, original trial identity and correction-cycle number, outside the planned positions. |
| Processes and ownership | Supervisor, issuer and recipient roles, PIDs, process start identities, credentials and executable identity; environment; parent/child and process-group membership; owned temporary paths and channel identities. Record each launch as it occurs so cleanup ownership survives partial execution. |
| Inputs and targets | Exact expanded issuer and recipient policy bytes and compilation results; class and flags; canonical A/B paths, expected identities and known bytes; supervisor fresh-read/identity baselines before child launch and independent identity/content checks after the trial. |
| Preparation and application | Per-role symbol-resolution and preparation results, linked/loaded-image inventory, descriptor snapshots at the boundaries below; application count and raw result/errno, or C0's explicit omission. |
| Ordering | Per-process ordered stage publications, supervisor acknowledgements and query collection/release markers linking preparation, application, each access, issuance, transfer and consumption to the same owned processes. |
| Issuance and transfer | Issue attempted/unavailable, null/non-null return and errno; bounded publication, framing/length validation, transfer readiness and recipient acceptance; transient issued/received-byte equality result. Retain no token or token hash. |
| Consumption and access | Raw signed 64-bit consume return and errno or omission/unavailability; for each recipient fresh read, separate open, descriptor-identity, read and close attempts/results/errno, descriptor number, observed identity and obtained bytes. These establish the known-byte match and descriptor closure independently of the consume label. |
| Queries | Caller and target PIDs; API/flag lookup outcomes and resolving library images; numeric exported flag, filter ID/value and complete type argument; operation string and raw return/errno pair or unavailability. Keep derived labels separate. |
| Completion and cleanup | Token-buffer erasure observations; elapsed times and any deadline reached; child exit publications and independent wait/reap results; signals sent and results, supervisor exit and process-group absence observations; temporary-resource removal results and any pending cleanup ownership. |

Descriptor snapshots have fixed points. For the issuer, take three: on entry
before preparation, immediately before the application boundary (also in C0),
and immediately before issuance. For the recipient, take four: on entry before
preparation, immediately before apply, immediately before the first target open,
and immediately before the second target open. Each snapshot lists descriptor
numbers, types and available identities, including apparatus descriptors and
any match to A/B; record inspection failures. Mark snapshots unavailable if their
boundary is not reached. Source inspection accounts for acquisitions between
snapshots; the snapshots do not claim to observe transient acquisitions.

The report reader checks evidence completeness and consistency separately from
whether delegation occurred. Retain its command, constructed control inputs and
results beside the trial records. The controls must:

- Reject missing/reordered application or transfer evidence, a target descriptor
  inherited or held across access boundaries, and claimed read success without
  matching identity and bytes. Descriptor-number reuse alone is not retention.
- Keep a negative query return and an unexpected return/errno pair out of the
  denial count. These checks establish reader behavior, not native semantics.
- Accept honestly recorded native refusal, failed consumption, unavailable
  queries and missing dependent stages, without requiring positive outcomes.

Constructed inputs establish reader behavior on inputs the reader's author
shaped. They do not establish that the reader is connected to the evidence the
experiment actually produces. So, once a planned trial has produced a record
that the reader accepts as a complete delegation sequence, make a disposable
copy of that record and remove or corrupt exactly one essential link in its
execution chain, for example delete the issuer's issuance publication while
leaving the recipient's acceptance, consume return and fresh-read observations
intact. Run the reader on the copy. It must no longer accept the copy as
evidence of the complete sequence: the recipient observations it still holds
may be genuine, but the inference connecting them to issuance is now
unsupported. Retain the copy, the single change made to it and the reader's
output beside the constructed controls, named as a control derived from the
trial it came from so it cannot be read as a trial record. The original record
is never modified. This needs no additional native trial.

### Deadlines and cleanup

Use one 20-second monotonic execution deadline, starting immediately before the
supervisor's first child spawn and shared by all stage waits and normal reaping.
Do not restart it at each gate. On expiry or equipment failure, preserve partial
evidence, send `SIGKILL` to still-live owned children and allow at most two
additional seconds per child for reaping. Erase owned token buffers during
cleanup and record any erasure that could not be confirmed.

The driver creates a fresh trial directory under `/private/tmp`, records its
ownership, and starts each supervisor in a new process group; issuer and
recipient remain in that group. It imposes a separate 30-second outer deadline
from supervisor launch. On expiry or cancellation, it sends
`SIGKILL` to that owned group and waits at most five seconds for supervisor exit
and group absence. A reaped supervisor alone does not establish child absence.
These are equipment bounds, not native refusal results.

The driver owns the group and temporary trial directory; the supervisor owns its
direct children and channels. Remove trial targets and temporary resources only
after process absence is confirmed and the final observations are retained.
If absence is unconfirmed, mark cleanup pending in the durable trial record,
retain the owned paths and stop launching trials. Recovery must revalidate
process start identities and resource ownership; historical PIDs or a pathname
prefix alone do not authorize termination or removal. Keep unresolved ownership
in the incomplete report for review. Do not pass investigation output to the
test-run pruner.

### Repetitions and troubleshooting

Run the 24 planned trials in three blocks of eight. Each block contains exactly
one trial of every arrangement C0–C7, with fresh processes and targets for each
trial and all existing evidence requirements. Choose and record each block's
sequence before starting that block. Blocks two and three may be ordered after
reviewing earlier observations and equipment behavior. Retain the chosen
sequences, each trial's block and chronological positions, and any relevant
scheduling rationale, alongside every trial's observations.

Deliberately vary positions across blocks: do not consistently put C0, C1 and C2
first or repeat the same adjacency relationships among positive and negative
controls. Sensible positional variation is sufficient; formal randomization is
not required. Scheduling discretion does not permit changing the arrangements or
their contrasts after seeing results.

Use explicit equipment-readiness checkpoints. The first is required: once the
first block's C0 and C1 trials have both run, use their records to show that the
apparatus is connected end to end. The showing comes from those two records, not
from inspection of the apparatus: the issuer reached its issue call and its raw
return and errno are in the record; the token publication, framing result and
recipient acceptance are in the record; the recipient reached its consume call
and each fresh read, and every result is in the record; the queries were
collected and released at their marked points. Where an earlier stage failed,
the stages that depend on it are recorded as unavailable with that reason, not
absent. A call that was made and published a failure is evidence. A function
that was resolved but never invoked,
or invoked with a result that never reached the record, is a disconnected
apparatus, and goes to the troubleshooting allowance below as a diagnosed
fault. Successful issuance is not required, and this checkpoint adds no trial
and no approval step. Checkpoints between blocks review planned trials in the
same way rather than adding control runs. At every checkpoint record whether
process control, evidence collection and cleanup remain functional, and any
diagnosed fault. Distinguish broken apparatus or missing required evidence
from a correctly executed native call returning an unexpected result, including
dependent stages honestly recorded as unavailable. When equipment remains
functional, execute all 24 planned trials.

Allow at most two documented equipment/instrumentation correction-and-retry
cycles and 60 minutes of cumulative troubleshooting across the pilot.
Troubleshooting ends at whichever limit is reached first. Each cycle permits at
most one affected trial rerun, for at most two diagnostic reruns in total.
Record these reruns separately from the 24 planned positions; they do not replace
the original observations. Retain the original failures and any source changes;
never combine results from different apparatus
revisions as matched contrasts.

After a source-level correction, keep the existing block sequence and continue
its remaining planned positions on the corrected revision if equipment functions.
Those trials count toward the 24 planned positions; record the apparatus revision
for every trial. Earlier positions remain recorded on their original revision,
including any invalidated evidence. A block spanning revisions is not a complete
set of matched contrasts, even if all eight positions were executed. Report only
contrasts supported within one revision and identify the missing comparisons as
coverage gaps. A cycle's diagnostic rerun does not repair or restart
that block, and no earlier arrangement is backfilled. Execution of a planned
position and valid evidence for a contrast are separate counts in the report.

If equipment prevents further execution within the troubleshooting allowance,
report the remaining positions as unrun rather than starting another battery.
Necessary cleanup still follows [deadlines and cleanup](#deadlines-and-cleanup).
A larger redesign, changed signing context, extra contrasts or further retries
require review.

### Report and stopping point

Write `records/browser-trace-investigations/REPORT.md`. Its first section is a
per-question status table; equipment, coverage, control failures, preparation
and query limits, variable outcomes, pending cleanup and recommendations follow
it. Link the committed evidence; referenced existing suite evidence keeps its
managed ownership and location. Answers land under these rules:

- **One answer per question part.** Q1 is answered per part (a)–(e), never as
  one verdict. Q2 is answered as (a) observed and (b) representation. Q3–Q18
  receive no answers from this investigation.
- **Every answer carries one status:** answered within contrasts; partially
  answered, naming the valid contrasts; unanswered because of equipment; or not
  attempted. The status mirrors the trial record's stage vocabulary: attempted
  with a published result, omitted by design, unavailable with a reason,
  interrupted.
- **Observations before labels.** An answer cites trial identities and raw
  values, including raw query return/errno pairs, then the decision-table row it
  rests on, then that row's supported finding in the row's words, then its
  withheld column verbatim. Nothing is supported that the table does not name.
- **Contrasts are valid only within one apparatus revision.** An answer that
  spans revisions reports the covered contrasts and lists the missing ones as
  coverage gaps, with attempted and unrun positions distinguished.
- **Incidental observations are filed, not pursued.** Anything the planned
  trials show about an inventory question, such as every consume return value
  for Q5, is recorded under that number as incidental, with no added trial. It
  is not an answer.

Finish after all 24 planned trials, or with an incomplete report when equipment
prevents further execution within the troubleshooting allowance. Retain the
report and return to the maintainer regardless of whether delegation was
observed, queries proved useful or a feature seems warranted.

## Where later outcomes could land

Possible recommendations for maintainer review after the report:

- **Report only.** Observations, including failures or inconclusive controls,
  can close the investigation without any product change.
- **Documentation.** Narrowing or restating the known gap in
  [WORKER.md](docs/WORKER.md#known-gaps), the FAQ answer in
  [QUESTIONS.md](docs/QUESTIONS.md), or a premise in
  [LIMITS.md](docs/LIMITS.md#premises-behind-the-interactions). Documentation
  describes current behavior only; no change history.
- **Fixture cases.** New opt-in cases in `sandbox_extensions_native` with
  constructed checker controls, under
  [add or change tests](tests/AGENTS.md#add-or-change-tests) and the suite's
  evidence rules.
- **Request grammar and admission.** A new lifecycle action, new `authority`
  values, flags or classes touch [the wire contract](docs/CONTRACT.md) and its
  version decision, [REQUEST-GRAMMAR.md](docs/REQUEST-GRAMMAR.md), the limits
  manifest and its regenerated document, the admission corpus, and worker
  identity regeneration.
- **Worker or runner structure.** A future production issuance action or
  process-binding capability could change the authority account, process
  topology or token channel. Process-binding timing relative to the target's
  apply is untested (Q13–Q16). Any proposal would identify affected
  implementation, contracts and checks:
  [architecture.json](docs/architecture.json) for topology changes, C/Swift layout
  agreement when layout changes, and the
  [order-barrier mutation control](tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls)
  when wait, release or eligibility changes. The independent pilot does not
  require retiring PW's ordinary-authority issuer.

## Boundaries owned elsewhere

- **Faithful cross-process delivery.** Issue in one sandboxed process and
  consume in another as a product capability needs a model of a second process
  that production PW does not have. A later proposal would own it. Q1's fixed
  native issuer/recipient experiment establishes no general product capability;
  Q14's process-binding control remains deferred.
- **Mach, IOKit and generic classes**
  ([T6](records/browser-trace-investigations/TRACES.md#t6-non-file-extension-classes-boundary-not-a-starting-point)).
  Each needs a new issuer entry point,
  an attempt kind and a class vocabulary decision. A later plan.
- **Browsers as products**, installed-profile evidence, and anything the packet
  report lists as outside the sources.

## Considerations for later review

These preserve possible directions from the traces without expanding Q1/Q2.

- **Self-consumption is distinct from delegation.** Q3 asks whether an issuer
  can widen its own access; Q4 asks about issuing under an extension predicate.
  Neither is needed to observe Q1. The Chromium Metal comments motivate a helper
  recipient, while other retained constructions have different or unspecified
  callers. They do not supply one common browser runtime story.
- **Native equipment and product integration are separate.** Production has no
  issue action and admits a bounded authority vocabulary. The independent fixture
  can investigate native calls without first changing that grammar. Promotion
  would require a separate decision about useful coverage and maintained checks.
- **Preparation remains part of the result.** The initial issuer has permissive
  read rules and pre-resolved symbols. Testing tighter ordinary access, loading
  strategies or additional ambient restrictions would change that premise and
  needs another bounded question, not an automatic response to refusal.
- **Binding creates choices, not a prescribed topology.** Q15 concerns obtaining
  a child's audit token and accounting for the resources used. A recipient waiting
  before apply is a candidate arrangement for later testing, not established
  bound-token behavior. Any claimed confinement benefit would need its own
  observations and would not replace token erasure.
