# Documentary origins and current inference bases

Historical introduction, documented motivation and present reader premise are separate kinds of evidence. A cited external contract supplies a current meaning; it does not by itself establish historical causation. No external document is proposed for editing.

## O01 — Evidence-basis annotations

The plan explicitly requires per-resource observed/source-only/unknown scope. The generated qualifiers entered with the pass-2 graph in 83f61f3. They record how a claim is supported, rather than documenting a particular reader error. This establishes documentary provenance and a current purpose; it does not establish private author intent.

docs/WORKER-INST-DOC-PLAN.md:100–100 at 5f878fe

```text
Mark source-only conclusions as such.
```

docs/WORKER-INST-DOC-PLAN.md:208–208 at 5f878fe

```text
| Sandbox-gated | Observed (cite the case), source-only, or unknown |
```

docs/WORKER-INST-DOC-PLAN.md:1454–1456 at 5f878fe

```text
No ordinary file, Mach, extension, mutation-barrier or allocation
case was freshly executed for this pass. Source-only conclusions and inspected
checkers above are not credited as live observations.
```

## O02 — Bounded launch observation

Row 11 and the launch-inventory contract identify what L observed and what it could not inspect. A complete starting-authority census was explicitly declined. These are settled observation boundaries; identifying the inference does not require completing the missing census.

docs/WORKER-INST-DOC-PLAN.md:596–598 at 5f878fe

```text
The
pre-ready and post-apply specimens use distinct workers, so VM address or size
differences are not within-process changes. No subtraction of them is claimed.
```

tests/suites/runner_exec_inheritance/README.md:78–79 at 5f878fe

```text
Signal state, resource limits and extension-bearing workers remain
outside this observation.
```

docs/WORKER-INST-DOC-PLAN.md:600–600 at 5f878fe

```text
Adjudication: Explain the measured starting substrate and accept the explicitly bounded observation as a Known gap. No new isolation guarantee or runtime change is authorized.
```

## O03 — Published source versus installed native internals

Row 6 traced and rejected blanket allocation claims. The pinned published sources are not an authenticated reconstruction of the installed libraries, and no allocation probe was credited. Retaining that distinction preserves useful source findings without promoting them to runtime observations.

docs/WORKER-INST-DOC-PLAN.md:456–459 at 5f878fe

```text
These are published-source conclusions, not a match of
Apple's source release to every instruction in the installed shared cache;
allocator, locale, lazy binding and private extension internals remain
unobserved.
```

docs/WORKER-INST-DOC-PLAN.md:224–227 at 5f878fe

```text
Call-site completeness does not reach library internals, such as what
`sandbox_compile_string`, the extension routines or libc formatting allocate.
Record the call and mark its internal behavior unobserved, unless a source or
probe establishes it.
```

## O04 — Private extension state and identity

The limitation originated in the extension account in 1f7abc0 and moved to WORKER in pass 3 under row 8. Its present basis includes native results versus access observations, PW-buffer erasure versus private copies, and preparation-time target identity versus later opens. These origins explain the boundaries; they do not authorize changes to other documents or reopen the accepted limitation.

docs/ARCHITECTURE.md:515–518 at 1f7abc0

```text
Known gap: private extension calls may allocate or retain internal state that PW
cannot inspect. Erasure observations cover PW-owned transient buffers; successful
native results and phase progress do not establish kernel extension state,
stable identity, effective permissions or access revocation.
```

docs/WORKER-INST-DOC-PLAN.md:506–509 at 5f878fe

```text
The existing architecture paragraph separates PW buffer erasure from
private allocation/retention, kernel state, identity, permissions and
revocation. Existing adjudication remains: move ownership to WORKER.md in
pass 3 and link from ARCHITECTURE.
```

tests/FAILURE-PROPAGATION-CONTRACT.md:188–190 at 5f878fe

```text
Resolution
and metadata are host observations before issuance; neither establishes that a
later open reached the same object.
```

tests/FAILURE-PROPAGATION-CONTRACT.md:203–205 at 5f878fe

```text
`host_buffer_erased`
records clearing the host's mapping, not proof that every process or native
library has erased every copy.
```

docs/WORKER-INST-DOC-PLAN.md:534–534 at 5f878fe

```text
Adjudication: Retain the accepted private-API limitation under row 8 and explain the observed after-release read with its allowed outcomes. No universal revocation claim or native API change is authorized.
```

## O05 — Compiled-profile ownership overclaim

Row 16 records the actual rejected sentence: retaining a pointer until exit was being expanded into an allocation-lifetime claim. The current guard marks the opaque apply boundary. Native ownership research is required before a future free, not before settling the editorial value of this boundary.

docs/WORKER-INST-DOC-PLAN.md:719–723 at 5f878fe

```text
**Row 16.** First candidate: “The compiled profile is retained until worker
exit.” That allocation-lifetime sentence exceeds the visible source:
`sandbox_apply` is private and may have ownership behavior not established
here. What PW itself does is keep the returned pointer, optionally read the
profile, call apply and make no explicit free call.
```

## O06 — Spawn observation versus helper outcome

The public exec account explicitly separates spawn, child disposition and helper-supplied evidence. This is a present external basis for the D2 distinction, not a claim that the guide caused the WORKER sentence.

docs/PolicyWitness.md:96–96 at 5f878fe

```text
The helper must supply evidence about its internal operation; PW does not turn that evidence into a record for that operation, and a successful spawn can coexist with a failed exec result.
```

