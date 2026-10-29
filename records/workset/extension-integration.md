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
