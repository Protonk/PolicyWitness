# Stage 1 evidence account

This account supports contract review, not acceptance of an implemented
consolidation. The production tree remains the current declaration-plus-actor
implementation. Future candidate controls are listed in
[verification-selection.md](verification-selection.md).

## Identified baseline

The starting checkout was clean at
`4cd1d6c7f14e3ebacfd2dda219dda85967f64680` (`Update EXTENSION-CONSOLIDATION-PLAN.md`).
The preceding turn inspected `1c9254ad`; the user's committed plan is the only
intervening change. All production source, assertions and catalog references
in this packet use 4cd1d6c7.

The preexisting distribution app reported an older dirty source and was not
credited as this baseline. A normal `make build` produced app build **1140**,
`v0.3.4-59-g4cd1d6c7`, using
`Developer ID Application: Adam Hyland (42D369QV8E)`. Its seven executables and
two seals passed the build's Developer ID chain, hardened-runtime, timestamp,
inventory and source checks. See [baseline-build.log](baseline-build.log) and
the copied app manifest/provenance under [evidence](evidence/).

The sandboxed keychain query reported zero identities. The identical query
outside the automation sandbox found the matching Developer ID; signing,
builds and live cases subsequently ran outside that sandbox. This observation
does not explain arbitrary future permission failures.

Execution was serialized under `tests/.checkout.lock`. No lock was removed.
Fresh managed directories were used for both dispatcher runs. Current retained
default/complementary pins were left intact. Rather than adding a third pin,
the new relied-on evidence is copied into the identified archives below.

## Dispatcher results

| Run | Selected/completed/pass | Scope and limits |
| --- | --- | --- |
| `extension-consolidation-native-20261105` | 2 / 2 / 2 | Independent signed native feasibility and directory authority. No app or XPC participation. |
| `extension-consolidation-baseline-20261105` | 11 / 11 / 11 | Fresh signed app, current actor/declaration behavior, selected native harness and BYOXPC controls. App inventory valid before and unchanged after. |

Both runs report zero skips, zero unrun cases and zero system-sleep overlap in
every selected case. Exact canonical IDs, run IDs, commands/configuration,
catalog snapshots and raw artifacts are retained in the archives. The readable
selection receipts are [native-selection.json](native-selection.json) and
[baseline-selection.json](baseline-selection.json).

The eleven baseline cases were:

- `runner_c_worker_harness/terminal_erasure`
- `runner_c_worker_harness/authority_binding`
- `runner_c_worker_harness/actor_operations`
- `smoke/specimen_file_read_deny`
- `smoke/specimen_file_read_deny_standard`
- `smoke/runner_caller_auth`
- `witness_contract/extension_redelegation`
- `witness_contract/actor_compositions`
- `witness_contract/extensions_byoxpc`
- `witness_contract/actors_byoxpc`
- `runner_byoxpc/entitlement_readback`

Both the principal built-in and BYOXPC re-delegation reports explicitly recorded
**credited: true**, with no first broken link;
the successful simpler calibration is independently required. This is stronger
than merely observing a passing case, but remains a result for these inputs and
this baseline. The BYOXPC chain credit comes from its own principal report,
not solely from its enclosing case pass.

The current terminal-erasure case is declaration-channel coverage and the
current actor-operations case calls operation bodies directly. Their passes
do not establish the proposed actor terminal-erasure or production-dispatch
controls. The ledger assigns those replacements. The complete Stage 4
coordinated selection and default battery have not been executed for a
consolidation candidate, because none exists yet.

An initial read-only selection used nonexistent `smoke/version` and was
refused before execution. It was corrected to the actual `smoke` suite before
the successful listed run. No missing case was silently skipped.

## Actual production-worker variant experiment

[run_actors.py](prototype/run_actors.py) copied the baseline core Swift sources
into an isolated package and compiled a driver using the current actor
scheduler, custody owner, C inputs and reply assembly. It copied the actual
shipped C worker into two paths, signed the host and selected variant with
`com.apple.security.cs.allow-jit=true`, and signed the other variant without
supplied entitlements. It used the shipped validator. The driver changes only
per-actor launch paths below public request translation.

Attempt 01 failed to compile because the Swift Security API required an
associated `SecStaticCode` object for signing information. No native authority
claim is credited to it. Attempt 02 corrected that conversion and resolved
the Swift product's actual output path. The first source snapshot and failure
logs remain preserved; the successful retry does not rewrite them.

