# LIMITS documentation implementation

Prepared D1–D5 changes in `docs/limits.json`, authored regions of
`docs/LIMITS.md`, and the existing `LimitsContractTests.swift` owner. No product
code, generators, tests, dispatcher/list commands, builds or native probes were
executed. No agents were started. Root owns regeneration and later validation.

## Changes and rationale

- D1: distinguish ordinary/declaration from public actor requests; scope eight
  declaration phases, sixteen global actor phases, global action/lifecycle
  counts and per-policy source/parameters. Correct public phase-record reachability,
  actor label admission, common/branched refusal order and unused issuer override
  capacity checking. Explain form exclusivity and per-participating-actor exec
  exclusion without duplicating semantic grammar.
- D3: replace nominal wording for elapsed host waits; start actor setup before
  preparation; distinguish one schedule pool and one collection pool, total and
  I/O overrides, ordinary sentinel override, per-worker exec exclusions and
  sampled lifetime enforcement. Qualification prose separates charged execution,
  host recipient wait, release proxy and setup plus elapsed execution total.
  The coordinator corrected the inherited report's total-accounting shorthand:
  total includes collection during execution, excludes final cleanup and the
  earlier cutoff-to-setup gap. No whole-lifetime or every-worker-exchange claim.
- D4: validator retention uses submitted planned query lists, before writes.
  Captures are per opted-in apply actor and require receipt prerequisites.
  Fallback is diagnostic, can precede host admission and can accumulate more
  policy inputs than the admitted actor count. Per-helper retention is not a
  cumulative envelope/memory limit. Retain the 85,852,557-byte informative reply
  construction, 84 MiB client and 248 MiB controller retention; clarify fixture
  completeness is not a proof of every future producer branch. Add derived
  authority-region formula without inventing an independent cap.
- D5: narrow the completeness promise to numeric capacities/budgets/retention,
  with routes to request, extension, capture, prediction and receiver semantics.
  Add request_failure_path_components=8 and request_failure_path_component=63;
  retain whole-path-or-null and separate 127-byte admission parameter-key echo.

The first-refusal list is replaced rather than appended to: a second partial
ordering would invite contradiction. The declaration/actor scope paragraph
consolidates distinctions needed to use the tables. Existing source-only
observed-path, attempt-error and stream-overflow qualifications remain intact.
No numeric values of the original 93 entries changed. Source inspection of the
diff confirms both generated LIMITS regions remain byte-for-byte untouched.

## Grounding and assertions

Inputs consulted include the plan, outflow decisions, readiness and verification
handoffs, admission/timing/evidence reports, all 93 grounding entries (33/30/30),
and the limits/consistency findings. Current constructor and admission source
was inspected for diagnostic semantics and refusal order. Recorded I1–I3 credit
comes from `implementation/VERIFICATION-01.md`: I1 actor 63/64 controls passed,
I2 native constructed exact-1-MiB capture passed (not compilation/application of
that size), and I3 constructed orchestration association passed (not live helper
invocation). F1 remains separately deferred and is not relabeled as passing.

`generate_limits.py` VALUE_OWNERS is a path allowlist. The existing Swift owner
selects manifest rows naming its file and compares their ID set against its
observations. Both new rows name only that existing value owner. Its new scans
construct actual returned paths for independent finite depth/byte ranges and
observe retained maxima, then compare them to the inventory; they do not copy
8/63 from the manifest. An empty scan fails with TestFailure. A separate case
uses literal depth 8/9 and ASCII/multibyte component 63/64 to assert full retention
or null, plus null input. Rust RequestError parity is source-inspected only.
No additional value-owner source, generator change or registration is needed.

## Coordination and outstanding work

Root must regenerate with the owning generators so LIMITS tables/coverage and
shared guide prose reflect these inputs. Shared prose links use guide anchors;
qualification links the existing principal-policy-qualification section. No
reader-facing document links into records were added. Root owns adjacent guide,
controller and witness README changes; architecture owner owns its input/tours.

These edits and new Swift assertions have not been compiled or executed. No
generator or generator --check ran in this task, and no source-drift or runtime
credit is claimed for this candidate. Pending work is root regeneration/review,
then user-authorized validation and final paired readers. Existing historical
passes do not cover the modified LimitsContractTests source. Full Rust depth
boundary execution, actual system sleep, arbitrary maximal actor compositions,
production-duration expiry and total native-call/cleanup or memory ceilings are
not newly established. No unresolved implementation question blocks this draft.

Coordinator follow-up: authored actor/path/key maxima use owning scalar spans;
the capture condition states nonce syntax and identity matching without claiming
freshness is enforced at admission. Formula constants remain derived geometry.
