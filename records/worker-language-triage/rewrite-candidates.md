# Concrete WORKER-only rewrite candidates

Frozen revision: `5f878fe0603b039ef1edf3119d448b65534e2e18`. Drafts only; nothing below has been applied.

Generated edits name their owning inputs. Preserve all factual context specified below, every settled/pending guard, and all A1 facts. Other documents are read-only. No new call-site completeness enforcement or behavioral claim is introduced. Reflow surrounding whitespace after deleting a selected prose span.

## R01 — Name requested cleanup as an action

Guard units: N004, N239.

Released can look like an achieved outcome. State the kind of information in the heading itself; keep every recorded return/failure and actual lifetime fact.

**Owner:** docs/architecture.json.

**Selector:** `worker_capabilities.node_facts and every worker node facts key named Released`.

**Before:**

```text
Released
```

**After:**

```text
Release / teardown action
```

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:55–56 at 5f878fe

```text
Cleanup entries name calls; retained
native returns establish their observed outcomes where available.
```

**After:**

```text
(remove this selected text/object; preserve surrounding context)
```

**Owner:** docs/architecture.json.

**Selector:** `graphs[id=worker_capabilities].items[id=s36b].facts[Released]`.

**Before:**

```text
Conditional group kill request, not an absence proof
```

**After:**

```text
Conditional process-group kill request
```

**Preserved:** All cleanup calls, retained results, ignored-return descriptions, process-exit/reference lifetimes, group lifetime and escaped-descendant facts remain. Rows 10/19 are not resolved by this repair.

**Read with the guard absent:** Reading a request under Release / teardown action supplies no completed-cleanup result. The group row still says members may remain beyond the attempt/worker; no absence of descendants follows.

**Validation at implementation:** Rename the owning key and node_facts declaration together; regenerate the worker table/map and check that every value except the named s36b edit survives. Review every cleanup-result cell for lost outcome data.

## R02 — Describe cited definitions precisely

Guard units: N005, N057.

Remove the presentation-level suggestion that a named check verifies the whole resource row. State the actual mechanical operation in the caption and label the cited definitions as such.

**Owner:** docs/generate_architecture.py:render_region, worker_capabilities output only.

**Selector:** `WORKER caption, details summary, node/edge check-column labels`.

**Before:**

```text
Shared caption pairs implementing source/checks, followed by the assertion-coverage disclaimer; column label Checks.
```

**After:**

```text
WORKER caption text after the figure/manifest/generator links: "Figure IDs correspond to the table IDs. Each row lists source references and cited test or rule definitions. The generator checks source-symbol presence and resolves those definitions." Details summary: "Worker capabilities: {node_count} nodes and {edge_count} edges; source symbols and cited definitions checked". Node/edge column label: "Cited check definitions". Counts remain generated.
```

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:238–240 at 5f878fe

```text
checks publication
under its bare-deny and full-region cases; that assertion scope belongs beside
the source account of preparation.
```

**After:**

```text
checks publication
under its bare-deny and full-region cases.
```

**Preserved:** Every source/check citation, every per-resource evidence qualifier, G10, generator_common.py guidance, and N053 source/assertion/execution distinction remain. Existing row-25 citation-ownership findings remain unresolved.

**Read with the guard absent:** A definition-resolution caption and Cited check definitions header describe locating definitions. They contain no assertion that a test ran or proved the row. The specific publication cases remain named in prose.

**Validation at implementation:** Use worker-specific rendering; compare every other generated document and figure byte-for-byte. Preserve G10 and the shared verification logic. Review the complete caption and table together; no new assertion-coverage or call-site-completeness enforcement is introduced.

## R03 — State launch and fixture conditions at the observation

Guard units: N019, N122.

Name the production case and deliberate descriptor intervention before describing their outcomes, so the reader has the actual configuration rather than an ordinary-launch generalization to retract.

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:293–295 at 5f878fe

```text
The recorded launch observation found matching
plain and environment-displaying process output, inherited null-device standard
output/error, and the expected protocol endpoints.
```

**After:**

