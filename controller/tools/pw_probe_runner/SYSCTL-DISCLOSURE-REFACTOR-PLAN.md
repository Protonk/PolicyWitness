# Disclose the bounded sysctl read

Status: implemented, reviewed and accepted against the signed app. The
[acceptance record](../../../records/worker-sysctl-read/implementation-acceptance.md)
retains the build, independent capacity control, full default battery and source
snapshot.
This implements the source naming and disclosure decision from
[SYSCTL-READ-PLAN.md](SYSCTL-READ-PLAN.md), under the
[worker redesign plan](../../../WORKER-REDESIGN-PLAN.md). The
[investigation report](../../../records/worker-sysctl-read/report.md)
retains the native capacity observations and existing signed-app compatibility
evidence. Planning baseline: `924a6ed048a805d8f5633e3b720fbed64ad00ccc`.

## Result and scope

Keep `sysctl/read` as one post-apply `sysctlbyname` value-read invocation with
a non-null 4096-byte stack destination. Name the capacity in worker source and
disclose it in the limits inventory and operation account. The operation
discards the returned value bytes and post-call length; its existing PW status,
saved errno and error text remain the only call-result evidence.

Add no preliminary sizing call, retry, allocation, request option or output
field. Preserve the current result classification and comparison rules. This
does not promise complete retrieval for arbitrarily sized values, identify the
cause of ENOMEM, or make a returned length available. Raw length metadata remains
outside this implementation. Request, response and envelope versions and shared
ABI geometry stay unchanged; worker source identity must be regenerated.

## Implementation

1. Give the existing 4096-byte array in
   [attempt_sysctl_read](pw_probe_runner.c) a local source constant, such as
   `PW_SYSCTL_READ_BYTES`, used as its array bound. Keep `len = sizeof(buf)` so
   the supplied capacity follows the actual destination. Preserve the exact
   call shape, one-call control flow and success/failure handling.
2. Add `sysctl_read_bytes` to [docs/limits.json](../../../docs/limits.json), in
   the execution section. It is fixed destination capacity for an attempted
   value read, not an admission bound or evidence-output cap. State that values
   and returned lengths are discarded and that call failure does not diagnose
   whether capacity was insufficient. Cite the actual producer and the compiled
   call-boundary control below. Register its checker as a value-check owner in
   [generate_limits.py](../../../docs/generate_limits.py) and the independent
   [source-drift owner list](../../../tests/suites/source_drift/limits.py); do
   not introduce an ABI field or duplicate runtime constant merely to expose a
   value to a test.
3. Expand the `sysctl/read` entry in the
   [user guide](../../../docs/PolicyWitness.md#what-policywitness-understands)
   with the operation, generated capacity span, and discarded-result semantics.
   Qualify the attempt-local storage account in
   [docs/architecture.json](../../../docs/architecture.json): the sysctl buffer
   is stack storage used after apply, and its value bytes/length are not copied
   into the result slot. Regenerate the worker account. Permanent documentation
   describes current behavior and does not link investigation records.
4. Regenerate with `docs/generate_limits.py`,
   `docs/generate_architecture.py`, and `docs/generate_worker_identity.py` using
   their normal repository entry points. Review generated changes, including
   the limits table copied into the guide and worker identity in C/Swift.
   Update the daughter and parent plan status on acceptance.

## Verification

Add one narrow default case to `runner_c_worker_harness`, using the existing
fixture pattern of compiling the production C source with its `main` renamed.
Substitute only `sysctlbyname` in that test translation unit; production needs
no new override. The substitute independently records the incoming target,
non-null destination, initial `*oldlenp`, null new-value pointer, zero new-value
length and call count. Its expected capacity is the literal 4096, not the
constant under test. The retained call receipt must also agree with the limits
manifest. A changed manifest cannot silently redefine the test's expectation.

Exercise a successful native return and a failed return with an independently
chosen errno. In both, change `*oldlenp` to a different value before returning.
Require exactly one call and the existing PW success/failure status and saved
errno. Keep the control small: it establishes the actual supplied capacity and
call shape, not kernel behavior, copied-byte counts or sandbox attribution.
One deliberately shortened supplied-capacity mutant must fail the independent
boundary assertion. Do not duplicate the investigation's capacity sweep or
add readers/publication controls for metadata that this change does not add.

Register the case, document its fixture and suite ownership, and cite it as
the limits value/boundary check. The existing live
`runner_filter_sysctl_name/prediction_unavailable_attempt_observed` case and its
checker controls remain the public compatibility checks. Their denial-shaped
result and unavailable prediction establish neither the capacity nor ENOMEM's
cause; the compiled control establishes the supplied-call facts separately.

Acceptance requires a signed build and the full default battery, including
the new control, source-drift checks, compiled ABI/identity agreement and the
existing live sysctl cases. Retain original failures and any replacement
credits under [test guidance](../../../tests/AGENTS.md), with source/build
snapshots and exact commands. Review that the only production call change is
the named array bound, the ABI and wire versions did not change, and no native
call, resource or per-run evidence was added.
