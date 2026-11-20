# P1 answer key: envelope interpretation

Written by the coordinator from source, the contract surfaces' rules and each
case's own checker, before any reader ran. Readers answer, per envelope:
(a) what happened; (b) the envelope-specific questions; (c) one conclusion a
reader might draw that the envelope does not support. Grading: (a) and (b)
against the key; (c) is credited when it names any listed non-conclusion or
another one the coordinator confirms from source.

## E1 `smoke/specimen_file_read_deny` (policy_witness.run.stdout.json)

(a) An ordinary run applied the policy (`sandboxed_after_apply: true`) and the
worker's `open(O_RDONLY)` of `/etc/hosts` failed with errno 1 (EPERM);
outcome `finished`, exit 0. The validator, queried before the attempt, gave
`deny` for `file-read-data` on `/etc/hosts`.

(b1) Does the envelope establish that the sandbox caused the EPERM?
Key: no. `comparison.observation: permission_failure` with basis
`permission_errno` records the shape of the native failure; the steps surface
says attribution to an enforcing mechanism requires supporting evidence, and
nothing in this envelope supplies it.

(b2) What does `order: query_first` establish?
Key: that this eligible prediction was collected before the phase's attempt
batch was released, with worker lifetime and setup established. It does not
mean the prediction and the attempt agree, nor that the prediction caused or
explains the result.

(b3) Do `sandbox_check.outcome: deny` and the failed attempt together establish
that prediction and enforcement agreed?
Key: no. They are separate channels (validator versus worker); PolicyWitness
makes no agreement or disagreement claim between them.

(c) Non-conclusions: the sandbox caused the failure; the policy's deny rule
was the matching rule; prediction and enforcement agree; the prediction
influenced the attempt.

## E2 `runner_validator_failure/validator_unavailable_reports_degraded` (run.json)

(a) An ordinary run applied the policy and attempted all three steps; the
worker reported each result (one write `ok`; two failures with errno 1). The
validator returned records for only two of the three steps; the third has a
synthetic `sandbox_check` (`outcome: error`, `missing_reason:
validator_no_verdict`) and `order: unestablished`. The run's outcome is
`validator_unavailable`, `ok: false`, exit 1.

(b1) Were the attempts carried out, and are their results reported?
Key: yes. All three attempts have worker results (`result_source: worker`);
`validator_unavailable` describes the prediction channel. The outcome makes
the run unsuccessful, but it does not withdraw the attempt results.

(b2) What prediction does the envelope give for the third step?
Key: none. Its check is synthetic (`validator_no_verdict`). It is not a deny,
and its order is `unestablished`.

(b3) Did the validator process crash?
Key: not established, and not indicated. The validator exited 0 and was
reaped. The association issue is a missing record for one step identifier.

(c) Non-conclusions: the third step was predicted to be denied; the
attempts did not happen or their results are invalid; the policy was not
applied; the validator crashed; the sandbox caused the two permission
failures.

## E3 `runner_byoxpc/reservation_controls`, lost execution (validated.json)

(a) An ordinary request went to an external runner. The client was granted a
reservation and invoked the execution, then the connection ended with
`terminal: xpc_error`. There is no host reply (`runner_result: null`), and the
outcome is `xpc_error`, `ok: false`, exit 1. Because the client's terminal was
`xpc_error`, the controller ran its standalone policy helper on the request's
policy. The helper compiled it (`policy_check.status: ok`, helper exit 0).

(b1) Did the worker apply the policy or perform any attempt?
Key: not established either way. Without a host reply, the client's
`xpc_error` says nothing about how far the worker got. Fallback eligibility
does not establish worker progress or the cause of the lost reply.

(b2) What does `policy_check.status: ok` establish?
Key: a separate helper process, which the controller started after the
transport failure, compiled the submitted policy text on this host. That is
an independent compilation. It is not evidence about the host's run,
application or enforcement, and it does not show the worker compiled
anything.

(b3) Why did the connection fail?
Key: the envelope does not say. The error names the service connection only.

