# Independent first report — test skeptic

Frozen revision: `5124b4309b6f7b0041c55318312a9ee18f579868`.

I read my assignment, repository/runner/test guidance and orientation, the frozen worker tour, and the sources/assertions cited below. I did not read the planning document, sibling reports or other reviewer conversations. I did not build, execute tests, change product/test sources or start agents. This report distinguishes historical receipts from assertion/source review; proposed counterexamples have **not** been executed.

The tour generally makes unusually careful distinctions between source placement, fixture observations, native returns and independent effects. I found one concrete failure-cleanup problem in a cited live test and two narrower weaknesses in the new setup oracle. None establishes a new product implementation defect. The documented unchecked setup returns and low-FD collision are already accurately characterized as product limitations.

## T1 — ordinary extension tests delete their targets even when child cleanup is unknown

**Label: source-supported. Type: test failure-cleanup defect. Priority: address before relying on a failed extension run's ownership/evidence.**

Challenged omission: the worker tour cites the “extension checks” (`docs/WORKER.md:448–451`) as evidence for native access observations, but that check's failure path has no worker/issuer-exit gate before removing its owned targets. This matters alongside the tour's explicit acknowledgment that “Worker death can interrupt that cleanup; the host supervises the worker” (`docs/WORKER.md:394–395`), rather than any claimed universal cleanup guarantee.

Exact path and assertions:

- `tests/suites/witness_contract/check_extensions.py:51–57` wraps the ordinary run in `TemporaryDirectory` and immediately returns `run_targets(...)` from inside its context. Its target-directory receipt labels ownership `temporary_directory` at lines 60–63.
- `capture(...)`, lines 35–48, asserts the CLI return code at line 41 before loading its envelope. A harness timeout, an unexpected nonzero return, malformed JSON, consumer rejection or later assertion unwinds this context. The directory is then removed regardless of whether a worker/issuer exit was observed.
- The first happy-path worker reap assertion is only at line 73; subsequent placement cases check `runner_subprocess.reaped` at line 159. Those assertions are neither failure cleanup nor proof that every preceding capture reached a known exit. On a timeout they are never reached.
- `tests/lib/run_capture.py:1–6` explicitly assigns workers/XPC hosts/fixture trees to the caller. Its `wait` raises `HarnessTimeout` at lines 80–90. `close` kills/waits only `self._process`, the CLI, at lines 108–121. It does not establish worker or issuer exit.
- A relevant existing alternative is `check_killed_before_publication.py:105–119,177–202`: retain staging when `worker_exit_witness` cannot establish exit and preserve a cleanup receipt even after a primary exception. The extension boundary fixture also has separate retained ownership (`check_extension_boundaries.py:102–133,276–283`).

Counterexample/uncertainty: interrupt the ordinary extension test while the CLI is waiting for a worker, or let its 40-second harness wait expire. `RunCapture` can clean up the CLI while the XPC host/worker is still executing. The outer context then deletes the target tree, changing the active experiment and losing recovery staging. This follows from source; I have not observed a live surviving worker on this path. The BYOXPC branch uses session-owned staging and is outside this particular finding.

What would refute it: an actual caller-level exit/ownership guard that runs before `TemporaryDirectory.__exit__` on **every** exceptional path, or evidence that the capture helper independently terminates and observes all workers and issuers. Neither appears in the traced path; a passing normal run would not refute it.

Smallest decisive probe: in a disposable test copy, replace `capture` with a stand-in that records the target path and raises immediately after entering the capture boundary; assert that the directory is retained with cleanup status unknown. The frozen implementation should fail that assertion. A separate live gated-worker timeout can confirm the process consequence if needed, with the reproduction owning independent cleanup. Adopt explicit staging ownership and retain it until child cleanup is established, preserving the original failure.

## T2 — the setup endpoint oracle can accept the wrong pipe direction or wrong protocol argument

**Label: source-supported. Type: fixture/oracle limitation, not proof of a production defect. Priority: strengthen the setup control's independence.**

Challenged scope: “Host spawn actions select the policy, evidence and readiness endpoints, plus the optional token endpoint” (`docs/WORKER.md:284–285`) and the new controls' “independent child observer” (`:319–322`). The observer independently sees native descriptor metadata, but its oracle does not independently establish the endpoint's required *role*. The fixture README already concedes shared-memory identity and token-validity limits; it does not identify this direction/argument limit.

Exact path and assertions:

