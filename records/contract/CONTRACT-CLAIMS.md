# CONTRACT.md claim inventory

Stage 3 of the plan in `records/contract/CONTRACT-CONTACT-PLAN.md`. One row per
claim in `docs/CONTRACT.md`: what the repository does that makes it true, the
source that implements it, and the check that would fail if it were false.
This file is the index. The rows themselves, with their full mechanism
accounts, are in `records/contract/claims/`, one file per unit. Sibling
artifacts are named by path without links, under the records link rule.

## How the rows were made, and how far to trust them

- Four delegated passes wrote the rows on 2026-11-09 at `00a32ef7`, each with
  a narrow brief, read-only. Each was told to read the source and the checks
  itself, to treat the report and traces as leads, to describe the machinery
  literally without judging it, and to say what it did not open.
- Nothing was built or run. A row's grade is "test read" or "source read" as
  its pass states it. No row is at grade "run".
- The coordinator assembled the rows mechanically and has read two of them
  through (`K-243-9` and `K-180-1`). Every other row is, from the
  coordinator's seat, a delegated read. Each row ends with what its pass did
  not find or did not open; several cite a helper located by search and not
  read, and several map a test script to a catalog case by name.
- Rows are as the passes wrote them, apart from the heading and the added
  **Pass** line.

## Coverage so far

| Covered | By |
| --- | --- |
| All thirteen "Example:" sentences (C:63, 129, 135, 141, 147, 153, 159, 165, 171, 243, 249, 255, 296) | `examples-request`, `examples-reply` |
| C:168-210, the `equipment` region to the end of `actors[].application` | `equipment-1` |
| C:212-236, termination dependencies and gates; C:165, `lifecycle`; C:243, `profile` | `gates-lifecycle-profile` |

Not yet inventoried: U01, U02, U16 to U20, and everything in U03 to U09 and
U13 to U15 other than the example sentence.

## Reading the index

- **Claim ID** is `K-<first line>-<n>`. It does not change when other units
  are added.
- **Kind** is one of the plan's ten. **Status** is the plan's owner status:
  `owned`, `sourced`, `split` or `unowned`. Where a pass qualified a status,
  the qualification is in the row, not here.
- **Source files** and **Check files** count the distinct paths a row cites.
  They are a rough guide to how much machinery stands behind a sentence, for
  choosing which rows to open first. They are not a judgment, and a low
  number does not mean a simple mechanism.

## Counts

| Kind | owned | sourced | split | unowned | Total |
| --- | --- | --- | --- | --- | --- |
| `denial` | 3 | 2 | 2 | 3 | 10 |
| `evidence` | 39 | 3 | 7 | 0 | 49 |
| `example` | 16 | 2 | 1 | 1 | 20 |
| `identity` | 0 | 1 | 0 | 0 | 1 |
| `machinery` | 0 | 1 | 0 | 0 | 1 |
| `referral` | 0 | 1 | 1 | 0 | 2 |
| `residue` | 1 | 0 | 0 | 0 | 1 |
| `shape` | 9 | 1 | 0 | 0 | 10 |
| Total | 68 | 11 | 11 | 4 | 94 |

## Index

### U03, `request` region

Rows in `records/contract/claims/U03.md`. 2 owned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-63-1` | C:63 | example | a foreign assertion plus an invalid runner selector reports the contract refusal | owned | 8 | 6 |
| `K-63-2` | C:63 | example | …and starts no client | owned | 5 | 6 (opt-in among them) |

### U04, `policy` region

Rows in `records/contract/claims/U04.md`. 1 owned, 1 sourced.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-129-1` | C:129 | example | a missing augment refuses before worker creation | owned | 4 | 5 |
| `K-129-2` | C:129 | example | …and leaves the input file unchanged | sourced | 4 | 4 |

### U05, `probes` region

Rows in `records/contract/claims/U05.md`. 2 owned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-135-1` | C:135 | example | file `open_write` opens with truncation | owned | 5 | 6 (opt-in among them) |
| `K-135-2` | C:135 | example | a same-shape foreign build assertion prevents that operation | owned | 1 | 4 (opt-in among them) |

### U06, `actors` region

Rows in `records/contract/claims/U06.md`. 2 owned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-141-1` | C:141 | example | a phase naming a nonexistent actor is refused | owned | 4 | 5 |
| `K-141-2` | C:141 | example | …before children | owned | 4 | 4 |

