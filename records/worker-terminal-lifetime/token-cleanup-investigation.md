# Ordinary token cleanup at the worker terminal boundary

This investigation supports the [terminal-publication daughter plan](../../controller/tools/pw_probe_runner/TERMINAL-PUBLICATION-PLAN.md), specifically WA-08. Source reviewed at `51487f74da15de196d44c4ac571c7b322a2fe83b` on 2026-10-18. No production changes, builds, tests or live process experiments were performed. Statements below describe source paths or proposed design constraints; they are not new runtime observations. The historical audit is not credited as fresh validation here.

## Recommendation for the design decision

Retain the shared borrowed token channel and its present preparation placement. Add one small, bounded ordinary-cleanup operation that erases an accepted token buffer, and use it on every reachable ordinary terminal path after preparation. A terminal-publication helper can call that operation before publishing `done` and exiting. Early refusals and cancellation need the same cleanup operation without acquiring a new `done` publication.

This cleanup is independently useful and does not require immediate exit. It is sensible to include it in the same implementation scope because both changes touch the same terminal paths, but the guarantees must stay separate: immediate exit removes intentional waiting after `done`; ordinary erasure covers paths that actually reach the cleanup operation. Neither establishes cleanup during a stuck native call or fatal termination.

No additional experiment is needed to choose this design over later preparation or a private copy. Independent byte observations are required to validate an implementation. A proposed confidentiality guarantee broader than ordinary PW-owned-buffer erasure would require a separate investigation.

## Present token ownership and partial initialization

The owning implementation is [`prepare_extension`](../../controller/tools/pw_probe_runner/pw_probe_runner.c) at lines 1268–1352, with fixed channel layout and the volatile erase loop in [`pw_extension_channel.h`](../../controller/tools/pw_probe_runner/pw_extension_channel.h).

1. If no extension is requested, preparation closes an optional descriptor and returns. No token mapping is accepted.
2. Requested preparation first resolves consume and release symbols, then disables core dumps, then inspects the descriptor's size, maps the channel, and closes the descriptor. A missing descriptor produces `token_unavailable` after the API/core-limit work. Early setup failures close the descriptor once and retain the first failure plus any cleanup-close failure separately.
3. After successful `mmap`, the pointer is assigned to `extension_channel` before descriptor-close and channel-validation checks. A close failure, invalid channel header, or invalid token follows `reject_mapping`: erase the full fixed token array, attempt `munmap`, set the pointer to null, and publish the original failure plus an independent unmap failure if present. A failed unmap does not cause the ordinary terminal helper to acquire a dangling-pointer cleanup responsibility; that rejection path already erased the bytes before its unmap attempt.
4. Only a fully accepted mapping retains a non-null `extension_channel` after preparation returns. Token length is nonzero and less than 16,384, its terminator is present and its prefix contains no NUL. `extension_delivered_bytes` and a release-store delivery publication establish validation, not consumption. The worker borrows these bytes directly; it does not make a PW-owned private token copy.
5. Fatal termination during mapping or validation can bypass rejection cleanup. An ordinary terminal routine cannot execute on that path. Existing controlled mode 106 deliberately interrupts validation before delivery publication.

Keeping the current initialization order avoids treating an unaccepted or unmapped channel as a valid ordinary-cleanup target. The proposed operation can test the retained non-null pointer and erase its fixed token array; it need not allocate, unmap, resolve symbols, inspect descriptors or call any sandbox API.

## Terminal-path inventory

All references in this table are to [`pw_probe_runner.c`](../../controller/tools/pw_probe_runner/pw_probe_runner.c). The early paths before line 1651 have not accepted the token mapping and therefore have no worker token bytes for this helper to erase.