Attempt 02's principal observations:

| Observation | Recorded result |
| --- | --- |
| Subject baseline fresh read | Open failed, errno 1. |
| Unentitled issuer fresh read | Returned the known target bytes. |
| Issue / transfer | Nonnull native issue; delivered transfer with actor custody. |
| Consume | Returned native handle 1. |
| Later subject fresh read | Returned the known target bytes through a fresh descriptor. |
| Release | Published native return 0. |
| Later fresh read after release | Open failed, errno 1 in this run; no general revocation promise. |
| Ownership and termination | Two distinct owned actor PIDs, both cleanly reaped. |
| Signed equipment | Live PID code lookup/validity and associated signed metadata identified the issuer path with an empty entitlement read-back and subject path with allow-jit=true. |

The deliberate same-selected substitution also completed its lifecycle and
fresh access. Its live read-back showed the issuer had the selected worker's
entitlement, so the independent empty-read-back equipment assertion rejected
the claimed unentitled arrangement. This is the necessary negative control:
a positive issue or read result alone cannot distinguish equipment selection.

The separate unapplied App Sandbox-signed worker failed to open the owned
target while reading the system control file; the ordinary worker read both.
It retained `application_count=0` and `unapplied_declared`. The experiment
therefore distinguishes skipping specimen application from removing a
worker's signed starting restrictions.

These are observations through the actual worker and actor machinery. They
do not establish future public equipment parsing, service-local inventory,
install validation, per-actor requirement enforcement, new reply readers or
the proposed pre-activation identity gate. Prototype identity inspection ran
inside each phase's collection callback after setup and activation. Dynamic
code validity plus associated static entitlement metadata is not an evaluation
of an entitlement's effective native permission. The allow-jit key is a
distinguishing signed attribute here, not the asserted cause of file access.

The experiment did not install a service. Its unique App Sandbox fixture
created a container that macOS refused to remove. The direct children were
reaped; container cleanup remains unresolved. See [recovery.json](recovery.json).

## Supplemental inherited-parent contrast: failed, with partial observations

[run_authority.py](prototype/run_authority.py) derived a separate native fixture,
retaining exact original/generated source and signatures. Its ordinary
lifecycle, issuer-exit, no-consume and no-predicate scenarios completed their
local assertions. The restricted-parent scenario returned failure, which
stopped the driver; this is **not** a passing lifecycle control.

The retained raw report nevertheless shows parent policy application return 0,
an unentitled child's fresh open failing with errno 1, and the subject's
pre-application open failing. The subject's subsequent `sandbox_apply`
returned -1/errno 1 and it exited 97; both children were reaped. No consume
or release was attempted. `worker_erased_channel` was false, so no worker
erasure is credited. `token_guard_passed` was true, a separate confinement
observation. These support only the narrow inherited-restriction observation
and failure path, not a second successful sandbox application or unrestricted
authority. No passing retry was sought to conceal this failure.

This supplemental result does not invalidate the successful mixed production
worker arrangement under its recorded parent context. It reinforces why the
equipment selector must describe signing choices without promising unrestricted
authority under arbitrary parent restrictions.

## Preservation and outstanding ownership

[evidence/index.json](evidence/index.json) identifies each gzip archive by SHA-256,
original path, run identity and result accounting. Per-archive inventories
record every copied file and hash. Archives preserve raw completed dispatcher
runs, both production-prototype attempts and the failed supplemental experiment.
The committed source baseline is separately archived, excluding historical
`records/` and `reports/`, which are not dependencies of the credited controls.
Compiler caches are excluded from prototype archives; the source package,
actual executed host/worker bytes, signatures and raw observations are retained.

[preserve_evidence.py](preserve_evidence.py) records the copying procedure. A
post-run prototype-source receipt hashes the retained Python drivers; it is
identified as reviewed post-run identity, not a timestamped pre-execution
attestation. The successful package's `sources.json` retains its source-copy
hashes. No old dirty app or unrelated retained run is relabeled as baseline.

All BYOXPC service sessions created by the selected cases report verified
removal. The ordinary registry was empty before and after. One existing
App Sandbox test container was already present before `actors_byoxpc` and
remains present; this run does not establish ownership of its creation.
The prototype's unique new container has its own durable ownership receipt.
Copies do not transfer active recovery ownership from the original paths.
No protected evidence, staging record or retention pin was deleted.
