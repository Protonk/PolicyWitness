[Test work survey](TEST-WORK-SURVEY-REPORT.md) supplies the case accounting,
assertion reading and implementation boundaries for this companion report.

# Test expectation authority: revision 31b8195

An expected result can protect a product promise, require an accurate account
of an execution, or keep a limitation reproducible. Some cases do all three.
Their passing status does not assign the same authority to every assertion.
The question here is what supports preserving an expectation, and what its
failure would mean after a plausible improvement.

The investigations below examine selected revealing cases at the survey's exact
revision, `31b81951c9c8c4124089aa4dd342b2b63c0a86de`. They are not an authority
classification of every catalog member. Source, documentation and ancestor
history were read in a detached worktree of that revision. The companion's
section numbers refer to its completed account. Relative source links identify
documents at the examined revision; later checkout contents may differ.
Historical statements below report what a commit or contemporary account said,
not a fresh confirmation of its recorded executions.

## 1. Descendant survival: a counterexample with a documented policy behind it

`runner_exec_lifecycle/closed_streams_leader_exit` (survey §2.6) requires the
same-group descendant to survive normal completion. Its authority is unusually
explicit: the [suite account](../../tests/suites/runner_exec_lifecycle/README.md#same-group-descendant-after-normal-completion)
calls it characterization of an observation limit and disclaims a desired
process-tree containment rule. The
[control account](../../tests/CHANGE-VERIFICATION.md#worker-resource-challenge-probes)
says passing means the stated counterexample was observed.

The origin supports that reading. Commit `2d63c98` (2026-10-17) introduced the
probe during a challenge to the worker resource account. Its historical
`records/worker-pass5-round1/reconciliation.md` reopens the normal-completion
finding because group escape was unnecessary: the original group could retain
a live member. It expressly separates a passing counterexample from successful
containment. This is evidence of an intentional demonstration of a limitation,
not evidence that users are promised surviving descendants.

There is nevertheless a current policy to distinguish from that demonstration.
The [exec evidence contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md#exec-collection-and-cleanup-evidence)
says ordinary completion requests no termination and the host supervises the
worker, not exec descendants. Commit `924a6ed` (2026-10-18) added that account
alongside explicit collection, cleanup and reap evidence. The case therefore
combines a required counterexample with reporting obligations: a completed
leader and closed streams must not become a claim that the group is empty.

A product that also stopped the surviving descendant would fail the survivor
assertion even if its reporting remained entirely honest. That failure would
establish a changed observation, not by itself a lost safety guarantee. If it
did so by adding termination on ordinary completion, it would also depart from
the documented no-request policy. Whether that policy is a compatibility
commitment or a description intended to evolve with containment is unresolved
by the examined evidence. Reporting a real request as `not_requested`, by
contrast, would violate the present evidence contract regardless of whether
the descendant exited.

## 2. Host-setup oracle insensitivity: preserving a demonstration of inadequate checking

`runner_unit/host_setup_oracle_sensitivity` (survey §2.5) has authority as a
controlled demonstration about a checker. Its
[stated purpose](../../tests/suites/runner_unit/README.md#host-setup-oracle-sensitivity-opt-in)
requires the old oracle to accept independently observed counterexamples.
Neither those bad operations nor the oracle's acceptance is described as a
desired property of PolicyWitness.

The same `2d63c98` reconciliation distinguishes the original setup observations
from what their checker could miss. In particular, it says production used the
complete mapping extent; the partial-unmap variant demonstrated a checker
blind spot, not an established production leak. The earlier
`runner_unit/host_setup_controls` case itself
[characterizes selected setup paths](../../tests/suites/runner_unit/README.md#host-setup-failures-and-descriptor-collisions),
including paths that still spawn after setup failure. Its passing result is not
a promise that every setup fault is refused. The authority for these cases is
bounded observations and a challenge to the adequacy of their interpretation.

The word “old” needs care when considering evolution. The sensitivity case
copies the checkout's current setup recipe/checker at invocation; it does not
retrieve an immutable historical checker
([`main`](../../tests/suites/runner_unit/host_setup_oracle_sensitivity.py)). A more
discriminating setup checker could reject a deliberately wrong host and make
this case fail while improving the evidence about the host. A host improvement
that refused a setup fault where the baseline currently proceeds could also
change the expected receipts; the stated characterization does not promise
continued spawning on those paths. A host refactor could instead prevent the
specified source substitution from being formed; that would leave the
experiment unperformed, not refute its historical result.

Thus failure can mean that a limitation is no longer reproduced, or that the
controlled experiment no longer applies. It need not mean a broken product
promise. The baseline's correct observations and independently confirmed
fixture cleanup are separate requirements: the characterization label does
not excuse their failure. No examined statement settles the intended lifetime
of the acceptance expectation if the original checker becomes stronger.

## 3. Ordering: preserving behavior and the evidence that qualifies it

`witness_contract/attempt_effects_wait_for_collection` and
`witness_contract/order_barrier_mutations` (survey §§2.5, 2.9) protect a stated
design constraint. The [core design guidance](../../AGENTS.md#core-ideas) requires the
collection/release barrier and the limited meaning of `query_first` to be
preserved, and specifically names the mutation control when its governing
operations change. The [ordering contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md#phase-association-and-partial-publication)
defines the publications that justify that meaning. Commit `5f0fbc3`
(2026-09-26) added the independent gates and bypass controls as acceptance
evidence. Here the rationale, current design instruction and current contract
support one another; the mutation's rejection is not authoritative merely
because it is an expected nonzero result.

These expectations require both a product behavior and truthful qualification
of observations. Effects must wait for closed collection, and a prediction
may acquire ordering credit only with the required chain. An optimization
that starts attempts during collection could produce faster, individually
correct results and still break this promise. A different implementation
preserving the chain would not break the promise merely by invalidating a
source-mutation anchor. The latter failure would establish lost applicability
of that control, not premature effects.

The limit is part of the intended guarantee. The
[interval cases](../../tests/suites/witness_contract/README.md#predictions-before-attempts),
including `witness_contract/query_interval_is_not_a_snapshot`, preserve the
distinction between order and stable state. Their changed-target observations
do not require the product to keep all future snapshot capabilities absent.
They do require the existing ordering label not to assert a snapshot that its
evidence cannot establish. A new capability that actually prevented the
controlled mutation would change the experiment and raise a contract question;
relabeling the same observations as a snapshot would break the existing meaning.

`runner_unit/reaped_ack_mutation` shows that preserving this guarantee can
include stronger evidence recovery. Commit `f382cf6` (2026-10-18) introduced
final acknowledgement reconciliation alongside earlier worker exit. The
current contract allows a missed acknowledgement to qualify after confirmed
reap while ownership remained intact, including fatal exit, but never repairs
a previously broken ownership chain. Failure to recover that evidence in the
baseline scenarios would now lose promised ordering information; granting it
in the ownership-loss control would overstate the evidence. The intended
invariant is justified order, not preservation of every historical
`unestablished` result.

## 4. Exec evidence: preserving what is known, including what is unavailable

`runner_unit/exec_reader_mutations` and
`runner_exec_lifecycle/worker_dies_during_exec` (survey §§2.5–2.6) protect a
publication rule with an explicit authority beyond the examples. The
[exec evidence contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md#exec-collection-and-cleanup-evidence)
requires absent metadata to remain unavailable, malformed present evidence not
to become a clean default, and unpublished slots to supply no exec account.
It separately requires actual collection, termination-request and reap facts
to retain their different meanings. Commit `924a6ed` introduced this structured
account and its reader controls. The intent is accurate reporting, including
refusal to report facts the producer has not published.

That does not require cleanup to remain ineffective. A product improvement
could stop more descendants, reap sooner, or obtain additional observations.
Those events could legitimately change a live expected record. What remains
protected is that the record describe the actual calls and observations:
successful signalling does not substitute for an observed exit, and missing
metadata does not mean no termination was requested. The constructed absent
metadata input must still remain absent under the current contract even if a
new producer normally supplies more evidence.

Earlier publication is a subtler improvement. The contract explicitly says
that reporting spawn facts from a worker killed before slot publication
requires a separate publication contract. Exposing the current incomplete slot
would violate the present guarantee. Publishing a new, independently valid
spawn record before the final result could change what is knowable and make
the old absence expectation inapplicable. That is an unresolved contract
evolution, not evidence that missing information is itself a desired product
limitation.

The live worker-death case also requires surviving helpers. Here the test
kills the worker while the exec leader and descendant remain live; the worker
cannot finish collection, cleanup or slot publication. This is a different
path from §1's ordinary completion without a termination request. The survival
assertion preserves a controlled limitation after worker loss; the
missing-publication assertions protect this section's reporting guarantee.
Better containment after worker loss could fail the first while preserving
the second, without changing the ordinary-completion policy. The case's single
pass/fail result cannot identify which expectation was affected; its individual
observations and assertions supply that distinction. Nor do the constructed
reader controls establish that an actual child was contained; their boundary
remains the one identified in the companion.

## 5. Honest attribution: a continuing constraint with a changed representation

`runner_exec_dac/execute_permission_controls_spawn` and
`witness_contract/comparison_matrix` (survey §§2.2, 2.15) illustrate a
commitment that survived a substantial change in the product's vocabulary.
Commit `e6bcfb3` (2026-09-13) introduced independent execute-permission
controls and described permission-shaped spawn failures as ambiguous. Its
original DAC README required `drift=null` for the failure and `drift=false`
for the successful permission control. The purpose was to prevent an ordinary
permission failure from substantiating disagreement about sandbox enforcement.

Commit `ed0bd3d` (2026-10-01) removed the agreement/disagreement judgments,
including the affirmative agreement assertion. At the examined revision,
[the DAC account](../../tests/suites/runner_exec_dac/README.md) and the
[public reading rules](../../docs/PolicyWitness.md#reading-a-comparison-record)
require observed outcomes, scope relations and justified order without sandbox
cause attribution. The repository's core design instruction corroborates this.
The old assertion is evidence of original purpose, not an alternative current
contract that the new record must continue to satisfy.

The duty is to report whatever occurred without promoting a permission errno
or paired query answer into a cause. The controlled permission interventions
justify the experiment's expected observations; they do not give an arbitrary
production envelope the test's outside knowledge. A product improvement that
retained more native error detail could preserve this constraint. A change
that inferred a sandbox cause from the same EACCES alone would break it even
if every reader agreed on the new label.

A capability supplying additional attribution evidence would raise
a different question. The current public contract does not define such a
claim, and the current comparison deliberately makes none. Failure of its
no-attribution assertions could not be dismissed as obsolete solely because
the feature was called an improvement. It would require settling the meaning
and authority of the new claim. These tests support the current abstention;
their history does not settle all possible future forms of evidence.

## 6. Disposition “reds”: specified gaps that became regression checks

`unit/rust.disposition_reds` (survey §2.4) originally made an implementation
gap reproducible while specifying behavior expected after a planned change.
Commit `5f6c619` (2026-09-27) identifies four intentionally failing controller
tests, including loss of the carried disposition record's witnessed cleanup
account. Commit `0ed4ae7`, later that day, records the implementation and
promotion: the reds became green and default. Its catalog and README changes
corroborate the promotion rather than leaving it as a commit-message claim.

At the examined revision, the [unit account](../../tests/suites/unit/README.md#invariants)
describes exact selection and failure classification. The
[cause and projection rules](../../tests/FAILURE-PROPAGATION-CONTRACT.md#cause-labels)
supply the semantic authority: preserve a supported host cleanup sequence,
report conflicting status instead of silently resolving it, and withhold a
claim that contradicts its basis. The host cleanup label does not identify an
exclusive signal sender or a sandbox cause. These are current reporting
commitments, not a requirement to preserve either the old loss or the “red”
status suggested by the name and stale script header.

An improvement that let the worker exit voluntarily before host cleanup could
legitimately change the label in a live run. It would not change the required
answer to the fixed unit input containing the full witnessed cleanup chain.
Failure to project that supported record would be a regression under the
current rules; an input that now supplies a different chain is a different
observation.

The historical
[known-loss capture](../../tests/fixtures/disposition/README.md) has a separate
present role: it is rejected for its unsupported envelope version, before its
reply or claims are read. That rejection establishes version admission, not
recognition of the original information loss. Current-format controls remove
the disposition record or replace the supported cause with `unknown` to check
the semantic losses. The contract and those controls support preserving the
information; the old capture's authenticity and rejection alone do not.

## 7. The outcome matrix: a maintenance obligation and a refactor-completion check

`witness_contract/attempt_outcome_matrix_enforced` (survey §2.3) began as
item R13 in `e1c42b5` (2026-05-29): the outcome enum, coverage matrix and
source-drift integration were to land together. That commit explicitly
intended the suite to become permanent regression coverage when green.

The current [coverage document](../../tests/COVERAGE.md) still requires every
enumerated outcome to have a matrix entry added with the constant. That is
evidence for an ongoing maintenance obligation. It is not a claim about a
particular runtime outcome, and equality of outcome names does not establish
that the named owner actually exercises each meaning. The companion supplies
the distinction between this case and
`source_drift/runner_source_manifests_agree`; their agreement is not additional
authority for the expectation.

Adding a useful outcome without accounting for it would fail an explicit
maintenance requirement even if product execution improved. Conversely, a
refactor that preserved complete outcome accounting while moving or
generating the declarations could fail the case's text and location
expectations without losing that obligation. The original integration intent
does not establish that those exact source forms are a lasting product
promise. The additional string-presence assertion supplies still less evidence
that integration works. Present intent for preserving the particular
text-reading arrangement, or the two separate checks as an intentional pair,
remains unresolved; their existence alone does not decide it.

## 8. A native deny answer: an observation used to reach a classifier branch

`validator_batch_mode/batch_ndjson_roundtrip` (survey §3) combines a
documented transport/classification contract with a particular native answer.
The [suite account](../../tests/suites/validator_batch_mode/README.md) requires
ordered verdicts, continued processing after per-probe failures and clean-EOF
completion. The script's comment before request construction expressly says
the `/tmp/foo` deny under the `/etc` policy is used to exercise the
`rc=1, errno=0` classifier branch, not to prove that the query matches the
policy's apparent structure
([rationale in the script](../../tests/suites/validator_batch_mode/run.sh)).

Commit `5bc61db` (2026-05-29) introduced the sandboxed target to close an
uncovered classifier branch. It connected that coverage to the drift detection
then being built. Drift judgments were later removed in `ed0bd3d`, while the
native-result classifier remains part of the present validator interface.
The present role is therefore narrower than that original product rationale;
the required deny answer is an empirical means of exercising it, not a promise
that PolicyWitness controls what the native query returns.

The request-construction comment still calls the observed answer “drift” from
the policy structure and invokes that interpretation as the product's purpose.
That language records the older rationale; it does not override the current
no-agreement/no-disagreement contract or establish a sandbox cause. The suite
README also retains the older generic `error` expectation for an unknown
operation, while the script now requires `unsupported_operation`. Its framing
rules remain relevant authority, but its entire expected-result list is not a
current specification.

Extending PolicyWitness to a system whose native query yielded allow for that
target would fail the fixed deny expectation even if the product faithfully
returned and classified the new result. That would establish a changed
observation and lost coverage of that branch in this execution, not by itself
a classifier defect. A parser or classifier improvement preserving the existing
interface ought to preserve its framing and mapping obligations;
misclassifying an actual native deny would break those obligations. The
[repository orientation](../../README.md) names macOS 26 on Apple Silicon as
the tested platform; it does not independently establish this answer across
future systems. The failure alone cannot distinguish native change, a failed
experimental prerequisite or bad reporting.

## 9. Findings across the investigations

The strongest evidence of a present commitment is a specific meaning supported
by current public or design language, a corresponding contract, and history
that does not contradict their current role. This is a reasoned reading of
the evidence, not a rule that documentation wins every disagreement. A suite
name, default selection, historical capture or green result supplies no such
meaning on its own.

The ordering chain, publication boundaries and refusal of unsupported cause
claims have that converging support. The survivor and host-checker acceptance
expectations intentionally reproduce limitations. The native deny
answer supplies an experimental condition. The outcome matrix protects a
maintenance obligation whose particular textual enforcement has less clearly
documented authority. Those distinctions apply to assertions, not uniformly
to whole cases: the same characterization also requires truthful records and
successful fixture cleanup.

The companion's shared-oracle and integration limits (§§2.15–2.16) still apply.
Agreement can show adherence to a chosen rule without establishing that the
rule is intended or justified. Independent observation can establish what
happened without establishing that it must continue to happen. Conversely,
discovering that an expectation originated in a regression or refactor does
not make its present contract expendable. The disposition and DAC histories
show both persistence of intent and deliberate changes in its expression.

## 10. Open questions about authority

1. **What status does ordinary no-termination have for callers?** The survivor
   documentation denies a desired containment rule, while the contract states
   no termination on ordinary completion. An explicit account of whether
   callers may rely on that policy would distinguish a compatibility promise
   from a current limitation. The examined texts do not settle it.
2. **What is the intended lifetime of the setup-oracle counterexample?** Its
   purpose is explicit, but its checker is copied from current sources. A
   statement of intent for the experiment after that checker rejects the
   counterexamples would settle whether continuing acceptance was ever meant
   to bind future checking. The historical observation alone cannot do so.
3. **Which guarantees would govern additional early evidence or attribution?**
   The present contract deliberately withholds unpublished exec facts and
   sandbox-cause claims. A separate publication or attribution contract,
   supported by observations sufficient for its claims, would settle the
   authority of additional facts. Existing abstention rules neither authorize
   those extensions nor prove that every such extension would be unsound.
4. **Is the outcome check's exact textual arrangement intentional?** The
   maintenance obligation and original integration goal are documented; a
   current rationale for the source-form assumptions and separate checking
   paths would establish whether their preservation is itself intended.
5. **What is committed about the native deny baseline across environments?**
   The classifier contract is clear, and the tested platform is named. An
   explicit account of whether preserving this native answer is a condition
   of platform support would distinguish an experimental prerequisite from
   an expected result whose loss is itself treated as a compatibility failure.
   The historical observation cannot decide that policy.

## Inspection footprint

This investigation executed no test case, build, native probe or prune, and
made no product, test or contract edits. Apart from creating and removing the
disposable worktree and writing this report and scratch checks, operations were
read-only: Git and file reads, static parsing and document checks. All cited
historical commits precede the examined revision. The detached source worktree
retained that revision, an empty Git status, and no `tests/out` or
`tests/.checkout.lock` before removal.
The only repository content written for this investigation is this report;
scratch validation material is outside the checkout. No test changes or case
retention decisions are proposed here.

Report review also checked the cited history and selected assertions from the
main checkout at `4365395`. Its product sources, tests and contract documents
are unchanged from the examined revision; the companion includes its completed
§§2.15–2.16 investigations. Static checks cover the report's Markdown, relative
links and anchors, catalog case IDs and cited commit ancestry. These checks do
not supply fresh execution evidence for any case.