### U07, `envelope` region

Rows in `records/contract/claims/U07.md`. 1 owned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-147-1` | C:147 | example | a foreign helper envelope claiming compilation cannot supply a successful policy-check status | owned | 4 | 5 |

### U08, `dossier` region

Rows in `records/contract/claims/U08.md`. 1 sourced.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-153-1` | C:153 | example | changing the source file after admission does not change the held submission | sourced | 5 | 3 |

### U09, `steps` region

Rows in `records/contract/claims/U09.md`. 1 owned, 1 split.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-159-1` | C:159 | example | a foreign host reply inside a current envelope yields one unsupported diagnostic | owned | 5 | 7 (opt-in among them) |
| `K-159-2` | C:159 | example | ... without recovered comparisons" (no comparison from the foreign reply is interpreted or reported as a comparison) | split | 5 | 6 (opt-in among them) |

### U10, `lifecycle` region

Rows in `records/contract/claims/U10.md`. 4 owned, 1 split.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-165-1` | C:165 | evidence | Lifecycle claims depend on native progress, collection and termination observations. | owned | 2 | 2 |
| `K-165-2` | C:165 | evidence | Unknown or contradictory observations withhold dependent claims. | owned | 3 | 1 |
| `K-165-3` | C:165 | evidence | An exit request is not proof of reap. | owned | 3 | 3 |
| `K-165-4` | C:165 | evidence | Successful return alone is not an effect witness. | split | 2 | 3 |
| `K-165-5` | C:165 | example | an unreaped worker remains unconfirmed even after a successful termination request | owned | 6 | 8 |

### U11, `equipment` region