(c) Non-conclusions:
- the policy was, or was not, applied;
- any attempt happened, or did not;
- the policy caused the failure;
- the helper's compilation shows the worker's compilation succeeded;
- a successful compilation says anything about allow or deny.

## E4 `runner_use_c_worker/exec_stream_invalid_utf8` (pw/run.json)

(a) An ordinary run applied the policy and spawned one child, which exited 0.
The worker read 17 bytes from the child's stdout up to EOF and retained all
17, with nothing truncated. Those bytes are not valid UTF-8, so the reply's
`stdout` is 17 replacement characters and `text_exact` is false. Stderr was
empty. The outcome is `finished`.

(b1) Is the `stdout` text the child's output?
Key: no. It is a lossy rendering. Each invalid sequence became U+FFFD,
`text_exact: false` says so, and the original bytes cannot be recovered from
the reply.

(b2) Was any output cut?
Key: no. `bytes_received` equals `bytes_retained` (17), `truncated` is
false, and EOF was observed.

(b3) What does `observation: succeeded` with basis `spawned_child` establish?
Key: that a child was spawned (a positive child PID). The child's exit status
is reported separately; here it is 0. The basis does not say the child's
program did what it was meant to do.

(c) Non-conclusions: the child printed replacement characters; the output was
truncated; the bytes can be recovered; the text is a faithful copy.

## E5 `witness_contract/happy_path_baseline` (run.json)

(a) An ordinary run applied the policy. The validator, queried first, gave
`allow` for `file-read-data` on `/etc/hosts`, and the worker's read-only open
of `/etc/hosts` then succeeded (`ok`, rc 0, basis `completed_worker_status`).
The order is `query_first` and the outcome `finished`.

(b1) Do the validator's `allow` and the successful open show that prediction
and enforcement agreed?
Key: no. They are separate channels. The envelope reports both and makes no
agreement claim.

(b2) Did the validator's answer cause or explain the successful open?
Key: no. The validator is a separate process that queries the compiled
policy. It does not decide enforcement, and `query_first` records only that
the query was collected before the attempt batch was released.

(b3) What does the successful attempt establish?
Key: that after the policy was applied, the worker's open returned success.
It does not establish which rule of the policy matched.

(c) Non-conclusions: prediction and enforcement agree; the prediction caused
or explains the result; an allow rule matched; the same access would succeed
under another policy or in another process.

## E6 `runner_outcome_bad_request/accepted_input_contract`, corpus CLI capture (run.json)

(a) An ordinary run requested capture of the compiled policy and applied the
policy, and its one `create` step succeeded. The receipt is `captured`. It
holds a 492-byte compiled object copied before application, the object's
digest, digests of the source text and parameters, the request nonce and the
worker PID. The outcome is `finished`.

(b1) What does `status: captured` establish?
Key: the worker published a copy of the compiled object it built from the
submitted source and parameters. The host checked the copy's identity (PID,
nonce, source and parameter digests) against its own inputs, and observed
successful application and clean completion.

(b2) Are these the bytes the kernel enforced?
Key: not established. The copy was taken before application. The receipt is
not an observation of the kernel's effective policy.

(b3) Does the receipt identify imported files the compiler read, or their
contents?
Key: no. No receipt field identifies a file the compiler reads. The source
digest covers the held source text only.

(c) Non-conclusions:
- the kernel enforced exactly these bytes;
- the contents of imported files are covered;
- the receipt is authenticated by anything outside the product's own
  processes;
- the receipt shows what any rule allows or denies.

## E7 `runner_outcome_bad_request/accepted_input_contract`, capture with worker death (run.json)

(a) An ordinary run requested capture and applied the policy. The worker
published an `ok` result for its `create` step, then was terminated by
signal 9 before publishing completion (`done_observed: false`). The host
reaped it. The process disposition is `signaled` and the termination cause
`unknown`. The outcome is `runner_failed`, exit 1. The receipt is
`unavailable` with reason `worker_not_complete`.