| Path after preparation | Current publication and exit meaning | Current worker erasure | Constraint for a refactor |
| --- | --- | --- | --- |
| Parameter count refusal, lines 1663–1669 | Failure and diagnostic; return 8; `done`, `applied`, and `apply_rc` untouched | None | Erase before the same return; do not publish `done`. |
| Expected policy length refusal, lines 1676–1684 | Failure and diagnostic; return 10; terminal flags untouched | None | Preserve failure and exit code. |
| Timing setup refusal, line 1691 | Published timing failure; return 12; terminal flags untouched | None | Preserve placement before policy reading and the distinct exit. |
| Policy read failure or overflow, lines 1705–1720 | Failure and diagnostic; return 7; no EOF receipt | None | Preserve missing EOF receipt. |
| EOF length mismatch, lines 1726–1740 | EOF byte count published first, then failure; return 11 | None | Preserve both the receipt and failure order. |
| Embedded NUL, lines 1747–1754 | EOF receipt retained; failure and diagnostic; return 9 | None | Preserve refusal before compilation. |
| Parameter creation/set or encoding failure, lines 1773–1807 | Failure, `apply_rc = -1`, release-store `done`, spin, eventual `_exit(0)` | None | Erase before `done`; retain native failure and exit 0. |
| Compilation failure, lines 1815–1832 | Failure, `apply_rc = -1`, release-store `done`, spin, eventual `_exit(0)` | None | Erase before `done`; do not reinterpret exit 0 as compilation success. |
| Application failure, lines 1884–1899 | Native return/errno retained; no `applied`; release-store `done`, spin, eventual `_exit(0)` | None | Preserve application evidence and erase before `done`. |
| Proceed clock refusal, timeout or future release, lines 1487–1552 | Failure, no acknowledgement for refused phase, release-store `done`, spin, eventual `_exit(0)` | None | Erase before `done`; retain phase and failure semantics. |
| Observed cancellation, lines 1539–1541 | `_exit(0)` before acknowledgement; no new failure or `done` | None | Erase before exit without adding a terminal publication or acknowledgement. |
| Normal phase-loop completion, line 1915 | Erase occurs before the post-apply hang/signal seams and before final progress/`done` at 1943–1945 | Full token buffer erased if mapped | Retain this early erase even if a terminal helper repeats it. Moving it after the seams would lengthen token lifetime. |

A single erase primitive can serve the distinct departure styles without forcing all paths into one publication policy. Preserve the distinction between ordinary `main` returns and the post-apply `_exit` route unless changing C runtime teardown is separately justified. There is no reason to flatten every refusal into `done = 1` or a common exit code.

The consume path has an earlier erasure obligation. [`attempt_extension`](../../controller/tools/pw_probe_runner/pw_probe_runner.c), lines 1354–1375, records the decision, performs any native call, retains its return/errno, and erases the shared token before the containing slot's result publication. Successful consumption stores a handle used by a later explicitly requested release. Keep this erase site; postponing it to terminal cleanup would retain raw token bytes through later actions and phases. Terminal cleanup must not automatically call `sandbox_extension_release`: that is a specimen action and changes the experiment independently of erasing a PW-owned buffer.

An interruption after native return but before result publication still withholds the native result. Erasing a buffer must not be treated as proof of native return, slot completion, permission change, or release.

## Host erasure remains independent

[`ExtensionSession`](../../runner/Sources/PWRunnerCore/ExtensionIssuer.swift), lines 166–173, provides the descriptor only after `issued`, erases the entire host channel through `pw_extension_clear`, and records `host_buffer_erased`. Destruction repeats the erase, unmaps and closes the session descriptor. The C shim's erase uses volatile stores.

The orchestrator erases explicitly before a capability-refusal reply at [`CWorkerOrchestrator.swift`](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) lines 84–93, and after the driver returns, before final reply assembly, at lines 227–251. The worker driver's cleanup request, grace/termination and final acquired snapshot occur first in [`CWorker.swift`](../../runner/Sources/PWRunnerCore/CWorker.swift), lines 1346–1388. Driver cleanup can remain unconfirmed, and final collection explicitly records `execution_may_continue`; host erasure is not conditional on confirmed worker reaping.

Consequently, host erasure can clear the shared bytes even if the worker did not reach its erase. Conversely, the host observation is not proof that the worker erased them. This distinction is explicit in the [native extension evidence contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence), lines 194–214. Host loss can prevent host-side erasure. Native exit drops the worker's mapping but is not itself a byte-erasure observation.