Rows in `records/contract/claims/U11.md`. 48 owned, 8 sourced, 5 split, 2 unowned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-171-1` | C:171 | evidence | Actor evidence binds observations to the named process and service-sealed equipment. | owned | 10 | 10 (opt-in among them) |
| `K-171-2` | C:171 | identity | The worker ABI identity remains independent of the public build identity. | sourced | 6 | 1 |
| `K-171-3` | C:171 | machinery | Worker entitlements are read from the selected binary. | sourced | 2 | 3 (opt-in among them) |
| `K-171-4` | C:171 | example | an equipment hash mismatch prevents use of the claimed equipment | owned | 5 | 5 |
| `K-176-1` | C:176 | residue | Actor execution has no declaration reply. | owned | 3 | 5 (opt-in among them) |
| `K-176-2` | C:176 | denial | Actor execution has no … singular worker projection. | owned | 4 | 3 |
| `K-177-1` | C:177-178 | shape | `actors[]` owns each launch, subprocess, application assessment and equipment association. | owned | 3 | 5 |
| `K-178-1` | C:178-180 | evidence | The `authority_setup.host` run/region/custody scopes and `authority_setup.workers` cells retain primary setup, indepen… | owned | 6 | 5 |
| `K-180-1` | C:180-181 | denial | An acquired decision does not publish another cell. | unowned | 2 | 1 |
| `K-181-1` | C:181 | denial | A scheduling summary does not replace any actor's facts. | split | 4 | 3 |
| `K-183-1` | C:183-184 | evidence | `equipment_inventory` identifies the selected service's sealed equipment inventory. | owned | 4 | 2 |
| `K-184-1` | C:184-186 | shape | Rows of `equipment_bindings` and `equipment_entitlements` are named by position: a binding is identified by its `role`… | owned | 4 | 1 |
| `K-186-1` | C:186-187 | shape | `binding_ref` and `entitlements_ref` are zero-based indexes into those two arrays. | owned | 5 | 2 (opt-in among them) |
| `K-187-1` | C:187-188 | shape | An actor's `binding_ref` is null when no binding row was produced for its role. | sourced | 5 | 1 (opt-in among them) |
| `K-188-1` | C:188-190 | shape | `equipment_bindings` separates packaged roles from explicitly instrumented overrides; the latter carry `unverified_fix… | owned | 5 | 2 (opt-in among them) |
| `K-190-1` | C:190 | denial | Override rows "cannot establish packaged selection. | unowned | 4 | 1 |
| `K-190-2` | C:190-191 | shape | `equipment_entitlements` contains independently associated static and live XML read-backs. | owned | 4 | 2 (opt-in among them) |
| `K-191-1` | C:191-192 | evidence | Every actor's requirements are evaluated separately using boolean true keys. | owned | 4 | 6 (opt-in among them) |
| `K-192-1` | C:192-193 | evidence | Requirements are evaluated with boolean true keys "including in the live read-back. | owned | 4 | 1 |
| `K-193-1` | C:193 | referral | Bounds and reserve geometry belong to [LIMITS](LIMITS.md). | split | 4 | 2 |
| `K-194-1` | C:194 | evidence | Runtime inspection failure cancels all scheduled activation. | owned | 5 | 2 |
| `K-194-2` | C:194-195 | evidence | Runtime inspection failure "retains any already published setup/application facts. | owned | 3 | 1 |
| `K-195-1` | C:195-196 | denial | Runtime inspection failure "is not a before-launch `preparation_failure`. | owned | 5 | 2 |
| `K-196-1` | C:196 | evidence | Independent earlier cancellation remains visible. | sourced | 3 | 0 |
| `K-198-1` | C:198-199 | evidence | `preparation_failure` admits only `resolved_plan/inconsistent_assignment` or `equipment/equipment_binding_refused`. | split | 4 | 5 (opt-in among them) |
| `K-199-1` | C:199 | evidence | `preparation_failure` comes "with `runner_failed`, `rc: 1`. | owned | 5 | 2 (opt-in among them) |
| `K-199-2` | C:199-200 | evidence | `preparation_failure` comes with "no launched actors. | owned | 4 | 4 (opt-in among them) |
| `K-200-1` | C:200 | evidence | Observation arrays are empty. | owned | 4 | 2 (opt-in among them) |
| `K-200-2` | C:200-202 | evidence | Unique bounded declarative phase and action identities may remain, without claiming that those actions ran. | sourced | 4 | 1 (opt-in among them) |
| `K-202-1` | C:202 | denial | This is the sole exception to their normal complete observation partition. | split | 3 | 1 (opt-in among them) |
| `K-204-1` | C:204 | shape | `actors[].application` has closed state/basis pairs. | owned | 3 | 5 |
| `K-204-2` | C:204-205 | evidence | Unapplied intent is `not_requested/unapplied_declaration`. | owned | 4 | 2 |
| `K-205-1` | C:205-206 | evidence | `not_attempted` requires host proof of no launch or an eligible terminal worker branch before application. | owned | 4 | 5 |
| `K-207-1` | C:207 | evidence | `observed` requires an applied publication or the native apply-failure publication. | split | 4 | 3 |
| `K-208-1` | C:208 | evidence | With no such source, requested application is `unobserved`. | owned | 3 | 1 |
| `K-209-1` | C:209-210 | denial | Setup timeout, `done`, process death or an auxiliary reporting failure alone cannot establish application nonattempt. | owned | 4 | 2 |
| `K-212-1` | C:212-213 | evidence | Termination dependencies retain a source actor's `owned_reap`. | owned | 5 | 5 |
| `K-212-2` | C:212-214 | shape | `owned_reap` includes native PID/return/raw wait status, capture stage, ownership/departure flags, `capture_ordinal` a… | owned | 5 | 4 |
| `K-214-1` | C:214-215 | shape | Each phase may retain `activation_observation: {capture_ordinal, observed_ns?}`. | owned | 3 | 3 |
| `K-215-1` | C:215-216 | denial | These ordinals are local to the source actor process, not a global process counter. | sourced | 1 | 0 |
| `K-217-1` | C:217-218 | shape | `termination_gate.observation` is `{capture_ordinal}` referencing that source actor's owned reap. | owned | 2 | 2 |
| `K-218-1` | C:218-220 | evidence | Every nonnull observation, including a failed gate's, requires a positive matching source reap ordinal and a present l… | owned | 5 | 4 |
| `K-220-1` | C:220-221 | evidence | A satisfied gate additionally requires the source's final activation before its owned reap. | owned | 3 | 2 |
| `K-221-1` | C:221 | evidence | …[the source's] owned reap before gate closure. | owned | 2 | 0 |
| `K-221-2` | C:221 | evidence | …consistent child PID. | owned | 2 | 0 |
| `K-221-3` | C:221-222 | evidence | …and decoded wait status. | owned | 2 | 0 |
| `K-222-1` | C:222 | evidence | …unbroken ownership. | owned | 2 | 0 |
| `K-222-2` | C:222 | evidence | …and no prior host departure request. | owned | 2 | 0 |
| `K-223-1` | C:223-224 | evidence | Both source final-activation and owned-reap timestamps must be present and monotonically ordered. | owned | 3 | 0 |
| `K-224-1` | C:224 | evidence | The gate wait also requires a usable clock. | owned | 2 | 0 |
| `K-224-2` | C:224-225 | evidence | …no native wait error. | sourced | 2 | 0 |
| `K-225-1` | C:225-226 | evidence | …and elapsed time within the positive termination-gate allowance. | owned | 2 | 0 |
| `K-225-2` | C:225-226 | referral | The termination-gate allowance is given in LIMITS. | sourced | 5 | 1 |
| `K-227-1` | C:227 | evidence | An abnormal natural reap can satisfy termination. | owned | 2 | 0 |
| `K-227-2` | C:227-228 | evidence | Final phase completion [or] `done` … cannot substitute. | owned | 2 | 0 |
| `K-228-1` | C:228 | evidence | A requested exit … cannot substitute. | owned | 0 | 0 |
| `K-228-2` | C:228 | evidence | A cleanup-only reap cannot substitute. | owned | 3 | 0 |
| `K-230-1` | C:230 | evidence | Native facts may retain absent source timestamps after clock failure. | owned | 2 | 0 |
| `K-230-2` | C:230-231 | evidence | …but cannot satisfy the dependency without them. | owned | 0 | 0 |
| `K-231-1` | C:231-233 | evidence | Once dependent activation has been stored, a missing post-store dependent timestamp retains that activation and the al… | owned | 2 | 0 |
| `K-234-1` | C:234 | evidence | A present dependent timestamp must not precede the source reap. | owned | 2 | 0 |
| `K-234-2` | C:234-235 | evidence | Reached failed gates withhold activation, collection and release. | owned | 2 | 0 |
| `K-235-1` | C:235-236 | evidence | …even if cleanup later observes reap. | owned | 1 | 0 |

### U12, `profile` region

Rows in `records/contract/claims/U12.md`. 2 owned, 1 sourced, 4 split, 2 unowned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-243-1` | C:243 | evidence | A compiled-profile receipt inherits its admitted host reply context. | owned | 2 | 1 |
| `K-243-2` | C:243 | denial | It has no independent schema marker. | sourced | 2 | 1 |
| `K-243-3` | C:243 | evidence | Status … [and] stage … must be consistent. | owned | 4 | 6 |
| `K-243-4` | C:243 | evidence | …nonce … must be consistent. | split | 4 | 2 |
| `K-243-5` | C:243 | evidence | …worker binding … must be consistent. | split | 2 | 2 |
| `K-243-6` | C:243 | evidence | …byte count … must be consistent. | split | 2 | 0 |
| `K-243-7` | C:243 | evidence | …digest must be consistent. | split | 2 | 0 |
| `K-243-8` | C:243 | denial | A detached receipt grants no producer context. | unowned | 2 | 0 |
| `K-243-9` | C:243 | example | a wrong nonce refuses the receipt even inside a current reply | unowned | 7 | 11 |

### U13, `transport` region

Rows in `records/contract/claims/U13.md`. 1 owned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-249-1` | C:249 | example | a foreign live peer behind a matching registry entry receives no specimen submission | owned | 6 | 7 (opt-in among them) |

### U14, `refusals` region

Rows in `records/contract/claims/U14.md`. 2 owned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-255-1` | C:255 | example | an old `schema_version`-only specimen reports missing `contract` | owned | 4 | 3 |
| `K-255-2` | C:255 | example | …not an unknown-field error | owned | 4 | 2 |

### U15, `installation` region

Rows in `records/contract/claims/U15.md`. 2 owned.

| Claim | Lines | Kind | Claim, shortened | Status | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- |
| `K-296-1` | C:296 | example | an owned legacy record cannot execute | owned | 4 | 4 (opt-in among them) |
| `K-296-2` | C:296 | example | …but can be removed after observed absence | owned | 2 | 3 (opt-in among them) |