```text
The recorded production launch case used an empty allow-default specimen.
Its observation found matching plain and environment-displaying process output,
inherited null-device standard output/error, and the expected protocol endpoints.
```

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:329–330 at 5f878fe

```text
With stdin closed
in the low-descriptor control, evidence is allocated at fd 0.
```

**After:**

```text
The low-descriptor fixture deliberately closes stdin and low unused
descriptors before exercising launch setup. In that configuration, evidence is
allocated at fd 0.
```

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:335–336 at 5f878fe

```text
These controlled launches do not establish that an ordinary XPC
host starts with the same descriptor arrangement.
```

**After:**

```text
(remove this selected text/object; preserve surrounding context)
```

**Owner:** docs/architecture.json.

**Selector:** `graphs[id=worker_capabilities].items[id=s14a].facts[Sandbox-gated]`.

**Before:**

```text
L presence only; no universal stdio rule
```

**After:**

```text
L: inherited null-device stdout/stderr observed
```

**Preserved:** Both ordinary and contaminated launch observations, the exact fd collision and missing-ready-endpoint outcomes, and the Known gap census remain. No universal launch invariant or additional observation is added.

**Read with the guard absent:** An ordinary host with stdin open has not been described by the deliberately modified fixture setup. The stdio cell is explicitly an L observation under the case named in prose.

**Validation at implementation:** Cross-check the fixture setup description and the retained L configuration; retain source facts about inheritance independently of the two observations.

## R04 — Name adapter calls instead of general native uses

Guard units: N017.

The actual control-flow observation is through fixture adapters. Naming their concrete action removes the broader libc-behavior premise.

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:325–327 at 5f878fe

```text
Failed handle initialization reaches later uses of the
invalid handle; fixture adapters contain those uses, so the controls establish
continued host flow without claiming libc's behavior on that input.
```

**After:**

```text
After a failed handle initialization, the fixture adapters record subsequent
invalid-handle uses and return EINVAL. Their receipts record the host control
flow through those adapter calls.
```

**Preserved:** Unchecked production setup and the other actual failure-flow observations remain. Fixture containment remains explicit. This does not close the reopened setup-verification finding.

**Read with the guard absent:** The described EINVAL comes from an adapter whose calls are named. Reading the paragraph supplies an adapter receipt, not an observed libc call on that invalid handle.

**Validation at implementation:** Match the fixture contract at its invalid-handle boundary; retain the existing link to host setup controls and its fixture contract.

## R05 — Name the source of attempt status

Guard units: N025, N216.

Replace high-level success phrasing with the operation whose return determines attempt status; preserve independent filesystem observations beside it.

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:353–353 at 5f878fe

```text
Opens read-only, attempts a one-byte read and close, and discards those latter returns. Published success is the open result, with an available descriptor-path observation.
```

**After:**

```text
Opens read-only. The open result determines the published attempt status. On successful open, records an available descriptor-path observation, attempts a one-byte read and close, and discards those latter returns.
```

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:354–354 at 5f878fe

```text
Opens with `O_WRONLY \| O_TRUNC`, then attempts to write `x` and close. Published success is the open result; the write and close returns are discarded.
```

**After:**

```text
Opens with `O_WRONLY \| O_TRUNC`. The open result determines the published attempt status. On successful open, attempts to write `x` and close and discards their returns.
```

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:361–363 at 5f878fe

```text
The source
establishes where each call occurs and which returns are discarded; those are
separate from an independently observed filesystem effect.
```

**After:**

```text
(remove this selected text/object; preserve surrounding context)
```

**Owner:** docs/architecture.json.

**Selector:** `graphs[id=worker_capabilities].items[id=s31b].facts[Sandbox-gated]`.

**Before:**

```text
Source-only; creation not implied for existing target
```

**After:**

```text
Source-only; conditional new-object acquisition at open(O_CREAT)
```

**Preserved:** Native operations, status transformation, discarded returns, existing-target/no-truncation behavior, source-only evidence and the existing-file byte/identity control remain. Attempt status is not relabeled as a raw syscall return.

