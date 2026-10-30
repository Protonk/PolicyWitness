# Independent comparison contract, declared before implementation

The fixed reference owners are `tests/suites/dispatcher/check_selection.py`,
`check_accounting.py`, `check_cancellation.py` and `check_retention.py` at
`77eb9875`. Their current suite contract and fixtures were read before this
declaration. Run their four public cases in the isolated worktree. No comparison
subject gets credited for behavior supplied by the outer experimental driver.

Reusable evidence mechanisms: independently authored starts/argv/environment
receipts; `tests/fixtures/exec/control.py`'s Unix peer-PID rendezvous and kernel
exit observer; direct nonblocking flock probes on the stable lock inode; byte
snapshots before refused publication; bounded independent stimulus/release
gates. Candidate observers import none of the candidate's account interpreter.
The existing fixture catalog and event encoding are not candidate oracles.

| Stimulus | Required external observations and account |
| --- | --- |
| Ordinary three-item completion | Exact selected order, three independent body receipts, three complete setup/call/teardown sequences, no hidden failures, resource gone only after observed exit. |
| Native pytest selection/preview | `-k`, node selection and deselection determine exact independent starts; collect-only causes no resource launch, owner publication or lock hold. Duplicate identities refuse before execution. No requirement to emulate `--suite` syntax or catalog aliases. |
| Collection/import or publication failure | No body starts; no successful empty run; absent or incomplete ownership cannot enable execution. Refused retained/preexisting output is byte-identical. |
| Setup acquires then raises before yield | Intent precedes resource creation; no body receipt for that item; setup failure retained, no invented call pass; later independent body executes; resource remains recoverable despite missing post-yield finalizer. |
| Body and teardown both fail | Both phase failures and their distinct diagnostic strings survive; later independent work proceeds; neither replaces the other. |
| SIGINT during active work | Completed receipt remains; active and queued cannot pass; queued has no receipt; stubborn helper first proves direct-SIGINT survival; candidate cleanup observes exit. |
| Engine SIGKILL | One completed, active incomplete, queued not started; raw partial artifact survives; supervisor reaps/observes owned processes, preserves missing reports and releases lock only after resource exit. |
| Supervisor and engine SIGKILL | Child remains responsive; lock held on same inode; competing execution refuses without starts; no terminal success; recovery verifies live peer and held descriptor, engine-exit evidence, then observes child exit before deletion; lock becomes free. |
| Dropped inherited lock descriptor | With both owners dead and child responsive, the independent lock probe detects the free lock and rejects the lifetime claim. Outside safety cleanup is labeled and never credited to the candidate. |
| Missing/duplicate/unexpected/invalid phase records | Independent malformed inputs to finalization cannot yield success. Complete reordered item records may remain valid; legal within-item phase order stays required. No candidate summary supplies the expected result. |
| Report write failure | Nonzero engine/session result and incomplete durable evidence, even if an ordinary body completed; no reconstruction of success from its return code. |
| Truncated last report frame (added prospectively after source review, before reader correction) | A complete earlier item retains its phase observations and completed status; later items remain incomplete, the raw bytes are unchanged, and the overall run fails with a journal diagnostic. |
| Subprocess environment/descriptors | FD capture catches deliberately inherited writes; an explicitly piped isolated helper has exact argv, cwd, env, stdin and outputs, no capture/lock FD. Protected child explicitly holds the stable lock descriptor; dropping it is detected. |

Compatibility choices: retain owner/terminal envelope fields sufficient for
existing retention tools; use pytest node IDs and separate phase records for
candidate results. Public selection aliases, full catalog migration, signed
artifact inspection and all production dependencies are outside this slice.
The original obligations remain visible as scope limits, not passes.

The driver may wait for readiness, inject faults and perform last-resort cleanup.
It may not schedule pytest items, pass a checkout hold into the candidate, write
candidate reports/ownership on its behalf, or count safety cleanup as recovery.
Controls explicitly distinguish stimulus release from resource cleanup.

Before implementation, intended displacement is the ordinary selection and
invocation loop in `test_cli.py`/`suite_run.py`, shell start/end events and one
terminal report per case. Framework collection/fixtures/phase reports should
replace those functions within the slice. Durable ownership, report validation,
resource lifetime, retention, native oracles and source applicability remain.
New plugin/supervisor code and the conditional replay adapter count toward
the candidate; outside stimulus/observation and deliberate mutants count as
investigation-only equipment. Final accounting will preserve that distinction.
