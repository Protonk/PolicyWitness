# Controller authority baseline

## Entry decision and identity

Gate opened by the coordinator on 2026-11-13 for the independent investigations
in the [controller plan](../../controller/NEW-DOC-INTEGRATION-PLAN.md).
The source snapshot is `dcc7dd0bd0634a603379ff185228abca70b5d22f`.
The accepted implementation, tests, authored contract and generated public
snapshot are unchanged from `a5de0c638ff37bfa99242147fa7a8cf00a915f0d`.
The intervening changes are the CLI evaluation and two release records only.
Baseline/dispatch/report commits are separate investigation records.

The maintainer authorized proceeding and committing during the plan. In response
to the missing CLI development artifacts, the maintainer said:

> I think we can settle for the historical pre-requisite OR we can regenerate a single run to evaluation. The trouble was at the conclusion of the previous plan there were 37 test runs and 2 whole worktrees, which wwas too much. You should proceed.

The coordinator selects the historical-prerequisite route. The committed CLI
evaluation and its recorded acceptance settle prerequisite completion; absent
raw runs are not newly inspected, retained execution evidence or release credit.
New consequential claims need applicable checks. This disposition replaces the
entry gate's requirement to reconstruct the pruned historical raw evidence. It
does not waive verification of changes made by this investigation.

No CLI failure disposition remains pending. The open success/integrity product
question and review of later CLI corrections remain investigation inputs, not
prerequisite blockers. The maintainer's acceptance, digest-and-length revision,
extracted `read_hosts` revision, and instruction to keep the tree buildable are
settled. Preserve the guide's accepted command-table row; workflow presentation
is deferred. No release preparation or tag is authorized by this plan.

| Identity | Observed value |
| --- | --- |
| Development contract, recomputed | `development:6a333cf6f19aea6939fa843655b6ce2a90ec05837fb4bb6b8b9288b0ccc572f0` |
| Worker identity, C and Swift declarations and app provenance | `52bbda618677886b6c59dcf5dd999e2b2a5021cbd2c8dc4f08aa0ba66ef2dd38` |
| Wire fingerprint, generated Rust declaration | `80013e5b7342e84db61177804883655e3d60bc370bf0a4aa1bc61453a064e224` |
| `docs/contract/public.json` SHA-256 | `36be1491309c8d204f005bafa3abdb1f643bacda3b09c961b3fd1b5ac13fc366` |
| `docs/porcelain.json` file SHA-256 (distinct from wire fingerprint) | `538b3cf552fa8fa3578287e39a56594592799ff6062d35e5bfc7242ea4b009c2` |
| Example source SHA-256 | `31ae70312ee0d32bffc8a524a2b6c663237a0387bb621c335ecf75b3cd5536b6` |

Tracked source was clean. The only initial untracked files were five Python
bytecode cache files under `docs/contract/__pycache__`; they were inspected as
bytecode and removed. Checks use `PYTHONDONTWRITEBYTECODE=1` to avoid recreating
them. No worktree was created and `tests/out/runs/` was empty at entry.
Annotated release tags through `v0.3.7` are present; no `v0.3.8` tag exists.
Current stamps remain `unreleased` where changed; ordinary history checks pass.

## Prerequisite review

The final [CLI plan](../../docs/CONTRACT-EXAMPLE-PLAN.md), including its entire
evaluation, later revisions, candidate verification and handoff, was read.
Implementation is `23440049`, accepted revisions are `d3c2a72a`, support is
`a5de0c63`, and later evidence records are `a1ceeebe` and `dcc7dd0b`.
Acceptance was recorded in `0c1b62a1`; it is not being requested again.

Coordinator inspection covered the constant/emitter, the request emission rule
and both extracted example citations, their support scopes, preparation capture,
the live case and independent-control construction, the consumer's admission
and result rule, and extraction/stale-output controls. The gate distinguishes:

- The command gates identity and renders before writing, with `write_all` and
  explicit flush. Unit controls of parse/gate failures are not signed-app
  observations. The native host still owns grammar admission through `run`.