- Production requests `adddup2(policyPipe[0],0)`, `adddup2(shmFD,3)` and `adddup2(readyPipe[1],4)` at `runner/Sources/PWRunnerCore/CWorker.swift:1094–1097`, and separately supplies `--shm-fd 3`, `--ready-fd 4`, optional `--extension-fd 5` at lines 1100–1106.
- `SetupControls.swift:76–80` captures whatever source the production call requests. `observer.c:10–25` observes only `argc` and `fstat` on 0/3/4/5; it neither reads argument values nor records `F_GETFL` access modes or performs the protocol I/O.
- `host_setup_controls.py:20–21,58–74` compares `(device,inode,mode)` from that requested source to the child destination. Its normal-path expectations therefore follow a changed source. It asserts argument **count**, not argument contents. The collision branch requires some overlap and mismatch at 3, but does not require fd 4 absence despite that additional observation being described in the tour (`:332–333`).

Counterexample: change only the ready source at CWorker line 1096 from `readyPipe[1]` to `readyPipe[0]`. In the reserved-low-FD baselines, the observer receives a read end and matches the source recorded by the adapter, yet the real worker cannot write its ready byte there. Fault rows still observe an omitted action, and the collision row still has the independent evidence-fd mismatch it requires. A second minimal mutation changes `--shm-fd`'s value from `3` to `4`; the observer's `argc` and descriptor census are unchanged although the real worker maps a pipe. The entire-control survival of either mutation remains untested.

What would refute it: an assertion comparing endpoint roles/access modes or parsed worker arguments to independent protocol expectations, or a focused mutation rejected specifically for the wrong direction/argument. The substitution-count check is useful mechanical grounding but both proposed edits preserve the call count. A different integrated real-worker test detecting the mutation would establish broader suite coverage, not eliminate this setup oracle's limitation.

Smallest decisive probe: run the unmodified setup case and each one-line disposable mutation separately, retaining every receipt. Add independent expected endpoint roles, `F_GETFL & O_ACCMODE`, argument values, and preferably bounded read/write or mmap/header checks with a non-secret nonce. Assert the documented fd 4 collision observation separately if it is intended as a regression property. Preserve the observer's separation from PW result publication.

## T3 — `maps_remaining == 0` counts successful unmap calls, not complete released extents

**Label: source-supported. Type: fixture cleanup-accounting limitation. Priority: make the cleanup receipt precise.**

Challenged sentence: “Cleanup is observed before independent fixture cleanup: descriptor closure, successful unmapping/destruction, released copied strings, name lookup and child reaping” (`tests/fixtures/host_setup/README.md:34–36`). The checker additionally names its assertion “descriptor/mapping cleanup” (`host_setup_controls.py:30`). The native `munmap` result is observed, but mapping completeness is not.

Exact source and assertions:

- `SetupControls.swift:13,53–62` stores only mapping base addresses in `Set<UInt>`. Any `munmap(address,length)` returning zero removes that base, without checking the original length or tracking a remaining suffix.
- `runSetupControl` emits only that set's count at lines 191–195. `host_setup_controls.py:30` requires zero, and its negative control at line 147 changes the derived count to 1; this checks the checker consuming a count, not the adapter's derivation of the count.
- The actual production calls supply the full extent today: `CWorker.swift:950–953` and `ExtensionIssuer.swift:170–174`. Thus this is not an allegation that the frozen product partially unmaps.

Counterexample: in a disposable host copy, change the evidence-region defer to unmap only the first page. If native `munmap` succeeds on that range, the adapter removes the whole base from its set and reports zero remaining maps while most of the region is still mapped. The fixture process exits soon afterward, hiding the remaining mapping at process teardown. No current field measures that suffix. This counterexample is source-supported and has not been run.

What would refute it: extent-aware tracking or independent VM-range observation demonstrating the whole acquired range was removed, or a decisive partial-unmap control rejected by the existing assertions. Merely seeing `munmap.rc == 0` does not refute it.

Smallest decisive probe: keep the original successful setup run, then mutate only the unmap length to one page in a disposable package. Independently inspect a page beyond the removed prefix before fixture exit and retain its mapping status. Track acquired ranges and subtract successful unmapped extents, or at minimum require every full-owner teardown call to match its recorded acquisition extent. Describe the receipt as call/result accounting unless independent extent observation is added.

## Coverage worksheet

