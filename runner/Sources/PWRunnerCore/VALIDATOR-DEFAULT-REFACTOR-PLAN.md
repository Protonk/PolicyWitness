# Resolve the default validator inside the service bundle

State: implemented, reviewed and accepted against the signed app. The user
approved removal of the implicit app-level fallback. The
[acceptance record](../../../records/worker-validator-default/implementation-acceptance.md)
retains source snapshots, the signed build, full default battery and focused
rerun after the test-only receipt-output correction. Associated investigation:
[execution configuration](EXECUTION-CONFIGURATION-PLAN.md). The
[source review](../../../records/worker-execution-configuration/post-refactor-review.md)
records the selection discrepancy and the deferred capabilities. Implementation
baseline: `6380645181bf87f1d0ac70ea2b3188378fc16761`.

## Result and scope

Resolve the default validator directly to the current XPC service bundle's
`Contents/MacOS/sb_api_validator`, for built-in and external runners. Remove
the executable-file check and the computed app-level alternative from
`CWorkerOrchestrator.defaultValidatorExecutablePath`. An explicit admitted
`validator_executable_path` still takes precedence in `PWRunnerService`.

Selection is not a launch or authentication fact. Preserve existing phase
eligibility and native launch behavior: a reached `posix_spawn` reports the
selected path's absence or non-executability; an earlier refusal or a phase
without eligible queries must not invent a validator failure. Add no eager
helper-availability admission, resolved-selection field, request mode, dynamic
allowance or intervention instrumentation. Ordering, collection and cleanup
policy, wire versions and shared layout remain unchanged.

The supported build and external installer already require the embedded helper.
Manually arranged older layouts no longer receive implicit app-level fallback.
Keep the controller's existing bundle-local default and explicit-override
selection account. Pre-invocation hashes remain observations of selected bytes.

## Implementation and account

Keep resolution small and direct, matching the worker and issuer defaults.
Use existing service/driver boundaries for controls; a narrow bundle-URL input
is acceptable if needed to exercise real temporary layouts without altering
the inspected app. Do not add a second launch implementation or JSON test seam.

Correct stale helper-layout comments and the related source accounts identified
in the review: override echoes describe supplied controls, values can be inert
or unreached, unsafe values can be omitted, and missing echoes are ambiguous.
Qualify requested sleep/signal effects by admission, reaching the native call
and its actual outcome. Describe the dossier as collection before invocation.
These are comment corrections, not changes to control handling or output.

Update the runner implementation reference and the applicable validator edge
in `docs/architecture.json`, then regenerate the architecture account. Regenerate
worker source identity after changes. Check the build account for agreement
when correcting build comments; do not change build behavior. Permanent docs
describe current behavior and do not link investigation records.

## Verification and acceptance

Extend existing registered tests where practical. Establish the default path
with a local helper present, absent and non-executable, including an executable
app-level decoy. The decoy must never replace the local default. Establish
explicit override precedence through service selection. Exercise native spawn
refusal for missing and non-executable selected helpers and retain the actual
attempted path/error. Keep selection observations distinct from native calls.

Retain controls for no eligible queries and failure before validator collection:
no validator subprocess or spawn failure may be fabricated, while ordinary
worker/attempt observations remain available as appropriate. Existing live
validator override, failure, phase and dossier cases cover public compatibility.
Neither the release protocol nor eligibility predicate changes, so this scope
introduces no ordering-mutation obligation.

The coordinator reviews implementation and controls before a signed build with
the configured Developer ID identity. Run the full default battery against the
fixed candidate, using a fresh managed output directory and the checkout lock.
Select additional controls only where the implementation introduces a new
obligation. Retain exact source/build identity, case outcomes and any failures
under the test-evidence rules. Acceptance requires correct default/override
selection, honest reached/unreached launch facts, passing signed acceptance,
and an implementation acceptance record linked from this plan. Update parent
and investigation status after acceptance; the historical review remains intact.

## Separate harness follow-up

Standardize machine-readable retained receipts as separate JSON artifacts whose
successful writes and expected contents are checked before a case passes; use
console output for diagnostics. A small shared console writer and an alternating
large-JSON/progress control can prevent mixed buffered/direct writes. This
refactor applies only the immediate direct-write correction. A single write is
not a general guarantee against interleaving by other writers.