- Exact request equality is a controlled preparation observation under
  `test:policy-witness`, ending at the client callback. Signed-app pipe length
  supplies neither byte identity nor host receipt.
- The result consumer uses captured host bytes and its admission gates,
  independently of the result fields. Its documented capacity-gate limitation
  remains visible. Interpretation controls do not establish native production.
- Example extraction changes the public request payload; source changes can
  change build identity. Support is `check_read`, without current execution or
  archived-release credit. The generator controls assert freshness refusal,
  unchanged files on refusal, and changed rendering/payload/identity afterward.

Reader inventory was rediscovered over tracked `.py`, `.sh` and `.rs` files:
51 files contain `from consumer import`, `consumer.validate` or `consumer.load`,
including Rust embedded Python. This is a conservative navigation inventory,
not a count of independently established call paths. `envelope_skeleton` has
seven current call sites: the five described in the CLI evaluation plus two
in the example's offline controls. No current caller is assumed covered merely
because an older planning count or unchanged digest says so. B will trace
reachability and C will challenge the relevant admission boundaries.

Historical results accepted as recorded, with their raw artifacts absent:

| Item | Historical result and scope |
| --- | --- |
| Step 3 evaluation and replacement sample | Two separately identified bounded ten-run samples; original build and corrected build distinguished; no failed assertion in either sample. These are not fresh trials. |
| Serialization challenge | Baseline and restoration passed, compact-serialization mutation failed the exact preparation assertion; repeated at `23440049`, test identity only. |
| Final support/revisions | Recorded checker coverage reaches 192 matched controls and 67 assertions; support remains check-read. |
| Candidate default battery | `example-candidate-battery`, `20261113T025645Z_fa04991f`, build `a5de0c63`: 231 case results, no skip/unrun/harness error, unchanged app inventory. |
| Candidate build refusal rehearsal | `example-candidate-rehearsal`, `20261113T032129Z_fe9dd38c`: 88 refusal controls and 16 bypass demonstrations; nested release-form fixture acceptance passed 231 results. This is historical fixture evidence, not a release or a present rerun. |
| Earlier failures | Plan prose-scan failure corrected; closed-at-launch stdout expectation withdrawn on observed successful write; candidate-record prose scan corrected. The evaluation retains each disposition and replacement run. |

The later CLI corrections were not independently reviewed again. A/B/C receive
their required source views and assess the final state without inheriting an
allocation recommendation. The old review does not stand in for their work.

## Fresh structural checks and available equipment

Both commands exited zero on this baseline:

```sh
env PYTHONDONTWRITEBYTECODE=1 tests/lib/python.sh docs/generate_contract_stamps.py --tree-check
env PYTHONDONTWRITEBYTECODE=1 tests/lib/python.sh docs/generate_contract_stamps.py --check --require-history
```

The tree reports 19 surfaces, 1,907 nodes, 1,004 fields, no uncovered records,
and free counts condition 51, dependency 0, effect 78, when 4. These checks
establish structural agreement and history availability, not behavior.

The local platform reports macOS 26.7.1 on arm64. The selected app remains
`dist/PolicyWitness.app`; its plist and provenance report clean source
`a5de0c638ff37bfa99242147fa7a8cf00a915f0d`, description
`v0.3.7-38-ga5de0c63`, build number 1372, provenance time
`2026-11-13T02:56:42Z`, and the contract/worker identities above. This is an
inspection of carried metadata, not fresh signature verification or execution.
The provenance reports Developer ID team `42D369QV8E`. Keychain availability,
GUI, live XPC and unified-log access are not yet established for this task;
the dispatcher and prescribed escalation procedure will establish them when
needed. No new app was built to open the historical gate.

## Artifact discipline

Use this checkout and serialize builds/tests through its existing lock. No
new worktree by default. Batch necessary selections, retain evidence until its
review/disposition, then use the repository pruning tools. Never copy raw runs
into these records or preserve them with manual pins. The coordinator records
new runs and their scope in `EVIDENCE.md`, and records any isolation workspace's
creation and removal there. A short historical summary is not raw evidence.