## O07 — Native completion versus publication

The document supplies a concrete independent counterexample: the file exists while its result is withheld. Preserve that positive account and payload-admission rule. It can support removing the duplicate negative counterfactual from the change-examples table.

docs/WORKER.md:473–475 at 5f878fe

```text
independently observes the created file while requiring the reply to withhold
the unpublished result. Partially written payload remains outside the evidence
the host is entitled to decode.
```

## O08 — Ordering versus conditions at execution

The release hold orders query collection before an action batch. The current guide expressly identifies earlier actions changing later conditions. This distinguishes temporal order from a shared state snapshot; it is a useful instrument limit even with precise ordering vocabulary.

docs/PolicyWitness.md:124–124 at 5f878fe

```text
Earlier actions in the phase, including consumption or release, can change what a later attempt encounters. Use another phase for a new query collection; neither interval is a common state snapshot.
```

## O09 — Citation machinery and assertion coverage

The renderer labels a column Checks and associates each row with implementing sources/checks, while the helper and G10 explicitly limit mechanical verification to definitions. A WORKER-specific caption/header repair can narrow that presentation. The shared helper comment and G10 remain settled rules for all their consumers.

docs/generator_common.py:3–3 at 5f878fe

```text
A definition is a place to look, never evidence that a test asserts a claim.
```

tests/suites/source_drift/README.md:155–158 at 5f878fe

```text
- **G10. Captions state the verified guarantee.** A generated caption or
  summary says what the generator verified about citations, presence and
  definition, and nothing stronger; it never says a test exercises, covers or
  proves a row.
```

docs/generate_architecture.py:380–380 at 5f878fe

```text
parts.append(_table(["Id", "Node", "Kind", *columns, "Sources", "Checks", "Limits"], rows))
```

## O10 — Explicit fixture intervention

The fixture contract identifies both deliberate low-descriptor setup and containment of invalid native handles. These are concrete conditions that WORKER can state directly, allowing its two generalization disclaimers to go after repair.

tests/fixtures/host_setup/README.md:12–14 at 5f878fe

```text
The collision case closes stdin and low unused descriptors;
the checker requires the actual source/destination overlap and the child's wrong
evidence endpoint, not merely a low-descriptor label.
```

tests/fixtures/host_setup/README.md:27–29 at 5f878fe

```text
A failed handle initialization leaves nil. Subsequent adapter calls record the
invalid use and return EINVAL instead of passing nil into libc; an attempted
spawn with such a handle is likewise contained.
```

## O11 — Selected graph and resource-role account

The worker graph is an explicitly authored set of resource relationships, and its white/mixed resources have positive multiple-role descriptions. The selection legend and mixed-role account help read that representation. Neither needs an inference RCA to remain useful.

docs/WORKER.md:45–45 at 5f878fe

```text
The edges select relationships among the inventoried resources.
```

docs/WORKER.md:32–33 at 5f878fe

```text
White nodes have multiple roles or form the ambient
execution substrate:
```

docs/generate_architecture.py:289–290 at 5f878fe

```text
for edge in graph["edges"]:
        attrs = dict(styles["edge_kinds"][edge["kind"]])
```

## O12 — File status and later pathname observations

WORKER determines open_read/open_write attempt status from open and separately describes later host pathname observations. W50 points that later observation at the newly created object, while W53 already preserves the supported attachment of later observations. Local labels and that edge can be repaired without inventing object identity or changing another document.

docs/WORKER.md:354–354 at 5f878fe

```text
Published success is the open result; the write and close returns are discarded.
```

docs/WORKER.md:209–209 at 5f878fe

```text
Later host path inspection may observe file effect
```

docs/WORKER.md:212–212 at 5f878fe

```text
Host attaches later path observations
```

docs/PolicyWitness.md:104–104 at 5f878fe

```text
or that a path named the same object both times
```

## O13 — Causal attribution and compiler receipt boundaries

The repository witness principle and the worker tour distinguish native records, external correlation and pre-apply receipt capture. Their meaning survives any concise local label: association remains useful precisely with its causal boundary, and a compiler receipt remains useful with its application boundary.

AGENTS.md:33–33 at 5f878fe

```text
**No dishonest attribution**: never turn a permission-shaped failure into a sandbox-cause claim without supporting evidence, or claim agreement or disagreement between prediction and enforcement.
```

docs/WORKER.md:154–154 at 5f878fe

```text
Capture before apply; host decode after publication
```

docs/WORKER.md:214–214 at 5f878fe

```text
Controller associates external log candidates with run evidence
```

## O14 — Unresolved specific inference behind three cautions

Git pickaxe located these phrases at the pass-2 graph introduction, but neither that insertion nor the targeted plan/contract reads identify the specific rationale for size-based object attribution, the undefined scope of exact child policy effects, or byte-erasure caveats on temporary frames. The RCA briefs distinguish plausible motivations from established provenance.

docs/architecture.json:7574–7574 at 83f61f3

```text
"Sandbox-gated": "L shared mappings observed; no mapping-identity attribution from size alone"
```

docs/architecture.json:7894–7894 at 83f61f3

```text
"Reaches exec children": "Inherited sandbox constraints; exact child policy effects not inventoried here"
```

docs/architecture.json:8588–8588 at 83f61f3

```text
"Released": "Return or process exit; no claim of byte erasure"
```