| Traced claim/control | Supported by actual assertions/source | Remaining limit |
| --- | --- | --- |
| Host setup faults and collision, WORKER 311–336 | Exact injection count, native child PID, argc, requested-source/destination metadata, host reap, fd-number closure, owner-teardown name lookup, map/string/handle counters: `host_setup_controls.py:24–75`. Failed init containment is explicit and correctly described. | T2/T3. The observer does not apply a sandbox or implement worker/issuer publication. Characterizing continued spawn does not certify setup refusal. |
| Worker reporting under bare deny and full-region case, WORKER 231–240 | `runner_c_worker_harness/run.sh:209–224` requires apply/done/completed/native failure and clean exit; `:267–284` requires all 256 completion flags, with selected payload checks. | Full-region means all slot completion publications, not every byte/page exercised or absent page faults. Tour preserves this scope. |
| Exec acquisition/reuse, WORKER 365–389 | `runner_c_worker_harness/run.sh:639–654` requires a 64-fd ceiling, 32 clean execs and both reads; `:677–688` checks the bare-deny setup reached the reported spawn boundary. | Ceiling rules out holding all 32 pipe pairs simultaneously; it does not prove per-attempt acquisition or handle lifetime. The tour and suite README explicitly leave placement to source. The stronger source comment at run.sh 626–629 (“no exec step holds descriptors across another step's work”) is not established by these assertions and should be aligned with the narrower README. |
| Exec group cleanup and interrupted publication, WORKER 391–400 | `runner_exec_lifecycle/check.py:46–60` independently observes the two helper processes, their group, exits and later file change. `check_edges.py:56–90` kills an independently identified worker, confirms helper survival, and requires absent unpublished child fields. | Observed members only. Escaped descendants and automatic descendant cleanup after worker death are not claimed by the tour. I did not inspect retained execution for these cases. |
| Fresh reads and extension lifecycle, WORKER 445–451 | `check_extensions.py:73–98` separates native issuer/consume/release results, worker/issuer reap, before failure, during bytes and identity, and conditional after bytes. Source `pw_probe_runner.c:1380–1405` opens and closes inside each action. | T1. Existing unchanged-target repeats do not independently reject retaining a successful read descriptor across later phases. The replacement at `check_extensions.py:206–230` occurs before the first fresh read; it guards issuance identity reuse. A later replacement after one successful read would discriminate cached descriptor authority. No current product caching is alleged. |
| Native extension interruption/publication, WORKER 423–456,466–476 | `check_extension_boundaries.py:222–236` demands unresolved/null return after independent pre-call/in-call/post-return positions and preserves earlier evidence. `control.c:55–68,274–283` separates controlled replacement position from real native return. Source `pw_probe_runner.c:1363–1375` writes native payload after the post-return observation; CWorker 1407–1442 gates decoding on slot completion. | The in-call control is a replacement function, not kernel-internal interruption. Post-return extension modes interrupt before native payload assignment; the ordinary create control below exercises already-written payload. These are complementary scopes, not universal private-state observations. |
| Native effect before unpublished ordinary slot, WORKER 466–476 | `check_killed_before_publication.py:184–192,209–240` observes created file before JSON, demands a reaped signal death/started slot, withholds rc/errno/path, and preserves prefix/suffix. Native seam at `pw_probe_runner.c:1443–1449` lies after payload writes and before completed release. | Establishes the exercised create and common slot gate; not all native calls or all publication races. Its explicit exit-gated cleanup is stronger than the ordinary extension test. |
| Exec inheritance, WORKER 299–305 | `runner_exec_inheritance/check.py:47–53,73–95` links child report PID/nonces and proves worker contamination. `fixtures/exec/inspection.py:29–50` requires empty environment, exactly 0/1/2, canary EBADF and stdin EOF. | The observer's SIGPIPE behavior and incomplete ambient-state census are expressly acknowledged by the tour. No new universal worker-isolation conclusion is justified. |

## Retained evidence inspected

I inspected `tests/out/runs/worker-p4-setup-final` (run ID `20261018T000428Z_baa4b43b`), specifically the passing run/case account, `artifacts/controls/results.json`, instrumentation manifest and selected native receipts. It contains 22 setup observations and 10 rejected checker controls. These are historical observed baselines, **not reproductions of T1–T3**.

The preserved acceptance copies of `SetupControls.swift`, `observer.c`, `shim.c`, `host_setup_controls.py` and its shell wrapper are byte-identical to the frozen revision. The manifest's original hashes for CWorker (`b1aedaefe685ff316f87b94c41811dfa3503188347d662b0be43622655c640e9`) and ExtensionIssuer (`12dfdc4b7a1509e158718e541d407bdbc88a33109518d9d72af8248665e891fc`) match the frozen bodies; retained instrumented hashes match their manifest. This is limited applicability grounding for the examined receipts, not a complete dependency audit or a new test credit.

Concrete receipts agree with the tour's bounded description: `worker-collision.json` has shm source 0, child fd 3 matching the policy pipe and fd 4 absent; `worker_token-dup2.5.json` has the omitted token action, real child/reap, and null-device metadata at 5 instead of the executable-file source; `issuer-collision.json` preserves the high-duplicate channel metadata and records `issuer_result_missing`, as expected for this non-publishing observer. The passing baseline's `outcome` likewise does not establish a real worker publication, and the Python checker does not claim that it does.

Recommended order: fix/test ordinary-extension exceptional cleanup; run the two endpoint mutations; run the partial-unmap counterexample. Preserve each independent first result and any failure evidence before revising an assertion. Native publication claims need their existing scoped wording retained, not a stronger claim derived from reviewer agreement.
