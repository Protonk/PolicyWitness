# Bounded worker-language RCAs

This round follows the frozen `positive-trial.md` and `positive-trial.json`.
Source and documentation references below use
`672374c38b2b728719510300ced1090f1e0e35ef` unless another revision is named.
The work was read-only apart from this record and `rca.json`: no new runtime
probe, test, native-platform research, repair or register adjudication. This is
not pass 6. Historical records remain unchanged.

All four clauses now have a disposition. The historical author's private
motivation is not established; the decisions rest on the present passages,
their source facts and the bounded evidence examined.

| Job / unit | Disposition | Final candidate |
| --- | --- | --- |
| Q01 / N164 | Positive rewrite with local evidence-scope repair | S18 `Sandbox-gated`: `Source-only; mapped before compilation` |
| Q02 / N203 | Elide the unspecified qualifier | S28 `Reaches exec children`: `Inherited sandbox constraints` |
| Q03 / N266 | Elide the erasure qualifier after R01 | N9a `Release / teardown action`: `Return or process exit` |
| Q03 / N270 | Elide the erasure qualifier after R01 | N9b `Release / teardown action`: `Return or process exit` |

## Provenance correction

The prior triage correctly located the manifest entries at pass 2, but their
wording already existed in the pass-1 inventory. Git pickaxe and direct reads
locate all four at `90fcb1b9a1e48a1e41725e9faca3095297ee493c`,
`docs/WORKER-INST-DOC-PLAN.md`: S18 line 295, S28 line 306, N9a/N9b lines
329–330. The earlier seed at `a5f6823` has none of these clauses. Pass 2
`83f61f35a96d295f2a2a94aa29740664ec2971f6` transferred the inventory into the
manifest and removed its old table. This establishes an earlier written origin,
not the author's reason for each phrase.

## Q01: mapping identity and size

**Retained evidence inspected.** The credited run is
`tests/out/runs/worker-p1-launch-final`, run ID
`20261017T215334Z_b7815087`. It is gitignored local evidence, retained in
`tests/RETAINED.json`; it is not portable with this record. Its production source
is `6fd44fb15397678d29f0f96bfee2b1abbe4bbbb6`, build 692,
`v0.3.1-8-g6fd44fb`, worker identity
`33890392b9337f128a06b89b7d831192e5e8d809f0a5f41613e8745c2d9c9eb9`.
The run used a working-tree observer whose exact snapshot is retained. The
retention index's null `source` is therefore not replaced with the later
inventory commit.

Read both `suites/runner_exec_inheritance/launch_inventory/artifacts/`
boundary directories (`pre_ready`, `post_apply`): full `observations.json`,
`mappings.stdout` and `descriptors.stdout`; also read the retained
`pass1-evidence/source-snapshot/tests/suites/runner_exec_inheritance/launch_inventory.py`,
`source-scope.json`, the provenance/manifest metadata, and the plan's launch
ledger and row 11. The source-scope hashes for the observer, worker source,
capture source, provenance and manifest match. The two native source snapshots
also match production commit `6fd44fb`. `rca.json` records exact hashes of the
six raw observation files and these provenance checks.

| Boundary | Worker / host | `lsof` fd 3 (line 8) | `vmmap` unnamed writable shared region |
| --- | --- | --- | --- |
| pre-ready | 38775 / 38774 | PSXSHM, size 3686400, `/pw_cw_38774` | line 197: `105bbc000-105f40000`, `3600K`, `rw-/rw-`, `SM=SHM` |
| post-apply | 38829 / 38828 | PSXSHM, size 3686400, `/pw_cw_38828` | line 191: `10232c000-1026b0000`, `3600K`, `rw-/rw-`, `SM=SHM` |

Both mapping observers returned zero. Each report also has two read-only
shared-memory regions. The writable region size equals the named descriptor's
object size. That supplies a concrete opportunity to infer that this particular
region is S18. The `vmmap` row supplies no backing-object name or identifier
linking it to the descriptor. The observer retains raw streams and command
statuses; it never parses a region or makes that association. No mistaken
attribution was found in the inspected observer, JSON or plan interpretation.
The matching sizes demonstrate a possible reader inference, not an observed
reader mistake and not proof of why the author wrote the warning.

The two captures are different workers. They cannot establish within-process
mapping changes by subtraction. The plan already states this at lines 595–608
and 1457–1466. Row 19's later fixture `mach_vm_region` measurements concern
teardown of known host/issuer mapping ranges; they are separate evidence and
do not identify S18 in L (`docs/WORKER-INST-DOC-PLAN.md:830–861,1150–1165`).

**Post-RCA comparison.** Simply deleting the size caution while retaining
`L shared mappings observed` inside S18 leaves the questionable resource-level
credit intact. The trial's positive mapping-call sentence alone also leaves
that credit intact if the L cell remains. Prefer replacing the whole S18 cell
with `Source-only; mapped before compilation`. `map_region`'s `fstat` and shared
`mmap`, source order, lifetime, publication role and citation remain. S16f
already retains `L vmmap inventory; per-allocation origin and gating unknown`,
and the ambient-context prose retains the observation and its bound. This
removes the local invitation to attribute an unnamed region while preserving
the raw observation in the account where it belongs.

**Completion.** The named retained artifacts exist and the bounded search is
complete. Exact VM-to-object identity remains unmeasured, but no further
measurement is needed for this source-only row. The source reference is
`controller/tools/pw_probe_runner/pw_probe_runner.c:563–583`; the two affected
inventory locations are `docs/WORKER.md:108,110`.

