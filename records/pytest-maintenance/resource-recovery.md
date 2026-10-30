# Early prototype resource: bookkeeping supplement

Codex, 2026-10-30. This supplement repairs the missing consolidated recovery
description; it does not change a historical observation or mark a lease closed.
`preservation.json`, in this plan's package, copies the relevant raw records with
hashes and records read-only filesystem observations at
`2026-10-30T15:57:23.650705+00:00`. The old record remains unchanged.

The source is `fa376979e40373c993149cf96ef62db2550b2a9a`, top-level retained
run/ID `pytest-boundary-demo-01`, under
`/private/tmp/pw-pytest-boundary-20261030/tests/out/runs/`.
Its incomplete candidate is `candidates/setup_failure` (run ID `setup_failure`,
started at Unix milliseconds `1793372203912`). The parent run started at
`1793372203133`. The lease is `resources/0/record.json` below that candidate:

| Identity | Recorded value |
| --- | --- |
| Item | `test_subject.py::test_active` |
| Supervisor / engine / owned child PIDs | `71946` / `71947` / `71948` |
| Lease nonce | `77e6da3550924b7db44bf64aaa391a13` |
| Held checkout lock inode | `143170175` |
| Resource | `/private/tmp/pw-pytest-boundary-20261030/tests/out/runs/pytest-boundary-demo-01/candidates/setup_failure/resources/0/owned` |
| Socket directory | `/private/tmp/pw-py-res-6e703d57e50848888c7d8b19e46202f9` |
| Raw outside observations | Parent run's `observations/setup_failure/observation.json` and `witness/resource.jsonl` |

The acquisition receipt identifies child `71948`, the same nonce/inode/path,
and a published intent already in `launched` state. The saved lease is
`acquired`. The outside observer authenticated peers C=`71948` and P=`71947`,
observed direct-SIGINT survival and then failed with
`AssertionError('processes still running: {71948}')`. Its saved exit set before
safety cleanup contains only `71947`. The resource's `observations.jsonl` also
records engine exit `71947`. These support acquisition, engine death and failure
of candidate cleanup at the observed time, not subsequent child exit.

The initial datagram-reset defect bypassed candidate resource finalization.
The outside driver's `TreeControl.close` has a safety-release/wait/kill path;
the old observation was written before that cleanup. Inferring that a particular
exit occurred from that source path would exceed the durable evidence. No
post-safety-cleanup child exit/reap receipt, candidate `supervisor.json` or
lease `recovery.json` is present. Later observer revisions saved before/after
exit sets separately; they cannot retroactively fill this gap.

Current read-only facts: the resource is a 15-byte regular file, device
`16777233`, inode `143189433`, SHA-256
`f73173f9010cc3dc5e06d26c1071a9607ccf84350141d1c24caa1a114c17b138`.
The socket directory still exists and is empty; `recover` is absent. The checkout
lock still has inode `143170175`, but its current owner record has nonce
`3167ea5e37c14320804d466002f3b9d9`, not the lease nonce. No lock was acquired or
probed for availability. No current process was identified or signalled using
the historical PIDs. The saved PID alone is insufficient to identify a live
process now; a reused number would not establish historical identity or exit.

The frozen recovery path requires a live socket peer matching the recorded PID,
the nonce, a transferred descriptor matching the lock identity/owner record,
and the child's engine-exit observation. It watches the child's exit before
resource removal. The absent endpoint prevents satisfying that protocol here.
A historical saved engine-exit receipt does not substitute for the missing
authenticated live peer/descriptor or a positive child-exit observation.

Disposition: **preserve the file, empty socket directory, acquired record and
original pin**. To reconsider cleanup requires either the stated authenticated
recovery evidence or a separately justified basis for absence/ownership and
cleanup that addresses the missing historical child exit. This supplement
does not invent that alternative. A missing socket, changed lock nonce, elapsed
time or a passing later run is not sufficient. The original unknown-worker
directory is a separate protected resource and was not investigated for recovery.
