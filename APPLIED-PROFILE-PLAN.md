# Applied-profile capture

Authorized 2026-09-14 from PAWL's policy-application handoff. Implement and qualify
compiled-object capture on authored controls; do not execute the receiving corpus
experiment or overwrite PAWL's historical bundle.

- [x] STATIC: bounded capture ABI, worker input/object identities, Swift receipt
  projection and fail-closed availability; preserve normal policy application.
- [x] STATIC: distinguishing/ignored-axis and refusal tests, ABI agreement,
  controller preservation and documentation.
- [x] BUILD: signed candidate in a separate distribution directory; retain build
  provenance and qualification receipts.
- [x] LIVE, serial: bounded authored controls for changed source/params, ignored
  diagnostics, application failure and the documented unsupported attempt route.
- [x] STATIC: hand off contract, candidate identity and test results to PAWL.

Capture names the object supplied to successful sandbox_apply, not a kernel
readback. Raw bytecode and input identities are sensitive evidence; retain them
only in restricted qualification/consumer custody. A missing or invalid capture
does not become a source-only success. Document all executed controls and stops.

## Qualification scope — 2026-09-14

Run the existing Swift runner suite against the separate candidate (its authored
worker/validator controls, never the receiving corpus), plus ABI/source-drift
checks. Then at most eight single-step authored CLI specimens: allow-default,
deny-default, parameterized literal at two values, an unused-parameter change,
the same literal with only a diagnostic specimen id changed, capture-off, and
an explicitly test-overridden post-apply worker death. Independently compile the
five distinct successful source/parameter inputs in PAWL for exact byte comparison.
The requested query is file-read-metadata on an owned qualification file; its
attempt is the documented unsupported generic/access route. Stop the CLI series
on any unexpected result. Failed-apply/length/corruption/PID/nonce refusal is also
covered by independently constructed pure receipts. No corpus query is authorized.

The initial Swift run built successfully but used the preserved ABI-4 dist worker
against ABI-5 host code: 103/118 passed, fifteen worker cases refused before apply.
The first production build exposed a client source-set omission: the new Codable
receipt belonged in PWRunnerAPI.swift, which the client builds without CWorker.
It was moved there and the separate candidate build succeeded. No libsandbox
crash occurred in either check.

Completion measured 2026-09-14: the separate Developer ID candidate and strict
signature check passed; 65 C/Swift ABI layout values agree, independent C capture
controls and source-drift checks pass, and the Swift suite passed 137/137 against
that candidate. A Swift test-only SHA256 sequence/collection conversion was fixed
before that green run. The eight authored CLI controls all passed through the
controller. Six captured successful receipts exactly equal PAWL's independently
compiled expected bytes; seven successful query contexts produce the intended
allow/deny and unsupported-attempt receipt. Capture-off omits the payload; forced
post-apply death reports unavailable without bytecode. Failed-apply and corrupted
capture refusals were constructed controls, not forced native apply failures.

Candidate, logs, input/receipt custody and build provenance are under PAWL's
`.scratch/applied-profile.s9t0Ma/`; the receiving immutable plan retains the
load-bearing artifacts. This work did not overwrite default dist or PAWL's
installed bundle, attempt notarization or commit either checkout. The installed
PAWL bundle is the user's separate `8ac3a97e33` vendoring commit, not byte-equal
to the older historical preparation; that older bundle remains in immutable
custody, and the new execution plan binds the scratch candidate explicitly.
The receiving corpus experiment remains unexecuted pending user authorization.
Keep this activity plan until the delivery is accepted/landed, then dissolve it
into the durable user guide, runner documentation and tests.

## Landing handoff — 2026-09-14

Subsequent user authority permitted PAWL's separate eighteen-query corpus
experiment, which completed once. Its retained observation is
`5e346eef81724cc52739f54c1ed9b81d8316c3532d30f1c15dae58deff526986`:
twelve expected-polarity controls and six original-source queries were admitted,
with all eighteen captured objects equal to their frozen expected bytes. PAWL
owns the exact claim, custody limits and pending audit; this is not an expansion
of the runner's authored qualification or a kernel-readback claim.

The user then authorized scoped commits after PAWL's full gate. That escalated
gate passed with four workers: 7606 passed, 17 skipped, 36 xfailed, plus CARTON
validation and the Swift build. Its logs and repair record remain in PAWL's
receiving activity plan. This does not rerun or stand in for PolicyWitness's
earlier 137/137 candidate qualification and authored controls recorded above.
Land only capture implementation, its tracked helper, tests and documentation;
leave concurrent test-harness changes alone. The separately signed candidate and
both default/installed bundles remain unchanged. The PAWL audit prompt is to be
replaced only after both scoped commits and left uncommitted for review.