**Read with the guard absent:** An open can determine attempt status while a later write fails; the draft explicitly discards the write return. Existing-target behavior is still stated in the create row, and S31b is expressly conditional.

**Validation at implementation:** Review against the original action table and the attempt-channel contract. Retain every operation and returned/discarded-status distinction; no new filesystem-effect observation is claimed.

## R06 — Use the concrete publication counterexample once

Guard units: N051.

The positive create-then-kill observation already supplies the counterexample. Make the event separation explicit at its introduction and remove the duplicate negative counterfactual from the later change table.

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:466–466 at 5f878fe

```text
A native call and publication are distinct boundaries.
```

**After:**

```text
A native call can complete before the worker publishes the attempt slot.
```

**Owner:** docs/WORKER.md authored prose.

**Before:** docs/WORKER.md:510–510 at 5f878fe

```text
| Move reply assembly into the worker or use missing publication as proof of no effect | Couples reporting to specimen-controlled communication or substitutes absence of evidence |
```

**After:**

```text
| Move reply assembly into the worker | Couples reporting to specimen-controlled communication |
```

**Preserved:** N042, the independently observed created file with withheld result, payload eligibility, the evidence-contract link, and the reply-assembly design example remain.

**Read with the guard absent:** The reader sees a completed native effect followed by an unpublished result in a concrete case. That fact defeats the absent-publication inference without repeating it as a prohibited conclusion in the change table.

**Validation at implementation:** Read the complete native-observation section with the shortened table row. Preserve both sides of the independent counterexample and its control citation.

## R07 — Remove the unsupported object-identity edge

Guard units: N299.

The x3-to-s31b observation arrow visually associates later pathname metadata with the newly created object. W53 already carries the supported relation: attaching later path observations to the host record.

**Owner:** docs/architecture.json.

**Selector:** `worker_capabilities.edges[id=W50]`.

**Before:**

```text
{
  "id": "W50",
  "from": "x3",
  "to": "s31b",
  "kind": "observes",
  "label": "Later host path inspection may observe file effect",
  "sources": [
    {
      "path": "runner/Sources/PWRunnerCore/PWRunnerService.swift",
      "symbol": "enrichPathDiagnostics"
    }
  ],
  "checks": [
    {
      "path": "tests/suites/witness_contract/opt_in/path_query_integrated.sh",
      "symbol": "path_query_integrated",
      "form": "test"
    }
  ]
}
```

**After:**

```text
(remove this selected text/object; preserve surrounding context)
```

**Owner:** docs/architecture.json.

**Selector:** `worker_capabilities.nodes[id=x3].note`.

**Before:**

```text
Path spelling alone is not object identity
```

**After:**

```text
(remove this selected text/object; preserve surrounding context)
```

**Owner:** docs/architecture.json.

**Selector:** `worker_capabilities.edges[id=W53].label`.

**Before:**

```text
Host attaches later path observations
```

**After:**

```text
Host attaches later target-path metadata
```

**Preserved:** Keep S31b, all worker acquisition/effect edges, X3 and its source/check citations, W53 and the externally observed metadata. The independent create-effect control is unchanged. No resource is removed.

**Read with the guard absent:** If a pathname resolves to a replacement object before host inspection, the repaired graph still says exactly what occurred: later target-path metadata was attached. It draws no identity relationship to the worker-created object.

**Validation at implementation:** Regenerate the worker figure/table and inspect the complete graph: X3 joins the host record through W53; it no longer observes S31b. Confirm the worker-created resource/effect account and all other documents remain intact.

## Common implementation boundary

Render all destinations through the existing generator, then verify that only WORKER.md and worker-capabilities DOT/SVG changed. Generated captions/header labels specific to WORKER require worker-specific rendering; keep shared helper rules and other tour captions intact. Use a fresh managed output directory for source_drift/architecture_documentation. These commands are future implementation checks, not tests run by this triage.

The repair IDs are not register adjudications. Existing open/reopened findings, especially citation ownership and setup/descendant verification, retain their current state. No package closes them.
