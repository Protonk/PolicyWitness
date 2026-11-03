# Documentation scouting for integrated sandbox-extension witnessing

Source review supporting the
[sandbox-extension witnessing plan](../../SANDBOX-EXTENSION-WITNESSING-PLAN.md).
This record maps where the plan changes what the repository documents, when
each document can change relative to the plan's stages and integration
boundary, and how the documentation machinery constrains the edits. It
complements the test scouting inventory; the associated plan is the inbound
link owner for both records. Section 5 maps the documentation work to the
associated plan; this record is a source survey, not the current behavior contract.

- Examined revision: `10cff848053030a879980d8649d43b7ac16fc523` ("Integrate
  extension test scouting into implementation gates").
- Method: read the plan's documentation requirements against the current
  documents, the limits, architecture, contract, build and identity generators,
  source-drift rules, records conventions and guide staging implementation.
  Counts and quoted phrases describe that revision; inspecting staging code
  is not verification of a built or shipped guide.
- No generators, builds or tests were run for this review. Quoted phrases are
  search anchors; verify each against the candidate before editing.

The plan's [Documentation and completion](../../SANDBOX-EXTENSION-WITNESSING-PLAN.md#documentation-and-completion)
section names the documents to update. This record adds what each one
currently asserts that the plan contradicts, which assertions are held by a
generator or a drift rule rather than by prose, and the order those holds
impose. The architecture and worker tours get the most detail because they
describe the worker/runner relationship the plan changes.

## 1. How documentation is held in this repository

Four mechanisms affect ownership and verification of documentation edits. The
plan's work touches all four; they do not impose a commit-by-commit chronology.

| Mechanism | Owner | What it fixes | Consequence for this plan |
| --- | --- | --- | --- |
| Generated regions and spans | [generate_limits.py](../../docs/generate_limits.py), [generate_architecture.py](../../docs/generate_architecture.py), [generate_contract.py](../../docs/generate_contract.py), [generate_worker_identity.py](../../docs/generate_worker_identity.py) | Limits tables, guide copies, architecture figures/tables, version sentences, identity bytes and registered scalar spans | Edit manifest-owned facts at their source and regenerate affected outputs with the implementation. Identity is derived from source/build inputs, not a hand-authored manifest. Freshness checks do not discover every new bound or process automatically. Do not defer these coupled updates to stage 4. |
| Citation forms | [generator_common.py](../../docs/generator_common.py); [generator contracts](../../tests/suites/source_drift/README.md#generator-contracts) G4 and G5 | Source presence and check definitions/forms; assertion scope on worker-capability citations | Required citations must resolve when checked. Implementation, test definitions, manifest rows and figures may arrive in one change. Worker-capability rows may explicitly have source-only support; other graph rows and limits require test/rule citations. Definition checks do not establish relevance, execution or passing coverage. |
| Prose drift rules | [check.py](../../tests/suites/source_drift/check.py) and [generators.py](../../tests/suites/source_drift/generators.py) | Known-gap indexes, evidence-channel paths, seam table, CLI block, coverage matrices, suite table, G9 values, G11 symbol links and local links | Use spans for manifest-owned scalar claims. G9 mechanically finds selected duration/size/step patterns, not every number; other counts need review. Architecture landing paths must resolve in shape goldens, and seam/suite changes need their corresponding accounts in the same valid tree. |
| Standalone guide staging | `--stage-guide` in [build.sh](../../build.sh); `validate_guide` and `require_standalone` in [generate_limits.py](../../docs/generate_limits.py) | The shipped [PolicyWitness.md](../../docs/PolicyWitness.md) supplies its copied coverage without companion files; copies permit specified heading/link transformations | Copy extension coverage into the guide and rebase the FAQ link. Status/reading blocks have verbatim ownership; questions/limits already have controlled transformations. Copied blocks generally require internal links, with a narrow historical-question exception. The whole guide may contain ordinary external links; that does not make sibling coverage a valid dependency. |

Two further rules shape the writing itself. The root guidance's
[wording rule](../../AGENTS.md#wording) asks for literal descriptions of
operations; use the plan's technical terms with their defined meanings. The
[records rules](../AGENTS.md) permit inbound links to this record only from
the plan; permanent documentation must not cite it.

## 2. Where the documents change

### 2.1 Architecture tour

[ARCHITECTURE.md](../../docs/ARCHITECTURE.md) has four generated figure
regions (topology, boundaries, documents, BYOXPC) and hand-written prose
between them. The generated tables come from
[architecture.json](../../docs/architecture.json); the prose is edited in
place and parsed by two drift rules.

| Section | Current assertion the plan contradicts or extends | Required change and holder |
| --- | --- | --- |
| Why these processes exist | "PolicyWitness spawns one worker per specimen"; "The issuer is separate so native issuance occurs before worker creation"; "Only the worker (compile/apply and consume/release), the issuer (file issuance), the validator ... call native sandbox APIs" | One fresh worker per actor; issuance inside an actor after (or without) application; the worker's native API list gains issue. The issuer paragraph becomes the legacy-declaration path. Host invariance (no sandbox API in the host) is unchanged and still holds custody code to that rule through `check_host_invariance`. |
| Process topology (generated) | Worker node Lifetime "one specimen; one application and all ordered phases"; Native sandbox API column lists consume and release; issuer node Lifetime "one declaration before worker creation"; edge T5 "optional fd 5 transient token channel"; notes T13/T14 | Manifest edits: worker lifetime per actor with parked waits; add issue to the worker's native API fact; issuer scoped to old declarations; new edges for host custody mailboxes and recipient delivery (the plan's separate custody/delivery/evidence channels). Each new node or edge needs a source symbol and a defined check (G4, G5), and durations only through limit placeholders (G8). |
| One run in time | "all phases use one worker and one policy application"; the issuer diagram runs "before worker creation"; the stage list pins "Extension preparation and issuer lifetime" to `ExtensionSession` | Add an actor-schedule timeline (A issues, host custody, transfer to B, B consumes and re-issues, C consumes, serial phase visits with parked actors) beside the legacy one; add stage bullets for actor session factoring, custody, transfer acceptance and per-actor barriers, each citing its control. The barrier paragraph's "order-barrier mutation control" reference must name both drivers once the actor driver exists. |
| Budgets paragraph | Describes issuer wait, policy transfer, ready, sentinel, proceed, collection and exec budgets for one worker | Add actor setup, schedule, exchange and lifetime accounting, with owned values through spans. Parked waits spend the cutoff, not a new release allowance at spawn. Identify the profile as provisional during development; accepted documentation must state the measured scope of qualification rather than assume it. |
| Evidence channels and ownership | Table rows for Extension preparation/issuance (`extensions[]`), Native lifecycle (`extension_events[]`), Fresh read | Add issue, delivery, custody and per-actor disposition landing paths with the stage 3 goldens. `check_evidence_channel_paths` requires those paths to exist when checked, not in an earlier commit. Keep each native result's actor writer distinct from host custody and recipient acknowledgement. |
| Boundaries (generated) | Nodes `extension_preparation` and `token_channel`; edges B13 to B16 describe one declaration, one channel, one consume/release | Add nodes for actor plan normalization, custody store and recipient mailbox; add guards for transfer acceptance, reference lifecycle and per-actor identity. B13's Limits column cites the legacy admission limits; the actor form cites its own limit ids. |
| How the system verifies itself | Lists goldens, generators, drift rules, consumer, test controls, C harness, lifecycle oracle, artifact check | Add the actor driver harness and quiescence observer once they exist; the "Request-exposed test controls" bullet must mention actor-scoped overrides when the seam table gains them. |
| The document graph (generated) | Shared-question and failure-contract input edges; an existing generator-to-guide output edge | Add `docs/EXTENSIONS.md` and its input edge; extend the existing guide-output account for the new copy. The generator also reads LIMITS.md, guide text and other registered inputs; the current graph is not grounds to call QUESTIONS.md its only other prose input. Keep the drift-rule inventory aligned when rules actually change. |
| BYOXPC as a variation | "An older bundle without the issuer can serve ordinary specimens but receives a named capability refusal for extension specimens" | Keep for legacy declarations; add that actor execution needs no issuer helper and that one installed runner's entitlements apply to every actor (the plan's shared-entitlement choice). |
| Known gaps | Index lists one gap (lost reply) | Maintain the index for actual "Known gap" paragraphs. Describe deliberate scope, parked polling and transient-token lifetime in their normal semantics sections; they are not automatically gaps. Unqualified timing is an open acceptance gate, not a limitation to ship in place of qualification. |

The hand-drawn timeline and stage list are the parts most likely to be
rewritten rather than extended. The plan's own schedule for the three-actor
specimen (`b_before`, `c_before`, `initial_supply`, `b_consume`,
`b_redelegate`, `c_consume`, `c_effect`, `b_cleanup`) is the natural example
for the new timeline.

### 2.2 Worker tour

[WORKER.md](../../docs/WORKER.md) is the document the plan changes most. Its
premise, "A fresh worker applies one specimen once; its later phases share
that process", becomes "one fresh worker per actor", and an actor can hold
authority it issued itself. The opening Mermaid capability map is hand-authored;
the detailed inventory's figure and tables come from `worker_capabilities`.

| Section | Current assertion | Required change |
| --- | --- | --- |
| Opening and Capability map | Mermaid figure shows one worker with "Optional token channel prepared separately" before apply and "Requested extension consume or release" after; "exec attempts cannot share a specimen with extension use" | The figure is hand-drawn (not generated): redraw with an unapplied issuing actor, host custody, recipient delivery after apply, and a second applied actor. State the exec restriction per actor: an actor that participates in extension operations cannot exec; other actors may. |
| What the worker can establish | "requested extension actions maintain local handle state" | Distinguish the actor's issue result/transfer request, host custody/copy and recipient acceptance publication. Native handles stay local to the consuming actor. Native returns do not establish kernel extension state, effective permission or revocation. |
| Reporting apparatus | One evidence object, one mapping, "Request, result and token storage have fixed capacities" | Per-actor evidence objects and mappings; bounded issue/delivery/handle tables replace the singleton; mailbox mappings for transient custody are separate from evidence storage and carry no retained bytes. |
| Starting authority and ambient context | "For an extension request, preparation sets both core limits to zero after resolving the private entry points"; "Public admission in `extensionMeaningFailure` refuses an exec attempt combined with extension use" | Account for actor setup and for disabling core dumps in the custody-owning host before tokens arrive. The new form's exec exclusion is per extension-participating actor; legacy exclusion remains. Unapplied does not mean unrestricted. |
| Launch observation L | "Extension-bearing workers, deny-policy acquisitions ... were outside the observation" | No edit to the receipt. Add that L covers neither multi-actor launches nor unapplied actors, so the inventory's L citations do not transfer to actor sessions. |
| Supplied extension authority | Issuer-centric preparation and static handle state across phases | Describe actor issuance with exact submitted path bytes, custody, explicit transfer, recipient acceptance, consume/release references and erasure at last declared use or terminal cleanup. Erasing at every transfer would break fanout/repeated consume. Preserve legacy target preparation and helper lifetime separately. Keep the limits on claims about private native state. |
| Native observations and publications | Single worker's release wait and terminal publication | Add bounded atomic polling, service acknowledgements and phase releases. Parked actors may publish delivery acknowledgements; they must not perform specimen actions or consume before release. Native execution, result publication and transport remain separate facts. |
| Changes that change the experiment | Rows on opening targets before apply, token during preparation, reusing a worker | Cover issuing from a different process, automatic delivery without a transfer request, consuming merely because delivery arrived, and equating raw handles with lifecycle references. Delivery to a parked recipient is supported; consumption before its phase release is not. Cite each applicable control without implying it establishes every row fact. |
| Detailed capability inventory legend | "H is the host, W the worker, E the host's extension session and I the issuer" | Add letters for actor sessions and custody (the plan's names decide them); define how inventory IDs distinguish per-actor copies of the S13/S18/S21 family. |
| Worker capabilities (generated) | 84 nodes: s5/s13d token fd 5, s8a to s8c session channel, s9 to s12 issuer, s19 static function pointers, s21/s22 channel and token view, s37 "Static extension handle" | Manifest edits: s19 gains the issue symbol; s37 becomes bounded tables; new nodes for issue output storage, outbound scratch, custody buffer, recipient mailbox mapping and per-actor evidence mapping; new `supplies_authority` edges for issue, custody, transfer and acceptance. Every check citation carries an assertion `scope` (G5); "Source only; no assertion cited" is permitted but reviewed. |
| Known gaps | Three gaps indexed | Retain/review their scope; index any new actual gap under the section it limits. Do not relabel every supported boundary as a gap. |

The plan asks that the worker tour keep "one-way application, native C
boundaries and witnessing rules". The sections above that state those rules
(Reporting apparatus, Native observations and publications) need extension,
not replacement.

### 2.3 Contracts and the request lesson

| Document | Current assertion | Required change and holder |
| --- | --- | --- |
| [CONTRACT.md](../../docs/CONTRACT.md), What each number identifies | Response schema description names `steps[].comparison` as what readers must handle | Add the actor association records to the response description; the controller envelope description gains per-actor disposition projections. Version sentence and table are generated from [contract.json](../../docs/contract.json). |
| CONTRACT.md, When a number moves | Rules only | No rule change. Stage 3 applies them: response 24 to 25 and envelope 9 to 10 are the plan's deferred bump; request schema stays 5 under the additive rule; runner protocol stays 2. |
| CONTRACT.md, Accepted input contract | Legacy `policy` with exactly one of `probe_plan` or `phases`; closed object keys | Document two execution forms: legacy policy/plan and `actors` plus nonempty actor-assigned `phases`. `actors` is exclusive with top-level `policy`, `probe_plan` and legacy `extensions`, not with `phases`. Add typed actor/action/reference keys and actual normalizer diagnostics with public admission in stage 3. |
| CONTRACT.md, Internal host/worker identity | Digest covers all `.c`, `.h`, `.swift` under the worker tools and runner sources | No prose change; the digest picks up split C sources automatically. Note that fixture copies under `tests/` are not identity inputs. |
| CONTRACT.md, Shape goldens | Shape/type allowlists and independent interpretation rules | Update shapes and semantic readers together with the public contract. A field's presence in a golden admits its shape; it does not define lifecycle meaning or make interpretation code unnecessary. |
| [REQUEST-GRAMMAR.md](../../docs/REQUEST-GRAMMAR.md), Declare authority separately | "uses one local declaration under `extensions`"; corpus family table of `extension_*` cases | Add a section for the actor form with its corpus families (apply/unapplied actors, phase assignment, issue/transfer/consume/release references, aggregate caps, public refusal before children). Keep the legacy section. The lesson's executable claims come from [examples.json](../../tests/fixtures/request_contract/examples.json), so new rows wait for corpus cases. |
| REQUEST-GRAMMAR.md, Deciding whether the contract changes | Table of change classes | No change; cite it as the reason request schema stays 5. |
| [LIMITS.md](../../docs/LIMITS.md), generated tables | Legacy declaration/lifecycle/phase limits, issuer wait and channel capacities | Add actor-specific counts, aggregate capacities and timing through [limits.json](../../docs/limits.json), preserving legacy values/scope. Reuse a per-resource invariant only where its meaning and ownership really remain shared; equal numbers alone do not justify reuse. Each new row needs an implementation-value owner, control wording and honest boundary/path coverage. Coordinate geometry with its actual ABI owner. |
| LIMITS.md, Interactions that matter (shared, copied into the guide) | "Extension issuance precedes worker creation"; "Each worker arrival starts its own 60,000 milliseconds release wait" | Scope pre-issuance wording to legacy declarations. Explain actor setup/schedule accounting, parked lifetime and exchange caps, and the release allowance beginning at the selected actor's phase arrival. Values through spans. |
| LIMITS.md, Premises | Nested timeouts bullet describes `ExtensionSession` ordering | Add the actor scheduler's clock basis beside its symbol once that symbol exists. |
| [FAILURE-PROPAGATION-CONTRACT.md](../../tests/FAILURE-PROPAGATION-CONTRACT.md), Native extension evidence | Legacy shared tables enumerate 13 issuance and 6 delivery statuses; lifecycle states are separate | Add actor issue/transfer/acceptance and consume/release meanings with producers and readers. Preserve the legacy table assertions and add distinct actor completeness controls; the current enumeration test does not automatically cover new tables. The failure contract remains the status/reading source for the guide. |
| Same document, Versions and Public compatibility | "The record is mandatory for every worker reply at the current response schema"; worker identity "only from a positive `runner_subprocess.pid`" | Per-actor disposition records; identity per actor; the response and envelope numbers move at stage 3. |
| Same document, Coverage audit table | Rows name single-worker controls | Add rows for the actor driver, custody and quiescence controls from the test report, with their production reach stated. |

### 2.4 User guide and FAQ

[PolicyWitness.md](../../docs/PolicyWitness.md) is the shipped document. Its
copied regions (limits, questions, reading rules, extension statuses) are
generated. The table distinguishes those owners from authored guide sections.

| Section | Current assertion | Required change |
| --- | --- | --- |
| Questions (copied from [QUESTIONS.md](../../docs/QUESTIONS.md)) | "Can PolicyWitness test sandbox-extension behavior? Yes, for bounded file-read and directory read-write experiments. A fresh issuer ... in the same worker under one fixed policy" | Replaced by the plan's gated answer, last, after acceptance. "Which happens first" and "Can I evaluate specimens in parallel?" speak of "the worker" and "its own runner and worker processes"; both need per-actor wording in the same change. |
| Top-level shape | Legacy `probe_plan`/`phases` choice and optional `extensions` | Add the actor execution form with required `phases`, exclusive legacy fields and typed references; do not present `actors` as a replacement for the phase array. |
| Ordered phases | "The worker and its once-applied policy remain the same" | Add that in the actor form each phase names its actor and the other actors are parked. |
| Sandbox extensions | Legacy declaration semantics, one heredoc example writing `$PW_EXTENSION_DIR/request.json` | Becomes the copied region whose source is `docs/EXTENSIONS.md` (plan). Keep exactly one fenced heredoc containing that `cat > "$PW_EXTENSION_DIR/request.json"` line: [check_extensions.py](../../tests/suites/witness_contract/check_extensions.py) asserts one such fence and executes it. An actor example uses a different variable or file name, or the check is narrowed first. |
| Limits (copied) | Generated | Follows limits.json. |
| Output envelope, Top-level fields | `phases[]` fields; "The authoritative child object also includes `worker_evidence`"; singular `runner_subprocess` | Document the actor association records, per-actor subprocess and evidence objects, and which legacy fields are null or absent for the actor form (the plan's "null singular projections"). |
| The specimen dossier | Issuer provenance fields (`runner_issuer_signature`, `binaries.issuer`) | Preserve legacy evidence; describe the actor-scoped policy/application dossiers and selected-worker signing context. Binary inventory is distinct from process execution: issuer metadata does not imply a helper launch. Use the final schema's actual fields. |
| Extension and fresh-read output | Table of `extensions[]`, `issuer`, `extension_events[]`, `fresh_read`, `fresh_write`; copied status block | Add issue, delivery and custody records and their reading rules; the copied block changes only through the failure contract. |
| Reading a comparison record | Rule 13: "Extension issuance, delivery, consumption and release are independent" | Extend to transfers and to the rule that a sibling actor's query never predicts for another actor. |
| normalized_outcome catalog | Legacy admission codes include helper/API unavailability | Keep aggregate outcome rules explicit. Actor operation unavailability is not automatically a legacy `bad_request`; distinguish structural refusal, failed application and reached native results. Update actual codes and their matrix owners together. |
| Running specimens in parallel | "Four processes per run" | Describe one host with bounded live actors and a validator per eligible phase, not a permanent validator per actor. Include applicable client/exec/helper lifetimes rather than replacing one simplistic fixed count with another. Use the final qualified actor cap. |
| External runners, Install and Use | Issuer signed separately; missing-helper refusal | Qualify helper dependence as legacy. Actor operations do not launch the helper, but this is no promise to execute an invalid bundle. Preserve installation/signature diagnostics and the shared selected-worker entitlement context. |

### 2.5 Repository orientation and working rules

| Document | Current assertion | Required change |
| --- | --- | --- |
| [README.md](../../README.md), The Experiment | "Each specimen gets a fresh worker that applies the policy once"; "successive rounds of queries and attempts within the same worker" | One fresh worker per actor, applied once or left unapplied. |
| README.md, bundle inventory | "PWRunner.xpc (Swift XPC host; one host and worker per specimen ...)"; issuer line | Wording only; [generate_build.py](../../docs/generate_build.py) reads this inventory (D70), so keep the list structure and paths intact. |
| README.md, Documentation index | No extensions entry | Add `docs/EXTENSIONS.md` under "Using the app" or "Consuming the output". |
| [AGENTS.md](../../AGENTS.md), Core ideas | "One-way sandbox per process: preserve a fresh host and worker per specimen; never reuse a sandboxed process" | The plan names this edit: one fresh worker per actor, one-way application preserved, no reuse. The order-barrier bullet's rerun rule gains the actor driver. |
| [runner/AGENTS.md](../../runner/AGENTS.md) | "Preserve fresh hosts/workers"; "Reviewing a new capability" procedure | Wording; the capability-review procedure applies as written to issue, custody and transfer and should be followed rather than edited. |
| [docs/AGENTS.md](../../docs/AGENTS.md) | Shared content rules name LIMITS.md and QUESTIONS.md as copy sources and `PolicyWitness.md#anchor` as the link form | Add `EXTENSIONS.md` as a copy source with its link-rebasing rule (see 4.2). |
| [controller/AGENTS.md](../../controller/AGENTS.md) | Verification table | No change expected. |

### 2.6 Component references and test documentation

| Document | Current assertion | Required change and holder |
| --- | --- | --- |
| [runner/README.md](../../runner/README.md), intro and Key files | "a fresh C worker applies the specimen policy to itself"; table rows for `ExtensionIssuer.swift`, `CWorker.swift` | Add rows for the owned session, scheduler and custody files the plan introduces; the native helper paragraph gains the worker's issue role. |
| runner/README.md, Run lifecycle | Six numbered steps for one worker; issuer "Before worker creation" | Add the actor schedule: per-actor preparation and setup dispositions, parking, serial visits, custody exchange, per-actor terminal publication, cleanup of every actor. |
| runner/README.md, Specimen inputs and Run result highlights | Legacy plan/lifecycle restrictions | Add actor execution with phases, scoped caps and actual evidence fields when publicly wired; keep legacy meanings. |
| runner/README.md, Test seam table | Keys checked against `PWRunnerTestOverrides` | Update rows with changed top-level keys and describe nested actor/phase/action selectors where introduced. Extend the checker if its current field extraction cannot express the new shape. Global controls need not become actor-scoped. |
| [controller/README.md](../../controller/README.md) | "Worker identity comes only from `runner_subprocess.pid`"; "After version admission, the controller checks native publication, local-reference association ..." | Per-actor identity and association checks; the CLI block is locked to `cli.rs` and should not change. "What a run reads and launches" changes only if the controller gains a read or launch. |
| [tests/README.md](../../tests/README.md), Suite coverage | Row text per suite; one row per directory | `check_index_vs_disk` requires a row per suite. Any new suite needs a README and a row; actor cases inside existing suites change only the row text. |
| [tests/COVERAGE.md](../../tests/COVERAGE.md) | Outcome matrices and extension coverage paragraphs | Matrices are locked to the outcome enums; prose paragraphs on extension coverage gain the actor cases. |
| [tests/CHANGE-VERIFICATION.md](../../tests/CHANGE-VERIFICATION.md) | Routing table; order-barrier, BYOXPC extension witness and native experiment entries | Add the actor driver and quiescence controls as entries and route "actor sessions, custody or transfer" to them; extend the order-barrier entry to both drivers. |
| Suite READMEs: [witness_contract](../../tests/suites/witness_contract/README.md), [runner_c_worker_harness](../../tests/suites/runner_c_worker_harness/README.md), [runner_unit](../../tests/suites/runner_unit/README.md), [blackbox_e2e](../../tests/suites/blackbox_e2e/README.md), fixture READMEs | Describe single-worker controls | Add the detailed assertions beside their suites; the suite map keeps summaries only. |
| [BUILD.md](../../docs/BUILD.md), [SIGNING.md](../../docs/SIGNING.md), [DEPENDENCIES.md](../../docs/DEPENDENCIES.md) | Build/signing/dependency accounts | No new executable is planned. A C split requires source-list and identity updates; review these documents only where their actual build, provenance, inventory or prerequisite claims change. `build.sh` is not the build generator's only input. |

### 2.7 The new document

The plan creates `docs/EXTENSIONS.md` as the durable coverage and semantics
document. Placing it under `docs/` puts it inside the prose scan from its
first commit: register owners for any spans, use symbol-form links correctly
and keep local destinations valid. Its contents per the plan: accepted forms, actors,
operations and families, exact native calls and limits, lifecycle and
reference rules, transient transport, missing evidence, process/timing/cleanup
limits, example re-delegation and refusal outcomes, and what each observation
establishes. The supported-family table starts with file read and read-write.

Recommended shape:

- Use normal coverage and explicit-limit sections, without introducing a new
  mandatory Known-gaps index or widening that drift rule. Supported scope is
  not an apology for missing universal coverage.
- Keep one authored shared coverage region and copy it into the guide, as the
  plan already chooses. Retain failure-contract ownership of status/reading
  blocks; do not hand-maintain second versions inside EXTENSIONS.md.
- Register EXTENSIONS.md as a limits span document and generator input when
  it states owned bounds. Render its source spans before deriving the copy.
- Use ordinary `policy-witness run` examples for product semantics. If a
  developer example runs a harness case, use `tests/run.sh`, not a case script.
- State the witnessing boundary: explicit operations by PW actors, transient
  raw tokens, no private-library interception, and independent native results,
  delivery, consumption and access. Honest refusal is a supported result.

## 3. When each document can change

The plan's [integration boundary](../../SANDBOX-EXTENSION-WITNESSING-PLAN.md#integration-boundary)
holds the whole series on a branch and integrates with one commit, so `main`
never shows intermediate wording. The build checks generated freshness before
compiling. Keep affected code, source/check definitions, manifests and generated
outputs coherent in each buildable branch change; source presence can be supplied
in that very change. Citation checks do not require a previous commit or prove a
test passed. The FAQ comes last, after all acceptance gates.

| Plan stage | Coupled work on the branch | Documentation scope | Keep deferred |
| --- | --- | --- | --- |
| 1. Contract and bounded execution model | Draft model/reference/dossier tests and their accounts; affected existing limit/identity/layout owners and generated copies | Describe draft/internal support as such in developer accounts. Prepare actor corpus cases without presenting them as admitted public examples. Keep the accepted-input contract and guide accurate for the closed public grammar. | Public actor admission rows/examples, new response/envelope versions and affirmative FAQ |
| 2. Owned actor sessions and schedule | Session/wait source changes, their controls, identity, applicable architecture rows and seam accounts; internal timing constants/checks | Distinguish test-driven session machinery from the still-closed public path. Add source/check citations and generated figures together where justified. Manifest descriptions of internal limits must state that scope; they are not qualified public actor budgets. | Public actor evidence paths/goldens and accepted-input claims |
| 3. Explicit file authority path and bump | Public admission/corpus and actor limit inventory, coordinated contract versions and shapes, semantic readers, scoped status tables and controls, architecture landing paths | Update public request/operation/evidence documentation for the complete branch candidate, including EXTENSIONS.md and the shared-coverage generator. Preserve legacy meanings and qualify the provisional timing profile until measured. | Affirmative FAQ and claims of completed native/timing acceptance |
| 4. Integrated acceptance and documentation | Final qualified limits and regenerated copies; signed candidate evidence applicability; documentation/example and standalone-staging checks | Complete orientation and working-rule wording, external-runner guidance and coverage claims against actual accepted results. Suite/case documentation already follows tests as they are added, rather than waiting for this stage. | FAQ, plan retirement and merge until every required acceptance gate closes |

New draft constants are not automatically public limits merely because a draft
codec exists. Promote public actor admission rows with the stage 3 path; if an
earlier change alters an existing manifest-owned value or documents an internal
bound, update its owner/checks and rendered account with that change. A new
literal caught by G9 is not a reason to grow the prose baseline: give the owned
claim a span. G9 has partial mechanical coverage, and release preflight refuses
baseline growth against its applicable release reference; neither fact requires
all numbers in all prose to be put in limits.json.

## 4. How the edits are made

### 4.1 Manifest edits and regeneration

- Limits: edit `limits.json`, run `tests/lib/python.sh docs/generate_limits.py`,
  then `--check`. New rows need `refusal_field` for admission rows, a control
  word, a value owner from the declared owner set and citations with `form`.
  The [limit-change verification](../../tests/AGENTS.md#verify-a-limit-change)
  battery applies to every new row.
- Architecture: edit `architecture.json`, run
  `tests/lib/python.sh docs/generate_architecture.py` (needs Graphviz on PATH;
  `--check` does not). Declared column vocabularies (G7) mean a new fact key
  needs declaring in `node_facts` or `edge_facts`; durations/sizes use `{limit:id}` placeholders
  (G8); captions are generated and must not be edited (G10). The worker graph
  requires a `scope` string on every check citation.
- Contract: change public versions at stage 3, using the next available values
  if the manifest advanced. Run `tests/lib/python.sh docs/generate_contract.py`;
  its declared Rust, Swift, Python, service-plist and documentation targets
  regenerate together.
- Identity: run `tests/lib/python.sh docs/generate_worker_identity.py` after
  source/build-input edits and contract regeneration. Its input closure includes
  `build.sh`, Meson files, `runner/Package.swift` and the generator itself as well
  as worker/runner sources. The build checks it twice and never writes it.
- Build: review `build.json` and run `tests/lib/python.sh docs/generate_build.py`
  when the structured build account changes, which can involve Meson, Makefile,
  inventories or generator behavior without a `build.sh` edit. A source split
  alone does not necessarily change the build narrative; it does require source
  registration and identity updates.

Run affected generators' read-only checks after regeneration and use the normal
source-drift/acceptance discipline for their controls. These are implementation
instructions; none of these commands were executed for this scouting review.

### 4.2 The guide's copied extension coverage

The plan asks that `docs/EXTENSIONS.md` become the source of the guide's
`sandbox-extensions` prose and that the shared-question generator gain a
rebasing rule from `EXTENSIONS.md` links to the internal guide anchor. The
current question copier rebases `PolicyWitness.md#...` links and verifies that
the transformation changes only link targets and heading nesting. It does not
yet handle the bare `EXTENSIONS.md` link in the plan's exact FAQ answer.
`validate_guide` owns the marker/anchor checks; `require_standalone` checks
copied blocks' link dependencies. Recommended implementation:

1. Give EXTENSIONS.md an authored `SHARED EXTENSION COVERAGE` region and the
   guide a corresponding `COPIED EXTENSION COVERAGE` region under its existing
   `Sandbox extensions` heading. Keep the existing failure-contract status and
   reading copies separate. Add the source file to generator inputs and span
   ownership as needed; render source spans before copying. Repository-specific
   citations can remain outside the shared region, which must contain everything
   needed to understand supported coverage in the standalone guide.
2. Rebase the exact bare FAQ target `EXTENSIONS.md` to `#sandbox-extensions`.
   Support `EXTENSIONS.md#...` only for anchors actually exposed by the copied
   coverage, if used, and preserve the existing `PolicyWitness.md#...` rule.
   Define heading nesting and check anchor collisions in the complete guide.
   Preserve labels, example literals and other prose; do not use an unchecked
   filename replacement. Reject unsupported sibling dependencies. Preserve the
   narrow historical-question exception in its existing scope, rather than
   widening it to new coverage or forbidding the whole guide's external links.
3. Register the new copy in `validate_guide` and in the explicit ownership map
   in [generators.py](../../tests/suites/source_drift/generators.py), plus fixture
   input discovery. Update the document graph's input/output account and
   [docs/AGENTS.md](../../docs/AGENTS.md). A new marker pair is not automatically
   known to the existing ownership controls.
4. Extend [limits.py](../../tests/suites/source_drift/limits.py) and generator
   controls for stale copies, missing/duplicate/misordered markers, input
   validation before writes, idempotence and preservation outside owned regions.
   Exercise the bare FAQ link, used fragments, missing/colliding anchors,
   unsupported sibling links and unchanged code/example literals. Check the
   staged standalone file without relying on sibling files. The existing
   `test_regeneration_changes_nothing_outside_regions` is useful after its
   ownership map includes this new region; it alone does not test link semantics.
5. Publish the affirmative FAQ only after full acceptance, with its source link
   relative to QUESTIONS.md and its generated guide link internal. The copier
   and its controls can be developed earlier on the branch; the FAQ itself
   remains gated by calibration, policy/timing qualification and other required
   acceptance.

### 4.3 Status tables, events and readers

The shared extension status block is copied verbatim. Its current enumeration
test hard-codes the legacy issuance/delivery sets; it does not inspect the
encoder or discover actor statuses. Keep those legacy assertions and add
distinct actor table/set controls with the stage 3 producers and readers.
Label the execution form so a helper's spawn/reap status is not confused with
an actor's native issue result, publication, custody or recipient acceptance.

The failure contract owns the authored meanings, the guide copies them, and
independent semantic readers enforce the wire rules. Shape goldens admit fields
and types; readers do not learn lifecycle semantics by reading Markdown or a
golden. New actor tables require corresponding completeness and interpretation
controls, not merely an enlarged legacy status set. Coordinate publication,
unavailability and unresolved-state wording with the actual final encoding.

### 4.4 Wording sites

Phrases that assert one worker per specimen, listed by document for a search
pass at stage 4. Each must be reread in context; some are true of the legacy
form and need qualification rather than replacement.

- README.md: "Each specimen gets a fresh worker"; "within the same worker";
  "one host and worker per specimen".
- AGENTS.md: "preserve a fresh host and worker per specimen".
- docs/ARCHITECTURE.md: "one worker per specimen"; "all phases use one worker
  and one policy application"; "native issuance occurs before worker
  creation".
- docs/WORKER.md: "A fresh worker applies one specimen once"; "exec attempts
  cannot share a specimen with extension use"; "The static handle carries
  state across actions and phases".
- docs/PolicyWitness.md: "The worker applies the submitted policy once and
  keeps that policy through every phase"; "Four processes per run"; the FAQ
  answers named in 2.4.
- docs/QUESTIONS.md: "in the same worker under one fixed policy"; "before the
  worker acknowledged that phase's host release"; "its own runner and worker
  processes".
- docs/LIMITS.md shared bullets: "Extension issuance precedes worker
  creation"; "Each worker arrival starts its own ... release wait".
- runner/README.md: "a fresh C worker applies the specimen policy to itself";
  "its fresh worker applies the policy"; "Before worker creation, the host
  resolves its target".
- controller/README.md: "Worker identity comes only from
  `runner_subprocess.pid`".
- tests/FAILURE-PROPAGATION-CONTRACT.md: "Worker identity comes only from a
  positive `runner_subprocess.pid`"; "The record is mandatory for every worker
  reply".

Use the wording rule when rewriting: "actor", "issue", "transfer", "consume",
"release", "custody" and "parked" as the plan defines them; no "attack" or
"exploit" framing for re-delegation, which is an ordinary specimen.

## 5. Integration with the plan and resolved choices

The associated plan links to this inventory and carries these dependencies in
its stages and documentation/completion section:

- Keep manifest-owned facts, source/check definitions and generated outputs
  together as their code changes; there is no mandatory extra commit between
  a test definition and a figure. Distinguish internal stages 1–2 from stage 3
  public admission and wire documentation. The final stage verifies and closes
  the documentation work; it does not begin all of it.
- Make the shared-coverage copier's ownership, exact bare-link rebasing, rendered
  source spans and standalone controls explicit implementation work. Preserve
  failure-contract ownership of statuses/reading rules and existing legacy
  enumeration checks while adding actor-specific ones.
- Require a final semantics review across request examples, diagrams, evidence
  paths and operator guidance: delivery while parked is supported, consume waits
  for phase release, actor references remain distinct, and an issue/consume result
  alone does not establish access. Mechanical freshness cannot establish this.
- Gate the affirmative FAQ on the plan's complete acceptance, including positive
  calibration, principal-policy application and timing qualification. Keep the
  accepted investigation and launch-observation bytes unchanged; cite new
  implementation evidence for new behavior without relabelling old receipts.

The plan keeps the legacy path supported, uses one maintained coverage source
and does not require a new gaps index for EXTENSIONS.md. A per-actor worker node
with explicit multiplicity is adequate for the production topology; the
conceptual specimen diagram may separately
show A, B and C. Exact layout and section titles remain editorial choices.
No documentation finding creates a new native uncertainty or standalone
experimental prerequisite. Detailed document/section inventories stay here,
not duplicated in the plan or linked from permanent documentation.
