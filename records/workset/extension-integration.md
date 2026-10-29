# Public directory authority and fresh write observations

E2 follows E1 acceptance at `d2f3bbf`. Design preparation is primary-agent C/ABI
review plus read-only review by `design_extension_integration` of admission,
Swift transport and independent consumers. This record owns the bounded
addition; the C and Swift modularization plans have not begun.

## Request and evidence

Add optional extension declaration `authority`, admitting only `read` and
`read_write`, with absent/null retaining `read`. The native classes remain
internally selected: `com.apple.app-sandbox.read` and
`com.apple.app-sandbox.read-write`. No caller-supplied class or token is accepted.
Keep the existing resolved target preparation and ordinary issuer. Directory
scope follows the native target; no new broker or workflow construct is needed.
Carry the admitted authority as a bounded integer in the transient channel's
reserved bytes and report the actual selected class. Preserve target/token
offsets and channel size; reject unknown internal authority before issuance.

Add file actions `write_fresh` and `create_fresh`. Both attempt a fixed one-byte
`x` write on a fresh descriptor. The first opens without implicit truncation,
then explicitly truncates to zero; the second opens with `O_CREAT|O_EXCL` and
mode 0600. Neither changes legacy `open_write` or `create`. No caller payload or
new payload limit is introduced. Neither opens any target before application.

Completed new actions publish `fresh_write`, with separate `open_rc/errno`,
`truncate_rc/errno`, `write_rc/errno` and `close_rc/errno`. Optional metadata
observations `preopen_stat`, `opened_stat`, `truncated_stat`, `written_stat`
each contain native `rc`, failure `errno`, and successful `identity` plus `size`.
`preopen_stat` is lstat immediately before exclusive creation only; it is
diagnostic and does not suppress the open or independently determine success.
Opened/truncated/written metadata come from the actual descriptor. Truncate and
its metadata are absent for creation; write and its metadata are absent after
failed truncation; close remains attempted after any successful open. Preserve
short transfers and all observed later failures. A short write is a failed
operation without an invented errno. The summary uses `write_failed`; effects
still need independent contents/entry observations. Unpublished slots provide
no completed fresh-write evidence.

Internal metadata records occupy 48 bytes each. A 232-byte fresh-write record
is carved from the existing slot reserve after exec evidence; existing offsets
and total slot size stay fixed. All optional native rc values use the existing
internal -2 unattempted convention, decoded to absent fields. Native calls
publish only through the existing completed-slot release gate. No wait, release
or query eligibility algorithm changes are planned.

Request schema remains unchanged because old requests and meanings are
preserved. Bump response schema to 24 because the extension-class vocabulary,
new action result requirements and `write_failed` reader rules change. Keep the
controller envelope number. Regenerate contract copies, worker identity,
architecture accounts and reviewed ABI layout through their owners. New
response captures come from the new signed build; never relabel old captures.

## Verification and ownership

Update Swift request/meaning admission, action mapping, worker transport,
result assembly/validation and response consumers; update Rust and Python
independent readers, fixtures and permanent accounts together. Include explicit
accepted default/read/read_write declarations and rejected unknown authority,
raw class/token, impossible syscall evidence, and old-operation preservation
controls. Native substituted calls establish short writes and call failures;
live CLI and BYOXPC witnesses establish actual native lifecycle, ordinary phases,
fresh effects and token confinement through the public path.

Use unique absent children and controlled existing contents in integrated
experiments; preserve absence before issuance and at exclusive creation,
post-release fresh attempts and independent final reads. Keep unresolved-path
prediction absence visible. The native matched/crossed follow-on has its own
record and supports only its bounded question.

Build a matching signed candidate. Run required admission/transport/ABI/unit
checks, extension boundary/combinations and independent consumer controls,
applicable BYOXPC extension witness, source drift and integrated behavior.
Record any actual ordering-observer change and rerun its mutation control if
triggered. Final whole-workset verification remains separate. Core refactoring
cannot begin before the experimental stage is sealed.

## Candidate preparation

The first candidate implements this design across C, Swift and the Rust/Python
readers. `design_extension_integration` authored the Swift/Rust portion and
registered independent Swift evidence/admission/maximum-reply controls;
`extension_consumers_tests` authored Python readers, rejected controls, public
directory witnesses, BYOXPC reuse and maximum-reply workloads. The primary
agent authored native operations, native-call controls, ABI geometry checks,
registration and permanent documentation/generator inputs. Source review is
separate from execution. Local syntax checks passed; a developmental working-tree
dispatcher run of `runner_c_worker_harness/fresh_write` passed fifteen native
substitution controls but is not stage verification.

Response24 live captures, response-shape and ABI-layout goldens deliberately
await a matching signed candidate and their owning capture/harvest tools. The
first test selection is expected to expose these stale acceptance fixtures;
do not edit historical response23 captures or call the initial candidate fully
verified. The predicted maximum reply is 52,843,694 bytes, to be confirmed by
the production encoder; the rounded controller output budget is unchanged.

Candidate `7426fc0` built and signed successfully as version 0.3.3 build977,
worker identity `944121356b57319eb7442c1d67b4841f96bd41f4be040d1751902a1230831593`.
The build verified all seven executables and both seals with the intended
Developer ID, hardened runtime and secure timestamps. No notarization/release
was performed.

`workset-e2-shape-01` exercised the owning Swift and ABI harvests. Swift reported
475/480 passing; four failures were current readers rejecting historical
response23 captures, and one requested the new response-shape golden. The
production encoder confirmed 52,843,694 bytes and the unchanged output budget.
ABI C/Swift values agreed; its deliberate golden refusal yielded 25 added
geometry entries and zero changed prior entries. Review accepted the harvested
48-byte metadata, 232-byte write record at slot6248, unchanged slot budget and
the response shape containing only the added fresh-write family plus schema24.
The owning candidates replace the two goldens; constructed path-diagnostic
fixtures advance to the current schema. The run remains failed and supplies
harvest observations only, not a passing suite credit.

`workset-e2-captures-01` (run `20261029T215525Z_30681311`) passed all six selected
cases at test source `3ff8bf2` against the unchanged signed `7426fc0` runtime:
BBX-001/002, worker-attempt-in-flight, extension_directory, extensions and
extension_combinations. Directory cases independently established effects and
preserved missing publication after an actual write; lifecycle and combined
fault controls retained their separate observations. Ten current-format fixture
files were copied byte-for-byte from this run, and executable readers now name
their response24 locations. Historical response23 bytes were not relabeled.
The capture run is pinned with app inventory and source applicability stated.

Read-only reviewer `review_public_extension` examined candidate `7426fc0` C,
Swift and Python paths, authority transport, native control reach and live
apparatus. It reported no consequential defect; this is source review, not
execution. Broader coordinated verification remains required before the seal.

`workset-e2-coordinated-01` ran 82 default cases at `a7c1408`, using the
unchanged signed `7426fc0` runtime. Eighty-one passed, including all 480 Swift
tests, native fresh-write substitutions, ABI values, independent readers,
admission/failure boundaries and live extension boundaries/maximum replies.
No case overlapped system sleep. The sole failure was the planner mutation
fixture's terminal-enum anchor: it still expected extensionRelease11, before
the new file actions12/13. Its insertion point now names fileCreateFresh13;
extra-kind controls use14 and the gap control15, preserving their distinct
diagnostics and restoration. This adapts experiment equipment, not the checker
guarantee. The original failed run is pinned; the corrected case awaits rerun.

The default external-runner registry and reconcile inspection were empty
before the BYOXPC witness: no runners, pending cleanup, candidates or errors.
