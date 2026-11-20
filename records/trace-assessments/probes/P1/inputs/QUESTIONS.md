# P1 questions

For each envelope file E1.json to E10.json in this directory, answer:
(a) In one to three sentences, what happened?
(b) The numbered questions below for that envelope. For each, answer and quote the sentence of docs/RESPONSE.md you relied on (or say the document does not decide it).
(c) Name one conclusion a reader might draw from this envelope that it does not support, and why.

## E1 (E1.json)

(b1) Does the envelope establish that the sandbox caused the EPERM?
(b2) What does `order: query_first` establish?
(b3) Do `sandbox_check.outcome: deny` and the failed attempt together establish that prediction and enforcement agreed?

## E2 (E2.json)

(b1) Were the attempts carried out, and are their results reported?
(b2) What prediction does the envelope give for the third step?
(b3) Did the validator process crash?

## E3 (E3.json)

(b1) Did the worker apply the policy or perform any attempt?
(b2) What does `policy_check.status: ok` establish?
(b3) Why did the connection fail?

## E4 (E4.json)

(b1) Is the `stdout` text the child's output?
(b2) Was any output cut?
(b3) What does `observation: succeeded` with basis `spawned_child` establish?

## E5 (E5.json)

(b1) Do the validator's `allow` and the successful open show that prediction and enforcement agreed?
(b2) Did the validator's answer cause or explain the successful open?
(b3) What does the successful attempt establish?

## E6 (E6.json)

(b1) What does `status: captured` establish?
(b2) Are these the bytes the kernel enforced?
(b3) Does the receipt identify imported files the compiler read, or their contents?

## E7 (E7.json)

(b1) Does the `unavailable` receipt say whether the worker copied the compiled object?
(b2) What killed the worker?
(b3) Did the `create` step take effect?

## E8 (E8.json)

(b1) What ended the worker?
(b2) Does the envelope establish why the worker did not finish in time?
(b3) Did the policy or the sandbox cause the timeout?

## E9 (E9.json)

(b1) What ended the actor's worker?
(b2) Does `cleanup_trigger: completion` mean the actor finished normally?
(b3) Was the read step's result lost?

## E10 (E10.json)

(b1) Was the policy compiled or applied, or any step attempted?
(b2) Does the refusal mean the timeout value was invalid?