(b1) Does the `unavailable` receipt say whether the worker copied the
compiled object?
Key: no. An `unavailable` receipt does not say whether the worker made the
copy.

(b2) What killed the worker?
Key: not established. The envelope records signal 9 and the reap. The
termination cause is `unknown`.

(b3) Did the `create` step take effect?
Key: the worker reported `ok` for it before it died. The envelope carries no
separate observation of the created file.

(c) Non-conclusions: the worker made no copy; the host or the policy killed
the worker; the sandbox caused the death; the file exists now.

## E8 `runner_outcome_runner_timeout/host_kills_hung_worker` (run.json)

(a) The run was submitted with experimental controls. The client's argument
vector requests `worker_post_apply_hang_ms: 8000` and `worker_timeout_ms:
2000`. The policy was applied. The host's sentinel wait ran out its
2,000 ms budget (`stop: sentinel_deadline`), and the host sent SIGKILL during
cleanup and reaped the worker. The cleanup trigger is `deadline_expiry`, the
termination cause `host_sentinel_deadline`, and the outcome `runner_timeout`,
exit 1. No step results are reported.

(b1) What ended the worker?
Key: the host, after its sentinel deadline expired. It requested SIGKILL
during cleanup (`termination_cause: host_sentinel_deadline`, signal 9).

(b2) Does the envelope establish why the worker did not finish in time?
Key: no. The argument vector records a requested hang control, which is
supplied intent, not an observation that the intervention took place. The
envelope observes only that completion was not published before the
deadline.

(b3) Did the policy or the sandbox cause the timeout?
Key: not established.

(c) Non-conclusions:
- the sandbox or the policy caused the hang;
- the worker hung because of the requested control (the envelope does not
  show it);
- any specimen step ran;
- the worker crashed by itself;
- the 20,000 ms client timeout expired.

## E9 `witness_contract/actor_compositions`, actor killed after exit grace (run.json)

(a) An actor-form run with one actor, `only`. Its equipment matched, and its
policy application was observed. Its read step published `ok`. The run also
requested an experimental post-apply hang of 3,000 ms. The worker did not
publish completion (`done_observed: false`). When the schedule finished, the
host's exit-grace wait of 1,000 ms ran out, and the host terminated the
worker with signal 9 and reaped it. The actor's termination cause is
`host_exit_grace_exhausted`, its `poll_stop_reason` is `schedule_complete`,
and its `cleanup_trigger` is `completion`. The outcome is `runner_failed`,
exit 1.

(b1) What ended the actor's worker?
Key: the host, after exit grace ran out (`host_exit_grace_exhausted`,
signal 9).

(b2) Does `cleanup_trigger: completion` mean the actor finished normally?
Key: no. The trigger is derived from the scheduler's stop reason
(`schedule_complete`): host cleanup began because the schedule finished. The
worker itself never published completion and was killed.

(b3) Was the read step's result lost?
Key: no. It was published (`ok`) before the kill.

(c) Non-conclusions:
- the actor completed normally;
- the worker exited on its own;
- the kill erased the step's result;
- the requested hang control is observed to have taken effect.

## E10 `witness_contract/test_input`, refused control in an ordinary request (run.json)

(a) An ordinary request carried `validator_io_timeout_ms` in its
`_test_overrides` block. The host refused it at admission: `bad_request`,
`inapplicable_field at _test_overrides.validator_io_timeout_ms: field has no
effect in this request`. No worker ran (`process_disposition: no_worker`),
and the outcome is `bad_request`, exit 1.

(b1) Was the policy compiled or applied, or any step attempted?
Key: no. The refusal came at admission, before any worker started.

(b2) Does the refusal mean the timeout value was invalid?
Key: no. An ordinary request refuses an experimental control in its override
block whatever the value. The control is admitted only on the experimental
route, `policy-witness test-input run`.

(c) Non-conclusions: the value was out of range; the validator timed out; a
worker started and was stopped; the field is ignored and the run proceeded.
