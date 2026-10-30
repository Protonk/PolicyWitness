# F2 lifecycle investigation

Authorized after the stopped checkpoint `17e02e6a`. This investigation preserves
F1 and all production behavior. Its stopping boundary is a concrete explanation,
its limits and a repair proposal for discussion, not an unapproved retry repair
or acceptance of the previously failed BYOXPC workload.

## Fixed comparison and questions

The selected current app is unchanged v0.3.3 build 1000 from `fd90eee`, identity
f477a8488d3f96715e987f7014dcd0aa76ba53b70575118e20ef238b600d4094.
The accepted Stage 1 source `2de5b1c7` is checked out at
`/private/tmp/pw-f2-stage1` and built with the normal signed pipeline and the same
Developer ID. Its build 999 uses identity
6f777628d0b0f233f6e26f99222e8f78cd0920bb94b842b5bf2d0c4b2e29a9a7.
Build output initially resides in `/private/tmp/pw-f2-stage1-build.log`; attach it
to the completed comparison run before removing the worktree. Signing/compiling
succeeded; no main app was replaced. Baseline and candidate live runs are serial.

Questions fixed before new observations:

1. Do ordinary empty-plan requests reproduce 4097 in the accepted Stage 1 app,
   current app, or both, under the same bounded schedule?
2. Which observed host generations and lifecycle boundaries surround failures?
   Process sampling cannot establish absence of an unsampled short-lived worker.
3. Can retirement overtake a refused request's reply, and can a lost reply also
   accompany completed work? Keep these mechanisms distinct from attribution of
   the original two failures.

## Equipment and limits

An opt-in observation case sends 48 unique ordinary allow-default empty-plan
requests, twelve each with predeclared 0/10/30/60 ms inter-call gaps, with no
resubmission of failed requests. It retains every outcome, actual timing,
process generations and unified logs. Passing means the bounded observation
completed and was accounted for, not that all requests succeeded or that F2
is resolved. Empty plans avoid creating a new effect-cleanup ambiguity.

The controlled follow-up uses copied production host sources, the shipped raw
client and real workers in separately owned signed services. Instrumentation
records admission, orchestration return, encoded reply, reply invocation and
scheduled exit. Its gates do not hold the admission lock. Retirement is held
inside the existing 50 ms closure. Compare delivered refusal, retirement before
refusal delivery, and host termination after completed work before its reply.
Append-only effects, request identity and observed kernel process generations
provide independent observations. Instrumentation is a declared intervention,
not proof of unchanged production timing or attribution of historical failures.

Production source, the inspected app, public retry rules and existing pass/fail
expectations remain unchanged. Current acquisition permits another execution
attempt only after an admitted pre-worker refusal and observed generation
retirement. A generic XPC error supplies neither fact. Any proposal to change
that boundary must address duplicate effects, unknown execution, client loss,
resource ownership and the original overall deadline together.
