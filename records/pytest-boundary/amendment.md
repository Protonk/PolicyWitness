# Experimental amendment to C0.2

Author: the independent reviewing Codex agent, 2026-10-30, under the user's
subsequent investigation authorization. This is an exposed, prospective
experiment following the review, not a correction attributed to C0.2's author.

Baseline: `77eb987554eef10ffa3371ffb21b235097562a78`. Engine: pytest **9.0.2**
in an isolated Python 3.14 virtual environment. Record dependency versions and
hashes before execution. Serial execution, no xdist, no auto-loaded plugins,
no ambient `PYTEST_ADDOPTS`/`PYTHONPATH`, no bytecode writes, explicit config,
`--capture=fd`, `--import-mode=importlib`, no cache provider, assertions enabled.
The actual subject subprocess gets an explicit interpreter, environment,
stdin/stdout/stderr and descriptor set; it does not inherit capture implicitly.

| Question | Supports | Weakens | Unresolved by this experiment |
| --- | --- | --- | --- |
| Can pytest own ordinary selection, scheduling and reporting? | Native pytest selection and fixture execution produce the observed starts and phase reports; the supervisor has no per-case execution loop or second fixture scheduler. | Supervisor must select/dispatch ordinary cases, reconstruct assertion results, or suppress inconvenient framework outcomes. | Full catalog metadata, dependency expansion and polyglot public-ID compatibility. |
| Can accounting and ownership survive partial setup, interruption and death? | Durable selection precedes eligibility; resource intent precedes acquisition; independent receipts and exit/lock observations agree with incomplete/failed accounts and justified recovery. | Missing/duplicate reports pass; queued work starts after interruption; ownership disappears; a surviving protected child loses the lock; cleanup proceeds on guessed exit. | Arbitrary escaped descendants, launchd installation, power-loss durability and all signed-app gates. |
| Does the arrangement simplify carrying consequential changes? | An exposed real replay removes ordinary loop/report scaffolding while preserving native reach, independent oracle and diagnostics, with a localized adaptation. | Equivalent declarations multiply, source changes are hidden by green results, or framework integration merely adds a second scheduler/report model. | Controlled productivity, net migration cost, runtime speedup and long-term maintenance. |

Feasibility and maintenance benefit are separate verdicts. A complete local
demonstrator can establish the selected lifetime/reporting obligations without
establishing a net reduction across PW. Lines and timings describe this equipment,
not agent productivity or an alternating performance comparison.

One collection process may wait at a publication barrier before execution,
instead of collecting twice. The external supervisor publishes ownership and
the selected IDs before releasing that barrier. Pytest remains responsible for
the ordinary execution order and fixture phases. Durable report validation and
joining missing items back to the plan are explicit integration costs.

The candidate reuses `tests/lib/checkout_lock.py` and `retention.py` directly.
Their machinery remains in the architectural cost; the current dispatcher does
not execute the candidate or confer its hold. Resource recovery is restricted
to the owned resource, with live peer/descriptor identity and exit observations;
it does not admit a new test session under a dead supervisor's claim.

The conditional adaptation is the historical C extraction, old source
`f8f3c24f` and extracted candidate `341f9441`. It directly tests whether fixture
sharing and parameterized reporting simplify include-closure/interception and
mutation maintenance after the lifetime boundary is proven. Use the unchanged
native fixture and independent call-policy golden, all six intended assertion
rejections, missing-owner refusals and an intentionally stale adapter. This is
an exposed historical replay, not a fresh refactor or blinded comparison.

The verified API basis is the versioned pytest 9.0.x reference identifying
9.0.2: collection and runtest phase hooks are available; a yield fixture that
raises before yielding does not run its post-yield teardown. These primitives
do not implement resource recovery. Sources:
[API reference](https://docs.pytest.org/en/9.0.x/reference/reference.html),
[fixture teardown](https://docs.pytest.org/en/9.0.x/how-to/fixtures.html#handling-errors-for-yield-fixture).