## Q02: “exact child policy effects”

**Search and concrete distinctions.** Read S28's seed, its pass-1 row and
pass-2 transfer; the plan's column contract; WORKER's starting-authority and
exec sections; the guide's helper/augment account; `runner/augments/README.md`;
and the exec-fixture, exec-inheritance, exec-DAC and run-effects suite accounts.
The relevant present facts are:

- The column asks what reaches exec children and by which inheritance rule
  (`docs/WORKER-INST-DOC-PLAN.md:219`). S28 names inherited sandbox constraints.
  The worker applies the specimen before entering its phase/attempt loop
  (`pw_probe_runner.c:1885–1914`).
- Applying SBPL restricts the worker's starting authority; an augment changes
  the submitted policy before compilation (`docs/WORKER.md:273–282`;
  `runner/augments/README.md:3–8,41–72`). These facts do not equate parent and
  child effective access.
- The guide assigns the helper's operation evidence to the helper
  (`docs/PolicyWitness.md:96`). WORKER separately states the selected child
  descriptors, environment, group, native spawn and child-exit observations
  (`docs/WORKER.md:380–389`). The inheritance suite describes its environment
  and descriptor measurements, while `run_effects/README.md:27–30` describes
  a specific child file-effect control. These are distinct, bounded accounts;
  no fresh results from those cases are credited here.

No inspected passage gives “exact child policy effects” a defined meaning,
claims parent/child effective-access equivalence, or promises an exhaustive
helper-operation inventory. The two candidate readings—identical effective
access, or every helper operation—are possible overreadings, not demonstrated
upstream claims or recovered author intent. The inherited-constraints fact is
an existing retained assertion; this RCA does not re-prove every native
inheritance rule or expand it into a permission guarantee.

**Post-RCA comparison and completion.** Prefer the elision trial:
`Inherited sandbox constraints`. The longer positive trial repeats the
apply-before-exec order already supplied by the row's acquisition/timing and
the source narrative. The deleted clause supplies an undefined coverage
qualification, with no identified separate useful proposition in this bounded
search. Its loss is acceptable for the inheritance column's stated purpose.
Leave the actual child-state, helper-evidence and native-result boundaries
intact. No named evidence item is missing; no platform investigation is needed
to decide this editorial scope.

## Q03: temporary-frame byte erasure

**Why these rows exist.** The pass-1 completeness audit explicitly introduced
N8–N11 to retain call-frame and capture hash/sorting storage in the resource
inventory (`90fcb1b:docs/WORKER-INST-DOC-PLAN.md:708–713`; current plan
lines 1403–1408). It distinguishes reused storage views from separately
acquired mappings. It does not identify a confidentiality or erasure
requirement for either N9 row.

**N266 / N9a ownership.** Read `parse_args`, `map_region`,
`read_all_from_fd`, `pw_timing_setup` and `prepare_extension` in the worker
source (`416–560`, `563–583`, `587–611`, `262–291`, `1268–1352`). Their
automatic working values include argument pointers/counts, metadata, a mapping
pointer, timebase/status values, and the extra byte used by the policy-overflow
check. Policy input normally goes into static `policy_buf` (`1703–1705`);
accepted token bytes are inspected in the separate shared channel, whose view
is held in `extension_channel`. The rejection erase targets that channel's
token array (`1338`), not the automatic call frame. This is a source ownership
description, not a claim that every local byte is nonsensitive or that native
callees make no copies.

**N270 / N9b ownership.** Read `pw_profile_capture.h:24–90`. Automatic
objects include a little-endian word buffer, pair digests, SHA contexts, a
copied-byte count and a compiler-profile view holding metadata/pointers.
`main` passes the S18 capture destination (`pw_probe_runner.c:1840–1845`);
the bytecode copy goes there, not into a whole-bytecode automatic buffer.
Hashing reads source/parameter data; native CommonCrypto and sorting behavior
remain under the row's existing unobserved-internals qualification. The
compiler's returned object, static parameter snapshot and published capture
are separately inventoried. No disposal or confidentiality claim for those
resources follows from returning out of these frames.

**Erasure requirements inspected.** The plan's rows 8, 14 and 18, WORKER's
extension section (`434–456`), and the native-extension evidence contract
(`tests/FAILURE-PROPAGATION-CONTRACT.md:183–205`) concern the issuer allocation,
PW-owned token-channel views, explicit erasure sites/early exits and native
private copies. `pw_extension_erase` uses volatile stores over its supplied
range (`pw_extension_channel.h:32–35`). None of these inspected requirements
applies a whole-frame wipe obligation to N9a or N9b. No frame-erasure observer,
claim of a completed wipe, or requirement for erasing these frames was found.
That is the result of this named search, not proof that no possible security
question could ever concern their remaining bytes.

**Post-RCA comparison and completion.** R01's `Release / teardown action`
heading resolves the relevant local wording ambiguity: `Return or process exit`
records the lifetime-ending event, rather than suggesting a verified disposal
outcome. The expanded positive trial states the same frame-lifetime fact at
greater length. Prefer concise elision for **each** unit: N266 and N270 both
become `Return or process exit` under that heading. With the separate token,
private-state and lifetime facts retained, neither original clause adds an
identified requirement to the passage. The header change alone does not
establish the absence of an erasure obligation; the ownership/requirement
review supplies that editorial basis. No new wipe, byte-retention guarantee,
native confidentiality guarantee or runtime evidence is introduced.