## Alternatives and their costs

| Design | What it could improve | Coordination and semantic costs | Assessment |
| --- | --- | --- | --- |
| Common bounded erase with current shared channel | Covers ordinary failure/cancellation paths; erase precedes `done`; leaves current acquisition, consume and reporting model intact | Must retain different publication/exit routes, existing pre-seam erase, and consume-time erase; fatal/stalled paths remain outside the guarantee | Recommended. |
| Move `prepare_extension` later | Worker maps the token for less pre-apply work and never maps it on some earlier refusals | Host already holds issued token bytes; inherited token descriptor stays open longer. Moving the whole function changes when symbols/core limits/setup run and which delivery observations survive beside header/policy/compile failures. Moving only part creates another split initialization state. Refusals after the new location and cancellation still need cleanup. | A separate acquisition-placement choice; not necessary for terminal exit or ordinary erasure. |
| Copy into fixed worker-private storage, then clear shared channel | Clears the transferable shared buffer earlier during successful setup; isolates later consumption from changes through the shared mapping | Creates an additional token copy and transfer/erase interruption window. Host erasure cannot clear the new private copy while the worker stalls. Requires private-buffer lifetime and partial-copy cleanup rules, changes the borrowed-view model and observations, and does not make fatal termination execute cleanup. | No motivating need established by WA-08 or terminal lifetime; defer. |

Neither a watchdog nor parent-loss detection is needed solely to perform this ordinary bounded erase. Those mechanisms concern paths that do not reach normal cleanup and would need their own requirement and syscall/resource review.

## Controls required before accepting implementation

Existing controls establish useful boundaries but not the proposed expanded guarantee. [Extension boundary fixtures](../../tests/fixtures/extension_controls/README.md) include production source with controlled native calls. Their `controlled_erase` wrapper in [`control.c`](../../tests/fixtures/extension_controls/control.c), lines 122–130, observes bytes after the actual erase. [`check_extension_boundaries.py`](../../tests/suites/witness_contract/check_extension_boundaries.py), lines 269–274, asserts worker erasure on its successful native path, while asserting host erasure separately. This is not coverage of every early return. [`ExtensionEvidenceTests.swift`](../../runner/Tests/PWRunnerCoreTests/ExtensionEvidenceTests.swift), lines 127–143, maps the actual host channel and observes full zeroing plus descriptor closure; that is a host control.

For a candidate, extend the existing controlled-native boundary approach instead of accepting `host_buffer_erased` as the worker oracle:

- Deliver a nonempty accepted token, trigger each distinct ordinary departure before consumption, and independently observe the worker's full-buffer erase before `done` or exit. Preserve the current distinct exit codes, EOF receipt presence, delivery publication, application flags, phase acknowledgement and failure payloads. Publicly reachable compile/apply paths belong in CLI controls; malformed shared headers and controlled timing/read failures need internal boundary controls.
- Exercise cancellation after token acceptance, both with no release and with a release made visible near cancellation. Assert no added acknowledgement, attempt or `done`; the erase must not move the cancellation decision or make a cancelled phase runnable. A change inside `wait_for_proceed` requires `witness_contract/order_barrier_mutations` under the repository rules.
- Retain successful consume and native refusal erasure before slot completion, omitted-consume normal completion, and erasure before post-apply hang/signal seams. Include no-token/API-unavailable and rejected/partially initialized channel cases so a helper cannot erase an invalid pointer or replace original setup/cleanup failure evidence.
- Retain fatal-interruption controls before consumption, during validation, and after native return but before publication. These must continue to leave missing publications missing and distinguish host erasure from absent worker cleanup.
- Use test-owned transient storage and independent cleanup ownership as the current extension fixture does. Do not persist token bytes in records. Instrumented-source receipts establish their controlled boundary behavior; run the signed production extension/lifecycle cases as the separate integrated check.

These are implementation acceptance controls. The narrow design choice is already supported by control-flow and ownership inspection; no present runtime uncertainty makes private storage or later preparation preferable.
